"""Orchestration: recording session, question detection, answer streaming, and UI events."""
from __future__ import annotations

import asyncio
import itertools
import logging
import time
from collections import OrderedDict
from datetime import datetime
from typing import Optional

from fastapi import WebSocket

from . import prompts
from .config import SESSIONS_DIR, UPLOADS_DIR, Settings
from .demo import DEMO_ANSWER, run_demo
from .documents import DocumentStore
from .llm import LLM, LLMError, parse_json_object
from .turns import WINDOW_CHARS, Aggregator, Turn

log = logging.getLogger("core")

Transcript = tuple[list[str], list[str]]  # (finished lines, lines still being spoken)


class SessionError(RuntimeError):
    pass


# --------------------------------------------------------------------------------------
# UI event hub
# --------------------------------------------------------------------------------------
class UiState:
    """Mirror of what the browser shows, so a refreshed page can catch up."""

    def __init__(self):
        self.reset()
        self.status = {"type": "status", "state": "idle", "message": "", "started_at": None, "demo": False}

    def reset(self):
        self.turns: "OrderedDict[int, dict]" = OrderedDict()
        self.answers: "OrderedDict[str, dict]" = OrderedDict()
        self.detections: dict[int, str] = {}

    def apply(self, ev: dict) -> None:
        t = ev.get("type")
        if t == "turn":
            self.turns[ev["turn"]["id"]] = ev["turn"]
        elif t == "turn_removed":
            self.turns.pop(ev["id"], None)
        elif t == "detector":
            self.detections[ev["turn_id"]] = ev["result"]
        elif t == "answer_start":
            self.answers[ev["answer"]["id"]] = {**ev["answer"], "text": "", "done": False}
        elif t == "answer_delta":
            a = self.answers.get(ev["id"])
            if a:
                a["text"] += ev["text"]
        elif t == "answer_done":
            a = self.answers.get(ev["id"])
            if a:
                a.update(done=True, latency_ms=ev.get("latency_ms"), error=ev.get("error"))
        elif t == "status":
            self.status = ev
        elif t == "clear":
            self.reset()

    def snapshot(self) -> dict:
        return {
            "type": "snapshot",
            "status": self.status,
            "turns": list(self.turns.values()),
            "answers": list(self.answers.values()),
            "detections": self.detections,
        }


class Hub:
    def __init__(self):
        self.state = UiState()
        self._clients: dict[WebSocket, asyncio.Queue] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def emit(self, ev: dict) -> None:
        """Call from the event loop thread."""
        if ev.get("type") != "levels":
            self.state.apply(ev)
        for ws, q in list(self._clients.items()):
            if q.qsize() > 2000:
                continue  # very slow client; it will resync from a snapshot on reconnect
            q.put_nowait(ev)

    def emit_threadsafe(self, ev: dict) -> None:
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.emit, ev)

    def notice(self, message: str, level: str = "info") -> None:
        self.emit({"type": "notice", "level": level, "message": message})

    async def serve(self, ws: WebSocket, extra_snapshot: dict) -> None:
        q: asyncio.Queue = asyncio.Queue()
        self._clients[ws] = q
        await ws.send_json({**self.state.snapshot(), **extra_snapshot})

        async def writer():
            while True:
                ev = await q.get()
                await ws.send_json(ev)

        w = asyncio.create_task(writer())
        try:
            while True:
                await ws.receive_text()  # we only use the socket for server -> browser events
        except Exception:
            pass
        finally:
            w.cancel()
            self._clients.pop(ws, None)


