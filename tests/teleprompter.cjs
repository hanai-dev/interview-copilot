// Phone teleprompter check: answers-only low-glare view that follows your voice through the answer.
// Run while the app is running:  node tests/teleprompter.cjs [http://127.0.0.1:8765] [screenshot-dir]
// Feeds the page a real answer and the words actually said while reading it (as live "Me" speech).
const { chromium, devices } = require("playwright");
const assert = require("assert");
const path = require("path");
const { Follower, norm } = require("../static/follow.js");

const ANSWER = `**So I'd label at two levels, what the student wrote and which misconception it shows, and I'd have the math specialists double-label everything.**

- The labels are a verbatim transcription of each crop with mistakes kept, then misconception codes from that lesson's pack with the evidence for each one, or an abstain when nothing fits. Tying codes to a pack keeps the labels consistent across specialists.
- The process is that two specialists label each submission independently in Label Studio, and a third one resolves disagreements. I'd start with about 1,000 consented submissions, plus 300 worksheets where specialists plant known mistakes.
- To coordinate the team, I'd run a short calibration round first on a shared batch, so we agree on code definitions before scaling. Then I'd track agreement every week and add flagged cases to the set.
- I'd keep a golden set that never goes into training, because it's what we measure launch gates against.`;
const SAID = `So I labeled I label it at two levels, what the student wrote and which misconception it shows. And I have the math specialist double label everything. But The labels are a verbatim transcription of its crap with with mistakes kept then misconception codes from that lessons pack with the evidence of for each one as an abs... Or an abstain when nothing fits, trying to codes tying codes to a pack keeps the levels consistent across specialist. So the process is that two specialists label its submission independently. In Label Studio or something like that. And the third one resolved this agreement. So I start with about 1,000 consented submissions plus 300 worksheets for specialist plus non... Plat down mistakes.`.split(/\s+/);

