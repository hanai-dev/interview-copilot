---
format: 1920x1080
duration: 51s
message: "They ask. You see the answer about 2 seconds later."
arc: Demo Loop — hook → product intro → setup → demo cycle (hear → transcribe → detect → answer → read it out) → proof → CTA
audience: Job seekers and students on a Windows PC
mode: collaborative
music: none
---

## Video direction

- **Palette** (from `frame.md`): app-screen frames (3–8) sit on `ground` #E9EDF1; title / stat / CTA frames (1, 2, 9, 10) sit on `bg` #FFFFFF. `primary` #2F5D8A is the single accent (eyebrows, accent lines, numerals, pills). Headlines `text` #1B2430, body `text-muted` #4A5563, tertiary `text-light` #7B8592. The app's role colors appear ONLY where they mean what they mean in the app: `them`/`them-tint` = Interviewer, `me`/`me-tint` = Me, `mark` yellow = detected question / key line, `rec` red = the Record/Stop dot. Frame 8 alone carries the phone's own teleprompter tones (black #000, device #0B0B0B, read #4A3D2C, next #C99A5B) because that IS the phone view. Cards: 4% tint fill, 20% border, 14px radius, no shadows.
- **Type**: Atkinson Hyperlegible only (400/700), via `frame.md` roles.
- **Motion grammar**: long-tail `power3` settles; smooth over bouncy (the only overshoots: Frame 4's inner-edge badges and the Record press release in Frame 10). Every piece reveals on its voiceover cue; nothing is dumped at t=0. Real app screenshots are never rebuilt: they are revealed with masks / wipes and moved with a virtual camera. Rebuilt UI is limited to Frame 1's bubbles, Frame 4's level meters, Frame 8's phone bezel and legend, and Frame 10's Record pill. Camera moves happen early in a shot, never as a back-half drift. During holds, at most subtle jitter.
- **Rhythm**: Frame 1 tension (typing) → Frame 2 calm title hold → Frames 3–8 the busy demo run (one surface after another, each paced to its line) → Frame 9 a single count-up that lands and holds still (the breather before the close) → Frame 10 a calm end card with one press.
- **Negative list**: no slideshow (front-load then freeze); no screensaver (many things floating); no lazy breathing / back-half pans; no bounce as house style; no glows, gradients, bokeh or purple "AI" looks; no drop shadows; no invented UI, data or logos; no narration sentences as on-screen text (captions carry the words); nothing in the bottom ~17% caption band; never frame the product as hidden or undetectable.

## Frame 1 — Mind goes blank

- scene: The interviewer's real question types itself into a blue "Interviewer" bubble on a bare ground; the "Me" bubble stays empty.
- voiceover: "They ask a tough question. Your mind goes blank."
- duration: 3.731s
- transition_in: cut
- status: animated
- src: compositions/frames/01-mind-goes-blank.html
- type: hook
- persuasion: Pain validation
- beat: tension
- blueprint: typewriter-reveal (Adapt)
- focal: the Interviewer bubble's typed question
- roles: Interviewer bubble = hero (rebuilt in the app's own style) · Me bubble = supporting
- asset_candidates:

narrativeRole: Open on the moment every interviewee dreads, in the app's own visual language (the blue Interviewer bubble), using the demo's real question.
keyMessage: You've been here — the question lands and nothing comes.

Adapt: keep the caret + character-by-character type-on signature inside UI chrome (the bubble is the input pill); change the in-place edit into the empty reply — the Me bubble arrives with a caret that blinks and types nothing. No collapse (the zoom-through transition into Frame 2 is the exit).
Scene 1 (0.0–2.1s): white field; the Interviewer bubble slides in from the left on a long-tail settle with its "Interviewer" label, then the question TYPES on character-by-character with a trailing caret → `discrete-text-sequence` (+ `context-sensitive-cursor`), finishing just after the VO's "tough question". Upper-left, asymmetric 70/30, the bubble dominates.
Scene 2 (2.1–3.7s): on "Your mind goes blank", the Me bubble rises in at lower-right → `spring-pop-entrance` (smooth settle, no overshoot); its "…" sits dim and a caret blinks three finite times beside it, typing nothing; the Interviewer caret stops blinking. Hold still.

## Frame 2 — Meet Interview Copilot

- scene: Title card "Interview Copilot" + three verbs on the left, then the real app window rises in on the right.
- voiceover: "Meet Interview Copilot. About two seconds after they finish, your answer is on screen."
- duration: 5.784s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/02-meet.html
- type: product_intro
- persuasion: Friction reduction
- beat: curiosity → relief
- blueprint: titlecard-reveal (Adapt)
- focal: assets/app-idle.jpg
- roles: app-idle = supporting product window (right, framed card) · title = hero
- asset_candidates: assets/app-idle.jpg — the idle app window (Record button, empty transcript, Answers column)

narrativeRole: Name the product and land the whole promise by beat 2 (reverse iceberg) — everything after is evidence.
keyMessage: They ask; ~2 s later the answer is on your screen.

Adapt: keep the calm card with ONE restrained move per element and a still hold; change: a two-column card (title left, real app window right) instead of a single centered title.
Scene 1 (0.0–1.3s): white field with the faint diagonal tint panel and dot grid already present; the accent line draws left→right → `svg-path-draw`; on "Meet Interview Copilot" the h1 slides up and fades in as one block → `gsap-effects` (power3). Left column, upper-middle.
Scene 2 (1.3–3.4s): on "About two seconds after they finish", the three verbs "Listens. Spots the question. Answers." reveal one by one under the title → `dynamic-content-sequencing`.
Scene 3 (3.4–5.8s): on "your answer is on screen", the app window card rises from slightly below into its right-column slot on a long-tail settle → `gsap-effects`; then hold still to the end (the allocated stillness).

## Frame 3 — Your files

- scene: The real Interview files card slides in; "Sam Rivera CV" and "Northwind Labs job post" appear as rows; the four file-type pills follow.
- voiceover: "First, add your CV and the job post. Every answer is built from them."
- duration: 5.059s
- transition_in: crossfade
- status: animated
- src: compositions/frames/03-your-files.html
- type: feature_showcase
- persuasion: Feature-to-benefit translation
- beat: control
- blueprint: device-surface-showcase (Adapt)
- focal: assets/files-drawer.jpg
- roles: files-drawer = hero surface (two crops: header, then the file rows — the glitchy drop zone stays cropped out)
- asset_candidates: assets/files-drawer.jpg — Interview files drawer with the two sample documents (crop to the list rows, the drop zone above has a glitch)

narrativeRole: Setup step that pays off in Frame 7 — the answer quotes these files, so plant them now.
keyMessage: Answers come from YOUR material, not generic advice.

Adapt: keep the held surface that advances through its own content; change: no device, the surface is the drawer card and it "advances" by revealing its rows in order.
Scene 1 (0.0–1.0s): ground; the eyebrow and "Add your files" headline slide up on the left → `gsap-effects`; the files card slides in from the right edge showing only its "Interview files" header row → `gsap-effects` (power3). Asymmetric 45/55.
Scene 2 (1.0–2.4s): on "your CV", the "Sam Rivera CV" row unmasks top→down; on "the job post", the "Northwind Labs job post" row unmasks; then "Paste text instead" → `dynamic-content-sequencing` (mask reveal of the screenshot crop, never rebuilt).
Scene 3 (2.4–5.1s): on "Every answer is built from them", the four pills (CV · Job post · Notes · Course material) reveal left→right → `dynamic-content-sequencing`; hold still.

## Frame 4 — Two channels

- scene: Split stage: left "Me" (green) with its level bar lit, right "Interviewer" (blue) with its bar lit; each side shows its real transcript row; LEFT / RIGHT pills.
- voiceover: "Press Record. Your mic is Me. Your computer's sound is the Interviewer. Two channels, so it always knows who's talking."
- duration: 7.427s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/04-two-channels.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: clarity + trust
- blueprint: comparison-split (Adapt)
- focal: the two cards together
- roles: me-speaking = supporting crop (the green Me row only) · interviewer-speaking = supporting crop (the blue Interviewer row only) · level meters = rebuilt (they move)
- asset_candidates: assets/me-speaking.jpg — Me bar high, green Me transcript row; assets/interviewer-speaking.jpg — Interviewer bar high, blue Interviewer row

narrativeRole: The mechanism the README leads with — speaker labels come from where the audio came from, not voice guessing. Builds trust before the demo.
keyMessage: It always knows who said what.

Adapt: keep the mirrored opposite-wing split-tilt entry and the badge punctuation; change: the two cards arrive one per VO cue instead of 0.2s apart, and a small Record pill press opens the shot.
Scene 1 (0.0–1.0s): ground; a small dark Record pill (app style, red dot) sits top-center above where the cards will land and PRESSES on "Press Record" → `press-release-spring`, flipping to the red Stop state; it then fades back to a quiet presence (it stays small, above the cards, never covering them).
Scene 2 (1.0–2.3s): on "Your mic is Me", the Me card enters from the LEFT wing with its mirrored rotateY tilt, settling flat → `split-tilt-cards`; its level bar fills and flickers on a deterministic pattern while its real green row wipes in left→right.
Scene 3 (2.3–4.4s): on "Your computer's sound is the Interviewer", the Interviewer card enters from the RIGHT wing (mirrored tilt) → `split-tilt-cards`; its bar flickers while the Me bar drops low (only one speaker at a time); its blue row wipes in.
Scene 4 (4.4–7.4s): on "Two channels", the LEFT then RIGHT pills pop in at each card's top-right → `spring-pop-entrance` (the lone overshoot); both bars settle to their sketch levels; hold, with at most phase-opposed subtle jitter on the two cards → `sine-wave-loop` (low amplitude, finite).

## Frame 5 — Live transcript

- scene: The real app window (top bar + transcript column); the interviewer's question appears word by word in grey (interim) inside the outlined row, while the Interviewer level bar moves; a LIVE pill.
- voiceover: "Their words show up live, as they speak."
- duration: 3.133s
- transition_in: crossfade
- status: animated
- src: compositions/frames/05-live-transcript.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: curiosity
- blueprint: device-surface-showcase (Adapt)
- focal: assets/interviewer-speaking.jpg
- roles: interviewer-speaking = hero surface (window crop with right-edge fade)
- asset_candidates: assets/interviewer-speaking.jpg — transcript with the deadline question mid-sentence (interim grey); assets/question-detected.jpg — same row, final

narrativeRole: Demo cycle step 1 — we're following ONE question: "Can you describe a time you had to deliver a project under a really tight deadline?"
keyMessage: You can read along live.

Adapt: keep the held real surface whose content advances on its own face; change: the "advance" is the live row filling in word by word (a mask over the screenshot's grey interim words, not a rebuilt UI). question-detected.jpg is not used here (it belongs to Frame 6).
Scene 1 (0.0–0.6s): the window is already in place; a short early push-in toward the bottom (live) row on a long-tail settle → `coordinate-target-zoom` (small scale, keeps the whole sketch composition in frame).
Scene 2 (0.3–2.3s): on "show up live, as they speak", the grey interim words in the outlined Interviewer row reveal word by word, left→right ("Nice. Can you describe a time you had to") → `dynamic-content-sequencing` (a row-tint cover retreating word by word over the screenshot); the outline fades in around the row with the first word; the LIVE pill pops in with its red dot → `spring-pop-entrance` (smooth).
Scene 3 (2.3–3.1s): hold still; the red LIVE dot dims and brightens twice (finite).

## Frame 6 — It spots the question

- scene: The transcript column; the camera moves from the "no answer needed" chip (small talk) down to the yellow "question" chip on the deadline question; side pills label each.
- voiceover: "Small talk gets skipped. A real question gets flagged."
- duration: 4.007s
- transition_in: crossfade
- status: animated
- src: compositions/frames/06-spots-the-question.html
- type: feature_showcase
- persuasion: Negative contrast
- beat: intrigue → confidence
- blueprint: camera-journey (Adapt)
- focal: assets/question-detected.jpg
- roles: question-detected = the world the camera travels (transcript column crop)
- asset_candidates: assets/question-detected.jpg — "no answer needed" chip on "Hi… can you hear me okay?" and yellow "question" chip on the deadline question

narrativeRole: Demo cycle step 2 — the app decides when a question was asked, so it doesn't spam answers.
keyMessage: It answers questions, not chatter.

Adapt: keep the multi-leg cursorless camera (dive in → travel to the consequence → land at rest); change: the world is one transcript column, and the journey ends by pulling back to the confirmed sketch framing.
Scene 1 (0.0–1.5s): the camera starts pushed in (~1.3×) on the top row → `viewport-change`; on "Small talk gets skipped" the grey "small talk · skipped" pill slides in at right with its tick line extending toward the "no answer needed" chip; the chip gets a thin circle marker → `css-marker-patterns`.
Scene 2 (1.5–2.4s): on "A real question", the camera travels DOWN the column to the deadline-question row → `multi-phase-camera` (one decisive pan, power3).
Scene 3 (2.4–4.0s): on "gets flagged", a yellow highlight sweep runs over the row's "question" chip → `css-marker-patterns`, the yellow "question · flagged" pill pops at right with its tick → `spring-pop-entrance` (smooth); the camera eases back out to the full sketch framing (both pills and the whole column visible) and holds.

## Frame 7 — The answer streams in

- scene: The real answer card; the answer reveals like a stream — the highlighted key line ("Yeah, my capstone project, ShelfLife…") then the bullets — and a "built from" pill names the two files.
- voiceover: "And your answer streams in. The key line highlighted, talking points from your own CV underneath."
- duration: 6.56s
- transition_in: crossfade
- status: animated
- src: compositions/frames/07-answer-streams.html
- type: benefit_highlight
- persuasion: Show-don't-tell proof
- beat: relief + control
- blueprint: camera-journey (Adapt)
- focal: assets/answer-ready.jpg
- roles: answer-ready = hero surface (answer card crop)
- asset_candidates: assets/answer-ready.jpg — deadline answer at the top of Answers with highlighted key line, 4 CV-based bullets, "first words in 1.0s"

narrativeRole: The payoff of the demo cycle and of Frame 3 — ShelfLife, the two-week deadline and the award all come from the sample CV.
keyMessage: A usable answer, grounded in your own experience.

Adapt: keep the cause→effect journey (the question at the top of the card is the cause; the camera lands on the payoff); change: the consequence is the answer text revealing in place as a stream, with only a short early camera settle.
Scene 1 (0.0–1.8s): the card is in place with only its question line + "first words in 1.0s" visible; a short early settle (slight scale-down to rest) → `multi-phase-camera`; on "your answer streams in", the highlighted key line unmasks left→right line by line like streaming text, a small dark caret riding the reveal edge → `dynamic-content-sequencing` (+ `context-sensitive-cursor`).
Scene 2 (1.8–3.2s): on "The key line highlighted", the key line's yellow highlight gets a brief brightness lift (a one-time pass, not a glow).
Scene 3 (3.2–5.2s): on "talking points from your own CV", the four bullets unmask one after another top→down → `dynamic-content-sequencing`; on "your own CV", the "built from Sam Rivera CV + Northwind Labs job post" pill slides up below the card → `gsap-effects`.
Scene 4 (5.2–6.6s): hold still on the full answer.

## Frame 8 — Read it from your phone

- scene: A phone in the teleprompter view (black screen, dim amber answer) scrolls as the voice reads: read words dim, the next words glow. Left: "On your phone" eyebrow, "Teleprompter" headline, read / next legend, QR pill.
- voiceover: "On your phone, it's a dim teleprompter. It follows your voice and keeps your place as you read."
- duration: 6.027s
- transition_in: crossfade
- status: animated
- src: compositions/frames/08-phone-teleprompter.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: control + ease
- blueprint: device-surface-showcase (Reproduce)
- focal: the phone (its screen cycles the four captures)
- roles: phone-read-00 / 22 / 44 / 66 = the phone screen's successive states (stacked inside the screen, never rebuilt) · phone bezel + legend = rebuilt
- asset_candidates: assets/phone-read-00.png — teleprompter, fresh answer, nothing read; assets/phone-read-22.png — key line read, "day." glowing; assets/phone-read-44.png — mid first bullet glowing; assets/phone-read-66.png — second bullet glowing

narrativeRole: The last step of the one question's journey: the same answer, read aloud from the phone, with the app keeping your place. Added at the user's request after the board was approved.
keyMessage: Read it out without losing your place.

Reproduce: the device held as hero while its screens advance through a real flow (floating device, stepwise screens).
Scene 1 (0.0–1.4s): ground; the phone slides in from the right with a slight tilt that settles flat → `gsap-effects` (power3), screen showing phone-read-00 (fresh answer); on "On your phone" the eyebrow slides up, then on "dim teleprompter" the "Teleprompter" headline → `gsap-effects`. Asymmetric 55/45 (text left, phone right).
Scene 2 (1.4–2.6s): the screen holds on the fresh answer.
Scene 3 (2.6–5.0s): on "It follows your voice", the screen advances 00 → 22 → 44 → 66, each a short upward scroll-crossfade (outgoing drifts up and fades as the incoming settles) spaced through "and keeps your place as you read" → `dynamic-content-sequencing`; with the first advance the "read" then "next" legend pills reveal → `spring-pop-entrance` (smooth); on "as you read" the "Scan the QR code to open it" pill slides up → `gsap-effects`.
Scene 4 (5.0–6.0s): hold still on phone-read-66.

## Frame 9 — About two seconds

- scene: One big count-up "~2s" with the eyebrow "their last word to your first line"; two metric cards add it up: "~1s" pause that ends their turn + "1.0s" to the answer's first words.
- voiceover: "Their last word to your first line: about two seconds."
- duration: 3.872s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/09-two-seconds.html
- type: benefit_highlight
- persuasion: Statistical proof
- beat: confidence
- blueprint: dataviz-countup (Adapt)
- focal: the "~2s" hero numeral
- roles: no image asset — the 1.0s figure is the app's own measurement from answer-ready.jpg, restated as a metric card
- asset_candidates: assets/answer-ready.jpg — crop of the "first words in 1.0s" meta line as the receipt

narrativeRole: Restate the message as a number. README: answers start ~1.5–3 s after the interviewer finishes; the app measures first words from turn close (≈1 s of silence closes a turn).
keyMessage: About two seconds.

Adapt: keep the hero number counting up while its scale grows, landing as one beat; change: no ring or chart — the two metric cards are the paired graphic, and the "push-through" is a single early push on the hero.
Scene 1 (0.0–1.6s): white field; the eyebrow is present as the VO says "Their last word to your first line"; the "~1s" card slides in at right → `gsap-effects`, then the "+" and the "1.0s" card → `gsap-effects`, its number counting 0.0 → 1.0 → `counting-dynamic-scale`.
Scene 2 (1.6–2.6s): on "about two seconds", the hero counts up 0 → 2 and grows to its final size, landing as "~2s" exactly on the word → `counting-dynamic-scale`, with one short early push-in on the hero → `multi-phase-camera`.
Scene 3 (2.6–3.9s): "measured in the demo interview" fades up beneath the hero → `gsap-effects`; hold still (the deliberate breather before the close).

## Frame 10 — Press Record

- scene: The app's dark Record pill under the "Interview Copilot" wordmark; a cursor presses it and it flips to the red Stop state. Small colophon line underneath.
- voiceover: "Interview Copilot. Try the demo interview, then press Record."
- duration: 5.248s
- transition_in: crossfade
- status: animated
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
