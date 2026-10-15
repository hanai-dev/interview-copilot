// Phone check: the PC's Phone dialog shows a QR code, and a phone on the same Wi-Fi gets in only through it.
// Run while the app is running:  node tests/phone.cjs [http://127.0.0.1:8765] [screenshot-dir]
const { chromium, devices } = require("playwright");
const assert = require("assert");
const path = require("path");

(async () => {
  const local = process.argv[2] || "http://127.0.0.1:8765";
  const shots = process.argv[3];
  const browser = await chromium.launch();
  try {
    // On the computer: Phone shows the QR code.
    const pc = await browser.newPage();
    await pc.goto(local);
    await pc.click("#phoneBtn");
    await pc.waitForSelector("#phoneDlg[open]");
    assert((await pc.getAttribute("#phoneQr", "src")).startsWith("data:image/svg"), "QR code shown");
    if (shots) await pc.screenshot({ path: path.join(shots, "pc-phone-dialog.png") });
    const { url } = await (await pc.request.get(`${local}/api/phone`)).json();
    const lan = new URL(url).origin;

    // A phone on the same Wi-Fi: refused without the key, let in by the QR link, live updates connected.
    const phone = await (await browser.newContext({ ...devices["iPhone 13"] })).newPage();
    assert.strictEqual((await phone.goto(`${lan}/`)).status(), 403, "no key, no access");
    const frames = [];
    phone.on("websocket", ws => ws.on("framereceived", f => frames.push(String(f.payload))));
    await phone.goto(url);
    assert.strictEqual(phone.url(), `${lan}/`, "key removed from the address bar");
    await phone.waitForFunction(() => document.title === "Interview Copilot");
    await phone.waitForTimeout(1500);
    assert(frames.some(f => f.includes('"snapshot"')), "live updates connected");
    assert(!(await phone.textContent("#status")).includes("Lost connection"), "no connection error");
    if (shots) await phone.screenshot({ path: path.join(shots, "phone.png") });
    console.log(`ok: QR dialog on the PC; phone at ${lan} refused without key, opened by the QR link, live`);
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
