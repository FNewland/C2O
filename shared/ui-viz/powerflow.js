/* ============================================================================
 * C2O pictorial displays — powerflow.js  (source: shared/ui-viz/powerflow.js)
 * ============================================================================
 * Energy-flow mimic: arrays (per wing / body string) -> array regulator ->
 * bus -> load groups, with the battery charging or discharging off the bus.
 *
 *   - Line WIDTH is power on a FIXED scale (1 px = 10 W, 1.5 px minimum),
 *     never auto-scaled, so the same width means the same watts on every
 *     screen and every pass. The watts are written beside every path.
 *   - Grey at rest. Colour only for status: SoC below its minimum, a
 *     predicted depth of discharge beyond the limit, a negative orbit balance.
 *   - Stale paths keep their last width, drawn dashed in the stale ink, with
 *     their values italic + age; never-received reads "no data".
 *   - Optional dash-flow animation (opts.animate) only on paths that carry
 *     power, slow, and off under prefers-reduced-motion. Arrowheads and the
 *     words "charging"/"discharging" carry the direction without motion.
 *
 *   mount(el, { t, variant: "full" | "summary", animate, onNavigate })
 *     -> { update(powerModel), destroy() }
 *
 * powerModel = derive.js derivePower(...) (plain object; SpaceCDF can build
 * the same shape from a design's power budget).
 * ============================================================================ */
import { esc, fmt, fmtSigned, fmtDur, withUnit, stateClass, readout, s, mountFrame,
  valuesTable, tDefault, reducedMotion, uid, ensureStyle } from "./common.js";

// Labels that arrive from derive.js and are translated with t(label).
// i18n-keys
export const DYNAMIC_KEYS = [
  "+Y wing", "−Y wing", "Body +X +Y +Z", "Body −X −Y −Z",
  "Platform", "Comms", "Payload", "Thermal", "AOCS", "Propulsion",
  "OBC", "TT&C RX", "TT&C TX", "Imager", "FPA cooler", "Battery heater", "OBC heater", "AOCS wheels",
];

const W_PER_PX = 10;
const lw = (w) => (w === null || w === undefined ? 1 : Math.min(16, Math.max(1.5, w / W_PER_PX)));

const CSS = `
.vz-pf .p-flow{fill:none;stroke:var(--vz-fill);stroke-linecap:butt}
.vz-pf .p-flow.is-zero{stroke:var(--vz-line2);stroke-dasharray:2 4}
.vz-pf .p-flow.is-stale{stroke:var(--vz-stale);stroke-dasharray:6 4}
.vz-pf .p-flow.is-nodata{stroke:var(--vz-line2);stroke-dasharray:1 4}
.vz-pf .p-head{fill:var(--vz-fill)} .vz-pf .p-head.is-stale{fill:var(--vz-stale)}
.vz-pf .p-head.is-zero,.vz-pf .p-head.is-nodata{display:none}
.vz-pf .p-pulse{fill:none;stroke:var(--vz-bg);opacity:.5;stroke-dasharray:2 22;animation:vzflow 2.4s linear infinite}
@keyframes vzflow{to{stroke-dashoffset:-24}}
@media (prefers-reduced-motion:reduce){.vz-pf .p-pulse{display:none;animation:none}}
.vz-pf .p-cell{stroke:var(--vz-line2);stroke-width:1}
.vz-pf .p-panel{fill:var(--vz-s2);stroke:var(--vz-tx3);stroke-width:1}
.vz-pf .is-dark .p-panel{fill:var(--vz-bg);stroke:var(--vz-line2)}
.vz-pf .p-bus{fill:var(--vz-s3);stroke:var(--vz-tx3);stroke-width:1}
.vz-pf .p-tank{fill:var(--vz-bg);stroke:var(--vz-tx3);stroke-width:1}
.vz-pf .p-soc{fill:var(--vz-fill)}
.vz-pf .is-caution .p-soc{fill:var(--vz-warn)} .vz-pf .is-alarm .p-soc{fill:var(--vz-alarm)}
.vz-pf .p-soc.is-stale{fill:var(--vz-stale)}
.vz-pf .p-pred{stroke:var(--vz-val);stroke-width:1.5;stroke-dasharray:3 2}
.vz-pf .p-pred.is-caution{stroke:var(--vz-warn)}
.vz-pf .p-in{fill:var(--vz-fill)} .vz-pf .p-out{fill:none;stroke:var(--vz-tx2);stroke-width:1.5}
.vz-pf .p-net.is-caution{fill:var(--vz-warn)}
.vz-pf .p-off{fill:var(--vz-off);font-size:12px}
.vz-pf .p-nav{cursor:pointer}
.vz-pf .p-nav:hover .g-box,.vz-pf .p-nav:focus-visible .g-box{stroke:var(--vz-accent)}
.vz-pf .t-cap{font-size:12px;fill:var(--vz-tx2)}
.vz-pf .t-warn{font-size:12px;fill:var(--vz-warn);font-weight:500}
.vz-pf .gl-caution{fill:none;stroke:var(--vz-warn);stroke-width:1.5}
.vz-pf .gl-alarm{fill:var(--vz-alarm)}
`;

