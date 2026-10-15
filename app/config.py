"""Settings: defaults, .env keys, and user overrides saved to data/settings.json."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("COPILOT_DATA_DIR") or ROOT / "data")
UPLOADS_DIR = DATA_DIR / "uploads"
SESSIONS_DIR = DATA_DIR / "sessions"
SETTINGS_FILE = DATA_DIR / "settings.json"
STATIC_DIR = ROOT / "static"

if load_dotenv:
    load_dotenv(ROOT / ".env")

# Model names change over time; all of these are editable in the Settings panel.
DEFAULTS: dict = {
    "provider": "claude",                     # "claude" or "openai"
    "claude_answer_model": "claude-sonnet-5-5",
    "claude_fast_model": "claude-haiku-5-5",  # used to decide "is this a question?"
    "claude_effort": "low",                   # low = fastest first words; blank to use the model default
    "openai_answer_model": "gpt-6.1-sol",
    "openai_fast_model": "gpt-6-luna",
    "openai_reasoning_effort": "low",         # blank to omit
    "deepgram_model": "nova-3",
    "language": "en",
    "keyterms": "",                           # comma-separated words to help transcription (names, tech terms)
    "answer_style": "talking_points",         # talking_points | full | short
    "extra_instructions": "",
    "auto_answer": True,
    "mic_device": None,
    "speaker_device": None,
    "save_audio": False,
    "font_scale": 1.0,
}

SECRET_KEYS = {
    "deepgram_api_key": "DEEPGRAM_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
}

STYLES = {"talking_points", "full", "short"}


class Settings:
    def __init__(self, path: Path = SETTINGS_FILE):
        self.path = path
        self._lock = threading.Lock()
        self._values = dict(DEFAULTS)
        for k, env in SECRET_KEYS.items():
            self._values[k] = os.environ.get(env, "").strip()
        if path.exists():
            try:
                saved = json.loads(path.read_text(encoding="utf-8"))
                for k, v in saved.items():
                    if k in SECRET_KEYS and not v:
                        continue  # an empty saved key never hides a .env key
                    if k in self._values:
                        self._values[k] = v
            except (OSError, ValueError):
                pass

    def get(self, key: str, default=None):
        with self._lock:
            return self._values.get(key, default)

    def __getitem__(self, key: str):
        return self.get(key)

    def update(self, changes: dict) -> None:
        with self._lock:
            for k, v in changes.items():
                if k not in self._values:
                    continue
                if k in SECRET_KEYS:
                    v = (v or "").strip()
                    if not v or set(v) == {"•"}:
                        continue  # blank or masked value = keep the current key
                if k == "answer_style" and v not in STYLES:
                    continue
                if k == "provider" and v not in ("claude", "openai"):
                    continue
                if k in ("mic_device", "speaker_device"):
                    v = None if v in (None, "", "default") else int(v)
                if k in ("auto_answer", "save_audio"):
                    v = bool(v)
                if k == "font_scale":
                    v = min(2.0, max(0.7, float(v)))
                self._values[k] = v
            self._save()

    def clear_key(self, key: str) -> None:
        with self._lock:
            if key in SECRET_KEYS:
                self._values[key] = ""
                self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._values, indent=2), encoding="utf-8")

    def public(self) -> dict:
        """Settings safe to send to the browser: keys are replaced by whether they're set."""
        with self._lock:
            out = {k: v for k, v in self._values.items() if k not in SECRET_KEYS}
            out["keys"] = {k: bool(self._values.get(k)) for k in SECRET_KEYS}
            return out

    def answer_key(self) -> str:
        return self.get("anthropic_api_key") if self.get("provider") == "claude" else self.get("openai_api_key")
