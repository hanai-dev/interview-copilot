"""Demo mode: plays a scripted interview through the same pipeline, no microphone or Deepgram needed.

Useful to check the UI and your AI key before a real session.
"""
from __future__ import annotations

import asyncio
import random
from typing import Callable

# (channel, text, pause after)  channel 0 = me, 1 = interviewer
SCRIPT = [
    (1, "Hi, thanks for joining today. Can you hear me okay?", 0.8),
    (0, "Yes, I can hear you clearly. Thanks for having me.", 1.0),
    (1, "Great. So to start, tell me a little about yourself and what drew you to this role.", 7.0),
    (0, "Sure. I'm a computer science student and I've been building web apps for about two years.", 1.5),
    (1, "Nice. Can you describe a time you had to deliver a project under a really tight deadline?", 7.0),
    (0, "Yes, last semester our team had two weeks to ship a working prototype.", 1.5),
    (1, "Okay, that's good to hear. Our team works mostly in Python and React day to day.", 2.5),
    (1, "What's the difference between a process and a thread?", 7.0),
    (1, "Last one from me. Where do you see yourself in five years?", 7.0),
]

WORD_S = 0.13
SILENCE_S = 1.0  # like Deepgram's utterance_end_ms


def _result(ch: int, text: str, final: bool, speech_final: bool = False) -> dict:
    return {
        "type": "Results",
        "channel_index": [ch, 2],
        "is_final": final,
        "speech_final": speech_final,
        "channel": {"alternatives": [{"transcript": text, "confidence": 0.98, "words": []}]},
    }


async def run_demo(handle: Callable[[dict], None], levels: Callable[[float, float], None]) -> None:
    for ch, text, pause in SCRIPT:
        words = text.split()
        for i in range(1, len(words) + 1):
            handle(_result(ch, " ".join(words[:i]), final=False))
            a = random.uniform(0.45, 0.8)
            levels(a if ch == 0 else 0.05, a if ch == 1 else 0.05)
            await asyncio.sleep(WORD_S)
        handle(_result(ch, text, final=True, speech_final=True))
        levels(0.0, 0.0)
        await asyncio.sleep(SILENCE_S)
        handle({"type": "UtteranceEnd", "channel": [ch, 2], "last_word_end": 0})
        await asyncio.sleep(pause)


DEMO_ANSWER = (
    "**Demo answer: add an Anthropic or OpenAI API key in Settings to get real answers.**\n"
    "- Answers stream in here, word by word, as soon as a question is detected\n"
    "- They're built from your uploaded files (CV, job post, notes)\n"
    "- Use **Answer now** to force an answer, or type your own question below"
)