const lum = rgb => {
  const m = rgb.match(/[\d.]+/g).map(Number);
  if (m.length === 4 && m[3] === 0) return 0;
  const c = m.slice(0, 3).map(v => (v /= 255) <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};

async function answer(page, id, md) {
  await page.evaluate(([id, md]) => {
    handle({ type: "answer_start", answer: { id, question: "How would you label this dataset?", turn_id: null, created: 0, provider: "claude", model: "test", manual: false, latency_ms: 900 } });
    handle({ type: "answer_delta", id, text: md });
    handle({ type: "answer_done", id, latency_ms: 900 });
  }, [id, md]);
}
const say = (page, turnId, words) => page.evaluate(([id, text]) =>
  handle({ type: "turn", turn: { id, speaker: "me", final: "", interim: text, closed: false, started: 0 } }), [turnId, words.join(" ")]);
const state = page => page.evaluate(() => {
  const box = document.querySelector("#answers"), words = [...document.querySelectorAll(".answer.latest .w")];
  const now = words.findIndex(w => w.classList.contains("now"));
  const nowTop = now >= 0 ? words[now].getBoundingClientRect().top - box.getBoundingClientRect().top : null;
  return { scroll: box.scrollTop, height: box.clientHeight, now, nowTop, read: words.filter(w => w.classList.contains("read")).length, total: words.length };
});
const expectedPos = words => { const f = new Follower(ANSWER.replace(/\*\*/g, "").replace(/^\s*-\s+/gm, "").split(/\s+/).filter(w => norm(w))); words.forEach(w => f.feed(w)); return f.pos; };

(async () => {
  const local = process.argv[2] || "http://127.0.0.1:8765";
  const shots = process.argv[3];
  const browser = await chromium.launch();
  const results = [];
  const ok = (row, cond, detail) => { results.push(`${cond ? "PASS" : "FAIL"} ${row} ${detail}`); };
  try {
    const pcPage = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    await pcPage.goto(local);
    const { url } = await (await pcPage.request.get(`${local}/api/phone`)).json();
    const js = await pcPage.request.get(`${local}/static/follow.js`);

    // ---- phone: layout, glare, following
    const phoneCtx = await browser.newContext({ ...devices["iPhone 13"] });
    const phone = await phoneCtx.newPage();
    await phone.goto(url);
    await phone.waitForFunction(() => typeof handle === "function" && document.querySelector("#status").textContent !== "");
    const phoneJs = await phone.request.get(new URL("/static/follow.js", url).href);
    ok("D1", js.status() === 200 && phoneJs.status() === 200, `follow.js PC ${js.status()} phone ${phoneJs.status()}`);

    await answer(phone, "tp1", ANSWER);
    const layout = await phone.evaluate(() => {
      const vis = el => { const r = el.getBoundingClientRect(); return getComputedStyle(el).display !== "none" && r.width > 0 && r.height > 0; };
      const col = document.querySelector(".answers-col").getBoundingClientRect();
      return { transcript: vis(document.querySelector("#transcript")), answersShare: col.height / innerHeight };
    });
    ok("F1", !layout.transcript && layout.answersShare >= 0.75, `transcript visible=${layout.transcript} answers=${Math.round(layout.answersShare * 100)}% of screen`);

    const colors = await phone.evaluate(() => {
      const bright = [];
      for (const el of document.querySelectorAll("body, body *")) {
        const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
        if (cs.display === "none" || cs.visibility === "hidden" || r.width === 0 || r.height === 0) continue;
        bright.push([el.tagName + (el.id ? "#" + el.id : "") + (el.className && typeof el.className === "string" ? "." + el.className.split(" ").join(".") : ""), cs.backgroundColor]);
      }
      const w = document.querySelector(".answer.latest .w:not(.read):not(.now)") || document.querySelector(".answer.latest .body");
      return { body: getComputedStyle(document.body).backgroundColor, bgs: bright, text: getComputedStyle(w).color };
    });
    const lit = colors.bgs.filter(([, bg]) => lum(bg) > 0.05);
    ok("U1", lum(colors.body) === 0 && lit.length === 0, `body ${colors.body}; light backgrounds: ${JSON.stringify(lit.slice(0, 4))}`);
    const tl = lum(colors.text), contrast = (tl + 0.05) / 0.05;
    ok("U2", tl <= 0.30 && contrast >= 4.5, `unread text ${colors.text} luminance ${tl.toFixed(3)} contrast ${contrast.toFixed(1)}:1`);

    // F2: read along: position marked, kept in the upper part of the window while scrolling
    const part = SAID.slice(0, 95);
    for (let i = 3; i <= part.length; i += 3) await say(phone, 900, part.slice(0, i));
    await phone.waitForTimeout(900);
    const s2 = await state(phone), want = expectedPos(part);
    ok("F2", Math.abs(s2.now - want) <= 1 && s2.read >= want - 1 && s2.scroll > 0 && s2.nowTop >= 0 && s2.nowTop <= s2.height * 0.5,
      `now=${s2.now} expected ${want} read=${s2.read} scroll=${s2.scroll} nowTop=${Math.round(s2.nowTop)}/${s2.height}`);
    if (shots) await phone.screenshot({ path: path.join(shots, "teleprompter-phone.png") });

    // F4: touch pauses following; Follow button off stops it, on resumes
    const before = s2.scroll;
    await phone.dispatchEvent("#answers", "touchstart");
    for (let i = part.length + 3; i <= part.length + 24; i += 3) await say(phone, 900, SAID.slice(0, i));
    await phone.waitForTimeout(600);
    const paused = (await state(phone)).scroll;
    await phone.click("#followBtn");
    const pressedOff = await phone.getAttribute("#followBtn", "aria-pressed");
    await phone.waitForTimeout(4500);  // touch pause over, but Follow is off
    for (let i = part.length + 27; i <= SAID.length; i += 3) await say(phone, 900, SAID.slice(0, i));
    await phone.waitForTimeout(600);
    const offScroll = (await state(phone)).scroll;
    await phone.click("#followBtn");
    await phone.waitForTimeout(900);
    const onScroll = (await state(phone)).scroll;
    ok("F4", paused === before && pressedOff === "false" && offScroll === paused && onScroll > offScroll,
      `touch-paused ${before}->${paused}, follow off (aria-pressed=${pressedOff}) ${offScroll}, back on ${onScroll}`);

    // F5: a new answer starts at its top and ignores what was said before it
    await say(phone, 901, ["So", "the", "submission", "ID"]);
    await answer(phone, "tp2", "**So the submission ID is the idempotency key, and I'd enforce it at the write.**\n\n- Worker claims job first, conditional write on submission ID");
    const s5a = await state(phone);
    await say(phone, 901, ["So", "the", "submission", "ID", "So", "the", "submission", "ID", "is", "the"]);
    const s5b = await state(phone);
    ok("F5", s5a.scroll === 0 && s5a.read === 0 && s5b.read === 6, `on arrival scroll=${s5a.scroll} read=${s5a.read}; after 6 new words read=${s5b.read}`);

    // H2: answer text is never parsed as HTML by the word marking
    await answer(phone, "tp3", "Use <img src=x onerror=window.__pwned=1> literally");
    const pwned = await phone.evaluate(() => [window.__pwned === 1, document.querySelectorAll(".answer.latest .body img").length]);
    ok("H2", !pwned[0] && pwned[1] === 0, `script ran=${pwned[0]} img elements=${pwned[1]}`);

    // F3: talking off-script keeps scrolling at your pace; silence holds still
    const clockCtx = await browser.newContext({ ...devices["iPhone 13"] });
    const cp = await clockCtx.newPage();
    await cp.clock.install();
    await cp.goto(url);
    await cp.waitForFunction(() => typeof handle === "function");
    await answer(cp, "tp4", ANSWER);
    const filler = "well you know honestly it really depends on the team and how much time we have for it".split(" ");
    for (let i = 1; i <= filler.length; i++) { await say(cp, 950, filler.slice(0, i)); await cp.clock.runFor(400); }
    const crept = (await state(cp)).scroll;
    await cp.clock.runFor(4000);
    const held = (await state(cp)).scroll;
    ok("F3", crept > 0 && held === crept, `scroll while talking off-script ${crept}, after 4 s silence ${held}`);

    // U4: reduced motion jumps straight to the spot (no smooth animation)
    const rmCtx = await browser.newContext({ ...devices["iPhone 13"], reducedMotion: "reduce" });
    const rm = await rmCtx.newPage();
    await rm.goto(url);
    await rm.waitForFunction(() => typeof handle === "function");
    await answer(rm, "tp5", ANSWER);
    await say(rm, 960, part);
    const r1 = (await state(rm)).scroll;
    await rm.waitForTimeout(500);
    const r2 = (await state(rm)).scroll;
    ok("U4", r1 > 0 && r1 === r2, `scroll right away ${r1}, 0.5 s later ${r2}`);

    // U3: desktop keeps its layout and colors, and doesn't scroll on its own
    await answer(pcPage, "tp6", ANSWER);
    await say(pcPage, 970, part);
    await pcPage.waitForTimeout(700);
    const desk = await pcPage.evaluate(() => ({
      transcript: getComputedStyle(document.querySelector("#transcript")).display !== "none",
      bg: getComputedStyle(document.body).backgroundColor,
      scroll: document.querySelector("#answers").scrollTop,
      follow: getComputedStyle(document.querySelector("#followBtn")).display,
    }));
    ok("U3", desk.transcript && lum(desk.bg) > 0.5 && desk.scroll === 0 && desk.follow === "none",
      `transcript=${desk.transcript} bg=${desk.bg} scroll=${desk.scroll} followBtn=${desk.follow}`);
  } catch (e) {
    results.push(`ERROR ${e.message.split("\n")[0]}`);
  } finally {
    await browser.close();
  }
  console.log(results.join("\n"));
  process.exit(results.every(r => r.startsWith("PASS")) ? 0 : 1);
})();