/* arrowhead pointing along (dx, dy) at (x, y), sized to the line width */
function head(x, y, dx, dy, w, cls) {
  const L = Math.max(7, w * 1.6), H = Math.max(4, w * 1.1);
  const n = Math.hypot(dx, dy) || 1, ux = dx / n, uy = dy / n;
  const bx = x - ux * L, by = y - uy * L;
  return `<path class="p-head ${cls}" d="M${x} ${y} L${bx - uy * H} ${by + ux * H} L${bx + uy * H} ${by - ux * H} Z"/>`;
}
/* A power path: a solid line (width = power) and, when animated, a thin
 * moving-gap overlay ON TOP of it, so the line itself never turns dashed
 * (dashed means stale in this vocabulary). */
function flowPath(d, q, w, anim) {
  const cls = flowCls(q);
  let p = `<path class="p-flow ${cls}" stroke-width="${w}" d="${d}"/>`;
  if (anim && cls === "") p += `<path class="p-pulse" stroke-width="${w}" d="${d}"/>`;
  return p;
}
function flowCls(q) {
  if (!q || q.v === null || q.verdict === "nodata") return "is-nodata";
  if (q.verdict === "stale") return "is-stale";
  if (Math.abs(q.v) < 0.5) return "is-zero";
  return "";
}
function tv(q, digits, t, opts = {}) {
  // SVG value text: class + content
  if (!q || q.v === null || q.verdict === "nodata") return { cls: "is-nodata", txt: t(opts.short ? "no data" : "no data") };
  const cls = stateClass(q.verdict);
  const age = q.verdict === "stale" && q.ageS !== null ? ` · ${fmtDur(q.ageS)}` : "";
  return { cls, txt: withUnit((opts.signed ? fmtSigned : fmt)(q.v, digits), opts.units ?? q.units) + age };
}
function vtext(x, y, q, digits, t, extra = {}) {
  const r = tv(q, digits, t, extra);
  return s("text", { x, y, class: `${extra.big ? "t-big" : "t-val"} ${r.cls}`, "text-anchor": extra.anchor || "start" }, esc(r.txt));
}
function panelIcon(x, y, w, h, dark) {
  const cols = 3, rows = 2;
  let g = `<rect class="p-panel" x="${x}" y="${y}" width="${w}" height="${h}" rx="1"/>`;
  for (let i = 1; i < cols; i++) g += `<line class="p-cell" x1="${x + (w * i) / cols}" y1="${y}" x2="${x + (w * i) / cols}" y2="${y + h}"/>`;
  for (let j = 1; j < rows; j++) g += `<line class="p-cell" x1="${x}" y1="${y + (h * j) / rows}" x2="${x + w}" y2="${y + (h * j) / rows}"/>`;
  return `<g class="${dark ? "is-dark" : ""}">${g}</g>`;
}

