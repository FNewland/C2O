/* ============================================================================
 * C2O pictorial displays — attitude2d.js  (source: shared/ui-viz/attitude2d.js)
 * ============================================================================
 * The 2D attitude instruments ("orient in 3D, operate in 2D"): every number
 * an operator must read sits in a fixed place, against its limits.
 *
 *   1. Pointing error dial, log scale 0.001°–100°, with the tolerance bands
 *      and the last minutes as a log-scale strip.
 *   2. Boresight view: the body-frame sky seen along the imager boresight
 *      (−Z), with the sun and nadir directions plotted, and the angles to
 *      the boresight, radiator, star tracker and wing normal written beside.
 *   3. Roll / pitch / yaw of the body relative to the COMMANDED attitude
 *      (z-y-x), and the body rates, as tapes against their limits. Near
 *      ±90° pitch the roll and yaw tapes say "near gimbal lock" instead.
 *   4. Reaction-wheel speeds against saturation and the zero-crossing band,
 *      and the momentum envelope with its time to saturation.
 *
 * The frame label and the quaternion convention are always visible.
 *
 *   mount(el, { t }) -> { update(attitudeModel), destroy() }
 *   attitudeModel = derive.js deriveAttitude(...) plus, optionally,
 *     errHistory: [{t, v}] (deg), aocsMode: "NOMINAL", limits: {hex: band}
 * ============================================================================ */
import { esc, fmt, fmtSigned, fmtDur, withUnit, stateClass, s, mountFrame, valuesTable,
  readout, tDefault, uid, ensureStyle, fin } from "./common.js";

const CSS = `
.vz-a2 .a2-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:0 var(--sp-5)}
.vz-a2 section{border-top:1px solid var(--vz-line);padding:var(--sp-2) 0 var(--sp-3);min-width:0}
.vz-a2 h3{font-size:var(--fs-label);font-weight:600;color:var(--vz-tx2);margin:0 0 var(--sp-2)}
.vz-a2 h3 span{font-weight:400;color:var(--vz-tx3)}
.vz-a2 .a2-row{display:grid;grid-template-columns:minmax(64px,auto) minmax(80px,1fr) minmax(92px,auto);align-items:center;
  gap:var(--sp-2);min-height:26px}
.vz-a2 .a2-row .k{font-size:var(--fs-label);color:var(--vz-tx2);white-space:nowrap}
.vz-a2 .a2-row .vz-v,.vz-a2 .a2-row .a2-note{text-align:right;justify-self:end}
.vz-a2 .a2-row svg{width:100%;height:16px}
.vz-a2 .a2-note{font-size:var(--fs-label);color:var(--vz-tx3)}
.vz-a2 .a2-dial{display:flex;gap:var(--sp-4);align-items:center;flex-wrap:wrap}
.vz-a2 .a2-dial svg{width:236px;height:auto;flex:0 0 auto}
.vz-a2 .a2-big{font-family:var(--vz-mono);font-variant-numeric:tabular-nums;font-size:var(--fs-title);font-weight:500;color:var(--vz-val)}
.vz-a2 .a2-big.is-stale{color:var(--vz-tx3);font-style:italic;font-weight:400}
.vz-a2 .a2-big.is-nodata{font-family:var(--vz-sans);font-size:var(--fs-body);color:var(--vz-tx2);font-weight:400}
.vz-a2 .a2-big.is-caution{color:var(--vz-warn)} .vz-a2 .a2-big.is-alarm{color:var(--vz-alarm)}
.vz-a2 .a2-kv{display:grid;grid-template-columns:auto auto;gap:2px var(--sp-3);font-size:var(--fs-label);color:var(--vz-tx2);align-items:baseline}
.vz-a2 .a2-kv .vz-v{text-align:right;font-size:var(--fs-body)}
.vz-a2 .a2-sky{display:flex;gap:var(--sp-4);align-items:flex-start;flex-wrap:wrap}
.vz-a2 .a2-sky svg{width:236px;height:auto;flex:0 0 auto}
.vz-a2 .a2-ptr{fill:var(--vz-val)} .vz-a2 .a2-ptr.is-stale{fill:var(--vz-stale)}
.vz-a2 .a2-ptr.is-caution{fill:var(--vz-warn)} .vz-a2 .a2-ptr.is-alarm{fill:var(--vz-alarm)}
.vz-a2 .a2-needle{stroke:var(--vz-val);stroke-width:2;stroke-linecap:round}
.vz-a2 .a2-needle.is-stale{stroke:var(--vz-stale);stroke-dasharray:3 2}
.vz-a2 .a2-needle.is-caution{stroke:var(--vz-warn)} .vz-a2 .a2-needle.is-alarm{stroke:var(--vz-alarm)}
.vz-a2 .a2-arc{fill:none;stroke:var(--vz-s3);stroke-width:10}
.vz-a2 .a2-arc-w{fill:none;stroke:var(--vz-warn);stroke-width:10;opacity:.45}
.vz-a2 .a2-arc-a{fill:none;stroke:var(--vz-alarm);stroke-width:10;opacity:.45}
.vz-a2 .a2-tick{stroke:var(--vz-tx3);stroke-width:1}
.vz-a2 .a2-ring{fill:none;stroke:var(--vz-line);stroke-width:1}
.vz-a2 .a2-ring.is-90{stroke:var(--vz-line2);stroke-dasharray:3 3}
.vz-a2 .a2-rim{fill:var(--vz-bg);stroke:var(--vz-tx3);stroke-width:1}
.vz-a2 .a2-sun{fill:var(--vz-val)} .vz-a2 .a2-sunray{stroke:var(--vz-val);stroke-width:1.25}
.vz-a2 .a2-nadir{fill:none;stroke:var(--vz-val);stroke-width:1.5}
.vz-a2 .is-stale .a2-sun,.vz-a2 .is-stale.a2-sun{fill:var(--vz-stale)}
.vz-a2 .a2-hist{stroke:var(--vz-tx2);stroke-width:1.25;fill:none}
.vz-a2 .a2-hist.is-stale{stroke:var(--vz-stale);stroke-dasharray:3 2}
.vz-a2 .a2-off{opacity:.45}
.vz-a2 .a2-warnline{stroke:var(--vz-warn);stroke-width:1;stroke-dasharray:2 2}
.vz-a2 .a2-alarmline{stroke:var(--vz-alarm);stroke-width:1;stroke-dasharray:2 2}
`;

