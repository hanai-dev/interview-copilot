"""How human do the answers sound? Generates real answers (costs ~$0.30 per run) and scores them.

    .venv\\Scripts\\python tests\\bench_human.py [--out answers.md]

Answers 10 real interviewer questions from the docs/ interview (transcript up to that point, your files
uploaded) in the "talking_points" and "full" styles through the app's own Answerer, with the Anthropic
key from .env. Prints AI tells per 100 words last (lower is better): em dashes, semicolons, colon labels,
"not just X but Y", AI-favourite words, stock openers, missing contractions. Also reports, on stderr, a
1-10 "sounds like a real person" rating from a different model (claude-opus-5-5) and how many answers
still contain the key facts from the design doc.
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_tokens as bt  # noqa: E402  (sets up an isolated temp data dir, cleaned up at exit)
from dotenv import dotenv_values  # noqa: E402

KEY = (dotenv_values(bt.ROOT / ".env").get("ANTHROPIC_API_KEY") or "").strip()
os.environ["ANTHROPIC_API_KEY"] = KEY  # environment only; never written to settings.json

from anthropic import AsyncAnthropic  # noqa: E402

from app.core import Core  # noqa: E402

JUDGE_MODEL = "claude-opus-5-5"
STYLES = ("talking_points", "full")
# (text that locates the interviewer's turn, facts from the design doc an answer should mention)
QUESTIONS = [
    ("How was the test?", ["qwen", "opus", "verif", "handwriting", "gemini", "30"]),
    ("how you would label this data set", ["specialist", "label", "golden", "agreement"]),
    ("Labels like what kind of labels", ["misconception", "transcri", "evidence"]),
    ("the check photo block", ["opencv", "align", "retake", "blur", "crop"]),
    ("how exactly does alignment require", ["homograph", "template", "blank", "feature", "warp"]),
    ("the diagnosed block, how does it work", ["qwen", "pack", "misconception", "transcri"]),
    ("How does it scale?", ["crop", "parallel", "linear", "problem"]),
    ("the third block, the validate", ["sympy", "schema", "haiku", "pii"]),
    ("Ever thought of improving this", ["golden", "eval", "feedback", "correction"]),
    ("groups of students", ["misconception", "code", "group", "cluster"]),
]

TELLS = {
    "dash": r"—|–|(?<=\w) - (?=\w)",
    "semicolon": r";",
    "colon": r"(?<!\d):(?!\d)",
    "parenthesis": r"\(",
    "symbol": r"[→≥≤×≈~]|\w/\w",
    "not just": r"\b(?:not|isn't|aren't|wasn't) (?:just|only|simply|merely)\b",
    "ai word": r"\b(?:delve|leverag\w*|robust|seamless\w*|crucial|pivotal|comprehensive|holistic|landscape"
               r"|tapestry|realm|utiliz\w*|facilitat\w*|streamlin\w*|cutting-edge|synerg\w*|paradigm|foster\w*"
               r"|empower\w*|underscor\w*|showcas\w*|testament|nuanced|multifaceted|intricate|meticulous\w*"
               r"|paramount|bespoke|furthermore|moreover|additionally|notably|in summary|in conclusion"
               r"|to summarize|ensur\w*)\b",
    "opener": r"(?im)^\W*(?:great|good|excellent) question|^\W*(?:absolutely|certainly)\b",
    "uncontracted": r"\b(?:I would|I will|I am|it is|that is|do not|does not|did not|is not|are not|cannot"
                    r"|we would|we will|we are|they are|there is|what is|it would|you would)\b",
    # read verbatim these come out as "p 95", "submission underscore id", "8 a m"
    "unspeakable": r"\b\w+_\w+\b|\bp\d{2}\b|\b\d+(?:am|pm|ms|s)\b|\be\.g\.|\bi\.e\.|\bvs\.",
}

JUDGE = """Below is exactly what a job candidate said out loud, word for word, in a live technical interview.

How much does it sound like a real person, rather than text written by an AI model? Think about word choice, \
rhythm, structure and punctuation. 1 = obviously AI-written, 10 = clearly a real person.

Reply with only the number.

