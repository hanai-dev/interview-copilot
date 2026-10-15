// Screenshots the phone teleprompter view following a voice through the demo's deadline answer.
// Run while the app is running:  node capture-phone.cjs [http://127.0.0.1:8765] [out-dir]
// Like tests/teleprompter.cjs, it feeds the page the answer and the words read aloud as live "Me" speech.
const { chromium, devices } = require("playwright");
const path = require("path");

// The real answer Claude gave to the deadline question in the demo run (session saved by the app).
const QUESTION = "Nice. Can you describe a time you had to deliver a project under a really tight deadline?";
const ANSWER = `**Yeah, my capstone project, ShelfLife, is a good example. We had two weeks to ship a working prototype for the department demo day.**

- It's a grocery-waste tracker, and I was the lead on a four-person team, so the main risk was trying to build too much in two weeks.
- I cut the scope down to just the scan-and-remind flow, because I figured one thing working well beats five things half done.
- I also set up daily fifteen-minute check-ins so we caught blockers early, and I owned the Python API myself.
- We shipped on time, and it won the demo-day people's choice award.`;
const WORDS = ANSWER.replace(/\*\*/g, "").replace(/^\s*-\s+/gm, "").split(/\s+/).filter(Boolean);
const STOPS = [0, 9, 22, 44, 66]; // words read aloud at each screenshot

(async () => {
  const base = process.argv[2] || "http://127.0.0.1:8765";
  const out = process.argv[3] || "shots";
  const { url } = await (await fetch(`${base}/api/phone`)).json();
  const browser = await chromium.launch();
  try {
    const phone = await (await browser.newContext({ ...devices["iPhone 13"], reducedMotion: "reduce" })).newPage();
    await phone.goto(url);
    await phone.waitForFunction(() => typeof handle === "function" && document.querySelector("#status").textContent !== "");
    await phone.evaluate(([q, md]) => {
      handle({ type: "answer_start", answer: { id: "v1", question: q, turn_id: null, created: 0, provider: "claude", model: "claude-sonnet-5-5", manual: false, latency_ms: 1000 } });
      handle({ type: "answer_delta", id: "v1", text: md });
      handle({ type: "answer_done", id: "v1", latency_ms: 1000 });
    }, [QUESTION, ANSWER]);
    for (const n of STOPS) {
      if (n) await phone.evaluate(text => handle({ type: "turn", turn: { id: 900, speaker: "me", final: "", interim: text, closed: false, started: 0 } }), WORDS.slice(0, n).join(" "));
      await phone.waitForTimeout(900);
      await phone.screenshot({ path: path.join(out, `phone-read-${String(n).padStart(2, "0")}.png`) });
    }
    console.log(`ok: ${STOPS.length} phone shots in ${out} (${WORDS.length} words in the answer)`);
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
