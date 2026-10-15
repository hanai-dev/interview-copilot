"""Token-cost benchmark: replays a real interview through the real pipeline and prices every Claude call.

    .venv\\Scripts\\python tests\\bench_tokens.py [transcript.txt] [doc.pdf ...]

Uses an Otter-style transcript ("Speaker N  MM:SS" then the text) with its real timestamps, uploads the
documents through DocumentStore, answers through Answerer/LLM with a mocked Anthropic API, then bills each
request with Anthropic prompt-cache rules (prefix match per block, 20-block lookback, 512-token minimum,
5 min / 1 h TTL, reads 0.1x, writes 1.25x / 2x). Prints the simulated interview cost in milli-dollars last.
Thinking tokens can't be simulated and are left out; output is a fixed ~80-word answer per call.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["COPILOT_DATA_DIR"] = tempfile.mkdtemp(prefix="copilot-bench-")
for k in ("DEEPGRAM_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
    os.environ[k] = ""
sys.path.insert(0, str(ROOT))

import httpx2  # noqa: E402
from anthropic import AsyncAnthropic  # noqa: E402

from app.core import Core, Session  # noqa: E402

DOCS = ROOT / "docs"
DEFAULT_TRANSCRIPT = DOCS / "AI Student Work Analysis Technical Review_transcript.txt"
DEFAULT_DOCS = [DOCS / "EdLight HoE Take-Home Challenge.pdf", DOCS / "EdLight-AI-Insights-Technical-Design.pdf"]
ME, INTERVIEWER = {"Speaker 1"}, {"Speaker 5", "Speaker 6"}  # others are pre-call chatter, not on the call

PRICES = {"claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50)}  # $/MTok in, out
MIN_CACHE, LOOKBACK = 512, 20
ANSWER = ("**I'd label each submission with the expected insight plus slice metadata.**\n"
          "- Two specialists label a calibration batch first, measure agreement\n"
          "- Fix the codebook where agreement is poor, then label the rest\n"
          "- Metadata: grade, unit, lesson, problem, codebook version, real vs planted\n"
          "- Use it as the golden set gate before any prompt or model change")

# Offline token estimate: regex word pieces x 1.5, calibrated against claude-sonnet-5-5 count_tokens
# (within ~15% on prose, transcripts and PDF text; tracks whitespace-heavy text where chars/4 doesn't).
_PIECES = re.compile(r"""'(?:s|t|re|ve|m|ll|d)| ?[^\W\d_]+| ?\d{1,3}| ?[^\s\w]+|\s+(?!\S)|\s+""")


