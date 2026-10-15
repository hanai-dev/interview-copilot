"""Tests that run on any OS (no microphone, no API keys needed).

    python -m pytest -q
"""
import asyncio
import json
import sys
import threading
import time
import types

import numpy as np
import pytest

from app import prompts
from app.turns import Aggregator


def res(ch, text, final=False, speech_final=False):
    return {"type": "Results", "channel_index": [ch, 2], "is_final": final, "speech_final": speech_final,
            "channel": {"alternatives": [{"transcript": text, "confidence": 0.9, "words": []}]}}


def ue(ch):
    return {"type": "UtteranceEnd", "channel": [ch, 2], "last_word_end": 1.0}


class Clock:
    t = 1000.0

    def __call__(self):
        return self.t


def make_agg():
    events, triggers = [], []
    clock = Clock()
    agg = Aggregator(events.append, lambda turn, reason: triggers.append((turn.final_text, reason)), clock)
    return agg, events, triggers, clock


# ---------------------------------------------------------------- turns / speakers
def test_speaker_labels_and_turn_close():
    agg, events, triggers, _ = make_agg()
    agg.handle(res(1, "Tell me about"))
    agg.handle(res(1, "Tell me about yourself.", final=True, speech_final=True))
    agg.handle(ue(1))
    agg.handle(res(0, "Sure, I'm a student.", final=True))
    agg.handle(ue(0))
    assert [(t.speaker, t.final_text) for t in agg.turns] == [
        ("interviewer", "Tell me about yourself."), ("me", "Sure, I'm a student.")]
    assert triggers == [("Tell me about yourself.", "utterance_end")]


def test_question_mark_fast_path_then_no_duplicate():
    agg, _, triggers, _ = make_agg()
    agg.handle(res(1, "What's your biggest strength?", final=True, speech_final=True))
    assert triggers == [("What's your biggest strength?", "question_mark")]
    agg.handle(ue(1))  # Session de-duplicates using turn.answered_words; aggregator reports both
    assert triggers[-1][1] == "utterance_end"


def test_backchannel_does_not_cut_off_interviewer():
    agg, _, triggers, _ = make_agg()
    agg.handle(res(1, "So walk me through", final=True))
    agg.handle(res(0, "Yeah.", final=True))  # short "yeah" from me
    assert agg.open["interviewer"] is not None
    agg.handle(res(1, "your last project and the hardest bug you fixed.", final=True, speech_final=True))
    agg.handle(ue(1))
    assert triggers[-1][0] == "So walk me through your last project and the hardest bug you fixed."


def test_speaker_change_closes_other_turn():
    agg, _, triggers, _ = make_agg()
    agg.handle(res(1, "Describe a challenge you faced", final=True))
    agg.handle(res(0, "One challenge I faced was a tight deadline.", final=True))
    assert triggers == [("Describe a challenge you faced", "speaker_change")]


def test_echo_on_mic_is_dropped():
    agg, events, triggers, _ = make_agg()
    agg.handle(res(1, "How do you handle conflict within a team?", final=True, speech_final=True))
    # Laptop speakers -> mic hears the same words a moment later on channel 0
    agg.handle(res(0, "how do you handle conflict"))
    agg.handle(res(0, "How do you handle conflict within a team?", final=True))
    assert [t.speaker for t in agg.turns] == ["interviewer"]
    assert agg.echo_count == 1
    # but a genuine reply on the mic is kept
    agg.handle(res(0, "I usually start by listening to both sides.", final=True))
    assert [t.speaker for t in agg.turns] == ["interviewer", "me"]


def test_empty_interim_discarded_and_transcript_text():
    agg, events, _, _ = make_agg()
    agg.handle(res(1, "Hello"))
    agg.handle(res(1, "", final=True))
    assert agg.turns == []
    assert any(e["type"] == "turn_removed" for e in events)
    agg.handle(res(1, "Why this company?", final=True))
    agg.handle(res(0, "Because I love the product you build.", final=True))
    assert agg.transcript() == "Interviewer: Why this company?\nMe: Because I love the product you build."


