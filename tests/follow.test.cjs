// Voice follower golden cases: real answers and what was actually said while reading them
// (Deepgram transcripts from practice sessions, recognition mistakes included).
// Run: node --test
const test = require("node:test");
const assert = require("node:assert");
const { Follower, Pace, norm } = require("../static/follow.js");

const words = s => s.replace(/\*\*/g, "").replace(/^\s*-\s+/gm, "").split(/\s+/).filter(w => norm(w));

// Index just past the first occurrence of phrase in tokens.
function after(tokens, phrase) {
  const p = words(phrase).map(norm), t = tokens.map(norm);
  for (let i = 0; i + p.length <= t.length; i++) if (p.every((w, k) => t[i + k] === w)) return i + p.length;
  throw new Error(`phrase not found: ${phrase}`);
}

function read(answer, spoken, checkpoints, { endWithin = 3 } = {}) {
  const ans = words(answer), said = words(spoken), f = new Follower(ans);
  const stops = checkpoints.map(([s, a]) => ({ at: after(said, s), want: after(ans, a), s }));
  said.forEach((w, i) => {
    f.feed(w);
    for (const c of stops) if (c.at === i + 1) {
      assert.ok(f.pos >= c.want - 1 && f.pos <= c.want + 3,
        `after saying "${c.s}": position ${f.pos}, expected ${c.want} (-1..+3) at "${ans.slice(c.want - 3, c.want).join(" ")}"`);
    }
  });
  if (endWithin != null) assert.ok(f.pos >= ans.length - endWithin, `ended at ${f.pos} of ${ans.length}`);
  return f;
}

const LABELING = `**So I'd label at two levels, what the student wrote and which misconception it shows, and I'd have the math specialists double-label everything.**

- The labels are a verbatim transcription of each crop with mistakes kept, then misconception codes from that lesson's pack with the evidence for each one, or an abstain when nothing fits. Tying codes to a pack keeps the labels consistent across specialists.
- The process is that two specialists label each submission independently in Label Studio, and a third one resolves disagreements. I'd start with about 1,000 consented submissions, plus 300 worksheets where specialists plant known mistakes.
- To coordinate the team, I'd run a short calibration round first on a shared batch, so we agree on code definitions before scaling. Then I'd track agreement every week and add flagged cases to the set.
- I'd keep a golden set that never goes into training, because it's what we measure launch gates against.`;

const KINDS = `**So I'd say there are really three kinds of labels, and they match the steps in the pipeline.**

- First is the verbatim transcription of each cropped problem, with the student's mistakes kept, because the reader model has to learn to copy what's there and not fix it.
- Second are the misconception codes from that lesson's pack, with the evidence for each one, or an abstain when nothing fits, since that teaches the ranker to stay quiet instead of over-diagnosing.
- Third is a usable rating on the final paragraph, plus teacher and specialist corrections as preference pairs, so we can improve the writing and not just the diagnosis.
- I'd also label the planted-mistake worksheets, where we already know the right answer, because they give us a clean check on recall.`;

const IDEMPOTENCY = `**So the submission ID is the idempotency key, and I'd enforce it at the write, not just the queue.**

- Worker claims job first, conditional write on submission ID, loser drops out
- SQS standard is at-least-once, so duplicates will happen
- Django result POST is upsert on submission ID, second write is a no-op
- Visibility timeout longer than p95, heartbeat for slow jobs
- Dead letter after few retries, alarm on it`;

const METADATA = `**Yeah, there's additional metadata too, not just the insights.**

- I'd tag each submission with the lesson, unit, and problem, and the photo quality, like blurry, scratch paper, or a crop that's cut off. That way I can slice results later and see where the model actually struggles.
- I'd also record how confident the specialist was, and whether the two labelers agreed, because disagreement tells me which codes are fuzzy and need a clearer definition.
- For the insight itself, I'd keep the usable rating and whether each claim was supported. Then the corrections go in as preference pairs, so we learn from what the specialist changed.
- And I'd mark the consent status on every item, so only consented work can go into evals or tuning.`;

test("L1 real reading: labeling process (restarts, 'its crap', 'resolved this agreement')", () => {
  read(LABELING, `So I labeled I label it at two levels, what the student wrote and which misconception it shows. And I have the math specialist double label everything. But The labels are a verbatim transcription of its crap with with mistakes kept then misconception codes from that lessons pack with the evidence of for each one as an abs... Or an abstain when nothing fits, trying to codes tying codes to a pack keeps the levels consistent across specialist. So the process is that two specialists label its submission independently. In Label Studio or something like that. And the third one resolved this agreement. So I start with about 1,000 consented submissions plus 300 worksheets for specialist plus non... Plat down mistakes. To coordinate the team, I run a short calibration around first and assured batch. So we agree on code definitions before scaling then I track agreement every week and add flag cases to the set I keep a golden set that never goes into training because it's that what we measure lads against, during LAN. So it's how I measure it against`, [
    ["which misconception it shows", "which misconception it shows,"],
    ["keeps the levels consistent across specialist", "consistent across specialists."],
    ["the third one resolved this agreement", "resolves disagreements."],
    ["add flag cases to the set", "flagged cases to the set."],
  ]);
});