def tokens(text: str) -> int:
    n = 0
    for m in _PIECES.findall(text):
        w = m.strip()
        n += 1 + (max(0, len(w) - 7) // 5 if w.isalpha() else 0)
    return round(n * 1.5)


# ---------------------------------------------------------------- transcript replay
def parse_transcript(path: Path) -> list[tuple[str, float, str]]:
    turns, cur = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(Speaker \d+)\s+(\d+):(\d+)\s*$", line)
        if m:
            cur = [m.group(1), int(m.group(2)) * 60 + int(m.group(3)), []]
            turns.append(cur)
        elif cur and line.strip() and not line.startswith("Transcribed by"):
            cur[2].append(line.strip())
    out = [(s, t, " ".join(x)) for s, t, x in turns if " ".join(x)]
    first = next(i for i, (s, _, _) in enumerate(out) if s in INTERVIEWER)
    return [x for x in out[first:] if x[0] in ME | INTERVIEWER]


def result(ch: int, text: str) -> dict:
    return {"type": "Results", "channel_index": [ch, 2], "is_final": True, "speech_final": True,
            "channel": {"alternatives": [{"transcript": text, "confidence": 0.95, "words": []}]}}


# ---------------------------------------------------------------- mocked Anthropic API
class Recorder:
    def __init__(self):
        self.now = 0.0
        self.calls: list[tuple[float, dict]] = []

    def handler(self, request):
        body = json.loads(request.content)
        self.calls.append((self.now, body))
        if body.get("stream"):
            return httpx2.Response(200, text=_sse(body["model"], ANSWER), headers={"content-type": "text/event-stream"})
        turn = body["messages"][-1]["content"]
        turn = turn if isinstance(turn, str) else "".join(b["text"] for b in turn)
        latest = turn.rsplit("latest turn:", 1)[-1]
        verdict = {"needs_answer": len(latest.split()) >= 8, "question": latest.strip()[:200]}
        return httpx2.Response(200, json={
            "id": "m", "type": "message", "role": "assistant", "model": body["model"],
            "content": [{"type": "text", "text": json.dumps(verdict)}], "stop_reason": "end_turn",
            "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}})


def _sse(model: str, text: str) -> str:
    ev = [
        ("message_start", {"type": "message_start", "message": {"id": "m", "type": "message", "role": "assistant", "model": model, "content": [], "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}}),
        ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
        ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 1}}),
        ("message_stop", {"type": "message_stop"}),
    ]
    return "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" for e, d in ev)


async def replay(transcript: Path, docs: list[Path]) -> Recorder:
    core = Core()
    core.settings.update({"provider": "claude", "anthropic_api_key": "sk-bench"})
    rec = Recorder()
    core.llm._clients[("claude", "sk-bench")] = AsyncAnthropic(
        api_key="sk-bench", max_retries=0, http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(rec.handler)))
    for p in docs:
        core.docs.add_file(p.name, p.read_bytes())
    session = Session(core)
    turns = parse_transcript(transcript)
    for i, (spk, start, text) in enumerate(turns):
        end = turns[i + 1][1] if i + 1 < len(turns) else start + len(text.split()) * 0.4
        ch = 1 if spk in INTERVIEWER else 0
        chunks = re.findall(r"[^.?!]+[.?!]*", text)
        total = sum(len(c.split()) for c in chunks) or 1
        said = 0
        for c in chunks:  # Deepgram finalizes phrase by phrase; a question mark can end a turn early
            said += len(c.split())
            rec.now = start + (end - start) * said / total
            session.aggregator.handle(result(ch, c.strip()))
            await _drain(core)
        session.aggregator.handle({"type": "UtteranceEnd", "channel": [ch, 2], "last_word_end": 0})
        await _drain(core)
    return rec


async def _drain(core: Core) -> None:
    while core.answerer._tasks:
        await asyncio.gather(*list(core.answerer._tasks))


# ---------------------------------------------------------------- Anthropic billing with prompt caching
def blocks(body: dict) -> list[tuple[str, dict | None]]:
    out = []
    system = body.get("system") or []
    for b in ([{"text": system}] if isinstance(system, str) else system):
        out.append((b["text"], b.get("cache_control")))
    for m in body["messages"]:
        content = m["content"]
        for b in ([{"text": content}] if isinstance(content, str) else content):
            out.append((m["role"] + ":" + b["text"], b.get("cache_control")))
    if body.get("cache_control") and out:  # top-level automatic caching marks the last block
        out[-1] = (out[-1][0], out[-1][1] or body["cache_control"])
    return out


def bill(calls: list[tuple[float, dict]]) -> dict:
    cache: dict[str, tuple[float, float]] = {}  # prefix hash -> (expires_at, ttl)
    tot = {"usd": 0.0, "uncached": 0, "read": 0, "write": 0, "output": 0, "answers": 0, "checks": 0}
    for now, body in calls:
        model = body["model"]
        p_in, p_out = PRICES[model]
        ns = json.dumps([model, body.get("output_config"), body.get("thinking")], sort_keys=True)
        h, cum, hashes, bps, size = hashlib.sha256(ns.encode()), 0, [], [], 0
        for i, (text, cc) in enumerate(blocks(body)):
            h.update(text.encode() + b"\x00")
            cum += tokens(text)
            hashes.append((h.hexdigest(), cum))
            if cc:
                bps.append((i, 3600.0 if cc.get("ttl") == "1h" else 300.0))
        size = cum
        covered = 0
        for i, _ in bps:  # each breakpoint looks back up to 20 blocks for a live entry
            for j in range(i, max(-1, i - LOOKBACK), -1):
                key, upto = hashes[j]
                if key in cache and cache[key][0] > now:
                    cache[key] = (now + cache[key][1], cache[key][1])
                    covered = max(covered, upto)
                    break
        read, w5, w1 = covered, 0, 0
        for i, ttl in bps:
            key, upto = hashes[i]
            if upto > covered and upto >= MIN_CACHE:
                if ttl > 300:
                    w1 += upto - covered
                else:
                    w5 += upto - covered
                covered = upto
                cache[key] = (now + ttl, ttl)
        uncached = size - covered
        out = tokens(ANSWER) if body.get("stream") else 25
        tot["usd"] += (p_in * (uncached + 0.1 * read + 1.25 * w5 + 2 * w1) + p_out * out) / 1e6
        tot["uncached"] += uncached
        tot["read"] += read
        tot["write"] += w5 + w1
        tot["output"] += out
        tot["answers" if body.get("stream") else "checks"] += 1
    return tot


def _selftest() -> None:
    sys_ = [{"type": "text", "text": "word " * 600, "cache_control": {"type": "ephemeral"}}]
    req = lambda q: {"model": "claude-sonnet-5-5", "system": sys_, "messages": [{"role": "user", "content": q}]}
    one, two = bill([(0, req("a"))]), bill([(0, req("a")), (10, req("b"))])
    assert one["write"] > 0 and one["read"] == 0
    assert two["read"] == one["write"], "second request must read the cached system prompt"
    assert bill([(0, req("a")), (400, req("b"))])["read"] == 0, "5-minute entries expire"
    small = [{"type": "text", "text": "hi", "cache_control": {"type": "ephemeral"}}]
    assert bill([(0, {"model": "claude-sonnet-5-5", "system": small, "messages": [{"role": "user", "content": "q"}]})])["write"] == 0


def main() -> None:
    _selftest()
    args = [Path(a) for a in sys.argv[1:]]
    transcript = args[0] if args else DEFAULT_TRANSCRIPT
    docs = args[1:] or DEFAULT_DOCS
    rec = asyncio.run(replay(transcript, docs))
    t = bill(rec.calls)
    print(f"answers={t['answers']} checks={t['checks']} input: uncached={t['uncached']} read={t['read']} "
          f"write={t['write']} output={t['output']} -> ${t['usd']:.4f}", file=sys.stderr)
    print(f"{t['usd'] * 1000:.3f}")


if __name__ == "__main__":
    main()
