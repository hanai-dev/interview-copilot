---
workflow: product-launch-video
flow: automation
storyboard: yes
message: "They ask. You see the answer about 2 seconds later."
destination: youtube
aspect: 1920x1080
language: en
audience: "Job seekers and students on a Windows PC"
length: 51s
angle: follow-one-question
narration: yes
---

## Intent

A show-how-it-works video for Interview Copilot, the local Windows app in this repo. Follow ONE interviewer
question end to end: the interviewer speaks → the live transcript labels the line "Interviewer" (mic and PC
sound are separate channels, so "who said it" is reliable) → the app detects it's a question → an answer built
from the user's files streams into the Answers panel ~2 s after they finish. Calm, clear, plain-language —
the README's tone. Show it as it is: the app's own captured screens are the featured assets.

## Assets

- capture/ — real screenshots of the running app (http://127.0.0.1:8765), driven through the built-in demo
  interview with Playwright: idle, Record pressed + both level bars, transcript filling, question detected,
  answer streaming. These are the video's featured visuals.

## Customizations

- Each scene pushes into the panel that matters (level bars → transcript → answers) instead of showing the
  whole 16:9 window, so app text stays readable.
- Count-up on the "~2 s" latency number.
- Voiceover (Kokoro, offline) + captions. No music bed (user chose offline voice, no music; HeyGen not signed in).
- Look: a shipped preset remixed onto the app's own palette (ink #1B2430, interviewer blue #2F5D8A,
  Me green #4F7233, highlighter #FFE873, ground #E9EDF1) and font Atkinson Hyperlegible; judged at the sketch pass.

## Notes

- Never use the user's real interview or PDFs in ../../docs/ (third-party speech, private). Demo script only.
- For the capture, a made-up sample CV + job post is uploaded temporarily so answers look grounded; removed after.
- Latency claims come from the README: words on screen within ~0.5 s; answer starts ~1.5–3 s after the turn ends.
- Don't frame the product as covert/undetectable; the README asks users to check consent and employer rules.
- Phone QR closing beat was offered and not taken. Later the user asked to add the phone teleprompter view (Frame 8).
