// C2O concept explainers: tiny SVG scene engine, filmed by the video pipeline.
//
// A page defines labels in both languages and a set of scenes:
//
//   EX.labels({ en: {...}, fr: {...} });
//   EX.scene("accept", (beat, secs) => { beat(0.1, () => EX.show("chip-11")); ... });
//
// The storyboard step calls  js: "EX.play('accept', ${say})"  — ${say} is that
// step's narration length in seconds, so beat(0.5, fn) fires half-way through
// what the narrator says. Scenes only add to the picture; the page builds the
// whole stage once, hidden, and scenes reveal and move things.
//
// Identifiers (TC(3,27), S1, SID) stay English in both languages, as on the
// consoles; prose labels come from the label table (?lang=fr).
/* global window, document */
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const params = new URLSearchParams(window.location.search);
  const lang = params.get("lang") === "fr" ? "fr" : "en";
  let L = { en: {}, fr: {} };
  const scenes = {};
  let timers = [];

  function t(key) {
    const v = (L[lang] && L[lang][key]) || (L.en && L.en[key]);
    return v === undefined ? key : v;
  }

  function el(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "text") n.textContent = v;
      else if (k === "label") n.textContent = t(v);
      else n.setAttribute(k, v);
    }
    if (parent) (typeof parent === "string" ? document.getElementById(parent) : parent).appendChild(n);
    return n;
  }

  function $(id) {
    const n = typeof id === "string" ? document.getElementById(id) : id;
    if (!n) throw new Error("explainer: no element #" + id);
    return n;
  }

  function show(id, ms) {
    const n = $(id);
    n.style.transition = `opacity ${ms === undefined ? 450 : ms}ms ease`;
    n.classList.remove("ex-hidden");
    n.style.opacity = 1;
  }
  function hide(id, ms) {
    const n = $(id);
    n.style.transition = `opacity ${ms === undefined ? 350 : ms}ms ease`;
    n.style.opacity = 0;
  }
  function dim(id, on) { $(id).classList.toggle("ex-dim", on !== false); }
  function mark(id, cls, on) { $(id).classList.toggle(cls, on !== false); }
  function text(id, key) { $(id).textContent = t(key); }
  function raw(id, s) { $(id).textContent = s; }

  // Move a group to (x, y) over ms (SVG transform, eased).
  function move(id, x, y, ms) {
    const n = $(id);
    n.style.transition = `transform ${ms || 900}ms cubic-bezier(.45,.05,.35,1), opacity 400ms ease`;
    n.style.transform = `translate(${x}px, ${y}px)`;
  }
  // Fly a group along straight segments [[x,y],...] in ms; resolves at the end.
  function fly(id, pts, ms) {
    const n = $(id);
    n.style.transition = "none";
    const frames = pts.map(([x, y]) => ({ transform: `translate(${x}px, ${y}px)` }));
    const a = n.animate(frames, { duration: ms || 1200, easing: "ease-in-out", fill: "forwards" });
    show(n, 200);
    return a.finished;
  }
  function pulse(id, times) {
    const n = $(id);
    n.animate([{ opacity: 1 }, { opacity: 0.25 }, { opacity: 1 }],
              { duration: 700, iterations: times || 2 });
  }
  // Draw a path or line progressively.
  function draw(id, ms) {
    const n = $(id);
    const len = n.getTotalLength ? n.getTotalLength() : 1000;
    n.style.transition = "none";
    n.style.strokeDasharray = len;
    n.style.strokeDashoffset = len;
    show(n, 0);
    n.getBoundingClientRect();
    n.style.transition = `stroke-dashoffset ${ms || 900}ms ease`;
    n.style.strokeDashoffset = 0;
  }
  // Count a number in a text node from a to b over ms, with a formatter.
  function count(id, a, b, ms, fmt) {
    const n = $(id), t0 = performance.now(), f = fmt || ((v) => v.toFixed(0));
    function tick(now) {
      const k = Math.min(1, (now - t0) / (ms || 1000));
      n.textContent = f(a + (b - a) * k);
      if (k < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  function play(name, secs) {
    const fn = scenes[name];
    if (!fn) throw new Error("explainer: no scene " + name);
    const s = Math.max(2, Number(secs) || 8);
    const beat = (frac, f) => timers.push(setTimeout(f, Math.max(0, frac) * s * 1000));
    document.body.dataset.scene = name;
    fn(beat, s);
  }

  function labels(tbl) {
    L = tbl;
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-t]").forEach((n) => { n.textContent = t(n.dataset.t); });
  }

  window.EX = { lang, t, el, $, show, hide, dim, mark, text, raw, move, fly, pulse, draw, count,
                play, labels, scene: (name, fn) => { scenes[name] = fn; }, scenes };
})();
