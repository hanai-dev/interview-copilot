"""Turns live Deepgram results into labeled speaker turns ("Me" / "Interviewer").

Rules:
- Channel 0 (mic) is "me", channel 1 (PC speakers) is "interviewer".
- A turn grows while the speaker keeps talking and closes when Deepgram reports ~1 s of
  silence on that channel (UtteranceEnd) or when the other person starts speaking.
- If you use speakers instead of headphones, your mic also hears the interviewer. Those
  "echo" lines on the mic channel are detected and dropped so they aren't labeled as you.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Callable, Optional

SPEAKERS = {0: "me", 1: "interviewer"}
OTHER = {"me": "interviewer", "interviewer": "me"}
ECHO_WINDOW_S = 12.0
ECHO_MIN_WORDS = 3
ECHO_THRESHOLD = 0.6


@dataclass
class Turn:
    id: int
    speaker: str
    started: float
    finals: list[str] = field(default_factory=list)
    interim: str = ""
    closed: bool = False
    ended: float = 0.0
    answered_words: int = 0  # word count when an answer was last triggered for this turn

    @property
    def final_text(self) -> str:
        return " ".join(self.finals).strip()

    @property
    def text(self) -> str:
        return " ".join([*self.finals, self.interim]).strip()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "speaker": self.speaker,
            "final": self.final_text,
            "interim": self.interim,
            "closed": self.closed,
            "started": self.started,
        }


def _words(text: str) -> list[str]:
    return [w.strip(".,!?;:\"'()").lower() for w in text.split() if w.strip(".,!?;:\"'()")]


class Aggregator:
    def __init__(
        self,
        emit: Callable[[dict], None],
        on_interviewer_turn: Callable[[Turn, str], None],
        clock: Callable[[], float] = time.time,
    ):
        self.emit = emit
        self.on_interviewer_turn = on_interviewer_turn
        self.clock = clock
        self.turns: list[Turn] = []
        self.open: dict[str, Optional[Turn]] = {"me": None, "interviewer": None}
        self._recent: dict[str, list[tuple[float, str]]] = {"me": [], "interviewer": []}
        self._next_id = 1
        self.echo_count = 0
        self._echo_warned = False

    # -- public --------------------------------------------------------
    def handle(self, msg: dict) -> None:
        kind = msg.get("type")
        if kind == "Results":
            self._on_results(msg)
        elif kind == "UtteranceEnd":
            ch = (msg.get("channel") or [None])[0]
            if ch in SPEAKERS:
                self._close(SPEAKERS[ch], "utterance_end")

    def flush(self) -> None:
        """Close any open turns (used when recording stops)."""
        for spk in ("interviewer", "me"):
            self._close(spk, "stopped")

    def latest_interviewer_turn(self) -> Optional[Turn]:
        for t in reversed(self.turns):
            if t.speaker == "interviewer" and t.text:
                return t
        return None

    def transcript(self, max_chars: int = 12000) -> str:
        lines: list[str] = []
        total = 0
        for t in reversed(self.turns):
            text = t.text
            if not text:
                continue
            line = f"{'Interviewer' if t.speaker == 'interviewer' else 'Me'}: {text}"
            if total + len(line) > max_chars and lines:
                break
            lines.append(line)
            total += len(line) + 1
        return "\n".join(reversed(lines))

    # -- internals -----------------------------------------------------
    def _is_echo(self, speaker: str, text: str) -> bool:
        """Mic picked up the interviewer through the speakers?"""
        if speaker != "me":
            return False
        words = _words(text)
        if len(words) < ECHO_MIN_WORDS:
            return False
        now = self.clock()
        recent = [w for ts, s in self._recent["interviewer"] if now - ts <= ECHO_WINDOW_S for w in _words(s)]
        current = self.open["interviewer"]
        if current is not None:
            recent += _words(current.text)
        if not recent:
            return False
        sm = SequenceMatcher(None, words, recent, autojunk=False)
        matched = sum(b.size for b in sm.get_matching_blocks())
        return matched / len(words) >= ECHO_THRESHOLD

    def _on_results(self, msg: dict) -> None:
        ch = (msg.get("channel_index") or [0])[0]
        speaker = SPEAKERS.get(ch)
        if speaker is None:
            return
        try:
            text = (msg["channel"]["alternatives"][0].get("transcript") or "").strip()
        except (KeyError, IndexError, TypeError):
            return
        is_final = bool(msg.get("is_final"))
        speech_final = bool(msg.get("speech_final"))

        if text and self._is_echo(speaker, text):
            if is_final:
                self.echo_count += 1
                if self.echo_count >= 3 and not self._echo_warned:
                    self._echo_warned = True
                    self.emit({"type": "notice", "level": "warn",
                               "message": "Your mic is picking up the interviewer's voice from your speakers. "
                                          "Echo lines are being filtered, but headphones work best."})
            turn = self.open[speaker]
            if turn is not None and is_final:
                turn.interim = ""
                if not turn.finals:
                    self._discard(turn)
                else:
                    self._emit_turn(turn)
            return

        # Hand-over: the other person was talking and this person just said something substantial
        # (3+ words, so a quick "yeah" / "mm-hmm" doesn't cut off the interviewer's question).
        other = self.open[OTHER[speaker]]
        if (is_final and other is not None and other.final_text and not other.interim
                and len(_words(text)) >= 3):
            self._close(OTHER[speaker], "speaker_change")

        turn = self.open[speaker]
        if turn is None:
            if not text:
                return
            turn = Turn(id=self._next_id, speaker=speaker, started=self.clock())
            self._next_id += 1
            self.turns.append(turn)
            self.open[speaker] = turn

        if is_final:
            if text:
                turn.finals.append(text)
                self._recent[speaker].append((self.clock(), text))
                self._prune_recent()
            turn.interim = ""
        else:
            turn.interim = text

        if not turn.text:
            self._discard(turn)
            return
        self._emit_turn(turn)

        if speaker == "interviewer" and speech_final and turn.final_text.endswith("?"):
            # Fast path: a clear question just ended, don't wait for the full 1 s silence.
            self.on_interviewer_turn(turn, "question_mark")

    def _prune_recent(self) -> None:
        now = self.clock()
        for spk in self._recent:
            self._recent[spk] = [(ts, s) for ts, s in self._recent[spk] if now - ts <= ECHO_WINDOW_S]

    def _close(self, speaker: str, reason: str) -> None:
        turn = self.open.get(speaker)
        if turn is None:
            return
        self.open[speaker] = None
        if turn.interim:
            turn.finals.append(turn.interim)
            turn.interim = ""
        if not turn.final_text:
            self._discard(turn)
            return
        turn.closed = True
        turn.ended = self.clock()
        self._emit_turn(turn)
        if speaker == "interviewer":
            self.on_interviewer_turn(turn, reason)

    def _discard(self, turn: Turn) -> None:
        if self.open.get(turn.speaker) is turn:
            self.open[turn.speaker] = None
        if turn in self.turns:
            self.turns.remove(turn)
            self.emit({"type": "turn_removed", "id": turn.id})

    def _emit_turn(self, turn: Turn) -> None:
        self.emit({"type": "turn", "turn": turn.to_dict()})
