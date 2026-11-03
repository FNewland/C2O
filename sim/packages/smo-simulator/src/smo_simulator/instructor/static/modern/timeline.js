/* ============================================================================
 * C2O INSTRUCTOR — the one timeline (SVG, no animation loop)
 * ============================================================================
 * One time axis carries the scenario phase, the injects (scheduled ahead of
 * "now", fired, cleared), on-board alarms (and when they reached the
 * ground), telecommands, procedures, link and sun, the instructor's own
 * actions, console staffing and the voice loops. Ground-side items (alarm
 * acknowledgements, procedure steps, GO/NO-GO, desk staffing, who talked on
 * which loop) come from the MCS's anonymous ground-activity summary
 * (/api/seats/activity, served on the ground by the GSG; positions only, no
 * names). Without it those lanes say "not available on the simulator side". Live,
 * it is the instructor's situational awareness; after the run the debrief
 * replays the same picture with a cursor (INSTRUCTOR_CONSOLE_DESIGN.md §4).
 *
 *   mountTimeline(el, { t, onSelect }) -> { update(model), destroy() }
 *   model = { items, pending, nowTs, windowS, futureFrac, segment, cursorTs,
 *             speed, selectedSeq }
 *
 * Pure helpers (spans, layout) are exported for tests and the debrief.
 * ========================================================================== */

export const LANES = [
  { id: "phase", label: "Phase & modes" },
  { id: "fault", label: "Injects" },
  { id: "alarm", label: "On-board alarms" },
  { id: "tc", label: "Telecommands" },
  { id: "proc", label: "Procedures" },
  { id: "link", label: "Link & sun" },
  { id: "instr", label: "Instructor" },
  { id: "crew", label: "Consoles" },
  { id: "voice", label: "Voice loops" },
];
// i18n-keys (dynamic labels)
export const DYNAMIC_KEYS = ["Phase & modes", "Injects", "On-board alarms", "Telecommands", "Procedures",
  "Link & sun", "Instructor", "Consoles", "Voice loops",
  "not available on the simulator side", "now", "contact", "eclipse", "{{n}} gated",
  "talking", "ground activity not available: {{why}}",
];

/** Talk spans per loop from ground "talk" items (+ talk still open now). */
export function talkSpans(items, talking, nowTs) {
  const out = [];
  for (const it of items) if (it.lane === "voice" && it.kind === "talk") out.push([it.ts, it.ts_end ?? it.ts, it]);
  for (const tk of talking || []) out.push([tk.since, nowTs, { position: tk.position, loop: tk.loop, open: true }]);
  return out;
}

const LABEL_W = 112;
const LANE_H = 17;
const AXIS_H = 16;

const svgEsc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/** Contact and eclipse spans from AOS/LOS and ecl_in/ecl_out points. */
export function spans(items, nowTs) {
  const out = { contact: [], eclipse: [] };
  const sorted = [...items].sort((a, b) => a.ts - b.ts);
  let aos = null, ecl = null;
  for (const it of sorted) {
    if (it.kind === "aos") aos = it.ts;
    else if (it.kind === "los") { out.contact.push([aos ?? null, it.ts]); aos = null; }
    else if (it.kind === "ecl_in") ecl = it.ts;
    else if (it.kind === "ecl_out") { out.eclipse.push([ecl ?? null, it.ts]); ecl = null; }
  }
  if (aos !== null) out.contact.push([aos, nowTs]);
  if (ecl !== null) out.eclipse.push([ecl, nowTs]);
  return out;
}

/** Window [t0, t1] around now: (1 - futureFrac) of it in the past. */
export function windowRange(nowTs, windowS, futureFrac = 0.2) {
  const f = Math.max(0, Math.min(0.6, futureFrac));
  return [nowTs - windowS * (1 - f), nowTs + windowS * f];
}

