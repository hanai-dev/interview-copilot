"""Deepgram live transcription over a WebSocket (multichannel: one channel per speaker)."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Awaitable, Callable, Optional
from urllib.parse import urlencode

from websockets.asyncio.client import connect
from websockets.exceptions import InvalidStatus

log = logging.getLogger("transcriber")

DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen"


def build_url(model: str, language: str, keyterms: list[str], sample_rate: int = 16000) -> str:
    params: list[tuple[str, str]] = [
        ("model", model or "nova-3"),
        ("language", language or "en"),
        ("encoding", "linear16"),
        ("sample_rate", str(sample_rate)),
        ("channels", "2"),
        ("multichannel", "true"),      # transcribe left (me) and right (interviewer) separately
        ("interim_results", "true"),   # words appear while people are still talking
        ("punctuate", "true"),
        ("smart_format", "true"),
        ("endpointing", "300"),        # finalize a phrase after 300 ms of silence
        ("utterance_end_ms", "1000"),  # signal "turn over" after ~1 s without new words
        ("vad_events", "true"),
    ]
    if (model or "").startswith("nova-3"):
        for term in keyterms[:50]:
            params.append(("keyterm", term))
    return f"{DEEPGRAM_URL}?{urlencode(params)}"


class FatalTranscriptionError(RuntimeError):
    pass


class DeepgramStream:
    """Sends audio frames from `audio_queue` and passes every server message to `on_message`.

    Reconnects automatically on network hiccups. Put `None` into the queue to finish cleanly.
    """

    def __init__(
        self,
        api_key: str,
        url: str,
        audio_queue: "asyncio.Queue[Optional[bytes]]",
        on_message: Callable[[dict], None],
        on_status: Callable[[str, str], Awaitable[None] | None],
    ):
        self.api_key = api_key
        self.url = url
        self.queue = audio_queue
        self.on_message = on_message
        self.on_status = on_status
        self._finishing = False

    async def _status(self, state: str, message: str = "") -> None:
        r = self.on_status(state, message)
        if asyncio.iscoroutine(r):
            await r

    async def run(self) -> None:
        delay = 1.0
        while not self._finishing:
            try:
                async with connect(
                    self.url,
                    additional_headers={"Authorization": f"Token {self.api_key}"},
                    max_size=None,
                    ping_interval=20,
                    open_timeout=10,
                ) as ws:
                    delay = 1.0
                    await self._status("recording")
                    sender = asyncio.create_task(self._send(ws))
                    try:
                        async for raw in ws:
                            if isinstance(raw, (bytes, bytearray)):
                                continue
                            try:
                                msg = json.loads(raw)
                            except ValueError:
                                continue
                            if msg.get("type") == "Error":
                                log.warning("Deepgram error: %s", msg.get("description"))
                            self.on_message(msg)
                    finally:
                        sender.cancel()
                        try:
                            await sender
                        except (asyncio.CancelledError, Exception):
                            pass
                if self._finishing:
                    break
            except InvalidStatus as e:
                code = getattr(getattr(e, "response", None), "status_code", 0)
                if code in (401, 403):
                    raise FatalTranscriptionError("Deepgram rejected the API key. Check it in Settings.") from e
                if code == 402:
                    raise FatalTranscriptionError("Deepgram account is out of credit.") from e
                log.warning("Deepgram connection refused (%s)", code)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # network drop, timeout, ...
                if self._finishing:
                    break
                log.warning("Deepgram connection lost: %s", e)
            if self._finishing:
                break
            await self._status("reconnecting", "Transcription connection dropped, reconnecting...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)

    async def _send(self, ws) -> None:
        while True:
            try:
                data = await asyncio.wait_for(self.queue.get(), timeout=5)
            except asyncio.TimeoutError:
                await ws.send(json.dumps({"type": "KeepAlive"}))
                continue
            if data is None:
                self._finishing = True
                await ws.send(json.dumps({"type": "CloseStream"}))
                return
            await ws.send(data)