// Labels and reasons that arrive from derive.js and are translated with t().
// i18n-keys
export const DYNAMIC_KEYS = [
  "Roll", "Pitch", "Yaw", "LVLH (nadir)", "inertial", "sun-pointing", "target track", "unknown",
  "no attitude solution", "not a unit quaternion", "sun sensors not valid (eclipse or off)", "sun not valid",
];

const LOG_MIN = -3, LOG_MAX = 2;            // 0.001° … 100°
const A0 = 210, A1 = -30;                    // dial sweep, math degrees: lower left, over the top, lower right

function polar(cx, cy, r, deg) {
  const a = (deg * Math.PI) / 180;
  return [cx + r * Math.cos(a), cy - r * Math.sin(a)];
}
function arc(cx, cy, r, d0, d1) {
  const [x0, y0] = polar(cx, cy, r, d0), [x1, y1] = polar(cx, cy, r, d1);
  const large = Math.abs(d1 - d0) > 180 ? 1 : 0;
  // angles decrease clockwise on screen: sweep-flag 1 when going d0 > d1
  return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${r} ${r} 0 ${large} ${d0 > d1 ? 1 : 0} ${x1.toFixed(2)} ${y1.toFixed(2)}`;
}
const dialAngle = (deg) => {
  const l = Math.log10(Math.max(10 ** LOG_MIN, Math.min(10 ** LOG_MAX, deg)));
  return A0 + ((A1 - A0) * (l - LOG_MIN)) / (LOG_MAX - LOG_MIN);
};

export function mount(el, opts = {}) {
  const t = opts.t || tDefault;
  ensureStyle("c2o-viz-a2", CSS);
  const parts = mountFrame(el, { title: opts.title ?? "", t, cls: "vz-a2" });
  let last = null;
  const ids = { dial: uid("a2d"), sky: uid("a2s") };

  const limState = (v, warn, alarm) => {
    if (!fin(v)) return "";
    const a = Math.abs(v);
    return fin(alarm) && a >= alarm ? "is-alarm" : fin(warn) && a >= warn ? "is-caution" : "";
  };
  const ptrCls = (q, warn, alarm) => (q.verdict === "stale" ? "is-stale" : limState(q.v, warn, alarm));

  /* symmetric tape −scale…+scale with warn/alarm bands */
  function tape(q, scale, warn, alarm, opt2 = {}) {
    const W = 200, H = 16, mid = W / 2;
    const X = (v) => mid + (Math.max(-scale, Math.min(scale, v)) / scale) * (W / 2 - 2);
    let g = `<rect class="g-track" x="0" y="5" width="${W}" height="6"/>`;
    if (fin(alarm) && alarm < scale) {
      g += `<rect class="g-band-a" x="0" y="5" width="${X(-alarm)}" height="6"/><rect class="g-band-a" x="${X(alarm)}" y="5" width="${W - X(alarm)}" height="6"/>`;
    }
    if (fin(warn) && warn < scale) {
      const hi = fin(alarm) ? Math.min(alarm, scale) : scale;
      g += `<rect class="g-band-w" x="${X(-hi)}" y="5" width="${X(-warn) - X(-hi)}" height="6"/><rect class="g-band-w" x="${X(warn)}" y="5" width="${X(hi) - X(warn)}" height="6"/>`;
    }
    if (opt2.zeroBand) g += `<rect class="g-hatch" x="${X(-opt2.zeroBand)}" y="3" width="${X(opt2.zeroBand) - X(-opt2.zeroBand)}" height="10"/>`;
    g += `<rect class="g-rule2" x="${mid - 0.5}" y="2" width="1" height="12"/>`;
    if (q && q.v !== null && q.verdict !== "nodata") {
      const off = Math.abs(q.v) > scale;
      const x = X(q.v);
      g += `<rect class="a2-ptr ${ptrCls(q, warn, alarm)}" x="${x - 2}" y="0" width="${off ? 3 : 4}" height="${H}"/>`;
    }
    return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">${g}</svg>`;
  }
  function row(label, svg, valHtml, cls = "") {
    return `<div class="a2-row ${cls}"><span class="k">${label}</span>${svg}${valHtml}</div>`;
  }

  /* 1 ── pointing error dial */
  function dial(a) {
    const cx = 118, cy = 104, r = 86;
    const warn = a.errLimits.warn, alarm = a.errLimits.alarm;
    let g = `<path class="a2-arc" d="${arc(cx, cy, r, A0, A1)}"/>`;
    if (fin(warn)) g += `<path class="a2-arc-w" d="${arc(cx, cy, r, dialAngle(warn), fin(alarm) ? dialAngle(alarm) : A1)}"/>`;
    if (fin(alarm)) g += `<path class="a2-arc-a" d="${arc(cx, cy, r, dialAngle(alarm), A1)}"/>`;
    for (let d = LOG_MIN; d <= LOG_MAX; d++) {
      const ang = dialAngle(10 ** d);
      const [x0, y0] = polar(cx, cy, r - 9, ang), [x1, y1] = polar(cx, cy, r + 7, ang);
      const [tx, ty] = polar(cx, cy, r + 18, ang);
      g += `<line class="a2-tick" x1="${x0}" y1="${y0}" x2="${x1}" y2="${y1}"/>`;
      g += s("text", { x: tx, y: ty + 4, class: "t-lab", "text-anchor": "middle" }, esc(d < 0 ? (10 ** d).toFixed(-d) : String(10 ** d)));
      for (const m of [2, 5]) {
        if (d === LOG_MAX) break;
        const am = dialAngle(m * 10 ** d);
        const [u0, v0] = polar(cx, cy, r - 5, am), [u1, v1] = polar(cx, cy, r + 3, am);
        g += `<line class="a2-tick" x1="${u0}" y1="${v0}" x2="${u1}" y2="${v1}"/>`;
      }
    }
    const e = a.errDeg;
    if (e && e.v !== null) {
      const cls = e.verdict === "stale" ? "is-stale" : limState(e.v, warn, alarm);
      const [nx, ny] = polar(cx, cy, r - 14, dialAngle(e.v));
      g += `<line class="a2-needle ${cls}" x1="${cx}" y1="${cy}" x2="${nx}" y2="${ny}"/>`;
    }
    g += `<circle class="g-ptr" cx="${cx}" cy="${cy}" r="3.5"/>`;
    g += s("text", { x: cx, y: cy + 34, class: "t-lab", "text-anchor": "middle" }, esc(t("degrees, log scale")));
    return `<svg viewBox="0 0 236 160" role="img" aria-labelledby="${ids.dial}"><title id="${ids.dial}">${esc(
      t("Pointing error dial: {{v}}", { v: e && e.v !== null ? withUnit(fmtErr(e.v), "°") : t("no data") }))}</title>${g}</svg>`;
  }
  const fmtErr = (v) => (Math.abs(v) >= 10 ? fmt(v, 1) : Math.abs(v) >= 1 ? fmt(v, 2) : Math.abs(v) >= 0.01 ? fmt(v, 3) : fmt(v, 4));

  function history(a) {
    const h = (a.errHistory || []).filter((p) => fin(p.v) && p.v > 0);
    if (h.length < 2) return `<p class="a2-note">${esc(t("Trend appears after a few samples."))}</p>`;
    const W = 236, H = 40, t0 = h[0].t, t1 = h[h.length - 1].t || t0 + 1;
    const X = (tt) => ((tt - t0) / Math.max(1, t1 - t0)) * (W - 2) + 1;
    const Y = (v) => H - 2 - ((Math.log10(Math.max(1e-3, Math.min(100, v))) - LOG_MIN) / (LOG_MAX - LOG_MIN)) * (H - 4);
    let g = `<rect class="g-track" x="0" y="0" width="${W}" height="${H}" opacity=".5"/>`;
    const warn = a.errLimits.warn, alarm = a.errLimits.alarm;
    if (fin(warn)) g += `<line class="a2-warnline" x1="0" x2="${W}" y1="${Y(warn)}" y2="${Y(warn)}"/>`;
    if (fin(alarm)) g += `<line class="a2-alarmline" x1="0" x2="${W}" y1="${Y(alarm)}" y2="${Y(alarm)}"/>`;
    g += `<path class="a2-hist ${a.errDeg.verdict === "stale" ? "is-stale" : ""}" d="${h.map((p, i) => `${i ? "L" : "M"}${X(p.t).toFixed(1)} ${Y(p.v).toFixed(1)}`).join(" ")}"/>`;
    return `<svg viewBox="0 0 ${W} ${H}" style="width:236px;height:40px" aria-hidden="true">${g}</svg>` +
      `<p class="a2-note">${esc(t("last {{d}}, log scale", { d: fmtDur(t1 - t0) }))}</p>`;
  }

  /* 2 ── boresight sky */
  function sky(a) {
    const R = 84, c = 100;
    const P = (bv) => [c + bv.x * R, c - bv.y * R];
    let g = `<circle class="a2-rim" cx="${c}" cy="${c}" r="${R}"/>`;
    for (const d of [30, 60, 90, 120, 150]) g += `<circle class="a2-ring ${d === 90 ? "is-90" : ""}" cx="${c}" cy="${c}" r="${(R * d) / 180}"/>`;
    g += `<line class="g-rule" x1="${c - R}" y1="${c}" x2="${c + R}" y2="${c}"/><line class="g-rule" x1="${c}" y1="${c - R}" x2="${c}" y2="${c + R}"/>`;
    g += s("text", { x: c + R + 4, y: c + 4, class: "t-lab" }, "+X");
    g += s("text", { x: c + 4, y: c - R - 4, class: "t-lab" }, "+Y");
    g += s("text", { x: c + 3, y: c - (R * 90) / 180 - 3, class: "t-lab" }, "90°");
    const bv = (v) => {
      if (!v) return null;
      const u = v.map((x) => x / (Math.hypot(...v) || 1));
      const off = (Math.acos(Math.max(-1, Math.min(1, -u[2]))) * 180) / Math.PI;
      const az = Math.atan2(u[1], u[0]);
      return { x: (off / 180) * Math.cos(az), y: (off / 180) * Math.sin(az) };
    };
    const nd = a.nadir && a.nadir.valid ? bv(a.nadir.v) : null;
    if (nd) {
      const [x, y] = P(nd);
      g += `<g class="${stateClass(a.nadir.verdict)}"><circle class="a2-nadir" cx="${x}" cy="${y}" r="7"/>` +
        `<line class="a2-sunray" x1="${x - 7}" y1="${y}" x2="${x + 7}" y2="${y}"/><line class="a2-sunray" x1="${x}" y1="${y - 7}" x2="${x}" y2="${y + 7}"/></g>`;
      g += s("text", { x: x + 10, y: y + 16, class: "t-lab" }, esc(t("nadir")));
    }
    const sn = a.sun && a.sun.valid ? bv(a.sun.v) : null;
    if (sn) {
      const [x, y] = P(sn);
      let rays = "";
      for (let k = 0; k < 8; k++) {
        const an = (k * Math.PI) / 4;
        rays += `<line class="a2-sunray" x1="${x + 7 * Math.cos(an)}" y1="${y + 7 * Math.sin(an)}" x2="${x + 10 * Math.cos(an)}" y2="${y + 10 * Math.sin(an)}"/>`;
      }
      g += `<g class="${stateClass(a.sun.verdict)}"><circle class="a2-sun" cx="${x}" cy="${y}" r="5"/>${rays}</g>`;
      g += s("text", { x: x + 12, y: y - 8, class: "t-lab" }, esc(t("sun")));
    }
    return `<svg viewBox="-6 -14 236 210" role="img" aria-labelledby="${ids.sky}"><title id="${ids.sky}">${esc(
      t("Sun and nadir directions seen along the imager boresight"))}</title>${g}</svg>`;
  }

  function sections(a) {
    const L = a.limits || {};
    const rateBand = L["0x0204"] || {};
    const wheelBand = L["0x0207"] || {};
    const envBand = L["0x02BA"] || {};
    const warn = a.errLimits.warn, alarm = a.errLimits.alarm;
    const e = a.errDeg;
    const bigCls = !e || e.v === null ? "is-nodata" : e.verdict === "stale" ? "is-stale" : limState(e.v, warn, alarm);
    const big = !e || e.v === null ? esc(t(e && e.reason ? e.reason : "no data"))
      : esc(withUnit(fmtErr(e.v), "°")) + (e.verdict === "stale" && fin(e.ageS) ? ` <span class="vz-age">· ${esc(fmtDur(e.ageS))}</span>` : "");
    // 1
    let h = `<section><h3>${esc(t("Pointing error"))} <span>${esc(t("total angle to the commanded attitude"))}</span></h3>
      <div class="a2-dial">${dial(a)}<div>
        <div class="a2-big ${bigCls}">${big}</div>
        <div class="a2-kv" style="margin-top:6px">
          <span>${esc(t("on board"))}</span>${readout(a.errTm, 3, t)}
          <span>${esc(t("caution / alarm"))}</span><span class="vz-v">${esc(fin(warn) ? withUnit(fmt(warn, 1), "°") : "–")} / ${esc(fin(alarm) ? withUnit(fmt(alarm, 1), "°") : "–")}</span>
        </div>
        <div style="margin-top:8px">${history(a)}</div>
      </div></div></section>`;
    // 2
    const ang = a.angles || {};
    const sunNote = a.sun && !a.sun.valid ? `<p class="a2-note" style="grid-column:1/-1">${esc(t(a.sun.reason || "no data"))}</p>` : "";
    h += `<section><h3>${esc(t("Sun and nadir"))} <span>${esc(t("seen along the imager boresight (−Z)"))}</span></h3>
      <div class="a2-sky">${sky(a)}
        <div class="a2-kv">
          <p class="a2-note" style="grid-column:1/-1;margin:0 0 4px">${esc(t("centre −Z (boresight), rim +Z (zenith)"))}</p>
          <span>${esc(t("off-nadir (boresight to nadir)"))}</span>${readout(ang.offNadir, 2, t)}
          <span>${esc(t("sun to boresight / radiator (−Z)"))}</span>${readout(ang.sunBoresight, 1, t, { reason: "sun not valid" })}
          <span>${esc(t("sun to star tracker (+Z)"))}</span>${readout(ang.sunStarTracker, 1, t, { reason: "sun not valid" })}
          <span>${esc(t("sun to wing normal"))}</span>${readout(ang.sunArray, 1, t, { reason: "sun not valid" })}
          <span>${esc(t("array drive angle"))}</span>${readout(a.driveDeg, 1, t)}
          ${sunNote}
        </div></div></section>`;
    // 3
    const sc = Math.max(4, (fin(alarm) ? alarm : 2) * 2);
    const sing = a.singular;
    const rpy = [["Roll", a.roll, "x"], ["Pitch", a.pitch, "y"], ["Yaw", a.yaw, "z"]].map(([k, q, ax]) => {
      if (sing && k !== "Pitch") return row(`${esc(t(k))} (${ax})`, tape(null, sc), `<span class="a2-note">${esc(t("near gimbal lock"))}</span>`);
      return row(`${esc(t(k))} (${ax})`, tape(q, sc, warn, alarm), readout(q, 3, t, { signed: true, reason: q && q.reason }));
    }).join("");
    const rw = fin(rateBand.yellow_high) ? rateBand.yellow_high : 0.5, ra = fin(rateBand.red_high) ? rateBand.red_high : 2;
    const rates = (a.rates || []).map((q, i) => row(`${esc(t("rate"))} ${"xyz"[i]}`, tape(q, ra * 1.25, rw, ra), readout(q, 3, t, { signed: true }))).join("");
    h += `<section><h3>${esc(t("Attitude relative to commanded"))} <span>${esc(t("z-y-x angles, scale ±{{s}}°", { s: sc }))}</span></h3>
      ${rpy}${rates}${sing ? `<p class="a2-note">${esc(t("Pitch within 5° of ±90°: roll and yaw are not separable here. Read the total pointing error."))}</p>` : ""}</section>`;
    // 4
    const ww = fin(wheelBand.yellow_high) ? wheelBand.yellow_high : 5000, wa = fin(wheelBand.red_high) ? wheelBand.red_high : 5500;
    const wheels = (a.wheels || []).map((w) => {
      const off = w.enabled === false;
      return row(esc(w.id), tape(off ? null : w.speed, w.maxRpm * 1.05, ww, wa, { zeroBand: w.zeroBandRpm }),
        off ? `<span class="a2-note">${esc(t("disabled"))}</span>` : readout(w.speed, 0, t, { signed: true }), off ? "a2-off" : "");
    }).join("");
    const env = (a.momentum || {}).envPct || {};
    const eta = (a.momentum || {}).etaS;
    const envSvg = (() => {
      const W = 200, X = (p) => (Math.max(0, Math.min(100, p)) / 100) * W;
      let g = `<rect class="g-track" x="0" y="5" width="${W}" height="6"/>`;
      const yw = fin(envBand.yellow_high) ? envBand.yellow_high : 70, ya = fin(envBand.red_high) ? envBand.red_high : 90;
      g += `<rect class="g-band-w" x="${X(yw)}" y="5" width="${X(ya) - X(yw)}" height="6"/><rect class="g-band-a" x="${X(ya)}" y="5" width="${W - X(ya)}" height="6"/>`;
      if (env.v !== null && env.v !== undefined) g += `<rect class="a2-ptr ${env.verdict === "stale" ? "is-stale" : env.v >= ya ? "is-alarm" : env.v >= yw ? "is-caution" : ""}" x="${X(env.v) - 2}" y="0" width="4" height="16"/>`;
      return `<svg viewBox="0 0 ${W} 16" preserveAspectRatio="none" aria-hidden="true">${g}</svg>`;
    })();
    const etaTxt = eta && eta.v !== null ? t("saturation in {{d}}", { d: fmtDur(eta.v) }) : t("not rising");
    h += `<section><h3>${esc(t("Reaction wheels"))} <span>${esc(t("speed vs saturation; hatched: zero-crossing band"))}</span></h3>
      ${wheels}${row(esc(t("momentum")), envSvg, readout(env, 1, t))}
      <p class="a2-note">${esc(t("Momentum envelope (most-loaded wheel): {{eta}}", { eta: etaTxt }))}</p></section>`;
    return `<div class="a2-grid">${h}</div>`;
  }

  function chips(a) {
    const out = [`<span class="vz-chip">${esc(t("Frame"))} <b>${esc(t(a.frameLabel || "unknown"))}</b></span>`];
    if (a.aocsMode) out.push(`<span class="vz-chip">${esc(t("AOCS"))} <b>${esc(a.aocsMode)}</b></span>`);
    out.push(`<span class="vz-chip">q <b>[x y z w]</b> ${esc(t("scalar last, ECI to body"))}</span>`);
    return out.join("");
  }

  function values(a) {
    const qtxt = (q) => (q && q.raw && q.raw.every((x) => x !== null) ? `<span class="vz-v">[${q.raw.map((x) => fmt(x, 5)).join(", ")}]</span>`
      : `<span class="vz-v is-nodata">${esc(t("no data"))}</span>`);
    const ang = a.angles || {};
    const rows = [
      [t("Estimated quaternion"), qtxt(a.est) + (a.est && !a.est.valid && a.est.reason !== "no data" ? ` <span class="vz-note">${esc(t(a.est.reason))}</span>` : ""), a.est && a.est.src],
      [t("Commanded quaternion"), qtxt(a.ref), a.ref && a.ref.src],
      [t("Published attitude quaternion"), qtxt(a.att), a.att && a.att.src],
      [t("Pointing error (computed)"), readout(a.errDeg, 4, t), a.errDeg && a.errDeg.src],
      [t("Pointing error (on board)"), readout(a.errTm, 4, t), a.errTm && a.errTm.src],
      [t("Roll"), readout(a.roll, 4, t, { signed: true }), ""], [t("Pitch"), readout(a.pitch, 4, t, { signed: true }), ""],
      [t("Yaw"), readout(a.yaw, 4, t, { signed: true }), ""],
      ...(a.rates || []).map((q, i) => [`${t("Body rate")} ${"xyz"[i]}`, readout(q, 4, t, { signed: true }), q.src]),
      [t("Sun vector (body)"), a.sun && a.sun.v ? `<span class="vz-v">[${a.sun.v.map((x) => fmt(x, 3)).join(", ")}]</span>` : `<span class="vz-v is-nodata">${esc(t(a.sun && a.sun.reason || "no data"))}</span>`, a.sun && a.sun.src],
      [t("Nadir vector (body)"), a.nadir && a.nadir.v ? `<span class="vz-v">[${a.nadir.v.map((x) => fmt(x, 3)).join(", ")}]</span>` : `<span class="vz-v is-nodata">${esc(t("no data"))}</span>`, a.nadir && a.nadir.src],
      [t("Off-nadir angle"), readout(ang.offNadir, 2, t), ang.offNadir && ang.offNadir.src],
      ...(a.wheels || []).map((w) => [`${w.id} ${t("speed")}`, readout(w.speed, 0, t, { signed: true }), w.speed.src]),
      [t("Momentum envelope"), readout((a.momentum || {}).envPct, 1, t), ((a.momentum || {}).envPct || {}).src],
      [t("Total momentum"), readout((a.momentum || {}).h, 4, t), ((a.momentum || {}).h || {}).src],
    ];
    return valuesTable(rows, t, t("Quaternions are [x y z w], scalar last, ECI to body: v_body = C(q) · v_ECI."));
  }

  function update(a) {
    last = a;
    if (!a) return;
    parts.chips.innerHTML = chips(a);
    parts.pic.innerHTML = sections(a);
    if (!parts.values.hidden) parts.values.innerHTML = values(a);
  }
  if (parts.btn) parts.btn.addEventListener("click", () => { if (!parts.values.hidden && last) parts.values.innerHTML = values(last); });
  return { update, destroy() { el.innerHTML = ""; } };
}
