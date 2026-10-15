# Frame packet: 10-press-record

## Project inputs

- Project: C:\Users\tenso\Downloads\interview-copilot\interview-copilot\videos\interview-copilot-demo
- Design tokens: C:\Users\tenso\Downloads\interview-copilot\interview-copilot\videos\interview-copilot-demo\frame.md
- RULES_DIR: C:\Users\tenso\.claude\skills\hyperframes-animation\rules

## Assigned storyboard block

## Frame 10 — Press Record

- scene: The app's dark Record pill under the "Interview Copilot" wordmark; a cursor presses it and it flips to the red Stop state. Small colophon line underneath.
- voiceover: "Interview Copilot. Try the demo interview, then press Record."
- duration: 5.248s
- transition_in: crossfade
- status: built
- src: compositions/frames/10-press-record.html
- type: cta
- persuasion: Friction reduction
- beat: urgency-to-act
- blueprint: cta-morph-press (Adapt)
- focal: the Record pill
- roles: Record pill = rebuilt in the app's own style (dark pill, red dot → red Stop with white square)
- asset_candidates: assets/app-idle.jpg — reference for the Record pill (dark pill, red dot) — rebuild as vector

narrativeRole: Close on the one action that starts everything, the app's own Record button. Colophon (small, text-light): "Runs on your Windows PC · Check consent and your employer's rules before using AI help" — mirrors the README's responsible-use note.
keyMessage: Try it — press Record.

Adapt: keep the condense-into-CTA at one center + human-aimed cursor click with feedback; change: the "brand mark" is the app's red record dot, which grows into the Record pill under the wordmark.
Scene 1 (0.0–1.2s): white field; the faint concentric rings draw outward from center → `svg-path-draw`; the accent line draws and on "Interview Copilot" the wordmark slides up → `gsap-effects`. Centered.
Scene 2 (1.2–2.4s): on "Try the demo interview", the red record dot appears at the pill's center and the dark pill CONDENSES out around it into "● Record" at the same center → `card-morph-anchor` (one element transforming, shared origin).
Scene 3 (2.4–3.3s): on "then press Record", an arrow cursor arrives from lower-right on a decelerating path, landing a few px off the pill's center → `cursor-click-ripple` (approach).
Scene 4 (3.3–5.2s): the click: cursor and pill compress together and release → `physics-press-reaction`; the pill flips to the red Stop state (white square + "Stop") with one soft ripple ring → `cursor-click-ripple`; the colophon fades up at the bottom of the content area → `gsap-effects`; hold still to the end (final frame: a gentle fade of the whole frame in the last ~0.4s is allowed).

## Selected blueprint: cta-morph-press

# cta-morph-press — CTA Morph & Press

**intent**: A resting brand mark condenses at the same screen center into a smaller, brighter CTA, then a cursor arrives from off-stage and lands a human-aimed click on it. The viewer's eye is walked from "this is who we are" to "and this is what you do." The morph and the click are the two headline beats.

**roles served**