# --------------------------------------------------------------------------------------
# Answer agent
# --------------------------------------------------------------------------------------
class Answerer:
    def __init__(self, core: "Core"):
        self.core = core
        self._ids = itertools.count(1)
        self._tasks: set[asyncio.Task] = set()
        self._sent: list[list[str]] = []  # finished transcript lines, grouped as the last answer sent them

    def spawn(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def _history_blocks(self, lines: list[str]) -> list[str]:
        """Repeat the last answer's blocks and add one block of lines finished since, so this answer's
        cache entry is one block after the previous one (the API looks back at most 20 blocks)."""
        sent = [line for block in self._sent for line in block]
        if lines[:len(sent)] != sent:  # new session, or the transcript window jumped
            self._sent, sent = [], []
        if len(lines) > len(sent):
            self._sent = [*self._sent, lines[len(sent):]]
        return ["".join(line + "\n" for line in block) for block in self._sent]

    async def handle_turn(self, turn_id: int, text: str, transcript: Transcript, t0: float) -> None:
        """An interviewer turn just ended: decide if it needs an answer, then answer it."""
        hub, llm = self.core.hub, self.core.llm
        verdict = prompts.quick_classify(text)
        label = text
        if verdict == "no":
            hub.emit({"type": "detector", "turn_id": turn_id, "result": "skip"})
            return
        if verdict == "maybe":
            if not llm.has_key():
                hub.emit({"type": "detector", "turn_id": turn_id, "result": "skip"})
                return
            hub.emit({"type": "detector", "turn_id": turn_id, "result": "checking"})
            try:
                raw = await llm.complete(
                    prompts.DETECT_SYSTEM,
                    prompts.DETECT_USER.format(transcript="\n".join(transcript[0] + transcript[1])[-3000:], turn=text),
                )
            except LLMError as e:
                hub.emit({"type": "detector", "turn_id": turn_id, "result": "error"})
                hub.notice(f"Question check failed: {e}", "error")
                return
            res = parse_json_object(raw)
            if not res.get("needs_answer"):
                hub.emit({"type": "detector", "turn_id": turn_id, "result": "skip"})
                return
            label = (res.get("question") or text).strip()
        hub.emit({"type": "detector", "turn_id": turn_id, "result": "question"})
        await self.answer(text, label, turn_id, transcript, t0, manual=False)

    async def answer(self, question: str, label: str, turn_id: Optional[int], transcript: Transcript,
                     t0: float, manual: bool) -> None:
        core, hub, llm = self.core, self.core.hub, self.core.llm
        aid = f"a{next(self._ids)}"
        meta = {
            "id": aid, "question": label, "turn_id": turn_id, "created": time.time(),
            "provider": llm.provider(), "model": llm.model("answer"), "manual": manual,
        }

        if not llm.has_key():
            if core.demo_active:
                await self._fake_answer(meta, t0)
            else:
                hub.notice("Add an Anthropic or OpenAI API key in Settings to get answers.", "warn")
                if turn_id is not None:
                    hub.emit({"type": "detector", "turn_id": turn_id, "result": "question"})
            return

        s = core.settings
        instructions = prompts.answer_system(s.get("answer_style"), s.get("extra_instructions") or "")
        docs, _ = core.docs.combined()
        template = prompts.ANSWER_USER_MANUAL if manual else prompts.ANSWER_USER
        closed, recent = transcript
        if not closed and not recent:
            recent = ["(nothing yet)"]
        user = template.format(transcript="".join(line + "\n" for line in recent), question=question)
        history = self._history_blocks([prompts.TRANSCRIPT_HEAD, *closed])

        started = False
        buf = ""
        latency_ms = None
        gen = llm.stream(instructions, prompts.docs_block(docs), user, history)
        try:
            async for chunk in gen:
                if not started:
                    buf += chunk
                    head = buf.lstrip()
                    if not manual:
                        if len(head) < len("NO_ANSWER") and "NO_ANSWER".startswith(head):
                            continue  # might still turn out to be NO_ANSWER
                        if head.startswith("NO_ANSWER"):
                            if turn_id is not None:
                                hub.emit({"type": "detector", "turn_id": turn_id, "result": "skip"})
                            return
                    if not head:
                        continue
                    started = True
                    latency_ms = int((time.perf_counter() - t0) * 1000)
                    hub.emit({"type": "answer_start", "answer": {**meta, "latency_ms": latency_ms}})
                    hub.emit({"type": "answer_delta", "id": aid, "text": head})
                else:
                    hub.emit({"type": "answer_delta", "id": aid, "text": chunk})
            if not started:
                head = buf.strip()
                if not head or head.startswith("NO_ANSWER"):
                    if turn_id is not None:
                        hub.emit({"type": "detector", "turn_id": turn_id, "result": "skip"})
                    return
                latency_ms = int((time.perf_counter() - t0) * 1000)
                hub.emit({"type": "answer_start", "answer": {**meta, "latency_ms": latency_ms}})
                hub.emit({"type": "answer_delta", "id": aid, "text": head})
            hub.emit({"type": "answer_done", "id": aid, "latency_ms": latency_ms})
        except LLMError as e:
            if not started:
                hub.emit({"type": "answer_start", "answer": meta})
            hub.emit({"type": "answer_done", "id": aid, "error": str(e)})
        finally:
            await gen.aclose()

    async def _fake_answer(self, meta: dict, t0: float) -> None:
        hub = self.core.hub
        await asyncio.sleep(0.6)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        hub.emit({"type": "answer_start", "answer": {**meta, "model": "demo", "latency_ms": latency_ms}})
        for word in DEMO_ANSWER.split(" "):
            hub.emit({"type": "answer_delta", "id": meta["id"], "text": word + " "})
            await asyncio.sleep(0.03)
        hub.emit({"type": "answer_done", "id": meta["id"], "latency_ms": latency_ms})


# --------------------------------------------------------------------------------------
# Recording session
# --------------------------------------------------------------------------------------
class Session:
    def __init__(self, core: "Core", demo: bool = False):
        self.core = core
        self.demo = demo
        self.stopping = False
        self.started_at = time.time()
        self.aggregator = Aggregator(emit=core.hub.emit, on_interviewer_turn=self._on_interviewer_turn)
        self.capture = None
        self.queue: Optional[asyncio.Queue] = None
        self.task: Optional[asyncio.Task] = None
        self.wav_path = None

    # Called by the aggregator (event loop thread) whenever an interviewer turn ends.
    def _on_interviewer_turn(self, turn: Turn, reason: str) -> None:
        if self.stopping or not self.core.settings.get("auto_answer"):
            return
        words = len(turn.final_text.split())
        if reason == "question_mark":
            if turn.answered_words:
                return
        elif turn.answered_words and words - turn.answered_words < 4:
            return  # already answered via the fast path and nothing much was added
        turn.answered_words = words
        self.core.answerer.spawn(
            self.core.answerer.handle_turn(turn.id, turn.final_text, self.aggregator.transcript_parts(), time.perf_counter())
        )

    def _status(self, state: str, message: str = "") -> None:
        self.core.hub.emit({"type": "status", "state": state, "message": message,
                            "started_at": self.started_at, "demo": self.demo})

    def _levels(self, me: float, them: float) -> None:
        self.core.hub.emit_threadsafe({"type": "levels", "me": round(me, 3), "interviewer": round(them, 3)})

    async def start(self) -> None:
        hub, s = self.core.hub, self.core.settings
        hub.emit({"type": "clear"})
        self._status("connecting")
        if self.demo:
            self.task = asyncio.create_task(self._run_demo())
            self._status("recording")
            return

        key = s.get("deepgram_api_key")
        if not key:
            raise SessionError("Add your Deepgram API key in Settings first (it does the live transcription).")

        from .audio_capture import DualCapture  # imported here so the app still runs off Windows
        from .transcriber import DeepgramStream, build_url

        loop = asyncio.get_running_loop()
        self.queue = asyncio.Queue(maxsize=1500)  # ~30 s of audio if the network stalls

        def on_frame(data: bytes) -> None:
            loop.call_soon_threadsafe(self._enqueue, data)

        if s.get("save_audio"):
            self.wav_path = SESSIONS_DIR / f"{datetime.now():%Y-%m-%d_%H%M%S}.wav"
        self.capture = DualCapture(on_frame, self._levels, s.get("mic_device"), s.get("speaker_device"), self.wav_path)
        await asyncio.to_thread(self.capture.start)
        hub.notice(f"Me = {self.capture.mic_name}  |  Interviewer = {self.capture.speaker_name}")

        keyterms = [k.strip() for k in (s.get("keyterms") or "").split(",") if k.strip()]
        url = build_url(s.get("deepgram_model"), s.get("language"), keyterms)
        stt = DeepgramStream(key, url, self.queue, self.aggregator.handle, self._status)
        self.task = asyncio.create_task(self._run_stt(stt))

    def _enqueue(self, data: bytes) -> None:
        q = self.queue
        if q is None:
            return
        if q.full():
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                pass
        q.put_nowait(data)

    async def _run_stt(self, stt) -> None:
        from .transcriber import FatalTranscriptionError
        try:
            await stt.run()
        except FatalTranscriptionError as e:
            self.core.hub.notice(str(e), "error")
            asyncio.create_task(self.core.stop_session(error=str(e)))

    async def _run_demo(self) -> None:
        try:
            await run_demo(self.aggregator.handle, self._levels)
            self.core.hub.notice("Demo finished.")
        finally:
            if not self.stopping:
                asyncio.create_task(self.core.stop_session())

    async def stop(self) -> Optional[str]:
        self.stopping = True
        if self.capture:
            await asyncio.to_thread(self.capture.stop)
        if self.queue is not None:
            self._enqueue(None)  # tells Deepgram to finish and send the last words
        if self.task and self.task is not asyncio.current_task():
            try:
                await asyncio.wait_for(asyncio.shield(self.task), timeout=4)
            except (asyncio.TimeoutError, Exception):
                self.task.cancel()
        self.aggregator.flush()
        return self._save()

    def _save(self) -> Optional[str]:
        state = self.core.hub.state
        if not state.turns:
            return None
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        path = SESSIONS_DIR / f"{datetime.fromtimestamp(self.started_at):%Y-%m-%d_%H%M%S}{'_demo' if self.demo else ''}.md"
        lines = [f"# Interview session {datetime.fromtimestamp(self.started_at):%Y-%m-%d %H:%M}", "", "## Transcript", ""]
        for t in state.turns.values():
            who = "Interviewer" if t["speaker"] == "interviewer" else "Me"
            lines.append(f"**{who}:** {t['final'] or t['interim']}")
            lines.append("")
        if state.answers:
            lines += ["## AI answers", ""]
            for a in state.answers.values():
                lines += [f"### {a['question']}", "", a.get("text") or f"_{a.get('error') or 'no answer'}_", ""]
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)


