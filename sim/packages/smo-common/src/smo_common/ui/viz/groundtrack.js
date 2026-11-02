/* ============================================================================
 * C2O pictorial displays — groundtrack.js  (source: shared/ui-viz/groundtrack.js)
 * ============================================================================
 * The 2D world map every console needs beside the 3D view (BEV's users still
 * needed one): equirectangular SVG over the offline Natural Earth 110 m
 * basemap, with
 *   - the ground track: past (faint dotted) and future (ink), the future
 *     split into sunlit (solid) and SPACECRAFT eclipse (dashed) from the
 *     served track's own eclipse flags, with ticks at entry and exit;
 *   - the day/night terminator ON THE GROUND (labelled as such: the ground
 *     terminator is not the spacecraft's eclipse);
 *   - station visibility circles at each station's elevation mask for the
 *     spacecraft's altitude, the station in contact drawn as active;
 *   - the current sub-satellite point and the imager's footprint;
 *   - a fixed readout strip (position, illumination and the next eclipse
 *     transition, next AOS / LOS) — numbers never sit on the moving marker.
 *
 *   mount(el, { t, height, showStrip }) -> { update(model), destroy() }
 *
 * MODEL (plain values; the planner's /api/ground-track rows work as is):
 *   nowMs                    sim "now", epoch ms (required for past/future)
 *   track   [{utc|t, lat, lon, in_eclipse|ecl, sun_fraction?}]
 *   position {lat, lon, altKm, verdict?, ageS?, src?}   (else interpolated)
 *   stations [{name, lat_deg|lat, lon_deg|lon, min_elevation_deg|maskDeg}]
 *   contacts [{station, aos, los, maxEl?}]  (ISO or ms)  — next AOS / LOS
 *   inContact  station name currently in contact, or ""
 *   fovDeg   imager full cross-track FOV for the footprint (optional)
 *   inEclipse, sunFraction  present illumination (else the track's flag)
 *   eclipseSource  "spacecraft" | "ground_propagator" (printed)
 * ============================================================================ */

import { LAND } from "./land110m.js";
import {
  injectBase, injectCss, translator, fmt, fin, esc, valueHtml, tableHtml, svgEl, clear,
  valuesToggle, fmtClock, fmtUtc,
} from "./vizkit.js";

/* ── pure geometry (exported for tests) ───────────────────────────────── */

const RE_KM = 6378.137;
const D2R = Math.PI / 180, R2D = 180 / Math.PI;
const wrapLon = (lon) => ((((lon + 180) % 360) + 360) % 360) - 180;

