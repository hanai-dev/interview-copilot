"""Switchable AI provider: Claude (Anthropic API) or ChatGPT (OpenAI API), with streaming."""
from __future__ import annotations

import json
import re
from typing import AsyncIterator

from .config import Settings


class LLMError(RuntimeError):
    pass


class LLM:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._clients: dict[tuple[str, str], object] = {}

    # -- clients -------------------------------------------------------
    def provider(self) -> str:
        return self.settings.get("provider") or "claude"

    def has_key(self) -> bool:
        return bool(self.settings.answer_key())

    def model(self, kind: str) -> str:
        """kind: 'answer' or 'fast'"""
        return self.settings.get(f"{self.provider()}_{kind}_model") or ""

    def _client(self):
        provider, key = self.provider(), self.settings.answer_key()
        if not key:
            name = "Anthropic" if provider == "claude" else "OpenAI"
            raise LLMError(f"No {name} API key set. Add it in Settings.")
        cache_key = (provider, key)
        if cache_key not in self._clients:
            if provider == "claude":
                from anthropic import AsyncAnthropic
                self._clients[cache_key] = AsyncAnthropic(api_key=key, max_retries=1, timeout=60)
            else:
                from openai import AsyncOpenAI
                self._clients[cache_key] = AsyncOpenAI(api_key=key, max_retries=1, timeout=60)
        return self._clients[cache_key]

    def _claude_extra(self) -> dict:
        # Lower effort = less thinking before the first word appears, which matters live.
        # Sent via extra_body so it works across Anthropic SDK versions.
        effort = (self.settings.get("claude_effort") or "").strip()
        return {"extra_body": {"output_config": {"effort": effort}}} if effort else {}

    # -- streaming answer ---------------------------------------------
    async def stream(self, instructions: str, docs: str, user: str, max_tokens: int = 700) -> AsyncIterator[str]:
        client = self._client()
        model = self.model("answer")
        try:
            if self.provider() == "claude":
                system = [
                    {"type": "text", "text": instructions},
                    # The documents rarely change during an interview: cache them so each
                    # answer starts faster and costs less.
                    {"type": "text", "text": docs, "cache_control": {"type": "ephemeral"}},
                ]
                async with client.messages.stream(
                    model=model, max_tokens=max_tokens * 3, system=system,
                    messages=[{"role": "user", "content": user}],
                    **self._claude_extra(),
                ) as s:
                    async for text in s.text_stream:
                        yield text
            else:
                async for text in self._openai_stream(client, model, instructions + "\n\n" + docs, user, max_tokens):
                    yield text
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(_friendly(e)) from e

    async def _openai_stream(self, client, model: str, system: str, user: str, max_tokens: int):
        kwargs = dict(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            stream=True,
            # reasoning models count thinking tokens here too, so leave headroom
            max_completion_tokens=max_tokens * 3,
        )
        effort = (self.settings.get("openai_reasoning_effort") or "").strip()
        if effort:
            kwargs["reasoning_effort"] = effort
        try:
            stream = await client.chat.completions.create(**kwargs)
        except Exception as e:
            if effort and "reasoning" in str(e).lower():
                kwargs.pop("reasoning_effort", None)
                stream = await client.chat.completions.create(**kwargs)
            else:
                raise
        async for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

    # -- short completion (question detector) --------------------------
    async def complete(self, system: str, user: str, max_tokens: int = 150) -> str:
        client = self._client()
        model = self.model("fast")
        try:
            if self.provider() == "claude":
                resp = await client.messages.create(
                    model=model, max_tokens=max_tokens * 4, system=system,
                    messages=[{"role": "user", "content": user}],
                    **self._claude_extra(),
                )
                return "".join(getattr(b, "text", "") for b in resp.content)
            out = []
            async for t in self._openai_stream(client, model, system, user, max_tokens):
                out.append(t)
            return "".join(out)
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(_friendly(e)) from e


def parse_json_object(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except ValueError:
        return {}


def _friendly(e: Exception) -> str:
    msg = str(e)
    low = msg.lower()
    status = getattr(e, "status_code", None)
    if status in (401, 403) or "authentication" in low or "invalid x-api-key" in low or "incorrect api key" in low:
        return "The AI provider rejected the API key. Check it in Settings."
    if status == 404 or "model_not_found" in low or ("model" in low and "not found" in low):
        return f"Model not found. Check the model name in Settings. ({msg[:160]})"
    if status == 429 or "rate limit" in low:
        return "Rate limited by the AI provider. Wait a moment and try again."
    if "credit" in low or "quota" in low or "billing" in low:
        return "The AI provider account is out of credit."
    return msg[:300] or e.__class__.__name__