- CTA (from `cta-morph-press`): when the close moves from brand identity to a single user action, two elements share the same center sequentially (a morph, not a cut), and the payoff is a simulated click with physical feedback. Reach for it for a focused "click here" sign-off — no spatial set, no multi-step UI (that's `cursor-ui-demo`).
- Hook (ROLE-WIDENED, from `widget-morph-on-blank-field`): the same
  machinery run as an OPENER — a lone `[widget]` (pill / chip lockup) on a flat field transforms
  in place, performs its payload, then vanishes to a plain frame that a typed `[title]` resolves.
  The click, when present, ignites the morph rather than closing it; there may be no cursor at
  all. Reach for it when the product hook IS one widget doing one thing — still no spatial set,
  no multi-step UI (that's `cursor-ui-demo`). Mint-reconsideration trigger: if future mining
  brings 2+ more widget-morph openers with the vanish → typed-title resolve, promote this variant
  to its own blueprint (the beat order is fully inverted by then).

**duration**: 4–6s (Hook widget-morph opener 5–7.5s)

**shot structure** (a `[bg]` canvas; hero and CTA are flex-centered siblings sharing one `transform-origin`)

- **Scene 1 (0.0–~1.4s) — presence.** The `[hero mark / brand lockup]` holds dead-center, alive but resting — only a faint rotational breath on the mark; any title text under it stays rock-stable. Camera static.
- **Scene 2 (~1.4–2.4s) — the morph (signature move).** The hero CONDENSES at the same screen center into a smaller, brighter `[CTA]` (button / card): the outgoing mark shrink-fades exactly as the CTA scales up in its place. Because they share one `transform-origin`, the eye reads it as one element transforming, not a swap.
- **Scene 3 (~2.4–3.4s) — approach.** A `[cursor]` arrives from off-stage on a **decelerating** path (it "arrives," it does not pass through) and lands a few px **off** the CTA's geometric center, so the aim reads human, not scripted.
- **Scene 4 (~3.4–end) — press.** The cursor lands a physical CLICK — cursor and CTA compress together in lockstep, then release with feedback (an optional ripple / glow bloom). Holds on the clicked state.
- **Variant — Hook (widget-morph opener)** (from `widget-morph-on-blank-field`;
  reorders the beats — press first, morph second, title last). **(1) presence**: a lone
  `[pill / chip lockup]` sits centered on a flat `[field]`; optionally the `[cursor]` glides in, a
  hover pill-background appears behind the chip, and the click lands with the same lockstep press.
  **(2) the morph**: the widget transforms IN PLACE — expands downward anchored at its top edge
  into a `[menu]`, or spring-morphs outward into a `[prompt card]` with a small overshoot settle —
  new content fades/slides into place. **(3) payload**: the transformed state performs —
  `[placeholder]` types with a blinking caret, `[user text]` types while a control flips from
  muted to its vibrant active color, or the menu snap-collapses back to the pill carrying the
  `[new value]` + a checkmark pop; the background may snap to a new color under the persistent
  foreground card. **(4) resolve**: the widget VANISHES; a plain frame closes the beat — a
  `[closing title]` types on center, or a hold on the flipped solid.

**motion vocabulary**: faint rotation-only resting breath (logo scope only); same-center morph-swap (shrink-fade ↔ scale-up sharing `transform-origin`); cursor decel-arrival from off-stage; off-center human aim; lockstep press compression; release feedback ripple / glow. Hook opener: anchored downward expand of a pill into a menu and springy snap-collapse back;
chip-to-card spring morph with overshoot settle; placeholder / user-text typewriter with blinking
caret (may cut mid-word); control color-state flip muted → vibrant; background color snap under a
persistent foreground card; checkmark pop; widget vanish to blank frame; typed closing title.

**rule mapping**

- hero → CTA condense at one center → `scale-swap-transition` (shared `transform-origin: 50% 50%` is what sells the morph; CTA `position: absolute` so it doesn't shove the hero during the brief overlap)
- resting-hero aliveness (rotation only, scoped to the mark so the Phase-2 scale doesn't fight it) → `sine-wave-loop` (low-amplitude rotation register — subtle jitter, not a scale breath)
- cursor press + release in lockstep (single-target-array so both compress together) → `physics-press-reaction` (PRESS_DOWN + RELEASE portion)
- cursor approach (decel from off-stage, off-center landing, hard-cut opacity in) → `gsap-effects` (translate on `power2.out`)
- click ripple / release glow → `cursor-click-ripple` (attack-decay ring) and/or `ambient-glow-bloom` (release bloom)
- (Hook) chip → prompt-card spring morph at one center → `scale-swap-transition` (the base morph
  contract, run in the expand direction) + `card-morph-anchor` (corner-radius / surface ride-along)
- (Hook) anchored-edge expand / snap-collapse (pill ↔ menu, top edge pinned) →
  `anchored-layout-expand` (edge-anchored directional container growth — origin-pinned expansion
  with counter-scaled children; `card-morph-anchor` stays for uniform-scale morphs only)
- (Hook) placeholder + user typing, blinking caret, mid-word cut → `gsap-effects` (typewriter) +
  `context-sensitive-cursor` (blink) + `discrete-text-sequence` (mid-word cut states)
- (Hook) control color flip muted → vibrant → `press-release-spring` (color-transition variation)
- (Hook) checkmark pop / card-arrival overshoot → `spring-pop-entrance`
- (Hook) hover pill-background + igniting click → the base's `physics-press-reaction` +
  `cursor-click-ripple` mappings apply unchanged

**camera modifier**: camera-static — the morph and click happen in element space; a camera move would compete with the click as the climax. The Hook opener keeps the same contract — even the background color flip is an element-level
snap, not a camera event.

## Selected motion rule: card-morph-anchor

---
name: card-morph-anchor
description: Container morphs dimensions and border-radius between shots, serving as a visual transition anchor.
metadata:
  tags: morph, anchor, transition, border-radius, container, shape
---

# Card Morph Anchor

A free-floating container morphs apparent size, corner radius, and surface treatment between two shots — the morph itself IS the transition; the viewer's eye tracks the persistent container. Distinct from [anchored-layout-expand.md](anchored-layout-expand.md) (an edge-pinned live layout participant that grows along one axis and reflows neighbors — here nothing is pushed) and [theme-crossfade-morph.md](theme-crossfade-morph.md) (a whole-theme reskin under a fixed anchor — here a single container changes shape).

## How It Works

Since `width`/`height` tweens are forbidden, **substitute uniform `scale` for apparent size**; the remaining morph channels are **paint-only**: `borderRadius`, `background`, `boxShadow`. All channels ride ONE tween (one ease, one duration) so the shape morphs in lockstep. Content choreography: old content fades out during the first ~40% of the morph, new content fades in during the last ~40% — the shape-only gap between is the natural "blink." Optionally the morph card itself fades at the very end, revealing the real next-shot element rendered behind it.

## Recipe

```html
<!-- inside a standard scene clip (hyperframes-core) -->
<!-- DOM order = stacking: the anchor renders BEFORE the card, so the card is on top -->
<div class="next-shot-anchor"><img src="{nextShotAnchor}" alt="anchor" /></div>
<div class="morph-card">
  <div class="content-old">{shotOneContent}</div>
  <div class="content-new">{shotTwoContent}</div>
</div>
```

```css
.morph-card {
  width: SHOT_ONE_W;
  height: SHOT_ONE_H; /* shot-1 geometry; the morph is scale, never width/height */
  border-radius: SHOT_ONE_RADIUS;
  background: {surfaceShotOne};
  overflow: hidden; /* content must clip during the shape change */
  display: grid;
  place-items: center;
  will-change: transform;
}
.content-old,
.content-new {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
}
.content-new {
  opacity: 0; /* author its inner sizes at apparent-size ÷ END_SCALE — it scales with the card */
}
.next-shot-anchor {
  position: absolute;
  opacity: 0; /* fades in as the morph card fades out */
}
```

```js
const END_SCALE = SHOT_TWO_W / SHOT_ONE_W; // uniform — keep the two shots aspect-matched

// Hold shot 1 for HOLD_BEAT first — an instant morph reads as glitchy.

// One tween, all channels: uniform scale + paint-only properties.
tl.to(
  ".morph-card",
  {
    scale: END_SCALE,
    borderRadius: SHOT_TWO_RADIUS / END_SCALE, // borderRadius is pre-scale — divide to land the APPARENT radius
    background: "{surfaceShotTwo}",
    boxShadow: "{shadowShotTwo}",
    duration: MORPH_DUR,
    ease: "power2.inOut",
  },
  MORPH_START,
);

tl.to(
  ".content-old",
  { opacity: 0, duration: MORPH_DUR * OLD_FADE_FRAC, ease: "power1.in" },
  MORPH_START,
);
tl.to(
  ".content-new",
  { opacity: 1, duration: MORPH_DUR * NEW_FADE_FRAC, ease: "power1.out" },
  MORPH_START + MORPH_DUR * (1 - NEW_FADE_FRAC),
);

// Optional handoff — card fades out over the pixel-identical real anchor.
tl.to(
  ".morph-card",
  { opacity: 0, duration: MORPH_DUR * FINAL_FADE_FRAC, ease: "power1.in", immediateRender: false },
  MORPH_START + MORPH_DUR * (1 - FINAL_FADE_FRAC),
);
tl.to(
  ".next-shot-anchor",
  { opacity: 1, duration: MORPH_DUR * FINAL_FADE_FRAC, ease: "power1.out" },
  MORPH_START + MORPH_DUR * (1 - FINAL_FADE_FRAC),
);
```

## Morph channels

| channel        | how                                                                                            |
| -------------- | ---------------------------------------------------------------------------------------------- |
| apparent size  | uniform `scale` — the substitution for the forbidden `width`/`height` tween; aspect preserved  |
| `borderRadius` | paint-only; pre-scale units — tween to `APPARENT_RADIUS / END_SCALE`, ≤ half the smaller side  |
| `background`   | paint-only; gradients interpolate only with equal stop counts (solid→solid: `backgroundColor`) |
| `boxShadow`    | paint-only; base shadow → accent glow shifts emphasis                                          |

## Variations

- **Landing on a non-centered target** (dock icon, sidebar slot): add `x`/`y` to the same tween, computed as the FLIP-style delta between the card's and the target's rects — `getBoundingClientRect()` both at build time (single-scene only, per the contract) and tween the difference. Don't hand-compute from CSS values: paddings, borders, and parent transforms compound, and center-vs-edge arithmetic is the classic off-by-half bug.
- **Aspect change between shots**: uniform scale preserves aspect — morph to the nearest uniform fit and let the crossfade/handoff absorb the small delta, or drop the handoff and hold the card's final state.

## Values

| token             | range                     | notes                                                                                |
| ----------------- | ------------------------- | ------------------------------------------------------------------------------------ |
| HOLD_BEAT         | 0.6–1.5s                  | ≥ shot 1's entry settle; the viewer must register shot 1 first                       |
| MORPH_DUR         | 0.6–1.2s                  | < 0.5s can't fit both content fades                                                  |
| END_SCALE         | SHOT_TWO_W / SHOT_ONE_W   | icon-sized handoffs typically land at 80–400px apparent width                        |
| SHOT_TWO_RADIUS   | ≤ min(W, H)/2 apparent    | half the smaller side = perfect circle; beyond is clamped                            |
| OLD/NEW_FADE_FRAC | 0.3–0.5 each, sum ≤ 1     | the gap between is the shape-only "blink"                                            |
| FINAL_FADE_FRAC   | 0 (no handoff) or 0.1–0.2 | only when a pixel-identical anchor exists                                            |
| ease              | `power2.inOut` canonical  | `power3`/`expo.inOut` OK; never `back`/`elastic` — overshoot fights the shape change |

## Critical Constraints

- **❗ Uniform-scale substitution** — never tween `width`/`height`; `scale` + the paint-only channels (`borderRadius`, `background`, `boxShadow`) are the ONLY morph properties.
- **❗ Handoff anchor must be pixel-identical to the card's final state** — same apparent size, radius, background, shadow, inner icon dimensions. Any delta = a visible pop during the crossfade. Can't match exactly? Drop the handoff and hold the morph card.
- **❗ Stacking by DOM order, never a z-index snap mid-fade** — render the anchor before the card; a `tl.set({ zIndex })` during an active opacity tween flips stacking before the fade finishes and flickers.
- **`overflow: hidden`** on the card — content must clip as the radius changes.
- **Hold a beat before morphing**; same ease family for shape and crossfade (mixed eases read unsynchronized).

## See also

`anchored-layout-expand` (edge-pinned one-axis growth with reflow) · `theme-crossfade-morph` (whole-theme reskin under a fixed anchor) · `scale-swap-transition` (content swap without shape change) · `sine-wave-loop` (a breath on the final state).

## Selected motion rule: cursor-click-ripple

---
name: cursor-click-ripple
description: Animated mouse cursor moves to target, clicks with scale depression and expanding ripple rings.
metadata:
  tags: cursor, click, ripple, interaction, mouse, button
---

# Cursor Click Ripple

An animated cursor moves to a target element, performs a click with visual depression, and emits expanding ripple rings from the click point. Three sequential phases on one timeline: **move** (eased translation to the target's center) → **click** (scale depression on cursor + target together, yoyo back) → **ripple** (1–3 staggered rings expand and fade from the click point). This is a _point event at one location_ — a sustained hold across space is [cursor-drag.md](cursor-drag.md).

## Recipe

```html
<button class="target-button">{ctaLabel}</button>
<div class="cursor"><!-- arrow SVG, positioned at the entry corner --></div>
<!-- Rings live in DOM from t=0 at the click-target CENTER, scale 0 + opacity 0 -->
<div class="ripple ripple-1"></div>
<div class="ripple ripple-2"></div>
<div class="ripple ripple-3"></div>
```

```css
.ripple {
  position: absolute;
  left: 50%;
  top: 50%; /* click-target center */
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border: 2px solid {rippleColor};
  transform: translate(-50%, -50%) scale(0);
  opacity: 0;
  pointer-events: none;
}
```

```js
// Phase 1 — Move: eased, not linear
tl.to(".cursor", { x: TARGET_X, y: TARGET_Y, duration: MOVE_DUR, ease: MOVE_EASE }, 0);

// Phase 2 — Click: cursor + target depress together, then return
tl.to(
  ".cursor",
  { scale: CURSOR_PRESS_SCALE, duration: PRESS_DUR, ease: "power2.in", yoyo: true, repeat: 1 },
  CLICK_AT,
);
tl.to(
  ".target-button",
  { scale: TARGET_PRESS_SCALE, duration: PRESS_DUR, ease: "power2.in", yoyo: true, repeat: 1 },
  CLICK_AT,
);

// Phase 3 — Ripple burst, N rings staggered from the click point
tl.set([".ripple-1", ".ripple-2", ".ripple-3"], { opacity: 1 }, RIPPLE_AT);
tl.to(
  [".ripple-1", ".ripple-2", ".ripple-3"],
  {
    scale: RIPPLE_SCALE,
    opacity: 0,
    duration: RIPPLE_DUR,
    ease: RIPPLE_EASE,
    stagger: RIPPLE_STAGGER,
    immediateRender: false, // holds scale 0 / opacity 0 until the click moment
  },
  RIPPLE_AT,
);
```

## Variations

- **Single ring** — one `.ripple`, no stagger; more elegant when the rest of the scene is busy.
- **Keyframed attack-decay** — a `keyframes` block ramps opacity 0 → peak → 0 across the duration; a clearer "energy radiates and dissipates" envelope.
- **Multi-ring expanding pulse** — 3 rings at 0.08 s stagger when the click is the scene's climactic moment.

## Values

| token                       | range                       | notes                                                                                                                                  |
| --------------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| MOVE_DUR                    | 0.4–1.0 s                   | short darts; long reads as a "considered click." Must end before CLICK_AT or it reads as a misclick                                    |
| MOVE_EASE                   | discrete choice             | `power2.inOut` calm · `power3.out` decisive · `back.out(1.2–1.4)` settles onto the button with a tiny recoil (higher reads cartoonish) |
| CLICK_AT                    | `MOVE_DUR + 0–0.3 s`        | zero pause reads as autopilot; >0.3 s reads as hesitation                                                                              |
| PRESS_DUR                   | 0.06–0.12 s (half; yoyo ×2) | short crisp, long mushy; must finish before the next phase needs normal scale                                                          |
| CURSOR / TARGET_PRESS_SCALE | 0.80–0.90 / 0.92–0.97       | cursor compresses MORE than the target — the cursor is the actor, the target the recipient                                             |
| RIPPLE_AT                   | `CLICK_AT + 0–0.08 s`       | simultaneous feels causal; slight delay feels acoustic                                                                                 |
| RIPPLE_DUR                  | 0.5–1.0 s                   | sharp ping vs soft sonar; must complete before anything that needs the ring gone                                                       |
| RIPPLE_SCALE                | 3–6                         | 3 stays near the click site; if the ring would exit the frame before fading, lower it                                                  |
| RIPPLE_STAGGER              | 0.06–0.12 s (or 0)          | below ~0.06 s reads as one thick ring; above ~0.12 s as separate events                                                                |
| RIPPLE_EASE                 | discrete choice             | `power2.out` standard ping · `power3.out` sharper attack · `expo.out` strong distant pulse                                             |
| TARGET_X / TARGET_Y         | layout-derived              | must match the target's visual centroid — a 4 px miss reads as missing the button                                                      |

Reference values: `../examples/cta-orbit-collapse.html` — 0.5 s move on `back.out(1.3)`, click +0.2 s, press 0.08 s at 0.85/0.95, single ring to 5× over 0.7 s `power2.out`.

## Critical Constraints

- **Move before click** — trigger the click only after the move tween settles; clicking mid-motion reads as unintentional.
- **Rings live in DOM from t=0** at the click-target center with `scale: 0` + `opacity: 0` — never conditionally rendered; `immediateRender: false` on the expand so they hold invisible until the trigger.
- **Ripple from the click point** — the button's visual center, not any element's bounding-box origin.
- **Synchronized depression** — cursor + target depress at the same position with the same duration, and both yoyo back.
- **Cursor above all content** (high z-index) for the whole sequence; `pointer-events: none` on cursor + ripples.

## See also

`orbit-3d-entry` (click as the pivot that collapses orbiters) · `center-outward-expansion` (click triggers an outward burst) · `press-release-spring` (stronger physical feel on the target) · `scale-swap-transition` (the button's post-click state change).

## Selected motion rule: gsap-effects

# GSAP Effects for HyperFrames

Drop-in animation patterns. Snippets show mechanism only, inside a standard scene clip (hyperframes-core); assume `tl` exists.

- [Typewriter](#typewriter) — character-by-character reveal with optional cursor / backspace / word rotation
- [Audio Visualizer](#audio-visualizer) — pre-extract audio data, drive Canvas/DOM rendering from the timeline

## Typewriter

Requires GSAP's TextPlugin alongside the core script:

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/TextPlugin.min.js"></script>
<script>
  gsap.registerPlugin(TextPlugin);
</script>
```

### Basic

```js
const text = "Hello, world!";
const cps = 10; // chars per second — see timing table
tl.to(
  "#typed-text",
  { text: { value: text }, duration: text.length / cps, ease: "none" },
  startTime,
);
```

### Blinking Cursor

Three rules: **one cursor visible at a time** (hide previous before showing next); **cursor must blink when idle** (after typing, during holds); **no gap between text and cursor** (elements flush in HTML).

```html
<span id="typed-text"></span><span id="cursor" class="cursor-blink">|</span>
```

```css
@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
.cursor-blink {
  animation: blink 0.8s step-end infinite;
}
.cursor-solid {
  animation: none;
  opacity: 1;
}
.cursor-hide {
  animation: none;
  opacity: 0;
}
```

Pattern: blink → solid (typing starts) → type → blink (typing done):

```js
tl.call(() => cursor.classList.replace("cursor-blink", "cursor-solid"), [], startTime);
tl.to("#typed-text", { text: { value: text }, duration: dur, ease: "none" }, startTime);
tl.call(() => cursor.classList.replace("cursor-solid", "cursor-blink"), [], startTime + dur);
```

Multi-line handoff: hide previous cursor → blink new → brief pause (~0.5s) → solid when typing. Never go `hidden → solid` (skips the idle blink).

### Backspacing

TextPlugin removes from the front — wrong for backspace. Use manual substring removal:

```js
function backspace(tl, selector, word, startTime, cps) {
  const el = document.querySelector(selector);
  const interval = 1 / cps;
  for (let i = word.length - 1; i >= 0; i--) {
    tl.call(
      () => (el.textContent = word.slice(0, i)),
      [],
      startTime + (word.length - i) * interval,
    );
  }
  return word.length * interval;
}
```

### Spacing With Static Text

A typewriter word next to static text (`<span>Ship something</span><span style="margin-left:14px"><span id="word"></span><span id="cursor">|</span></span>` in a baseline-aligned flex row): use `margin-left` on the wrapper span. Don't use flex `gap` (it spaces the cursor from the text) and don't put a trailing space in the static text (it collapses when the dynamic span is empty).

### Word Rotation

Type → hold → backspace → next word; cursor blinks during every idle moment:

```js
let offset = 0;
words.forEach((word, i) => {
  const typeDur = word.length / 10;
  // cursor: solid while typing, blink during holds (same call pattern as above)
  tl.to("#typed-text", { text: { value: word }, duration: typeDur, ease: "none" }, offset);
  offset += typeDur + 1.5; // hold
  if (i < words.length - 1) offset += backspace(tl, "#typed-text", word, offset, 20) + 0.3;
});
```

### Appending Words

Build a sentence word-by-word into the same element: keep an `accumulated` string, each step tweens `text: { value: accumulated + " " + word }` with `duration: newChars / cps`, then advances the offset.

### Timing Guide

| CPS   | Feel             | Good for                   |
| ----- | ---------------- | -------------------------- |
| 3-5   | Slow, deliberate | Dramatic reveals, suspense |
| 8-12  | Natural typing   | Dialogue, narration        |
| 15-20 | Fast, energetic  | Tech demos, code           |
| 30+   | Near-instant     | Filling long blocks        |

## Audio Visualizer

Pre-extract audio data, drive Canvas / DOM rendering from the timeline. **Do not use the Web Audio API at render time** — there's no playback during seek.

### Extract Audio Data

Bundled extractor (requires `ffmpeg` + Python `numpy`):

```bash
python skills/hyperframes-creative/scripts/extract-audio-data.py audio.mp3 -o audio-data.json
python skills/hyperframes-creative/scripts/extract-audio-data.py video.mp4 --fps 30 --bands 16 -o audio-data.json
```

Output: `{ "fps": 30, "totalFrames": 5415, "frames": [{ "time": 0.0, "rms": 0.42, "bands": [0.8, 0.6, 0.3] }] }` — `rms` (0-1) is overall loudness; `bands[]` (0-1) are frequency magnitudes, index 0 = bass, each band normalized independently.

### Loading (Synchronously)

Inline the JSON for small files (< ~500 KB), or sync XHR for large ones:

```js
const xhr = new XMLHttpRequest();
xhr.open("GET", "audio-data.json", false); // synchronous — deliberate
xhr.send();
const AUDIO_DATA = JSON.parse(xhr.responseText);
```

**Do NOT use async `fetch()`** — HyperFrames reads `window.__timelines` synchronously after page load; building the timeline inside `.then()` means it isn't ready when capture starts.

### Driving the Timeline

Canvas 2D is the workhorse (bars, waveforms, circles, gradients) — one `tl.call` per frame:

```js
const ctx = document.getElementById("viz").getContext("2d");
for (let f = 0; f < AUDIO_DATA.totalFrames; f++) {
  tl.call(
    () => {
      const frame = AUDIO_DATA.frames[f];
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      // draw using frame.rms and frame.bands
    },
    [],
    f / AUDIO_DATA.fps,
  );
}
```

WebGL / Three.js: HyperFrames patches `THREE.Clock` for deterministic time — update uniforms from audio data each frame. DOM elements: fine under ~20 elements, slower than Canvas beyond that.

### Smoothing

```js
let prev = null;
const smoothing = 0.25; // 0.1-0.2 snappy, 0.3-0.5 flowing
function smooth(f) {
  const raw = AUDIO_DATA.frames[f];
  if (!prev) prev = { rms: raw.rms, bands: [...raw.bands] };
  else {
    prev = {
      rms: prev.rms * smoothing + raw.rms * (1 - smoothing),
      bands: raw.bands.map((b, i) => prev.bands[i] * smoothing + b * (1 - smoothing)),
    };
  }
  return prev;
}
```

### Design Guide

- **Spatial mapping** — horizontal: bass left, treble right; vertical: bass bottom; circular: bass at 12 o'clock, wrap clockwise (mirror for a full circle).
- **Bass drives big moves** (scale, glow, position); **treble drives detail** (shimmer, flicker, edges); **RMS drives globals** (background brightness, overall energy).
- Pick 2-3 animated properties — more looks noisy. Keep minimums above zero so quiet sections still have life.
- **Band count**: 4 = background glow/pulse, 8 = bar charts, 16 = detailed EQ (default), 32 = dense radial layouts.
- **Layering**: stack canvases with `z-index` — a background layer driven by bass/rms under a foreground layer driven by individual bands gives depth without per-element complexity.

## Selected motion rule: physics-press-reaction

---
name: physics-press-reaction
description: Cursor + element synchronized press via subtractive spring forces — cursor lands on element, both compress together, then release. Distinct from press-release-spring (which has no cursor).
metadata:
  tags: spring, click, physics, cursor, subtractive, interaction, synchronized
---

# Physics Press Reaction (Cursor + Element Synced)

Models a real click: a cursor approaches a button, lands, and both compress IN SYNC, then release together. Distinct from [press-release-spring.md](press-release-spring.md) (no cursor — just a press happening); this rule is the COMBINED cursor + element behavior. A single `PRESS_INTENSITY` drives both: press down compresses both to `1 - PRESS_INTENSITY` via **one targets array**, release springs both back to 1.0 with overshoot. The cursor translates to the button's center BEFORE the press starts; after release it may move on or hold.

## Recipe

```html
<button class="btn" id="btn">{ctaCopy}</button>
<!-- Cursor at scene-root level so it translates freely; arrow TIP is the click
     point, so transform-origin: 0 0 — scaling around the tip keeps it stable. -->
<svg class="cursor" id="cursor" style="pointer-events: none; transform-origin: 0 0">…</svg>
```

```js
gsap.set("#cursor", { x: CURSOR_START_X, y: CURSOR_START_Y }); // off-screen / far corner

// Phase 1 — approach
tl.to(
  "#cursor",
  { x: BUTTON_CENTER_X, y: BUTTON_CENTER_Y, duration: APPROACH_DUR, ease: "power2.inOut" },
  APPROACH_START,
);

// Phase 2 — coordinated press down: ONE targets array, same scale
tl.to(
  ["#btn", "#cursor"],
  { scale: 1 - PRESS_INTENSITY, duration: PRESS_DOWN_DUR, ease: "power1.in" },
  PRESS_DOWN_AT,
);

// Phase 3 — release: both spring back together
tl.to(
  ["#btn", "#cursor"],
  { scale: 1, duration: RELEASE_DUR, ease: `back.out(${BOUNCE_FACTOR})` },
  RELEASE_AT,
);

// Phase 4 — inner glow during press, resting shadow on release (contact confirmation)
tl.to(
  "#btn",
  { boxShadow: "{btnPressedShadow}", duration: PRESS_DOWN_DUR, ease: "power1.in" },
  PRESS_DOWN_AT,
);
tl.to(
  "#btn",
  { boxShadow: "{btnRestingShadow}", duration: RELEASE_DUR, ease: "power2.out" },
  RELEASE_AT,
);

// Cursor optionally exits after the press settles
tl.to(
  "#cursor",
  { x: CURSOR_EXIT_X, y: CURSOR_EXIT_Y, duration: CURSOR_EXIT_DUR, ease: "power2.out" },
  CURSOR_EXIT_AT,
);
```

## Variations

- **Multiple-element chain press** — press button A → A triggers a swap → cursor moves to button B → presses again; each press is one full down-release sub-routine.
- **Hold press (continuous pressure)** — insert a `HOLD_DUR` window between press-down and release: both scales stay at `1 - PRESS_INTENSITY`, inner glow stays on. Suggests "thinking" or "loading."
- **Synchronized inner-glow pulse** — during the hold, pulse the inset glow with a sine driver: a `{ p: 0 }` proxy tweened to `Math.PI * GLOW_PULSE_CYCLES * 2` on `ease: "none"`, `onUpdate` writing `boxShadow` with `alpha = GLOW_BASE_ALPHA + sin(p) * GLOW_PULSE_AMP`. Suggests "processing."

## Values

| token               | range / rule                             | notes                                                                                  |
| ------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------- |
| APPROACH_START      | 0–0.3 s                                  | long delays read as a dead frame                                                       |
| APPROACH_DUR        | 0.7–1.3 s                                | faster = urgent, slower = deliberate                                                   |
| PRESS_DOWN_AT       | `= APPROACH_START + APPROACH_DUR`        | cursor arrives exactly as the press begins — avoids "tapping on air"                   |
| PRESS_DOWN_DUR      | 0.1–0.25 s                               |                                                                                        |
| RELEASE_AT          | > `PRESS_DOWN_AT + PRESS_DOWN_DUR`       | optional 0.05–0.4 s hold (or `HOLD_DUR` 0.3–0.8 s) for "thinking" interactions         |
| RELEASE_DUR         | 0.4–0.7 s                                | long enough for the overshoot to settle                                                |
| PRESS_INTENSITY     | 0.05 subtle · 0.10 standard · 0.15 heavy | applied to both cursor and button via the single targets array                         |
| BOUNCE_FACTOR       | 1.6 soft · 2.0 firm · 2.4 cartoony       |                                                                                        |
| CURSOR_START / EXIT | off-screen or far corner                 | the approach must read as motion-in, not a teleport; exit ≥ `RELEASE_AT + RELEASE_DUR` |
| BUTTON_CENTER       | measured                                 | for `place-items: center` at 1920×1080: `(960, 540)`                                   |
| BRAND_REVEAL_AT     | < `PRESS_DOWN_AT`                        | context precedes interaction                                                           |
| glow pulse          | 1–4 cycles; base α 0.15–0.3; amp 0.1–0.2 | `GLOW_BASE_ALPHA − GLOW_PULSE_AMP ≥ 0`                                                 |
| CURSOR_SIZE         | 48–96 px at 1080p                        |                                                                                        |

## Critical Constraints

- **Same press scale on cursor AND button** (one targets array) — only the button scaling makes the cursor "tap on air"; only the cursor scaling makes the button feel disconnected.
- **Cursor arrives BEFORE the press starts** — a clear "cursor over target" moment, or the press is unattributed.
- **`back.out(BOUNCE_FACTOR)` on the release, for both together** — a linear release loses the tactile feel; release MUST come after press.
- **Inner glow appears DURING press, fades on release** — outer shadow shrinks (pushed in), inner glow appears (energy concentrated).
- **Cursor `transform-origin: 0 0`** — the arrow's tip is the click point; scale around the tip keeps it stable. `pointer-events: none` on the cursor.
- **Climax dwell ≥ 1 s** — after release the composition must continue ≥ 1 s; the press is a beat, the viewer needs time to see the result.
- **No real `mouseenter` / `click` events** — HF is a render context; everything runs via the timeline.

## See also

`press-release-spring` (the BUTTON-only press; this rule layers the cursor on top) · `cursor-click-ripple` (adds a ripple at the click point) · `scale-swap-transition` (the press TRIGGERS the swap).

## Selected motion rule: svg-path-draw

---
name: svg-path-draw
description: Animate SVG paths drawing progressively using stroke-dasharray and stroke-dashoffset.
metadata:
  tags: svg, stroke, draw, path, reveal, icon, vector
---

# SVG Path Draw

Reveals an SVG shape by animating its stroke as if a pen were tracing it. Two stroke properties together: **`stroke-dasharray = <pathLength>`** makes the entire path one dash; **`stroke-dashoffset`** starts at the path length (dash shifted fully out of view → invisible) and tweens to `0` (fully drawn). The length comes from the DOM API `path.getTotalLength()` — measured, never guessed.

Works on anything with a stroke: `<path>`, `<circle>`, `<rect>`, `<line>`, `<polyline>`, `<polygon>`, `<ellipse>`.

## Recipe

```html
<!-- inside a standard scene clip -->
<svg class="logo-mark" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <path id="bar-left" d="M 60 40 L 60 160" />
  <path id="bar-right" d="M 140 40 L 140 160" />
  <path id="bar-mid" d="M 60 100 L 140 100" />
</svg>
```

```css
.logo-mark path {
  fill: none; /* outline-only draw — a fill would appear immediately and ruin the reveal */
  stroke: {accentColor};
  stroke-width: 12;
  stroke-linecap: round; /* softer endpoints */
  stroke-linejoin: round;
}
```

```js
// Setup: measure each path and set its dash pattern. Real measured geometry, not a magic number.
document.querySelectorAll(".logo-mark path").forEach((p) => {
  const len = p.getTotalLength();
  p.style.strokeDasharray = `${len}`;
  p.style.strokeDashoffset = `${len}`;
});

// Stagger draws so the eye reads continuous motion — each segment starts at
// ~70-80% of the previous segment's duration, before it finishes.
tl.to(
  "#bar-left",
  { strokeDashoffset: 0, duration: SEGMENT_DRAW_DUR, ease: "power2.out" },
  SEG_1_START,
);
tl.to(
  "#bar-right",
  { strokeDashoffset: 0, duration: SEGMENT_DRAW_DUR, ease: "power2.out" },
  SEG_2_START,
);
tl.to(
  "#bar-mid",
  { strokeDashoffset: 0, duration: FINAL_SEGMENT_DUR, ease: "power2.out" },
  SEG_3_START,
);

// Companion wordmark fades in only after the last stroke settles.
tl.to(
  ".brand-line",
  { opacity: 1, duration: BRAND_FADE_DUR, ease: "power1.out" },
  BRAND_FADE_START,
);
```

## Variations

- **Ring starting at 12 o'clock** — `<circle>` / `<rect>` strokes start at 3 o'clock by default; rotate the element `-90deg` so a progress ring draws from the top:

```html
<circle
  cx="100"
  cy="100"
  r="60"
  id="ring"
  style="transform-origin: 100px 100px; transform: rotate(-90deg)"
/>
```

- **Linear (constant-speed) draw** — `ease: "none"` for a steady-rate "real pen" trace.
- **Draw then fill** — for filled shapes, tween `fillOpacity: 0 → 1` AFTER the stroke completes (requires `fill-opacity: 0` initially and a real `fill` in CSS):

```js
tl.to(
  "#path",
  { strokeDashoffset: 0, duration: SEGMENT_DRAW_DUR, ease: "power2.out" },
  SEG_1_START,
);
tl.to(
  "#path",
  { fillOpacity: 1, duration: FILL_FADE_DUR, ease: "power1.out" },
  SEG_1_START + SEGMENT_DRAW_DUR,
);
```

## Values

| token             | range                                   | notes                                                                                              |
| ----------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------- |
| SEGMENT_DRAW_DUR  | 0.3–0.8s                                | fast snap vs deliberate pen trace; >~1s feels sluggish for a logo reveal                           |
| FINAL_SEGMENT_DUR | 60–80% of SEGMENT_DRAW_DUR              | proportional to segment length — a short connector at full duration reads slower than its siblings |
| SEG_N_START       | previous start + 70–80% of its duration | reads as continuous motion, not N isolated animations                                              |
| SEG_1_START       | 0–0.4s                                  | a small ~0.2s lead-in lets the viewer settle before motion                                         |
| BRAND_FADE_START  | ≥ last stroke end (+ ~0.2s beat)        | earlier and the wordmark competes with the draw                                                    |
| BRAND_FADE_DUR    | 0.3–0.8s                                | snap (urgent) vs glide (premium)                                                                   |

Ease families are discrete choices: **stroke draws** use `power2.out` (a hand lifting at end of stroke) or `none` for constant speed — never `back.out` / `elastic.out` (pens don't bounce). **Fades** use `power1.out`.

## Critical Constraints

- **`fill: none`** for outline-only draws — otherwise the fill appears immediately.
- **Dasharray/dashoffset = the measured `getTotalLength()`**, set at setup; requires the SVG in the DOM (inline SVG is fine; a loaded `<image>` SVG is not).
- **Complex paths**: if `getTotalLength()` looks wrong, overestimate slightly (`len * 1.05`) — too large is invisible at animation start; too small clips the end.
- **Stagger multi-path draws at ~70–80%** of the previous segment's duration.
- **A drawn line must land on something.** When the path is a connector (rail, beam, underline, callout) rather than a shape, both endpoints must sit on real elements and the draw must do a job — reveal, route, validate, or emphasize. A stroke that only decorates empty space reads as filler; attach it or cut it.

## See also

`svg-icon-enrichment` (internal parts animate after the outline draws) · `counting-dynamic-scale` (stroke draws an icon while a number counts up) · `hacker-flip-3d` (logo draws, wordmark decodes beneath).