export function mount(el, opts = {}) {
  const t = opts.t || tDefault;
  const variant = opts.variant || "full";
  ensureStyle("c2o-viz-pf", CSS);
  const parts = mountFrame(el, { title: opts.title ?? "", t, cls: "vz-pf" });
  const tid = uid("pft"), did = uid("pfd");
  let last = null;

  function chips(m) {
    const o = m.orbit || {};
    const out = [];
    if (o.inEclipse === true) {
      out.push(`<span class="vz-chip is-ecl">${esc(t("Eclipse"))}${o.toExitS && o.toExitS.v !== null
        ? ` · ${esc(t("exit in {{d}}", { d: fmtDur(o.toExitS.v) }))}` : ""}</span>`);
    } else if (o.inEclipse === false) {
      out.push(`<span class="vz-chip">${esc(t("Sunlit"))}${o.toEntryS && o.toEntryS.v !== null
        ? ` · ${esc(t("eclipse in {{d}}", { d: fmtDur(o.toEntryS.v) }))}` : ""}</span>`);
    } else out.push(`<span class="vz-chip">${esc(t("Eclipse state: no data"))}</span>`);
    const st = m.shedStage;
    if (st && st.v !== null) {
      out.push(`<span class="vz-chip">${esc(t("Load shed"))} <b>L${Math.round(st.v)}</b></span>`);
    }
    out.push(`<span class="vz-chip">${esc(t("line width: 1 px = {{w}} W", { w: W_PER_PX }))}</span>`);
    return out.join("");
  }

  function summaryText(m) {
    const b = m.battery || {};
    const parts2 = [];
    parts2.push(t("Generation {{g}}, consumption {{c}}.", { g: tv(m.gen, 1, t).txt, c: tv(m.cons, 1, t).txt }));
    if (b.dir) parts2.push(t("Battery {{dir}} at {{w}}, state of charge {{soc}}.", {
      dir: t(b.dir === "charge" ? "charging" : b.dir === "discharge" ? "discharging" : "idle"),
      w: tv(b.w, 1, t, { units: "W" }).txt, soc: tv(b.soc, 1, t).txt }));
    const bal = m.balance || {};
    if (bal.netWh && bal.netWh.v !== null) parts2.push(t("Estimated net energy this orbit {{n}}.", { n: tv(bal.netWh, 0, t, { signed: true }).txt }));
    return parts2.join(" ");
  }

  function socGauge(x, y, h, w, m) {
    const b = m.battery || {}, soc = b.soc || {};
    const pct = soc.v === null || soc.v === undefined ? null : Math.max(0, Math.min(100, soc.v));
    const yOf = (p) => y + h - (h * p) / 100;
    const low = pct !== null && pct < b.socFloor ? "is-alarm" : pct !== null && pct < b.socMin ? "is-caution" : "";
    let g = `<g class="${low}">`;
    g += `<rect class="p-tank" x="${x}" y="${y}" width="${w}" height="${h}" rx="2"/>`;
    if (pct !== null) g += `<rect class="p-soc ${stateClass(soc.verdict)}" x="${x + 2}" y="${yOf(pct)}" width="${w - 4}" height="${Math.max(0, yOf(0) - yOf(pct) - 2)}"/>`;
    for (const p of [25, 50, 75]) g += `<line class="g-rule" x1="${x}" y1="${yOf(p)}" x2="${x + 5}" y2="${yOf(p)}"/>`;
    g += `<line class="g-lim-w" x1="${x - 5}" y1="${yOf(b.socMin)}" x2="${x + w + 5}" y2="${yOf(b.socMin)}"/>`;
    g += `<line class="g-lim-a" x1="${x - 5}" y1="${yOf(b.socFloor)}" x2="${x + w + 5}" y2="${yOf(b.socFloor)}"/>`;
    g += s("text", { x: x + w + 8, y: yOf(b.socMin) + 4, class: "t-lab" }, esc(t("min {{p}} %", { p: b.socMin })));
    g += s("text", { x: x + w + 8, y: yOf(b.socFloor) + 10, class: "t-lab" }, esc(t("floor {{p}} %", { p: b.socFloor })));
    const pr = (m.pred || {}).socAtExit;
    if (pr && pr.v !== null) {
      const pp = Math.max(0, Math.min(100, pr.v));
      const bad = pp < b.socMin ? "is-caution" : "";
      g += `<line class="p-pred ${bad}" x1="${x - 8}" y1="${yOf(pp)}" x2="${x + w + 4}" y2="${yOf(pp)}"/>`;
    }
    g += "</g>";
    return g;
  }

  function full(m) {
    const W = 900, H = 456;
    const anim = !!opts.animate && !reducedMotion();
    let g = "";
    const ecl = (m.orbit || {}).inEclipse === true;
    // ── sources ──
    const sy = [44, 104, 164, 224];
    const join = { x: 230, y: 154 };
    (m.sources || []).forEach((src, i) => {
      const y = sy[i];
      g += panelIcon(16, y - 16, 30, 32, ecl);
      g += s("text", { x: 56, y: y - 3, class: "t-cap" }, esc(t(src.label)));
      g += vtext(56, y + 15, src.w, 1, t);
      const w = lw(src.w.v);
      const ey = join.y - 12 + i * 8;
      g += flowPath(`M164 ${y} H184 C212 ${y} 204 ${ey} ${join.x} ${ey}`, src.w, w, anim);
    });
    if (ecl) g += s("text", { x: 16, y: 262, class: "t-lab" }, esc(t("arrays dark: eclipse")));
    // ── regulator ──
    g += `<rect class="g-box" x="230" y="108" width="134" height="92" rx="3"/>`;
    g += s("text", { x: 242, y: 130, class: "t-name" }, esc(t("Array regulator")));
    g += s("text", { x: 242, y: 148, class: "t-lab" }, esc(t("generation (MPPT)")));
    g += vtext(242, 176, m.gen, 1, t, { big: true });
    const gw = lw(m.gen && m.gen.v);
    g += flowPath(`M364 154 H${414}`, m.gen, gw, anim) + head(418, 154, 1, 0, gw, flowCls(m.gen, false));
    // ── bus ──
    g += `<rect class="p-bus" x="420" y="30" width="14" height="292" rx="2"/>`;
    g += s("text", { x: 427, y: 20, class: "t-name", "text-anchor": "middle" }, esc(t("Bus")));
    g += vtext(442, 46, m.busV, 2, t);
    // ── loads ──
    const groups = m.groups || [];
    const ly0 = 52, ldy = 52, bx = 520, bwid = 240;
    groups.forEach((grp, k) => {
      const y = ly0 + k * ldy;
      const w = lw(grp.w.v);
      g += flowPath(`M434 ${y} H${bx - 8}`, grp.w, w, anim) + head(bx - 4, y, 1, 0, w, flowCls(grp.w, false));
      const nav = opts.onNavigate && grp.subsystem ? ` class="p-nav" tabindex="0" role="link" data-page="${esc(grp.subsystem)}" aria-label="${esc(t(grp.label) + " " + tv(grp.w, 1, t).txt)}"` : "";
      g += `<g${nav}><rect class="g-box" x="${bx}" y="${y - 22}" width="${bwid}" height="44" rx="3"/>`;
      g += s("text", { x: bx + 12, y: y - 4, class: "t-cap" }, esc(t(grp.label)));
      g += vtext(bx + bwid - 10, y - 4, grp.w, 1, t, { anchor: "end" });
      // the lines of the group; switched-off lines in the disabled ink
      const names = grp.lines.map((l) => ({ txt: t(l.label) + (l.on === false ? " " + t("off") : ""), off: l.on === false }));
      const est = names.reduce((a2, n) => a2 + 8 + n.txt.length * 6.6, 0);
      let lx = bx + 12;
      if (est <= bwid - 20) {
        for (const n of names) {
          g += s("text", { x: lx, y: y + 14, class: n.off ? "p-off" : "t-lab" }, esc(n.txt));
          lx += 8 + n.txt.length * 6.6;
        }
      } else {
        const on = grp.lines.filter((l) => l.on !== false).map((l) => t(l.label));
        const off = grp.lines.length - on.length;
        g += s("text", { x: lx, y: y + 14, class: "t-lab" }, esc(on.join(", ")));
        if (off) g += s("text", { x: bx + bwid - 10, y: y + 14, class: "p-off", "text-anchor": "end" },
          esc(t("{{n}} off", { n: off })));
      }
      g += "</g>";
    });
    // total consumption as downlinked (the line sum above is computed)
    const ty = ly0 + groups.length * ldy - 14;
    g += s("text", { x: bx + 12, y: ty, class: "t-lab" }, esc(t("Total consumption (TM)")));
    g += vtext(bx + bwid - 10, ty, m.cons, 1, t, { anchor: "end" });
    // ── battery ──
    const b = m.battery || {};
    const bw = lw(b.w && b.w.v !== null ? Math.abs(b.w.v) : null);
    if (b.dir === "discharge") {
      g += flowPath("M427 362 V326", b.w, bw, anim) + head(427, 324, 0, -1, bw, flowCls(b.w, false));
    } else {
      g += flowPath("M427 322 V358", b.w, bw, anim) + head(427, 362, 0, 1, bw, flowCls(b.w, false));
    }
    const dirTxt = b.dir === "charge" ? t("charging") : b.dir === "discharge" ? t("discharging") : b.dir === "idle" ? t("idle") : "";
    g += vtext(442, 340, b.w, 1, t, { signed: true, units: "W" });
    if (dirTxt) g += s("text", { x: 442, y: 356, class: "t-lab" }, esc(dirTxt));
    g += `<rect class="g-box" x="364" y="366" width="170" height="70" rx="3"/>`;
    g += s("text", { x: 376, y: 386, class: "t-name" }, esc(t("Battery")));
    g += vtext(522, 386, b.temp, 1, t, { anchor: "end" });
    g += vtext(376, 406, b.v, 2, t);
    g += vtext(522, 406, b.i, 2, t, { signed: true, anchor: "end" });
    g += s("text", { x: 376, y: 426, class: "t-lab" }, esc(t("{{c}} Wh capacity", { c: fmt(b.capWh, 0) })));
    // ── SoC gauge ──
    g += s("text", { x: 766, y: 20, class: "t-name" }, esc(t("State of charge")));
    g += socGauge(778, 34, 230, 26, m);
    g += vtext(766, 290, b.soc, 1, t, { big: true });
    g += s("text", { x: 766, y: 308, class: "t-lab" }, esc(t("DoD {{d}}", { d: tv(b.dod, 1, t).txt })));
    const pr = (m.pred || {}).socAtExit;
    if (pr && pr.v !== null) {
      const bad = pr.v < b.socMin;
      g += `<line class="p-pred ${bad ? "is-caution" : ""}" x1="766" y1="326" x2="782" y2="326"/>`;
      g += s("text", { x: 788, y: 330, class: bad ? "t-warn" : "t-val" }, esc(tv(pr, 0, t).txt));
      g += s("text", { x: 766, y: 346, class: bad ? "t-warn" : "t-lab" }, esc(t("at eclipse exit")));
    }
    const tm = (m.pred || {}).timeToMinSocS;
    if (tm && tm.v !== null) g += s("text", { x: 766, y: 364, class: "t-lab" }, esc(t("min SoC in {{d}}", { d: fmtDur(tm.v) })));
    // ── orbit balance ──
    g += balanceBar(16, 368, 330, m, true);
    return { W, H, g };
  }

  function balanceBar(x, y, w, m, withTitle) {
    const bal = m.balance || {};
    const ein = bal.inWh && bal.inWh.v, eout = bal.outWh && bal.outWh.v;
    let g = "";
    if (withTitle) g += s("text", { x, y: y + 4, class: "t-name" }, esc(t("This orbit")));
    g += s("text", { x: x + (withTitle ? 78 : 0), y: y + 4, class: "t-lab" }, esc(t("ground estimate, in vs out")));
    const y0 = y + 16;
    if (ein === null || ein === undefined || eout === null || eout === undefined) {
      g += s("text", { x, y: y0 + 16, class: "t-val is-nodata" }, esc(t("not enough data for an orbit estimate")));
      return g;
    }
    const max = Math.max(ein, eout) * 1.1 || 1;
    const lab = 44, bw = w - lab - 70;
    const len = (e) => Math.max(1, (bw * e) / max);
    g += s("text", { x, y: y0 + 11, class: "t-lab" }, esc(t("In")));
    g += `<rect class="p-in" x="${x + lab}" y="${y0 + 1}" width="${len(ein)}" height="12" rx="1"/>`;
    g += vtext(x + lab + len(ein) + 6, y0 + 12, bal.inWh, 0, t);
    g += s("text", { x, y: y0 + 31, class: "t-lab" }, esc(t("Out")));
    g += `<rect class="p-out" x="${x + lab}" y="${y0 + 21}" width="${len(eout)}" height="12" rx="1"/>`;
    g += vtext(x + lab + len(eout) + 6, y0 + 32, bal.outWh, 0, t);
    const net = bal.netWh;
    const neg = net.v < 0;
    g += s("text", { x, y: y0 + 54, class: neg ? "t-warn" : "t-lab" },
      esc(neg ? t("Net {{n}}: the battery ends the orbit lower", { n: tv(net, 0, t, { signed: true }).txt })
        : t("Net {{n}}: the battery can recharge", { n: tv(net, 0, t, { signed: true }).txt })));
    return g;
  }

  function summary(m) {
    const W = 360, H = 330;
    const anim = !!opts.animate && !reducedMotion();
    let g = "";
    const ecl = (m.orbit || {}).inEclipse === true;
    // arrays -> bus -> loads
    g += panelIcon(8, 18, 28, 30, ecl);
    g += s("text", { x: 44, y: 30, class: "t-cap" }, esc(t("Arrays")));
    g += vtext(44, 48, m.gen, 1, t);
    const gw = lw(m.gen && m.gen.v);
    g += flowPath("M118 34 H176", m.gen, gw, anim) + head(180, 34, 1, 0, gw, flowCls(m.gen));
    g += `<rect class="p-bus" x="182" y="12" width="12" height="96" rx="2"/>`;
    g += s("text", { x: 174, y: 84, class: "t-lab", "text-anchor": "end" }, esc(t("Bus")));
    g += vtext(174, 102, m.busV, 1, t, { anchor: "end" });
    const cw = lw(m.cons && m.cons.v);
    g += flowPath("M194 34 H254", m.cons, cw, anim) + head(258, 34, 1, 0, cw, flowCls(m.cons));
    g += s("text", { x: 266, y: 30, class: "t-cap" }, esc(t("Loads")));
    g += vtext(266, 48, m.cons, 1, t);
    // battery off the bus
    const b = m.battery || {};
    const bw = lw(b.w && b.w.v !== null ? Math.abs(b.w.v) : null), bcls = flowCls(b.w);
    g += b.dir === "discharge"
      ? flowPath("M188 150 V116", b.w, bw, anim) + head(188, 112, 0, -1, bw, bcls)
      : flowPath("M188 110 V146", b.w, bw, anim) + head(188, 150, 0, 1, bw, bcls);
    g += s("text", { x: 204, y: 124, class: "t-cap" }, esc(t("Battery")));
    g += vtext(204, 142, b.w, 1, t, { signed: true, units: "W" });
    const dirTxt = b.dir === "charge" ? t("charging") : b.dir === "discharge" ? t("discharging") : b.dir === "idle" ? t("idle") : "";
    if (dirTxt) g += s("text", { x: 204, y: 158, class: "t-lab" }, esc(dirTxt));
    // state of charge, full width
    g += socBar(8, 178, 344, m);
    // orbit energy balance
    g += `<line class="g-rule" x1="8" y1="236" x2="352" y2="236"/>`;
    g += balanceBar(8, 250, 344, m, false);
    return { W, H, g };
  }

  function socBar(x, y, w, m) {
    const b = m.battery || {}, soc = b.soc || {};
    const pct = soc.v === null || soc.v === undefined ? null : Math.max(0, Math.min(100, soc.v));
    const xOf = (p) => x + (w * p) / 100;
    const low = pct !== null && pct < b.socFloor ? "is-alarm" : pct !== null && pct < b.socMin ? "is-caution" : "";
    let g = `<g class="${low}">`;
    g += s("text", { x, y: y + 6, class: "t-cap" }, esc(t("SoC")));
    g += vtext(x + w, y + 6, soc, 1, t, { anchor: "end" });
    g += `<rect class="p-tank" x="${x}" y="${y + 14}" width="${w}" height="14" rx="2"/>`;
    if (pct !== null) g += `<rect class="p-soc ${stateClass(soc.verdict)}" x="${x + 2}" y="${y + 16}" width="${Math.max(0, xOf(pct) - x - 2)}" height="10"/>`;
    g += `<line class="g-lim-w" x1="${xOf(b.socMin)}" y1="${y + 10}" x2="${xOf(b.socMin)}" y2="${y + 32}"/>`;
    g += `<line class="g-lim-a" x1="${xOf(b.socFloor)}" y1="${y + 10}" x2="${xOf(b.socFloor)}" y2="${y + 32}"/>`;
    const pr = (m.pred || {}).socAtExit;
    if (pr && pr.v !== null) {
      const pp = Math.max(0, Math.min(100, pr.v)), bad = pp < b.socMin;
      g += `<line class="p-pred ${bad ? "is-caution" : ""}" x1="${xOf(pp)}" y1="${y + 12}" x2="${xOf(pp)}" y2="${y + 30}"/>`;
      g += s("text", { x, y: y + 46, class: bad ? "t-warn" : "t-lab" }, esc(t("{{p}} at eclipse exit", { p: tv(pr, 0, t).txt })));
    }
    return g + "</g>";
  }

  function values(m) {
    const b = m.battery || {}, bal = m.balance || {}, pr = m.pred || {};
    const R = (label, q, d, o = {}) => [label, readout(q, d, t, o), q && q.src];
    const rows = [
      R(t("Bus voltage"), m.busV, 2), R(t("Generation"), m.gen, 1), R(t("Consumption"), m.cons, 1),
      R(t("Power margin"), m.margin, 1, { signed: true }),
      ...(m.sources || []).map((x) => R(t(x.label), x.w, 1)),
      ...(m.loads || []).map((l) => [t(l.label) + (l.on === false ? ` (${t("off")})` : ""), readout(l.w, 1, t), l.w.src]),
      R(t("Battery power (+ charging)"), b.w, 1, { signed: true }), R(t("Battery current"), b.i, 2, { signed: true }),
      R(t("Battery voltage"), b.v, 2), R(t("State of charge"), b.soc, 1), R(t("Depth of discharge"), b.dod, 1),
      [t("Battery capacity"), readout({ v: b.capWh, units: "Wh", verdict: "fresh" }, 0, t), b.capSrc],
      R(t("Energy in this orbit"), bal.inWh, 1), R(t("Energy out this orbit"), bal.outWh, 1),
      R(t("Net energy this orbit"), bal.netWh, 1, { signed: true }),
      R(t("SoC at next eclipse exit"), pr.socAtExit, 1), R(t("Time to minimum SoC"), pr.timeToMinSocS, 0),
    ];
    return valuesTable(rows, t, t("Power flow values. Sign: battery power is positive when charging."));
  }

  function update(m) {
    last = m;
    if (!m) return;
    const r = variant === "summary" ? summary(m) : full(m);
    const title = variant === "summary" ? t("Power flow summary") : t("Power flow");
    parts.chips.innerHTML = variant === "summary" ? "" : chips(m);
    parts.pic.innerHTML = `<div class="vz-stage" tabindex="0" role="group" aria-label="${esc(title)}">` +
      `<svg viewBox="0 0 ${r.W} ${r.H}" role="${variant === "summary" ? "img" : "group"}" aria-labelledby="${tid} ${did}" ` +
      `style="width:100%;min-width:${Math.round(r.W * 0.93)}px;max-width:${Math.round(r.W * 1.3)}px">` +
      `<title id="${tid}">${esc(title)}</title><desc id="${did}">${esc(summaryText(m))}</desc>${r.g}</svg></div>`;
    if (!parts.values.hidden) parts.values.innerHTML = values(m);
    else parts.values.dataset.dirty = "1";
  }
  const onToggle = () => { if (!parts.values.hidden && last) parts.values.innerHTML = values(last); };
  if (parts.btn) parts.btn.addEventListener("click", onToggle);
  const onClick = (e) => {
    const n = e.target.closest && e.target.closest("[data-page]");
    if (n && opts.onNavigate) opts.onNavigate(n.getAttribute("data-page"));
  };
  const onKey = (e) => { if (e.key === "Enter" || e.key === " ") { onClick(e); if (e.target.closest && e.target.closest("[data-page]")) e.preventDefault(); } };
  el.addEventListener("click", onClick);
  el.addEventListener("keydown", onKey);
  return {
    update,
    destroy() {
      el.removeEventListener("click", onClick);
      el.removeEventListener("keydown", onKey);
      el.innerHTML = "";
      el.classList.remove("c2o-viz", "vz-pf");
    },
  };
}