test("L1 real reading: three kinds of labels ('rancor', 'usable usable')", () => {
  read(KINDS, `Okay. So I'd say there are three kind of labels and they match the steps in the pipeline. First is the verbatim transcription for each problem, which the students mistakes kept because the reader model has to learn to copy what's there and not to fix it. Second are the misconceptions codes from that lessons pack. With the evidence for each one or an abstain when nothing fits. Since the teacher teaches the rancor to stay quiet instead of over diagnosing Third is a usable usable rating the final paragraph, plus teacher and specialist corrections are preference pair so we can improve the writing and adjust the diagnosis. I also labeled the planted mistakes worksheets where we, already know the right answer because they gives us clean check on recall.`, [
    ["steps in the pipeline", "steps in the pipeline."],
    ["not to fix it", "not fix it."],
    ["stay quiet instead of over diagnosing", "instead of over-diagnosing."],
    ["clean check on recall", "clean check on recall."],
  ]);
});

test("L1 real reading: idempotency note-style bullets ('absurd', 'now up', 'furitize')", () => {
  read(IDEMPOTENCY, `Yeah. For... So the submission ID is the idempotency key, and I'll enforce it at the right, not just So the worker claims, job first and it conditional right on submission ID, and the loser drops out. SQS standard is at least one, so duplicates will happen. Django result post is absurd on submission ID. Second right is now up. Visibility time out longer than p 95. Heartbeat for slow jobs. Dead letter after furitize. Alarm on it.`, [
    ["the idempotency key", "the idempotency key,"],
    ["loser drops out", "loser drops out"],
    ["duplicates will happen", "duplicates will happen"],
    ["Heartbeat for slow jobs", "heartbeat for slow jobs"],
  ]);
});

test("L1 real reading: metadata ('content status', 'considered work')", () => {
  read(METADATA, `Yeah. There's additional metadata, though, not just the insights. I tag each submissions with a lesson unit and problem on the photo quality, like blurry sketch, tape, scratch paper or a crop that cuts off. That way, I can slice results later and see where the model actually struggles. I also record how confident, like, the specialist was. Specialist was and whether the two labelers agreed because disagreement tells me which codes are fuzzy and need clear definition. For the insight itself, I keep the usable rating and whether its claim was supported. Then the correction go in the preference pair. So we learn from specialist chains and and I marked the content status that I've arrived. So only considered work, good, involves, or tuning.`, [
    ["model actually struggles", "model actually struggles."],
    ["need clear definition", "clearer definition."],
    ["whether its claim was supported", "claim was supported."],
  ]);
});

test("L2 off-script talk does not move the position", () => {
  const f = new Follower(words(IDEMPOTENCY));
  for (const w of words("um let me think about that for a second honestly I mean it depends")) f.feed(w);
  assert.ok(f.pos <= 2, `moved to ${f.pos}`);
});

test("L3 skipping ahead a bullet re-syncs to what is being read", () => {
  read(IDEMPOTENCY, `So the submission ID is the idempotency key and I'd enforce it at the write not just the queue. Worker claims job first conditional write on submission ID loser drops out. Visibility timeout longer than p95 heartbeat for slow jobs`, [
    ["loser drops out", "loser drops out"],
    ["heartbeat for slow jobs", "heartbeat for slow jobs"],
  ], { endWithin: null });
});

test("Pace: speaking rate from word arrivals, and silence detection", () => {
  const p = new Pace();
  assert.strictEqual(p.rate(0), 2.5, "default before any speech");
  for (let i = 0; i < 20; i++) p.word(i * 0.4);  // 2.5 words/s ... then measured
  assert.ok(Math.abs(p.rate(8) - 2.5) < 0.3, `rate ${p.rate(8)}`);
  const q = new Pace();
  for (let i = 0; i < 20; i++) q.word(i * 0.25);  // 4 words/s
  assert.ok(Math.abs(q.rate(5) - 4) < 0.4, `rate ${q.rate(5)}`);
  assert.ok(q.speaking(5.2) && !q.speaking(7), "talking within 1.5 s of the last word");
});