def test_transcript_parts_keep_a_stable_prefix(monkeypatch):
    from app import turns
    monkeypatch.setattr(turns, "WINDOW_CHARS", 400)  # ~4 question/answer pairs
    agg, _, _, _ = make_agg()
    for i in range(3):
        agg.handle(res(1, f"Question number {i} about your experience?", final=True))
        agg.handle(res(0, f"Answer number {i} with plenty of detail.", final=True))
    closed, recent = agg.transcript_parts()
    assert closed[0].startswith("Interviewer: Question number 0") and recent == ["Me: Answer number 2 with plenty of detail."]
    agg.handle(ue(0))
    closed2, recent2 = agg.transcript_parts()
    assert closed2[:len(closed)] == closed and recent2 == []  # finished lines only grow at the end
    for i in range(3, 6):  # overflow: the window jumps forward once, then grows from its new start
        agg.handle(res(1, f"Question number {i} about your experience?", final=True))
        agg.handle(res(0, f"Answer number {i} with plenty of detail.", final=True))
        agg.handle(ue(0))
    jumped = agg.transcript_parts()[0]
    assert "Question number 0" not in jumped[0] and sum(len(x) + 1 for x in jumped) <= 400 // 2
    agg.handle(res(1, "One more question?", final=True))
    agg.handle(ue(1))
    assert agg.transcript_parts()[0][:len(jumped)] == jumped


def test_each_answer_adds_one_history_block():
    from app.core import Answerer
    a = Answerer(core=None)
    assert a._history_blocks(["H", "A"]) == ["H\nA\n"]
    lines = ["H", "A"] + [f"Me: part {i}" for i in range(30)]  # 30 short turns between two answers
    assert a._history_blocks(lines) == ["H\nA\n", "".join(f"Me: part {i}\n" for i in range(30))]
    assert a._history_blocks(lines) == a._history_blocks(lines)  # nothing new: same blocks
    assert a._history_blocks(["H", "B"]) == ["H\nB\n"]  # window jumped: start over


# ---------------------------------------------------------------- question classifier
@pytest.mark.parametrize("text,expected", [
    ("Can you hear me okay?", "no"),
    ("How are you doing today?", "no"),
    ("What is a hash map?", "yes"),
    ("Tell me about a time you failed.", "yes"),
    ("Walk me through your resume", "yes"),
    ("Great, thanks.", "no"),
    ("Okay so our team works mostly in Python and React", "maybe"),
])
def test_quick_classify(text, expected):
    assert prompts.quick_classify(text) == expected


def test_answer_prompt_has_style_and_extra():
    s = prompts.answer_system("short", "I'm applying for a data analyst role.")
    assert "2-3 sentences" in s and "data analyst" in s and "NO_ANSWER" in s


# ---------------------------------------------------------------- audio mixing (fake pyaudiowpatch)
class _FakeStream:
    def __init__(self, cb, rate, channels, freq, amp):
        self.cb, self.rate, self.channels, self.freq, self.amp = cb, rate, channels, freq, amp
        self._stop = threading.Event()
        self.t = None

    def start_stream(self):
        def run():
            n, i = int(self.rate * 0.01), 0
            while not self._stop.is_set():
                tt = (np.arange(n) + i) / self.rate
                mono = (np.sin(2 * np.pi * self.freq * tt) * self.amp * 32767).astype(np.int16)
                frames = np.repeat(mono, self.channels)
                self.cb(frames.tobytes(), n, {}, 0)
                i += n
                time.sleep(0.01)
        self.t = threading.Thread(target=run, daemon=True)
        self.t.start()

    def stop_stream(self):
        self._stop.set()

    def close(self):
        pass


def _install_fake_pyaudio(monkeypatch, speaker_silent=False):
    devices = {
        0: {"index": 0, "name": "Headphones (USB)", "hostApi": 0, "maxInputChannels": 0, "defaultSampleRate": 48000},
        1: {"index": 1, "name": "Microphone (USB)", "hostApi": 0, "maxInputChannels": 1, "defaultSampleRate": 44100},
        2: {"index": 2, "name": "Headphones (USB) [Loopback]", "hostApi": 0, "maxInputChannels": 2,
            "defaultSampleRate": 48000, "isLoopbackDevice": True},
    }

    class PyAudio:
        def get_host_api_info_by_type(self, t):
            return {"index": 0, "defaultInputDevice": 1, "defaultOutputDevice": 0}

        def get_device_count(self):
            return len(devices)

        def get_device_info_by_index(self, i):
            return devices[i]

        def get_default_input_device_info(self):
            return devices[1]

        def get_default_wasapi_loopback(self):
            return devices[2]

        def get_loopback_device_info_generator(self):
            yield devices[2]

        def open(self, format, channels, rate, input, input_device_index, frames_per_buffer, stream_callback):
            mic = input_device_index == 1
            amp = 0.0 if (not mic and speaker_silent) else 0.5
            return _FakeStream(stream_callback, rate, channels, 300 if mic else 500, amp)

        def terminate(self):
            pass

    mod = types.SimpleNamespace(PyAudio=PyAudio, paWASAPI=13, paInt16=8, paContinue=0)
    monkeypatch.setitem(sys.modules, "pyaudiowpatch", mod)