<answer>
{answer}
</answer>"""


def tells(text: str) -> dict[str, int]:
    return {name: len(re.findall(rx, text)) for name, rx in TELLS.items()}


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def contexts() -> list[tuple[str, list[str]]]:
    """For each question: the interviewer's full turn and the transcript lines up to and including it."""
    turns = bt.parse_transcript(bt.DEFAULT_TRANSCRIPT)
    lines = [f"{'Interviewer' if s in bt.INTERVIEWER else 'Me'}: {t}" for s, _, t in turns]
    out = []
    for needle, _ in QUESTIONS:
        i = next(i for i, (s, _, t) in enumerate(turns) if s in bt.INTERVIEWER and needle in t)
        history = lines[: i + 1]
        while sum(len(x) + 1 for x in history) > 16000:
            history = history[1:]
        out.append((turns[i][2], history))
    return out


async def generate(core: Core) -> dict[tuple[str, int], str]:
    ctx = contexts()
    answers: dict[tuple[str, int], str] = {}
    for style in STYLES:
        with core.settings._lock:  # not update(): that would save the key into settings.json
            core.settings._values["answer_style"] = style
        await asyncio.gather(*(core.answerer.answer(q, f"{style}|{i}", None, (hist, []), time.perf_counter(), manual=False)
                               for i, (q, hist) in enumerate(ctx)))
        for a in core.hub.state.answers.values():
            s, i = a["question"].split("|")
            if s == style:
                answers[(style, int(i))] = a.get("text") or ""
    return answers


def spoken(text: str) -> str:
    """What the candidate actually says: they read the answer out loud, bullets included, word for word."""
    lines = [re.sub(r"^\s*[-*•]\s*", "", line).replace("**", "").strip() for line in text.splitlines()]
    return " ".join(line if line[-1:] in ".?!" else line + "." for line in lines if line)


async def judge(client: AsyncAnthropic, text: str) -> int:
    r = await client.messages.create(model=JUDGE_MODEL, max_tokens=2000, output_config={"effort": "low"},
                                     messages=[{"role": "user", "content": JUDGE.format(answer=spoken(text))}])
    m = re.search(r"\b(10|[1-9])\b", "".join(getattr(b, "text", "") for b in r.content))
    return int(m.group(1)) if m else 0


async def run(out: Path | None) -> float:
    if not KEY:
        sys.exit("No ANTHROPIC_API_KEY in .env")
    core = Core()
    for p in bt.DEFAULT_DOCS:
        core.docs.add_file(p.name, p.read_bytes())
    answers = await generate(core)
    client = AsyncAnthropic(api_key=KEY, max_retries=2)
    keys = sorted(answers)
    scores = dict(zip(keys, await asyncio.gather(*(judge(client, answers[k]) for k in keys))))

    total_tells: dict[str, int] = {}
    n_words, grounded, report = 0, 0, []
    for style, i in keys:
        text = answers[(style, i)]
        t = tells(text)
        for k, v in t.items():
            total_tells[k] = total_tells.get(k, 0) + v
        n_words += words(text)
        ok = any(f in text.lower() for f in QUESTIONS[i][1])
        grounded += ok
        report.append(f"### {style} | Q{i}: {QUESTIONS[i][0]}\nhuman={scores[(style, i)]} tells={sum(t.values())} "
                      f"facts={'yes' if ok else 'NO'}\n\n{text or '(no answer)'}\n")
    missing = 2 * len(QUESTIONS) - sum(1 for v in answers.values() if v)
    metric = 100 * sum(total_tells.values()) / max(n_words, 1)
    judged = [s for s in scores.values() if s]
    by_style = {s: sum(v for (st, _), v in scores.items() if st == s) / len(QUESTIONS) for s in STYLES}
    first = sorted(a["latency_ms"] for a in core.hub.state.answers.values() if a.get("latency_ms"))
    summary = (f"tells/100w={metric:.2f} human={sum(judged) / max(len(judged), 1):.2f}/10 "
               f"({', '.join(f'{s} {v:.1f}' for s, v in by_style.items())}) "
               f"facts={grounded}/{len(keys)} missing={missing} words/answer={n_words // max(len(keys), 1)} "
               f"first-words median={first[len(first) // 2] if first else 0}ms "
               f"by kind={ {k: v for k, v in total_tells.items() if v} }")
    print(summary, file=sys.stderr)
    if out:
        out.write_text(summary + "\n\n" + "\n".join(report), encoding="utf-8")
    return metric


def main() -> None:
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None
    print(f"{asyncio.run(run(out)):.3f}")


if __name__ == "__main__":
    main()
