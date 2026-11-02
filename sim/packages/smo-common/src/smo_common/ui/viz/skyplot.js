/* ============================================================================
 * C2O pictorial displays — skyplot.js  (source: shared/ui-viz/skyplot.js)
 * ============================================================================
 * The polar az/el sky plot of one pass as the ground station's antenna
 * sees it, in Gpredict's familiar layout: zenith at the centre, horizon at
 * the rim, north up, azimuth clockwise (east to the right, as on the
 * antenna's az/el map, not the mirror image of looking up). The elevation
 * mask is shaded, the AOS->LOS track is drawn (past part faint), the "now"
 * marker sits on it, and the fixed strip gives the max elevation WITH its
 * time, the pass duration and the time to AOS / LOS.
 *
 *   mount(el, { t, size }) -> { update(model), destroy() }
 *
 * MODEL:
 *   nowMs
 *   station  {name, lat_deg|lat, lon_deg|lon, alt_km|altKm, min_elevation_deg|maskDeg}
 *   pass     {aos, los, samples:[{t, az, el}]}   — or, instead of samples:
 *   track    served ground-track rows [{utc|t, lat, lon, alt_km}] from which
 *            the look angles are computed here (lookAngles, WGS-84; the
 *            served positions, not an independent propagation)
 *   current  {az, el, verdict?, ageS?}  measured/served present look angle
 *
 * Exported pure helpers: lookAngles(station, points), passesFromTrack(...).
 * ============================================================================ */

import {
  injectBase, injectCss, translator, fmt, fin, esc, valueHtml, tableHtml, svgEl, clear,
  valuesToggle, fmtClock, fmtUtc,
} from "./vizkit.js";

/* ── pure geometry (exported for tests) ───────────────────────────────── */

const A = 6378.137, F = 1 / 298.257223563, E2 = F * (2 - F);
const D2R = Math.PI / 180, R2D = 180 / Math.PI;
const toMs = (x) => (x instanceof Date ? x.getTime() : typeof x === "number" ? x : Date.parse(x));

/** WGS-84 geodetic (deg, deg, km) -> ECEF km. */
export function geodeticToEcef(latDeg, lonDeg, hKm) {
  const la = latDeg * D2R, lo = lonDeg * D2R;
  const N = A / Math.sqrt(1 - E2 * Math.sin(la) ** 2);
  return [(N + hKm) * Math.cos(la) * Math.cos(lo), (N + hKm) * Math.cos(la) * Math.sin(lo),
    (N * (1 - E2) + hKm) * Math.sin(la)];
}
/** Azimuth (deg, clockwise from north), elevation (deg), range (km) of a
 *  target ECEF position from a station (geodetic). */
export function azEl(st, tgt) {
  const la = st.lat * D2R, lo = st.lon * D2R;
  const o = geodeticToEcef(st.lat, st.lon, st.alt || 0);
  const d = [tgt[0] - o[0], tgt[1] - o[1], tgt[2] - o[2]];
  const e = -Math.sin(lo) * d[0] + Math.cos(lo) * d[1];
  const n = -Math.sin(la) * Math.cos(lo) * d[0] - Math.sin(la) * Math.sin(lo) * d[1] + Math.cos(la) * d[2];
  const u = Math.cos(la) * Math.cos(lo) * d[0] + Math.cos(la) * Math.sin(lo) * d[1] + Math.sin(la) * d[2];
  const rng = Math.hypot(e, n, u);
  return { az: ((Math.atan2(e, n) * R2D) + 360) % 360, el: Math.asin(u / rng) * R2D, range: rng };
}
export function normStation(s) {
  return { name: s.name, lat: Number(s.lat_deg ?? s.lat), lon: Number(s.lon_deg ?? s.lon),
    alt: Number(s.alt_km ?? s.altKm ?? 0) || 0, mask: Number(s.min_elevation_deg ?? s.maskDeg ?? 5) };
}
/** Look angles of served track rows {t|utc, lat, lon, alt_km} from a station. */
export function lookAngles(station, points) {
  const st = normStation(station);
  return (points || []).map((p) => {
    const alt = Number(p.alt_km ?? p.alt ?? 513);
    const r = azEl(st, geodeticToEcef(Number(p.lat), Number(p.lon), alt));
    return { t: toMs(p.t ?? p.utc), az: r.az, el: r.el, range: r.range };
  }).filter((s) => Number.isFinite(s.t)).sort((a, b) => a.t - b.t);
}
/** Passes above the mask in a look-angle series: AOS/LOS interpolated to the
 *  mask crossing, max elevation and its time, samples (incl. the crossings). */
