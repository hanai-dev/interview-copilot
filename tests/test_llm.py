"""Checks the exact requests sent to Anthropic / OpenAI, using fake HTTP servers (no keys needed)."""
import asyncio
import json

import httpx

try:  # newer Anthropic SDKs use httpx2
    import httpx2 as ahttpx
except ImportError:  # older SDKs use httpx
    ahttpx = httpx

from app.config import Settings
from app.llm import LLM, LLMError


def sse(events):
    return "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" if e else f"data: {d if isinstance(d, str) else json.dumps(d)}\n\n"
                   for e, d in events)


ANTHROPIC_STREAM = sse([
    ("message_start", {"type": "message_start", "message": {"id": "m1", "type": "message", "role": "assistant", "model": "claude-sonnet-5-5", "content": [], "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": 10, "output_tokens": 1}}}),
    ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
    ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "**Hello"}}),
    ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": " there.**"}}),
    ("content_block_stop", {"type": "content_block_stop", "index": 0}),
    ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 5}}),
    ("message_stop", {"type": "message_stop"}),
])


def make_settings(tmp_path, **kw):
    s = Settings(tmp_path / "settings.json")
    s.update(kw)
    return s


def test_claude_stream_request(tmp_path):
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        seen["key"] = request.headers.get("x-api-key")
        return ahttpx.Response(200, text=ANTHROPIC_STREAM, headers={"content-type": "text/event-stream"})

    settings = make_settings(tmp_path, provider="claude", anthropic_api_key="sk-ant-test")
    llm = LLM(settings)
    from anthropic import AsyncAnthropic
    llm._clients[("claude", "sk-ant-test")] = AsyncAnthropic(
        api_key="sk-ant-test", http_client=ahttpx.AsyncClient(transport=ahttpx.MockTransport(handler)))

    async def run():
        return "".join([t async for t in llm.stream("INSTR", "<my_documents>CV</my_documents>", "Q?",
                                                    ["Head:", "Interviewer: Hi"])])

    assert asyncio.run(run()) == "**Hello there.**"
    b = seen["body"]
    assert seen["key"] == "sk-ant-test"
    assert b["model"] == "claude-sonnet-5-5" and b["stream"] is True
    assert b["output_config"] == {"effort": "low"}
    assert b["system"][1]["cache_control"] == {"type": "ephemeral"} and "CV" in b["system"][1]["text"]
    # finished transcript lines: one block each, cached up to the last one; the live part after it
    assert b["messages"] == [{"role": "user", "content": [
        {"type": "text", "text": "Head:\n"},
        {"type": "text", "text": "Interviewer: Hi\n", "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": "Q?"},
    ]}]


def test_openai_stream_retries_without_reasoning_effort(tmp_path):
    calls = []

    def handler(request: httpx.Request):
        body = json.loads(request.content)
        calls.append(body)
        if "reasoning_effort" in body:
            return httpx.Response(400, json={"error": {"message": "Unsupported parameter: 'reasoning_effort'", "type": "invalid_request_error", "param": "reasoning_effort", "code": None}})
        chunks = [
            {"id": "c", "object": "chat.completion.chunk", "created": 1, "model": body["model"], "choices": [{"index": 0, "delta": {"role": "assistant", "content": "Hi"}, "finish_reason": None}]},
            {"id": "c", "object": "chat.completion.chunk", "created": 1, "model": body["model"], "choices": [{"index": 0, "delta": {"content": " you"}, "finish_reason": "stop"}]},
        ]
        text = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
        return httpx.Response(200, text=text, headers={"content-type": "text/event-stream"})

    settings = make_settings(tmp_path, provider="openai", openai_api_key="sk-test")
    llm = LLM(settings)
    from openai import AsyncOpenAI
    llm._clients[("openai", "sk-test")] = AsyncOpenAI(
        api_key="sk-test", max_retries=0, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    async def run():
        return "".join([t async for t in llm.stream("INSTR", "DOCS", "Q?", ["Head:", "Me: Hi"])])

    assert asyncio.run(run()) == "Hi you"
    assert calls[0]["reasoning_effort"] == "low" and "reasoning_effort" not in calls[1]
    assert calls[1]["messages"][0] == {"role": "system", "content": "INSTR\n\nDOCS"}
    assert calls[1]["messages"][1] == {"role": "user", "content": "Head:\nMe: Hi\nQ?"}
    assert calls[1]["model"] == "gpt-6.1-sol"


def test_bad_key_message(tmp_path):
    def handler(request):
        return ahttpx.Response(401, json={"type": "error", "error": {"type": "authentication_error", "message": "invalid x-api-key"}})

    settings = make_settings(tmp_path, provider="claude", anthropic_api_key="bad")
    llm = LLM(settings)
    from anthropic import AsyncAnthropic
    llm._clients[("claude", "bad")] = AsyncAnthropic(
        api_key="bad", max_retries=0, http_client=ahttpx.AsyncClient(transport=ahttpx.MockTransport(handler)))

    async def run():
        try:
            await llm.complete("s", "u")
        except LLMError as e:
            return str(e)

    assert "rejected the API key" in asyncio.run(run())


def test_missing_key(tmp_path):
    llm = LLM(make_settings(tmp_path, provider="openai"))

    async def run():
        try:
            async for _ in llm.stream("a", "b", "c"):
                pass
        except LLMError as e:
            return str(e)

    assert "No OpenAI API key" in asyncio.run(run())
