// Follows your voice through an answer: given the words you say (live speech-to-text, mistakes
// and all), where in the answer are you? Used by the phone view; tested in tests/follow.test.cjs.
(function (root) {
  "use strict";
  const LOOKAHEAD = 10;  // how far ahead one spoken word may move the position
  const STOP = new Set(("a an the and or but so of to in on at for with by from as is are was were be been it " +
    "this that these those i me my we our you your they them their there then than just not no do does did " +
    "can could would will should if when what which who how also about like um uh yeah okay oh well let").split(" "));

  function norm(word) {
    return String(word).toLowerCase().replace(/’/g, "'").replace(/'(s|d|ll|re|ve|m)\b/g, "").replace(/[^a-z0-9]/g, "");
  }

  function lev(a, b) {
    let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
    for (let i = 1; i <= a.length; i++) {
      const cur = [i];
      for (let j = 1; j <= b.length; j++) cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      prev = cur;
    }
    return prev[b.length];
  }

  // Speech-to-text gets words slightly wrong ("rancor" for "ranker", "lessons" for "lesson's").
  function similar(a, b) {
    if (a === b) return true;
    if (a.length < 3 || b.length < 3) return false;
    if (a.length >= 4 && b.length >= 4 && a.slice(0, 4) === b.slice(0, 4)) return true;
    const limit = Math.max(a.length, b.length) >= 6 ? 2 : 1;
    return Math.abs(a.length - b.length) <= limit && lev(a, b) <= limit;
  }

  class Follower {
    constructor(words) {
      this.words = words.map(norm);
      this.pos = 0;      // index of the next answer word to be read
      this.misses = 0;   // content words in a row that didn't match
      this.recent = [];  // last spoken words, for re-syncing
    }

    // Returns true when the position moved.
    feed(word) {
      const w = norm(word);
      if (!w) return false;
      this.recent = [...this.recent.slice(-5), w];
      const stop = STOP.has(w);
      const end = Math.min(this.words.length, this.pos + LOOKAHEAD);
      for (let j = this.pos; j < end; j++) {
        if (stop && j > this.pos + 1) break;  // small words only count right at the cursor
        if (similar(w, this.words[j])) { this.pos = j + 1; this.misses = 0; return true; }
      }
      if (!stop) this.misses++;
      return this.misses >= 3 && this.resync();
    }

    // Lost (skipped a bullet, or several words misheard): find where the last few content words were read.
    resync() {
      const said = this.recent.filter(w => !STOP.has(w));
      if (said.length < 3) return false;
      let best = null;
      for (let e = this.pos + 1; e <= this.words.length; e++) {
        const n = this.matchesEndingAt(said, e);
        if (n >= 3 && (!best || n > best.n)) best = { n, e };
      }
      if (!best) return false;
      this.pos = best.e;
      this.misses = 0;
      return true;
    }

    matchesEndingAt(said, e) {
      if (!similar(said[said.length - 1], this.words[e - 1])) return 0;
      const floor = Math.max(this.pos, e - 14);
      let n = 1, j = e - 2;
      for (let i = said.length - 2; i >= 0 && j >= floor; i--) {
        for (let k = j; k >= floor; k--) if (similar(said[i], this.words[k])) { n++; j = k - 1; break; }
      }
      return n;
    }
  }

  // Speaking rate from when words arrive; used to keep scrolling while you talk but nothing matches.
  class Pace {
    constructor(windowS = 10) { this.windowS = windowS; this.times = []; }
    word(t) {
      this.times.push(t);
      while (t - this.times[0] > this.windowS) this.times.shift();
    }
    rate(now) {
      const t = this.times.filter(x => now - x <= this.windowS);
      const span = t.length >= 4 ? t[t.length - 1] - t[0] : 0;
      return span > 0 ? (t.length - 1) / span : 2.5;  // words per second; 2.5 is a typical speaking pace
    }
    speaking(now) { return this.times.length > 0 && now - this.times[this.times.length - 1] <= 1.5; }
  }

  const api = { norm, similar, Follower, Pace };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.Follow = api;
})(this);