/** Which mark to draw for an item: {shape, cls}. */
export function markOf(it) {
  const k = it.kind;
  // ground-side (anonymous MCS activity): squares, so they read as "the team"
  if (k === "g_ack") return { shape: "sq", cls: "m-ground" };
  if (k === "g_step") return (it.result === "PASSED") ? { shape: "sq", cls: "m-ground" }
    : (it.result === "SKIPPED") ? { shape: "dot-o", cls: "m-info" } : { shape: "x", cls: "m-alarm" };
  if (k === "g_proc") return { shape: "dia", cls: it.outcome === "failed" || it.outcome === "aborted" ? "m-warn" : "m-ground" };
  if (k === "g_poll" || k === "g_result") return { shape: "flag", cls: it.outcome === "NO_GO" ? "m-warn" : "m-ground" };
  if (k === "g_vote") return { shape: "tick", cls: it.response === "GO" ? "m-ground" : "m-warn" };
  if (k === "seat") return it.state === "vacant" ? { shape: "x", cls: "m-alarm" }
    : it.state === "staffed" ? { shape: "tick", cls: "m-ground" } : { shape: "ring", cls: "m-warn" };
  if (it.lane === "fault") {
    if (k === "inject") return { shape: "tri", cls: "m-inject" };
    if (k === "clear") return { shape: "tri-o", cls: "m-clear" };
    if (k === "diverge") return { shape: "dot", cls: "m-inject" };
    if (k === "sched_fire") return { shape: "bar", cls: "m-inject" };
    return { shape: "dot-o", cls: "m-inject" };
  }
  if (it.lane === "alarm") {
    if (k === "ev_down") return { shape: "tick", cls: "m-down" };
    if (k === "missed_cue") return { shape: "ring", cls: "m-warn" };
    return it.sev >= 3 ? { shape: "tri", cls: "m-alarm" }
      : it.sev === 2 ? { shape: "tri-o", cls: "m-warn" } : { shape: "dot", cls: "m-info" };
  }
  if (it.lane === "tc") {
    if (k === "tc_rx") return { shape: "bar", cls: "m-tc" };
    if (k === "tc_rej" || k === "tc_fail" || k === "tc_link") return { shape: "x", cls: "m-alarm" };
    return { shape: "tick", cls: "m-info" };
  }
  if (it.lane === "phase") return { shape: "dia", cls: it.sev >= 3 ? "m-alarm" : "m-phase" };
  if (it.lane === "instr") {
    if (k === "anomaly") return { shape: "ring", cls: "m-warn" };
    if (k === "bookmark") return { shape: "flag", cls: "m-instr" };
    return { shape: "sq", cls: "m-instr" };
  }
  if (it.lane === "link") return { shape: "tick", cls: "m-info" };
  return { shape: "dot", cls: it.sev >= 2 ? "m-warn" : "m-info" };
}

function shape(sh, x, y, cls) {
  const c = `class="${cls}"`;
  switch (sh) {
    case "tri": return `<path ${c} d="M${x} ${y - 6}L${x + 5} ${y + 4}L${x - 5} ${y + 4}Z"/>`;
    case "tri-o": return `<path ${c} fill="none" stroke-width="1.5" d="M${x} ${y - 5}L${x + 4.5} ${y + 3.5}L${x - 4.5} ${y + 3.5}Z"/>`;
    case "dia": return `<path ${c} d="M${x} ${y - 5}L${x + 5} ${y}L${x} ${y + 5}L${x - 5} ${y}Z"/>`;
    case "sq": return `<rect ${c} x="${x - 3.5}" y="${y - 3.5}" width="7" height="7"/>`;
    case "bar": return `<rect ${c} x="${x - 1}" y="${y - 6}" width="2.5" height="12"/>`;
    case "tick": return `<rect ${c} x="${x - 0.75}" y="${y - 3}" width="1.5" height="9"/>`;
    case "x": return `<path ${c} fill="none" stroke-width="2" d="M${x - 4} ${y - 4}L${x + 4} ${y + 4}M${x + 4} ${y - 4}L${x - 4} ${y + 4}"/>`;
    case "ring": return `<circle ${c} fill="none" stroke-width="1.75" cx="${x}" cy="${y}" r="4.5"/>`;
    case "dot-o": return `<circle ${c} fill="none" stroke-width="1.5" stroke-dasharray="2 1.5" cx="${x}" cy="${y}" r="4.5"/>`;
    case "flag": return `<path ${c} d="M${x} ${y + 6}V${y - 6}L${x + 7} ${y - 3}L${x} ${y}"/>`;
    default: return `<circle ${c} cx="${x}" cy="${y}" r="3"/>`;
  }
}

