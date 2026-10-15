# Asset Descriptions

⚠️  No vision credentials — descriptions below are catalog-derived (alt text, headings, section context, filename) instead of Vision-generated. To get richer Vision descriptions on the next capture, set GEMINI_API_KEY (or GOOGLE_API_KEY), or HYPERFRAMES_VERTEX_PROJECT_ID plus HYPERFRAMES_VERTEX_SERVICE_ACCOUNT for Vertex service-account auth, and re-run.

The `logo-<hash>.svg` filename prefix is a structural hint (DOM said this SVG was inside a `<header>`, home-link `<a>`, or had an aria-label matching the page brand). To pick the actual brand logo without Vision, open the `logo-*` candidates in a previewer or rasterize them with `sharp` before referencing — composing a fake logo ships off-brand in the final video.

- fonts/9Bt23C1KxNDXMspQ1lPyU89-1h6ONRlW45G04pIoWQeCbA.woff2 — font file
- fonts/9Bt23C1KxNDXMspQ1lPyU89-1h6ONRlW45G07JIoWQeCbGWn.woff2 — font file
- fonts/9Bt43C1KxNDXMspQ1lPyU89-1h6ONRlW45G056IkUwCgblWmLWQ.woff2 — font file
- fonts/9Bt43C1KxNDXMspQ1lPyU89-1h6ONRlW45G056IqUwCgblWm.woff2 — font file
- fonts/9Bt73C1KxNDXMspQ1lPyU89-1h6ONRlW45G8Wbc9dCWPRl-uFQ.woff2 — font file
- fonts/9Bt73C1KxNDXMspQ1lPyU89-1h6ONRlW45G8Wbc9eiWPRl-uFV24.woff2 — font file

## App screens (Playwright, built-in demo interview, 1600x900 viewport @2x = 3200x1800 JPEG)

Real screenshots of the running app (capture-demo.cjs). Sample CV "Sam Rivera" + "Northwind Labs" job post are made up.
Layout (in 3200x1800 px): top bar y 0-130 (Record/Stop x 30-295, timer x 320-395, Me meter x 465-645, Interviewer meter x 670-960, status x 985-1290, Files/Settings/Phone x 2460-3170); transcript column x 0-1218; Answers column x 1218-3200, answer card from y ~250; Ask bar y 1655-1800.

- app-idle.jpg — idle app: Record button, empty level bars, "Ready", Files 2, empty transcript hint, "Try a demo interview".
- files-drawer.jpg — Interview files drawer listing "Sam Rivera CV" and "Northwind Labs job post" (drawer x 2320-3200; the list rows y 520-750 are clean, the drop zone above has a dashed-border glitch, crop it out).
- interviewer-speaking.jpg — Stop (recording) 0:23, Interviewer level bar high, latest transcript row "Interviewer: Nice. Can you describe a time you had to deliver a project under…" still interim (grey).
- question-detected.jpg — same question final, yellow "question" chip on the Interviewer row; Answers column still shows only the previous answer.
- answer-ready.jpg — answer for the deadline question at the top of Answers: question line, "first words in 1.0s", highlighted key line "Yeah, my capstone project, ShelfLife, is a good example…", 4 bullets built from the CV.
- me-speaking.jpg — Me level bar high, green "Me" transcript row "Yes, last semester our team had two weeks…" (interim).
- checking.jpg — interviewer statement "Our team works mostly in Python and React day to day." with grey "checking…" chip.
- no-answer-needed.jpg — same row now chipped "no answer needed" (not a question, no answer generated).

## Phone teleprompter (Playwright, iPhone 13 profile 390x844 @3x = 1170x2532 PNG, capture-phone.cjs)

Answers-only phone view: black screen, dim amber text, header "Ready · A− · A+ · Follow", bottom "Answer now". The deadline answer
is fed in and read aloud word by word as live "Me" speech; read words dim, the next words glow, the answer scrolls to keep your place.

- phone-read-00.png — fresh answer at the top: question line, "first words in 1.0s", bold key line, first bullet; nothing read yet.
- phone-read-09.png — 9 words read: "Yeah, my capstone project, ShelfLife, is a good example." dimmed.
- phone-read-22.png — key line read and scrolled up; "day." glowing; first bullet next.
- phone-read-44.png — mid first bullet; "too much in two weeks." glowing.
- phone-read-66.png — second bullet; "beats five things half done." glowing.