export function passesFromSamples(samples, mask) {
  const out = [];
  let cur = null;
  const cross = (a, b) => {
    const f = (mask - a.el) / (b.el - a.el);
    let daz = b.az - a.az;
    if (daz > 180) daz -= 360;
    if (daz < -180) daz += 360;
    return { t: a.t + f * (b.t - a.t), az: (a.az + f * daz + 360) % 360, el: mask };
  };
  for (let i = 0; i < samples.length; i++) {
    const s = samples[i], p = samples[i - 1];
    const up = s.el >= mask;
    if (up && !cur) {
      cur = { samples: [], maxEl: -90, tMax: null, aosPartial: !p };
      if (p) cur.samples.push(cross(p, s));
    }
    if (cur && up) {
      cur.samples.push(s);
      if (s.el > cur.maxEl) { cur.maxEl = s.el; cur.tMax = s.t; }
    }
    if (cur && !up) {
      cur.samples.push(cross(p, s));
      cur.aos = cur.samples[0].t; cur.los = cur.samples[cur.samples.length - 1].t;
      out.push(cur);
      cur = null;
    }
  }
  if (cur) {
    cur.aos = cur.samples[0].t; cur.los = cur.samples[cur.samples.length - 1].t; cur.losPartial = true;
    out.push(cur);
  }
  return out;
}
export function passesFromTrack(station, track) {
  return passesFromSamples(lookAngles(station, track), normStation(station).mask);
}

/* Reasons and labels passed to t() as variables.
// i18n-keys (English text is the i18n key)
 */
export const I18N_KEYS = ["none in the served track", "no station", "not in pass", "ended", "no data",
  "N", "E", "S", "W"];

/* ── view ──────────────────────────────────────────────────────────────── */

/** Polar projection into a plot of side `S` (rim radius R = 0.427 S):
 *  el 90 -> centre, el 0 -> rim; az clockwise from north (up). */
export function polar(az, el, S = 300) {
  const C0 = S / 2, R = S * 0.427;
  const r = (R * (90 - Math.max(-5, el))) / 90;
  return [C0 + r * Math.sin(az * D2R), C0 - r * Math.cos(az * D2R)];
}

const CSS = `
.vz-sky{ display:grid; grid-template-columns:minmax(200px,320px) minmax(180px,1fr); gap:0 var(--sp-4,16px); align-items:start; }
.vz-sky > .vz-bar,.vz-sky > .vz-tabhost{ grid-column:1 / -1; }
.vz-sky .vz-plot{ border:1px solid var(--vz-line); border-radius:var(--radius,3px); background:var(--vz-s1); position:relative; }
.vz-sky .vz-plot.is-stale{ border-style:dashed; border-color:var(--vz-stale); }
.vz-sky svg{ display:block; width:100%; height:auto; }
.vz-sky .ring{ fill:none; stroke:var(--vz-line); stroke-width:.75; }
.vz-sky .rim{ fill:none; stroke:var(--vz-line2); stroke-width:1; }
.vz-sky .spoke{ stroke:var(--vz-line); stroke-width:.75; }
.vz-sky .mask{ fill:var(--vz-s3); fill-opacity:.8; }
.vz-sky .mask-l{ fill:none; stroke:var(--vz-tx3); stroke-width:.8; stroke-dasharray:3 3; }
.vz-sky .lab{ font-size:12px; fill:var(--vz-tx3); }
.vz-sky .card{ font-size:12px; font-weight:600; fill:var(--vz-tx2); }
.vz-sky .trk{ fill:none; stroke:var(--vz-val); stroke-width:1.8; stroke-linejoin:round; stroke-linecap:round; }
.vz-sky .trk.past{ stroke:var(--vz-tx3); stroke-width:1.2; stroke-dasharray:1 3; }
.vz-sky .ev{ fill:var(--vz-s1); stroke:var(--vz-val); stroke-width:1.4; }
.vz-sky .ev.los{ fill:var(--vz-val); }
.vz-sky .ev-l{ font-size:12px; fill:var(--vz-tx2); paint-order:stroke; stroke:var(--vz-s1); stroke-width:3px; }
.vz-sky .mx{ fill:none; stroke:var(--vz-tx2); stroke-width:1.2; }
.vz-sky .now{ fill:var(--vz-accent); stroke:var(--vz-s1); stroke-width:1.5; }
.vz-sky .vz-plot.is-stale .now{ fill:var(--vz-tx3); }
.vz-sky .vz-empty{ position:absolute; inset:auto 0 46% 0; text-align:center; color:var(--vz-tx2); padding:0 24px; }
.vz-sky .vz-strip{ display:flex; flex-direction:column; border-top:1px solid var(--vz-line); }
.vz-sky .vz-row{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:2px 8px; align-items:baseline;
  padding:6px 0; border-bottom:1px solid var(--vz-line); }
.vz-sky .vz-row > .k{ font-size:var(--fs-label,12px); color:var(--vz-tx3); }
.vz-sky .vz-row > .v{ text-align:right; }
.vz-sky .vz-row > .d{ grid-column:1 / -1; font-size:var(--fs-label,12px); color:var(--vz-tx3); }
@media (max-width: 560px){
  .vz-sky{ grid-template-columns:minmax(0,1fr); }
  .vz-sky .vz-strip{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:16px; margin-top:8px; }
}
`;

