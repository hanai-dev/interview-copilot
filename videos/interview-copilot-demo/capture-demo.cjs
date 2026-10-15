// Drives the app's built-in demo interview and screenshots it for the video.
// Run while the app is running with a throwaway COPILOT_DATA_DIR (it uploads a made-up CV + job post):
//   node capture-demo.cjs [http://127.0.0.1:8765] [out-dir]
// Writes <out-dir>/shot-NNN.jpg (2x, 1600x900 viewport) plus index.json describing what each shot shows.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const SAMPLE_CV = `Sam Rivera — Computer Science student, State University (graduating May 2027)
Experience
- Web developer intern, Campus IT (2025-2026): built a room-booking app in React + FastAPI used by 3,000 students.
- Capstone lead, "ShelfLife" (2026): grocery-waste tracker. Our 4-person team had two weeks to ship a working
  prototype for the department demo day. I cut scope to the scan-and-remind flow, set up daily 15-minute check-ins,
  and owned the Python API. We shipped on time; it won the demo-day people's choice award.
Skills: Python, FastAPI, React, TypeScript, PostgreSQL, Git, Docker.`;

const SAMPLE_JOB = `Junior Software Engineer — Northwind Labs
Build internal tools in Python and React. Small team, fast release cycle, weekly demos.
Looking for: shipping under deadlines, clear communication, ownership of features end to end.`;

(async () => {
  const base = process.argv[2] || "http://127.0.0.1:8765";
  const out = process.argv[3] || "shots";
  fs.mkdirSync(out, { recursive: true });

  for (const [name, text] of [["Sam Rivera CV", SAMPLE_CV], ["Northwind Labs job post", SAMPLE_JOB]]) {
    const r = await fetch(`${base}/api/docs/text`, {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name, text }),
    });
    if (!r.ok) throw new Error(`upload ${name}: ${r.status}`);
  }

  const browser = await chromium.launch();
  const index = [];
  try {
    const page = await (await browser.newContext({
      viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2, colorScheme: "light",
    })).newPage();
    await page.goto(base);
    await page.waitForFunction(() => document.querySelector("#docCount")?.textContent.trim() === "2");

    let n = 0;
    const snap = async (label) => {
      const file = `shot-${String(n++).padStart(3, "0")}.jpg`;
      await page.screenshot({ path: path.join(out, file), type: "jpeg", quality: 92 });
      const dom = await page.evaluate(() => ({
        status: document.querySelector("#status")?.textContent.trim(),
        timer: document.querySelector("#timer")?.textContent.trim(),
        me: document.querySelector("#lvlMe")?.style.width,
        them: document.querySelector("#lvlThem")?.style.width,
        turns: [...document.querySelectorAll(".turn")].map(t => t.textContent.replace(/\s+/g, " ").trim()).slice(-3),
        answers: [...document.querySelectorAll(".answer")].map(a => a.textContent.replace(/\s+/g, " ").trim().slice(0, 140)),
      }));
      index.push({ file, label, t: Date.now(), ...dom });
    };

    await snap("idle");
    await page.click("#filesBtn");
    await page.waitForTimeout(600);
    await snap("files-drawer");
    await page.keyboard.press("Escape");
    await page.waitForTimeout(400);

    await page.getByRole("button", { name: "Try a demo interview" }).click();
    const end = Date.now() + 110_000;
    while (Date.now() < end) {
      await snap("demo");
      const status = index[index.length - 1].status || "";
      if (/Demo finished|Saved/i.test(status) && index.length > 20) break;
      await page.waitForTimeout(250);
    }
    await page.waitForTimeout(1500);
    await snap("final");
  } finally {
    fs.writeFileSync(path.join(out, "index.json"), JSON.stringify(index, null, 1));
    await browser.close();
  }
  console.log(`ok: ${index.length} shots in ${out}`);
})().catch(e => { console.error(e); process.exit(1); });