# --------------------------------------------------------------------------------------
# App core
# --------------------------------------------------------------------------------------
class Core:
    def __init__(self):
        self.settings = Settings()
        self.docs = DocumentStore(UPLOADS_DIR)
        self.llm = LLM(self.settings)
        self.hub = Hub()
        self.answerer = Answerer(self)
        self.session: Optional[Session] = None
        self._lock = asyncio.Lock()

    @property
    def demo_active(self) -> bool:
        return bool(self.session and self.session.demo)

    async def start_session(self, demo: bool = False) -> None:
        async with self._lock:
            if self.session:
                return
            session = Session(self, demo=demo)
            self.session = session
            try:
                await session.start()
            except Exception as e:
                self.session = None
                if session.capture:
                    await asyncio.to_thread(session.capture.stop)
                session._status("idle", str(e))
                raise SessionError(str(e)) from e

    async def stop_session(self, error: str = "") -> Optional[str]:
        async with self._lock:
            session = self.session
            if not session:
                return None
            path = await session.stop()
            self.session = None
            self.hub.emit({"type": "status", "state": "error" if error else "idle", "message": error,
                           "started_at": None, "demo": False})
            if path:
                self.hub.emit({"type": "saved", "path": path})
            return path

    async def manual_answer(self, question: str = "") -> None:
        """'Answer now' button (latest interviewer turn) or a typed question."""
        turn_id = None
        session = self.session
        if session:
            transcript = session.aggregator.transcript_parts()
        else:  # recording stopped: every turn is finished
            lines = [f"{'Interviewer' if t['speaker'] == 'interviewer' else 'Me'}: {t['final'] or t['interim']}"
                     for t in self.hub.state.turns.values()]
            while len(lines) > 1 and sum(len(line) + 1 for line in lines) > WINDOW_CHARS:
                lines.pop(0)
            transcript = (lines, [])
        if question.strip():
            label = question.strip()
        else:
            latest = None
            if session:
                latest = session.aggregator.latest_interviewer_turn()
                if latest:
                    turn_id, question = latest.id, latest.text
            if not latest:
                for t in reversed(self.hub.state.turns.values()):
                    if t["speaker"] == "interviewer":
                        turn_id, question = t["id"], t["final"] or t["interim"]
                        break
            if not question:
                raise SessionError("No interviewer question yet.")
            label = question
        self.answerer.spawn(self.answerer.answer(question, label, turn_id, transcript, time.perf_counter(), manual=True))