export function mount(el, opts = {}) {
  injectBase();
  injectCss("vz-sp-css", CSS);
  const t = translator(opts);
  const d = globalThis.document;
  const uid = Math.random().toString(36).slice(2, 8);
  let model = null;
  /* drawn at its rendered pixel size (redrawn on resize): 12 px text floor */
  let S = 300, C0 = 150, R = 128;
  const polarS = (az, el) => polar(az, el, S);

  const root = d.createElement("div");
  root.className = "vz vz-sky";
  el.appendChild(root);
  const bar = d.createElement("div");
  bar.className = "vz-bar";
  const cap = d.createElement("span");
  cap.className = "vz-cap";
  const sp = d.createElement("span");
  sp.className = "vz-sp";
  const tabHost = d.createElement("div");
  tabHost.className = "vz-tabhost";
  const vt = valuesToggle(t, tabHost, `vz-sp-tab-${uid}`);
  vt.btn.addEventListener("click", () => draw());
  bar.append(cap, sp, vt.btn);
  if (opts.showBar !== false) root.appendChild(bar);

  const plot = d.createElement("div");
  plot.className = "vz-plot";
  const svg = svgEl("svg", { viewBox: `0 0 ${S} ${S}`, role: "img", "aria-labelledby": `vz-sp-ti-${uid} vz-sp-de-${uid}` });
  const title = svgEl("title", { id: `vz-sp-ti-${uid}` });
  const desc = svgEl("desc", { id: `vz-sp-de-${uid}` });
  const gBase = svgEl("g"), gMask = svgEl("g"), gTrk = svgEl("g");
  svg.append(title, desc, gMask, gBase, gTrk);
  plot.appendChild(svg);
  const empty = d.createElement("div");
  empty.className = "vz-empty";
  plot.appendChild(empty);
  const strip = d.createElement("div");
  strip.className = "vz-strip";
  root.append(plot, strip, tabHost);

  /* grid: elevation rings 0/30/60, spokes every 30 deg (rebuilt on resize) */
  function drawBase() {
  clear(gBase);
  svg.setAttribute("viewBox", `0 0 ${S} ${S}`);
  for (const el2 of [30, 60]) {
    gBase.appendChild(svgEl("circle", { class: "ring", cx: C0, cy: C0, r: (R * (90 - el2)) / 90 }));
    gBase.appendChild(svgEl("text", { class: "lab", x: C0 + 3, y: C0 - (R * (90 - el2)) / 90 - 3 }, `${el2}°`));
  }
  gBase.appendChild(svgEl("circle", { class: "rim", cx: C0, cy: C0, r: R }));
  for (let az = 0; az < 360; az += 30) {
    const [x, y] = polarS(az, 0);
    gBase.appendChild(svgEl("line", { class: "spoke", x1: C0, y1: C0, x2: x.toFixed(1), y2: y.toFixed(1) }));
  }
  }
  const cards = [["N", 0], ["E", 90], ["S", 180], ["W", 270]];

  function draw() {
    const m = model || {};
    const now = fin(m.nowMs) ? Number(m.nowMs) : null;
    const st = m.station ? normStation(m.station) : null;
    clear(gMask); clear(gTrk);
    for (const n of [...gBase.querySelectorAll(".card")]) n.remove();
    for (const [l, az] of cards) {
      const [x, y] = polarS(az, -9);
      gBase.appendChild(svgEl("text", { class: "card", x: x.toFixed(1), y: (y + 4).toFixed(1), "text-anchor": "middle" }, t(l)));
    }
    // elevation mask: annulus between the horizon and the mask
    if (st) {
      const rm = (R * (90 - st.mask)) / 90;
      gMask.appendChild(svgEl("path", { class: "mask", "fill-rule": "evenodd",
        d: `M${C0 - R} ${C0}a${R} ${R} 0 1 0 ${2 * R} 0a${R} ${R} 0 1 0 ${-2 * R} 0Z` +
          `M${C0 - rm} ${C0}a${rm} ${rm} 0 1 0 ${2 * rm} 0a${rm} ${rm} 0 1 0 ${-2 * rm} 0Z` }));
      gMask.appendChild(svgEl("circle", { class: "mask-l", cx: C0, cy: C0, r: rm }));
    }
    // the pass: samples given, or computed from served track rows
    let pass = null;
    if (m.pass && Array.isArray(m.pass.samples) && m.pass.samples.length) {
      const sm = m.pass.samples.map((s) => ({ t: toMs(s.t), az: Number(s.az), el: Number(s.el) }));
      let mx = sm[0];
      for (const s of sm) if (s.el > mx.el) mx = s;
      pass = { samples: sm, aos: toMs(m.pass.aos ?? sm[0].t), los: toMs(m.pass.los ?? sm[sm.length - 1].t),
        maxEl: mx.el, tMax: mx.t };
    } else if (st && m.track) {
      const ps = passesFromTrack(m.station, m.track);
      pass = (now !== null ? ps.find((p) => p.los >= now) : ps[0]) || null;
    }
    empty.textContent = !st ? t("No station selected") : pass ? "" : t("No pass above the mask in the served track");
    empty.hidden = !!(st && pass);
    const cur = m.current && fin(m.current.az) && fin(m.current.el) ? m.current : (pass && now !== null ? interp(pass, now) : null);
    plot.classList.toggle("is-stale", !!(m.current && m.current.verdict === "stale"));
    if (pass) {
      const pastPts = [], futPts = [];
      for (const s of pass.samples) {
        const isPast = now !== null && s.t < now;
        (isPast ? pastPts : futPts).push(s);
      }
      if (cur && pastPts.length) { pastPts.push(cur); futPts.unshift(cur); }
      const path = (pts) => pts.map((s, i) => { const [x, y] = polarS(s.az, s.el); return (i ? "L" : "M") + x.toFixed(1) + " " + y.toFixed(1); }).join("");
      if (pastPts.length > 1) gTrk.appendChild(svgEl("path", { class: "trk past", d: path(pastPts) }));
      if (futPts.length > 1) gTrk.appendChild(svgEl("path", { class: "trk", d: path(futPts) }));
      const s0 = pass.samples[0], s1 = pass.samples[pass.samples.length - 1];
      const mark = (s, cls, txt, title2) => {
        const [x, y] = polarS(s.az, s.el);
        const g = svgEl("g", { transform: `translate(${x.toFixed(1)} ${y.toFixed(1)})` });
        g.appendChild(svgEl("circle", { class: "ev " + cls, r: 3.5 }));
        const outx = x < C0 ? -7 : 7;
        g.appendChild(svgEl("text", { class: "ev-l", x: outx, y: 4, "text-anchor": outx < 0 ? "end" : "start" }, txt));
        g.appendChild(svgEl("title", {}, title2));
        gTrk.appendChild(g);
      };
      mark(s0, "aos", t("AOS"), t("AOS {{utc}} UTC", { utc: fmtUtc(pass.aos, true) }));
      mark(s1, "los", t("LOS"), t("LOS {{utc}} UTC", { utc: fmtUtc(pass.los, true) }));
      const mxS = pass.samples.reduce((a, b) => (b.el > a.el ? b : a));
      const [mx, my] = polarS(mxS.az, mxS.el);
      const mg = svgEl("path", { class: "mx", d: `M${mx - 4} ${my - 4}L${mx + 4} ${my + 4}M${mx - 4} ${my + 4}L${mx + 4} ${my - 4}` });
      mg.appendChild(svgEl("title", {}, t("Maximum elevation {{el}}°", { el: fmt(mxS.el, 1) })));
      gTrk.appendChild(mg);
    }
    if (cur) {
      const [x, y] = polarS(cur.az, cur.el);
      const c = svgEl("circle", { class: "now", cx: x.toFixed(1), cy: y.toFixed(1), r: 5 });
      c.appendChild(svgEl("title", {}, t("Now")));
      gTrk.appendChild(c);
    }
    renderStrip(m, st, pass, cur, now);
    title.textContent = st ? t("Sky plot, {{station}}", { station: st.name }) : t("Sky plot");
    desc.textContent = summary(st, pass, cur, now);
    cap.textContent = st ? t("{{station}} · mask {{mask}}° · north up, east right", { station: st.name, mask: fmt(st.mask, 0) }) : "";
  }

  function interp(pass, now) {
    const s = pass.samples;
    if (now < s[0].t || now > s[s.length - 1].t) return null;
    for (let i = 1; i < s.length; i++) {
      if (now <= s[i].t) {
        const f = (now - s[i - 1].t) / ((s[i].t - s[i - 1].t) || 1);
        let daz = s[i].az - s[i - 1].az;
        if (daz > 180) daz -= 360;
        if (daz < -180) daz += 360;
        return { az: (s[i - 1].az + f * daz + 360) % 360, el: s[i - 1].el + f * (s[i].el - s[i - 1].el) };
      }
    }
    return null;
  }
  function renderStrip(m, st, pass, cur, now) {
    const row = (k, html, dsc) => `<div class="vz-row"><span class="k">${esc(k)}</span><span class="v">${html}</span>` +
      (dsc ? `<span class="d">${esc(dsc)}</span>` : "") + `</div>`;
    const nd = (why) => valueHtml(null, { t, reason: why });
    const clockV = (s) => valueHtml(null, { t, text: fmtClock(s), verdict: "fresh" });
    if (!pass) {
      strip.innerHTML = row(t("Next pass"), nd(st ? "none in the served track" : "no station"));
      tabHost.innerHTML = "";
      return;
    }
    const inPass = now !== null && now >= pass.aos && now <= pass.los;
    const rows = [];
    if (inPass) rows.push(row(t("Time to LOS"), clockV((pass.los - now) / 1000), t("LOS {{utc}} UTC", { utc: fmtUtc(pass.los) })));
    else if (now !== null && now < pass.aos) rows.push(row(t("Time to AOS"), clockV((pass.aos - now) / 1000), t("AOS {{utc}} UTC", { utc: fmtUtc(pass.aos) })));
    else rows.push(row(t("Pass"), nd("ended")));
    rows.push(row(t("Max elevation"), valueHtml(pass.maxEl, { digits: 1, units: "°", t, verdict: "fresh" }),
      t("at {{utc}} UTC", { utc: fmtUtc(pass.tMax) })));
    rows.push(row(t("Duration"), valueHtml(null, { t, text: fmtClock((pass.los - pass.aos) / 1000), verdict: "fresh" }),
      `${fmtUtc(pass.aos)}–${fmtUtc(pass.los)} UTC`));
    rows.push(row(t("Azimuth"), cur ? valueHtml(cur.az, { digits: 1, units: "°", t, verdict: m.current && m.current.verdict, ageS: m.current && m.current.ageS })
      : nd(inPass ? "no data" : "not in pass")));
    rows.push(row(t("Elevation"), cur ? valueHtml(cur.el, { digits: 1, units: "°", t, verdict: m.current && m.current.verdict, ageS: m.current && m.current.ageS })
      : nd(inPass ? "no data" : "not in pass")));
    strip.innerHTML = rows.join("");
    if (vt.isOpen()) {
      tabHost.innerHTML = tableHtml(t("Pass samples"), pass.samples.filter((_, i) => i % 2 === 0 || i === pass.samples.length - 1)
        .map((s) => ({ label: `${fmtUtc(s.t, true)} UTC`, html: `${esc(fmt(s.az, 1))}° / ${esc(fmt(s.el, 1))}°`, src: t("azimuth / elevation") })), t);
    }
  }
  function summary(st, pass, cur, now) {
    if (!st) return t("Sky plot. No station selected.");
    if (!pass) return t("Sky plot for {{s}}. No pass above the mask in the served track.", { s: st.name });
    const parts = [t("Pass over {{s}}: AOS {{aos}}, LOS {{los}} UTC, maximum elevation {{el}} degrees.", {
      s: st.name, aos: fmtUtc(pass.aos), los: fmtUtc(pass.los), el: fmt(pass.maxEl, 0) })];
    if (now !== null && now < pass.aos) parts.push(t("AOS in {{min}} min.", { min: fmt((pass.aos - now) / 60000, 0) }));
    if (cur) parts.push(t("Now at azimuth {{az}}, elevation {{el}} degrees.", { az: fmt(cur.az, 0), el: fmt(cur.el, 0) }));
    return parts.join(" ");
  }

  function size() {
    const w = Math.round(Math.min(plot.clientWidth || 300, 420));
    if (w < 40 || w === S) return false;
    S = w; C0 = w / 2; R = w * 0.427;
    drawBase();
    return true;
  }
  let ro = null;
  try { ro = new ResizeObserver(() => { if (size()) draw(); }); ro.observe(plot); } catch (e) { /* fixed size */ }
  size();
  drawBase();
  draw();
  return {
    update(m) { model = m || null; draw(); },
    destroy() { if (ro) ro.disconnect(); root.remove(); },
  };
}