function fmtHM(ts, withS) {
  const d = new Date(ts * 1000);
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getUTCHours())}:${p(d.getUTCMinutes())}${withS ? ":" + p(d.getUTCSeconds()) : ""}`;
}

function tickStep(windowS) {
  const steps = [60, 120, 300, 600, 900, 1800, 3600, 7200, 10800];
  for (const s of steps) if (windowS / s <= 8) return s;
  return 21600;
}

export function mountTimeline(el, opts = {}) {
  const t = opts.t || ((s) => s);
  el.classList.add("tl");
  let model = null;
  let width = el.clientWidth || 800;

  function render() {
    if (!model) return;
    width = Math.max(300, el.clientWidth || width);
    const W = width, plotW = W - LABEL_W - 8;
    const H = AXIS_H + LANES.length * LANE_H + 4;
    const nowTs = model.nowTs;
    const [t0, t1] = windowRange(nowTs, model.windowS || 1800, model.futureFrac ?? 0.2);
    const x = (ts) => LABEL_W + ((ts - t0) / (t1 - t0)) * plotW;
    const laneY = (id) => AXIS_H + LANES.findIndex((l) => l.id === id) * LANE_H + LANE_H / 2;
    const seg = model.segment;
    const items = (model.items || []).filter((i) => seg === undefined || i.seg === seg);
    const out = [];
    // lane backgrounds and labels
    LANES.forEach((l, i) => {
      const y = AXIS_H + i * LANE_H;
      out.push(`<rect class="tl-lane${i % 2 ? " odd" : ""}" x="${LABEL_W}" y="${y}" width="${plotW}" height="${LANE_H}"/>`);
      out.push(`<text class="tl-lbl" x="${LABEL_W - 8}" y="${y + LANE_H / 2 + 4}" text-anchor="end">${svgEsc(t(l.label))}</text>`);
    });
    // axis ticks
    const step = tickStep(model.windowS || 1800);
    for (let ts = Math.ceil(t0 / step) * step; ts <= t1; ts += step) {
      const xx = x(ts).toFixed(1);
      out.push(`<line class="tl-grid" x1="${xx}" x2="${xx}" y1="${AXIS_H - 3}" y2="${H - 4}"/>`);
      out.push(`<text class="tl-ax" x="${xx}" y="${AXIS_H - 5}" text-anchor="middle">${fmtHM(ts)}</text>`);
    }
    // link lane: contact (upper half) and eclipse (lower half) spans
    const sp = spans(items, nowTs);
    const yl = AXIS_H + LANES.findIndex((l) => l.id === "link") * LANE_H;
    for (const [a, b] of sp.contact) {
      const xa = Math.max(LABEL_W, x(a ?? t0)), xb = Math.min(LABEL_W + plotW, x(b));
      if (xb > xa) out.push(`<rect class="tl-contact" x="${xa.toFixed(1)}" y="${yl + 2}" width="${(xb - xa).toFixed(1)}" height="6"><title>${svgEsc(t("contact"))}</title></rect>`);
    }
    for (const [a, b] of sp.eclipse) {
      const xa = Math.max(LABEL_W, x(a ?? t0)), xb = Math.min(LABEL_W + plotW, x(b));
      if (xb > xa) out.push(`<rect class="tl-eclipse" x="${xa.toFixed(1)}" y="${yl + 9}" width="${(xb - xa).toFixed(1)}" height="6"><title>${svgEsc(t("eclipse"))}</title></rect>`);
    }
    // voice and consoles lanes: from the ground-activity summary, when the
    // ground answers; otherwise drawn as not available
    const ground = model.ground || {};
    const yv = AXIS_H + LANES.findIndex((l) => l.id === "voice") * LANE_H;
    const yc = AXIS_H + LANES.findIndex((l) => l.id === "crew") * LANE_H;
    if (!ground.available) {
      const why = ground.reason ? t("ground activity not available: {{why}}", { why: ground.reason })
        : t("not available on the simulator side");
      for (const y of [yc, yv]) {
        out.push(`<rect class="tl-na" x="${LABEL_W}" y="${y + 2}" width="${plotW}" height="${LANE_H - 4}"/>`);
        out.push(`<text class="tl-na-t" x="${LABEL_W + 8}" y="${y + LANE_H / 2 + 4}">${svgEsc(why)}</text>`);
      }
    } else {
      for (const [a, b, it] of talkSpans(items, ground.talking, nowTs)) {
        const xa = Math.max(LABEL_W, x(a)), xb = Math.min(LABEL_W + plotW, Math.max(x(b), x(a) + 2));
        if (xb <= LABEL_W || xa >= LABEL_W + plotW) continue;
        const label = `${it.position || ""} · ${it.loop || ""}${it.open ? " · " + t("talking") : ""}`;
        out.push(`<rect class="tl-talk${it.open ? " open" : ""}" x="${xa.toFixed(1)}" y="${yv + 3}" width="${Math.max(2, xb - xa).toFixed(1)}" height="${LANE_H - 6}"` +
          (it.seq != null ? ` data-seq="${it.seq}"` : "") + `><title>${svgEsc(fmtHM(a, true) + " · " + label)}</title></rect>`);
      }
    }
    // points
    for (const it of items) {
      if (it.ts < t0 || it.ts > t1 || it.lane === "voice") continue;
      if (it.lane === "link" && it.kind !== "aos" && it.kind !== "los") continue;
      const m = markOf(it);
      const xx = +x(it.ts).toFixed(1), yy = laneY(it.lane);
      const sel = model.selectedSeq === it.seq ? " is-sel" : "";
      out.push(`<g class="tl-pt${sel}" data-seq="${it.seq}">${shape(m.shape, xx, yy, m.cls)}` +
        `<title>${svgEsc(fmtHM(it.ts, true) + " · " + it.text)}</title></g>`);
    }
    // pending (future) injects and scenario events
    for (const p of model.pending || []) {
      if (p.ts == null || p.ts < t0 || p.ts > t1) continue;
      const xx = +x(p.ts).toFixed(1), yy = laneY(p.lane || "fault");
      out.push(`<g class="tl-pend">${shape("tri-o", xx, yy, "m-pending")}` +
        `<title>${svgEsc(fmtHM(p.ts, true) + " · " + (p.source === "scenario" ? "scenario: " : "") + p.text)}</title></g>`);
    }
    // now line and cursor
    const xn = x(nowTs).toFixed(1);
    out.push(`<line class="tl-now" x1="${xn}" x2="${xn}" y1="${AXIS_H - 2}" y2="${H - 2}"/>`);
    out.push(`<text class="tl-now-t" x="${xn}" y="${H}" text-anchor="middle">${svgEsc(t("now"))}</text>`);
    if (model.cursorTs != null && model.cursorTs >= t0 && model.cursorTs <= t1) {
      const xc = x(model.cursorTs).toFixed(1);
      out.push(`<line class="tl-cursor" x1="${xc}" x2="${xc}" y1="${AXIS_H - 2}" y2="${H - 4}"/>`);
    }
    // gated (untimed) pending items summarised at the right edge
    const gates = (model.pending || []).filter((p) => p.ts == null);
    if (gates.length) {
      out.push(`<text class="tl-gate" x="${LABEL_W + plotW - 4}" y="${laneY("fault") + 4}" text-anchor="end">` +
        `${svgEsc(t("{{n}} gated", { n: gates.length }))}<title>${svgEsc(gates.map((g) => g.text + " — " + g.gate).join("\n"))}</title></text>`);
    }
    const summary = `${items.length} events; window ${Math.round((model.windowS || 1800) / 60)} min`;
    el.innerHTML = `<svg class="tl-svg" width="${W}" height="${H + 6}" viewBox="0 0 ${W} ${H + 6}" role="img" aria-label="${svgEsc(summary)}">${out.join("")}</svg>`;
    el.__tlX = { t0, t1, plotW };
  }

  function onClick(ev) {
    const g = ev.target.closest && ev.target.closest(".tl-pt");
    if (g && opts.onSelect) { opts.onSelect(+g.dataset.seq); return; }
    if (opts.onCursor && el.__tlX) {
      const r = el.getBoundingClientRect();
      const px = ev.clientX - r.left - LABEL_W;
      if (px < 0) return;
      const { t0, t1, plotW } = el.__tlX;
      opts.onCursor(t0 + (px / plotW) * (t1 - t0));
    }
  }
  el.addEventListener("click", onClick);
  let ro = null;
  if (typeof ResizeObserver !== "undefined") {
    ro = new ResizeObserver(() => { if (Math.abs((el.clientWidth || 0) - width) > 4) render(); });
    ro.observe(el);
  }
  return {
    update(m) { model = m; render(); },
    destroy() { el.removeEventListener("click", onClick); if (ro) ro.disconnect(); el.innerHTML = ""; },
  };
}
