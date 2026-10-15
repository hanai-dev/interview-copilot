"""End-to-end: web app + demo interview + question detection + streamed answers (AI mocked)."""
import json
import time

from fastapi.testclient import TestClient

from app import demo, server


class FakeLLM:
    def __init__(self):
        self.answer_calls, self.detect_calls = [], []

    def provider(self):
        return "claude"

    def model(self, kind):
        return f"fake-{kind}"

    def has_key(self):
        return True

    async def complete(self, system, user, max_tokens=150):
        self.detect_calls.append(user)
        return '{"needs_answer": false, "question": ""}'

    async def stream(self, instructions, docs, user, max_tokens=700):
        self.answer_calls.append((instructions, docs, user))
        latest = user.split("latest turn:")[-1]
        if "process and a thread" in latest and "do not reply NO_ANSWER" not in user:
            for part in ["NO_", "ANSWER"]:
                yield part
            return
        for part in ["**I build web apps", " with Python.**\n", "- Point one\n", "- Point two"]:
            yield part


def collect(ws, until, timeout=20):
    events, end = [], time.time() + timeout
    while time.time() < end:
        ev = ws.receive_json()
        events.append(ev)
        if until(ev):
            return events
    raise AssertionError("timed out")


def test_demo_interview_end_to_end(monkeypatch):
    monkeypatch.setattr(demo, "WORD_S", 0.002)
    monkeypatch.setattr(demo, "SILENCE_S", 0.05)
    monkeypatch.setattr(demo, "SCRIPT", [(ch, text, 0.3) for ch, text, _ in demo.SCRIPT])
    fake = FakeLLM()
    monkeypatch.setattr(server.core, "llm", fake)

    with TestClient(server.app) as client:
        assert client.get("/").status_code == 200
        r = client.post("/api/docs/text", json={"name": "CV", "text": "Jane Cruz, Python developer"})
        assert r.json()["docs"][0]["name"] == "CV"

        with client.websocket_connect("/ws") as ws:
            snap = ws.receive_json()
            assert snap["type"] == "snapshot" and snap["status"]["state"] == "idle"
            assert client.post("/api/start", json={"demo": True}).status_code == 200
            events = collect(ws, lambda e: e["type"] == "saved")

        turns = {}
        for e in events:
            if e["type"] == "turn":
                turns[e["turn"]["id"]] = e["turn"]
        speakers = [t["speaker"] for t in turns.values()]
        assert speakers == ["interviewer", "me", "interviewer", "me", "interviewer", "me",
                            "interviewer", "interviewer", "interviewer"]

        det = {}
        for e in events:
            if e["type"] == "detector":
                det[e["turn_id"]] = e["result"]
        by_text = {turns[i]["final"][:20]: r for i, r in det.items()}
        assert by_text["Hi, thanks for joini"] == "skip"           # audio check -> no answer
        assert by_text["Great. So to start, "] == "question"       # tell me about yourself
        assert by_text["Okay, that's good to"] == "skip"           # statement -> fast model said no
        assert by_text["What's the differenc"] == "skip"           # answer model replied NO_ANSWER
        assert by_text["Last one from me. Wh"] == "question"

        starts = [e["answer"] for e in events if e["type"] == "answer_start"]
        assert len(starts) == 3  # yourself, deadline, five years
        a0 = starts[0]["id"]
        text = "".join(e["text"] for e in events if e["type"] == "answer_delta" and e["id"] == a0)
        assert text.startswith("**I build web apps with Python.**")
        assert len(fake.detect_calls) == 1
        # the answer prompt includes the uploaded file and the transcript so far
        instructions, docs, user = fake.answer_calls[0]
        assert "Jane Cruz" in docs and "Interviewer: Great. So to start" in user
        assert not any(e["type"] == "answer_start" and "NO_ANSWER" in json.dumps(e) for e in events)

        # Manual "Answer now" after the session uses the latest interviewer turn, forced
        with client.websocket_connect("/ws") as ws:
            snap = ws.receive_json()
            assert len(snap["answers"]) == 3 and snap["status"]["state"] == "idle"
            assert client.post("/api/answer", json={}).status_code == 200
            ev = collect(ws, lambda e: e["type"] == "answer_done")
            start = next(e for e in ev if e["type"] == "answer_start")
            assert start["answer"]["manual"] is True and "five years" in start["answer"]["question"]

        # Typed question
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
            client.post("/api/answer", json={"question": "Explain process vs thread"})
            ev = collect(ws, lambda e: e["type"] == "answer_done")
            assert any(e["type"] == "answer_start" for e in ev)


def test_settings_and_errors():
    with TestClient(server.app) as client:
        info = client.post("/api/settings", json={
            "provider": "openai", "answer_style": "full", "anthropic_api_key": "sk-ant-x",
            "mic_device": "", "auto_answer": False, "font_scale": 9}).json()
        s = info["settings"]
        assert s["provider"] == "openai" and s["answer_style"] == "full" and s["font_scale"] == 2.0
        assert s["keys"]["anthropic_api_key"] is True and "anthropic_api_key" not in s
        # blank key in a later save keeps the stored key
        info = client.post("/api/settings", json={"anthropic_api_key": ""}).json()
        assert info["settings"]["keys"]["anthropic_api_key"] is True
        client.post("/api/settings", json={"provider": "claude", "auto_answer": True})

        # Real recording without a Deepgram key gives a clear message
        r = client.post("/api/start", json={"demo": False})
        assert r.status_code == 400 and "Deepgram" in r.json()["detail"]
        # Devices endpoint degrades gracefully off Windows
        d = client.get("/api/devices").json()
        assert d["available"] in (True, False)
        # Bad upload
        r = client.post("/api/docs", files=[("files", ("x.png", b"123", "image/png"))]).json()
        assert r["errors"] and not r["added"]
