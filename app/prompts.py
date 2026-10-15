"""Prompts for the question detector and the answer agent."""
from __future__ import annotations

import re

STYLE_RULES = {
    "talking_points": (
        "Format: first line is a one-sentence headline answer in **bold**. Then 3-5 short bullet "
        "points (each under 15 words) the candidate can glance at while speaking. About 80 words total."
    ),
    "full": (
        "Format: a natural spoken answer in first person that the candidate could say almost word for "
        "word. 120-180 words, short paragraphs, no headings."
    ),
    "short": "Format: 2-3 sentences in first person. No lists.",
}

ANSWER_SYSTEM = """You are a real-time interview assistant. The person you help ("Me") is the one being interviewed, live, right now. You see a live transcript where "Interviewer" is the other person and "Me" is the person you help.

When the interviewer asks something, write what Me can say in reply. Speed and clarity matter more than polish: Me will read your answer at a glance while talking.

Rules:
- Write in first person, as Me, in a natural spoken tone.
- Ground answers in Me's documents below (CV, job description, notes, course material). Use real names, projects, numbers and facts from them.
- Never invent experience, employers, numbers or facts about Me. If the documents don't cover it, give a strong structure with clear placeholders like [your example].
- Behavioral questions ("tell me about a time..."): use STAR (Situation, Task, Action, Result), compressed into the format below.
- Technical questions: lead with the correct core answer, then key details. Include a tiny code snippet only if it is essential.
- If the question is unclear or only partly heard, answer the most likely intended question.
- Reply in the same language the interviewer is using.
- If the interviewer's latest turn does not actually need a prepared answer (small talk, "can you hear me?", logistics, the interviewer just making a statement or giving feedback), reply with exactly: NO_ANSWER
{style}{extra}"""

DOCS_BLOCK = """<my_documents>
{docs}
</my_documents>"""

NO_DOCS = "<my_documents>(none uploaded)</my_documents>"

ANSWER_USER = """Live transcript so far (most recent last):
{transcript}

The interviewer's latest turn:
"{question}"

Write Me's answer now."""

ANSWER_USER_MANUAL = """Live transcript so far (most recent last):
{transcript}

Me needs help with this right now:
"{question}"

Answer it (do not reply NO_ANSWER)."""

DETECT_SYSTEM = """You monitor a live interview transcript. Decide whether the interviewer's latest turn asks the person being interviewed ("Me") something that deserves a prepared answer: a question, or a request like "tell me about...", "walk me through...", "describe...".

It does NOT need an answer if it is: a greeting, small talk, an audio check ("can you hear me?"), scheduling/logistics, the interviewer talking about the company or role without asking anything, feedback like "great, thanks", or a sentence that was cut off before any question.

Reply with ONLY a JSON object, no other text:
{"needs_answer": true or false, "question": "the question restated in one clear sentence, or empty"}"""

DETECT_USER = """Recent transcript:
{transcript}

Interviewer's latest turn:
"{turn}\""""

_ASK_PHRASES = (
    "tell me", "tell us", "walk me", "walk us", "talk me through", "talk us through", "describe",
    "explain", "give me an example", "give us an example", "share an example", "talk about",
    "what would you", "how would you", "why should", "why do you", "how do you", "what do you",
    "can you", "could you", "would you", "have you", "do you",
)
_SMALL_TALK = re.compile(
    r"\b(can|could) you (hear|see) me\b|\b(is|are) (my|the) (audio|video|mic|sound|screen)\b"
    r"|\bhow are you( doing)?( today)?\b|\bhow's it going\b|\bcan you see my screen\b",
    re.I,
)
SMALL_TALK_MAX_WORDS = 14  # only treat it as small talk when nothing else much was said


def quick_classify(text: str) -> str:
    """Cheap first pass before calling a model. Returns "yes", "no" or "maybe"."""
    t = " ".join(text.lower().split())
    words = re.findall(r"[a-z']+", t)
    if not words:
        return "no"
    if _SMALL_TALK.search(t) and len(words) <= SMALL_TALK_MAX_WORDS:
        return "no"
    if "?" in t:
        return "yes"
    if any(p in t for p in _ASK_PHRASES) and len(words) >= 4:
        return "yes"
    if len(words) < 5:
        return "no"
    return "maybe"  # longer statement without a clear question mark: let the fast model decide


def answer_system(style: str, extra: str) -> str:
    rules = STYLE_RULES.get(style, STYLE_RULES["talking_points"])
    extra = extra.strip()
    return ANSWER_SYSTEM.format(
        style=rules,
        extra=f"\n\nExtra instructions from Me:\n{extra}" if extra else "",
    )


def docs_block(docs: str) -> str:
    return DOCS_BLOCK.format(docs=docs) if docs.strip() else NO_DOCS