/** Sub-solar point at `ms` (low-precision almanac, < 0.1 deg; the planner's). */
export function subsolarPoint(ms) {
  const JD = ms / 86400000 + 2440587.5;
  const n = JD - 2451545.0;
  const L0 = (280.460 + 0.9856474 * n) % 360;
  const g = (((357.528 + 0.9856003 * n) % 360)) * D2R;
  const lambda = (L0 + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * D2R;
  const eps = (23.439 - 0.0000004 * n) * D2R;
  const decl = Math.asin(Math.sin(eps) * Math.sin(lambda));
  const RA = Math.atan2(Math.cos(eps) * Math.sin(lambda), Math.cos(lambda));
  const eqTime = ((L0 * D2R - RA) * 720) / Math.PI;      // minutes
  const d = new Date(ms);
  const utcH = d.getUTCHours() + d.getUTCMinutes() / 60 + d.getUTCSeconds() / 3600;
  return { lat: decl * R2D, lon: wrapLon((12 - utcH - eqTime / 60) * 15) };
}
/** Latitude of the ground terminator at `lon` for a sub-solar point. */
export function terminatorLat(lon, ss) {
  const dec = ss.lat * D2R;
  if (Math.abs(dec) < 1e-6) return 0;   // equinox: the terminator is a meridian pair; handled by caller
  return Math.atan(-Math.cos((lon - ss.lon) * D2R) / Math.tan(dec)) * R2D;
}
/** Earth-central angle (deg) from a station to the edge of its visibility at
 *  elevation mask `maskDeg` for a spacecraft at `altKm`. */
export function coverageAngleDeg(altKm, maskDeg) {
  const e = maskDeg * D2R;
  return (Math.acos((RE_KM / (RE_KM + altKm)) * Math.cos(e)) - e) * R2D;
}
/** Small circle of angular radius `lamDeg` about (lat, lon): [[lon, lat]...]. */
export function smallCircle(lat, lon, lamDeg, n = 120) {
  const la = lat * D2R, lo = lon * D2R, lam = lamDeg * D2R, out = [];
  for (let k = 0; k <= n; k++) {
    const az = (k / n) * 2 * Math.PI;
    const lat2 = Math.asin(Math.sin(la) * Math.cos(lam) + Math.cos(la) * Math.sin(lam) * Math.cos(az));
    const lon2 = lo + Math.atan2(Math.sin(az) * Math.sin(lam) * Math.cos(la), Math.cos(lam) - Math.sin(la) * Math.sin(lat2));
    out.push([wrapLon(lon2 * R2D), lat2 * R2D]);
  }
  return out;
}
const toMs = (x) => (x instanceof Date ? x.getTime() : typeof x === "number" ? x : Date.parse(x));
/** Normalise served rows to {t, lat, lon, ecl, sf}. */
export function normTrack(rows) {
  return (rows || []).map((p) => ({
    t: toMs(p.t ?? p.utc), lat: Number(p.lat), lon: Number(p.lon),
    ecl: !!(p.ecl ?? p.in_eclipse),
    sf: fin(p.sun_fraction) ? Number(p.sun_fraction) : null,
    alt: fin(p.alt_km) ? Number(p.alt_km) : null,
  })).filter((p) => Number.isFinite(p.t) && fin(p.lat) && fin(p.lon)).sort((a, b) => a.t - b.t);
}
/** Track position at `ms` (linear, antimeridian-aware), or null outside. */
export function interpTrack(tr, ms) {
  for (let i = 1; i < tr.length; i++) {
    const a = tr[i - 1], b = tr[i];
    if (ms >= a.t && ms <= b.t) {
      const f = b.t === a.t ? 0 : (ms - a.t) / (b.t - a.t);
      let dl = b.lon - a.lon;
      if (dl > 180) dl -= 360;
      if (dl < -180) dl += 360;
      return { lat: a.lat + f * (b.lat - a.lat), lon: wrapLon(a.lon + f * dl), ecl: f < 0.5 ? a.ecl : b.ecl,
        alt: a.alt !== null && b.alt !== null ? a.alt + f * (b.alt - a.alt) : a.alt, heading: Math.atan2(dl, b.lat - a.lat) * R2D };
    }
  }
  return null;
}
/** Eclipse transitions after `ms` in the track: [{t, kind:"entry"|"exit", lat, lon}]. */
export function eclipseTransitions(tr, ms = -Infinity) {
  const out = [];
  for (let i = 1; i < tr.length; i++) {
    if (tr[i].ecl !== tr[i - 1].ecl && tr[i].t > ms) {
      out.push({ t: tr[i].t, kind: tr[i].ecl ? "entry" : "exit", lat: tr[i].lat, lon: tr[i].lon });
    }
  }
  return out;
}

/* Reasons passed to t() as variables.
// i18n-keys (English text is the i18n key)
 */
export const I18N_KEYS = ["none in the served window", "no contacts served", "not in the served track"];

/* ── view ──────────────────────────────────────────────────────────────── */


const CSS = `
.vz-gt{ display:grid; grid-template-columns:minmax(0,1fr) 220px; gap:0 var(--sp-4,16px); }
.vz-gt > .vz-bar,.vz-gt > .vz-tabhost,.vz-gt > .vz-legend{ grid-column:1 / -1; }
.vz-gt.no-strip{ grid-template-columns:minmax(0,1fr); }
.vz-gt .vz-map{ position:relative; border:1px solid var(--vz-line); border-radius:var(--radius,3px); overflow:hidden;
  background:var(--vz-s1); }
.vz-gt .vz-map.is-stale{ border-style:dashed; border-color:var(--vz-stale); }
.vz-gt svg{ display:block; width:100%; height:auto; }
.vz-gt .sea{ fill:var(--vz-s1); }
.vz-gt .land{ fill:var(--vz-s3); stroke:var(--vz-line2); stroke-width:.5; }
.vz-gt .grid{ stroke:var(--vz-line); stroke-width:.5; fill:none; }
.vz-gt .night{ fill:var(--vz-overlay); fill-opacity:.5; }
.vz-gt .term{ fill:none; stroke:var(--vz-tx3); stroke-width:.75; stroke-dasharray:1 3; }
.vz-gt .vis{ fill:none; stroke:var(--vz-tx3); stroke-width:.8; stroke-opacity:.7; }
.vz-gt .vis.on{ stroke:var(--vz-accent); stroke-width:1.4; stroke-dasharray:none; }
.vz-gt .past{ fill:none; stroke:var(--vz-tx3); stroke-width:1; stroke-dasharray:1 3; stroke-linecap:round; }
.vz-gt .sun{ fill:none; stroke:var(--vz-val); stroke-width:1.6; stroke-linejoin:round; }
.vz-gt .ecl{ fill:none; stroke:var(--vz-tx2); stroke-width:1.6; stroke-dasharray:5 4; }
.vz-gt .ctc{ fill:none; stroke:var(--vz-accent); stroke-width:4; stroke-opacity:.45; stroke-linecap:round; }
.vz-gt .tick{ stroke:var(--vz-val); stroke-width:1.4; }
.vz-gt .tick.exit{ stroke:var(--vz-tx2); }
.vz-gt .stn{ fill:var(--vz-bg); stroke:var(--vz-tx2); stroke-width:1.2; }
.vz-gt .stn.on{ fill:var(--vz-accent); stroke:var(--vz-accent); }
.vz-gt .stn-l{ font-size:12px; fill:var(--vz-tx2); paint-order:stroke; stroke:var(--vz-s1); stroke-width:3px; stroke-linejoin:round; }
.vz-gt .ax{ font-size:12px; fill:var(--vz-tx3); }
.vz-gt .fp{ fill:var(--vz-val); fill-opacity:.08; stroke:var(--vz-val); stroke-width:.8; stroke-dasharray:2 2; }
.vz-gt .sc{ fill:var(--vz-val); stroke:var(--vz-bg); stroke-width:1.5; }
.vz-gt .sc-ring{ fill:none; stroke:var(--vz-val); stroke-width:1; }
.vz-gt .vz-map.is-stale .sc{ fill:var(--vz-tx3); }
.vz-gt .ss{ fill:none; stroke:var(--vz-tx2); stroke-width:1; }
.vz-gt .vz-strip{ display:flex; flex-direction:column; border-top:1px solid var(--vz-line); }
.vz-gt .vz-row{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:2px 8px; align-items:baseline;
  padding:6px 0; border-bottom:1px solid var(--vz-line); }
.vz-gt .vz-row > .k{ font-size:var(--fs-label,12px); color:var(--vz-tx3); }
.vz-gt .vz-row > .v{ text-align:right; }
.vz-gt .vz-row > .d{ grid-column:1 / -1; font-size:var(--fs-label,12px); color:var(--vz-tx3); }
.vz-gt .vz-legend{ display:flex; gap:4px 16px; flex-wrap:wrap; padding-top:6px; font-size:var(--fs-label,12px); color:var(--vz-tx3); }
.vz-gt .vz-legend svg{ width:22px; height:10px; vertical-align:-1px; margin-right:4px; overflow:visible; }
.vz-gt .vz-empty{ position:absolute; left:0; right:0; top:42%; text-align:center; color:var(--vz-tx2); }
@media (max-width: 720px){
  .vz-gt{ grid-template-columns:minmax(0,1fr); }
  .vz-gt .vz-strip{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:16px; margin-top:8px; }
  .vz-gt .ax{ display:none; }
}
`;

export function mount(el, opts = {}) {
  injectBase();
  injectCss("vz-gt-css", CSS);
  const t = translator(opts);
  const d = globalThis.document;
  const uid = Math.random().toString(36).slice(2, 8);
  let model = null;
  /* The SVG is drawn at its rendered pixel size (redrawn on resize) so text
   * stays at the 12 px floor instead of shrinking with a scaled viewBox. */
  let W = 720, H = 360;
  const P = (lon, lat) => [((lon + 180) / 360) * W, ((90 - lat) / 180) * H];
  /** SVG path of a [lon, lat] polyline, broken where it wraps the antimeridian. */
  const pathOf = (pts) => {
    let dd = "", prev = null;
    for (const [lon, lat] of pts) {
      const [x, y] = P(lon, lat);
      dd += (prev === null || Math.abs(lon - prev) > 180 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1);
      prev = lon;
    }
    return dd;
  };

  const root = d.createElement("div");
  root.className = "vz vz-gt" + (opts.showStrip === false ? " no-strip" : "");
  el.appendChild(root);
  const bar = d.createElement("div");
  bar.className = "vz-bar";
  const cap = d.createElement("span");
  cap.className = "vz-cap";
  const sp = d.createElement("span");
  sp.className = "vz-sp";
  const tabHost = d.createElement("div");
  tabHost.className = "vz-tabhost";
  const vt = valuesToggle(t, tabHost, `vz-gt-tab-${uid}`);
  vt.btn.addEventListener("click", () => draw());
  bar.append(cap, sp, vt.btn);
  if (opts.showBar !== false) root.appendChild(bar);

  const mapBox = d.createElement("div");
  mapBox.className = "vz-map";
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-labelledby": `vz-gt-ti-${uid} vz-gt-de-${uid}` });
  const title = svgEl("title", { id: `vz-gt-ti-${uid}` });
  const desc = svgEl("desc", { id: `vz-gt-de-${uid}` });
  svg.append(title, desc);
  const gBase = svgEl("g"), gNight = svgEl("g"), gVis = svgEl("g"), gTrack = svgEl("g"), gTop = svgEl("g");
  svg.append(gBase, gNight, gVis, gTrack, gTop);
  mapBox.appendChild(svg);
  const empty = d.createElement("div");
  empty.className = "vz-empty";
  empty.hidden = true;
  mapBox.appendChild(empty);
  const strip = d.createElement("div");
  strip.className = "vz-strip";
  const legend = d.createElement("div");
  legend.className = "vz-legend";
  root.append(mapBox);
  if (opts.showStrip !== false) root.append(strip);
  root.append(legend, tabHost);

  /* basemap: sea, land, graticule, axis labels (rebuilt on resize) */
  function drawBase() {
    clear(gBase);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    gBase.appendChild(svgEl("rect", { class: "sea", x: 0, y: 0, width: W, height: H }));
    let land = "";
    for (const ring of LAND) {
      for (let i = 0; i < ring.length; i += 2) {
        const [x, y] = P(ring[i], ring[i + 1]);
        land += (i ? "L" : "M") + x.toFixed(1) + " " + y.toFixed(1);
      }
      land += "Z";
    }
    gBase.appendChild(svgEl("path", { class: "land", d: land }));
    let grid = "";
    for (let lon = -150; lon <= 150; lon += 30) { const [x] = P(lon, 0); grid += `M${x} 0V${H}`; }
    for (let lat = -60; lat <= 60; lat += 30) { const [, y] = P(0, lat); grid += `M0 ${y}H${W}`; }
    gBase.appendChild(svgEl("path", { class: "grid", d: grid }));
    for (let lon = -120; lon <= 120; lon += 60) {
      const [x] = P(lon, 0);
      gBase.appendChild(svgEl("text", { class: "ax", x: x + 3, y: H - 4 }, `${Math.abs(lon)}°${lon < 0 ? "W" : lon > 0 ? "E" : ""}`));
    }
    for (const lat of [-60, -30, 30, 60]) {
      const [, y] = P(-180, lat);
      gBase.appendChild(svgEl("text", { class: "ax", x: 3, y: y - 3 }, `${Math.abs(lat)}°${lat < 0 ? "S" : "N"}`));
    }
  }

  function stations() {
    return ((model && model.stations) || []).map((s) => ({
      name: s.name, lat: Number(s.lat_deg ?? s.lat), lon: Number(s.lon_deg ?? s.lon),
      mask: Number(s.min_elevation_deg ?? s.maskDeg ?? 5),
    })).filter((s) => fin(s.lat) && fin(s.lon));
  }

  function draw() {
    const m = model || {};
    const now = fin(m.nowMs) ? Number(m.nowMs) : null;
    const tr = normTrack(m.track);
    const pos = m.position && fin(m.position.lat) ? m.position : (now !== null ? interpTrack(tr, now) : null);
    const altKm = (pos && fin(pos.altKm) ? Number(pos.altKm) : null) ?? (pos && fin(pos.alt) ? pos.alt : null)
      ?? (tr.find((p) => p.alt !== null) || {}).alt ?? null;
    const stale = m.position && m.position.verdict === "stale";
    mapBox.classList.toggle("is-stale", !!stale);
    const inCtc = m.inContact || "";
    clear(gNight); clear(gVis); clear(gTrack); clear(gTop);

    /* night side + ground terminator */
    if (now !== null) {
      const ss = subsolarPoint(now);
      const pts = [];
      for (let lon = -180; lon <= 180; lon += 2) pts.push([lon, terminatorLat(lon, ss)]);
      const pole = ss.lat >= 0 ? -90 : 90;
      let dn = pathOf(pts) + `L${W} ${P(0, pole)[1]}L0 ${P(0, pole)[1]}Z`;
      gNight.appendChild(svgEl("path", { class: "night", d: dn }));
      gNight.appendChild(svgEl("path", { class: "term", d: pathOf(pts) }));
      const [sx, sy] = P(ss.lon, ss.lat);
      const sun = svgEl("g", { transform: `translate(${sx.toFixed(1)} ${sy.toFixed(1)})` });
      sun.appendChild(svgEl("circle", { class: "ss", r: 4 }));
      sun.appendChild(svgEl("circle", { class: "ss", r: 1.2 }));
      sun.appendChild(svgEl("title", {}, t("Sub-solar point")));
      gNight.appendChild(sun);
    }

    /* station visibility circles at each mask, for the spacecraft altitude */
    const sts = stations();
    if (altKm !== null) {
      for (const s of sts) {
        const lam = coverageAngleDeg(altKm, s.mask);
        const c = svgEl("path", { class: "vis" + (s.name === inCtc ? " on" : ""), d: pathOf(smallCircle(s.lat, s.lon, lam)) });
        c.appendChild(svgEl("title", {}, t("{{name}} visibility at {{mask}}° elevation", { name: s.name, mask: fmt(s.mask, 0) })));
        gVis.appendChild(c);
      }
    }

    /* track: past, future sunlit / eclipse; contact runs */
    const ctcs = ((m.contacts) || []).map((c) => ({ station: c.station ?? c.gs_name, aos: toMs(c.aos), los: toMs(c.los),
      maxEl: c.maxEl ?? c.max_elevation_deg })).filter((c) => Number.isFinite(c.aos) && Number.isFinite(c.los));
    const inPass = (ms) => ctcs.some((c) => ms >= c.aos && ms <= c.los);
    const runs = { past: [], sun: [], ecl: [], ctc: [] };
    let cur = null, curKind = null, ctcRun = [];
    const flush = () => { if (cur && cur.length > 1) runs[curKind].push(cur); cur = null; };
    for (let i = 0; i < tr.length; i++) {
      const p = tr[i];
      const kind = now !== null && p.t < now ? "past" : p.ecl ? "ecl" : "sun";
      if (kind !== curKind) {
        const last = cur && cur[cur.length - 1];
        flush();
        cur = last ? [last] : [];
        curKind = kind;
      }
      cur.push([p.lon, p.lat]);
      if (now !== null && p.t >= now && inPass(p.t)) ctcRun.push([p.lon, p.lat]);
      else { if (ctcRun.length > 1) runs.ctc.push(ctcRun); ctcRun = []; }
    }
    flush();
    if (ctcRun.length > 1) runs.ctc.push(ctcRun);
    for (const r of runs.ctc) gTrack.appendChild(svgEl("path", { class: "ctc", d: pathOf(r) }));
    for (const k of ["past", "ecl", "sun"]) {
      for (const r of runs[k]) gTrack.appendChild(svgEl("path", { class: k, d: pathOf(r) }));
    }
    // eclipse entry / exit ticks across the track (future only)
    const trans = eclipseTransitions(tr, now ?? -Infinity);
    for (const e of trans) {
      const [x, y] = P(e.lon, e.lat);
      const tk = svgEl("path", { class: "tick " + e.kind, d: `M${(x - 5).toFixed(1)} ${y.toFixed(1)}H${(x + 5).toFixed(1)}` });
      tk.appendChild(svgEl("title", {}, (e.kind === "entry" ? t("Eclipse entry") : t("Eclipse exit")) + " " + fmtUtc(e.t)));
      gTrack.appendChild(tk);
    }

    /* stations on top */
    for (const s of sts) {
      const [x, y] = P(s.lon, s.lat);
      const on = s.name === inCtc;
      const g = svgEl("g", { transform: `translate(${x.toFixed(1)} ${y.toFixed(1)})` });
      g.appendChild(svgEl("path", { class: "stn" + (on ? " on" : ""), d: "M0 -5L4.5 3.5H-4.5Z" }));
      const right = x < W - 80;
      g.appendChild(svgEl("text", { class: "stn-l", x: right ? 7 : -7, y: 4, "text-anchor": right ? "start" : "end" }, s.name));
      gTop.appendChild(g);
    }

    /* spacecraft + footprint */
    empty.hidden = !!pos || !!tr.length;
    if (!pos && !tr.length) empty.textContent = t("No ground track served");
    if (pos) {
      const [x, y] = P(pos.lon, pos.lat);
      if (fin(m.fovDeg) && altKm !== null) {
        const halfKm = altKm * Math.tan((m.fovDeg / 2) * D2R);
        const fp = svgEl("path", { class: "fp", d: pathOf(smallCircle(pos.lat, pos.lon, (halfKm / RE_KM) * R2D, 48)) + "Z" });
        fp.appendChild(svgEl("title", {}, t("Imager footprint ({{km}} km swath)", { km: fmt(2 * halfKm, 0) })));
        gTop.appendChild(fp);
      }
      const g = svgEl("g", { transform: `translate(${x.toFixed(1)} ${y.toFixed(1)})` });
      g.appendChild(svgEl("circle", { class: "sc-ring", r: 8.5 }));
      g.appendChild(svgEl("path", { class: "sc", d: "M0 -6L5 0L0 6L-5 0Z" }));
      g.appendChild(svgEl("title", {}, t("Spacecraft")));
      gTop.appendChild(g);
    }

    renderStrip(m, pos, altKm, now, tr, trans, ctcs);
    title.textContent = t("Ground track");
    desc.textContent = summary(m, pos, now, trans, ctcs);
    cap.textContent = tr.length ? t("{{n}} min of track · {{src}}", {
      n: fmt((tr[tr.length - 1].t - tr[0].t) / 60000, 0),
      src: m.eclipseSource === "spacecraft" ? t("eclipse now from the spacecraft") : t("ground propagation") }) : "";
    legend.innerHTML = legendHtml();
  }

  function nextPass(ctcs, now) {
    if (now === null) return null;
    return ctcs.filter((c) => c.los > now).sort((a, b) => a.aos - b.aos)[0] || null;
  }
  function illum(m, pos) {
    if (m.inEclipse === true || m.inEclipse === false) {
      const f = fin(m.sunFraction) ? Number(m.sunFraction) : (m.inEclipse ? 0 : 1);
      return f >= 0.999 ? t("Sunlit") : f <= 0.001 ? t("Eclipse") : t("Penumbra {{pct}} %", { pct: fmt(f * 100, 0) });
    }
    return pos ? (pos.ecl ? t("Eclipse") : t("Sunlit")) : null;
  }
  function renderStrip(m, pos, altKm, now, tr, trans, ctcs) {
    const vv = (x, digits, units, o = {}) => valueHtml(x, { digits, units, t, verdict: m.position && m.position.verdict, ageS: m.position && m.position.ageS, ...o });
    const latS = pos ? `${fmt(Math.abs(pos.lat), 2)}° ${pos.lat >= 0 ? "N" : "S"}` : null;
    const lonS = pos ? `${fmt(Math.abs(pos.lon), 2)}° ${pos.lon >= 0 ? "E" : "W"}` : null;
    const row = (k, html, dsc) => `<div class="vz-row"><span class="k">${esc(k)}</span><span class="v">${html}</span>` +
      (dsc ? `<span class="d">${esc(dsc)}</span>` : "") + `</div>`;
    const il = illum(m, pos);
    const nx = trans[0];
    const np = nextPass(ctcs, now);
    let passHtml, passK, passD = "";
    if (np && now !== null && np.aos <= now) {
      passK = t("LOS {{station}}", { station: np.station });
      passHtml = vv(null, 0, "", { text: fmtClock((np.los - now) / 1000), verdict: "fresh" });
      passD = t("in contact · LOS {{utc}} UTC", { utc: fmtUtc(np.los) });
    } else if (np && now !== null) {
      passK = t("Next AOS {{station}}", { station: np.station });
      passHtml = vv(null, 0, "", { text: fmtClock((np.aos - now) / 1000), verdict: "fresh" });
      passD = t("AOS {{aos}} · {{min}} min · max {{el}}°", { aos: fmtUtc(np.aos), min: fmt((np.los - np.aos) / 60000, 0),
        el: fin(np.maxEl) ? fmt(np.maxEl, 0) : "?" });
    } else {
      passK = t("Next AOS");
      passHtml = valueHtml(null, { t, reason: ctcs.length ? "none in the served window" : "no contacts served" });
    }
    strip.innerHTML = [
      row(t("Latitude"), vv(pos ? pos.lat : null, 2, "", { text: latS ?? undefined })),
      row(t("Longitude"), vv(pos ? pos.lon : null, 2, "", { text: lonS ?? undefined })),
      row(t("Altitude"), vv(altKm, 1, "km")),
      row(t("Illumination"), il ? `<span class="vz-v" style="font-size:var(--fs-body,13px)">${esc(il)}</span>` : valueHtml(null, { t })),
      row(nx ? (nx.kind === "entry" ? t("Eclipse entry in") : t("Eclipse exit in")) : t("Next eclipse transition"),
        nx && now !== null ? vv(null, 0, "", { text: fmtClock((nx.t - now) / 1000), verdict: "fresh" })
          : valueHtml(null, { t, reason: "not in the served track" }), nx ? `${fmtUtc(nx.t)} UTC` : ""),
      row(passK, passHtml, passD),
    ].join("");
    if (vt.isOpen()) {
      tabHost.innerHTML = tableHtml(t("Ground track values"), [
        { label: t("Latitude"), html: vv(pos ? pos.lat : null, 3, "°"), src: m.position && m.position.src || t("interpolated from the served track") },
        { label: t("Longitude"), html: vv(pos ? pos.lon : null, 3, "°"), src: m.position && m.position.src || t("interpolated from the served track") },
        { label: t("Altitude"), html: vv(altKm, 2, "km"), src: "" },
        { label: t("Illumination"), html: il ? esc(il) : valueHtml(null, { t }), src: m.eclipseSource || "" },
        ...trans.slice(0, 4).map((e) => ({ label: e.kind === "entry" ? t("Eclipse entry") : t("Eclipse exit"),
          html: esc(fmtUtc(e.t, true)) + " UTC", src: t("served track") })),
        ...ctcs.filter((c) => now === null || c.los > now).slice(0, 4).map((c) => ({
          label: t("Pass {{station}}", { station: c.station }),
          html: esc(`${fmtUtc(c.aos)}–${fmtUtc(c.los)} UTC`), src: fin(c.maxEl) ? t("max {{el}}°", { el: fmt(c.maxEl, 1) }) : "" })),
        ...stations().map((s) => ({ label: t("{{name}} visibility radius", { name: s.name }),
          html: altKm !== null ? esc(fmt(coverageAngleDeg(altKm, s.mask) * D2R * RE_KM, 0)) + `<span class="u">km</span>` : valueHtml(null, { t }),
          src: t("mask {{mask}}°", { mask: fmt(s.mask, 0) }) })),
      ], t);
    }
  }
  function summary(m, pos, now, trans, ctcs) {
    if (!pos) return t("Ground track map. No current position.");
    const parts = [t("Spacecraft over {{lat}}, {{lon}}.", {
      lat: `${fmt(Math.abs(pos.lat), 1)}° ${pos.lat >= 0 ? "N" : "S"}`, lon: `${fmt(Math.abs(pos.lon), 1)}° ${pos.lon >= 0 ? "E" : "W"}` })];
    const il = illum(m, pos);
    if (il) parts.push(il + ".");
    if (trans[0] && now !== null) parts.push(t("{{what}} in {{min}} min.", {
      what: trans[0].kind === "entry" ? t("Eclipse entry") : t("Eclipse exit"), min: fmt((trans[0].t - now) / 60000, 0) }));
    const np = nextPass(ctcs, now);
    if (np && now !== null) parts.push(np.aos <= now ? t("In contact with {{s}}.", { s: np.station })
      : t("Next AOS {{s}} in {{min}} min.", { s: np.station, min: fmt((np.aos - now) / 60000, 0) }));
    return parts.join(" ");
  }
  function legendHtml() {
    const ln = (cls, extra = "") => `<svg viewBox="0 0 22 10" aria-hidden="true"><line x1="1" y1="5" x2="21" y2="5" ${extra} style="${cls}"/></svg>`;
    return [
      `<span>${ln("stroke:var(--vz-val);stroke-width:1.6")}${esc(t("Sunlit"))}</span>`,
      `<span>${ln("stroke:var(--vz-tx2);stroke-width:1.6;stroke-dasharray:5 4")}${esc(t("Spacecraft in eclipse"))}</span>`,
      `<span>${ln("stroke:var(--vz-tx3);stroke-dasharray:1 3;stroke-linecap:round")}${esc(t("Past"))}</span>`,
      `<span>${ln("stroke:var(--vz-accent);stroke-width:4;stroke-opacity:.45")}${esc(t("Predicted contact"))}</span>`,
      `<span>${ln("stroke:var(--vz-tx3);stroke-width:.8;stroke-opacity:.7")}${esc(t("Station visibility at mask"))}</span>`,
      `<span><svg viewBox="0 0 22 10" aria-hidden="true"><rect x="1" y="1" width="20" height="8" style="fill:var(--vz-overlay);fill-opacity:.5;stroke:var(--vz-tx3);stroke-dasharray:1 3"/></svg>${esc(t("Night on the ground"))}</span>`,
    ].join("");
  }

  function size() {
    const w = Math.round(mapBox.clientWidth || 720);
    if (w < 40 || w === W) return false;
    W = w; H = Math.round(w / 2);
    drawBase();
    return true;
  }
  let ro = null;
  try { ro = new ResizeObserver(() => { if (size()) draw(); }); ro.observe(mapBox); } catch (e) { /* fixed size */ }
  size();
  drawBase();
  draw();
  return {
    update(m) { model = m || null; draw(); },
    destroy() { if (ro) ro.disconnect(); root.remove(); },
  };
}
