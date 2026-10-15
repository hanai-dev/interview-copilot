# Interview Copilot

Press **Record** on your Windows PC during a video call. The app:

1. Captures two audio sources at once: your **microphone** and your **PC's sound output** (Zoom, Meet, Teams…).
2. Transcribes both live with Deepgram, labeling every line **Me** or **Interviewer**.
3. Watches the interviewer's turns and decides when a question was asked.
4. Streams an answer from **Claude** or **ChatGPT** (switchable), built from the files you uploaded: CV, job description, notes, course material.

```
Mic ──────────┐                         ┌─ Live transcript (Me / Interviewer)
              ├─ stereo ─► Deepgram ────┤
PC speakers ──┘  (L=Me,     (per-channel)└─ Interviewer turn ends ─► "Is it a question?" ─► Answer agent ─► Answers panel
                  R=Interviewer)                                        (rules + fast model)   (your files cached)
```

### How it tells you and the interviewer apart

Your mic and the PC's sound are recorded as two separate channels, and Deepgram transcribes each channel on its own. So "who said this" comes from *where the audio came from*, not from guessing voices. That makes it reliable from the first word, with no voice training.

Wear **headphones**. If you use laptop speakers, your mic also hears the interviewer. The app detects and drops those echo lines, but headphones avoid the problem entirely.

---

## Setup (Windows 10/11)

You need:

- **Python 3.12** (64-bit) from python.org. During install, tick **Add python.exe to PATH**.
- A **Deepgram** API key for transcription: https://console.deepgram.com
- An **Anthropic** key (https://console.anthropic.com) and/or an **OpenAI** key (https://platform.openai.com)

Then:

1. Unzip this folder anywhere, for example `Documents\interview-copilot`.
2. Double-click **`run.bat`**. The first run installs everything (a minute or two), then your browser opens at `http://127.0.0.1:8765`. Keep the black window open while you use the app.
3. Click **Settings**, paste your keys, pick Claude or ChatGPT, and click **Save settings**.
4. Click **Files** and add your CV, the job description or any material the interview is based on. You can also paste text.
5. Click **Try a demo interview** to check everything works. With an AI key set, the demo gives real answers.
6. Join your call, then press **Record**. Check the two level bars: **Me** moves when you talk, **Interviewer** moves when they talk.

## Using it

- Answers appear on the right as soon as a question is detected. The newest is large, with its key line highlighted.
- **Answer now** (or press **A**) forces an answer to the interviewer's latest turn, useful if a question was missed.
- Type into the box to ask anything, e.g. "give me a stronger example" or "explain that more simply".
- **A− / A+** change the text size.
- When you press **Stop**, the transcript and answers are saved to `data\sessions\`.

### Settings worth knowing

| Setting | What it does |
|---|---|
| Answer style | Talking points (default), a full answer to read out, or 2–3 sentences |
| Extra instructions | Anything the AI should always know, e.g. the role you're applying for |
| Answer automatically | Turn off to only get answers when you press **Answer now** |
| Call audio output | The headphones/speakers your call plays through. "Windows default" follows your system |
| Key terms | Names and jargon (company, tech stack, your school) so transcription spells them right |
| Language | `en` by default; `multi` if the interview switches between Deepgram's multilingual languages (English, Spanish, French, German, Hindi, and a few others) |
| Models | Defaults: `claude-sonnet-5-5` for answers and `claude-haiku-5-5` for the question check; for OpenAI `gpt-6.1-sol` and `gpt-6-luna`. Change them if the providers rename models |

## Troubleshooting

- **Interviewer bar doesn't move:** in Settings, set *Call audio output* to the device your call plays through. Bluetooth headsets switch to a separate "Hands-Free" device during calls, so pick that one.
- **Me bar doesn't move:** Windows Settings → Privacy & security → Microphone → allow desktop apps to use the microphone. Then pick your mic in Settings.
- **"Deepgram rejected the API key":** re-paste the key in Settings.
- **"Model not found":** the model name in Settings → Models no longer exists; change it to a current one from your provider's model list.
- **Setup failed on PyAudioWPatch:** install Python 3.12 64-bit, delete the `.venv` folder, and run `run.bat` again.

## How it works (code map)

| File | Role |
|---|---|
| `app/audio_capture.py` | Opens your mic and a WASAPI loopback of your speakers, resamples both to 16 kHz, and interleaves them into one stereo stream |
| `app/transcriber.py` | Streams the audio to Deepgram (`multichannel=true`, interim results, utterance-end events) with auto-reconnect |
| `app/turns.py` | Builds speaker turns, closes a turn after ~1 s of silence or when the other person starts talking, filters mic echo |
| `app/prompts.py` | Quick rules for "is this a question?" plus the prompts for the question check and answer agent |
| `app/llm.py` | Claude / OpenAI streaming. Your files and the finished part of the transcript are prompt-cached, so repeat answers start faster and cost less |
| `app/core.py` | Ties it together: session, answer agent, events to the browser |
| `app/server.py` + `static/index.html` | Local web app |

Latency you can expect: words appear on screen within about half a second; an answer starts streaming roughly 1.5–3 seconds after the interviewer finishes. The time to first words is shown on every answer.

Run the tests (any OS, no keys needed): `.venv\Scripts\python -m pip install pytest httpx` then `.venv\Scripts\python -m pytest -q`.

Estimate what an interview costs (no keys needed): `.venv\Scripts\python tests\bench_tokens.py transcript.txt cv.pdf job.pdf` replays an Otter-style transcript through the app with a mocked Claude API and prints the simulated cost in thousandths of a dollar. Set which speakers are you and the interviewer in `ME` / `INTERVIEWER` at the top of that file.

Check how human the answers sound: `.venv\Scripts\python tests\bench_human.py --out answers.md` answers 10 questions from that transcript with your real key (about $0.30), counts AI tells and has a second model rate each answer 1-10.

## Privacy and responsible use

Audio goes to Deepgram and text goes to the AI provider you choose; nothing else leaves your PC. Your keys are stored in `data\settings.json` and `.env`, so don't share those files. Recording laws in many places require the other person's consent, and many employers and schools don't allow AI help during interviews or exams, so check before using it in a real one.