def test_list_devices(monkeypatch):
    _install_fake_pyaudio(monkeypatch)
    from app.audio_capture import list_devices
    d = list_devices()
    assert d["mics"] == [{"index": 1, "name": "Microphone (USB)", "default": True}]
    assert d["speakers"] == [{"index": 2, "name": "Headphones (USB)", "default": True}]


@pytest.mark.parametrize("speaker_silent", [False, True])
def test_dual_capture_produces_stereo_16k(monkeypatch, tmp_path, speaker_silent):
    _install_fake_pyaudio(monkeypatch, speaker_silent)
    from app.audio_capture import DualCapture
    chunks, levels = [], []
    cap = DualCapture(chunks.append, lambda a, b: levels.append((a, b)), wav_path=tmp_path / "a.wav")
    cap.start()
    time.sleep(1.2)
    cap.stop()
    audio = np.frombuffer(b"".join(chunks), dtype=np.int16).reshape(-1, 2)
    seconds = len(audio) / 16000
    assert 0.9 <= seconds <= 1.25, seconds  # real-time rate, ~100 ms behind
    me, them = audio[4000:, 0].astype(float), audio[4000:, 1].astype(float)
    assert np.abs(me).max() > 10000  # mic tone on the left channel
    if speaker_silent:
        assert np.abs(them).max() < 100  # silence padded when loopback sends nothing
    else:
        assert np.abs(them).max() > 10000
        # check the tones landed on the right channels (300 Hz mic, 500 Hz speakers)
        def peak(x):
            spec = np.abs(np.fft.rfft(x[:8000]))
            return np.fft.rfftfreq(8000, 1 / 16000)[spec.argmax()]
        assert abs(peak(me) - 300) < 10 and abs(peak(them) - 500) < 10
    assert levels and (tmp_path / "a.wav").stat().st_size > 30000


# ---------------------------------------------------------------- Deepgram client against a fake server
def test_deepgram_stream_roundtrip():
    from websockets.asyncio.server import serve
    from app import transcriber

    received = {"bytes": 0, "auth": None, "path": None, "close": False}

    async def handler(ws):
        received["auth"] = ws.request.headers.get("Authorization")
        received["path"] = ws.request.path
        async for msg in ws:
            if isinstance(msg, bytes):
                received["bytes"] += len(msg)
                if received["bytes"] == 6400:
                    await ws.send(json.dumps(res(1, "What is Python?", final=True, speech_final=True)))
            elif json.loads(msg).get("type") == "CloseStream":
                received["close"] = True
                await ws.send(json.dumps(ue(1)))
                await ws.close()

    async def main():
        async with serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            url = transcriber.build_url("nova-3", "en", ["Kubernetes"]).replace(
                "wss://api.deepgram.com", f"ws://127.0.0.1:{port}")
            q = asyncio.Queue()
            msgs, statuses = [], []
            stream = transcriber.DeepgramStream("KEY123", url, q, msgs.append, lambda s, m="": statuses.append(s))
            task = asyncio.create_task(stream.run())
            for _ in range(5):
                await q.put(b"\x00" * 1280)
            await q.put(None)
            await asyncio.wait_for(task, 5)
            return msgs, statuses

    msgs, statuses = asyncio.run(main())
    assert received["auth"] == "Token KEY123"
    assert "multichannel=true" in received["path"] and "channels=2" in received["path"]
    assert "keyterm=Kubernetes" in received["path"]
    assert received["bytes"] == 6400 and received["close"]
    assert [m["type"] for m in msgs] == ["Results", "UtteranceEnd"]
    assert statuses == ["recording"]


# ---------------------------------------------------------------- documents
def test_documents(tmp_path, monkeypatch):
    import docx
    from app.documents import DocumentStore
    store = DocumentStore(tmp_path)
    d = docx.Document()
    d.add_paragraph("Jane Cruz - Python developer at Acme, 2 years")
    p = tmp_path / "cv.docx"
    d.save(p)
    store.add_file("cv.docx", p.read_bytes())
    store.add_text("Job description", "We need a backend engineer with FastAPI experience.")
    with pytest.raises(ValueError):
        store.add_file("photo.png", b"123")
    text, trimmed = store.combined()
    assert "Jane Cruz" in text and "FastAPI" in text and not trimmed
    assert len(DocumentStore(tmp_path).list()) == 2  # persisted
    store.remove(store.list()[0]["id"])
    assert len(store.list()) == 1
    import pypdf
    page = types.SimpleNamespace(extract_text=lambda: "Jane\n \nCruz\n \nled  the\nmigration\n\n\n\nEnd")
    monkeypatch.setattr(pypdf, "PdfReader", lambda _: types.SimpleNamespace(pages=[page]))
    store.add_file("cv.pdf", b"%PDF")
    assert "[page 1]\nJane Cruz led the\nmigration\n\nEnd" in store.combined()[0]  # padding gone, text kept
