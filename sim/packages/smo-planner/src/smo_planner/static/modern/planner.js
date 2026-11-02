/* ============================================================================
 * C2O MISSION PLANNER — modern interactive page logic
 * (plan §2.2; design-system pass 2026-11, docs/ui/C2O_UI_BRIEF.md)
 * ============================================================================
 * ES module, no build step. Companion to modern/index.html; classic
 * reference is ../index.html (frozen).
 *
 * Endpoints used (all pre-existing planner routes — additive-only API rule):
 *   GET  /api/time-source                 clock anchor + mode (5 s)
 *   GET  /api/spacecraft-state            position / eclipse / contact (5 s)
 *   GET  /api/contacts                    contact windows (30 s poll)
 *   GET  /api/schedule                    activity schedule (30 s poll)
 *   POST /api/schedule                    add activity (dialog)
 *   PUT  /api/schedule/{id}               edit activity (per-row Edit)
 *   DELETE /api/schedule/{id}             delete activity (per-row, two-step)
 *   DELETE /api/schedule                  clear schedule (two-step)
 *   GET  /api/schedule/templates          standard activity sets
 *   POST /api/schedule/load-template      instantiate a set
 *   GET  /api/schedule/validate           schedule validation (every poll:
 *                                         flags rows, gates the upload)
 *   POST /api/schedule/upload             upload to MCS (two-step)
 *   GET  /api/activity-types              dialog type list + descriptions
 *   GET  /api/ground-stations             station list (canonical, orbit.yaml)
 *   GET  /api/ground-track                map track (120 s) + 24 h eclipse arcs
 *   GET  /api/config/planner              orbit/budget configuration (P4)
 *   GET  /api/budget/power                power budget (30 s) — SoC trace
 *   GET  /api/budget/data                 data budget (30 s)
 *   GET  /api/imaging/targets             target list
 *   GET  /api/imaging/opportunities       imaging windows (30 s)
 *   POST /api/imaging/schedule            schedule a capture
 *   GET  /api/constraints/validate        aggregate check (explicit SoC — P5)
 *   GET  /api/constraints/power|aocs|thermal|data-volume|conflicts
 *                                         per-domain breakdown (disclosures)
 *
 * States (brief §1.3): every button is enabled, disabled WITH a reason
 * (setDisabled), armed (armButton: clear schedule, delete, upload) or active.
 * Values that were never served say "no data" / "not served" — never a dash.
 *
 * Polling cadences preserved from the classic page (Report 1 §1B):
 *   1 s clock + countdowns · 5 s spacecraft-state · 5 s time-source ·
 *   10 s picture redraw · 30 s main poll · 60 s terminator · 120 s track.
 * ============================================================================ */

import {
  esc, poller, mountLangToggle, renderChip, renderGauge, renderNoData, renderBanner,
  glyph, setDisabled, setEnabled, armButton,
} from "/static/shared/components.js";
import { fmtUTC, fmtMET } from "/static/shared/format.js";
// UI language (EN|FR) — see docs/i18n/UI_I18N_GUIDE.md. Identifiers never
// go through t(); tText() for attributes, canvas/SVG text and textContent.
import { I18n, t, tText, tdb, onLangChange } from "/static/shared/i18n.js";

const $ = (id) => document.getElementById(id);
const SVGNS = "http://www.w3.org/2000/svg";

/* ── Server clock (P2 / defect #58): the ONE time primitive ───────────── */
let timeSource = null;          // null until /api/time-source resolves (P3)
let simAnchorMs = null, simAnchorWallMs = null, simSpeed = 1.0;
let metAnchorS = null;          // MET at the anchor instant; null = not served
let clockDegraded = false, clockNote = null;   // () => translated note | null
const clockNoteText = () => (clockNote ? clockNote() : "");

function simNow() {
  if (simAnchorMs === null) return Date.now();
  return simAnchorMs + (Date.now() - simAnchorWallMs) * simSpeed;
}
const simNowDate = () => new Date(simNow());
function metNowS() {
  if (metAnchorS === null || simAnchorMs === null) return null;
  return metAnchorS + (simNow() - simAnchorMs) / 1000;
}

/* ── Page state ───────────────────────────────────────────────────────── */
let contacts = [];              // {station, aos:Date, los:Date, maxEl, durationMin}
let schedule = [];              // raw rows + start:Date, durationMin
let groundStations = [], groundStationsError = false;
let mapTrack = [];              // 3 h map window (past 90 min + future)
let eclipseTrack = [];          // 24 h track for timeline arcs / next eclipse
let scState = null;
let plannerConfig = null, budgetParams = null, services = null;
let activityTypes = [], planTemplates = [], imagingOpps = [];
let powerBudget = null, dataBudget = null;
let validation = null;          // GET /api/schedule/validate (last good)
let constraintCheck = null;     // GET /api/constraints/validate (last good)
let apiOk = null;               // null = not yet known
let uploadMode = "s11";

/* Cross-origin service URL join (G14): the path literal deliberately has no
 * leading slash — it is relative to the CONFIGURED base
 * (planning/planner.yaml services.*), never a planner route. */
function serviceUrl(base, path) {
  return String(base).replace(/\/+$/, "") + "/" + path;
}

/* ── Small formatters ─────────────────────────────────────────────────── */
const pad2 = (n) => String(n).padStart(2, "0");
const hhmm = (d) => pad2(d.getUTCHours()) + ":" + pad2(d.getUTCMinutes());
function countdown(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h > 0 ? h + ":" + pad2(m) + ":" + pad2(s % 60) : pad2(m) + ":" + pad2(s % 60);
}
const num = (v, d) => (v === null || v === undefined || !Number.isFinite(Number(v)))
  ? null : Number(v).toFixed(d);
const minPart = (min) => tText("{{n}} min", { n: min });
const PRIORITY = { high: () => tText("High"), medium: () => tText("Medium"), low: () => tText("Low") };
const prioText = (p) => (PRIORITY[p] ? PRIORITY[p]() : (p || ""));

/* ── Derived orbit values (P4: from served data, never literals) ──────── */
const MU_KM3_S2 = 398600.4418, EARTH_R_KM = 6378.137;
function orbitPeriodMin() {
  const alt = budgetParams && Number(budgetParams.orbit_altitude_km);
  if (!alt || !Number.isFinite(alt)) return null;
  const a = EARTH_R_KM + alt;
  return (2 * Math.PI * Math.sqrt((a * a * a) / MU_KM3_S2)) / 60;
}
function inclinationEstimateDeg() {
  // Max |lat| of the served track = i (prograde) or 180-i (retrograde);
  // the longitude drift at the northernmost point tells the two apart.
  const tr = eclipseTrack.length ? eclipseTrack : mapTrack;
  if (tr.length < 3) return null;
  let iMax = 0;
  for (let i = 1; i < tr.length; i++) {
    if (Math.abs(tr[i].lat) > Math.abs(tr[iMax].lat)) iMax = i;
  }
  const maxLat = Math.abs(tr[iMax].lat);
  const j = Math.min(iMax + 1, tr.length - 1), k = Math.max(iMax - 1, 0);
  let dLon = tr[j].lon - tr[k].lon;
  if (dLon > 180) dLon -= 360;
  if (dLon < -180) dLon += 360;
  return dLon >= 0 ? maxLat : 180 - maxLat;
}

/* ── Clock + source chips ─────────────────────────────────────────────── */
function updateClock() {
  const now = simNowDate();
  $("utcClock").textContent = fmtUTC(now);
  $("utcDate").textContent = now.toISOString().slice(0, 10);
  const met = metNowS();
  const metEl = $("metReadout");
  if (met === null) {
    metEl.innerHTML = "MET " + renderNoData({ label: tText("not served") });
    metEl.title = tText(
      "MET is not published by the planner in this mode (real mode has no simulator MET — disposition L4)");
  } else {
    metEl.textContent = fmtMET(met);
    metEl.title = tText("Mission elapsed time as published by the planner");
  }
  updateCountdowns();
}

// P1: the chip names the clock; the speed tooltip is deliberately gone.
// P3: it stays hidden until /api/time-source has answered.
function updateClockBadge() {
  const el = $("clockSourceBadge");
  if (timeSource === null && !clockDegraded) { el.hidden = true; return; }
  el.hidden = false;
  el.className = "";
  if (clockDegraded) {
    el.className = "wall";
    el.innerHTML = glyph("alarm-up") + " " + esc(tText("Wall clock"));
    el.title = clockNoteText() || tText("Planner sim clock unavailable — showing browser wall clock");
  } else if (timeSource === "sim") {
    el.className = "ds-training";
    el.textContent = tText("Training: sim time");
    el.title = tText("Clock source: {{src}}", { src: timeSource });
  } else {
    el.innerHTML = renderChip({ kind: "neutral", label: tText("Real UTC") });
    el.title = tText("Clock source: {{src}}", { src: timeSource });
  }
}

function renderApiChip() {
  $("apiChip").innerHTML = apiOk === null ? ""
    : apiOk ? renderChip({ kind: "ok", label: tText("Planner connected") })
      : renderChip({ kind: "alarm", label: tText("Planner unreachable"),
        title: tText("The last poll of /api/contacts or /api/schedule failed") });
}

async function loadTimeSource() {
  try {
    const res = await fetch("/api/time-source");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    if (data.time_source === "sim" || data.time_source === "real") {
      timeSource = data.time_source;
    }
    const serverNow = data.now || data.sim_time;
    if (serverNow) {
      simAnchorMs = new Date(serverNow).getTime();
      simAnchorWallMs = Date.now();
    }
    if (typeof data.speed === "number") simSpeed = data.speed;
    metAnchorS = (typeof data.met_s === "number") ? data.met_s : null;
    clockDegraded = !!(data.degraded || data.wall_clock_fallback);
    clockNote = null;
    if (data.wall_clock_fallback) {
      const url = data.sim_state_url;
      clockNote = url
        ? () => tText("Simulator at {{url}} is unreachable — planner is running on wall-clock UTC", { url })
        : () => tText("Simulator at the configured URL is unreachable — planner is running on wall-clock UTC");
    } else if (data.degraded) {
      const age = data.anchor_age_s;
      clockNote = () => tText("Sim clock anchor is stale ({{age}} s old)", { age });
    }
  } catch (e) {
    clockDegraded = true;
    clockNote = () => tText("Planner API unreachable — page is on browser wall clock");
  }
  updateClockBadge();
}

/* ── Planner configuration (P4) ───────────────────────────────────────── */
async function loadPlannerConfig() {
  const res = await fetch("/api/config/planner");
  if (!res.ok) throw new Error("HTTP " + res.status);
  const data = await res.json();
  plannerConfig = data.planner_config || null;
  budgetParams = data.budget_params || null;
  services = (plannerConfig && plannerConfig.services) || null;
  renderOrbitFacts();
  socHint();
}

function renderOrbitFacts() {
  const p = orbitPeriodMin();
  const notServed = () => renderNoData({ label: tText("not served") });
  $("bbPeriod").innerHTML = p ? esc(p.toFixed(1)) + " min" : notServed();
  $("bbRevDay").innerHTML = p ? esc((1440 / p).toFixed(2)) : notServed();
  const incl = inclinationEstimateDeg();
  $("bbIncl").innerHTML = incl === null ? renderNoData() : "~" + esc(incl.toFixed(1)) + "°";
  $("bbEcc").innerHTML = notServed();
}

const MIN_SOC = () => (plannerConfig && plannerConfig.budget
  && Number.isFinite(plannerConfig.budget.min_soc_percent)) ? plannerConfig.budget.min_soc_percent : null;

/* SoC input placeholder/title: generic until the configured default is known. */
function socHint() {
  const soc = plannerConfig && plannerConfig.budget
    && plannerConfig.budget.initial_soc_percent;
  const socEl = $("socInput");
  if (typeof soc === "number") {
    socEl.placeholder = tText("default {{soc}}", { soc });
    $("socHint").textContent = tText(
      "Blank uses the planner's configured default ({{soc}} % from planner.yaml).", { soc });
  } else {
    socEl.placeholder = tText("server default");
    $("socHint").textContent = tText("Blank uses the planner's configured default.");
  }
}

/* ── Ground track map (svg-world-map from /static/vendor/) ────────────── */
let map = null;
let trackLayers = [], gsMarkers = [], gsCircles = [], gsLabels = [];
let scMarker = null, scFootprint = null, nightOverlay = null;
const tok = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

function loadVendorMap() {
  // index.html already loads it with a <script> tag; injecting it again threw
  // "Identifier 'SMO_COASTLINE' has already been declared" on every load.
  if (typeof window.SvgWorldMap !== "undefined") return Promise.resolve(true);
  return new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = "/static/vendor/js/svg-world-map.js";
    s.onload = () => resolve(typeof window.SvgWorldMap !== "undefined");
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  });
}

async function initMap() {
  const ok = await loadVendorMap();
  if (!ok) {
    // Designed vendor-missing state (risk R3) — never a silent black box.
    $("groundTrackMap").style.display = "none";
    $("mapFallback").style.display = "block";
    return;
  }
  map = new SvgWorldMap("groundTrackMap");
  updateTerminator();
  setInterval(updateTerminator, 60000);           // 60 s (classic cadence)
  drawGroundTrack();
  updateGroundStationMarkers();
  updateSpacecraftMarker();
}

function computeSubsolarPoint(date) {
  const JD = date.getTime() / 86400000 + 2440587.5;
  const n = JD - 2451545.0;
  const L0 = (280.460 + 0.9856474 * n) % 360;
  const g = ((357.528 + 0.9856003 * n) % 360) * Math.PI / 180;
  const lambda = (L0 + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * Math.PI / 180;
  const epsilon = (23.439 - 0.0000004 * n) * Math.PI / 180;
  const decl = Math.asin(Math.sin(epsilon) * Math.sin(lambda));
  const RA = Math.atan2(Math.cos(epsilon) * Math.sin(lambda), Math.cos(lambda));
  const eqTime = (L0 * Math.PI / 180 - RA) * 720 / Math.PI;
  const utcHours = date.getUTCHours() + date.getUTCMinutes() / 60 + date.getUTCSeconds() / 3600;
  const subLon = (12 - utcHours - eqTime / 60) * 15;
  return { lat: decl * 180 / Math.PI, lon: ((subLon + 180) % 360 + 360) % 360 - 180 };
}

function terminatorLatAtLon(lonDeg, subsolar) {
  const declR = subsolar.lat * Math.PI / 180;
  if (Math.abs(declR) < 1e-6) return 0;
  const H = (lonDeg - subsolar.lon) * Math.PI / 180;
  return Math.atan(-Math.cos(H) / Math.tan(declR)) * 180 / Math.PI;
}

function updateTerminator() {
  if (!map) return;
  const subsolar = computeSubsolarPoint(simNowDate());
  const poly = [];
  for (let lon = -180; lon <= 180; lon += 2) {
    poly.push([terminatorLatAtLon(lon, subsolar), lon]);
  }
  const nightPoleLat = subsolar.lat >= 0 ? -90 : 90;
  poly.push([nightPoleLat, 180]); poly.push([nightPoleLat, -180]);
  if (nightOverlay) map.removeLayer(nightOverlay);
  nightOverlay = map.addPolygon(poly, { fillColor: "#000000", fillOpacity: 0.4, color: "none" });
}

function updateGroundStationMarkers() {
  if (!map) return;
  for (const l of [...gsMarkers, ...gsCircles, ...gsLabels]) map.removeLayer(l);
  gsMarkers = []; gsCircles = []; gsLabels = [];
  const ink = tok("--tx2"), dim = tok("--tx3");
  for (const gs of groundStations) {
    gsMarkers.push(map.addMarker(gs.lat_deg, gs.lon_deg, {
      color: tok("--bg"), strokeColor: ink, radius: 3.5 }));
    gsLabels.push(map.addLabel(gs.lat_deg, gs.lon_deg, gs.name, { color: ink, fontSize: "6" }));
    gsCircles.push(map.addCircle(gs.lat_deg, gs.lon_deg, 2200, {
      color: dim, weight: 0.5, opacity: 0.35, fillColor: dim, fillOpacity: 0.03, dashArray: "2 3" }));
  }
}

function drawGroundTrack() {
  if (!map || mapTrack.length < 2) return;
  for (const l of trackLayers) map.removeLayer(l);
  trackLayers = [];
  const nowMs = simNow();
  const sun = tok("--val"), dim = tok("--tx3");
  let seg = [], segEclipse = mapTrack[0].in_eclipse;
  let segPast = new Date(mapTrack[0].utc).getTime() < nowMs;
  const flush = () => {
    if (seg.length > 1) {
      // Calm by default (brief §1.4): the track is ink, not colour; eclipse
      // is dashed, the past is a faint dotted line.
      trackLayers.push(map.addPolyline(seg, {
        color: segPast || segEclipse ? dim : sun,
        weight: segPast ? 1 : 2,
        opacity: segPast ? 0.6 : 0.95,
        dashArray: segPast ? "1 4" : (segEclipse ? "5 4" : null) }));
    }
  };
  for (let i = 0; i < mapTrack.length; i++) {
    const pt = mapTrack[i];
    const isPast = new Date(pt.utc).getTime() < nowMs;
    const prev = i > 0 ? mapTrack[i - 1] : null;
    const lonJump = prev ? Math.abs(pt.lon - prev.lon) : 0;
    if ((lonJump > 180 || pt.in_eclipse !== segEclipse || isPast !== segPast) && seg.length) {
      flush(); seg = [];
    }
    segEclipse = pt.in_eclipse; segPast = isPast;
    seg.push([pt.lat, pt.lon]);
  }
  flush();
}

function scGlyph(headingDeg) {
  return '<svg width="18" height="18" viewBox="0 0 24 24" style="transform:rotate('
    + (headingDeg || 0) + 'deg)"><polygon points="12,2 18,20 12,16 6,20" fill="'
    + tok("--val") + '" stroke="' + tok("--bg") + '" stroke-width="1.5"/></svg>';
}

const latStr = (lat) => Math.abs(lat).toFixed(2) + "°" + (lat >= 0 ? "N" : "S");
const lonStr = (lon) => Math.abs(lon).toFixed(2) + "°" + (lon >= 0 ? "E" : "W");

function updateSpacecraftMarker() {
  if (!scState) {
    for (const id of ["mapLat", "mapLon", "mapAlt", "mapBeta"]) $(id).innerHTML = renderNoData();
    return;
  }
  const { lat, lon } = scState;
  $("mapLat").textContent = latStr(lat);
  $("mapLon").textContent = lonStr(lon);
  $("mapAlt").textContent = num(scState.alt_km, 1) !== null ? num(scState.alt_km, 1) + " km" : "";
  $("mapBeta").textContent = num(scState.solar_beta_deg, 1) !== null ? num(scState.solar_beta_deg, 1) + "°" : "";
  if (!map) return;
  if (!scMarker) {
    scMarker = map.addMarker(lat, lon, { html: scGlyph(scState.heading_deg), size: 18 });
  } else {
    scMarker.setLatLng(lat, lon);
    scMarker.setIcon({ html: scGlyph(scState.heading_deg) });
  }
  // Sensor footprint from the CONFIGURED payload FOV (P4), not a literal.
  const fov = plannerConfig && plannerConfig.imaging && plannerConfig.imaging.fov_deg;
  if (fov && scState.alt_km) {
    const rKm = scState.alt_km * Math.tan((fov / 2) * Math.PI / 180);
    if (!scFootprint) {
      scFootprint = map.addCircle(lat, lon, rKm, {
        color: tok("--val"), weight: 0.8, opacity: 0.35,
        fillColor: tok("--val"), fillOpacity: 0.06, dashArray: "2 3" });
    } else {
      scFootprint.setLatLng(lat, lon);
    }
  }
}

/* ── Spacecraft state (header + map overlay) ──────────────────────────── */
async function loadSpacecraftState() {
  const res = await fetch("/api/spacecraft-state");
  if (!res.ok) throw new Error("HTTP " + res.status);
  scState = await res.json();
  $("scStateBadge").innerHTML = renderChip({ kind: "neutral",
    label: scState.in_eclipse ? tText("In eclipse") : tText("Sunlit"),
    title: tText("Illumination from {{src}}", { src: scState.eclipse_source || "?" }) });
  updateSpacecraftMarker();
}

/* ── Ground track fetches (map 3 h window + 24 h eclipse horizon) ─────── */
async function loadGroundTrack() {
  // Map window: 90 min of past + the rest future (classic behaviour).
  try {
    let res = await fetch("/api/ground-track?offset_minutes=-90&duration_hours=3.0&step_s=30");
    if (!res.ok) res = await fetch("/api/ground-track");
    if (res.ok) {
      mapTrack = (await res.json()).ground_track || [];
      drawGroundTrack();
    }
  } catch (e) { /* map keeps last track */ }
  // Timeline horizon: the picture is 24 h, so its eclipse arcs and the next
  // eclipse readout come from a 24 h track — real propagation, not the
  // classic page's fixed orbit-period pattern (P4).
  try {
    const res = await fetch("/api/ground-track?duration_hours=" + horizonHours() + "&step_s=120");
    if (res.ok) eclipseTrack = (await res.json()).ground_track || [];
  } catch (e) { /* keep last horizon */ }
  renderOrbitFacts();
}

const horizonHours = () => (plannerConfig && plannerConfig.horizons
  && plannerConfig.horizons.timeline_hours) || 24;

function eclipseIntervals() {
  const out = [];
  let start = null;
  for (const pt of eclipseTrack) {
    const tm = new Date(pt.utc).getTime();
    if (pt.in_eclipse && start === null) start = tm;
    if (!pt.in_eclipse && start !== null) { out.push([start, tm]); start = null; }
  }
  if (start !== null && eclipseTrack.length) {
    out.push([start, new Date(eclipseTrack[eclipseTrack.length - 1].utc).getTime()]);
  }
  return out;
}

/* ── Main poll: contacts, schedule, verdicts, budgets ─────────────────── */
async function pollAPIs() {
  let contactsOk = false, scheduleOk = false;
  try {
    const res = await fetch("/api/contacts");
    if (res.ok) {
      const data = await res.json();
      contacts = (data.contacts || []).map((c) => ({
        station: c.gs_name, aos: new Date(c.aos), los: new Date(c.los),
        maxEl: c.max_elevation_deg,
        durationMin: Math.round((c.duration_s || 0) / 60) }));
      contactsOk = true;
    }
  } catch (e) { /* keep last */ }
  try {
    const res = await fetch("/api/schedule");
    if (res.ok) {
      const data = await res.json();
      schedule = (data.schedule || []).map((s) => ({
        ...s, start: new Date(s.start_time),
        durationMin: Math.round((s.duration_s || 300) / 60),
        state_name: s.state_name || "PLANNED" }));
      scheduleOk = true;
    }
  } catch (e) { /* keep last */ }
  apiOk = contactsOk && scheduleOk;
  renderApiChip();
  // Draw the schedule at once: the four checks below can take seconds
  // (the constraint check most of all), and a just-added activity must not
  // wait for them. Their verdicts are drawn when they arrive.
  redraw();
  updateActivityList();
  await Promise.all([loadValidation(), loadConstraintCheck(),
    loadPowerBudget(), loadDataBudget()]);
  redraw();
  updateActivityList();
  loadImagingOpportunities(); loadImagingTargets(); loadPassRollups();
}

/** Redraw everything that depends on "now" (10 s) and on the last poll. */
function redraw() {
  renderFacts(); updateCountdowns(); drawTimeline(); updateContactsTable();
}

/* Schedule validation on every poll: it flags the rows and gates Upload. */
async function loadValidation() {
  try {
    const res = await fetch("/api/schedule/validate");
    if (res.ok) validation = await res.json();
  } catch (e) { /* keep last */ }
}
async function loadConstraintCheck() {
  try {
    const res = await fetch(constraintUrl());
    const data = await res.json();
    if (res.ok && !data.error) constraintCheck = data;
  } catch (e) { /* keep last */ }
}

/* Per-activity verdicts from both checks: alarm (constraint error, or a
 * time conflict) wins over caution (any other validation issue, warning). */
const ALARM_ISSUES = new Set(["conflict", "time_overlap"]);
function activityVerdicts() {
  const out = new Map();
  const add = (id, level, msg) => {
    if (id === null || id === undefined) return;
    const v = out.get(id) || { level: "caution", msgs: [] };
    if (level === "alarm") v.level = "alarm";
    v.msgs.push(msg);
    out.set(id, v);
  };
  for (const i of (validation && validation.issues) || []) {
    add(i.activity_id, ALARM_ISSUES.has(i.type) ? "alarm" : "caution", i.message || i.type);
  }
  for (const v of (constraintCheck && constraintCheck.violations) || []) {
    if (v.severity === "error") add(v.activity_id, "alarm", v.message);
    else if (v.severity === "warning") add(v.activity_id, "caution", v.message);
  }
  return out;
}

/* ── 1. The picture: next 24 h as an SVG timeline ─────────────────────── */
function el(tag, attrs, text) {
  const n = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, v);
  if (text !== undefined) n.textContent = text;
  return n;
}
function titled(node, text) { node.appendChild(el("title", {}, text)); return node; }

function socSeries() {
  const b = powerBudget;
  if (!b || b.computable === false || b.final_soc === null || b.final_soc === undefined) return null;
  const pts = [];
  if (Number.isFinite(b.initial_soc)) pts.push([simNow(), b.initial_soc]);
  for (const p of b.pass_predictions || []) {
    pts.push([new Date(p.aos).getTime(), p.soc_at_aos]);
    pts.push([new Date(p.los).getTime(), p.soc_at_los]);
  }
  return pts.filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y)).sort((a, c) => a[0] - c[0]);
}

function drawTimeline() {
  const svg = $("timeline");
  if (!svg) return;
  const W = Math.max(680, svg.parentElement.clientWidth);
  const now = simNow();
  const spanMs = horizonHours() * 3600 * 1000;
  const L = 92, R = 76, top = 22;
  const pw = W - L - R;
  const X = (tm) => L + ((tm - now) / spanMs) * pw;
  const clipX = (tm) => Math.max(L, Math.min(L + pw, X(tm)));
  const stations = groundStations.length ? groundStations.map((g) => g.name)
    : [...new Set(contacts.map((c) => c.station))];
  const verdicts = activityVerdicts();

  // Rows (top to bottom): eclipse, one lane per station, activities, SoC.
  // The picture fills the height the numbers beside it take (no dead band
  // under the plot); the spare height goes to the SoC trace.
  const LH = 22;
  let y = top + 4;
  const rows = {};
  rows.ecl = y; y += 14 + 8;
  rows.st = y; y += stations.length * LH + 8;
  rows.act = y; y += 2 * 16 + 14;
  const facts = document.querySelector("#panel-overview .facts");
  const want = facts && window.innerWidth > 1100 ? facts.offsetHeight - 60 : 0;
  const socH = Math.max(80, Math.min(200, want - y - 10));
  rows.soc = y; y += socH + 10;
  const H = y;
  svg.setAttribute("height", H);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  while (svg.lastChild && svg.lastChild.nodeName !== "desc") svg.removeChild(svg.lastChild);
  while (svg.firstChild && svg.firstChild.nodeName !== "desc") svg.removeChild(svg.firstChild);

  // Hour grid + UTC labels every 2 h (on the hour); none under the "Now" tag.
  const nowTag = clockDegraded ? tText("Now (wall clock)") : tText("Now");
  const clearOfNow = L + nowTag.length * 7.5 + 28;
  const first = Math.ceil(now / 3600000) * 3600000;
  for (let tm = first; tm <= now + spanMs; tm += 3600000) {
    const d = new Date(tm);
    const x = X(tm);
    const major = d.getUTCHours() % 2 === 0;
    svg.appendChild(el("line", { class: "grid", x1: x, x2: x, y1: top - 4, y2: H - 4,
      "stroke-opacity": major ? 1 : 0.45 }));
    if (major && x > clearOfNow && x < L + pw - 18) {
      svg.appendChild(el("text", { x, y: top - 8, "text-anchor": "middle" }, hhmm(d)));
    }
  }

  // Lane labels.
  const lane = (txt, yy) => svg.appendChild(el("text", { class: "lane", x: L - 10, y: yy, "text-anchor": "end",
    "dominant-baseline": "middle" }, txt));
  lane(tText("Eclipse"), rows.ecl + 7);
  stations.forEach((s, i) => lane(s, rows.st + i * LH + LH / 2));
  lane(tText("Activities"), rows.act + 16);
  lane(tText("SoC"), rows.soc + socH / 2);

  // Eclipse arcs from the SERVED 24 h track (P4) — none served, none drawn.
  for (const [a, b] of eclipseIntervals()) {
    if (b < now || a > now + spanMs) continue;
    const x1 = clipX(a), x2 = clipX(b);
    svg.appendChild(titled(el("rect", { class: "ecl", x: x1, y: rows.ecl, width: Math.max(1, x2 - x1), height: 14 }),
      tText("Eclipse {{a}}–{{b}} UTC", { a: hhmm(new Date(a)), b: hhmm(new Date(b)) })));
  }
  // Passes: outline = pass, filled = pass with a planned dump, accent = now.
  const dumps = new Map(((dataBudget && dataBudget.pass_downlink) || [])
    .map((p) => [p.gs_name + "|" + new Date(p.aos).getTime(), p]));
  for (const c of contacts) {
    const i = stations.indexOf(c.station);
    if (i < 0) continue;
    const a = c.aos.getTime(), b = c.los.getTime();
    if (b < now || a > now + spanMs) continue;
    const live = a <= now && b >= now;
    const dp = dumps.get(c.station + "|" + a);
    const cls = "pass" + (live ? " live" : dp && dp.dump_scheduled ? " dump" : "");
    const x1 = clipX(a), x2 = clipX(b);
    svg.appendChild(titled(el("rect", { class: cls, x: x1 + 0.5, y: rows.st + i * LH + 5,
      width: Math.max(3, x2 - x1 - 1), height: LH - 10, rx: 1 }),
      tText("{{gs}} {{a}}–{{b}} UTC, max elevation {{el}}°", { gs: c.station,
        a: fmtUTC(c.aos), b: fmtUTC(c.los), el: num(c.maxEl, 1) ?? "?" })
      + (dp && dp.dump_scheduled ? " · " + tText("dump planned") : "")));
  }
  // Activities on two sub-lanes (overlaps drop to the second); a caution or
  // alarm activity carries the triangle above its bar, not only colour.
  const laneEnd = [-Infinity, -Infinity];
  const acts = schedule.filter((a) => a.state_name !== "CANCELLED")
    .slice().sort((a, b) => a.start - b.start);
  for (const a of acts) {
    const s = a.start.getTime(), e = s + Math.max(1, a.durationMin) * 60000;
    if (e < now || s > now + spanMs) continue;
    const x1 = clipX(s), x2 = Math.max(x1 + 3, clipX(e));
    const k = x1 >= laneEnd[0] + 2 ? 0 : 1;
    laneEnd[k] = Math.max(laneEnd[k], x2);
    const v = verdicts.get(a.id);
    const st = a.state_name;
    const cls = "act" + (v ? (v.level === "alarm" ? " is-alarm" : " is-caution")
      : (st === "EXECUTING" || st === "UPLOADED") ? " is-active" : "");
    const yy = rows.act + k * 16 + 4;
    svg.appendChild(titled(el("rect", { class: cls, x: x1, y: yy, width: x2 - x1, height: 10, rx: 1 }),
      `#${a.id} ${a.name} ${hhmm(a.start)} UTC` + (v ? " · " + v.msgs.join("; ") : "")));
    if (v) {
      const cx = (x1 + x2) / 2;
      svg.appendChild(el("path", { class: v.level === "alarm" ? "flag-a" : "flag-c",
        d: `M${cx - 4} ${yy - 1} L${cx + 4} ${yy - 1} L${cx} ${yy - 8} Z` }));
    }
  }

  // Predicted SoC against its configured minimum (0-100 % scale).
  const sy = (p) => rows.soc + socH - (Math.max(0, Math.min(100, p)) / 100) * socH;
  svg.appendChild(el("line", { class: "base", x1: L, x2: L + pw, y1: sy(0), y2: sy(0) }));
  svg.appendChild(el("line", { class: "grid", x1: L, x2: L + pw, y1: sy(100), y2: sy(100) }));
  svg.appendChild(el("text", { x: L + pw + 6, y: sy(100) + 4 }, "100 %"));
  svg.appendChild(el("text", { x: L + pw + 6, y: sy(0) }, "0 %"));
  const minSoc = MIN_SOC();
  if (minSoc !== null) {
    svg.appendChild(el("line", { class: "lim-y", x1: L, x2: L + pw, y1: sy(minSoc + 10), y2: sy(minSoc + 10) }));
    svg.appendChild(el("line", { class: "lim-r", x1: L, x2: L + pw, y1: sy(minSoc), y2: sy(minSoc) }));
    svg.appendChild(el("text", { class: "lim-t", x: L + pw + 6, y: sy(minSoc) + 4 },
      tText("min {{v}} %", { v: minSoc })));
  }
  const pts = socSeries();
  if (pts && pts.length > 1) {
    const vis = pts.filter(([x]) => x >= now - 1 && x <= now + spanMs);
    if (vis.length > 1) {
      svg.appendChild(el("path", { class: "soc",
        d: vis.map(([x, p], i) => (i ? "L" : "M") + X(x).toFixed(1) + " " + sy(p).toFixed(1)).join(" ") }));
      const [lx, lp] = vis[vis.length - 1];
      svg.appendChild(el("circle", { class: "soc-dot", cx: X(lx), cy: sy(lp), r: 2.5 }));
      const low = vis.reduce((m, q) => (q[1] < m[1] ? q : m), vis[0]);
      svg.appendChild(titled(el("circle", { class: "soc-dot", cx: X(low[0]), cy: sy(low[1]), r: 2 }),
        tText("Lowest predicted SoC {{v}} % at {{t}} UTC", { v: low[1].toFixed(1), t: hhmm(new Date(low[0])) })));
    }
  } else {
    svg.appendChild(el("text", { class: "empty", x: L + 8, y: rows.soc + socH / 2 + 4 },
      powerBudget && powerBudget.computable === false
        ? tText("SoC prediction cannot be computed: see the power budget")
        : tText("No SoC prediction yet")));
  }

  // Now.
  svg.appendChild(el("line", { class: "now", x1: L, x2: L, y1: top - 4, y2: H - 4 }));
  svg.appendChild(el("text", { class: "now-t", x: L + 4, y: top - 8 }, nowTag));

  if (!stations.length || !contacts.length) {
    svg.appendChild(el("text", { class: "empty", x: L + pw / 2, y: rows.st + 12, "text-anchor": "middle" },
      groundStationsError
        ? tText("Ground-station list unavailable — check {{route}}", { route: "/api/ground-stations" })
        : (!stations.length
          ? tText("No ground stations configured — check {{file}}", { file: "orbit.yaml" })
          : tText("No contact windows — check configuration"))));
  }
  $("tl-desc").textContent = tText(
    "Timeline of the next {{h}} hours: {{n}} passes, {{e}} eclipses, {{a}} activities and the predicted battery state of charge.",
    { h: horizonHours(), n: contacts.filter((c) => c.los.getTime() > now).length,
      e: eclipseIntervals().filter(([, b]) => b > now).length, a: acts.length });
  $("ovMeta").textContent = tText("from {{t}} UTC", { t: fmtUTC(new Date(now), { seconds: false }) });
}

/* ── The numbers beside the picture ───────────────────────────────────── */
function updateCountdowns() {
  const now = simNow();
  const live = contacts.find((c) => c.aos.getTime() <= now && c.los.getTime() > now);
  const next = contacts.filter((c) => c.aos.getTime() > now).sort((a, b) => a.aos - b.aos)[0];
  const k = $("factAos").querySelector(".k");
  if (live) {
    k.textContent = tText("In contact: loss of signal in");
    $("nextAosStation").textContent = live.station;
    $("nextAos").textContent = countdown(live.los.getTime() - now);
    $("nextAosSub").textContent = tText("LOS {{t}} UTC · max el {{el}}°",
      { t: fmtUTC(live.los), el: num(live.maxEl, 0) ?? "?" });
  } else if (next) {
    k.textContent = tText("Next contact");
    $("nextAosStation").textContent = next.station;
    $("nextAos").textContent = countdown(next.aos.getTime() - now);
    $("nextAosSub").textContent = tText("AOS {{t}} UTC · {{d}} · max el {{el}}°",
      { t: fmtUTC(next.aos), d: minPart(next.durationMin), el: num(next.maxEl, 0) ?? "?" });
  } else {
    k.textContent = tText("Next contact");
    $("nextAosStation").textContent = "";
    $("nextAos").innerHTML = renderNoData({ label: tText("none in the horizon") });
    $("nextAosSub").textContent = "";
  }
  const iv = eclipseIntervals();
  const inEcl = iv.find(([a, b]) => a <= now && b > now);
  const ecl = iv.find(([a]) => a > now);
  const ek = $("factEclipse").querySelector(".k");
  if (inEcl) {
    ek.textContent = tText("In eclipse: sunlight in");
    $("nextEclipse").textContent = countdown(inEcl[1] - now);
    $("nextEclipseSub").textContent = tText("exit {{t}} UTC", { t: fmtUTC(new Date(inEcl[1])) });
  } else if (ecl) {
    ek.textContent = tText("Next eclipse");
    $("nextEclipse").textContent = countdown(ecl[0] - now);
    $("nextEclipseSub").textContent = tText("{{a}}–{{b}} UTC ({{d}})", {
      a: fmtUTC(new Date(ecl[0]), { seconds: false }), b: fmtUTC(new Date(ecl[1]), { seconds: false }),
      d: minPart(Math.round((ecl[1] - ecl[0]) / 60000)) });
  } else {
    ek.textContent = tText("Next eclipse");
    $("nextEclipse").innerHTML = eclipseTrack.length
      ? renderNoData({ label: tText("none in the horizon") }) : renderNoData();
    $("nextEclipseSub").textContent = "";
  }
}

function socLimits() {
  const m = MIN_SOC();
  return m === null ? { lo: 0, hi: 100 } : { red_low: m, yellow_low: m + 10, lo: 0, hi: 100 };
}

function renderFacts() {
  // SoC at the end of the horizon, against the minimum.
  const b = powerBudget;
  let soc;
  if (!b) soc = renderNoData();
  else if (b.computable === false || b.final_soc === null || b.final_soc === undefined) {
    soc = renderNoData({ label: tText("cannot be computed") });
  } else {
    soc = renderGauge(b.final_soc, socLimits(), { units: "%", digits: 1 })
      + `<div class="sub">${esc(MIN_SOC() !== null
        ? tText("minimum {{m}} % · lowest {{low}} %", { m: MIN_SOC(), low: lowestSoc() })
        : tText("lowest {{low}} %", { low: lowestSoc() }))}</div>`
      + (b.soc_saturated ? `<div class="chips">${renderChip({ kind: "warn",
        label: tText("Saturated: a limit, not a prediction") })}</div>` : "");
  }
  $("factSocBody").innerHTML = soc;

  const d = dataBudget;
  let dat;
  if (!d || d.utilization_percent === undefined) dat = renderNoData();
  else {
    const warnAt = warnUtil();
    const peak = d.peak_utilization_percent ?? d.utilization_percent;
    dat = renderGauge(peak, { yellow_high: warnAt, red_high: 100, lo: 0, hi: 100 }, { units: "%", digits: 1 })
      + `<div class="sub">${esc(tText("{{mb}} of {{cap}} MB", {
        mb: num(d.peak_onboard_mb, 0) ?? "?", cap: num(d.storage_capacity_mb, 0) ?? "?" }))}</div>`
      + `<div class="chips">${d.plan_closes === false
        ? renderChip({ kind: "alarm", label: tText("Plan does not close") })
        : renderChip({ kind: "neutral", label: tText("Plan closes") })}</div>`;
  }
  $("factDataBody").innerHTML = dat;

  const chips = [];
  if (validation) {
    const n = (validation.issues || []).length;
    chips.push(validation.valid
      ? renderChip({ kind: "ok", label: tText("Schedule valid") })
      : renderChip({ kind: "warn", label: tText("{{n}} schedule issue(s)", { n }) }));
  }
  if (constraintCheck) {
    const e = constraintCheck.error_count || 0, w = constraintCheck.warning_count || 0;
    if (e) chips.push(renderChip({ kind: "alarm", label: tText("{{n}} constraint error(s)", { n: e }) }));
    if (w) chips.push(renderChip({ kind: "warn", label: tText("{{n}} constraint warning(s)", { n: w }) }));
    if (!e && !w) chips.push(renderChip({ kind: "ok", label: tText("Constraints met") }));
  }
  $("factPlanBody").innerHTML = chips.join("") || renderNoData();
}

function lowestSoc() {
  const pts = socSeries();
  if (!pts || !pts.length) return "?";
  return Math.min(...pts.map((p) => p[1])).toFixed(1);
}
const warnUtil = () => (plannerConfig && plannerConfig.budget
  && plannerConfig.budget.warn_utilization_percent) ?? 90;

/* ── Contacts table ───────────────────────────────────────────────────── */
function updateContactsTable() {
  const now = simNow();
  const upcoming = contacts.filter((c) => c.los.getTime() > now)
    .sort((a, b) => a.aos - b.aos).slice(0, 5);
  $("contactMeta").textContent = tText("{{n}} in the next {{h}} h",
    { n: contacts.filter((c) => c.los.getTime() > now).length, h: horizonHours() });
  if (!upcoming.length) {
    $("contactsBody").innerHTML = `<tr><td colspan="6">${renderNoData({ label: tText("no contact windows") })}</td></tr>`;
    return;
  }
  $("contactsBody").innerHTML = upcoming.map((c) => {
    const active = c.aos.getTime() <= now && c.los.getTime() >= now;
    return "<tr" + (active ? " class=\"is-active\"" : "") + "><td>" + esc(c.station) + "</td><td class=\"n\">"
      + fmtUTC(c.aos) + "</td><td class=\"n\">" + fmtUTC(c.los) + "</td><td class=\"n\">"
      + esc(minPart(c.durationMin)) + "</td><td class=\"n\">"
      + (typeof c.maxEl === "number" ? c.maxEl.toFixed(1) : esc(String(c.maxEl))) + "°</td><td>"
      + (active ? renderChip({ kind: "active", label: tText("In progress") })
        : "<span class=\"ds-id\">" + esc(tText("in {{t}}", { t: countdown(c.aos.getTime() - now) })) + "</span>")
      + "</td></tr>";
  }).join("");
}

/* ── Activity schedule list (per-row Edit + two-step Delete) ──────────── */
const STATE_CHIP = {
  PLANNED: ["neutral", () => tText("Planned")], UPLOADED: ["cmd", () => tText("Uploaded")],
  EXECUTING: ["active", () => tText("Executing")], COMPLETED: ["ok", () => tText("Completed")],
  FAILED: ["alarm", () => tText("Failed")], CANCELLED: ["off", () => tText("Cancelled")],
};
function stateChip(s) {
  const e = STATE_CHIP[s];
  return renderChip({ kind: e ? e[0] : "neutral", label: e ? e[1]() : s });
}
function actDescription(name) {
  const at = activityTypes.find((a) => a.name === name);
  return at && at.description ? tdb("activity:" + name + ":description", at.description) : "";
}

function updateActivityList() {
  const list = $("activityList");
  // Never rebuild under a pending two-step: it would silently disarm it.
  if (list.querySelector(".is-armed")) return;
  const verdicts = activityVerdicts();
  const n = schedule.length;
  $("schedMeta").textContent = n ? tText("{{n}} activities", { n }) : "";
  if (!n) {
    list.innerHTML = "<div class=\"act-empty\">"
      + t("No activities planned. Add one, or load a standard activity set above.") + "</div>";
  } else {
    list.innerHTML = schedule.slice().sort((a, b) => a.start - b.start).map((a) => {
      const v = verdicts.get(a.id);
      const lvl = v ? (v.level === "alarm" ? "is-alarm" : "is-caution") : "";
      const desc = actDescription(a.name);
      const hasId = a.id !== undefined && a.id !== null;
      return "<div class=\"act-row " + lvl + "\" data-id=\"" + esc(a.id) + "\">"
        + "<div class=\"when\">" + hhmm(a.start) + "</div>"
        + "<div><div class=\"nm\"><span class=\"ds-mono\">" + esc(a.name) + "</span>" + stateChip(a.state_name)
        + "</div><div class=\"meta\" title=\"" + esc(desc) + "\">#" + esc(a.id) + " · " + esc(minPart(a.durationMin))
        + " · " + esc(a.station || tText("no station")) + " · " + esc(prioText(a.priority || "medium")) + "</div></div>"
        + "<div class=\"ops\">"
        + (hasId
          ? "<button type=\"button\" class=\"ds-btn ghost sm\" data-act=\"edit\" data-id=\"" + esc(a.id)
            + "\" aria-label=\"" + esc(tText("Edit activity #{{id}}", { id: a.id })) + "\">" + t("Edit") + "</button>"
            + "<button type=\"button\" class=\"ds-btn ghost sm\" data-act=\"delete\" data-id=\"" + esc(a.id)
            + "\" aria-label=\"" + esc(tText("Delete activity #{{id}}", { id: a.id })) + "\">" + t("Delete") + "</button>"
          : "")
        + "</div>"
        + (v ? v.msgs.slice(0, 2).map((m) => "<div class=\"why " + lvl + "\">"
          + glyph(v.level === "alarm" ? "alarm-up" : "warn-up") + "<span>" + esc(m) + "</span></div>").join("") : "")
        + "</div>";
    }).join("");
    for (const btn of list.querySelectorAll("[data-act=\"delete\"]")) {
      armButton(btn, { seconds: 5, onExecute: () => deleteActivity(Number(btn.dataset.id)) });
    }
  }
  updateScheduleControls();
}

/** Enabled / disabled-with-reason for every schedule control (brief §1.3). */
function updateScheduleControls() {
  const empty = !schedule.length;
  const planned = schedule.filter((a) => a.state_name === "PLANNED" || !a.state_name)
    .sort((a, b) => a.start - b.start);
  const btnClear = $("btnClearSchedule"), btnVal = $("btnValidate"), btnUp = $("btnUpload");
  if (empty) setDisabled(btnClear, tText("The schedule is already empty"));
  else setEnabled(btnClear);
  if (empty) setDisabled(btnVal, tText("Nothing to validate: the schedule is empty"));
  else setEnabled(btnVal);
  if ($("templateSelect").value) setEnabled($("btnLoadTemplate"));
  else setDisabled($("btnLoadTemplate"), tText("Choose a standard activity set first"));

  const verdicts = activityVerdicts();
  const next = planned[0];
  const nextBad = next && verdicts.get(next.id) && verdicts.get(next.id).level === "alarm";
  const issues = validation && !validation.valid ? (validation.issues || []).length : 0;
  let reason = "";
  if (empty) reason = tText("Nothing to upload: the schedule is empty");
  else if (!next) reason = tText("No planned activity left to upload");
  else if (next.id === undefined || next.id === null) reason = tText("The next activity has no ID");
  else if (nextBad) reason = tText("Resolve the conflict on activity #{{id}} first", { id: next.id });
  else if (apiOk === false) reason = tText("Planner API unreachable");
  if (reason) setDisabled(btnUp, reason); else setEnabled(btnUp);
  $("uploadWhat").innerHTML = next
    ? t("Next to upload: {{-name}} at {{t}} UTC", { name: "<b>" + esc(next.name) + "</b>", t: hhmm(next.start) })
      + (issues ? " · <span style=\"color:var(--warn)\">" + esc(tText("{{n}} schedule issue(s)", { n: issues })) + "</span>" : "")
    : esc(empty ? tText("Nothing to upload yet.") : tText("Every activity has been uploaded."));
  const step = $("stepMode");
  if (uploadMode === "immediate") { setEnabled(step); step.closest("label").classList.remove("is-disabled"); }
  else {
    setDisabled(step, tText("Step-by-step applies to MCS procedures only"));
    step.closest("label").classList.add("is-disabled");
  }
}

async function deleteActivity(id) {
  try {
    const res = await fetch("/api/schedule/" + id, { method: "DELETE" });
    notify(res.ok ? "ok" : "alarm", res.ok ? tText("Activity #{{id}} deleted", { id })
      : tText("Could not delete activity #{{id}} (HTTP {{s}})", { id, s: res.status }));
  } catch (e) { notify("alarm", tText("Could not delete activity #{{id}}: {{e}}", { id, e: String(e) })); }
  mainPoller.kick();
}

/* ── Toast (replaces native alert(): says what happened, in place) ────── */
function notify(kind, text) {
  const host = $("toast");
  host.innerHTML = renderBanner(kind === "ok" ? "ok" : kind === "alarm" ? "alarm" : kind === "caution" ? "caution" : "info", text);
  host.classList.add("show");
  clearTimeout(notify._t);
  notify._t = setTimeout(() => host.classList.remove("show"), kind === "alarm" ? 9000 : 5000);
}

/* ── Add / Edit dialog — classic page's proven UTC handling, verbatim ─── */
function dateToUtcInputValue(d) {
  return d.getUTCFullYear() + "-" + pad2(d.getUTCMonth() + 1) + "-" + pad2(d.getUTCDate())
    + "T" + pad2(d.getUTCHours()) + ":" + pad2(d.getUTCMinutes());
}
function utcInputValueToDate(v) {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(v || "");
  if (!m) return null;
  return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +(m[6] || 0)));
}
function updateStartTimeHint() {
  const hintEl = $("actStartTimeHint");
  const d = utcInputValueToDate($("actStartTime").value);
  if (!d || isNaN(d.getTime())) { hintEl.textContent = tText("Enter a UTC start time."); return; }
  let zone = "";
  try { zone = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) { /* ok */ }
  const offMin = -d.getTimezoneOffset();
  const sign = offMin < 0 ? "-" : "+";
  const abs = Math.abs(offMin);
  const offset = "UTC" + sign + pad2(Math.floor(abs / 60)) + ":" + pad2(abs % 60);
  hintEl.textContent = tText("{{utc}} UTC = {{local}} local ({{zone}})", {
    utc: d.toISOString().slice(0, 16).replace("T", " "),
    local: d.toLocaleString(), zone: (zone ? zone + ", " : "") + offset });
}

let editingId = null;   // null = add mode; number = PUT /api/schedule/{id}

function modalTitle() {
  return editingId !== null ? tText("Edit activity #{{id}}", { id: editingId }) : tText("Add activity");
}
function updateSubmitState() {
  const btn = $("btnModalSubmit");
  if (editingId === null && !$("actType").value) setDisabled(btn, tText("Select an activity type first"));
  else if (!utcInputValueToDate($("actStartTime").value)) setDisabled(btn, tText("Enter a UTC start time."));
  else setEnabled(btn);
}

function openModal(activity) {
  editingId = activity ? activity.id : null;
  $("modalTitle").textContent = modalTitle();
  $("editNote").hidden = !activity;
  for (const id of ["actType", "actStation"]) {
    if (activity) setDisabled($(id), tText("Type and station are fixed at creation"));
    else setEnabled($(id));
  }
  if (activity) {
    // The catalogue name may not be in the select; show it as-is.
    const sel = $("actType");
    if (![...sel.options].some((o) => o.value === activity.name)) {
      const opt = document.createElement("option");
      opt.value = activity.name; opt.textContent = activity.name;
      sel.appendChild(opt);
    }
    sel.value = activity.name;
    $("actStartTime").value = dateToUtcInputValue(activity.start);
    $("actDuration").value = activity.durationMin;
    $("actPriority").value = activity.priority || "medium";
    $("actStation").value = activity.station || "";
  } else {
    // Prefill with the PLANNER's current time (sim time in sim mode).
    $("actStartTime").value = dateToUtcInputValue(simNowDate());
  }
  renderActTypeInfo();
  updateStartTimeHint();
  updateSubmitState();
  $("modalOverlay").classList.add("active");
  (activity ? $("actStartTime") : $("actType")).focus();
}
function closeModal() {
  $("modalOverlay").classList.remove("active"); editingId = null;
  $("btnAddActivity").focus();
}

async function submitActivity() {
  const startDate = utcInputValueToDate($("actStartTime").value);
  if (!startDate || isNaN(startDate.getTime())) {
    notify("alarm", tText("Could not read the start time — expected UTC YYYY-MM-DD HH:MM.")); return;
  }
  const duration = parseInt($("actDuration").value, 10) || 15;
  const priority = $("actPriority").value || "medium";
  try {
    let res;
    if (editingId !== null) {
      res = await fetch("/api/schedule/" + editingId, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_time: startDate.toISOString(),
          duration_s: duration * 60, priority }) });
    } else {
      const name = $("actType").value;
      if (!name) return;
      res = await fetch("/api/schedule", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name, start_time: startDate.toISOString(),
          duration_s: duration * 60, priority,
          station: $("actStation").value || null }) });
    }
    if (res.ok) {
      notify("ok", editingId !== null ? tText("Activity #{{id}} saved", { id: editingId }) : tText("Activity added"));
      closeModal(); mainPoller.kick();
    } else {
      const err = await res.json().catch(() => ({}));
      notify("alarm", tText("Could not save activity: {{reason}}", { reason: err.error || ("HTTP " + res.status) }));
    }
  } catch (e) {
    notify("alarm", tText("Could not save activity — planner API unreachable: {{e}}", { e: String(e) }));
  }
}

/* ── Activity types / templates / stations ────────────────────────────── */
async function loadActivityTypes() {
  try {
    const res = await fetch("/api/activity-types");
    if (!res.ok) return;
    activityTypes = (await res.json()).activity_types || [];
    if (activityTypes.length) {
      const sel = $("actType");
      const keep = sel.value;
      sel.innerHTML = "<option value=\"\">" + t("Select activity type…") + "</option>";
      for (const at of activityTypes) {
        const opt = document.createElement("option");
        opt.value = at.name;
        opt.textContent = at.name;    // identifier (operator vocabulary)
        sel.appendChild(opt);
      }
      if (keep && [...sel.options].some((o) => o.value === keep)) sel.value = keep;
    }
  } catch (e) { /* keep static options */ }
}

function renderActTypeInfo() {
  const name = $("actType").value;
  const infoEl = $("actTypeInfo");
  const at = activityTypes.find((a) => a.name === name);
  if (!at) { infoEl.style.display = "none"; return null; }
  infoEl.style.display = "block";
  const dur = Math.round((at.duration_s || 0) / 60);
  const pre = (at.pre_conditions || []).map((p, i) =>
    tdb("activity:" + at.name + ":pre_conditions." + i, p));
  infoEl.innerHTML = esc(tdb("activity:" + at.name + ":description", at.description || ""))
    + "<br>" + t("Duration: {{dur}} min | Power: {{power}} W | Procedure: {{proc}}", {
      dur, power: at.power_w || 0, proc: at.procedure_ref || tText("N/A") })
    + (pre.length
      ? "<br>" + t("Pre-conditions: {{list}}", { list: pre.join(", ") }) : "");
  return at;
}

function onActivityTypeChange() {
  const at = renderActTypeInfo();
  updateSubmitState();
  if (!at) return;
  $("actDuration").value = Math.round((at.duration_s || 0) / 60);
  $("actPriority").value = at.priority || "medium";
}

async function loadPlanTemplates() {
  try {
    const res = await fetch("/api/schedule/templates");
    if (!res.ok) return;
    const data = await res.json();
    planTemplates = data.templates || [];
    const sel = $("templateSelect");
    const keep = sel.value;
    sel.innerHTML = "<option value=\"\">" + t("Standard activities…") + "</option>";
    for (const tp of planTemplates) {
      const opt = document.createElement("option");
      opt.value = tp.id;
      opt.textContent = tdb("plan:" + tp.id + ":name", tp.name) + " (" + tp.activity_count + ")";
      opt.title = tp.description ? tdb("plan:" + tp.id + ":description", tp.description) : "";
      if (keep ? tp.id === keep : tp.id === data.default_template) opt.selected = true;
      sel.appendChild(opt);
    }
    updateScheduleControls();
  } catch (e) { /* dropdown stays empty */ }
}

async function loadStandardActivities() {
  const id = $("templateSelect").value;
  if (!id) return;
  try {
    const res = await fetch("/api/schedule/load-template", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ template: id }) });
    const data = await res.json();
    if (!res.ok) { notify("alarm", tText("Could not load \"{{id}}\": {{reason}}", { id, reason: data.error || res.status })); return; }
    let msg = tText("Loaded {{n}} activities from \"{{template}}\" at {{t0}}",
      { n: data.added, template: data.template, t0: fmtUTC(data.t0) });
    if (data.warnings && data.warnings.length) msg += "\n" + data.warnings.join("\n");
    notify(data.warnings && data.warnings.length ? "caution" : "ok", msg);
    mainPoller.kick();
  } catch (e) { notify("alarm", tText("Could not load standard activities: {{e}}", { e: String(e) })); }
}

async function clearSchedule() {
  try {
    const res = await fetch("/api/schedule", { method: "DELETE" });
    const data = await res.json();
    if (data.removed !== undefined) {
      notify("ok", tText("Schedule cleared ({{n}} removed)", { n: data.removed }));
      mainPoller.kick();
    }
  } catch (e) { notify("alarm", tText("Could not clear the schedule: {{e}}", { e: String(e) })); }
}

async function loadGroundStations() {
  try {
    const res = await fetch("/api/ground-stations");
    if (!res.ok) throw new Error("HTTP " + res.status);
    groundStations = (await res.json()).ground_stations || [];
    groundStationsError = groundStations.length === 0;
  } catch (e) {
    groundStations = []; groundStationsError = true;
  }
  const sel = $("actStation");
  while (sel.options.length > 1) sel.remove(1);
  for (const gs of groundStations) {
    const opt = document.createElement("option");
    opt.value = gs.name; opt.textContent = gs.name;
    sel.appendChild(opt);
  }
  updateGroundStationMarkers();
}

/* ── Validate / upload ────────────────────────────────────────────────── */
async function validateSchedule() {
  const host = $("scheduleValidation");
  try {
    const res = await fetch("/api/schedule/validate");
    const data = await res.json();
    validation = data;
    if (data.valid) {
      host.innerHTML = renderBanner("ok", tText("Schedule valid ({{n}} activities, no conflicts)", { n: data.activity_count }));
    } else {
      host.innerHTML = data.issues.map((i) => renderBanner(ALARM_ISSUES.has(i.type) ? "alarm" : "caution",
        tText("{{type}}: {{message}} (activity #{{id}})", { type: i.type, message: i.message, id: i.activity_id }))).join("");
    }
    clearTimeout(validateSchedule._t);
    validateSchedule._t = setTimeout(() => { host.innerHTML = ""; }, 10000);
    updateActivityList(); renderFacts(); drawTimeline();
  } catch (e) {
    host.innerHTML = renderBanner("alarm", tText("Validation failed: {{e}}", { e: String(e) }));
  }
}

async function uploadToMCS() {
  const planned = schedule.filter((a) => a.state_name === "PLANNED" || !a.state_name)
    .sort((a, b) => a.start - b.start);
  const act = planned[0];
  if (!act || !act.id) return;
  const useS11 = uploadMode === "s11";
  const stepMode = !useS11 && $("stepMode").checked;
  try {
    const res = await fetch("/api/schedule/upload", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        activity_id: act.id, mode: useS11 ? "s11" : "immediate",
        step_by_step: stepMode }) });
    const data = await res.json();
    if (data.error) { notify("alarm", tText("Upload failed: {{e}}", { e: data.error })); return; }
    if (useS11) {
      const nCmd = data.count !== undefined ? data.count : "?";
      notify("ok", tText("Activity \"{{name}}\" scheduled on board: {{n}} time-tagged command(s) at {{t}}",
        { name: act.name, n: nCmd, t: fmtUTC(act.start_time) })
        + (data.skipped && data.skipped.length
          ? "\n" + tText("({{n}} telemetry-check step(s) skipped — ground-only)",
            { n: data.skipped.length }) : ""));
    } else {
      notify("ok", tText(
        "Activity \"{{name}}\" uploaded to MCS. Switch to the MCS Procedures page to execute.",
        { name: act.name }));
    }
    mainPoller.kick();
  } catch (e) { notify("alarm", tText("Upload failed: {{e}}", { e: String(e) })); }
}

/* ── Constraint validation (P5: explicit SoC, per-domain breakdown) ───── */
function constraintUrl() {
  const v = $("socInput").value.trim();
  // Blank = server default: the request carries NO battery_soc parameter.
  if (v === "") return "/api/constraints/validate";
  return "/api/constraints/validate?battery_soc=" + encodeURIComponent(v);
}

function socInputError() {
  const v = $("socInput").value.trim();
  if (v === "") return "";
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 && n <= 100 ? "" : tText("Enter a value between 0 and 100");
}

function vrow(kind, text) {
  const g = kind === "alarm" ? "alarm-up" : kind === "caution" ? "warn-up" : "ack";
  return `<div class="vrow is-${kind}">${glyph(g)}<span>${esc(text)}</span></div>`;
}

async function validateConstraints() {
  const elOut = $("constraintsResult");
  const bad = socInputError();
  $("socInput").setAttribute("aria-invalid", bad ? "true" : "false");
  if (bad) { elOut.innerHTML = vrow("alarm", bad); return; }
  elOut.innerHTML = `<span class="muted">${t("Checking…")}</span>`;
  try {
    const res = await fetch(constraintUrl());
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || ("HTTP " + res.status));
    constraintCheck = data;
    const head = data.valid
      ? vrow("ok", tText("No constraint violations"))
      : vrow((data.error_count || 0) > 0 ? "alarm" : "caution", tText("{{e}} error(s), {{w}} warning(s)",
        { e: data.error_count ?? "?", w: data.warning_count ?? "?" }));
    const rows = (data.violations || []).slice(0, 12).map((v) =>
      vrow(v.severity === "error" ? "alarm" : "caution",
        (v.activity_name ? v.activity_name : tText("System")) + ": " + (v.message || "")));
    elOut.innerHTML = head + rows.join("");
    renderFacts(); updateActivityList(); drawTimeline();
  } catch (e) {
    elOut.innerHTML = vrow("alarm", tText("Constraint validation failed: {{e}}", { e: String(e) }));
  }
}

function renderDomainResult(data) {
  const violations = data.violations || data.issues || [];
  const rows = violations.slice(0, 10).map((v) =>
    vrow(v.severity === "error" ? "alarm" : "caution",
      (v.activity_name || v.type ? (v.activity_name || v.type) + ": " : "") + (v.message || JSON.stringify(v))));
  const scalars = Object.entries(data)
    .filter(([k, v]) => (typeof v === "number" || typeof v === "string" || typeof v === "boolean")
      && k !== "error")
    .map(([k, v]) => "<span>" + esc(k) + "</span><span>" + esc(String(v)) + "</span>").join("");
  return (rows.join("") || vrow("ok", tText("No violations reported.")))
    + (scalars ? "<div class=\"kv\">" + scalars + "</div>" : "");
}

async function loadDomainConstraint(details) {
  const domain = details.dataset.domain;
  const bd = details.querySelector(".bd");
  bd.textContent = tText("Checking…");
  try {
    const res = await fetch("/api/constraints/" + domain);
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || ("HTTP " + res.status));
    bd.innerHTML = renderDomainResult(data);
  } catch (e) {
    bd.innerHTML = vrow("alarm", tText("Check failed: {{e}}", { e: String(e) }));
  }
}

/* ── Power budget ─────────────────────────────────────────────────────── */
async function loadPowerBudget() {
  try {
    const res = await fetch("/api/budget/power");
    if (!res.ok) return;
    powerBudget = await res.json();
    renderPowerBudget(powerBudget);
  } catch (e) { /* keep last render */ }
}

function renderPowerBudget(b) {
  const panel = $("powerBudgetPanel");
  const warnings = b.warnings || [];
  // "Cannot compute" is a RESULT, not a zero — render it as a designed
  // state, never a confident 0 % / 100 % (server contract, plan §2.2).
  if (b.computable === false || b.final_soc === null || b.final_soc === undefined) {
    const reason = b.reason || warnings[0]
      || tText("the planner returned no state-of-charge prediction");
    panel.innerHTML = "<div class=\"nocompute\"><b>" + glyph("warn-up") + t("Power budget cannot be computed")
      + "</b><span>" + esc(reason) + "</span></div>";
    $("powerMeta").textContent = "";
    $("powerPassBody").innerHTML = "";
    $("powerPassCount").textContent = "";
    return;
  }
  const minSoc = MIN_SOC();
  $("powerMeta").textContent = b.window_end_utc
    ? tText("to {{t}} UTC", { t: fmtUTC(b.window_end_utc, { seconds: false }) }) : "";
  let html = "<div class=\"bgrid\">"
    + renderGauge(b.final_soc, socLimits(), { label: tText("Final SoC"), units: "%", digits: 1 })
    + "<div class=\"kv\"><span>" + t("Initial SoC") + "</span><span>" + esc(num(b.initial_soc, 1) ?? "?") + " %</span>"
    + "<span>" + t("Lowest predicted") + "</span><span>" + esc(lowestSoc()) + " %</span>"
    + "<span>" + t("Minimum allowed") + "</span><span>" + (minSoc !== null ? esc(minSoc) + " %" : renderNoData()) + "</span></div>"
    + "<div class=\"kv\"><span>" + t("Charge") + "</span><span>" + esc(b.total_charge_wh ?? "?") + " Wh</span>"
    + "<span>" + t("Drain") + "</span><span>" + esc(b.total_drain_wh ?? "?") + " Wh</span>"
    + "<span>" + t("Battery capacity") + "</span><span>" + esc(b.battery_capacity_wh ?? "?") + " Wh</span></div>"
    + "</div>";
  const notes = [];
  if (b.soc_saturated) {
    notes.push(vrow("caution", tText("SoC saturated against a battery rail ({{lo}} at 0 %, {{hi}} at 100 %) — the final figure is a limit, not a prediction.",
      { lo: b.soc_floor_hits || 0, hi: b.soc_ceiling_hits || 0 })));
  }
  for (const w of warnings.slice(0, 3)) notes.push(vrow("caution", String(w)));
  if (notes.length) html += "<div class=\"notes\">" + notes.join("") + "</div>";
  panel.innerHTML = html;

  const passes = b.pass_predictions || [];
  $("powerPassCount").textContent = passes.length ? tText("{{n}} passes", { n: passes.length }) : "";
  const cls = (soc) => minSoc === null ? "" : soc < minSoc ? "is-alarm" : soc < minSoc + 10 ? "is-caution" : "";
  $("powerPassBody").innerHTML = passes.length
    ? "<table class=\"ds-table dense\"><thead><tr><th>" + t("Station") + "</th><th class=\"n\">AOS</th>"
      + "<th class=\"n\">" + t("SoC at AOS") + "</th><th class=\"n\">" + t("SoC at LOS") + "</th></tr></thead><tbody>"
      + passes.slice(0, 12).map((p) => "<tr><td>" + esc(p.gs_name) + "</td><td class=\"n\">"
        + fmtUTC(p.aos, { seconds: false }) + "</td><td class=\"n\">" + p.soc_at_aos.toFixed(1)
        + " %</td><td class=\"n\"><span class=\"ds-value " + cls(p.soc_at_los) + "\" style=\"font-size:inherit\">"
        + (cls(p.soc_at_los) ? glyph(cls(p.soc_at_los) === "is-alarm" ? "alarm-down" : "warn-down") : "")
        + p.soc_at_los.toFixed(1) + " %</span></td></tr>").join("")
      + "</tbody></table>"
    : renderNoData();
}

/* ── Data budget + fit verdicts (G3 planner half) ─────────────────────── */
/* Joins the budget tracker's per-pass achievable capacity (served on
 * /api/budget/data pass_downlink) with the schedule's dump activities:
 * backlog to move vs what the pass can carry. Computed entirely from the
 * planner's own budget machinery — the MCS is never called.
 *
 * backlog at time T = onboard now
 *                   + generation planned before T (non-dump activities)
 *                   - downlink the tracker already credits to passes that
 *                     END before T (planned_dump_mb), clamped at 0.
 * fit ratio = achievable / backlog (the planner-side analogue of the MCS
 * derived ttc.pass_fit_ratio). >= 1 fits; < 1 will not fit. */
function computeFitVerdicts(d) {
  if (!d || !Array.isArray(d.pass_downlink)) return null;
  const now = simNow();
  const passes = d.pass_downlink.map((p) => ({
    ...p,
    aosMs: new Date(p.aos).getTime(),
    losMs: new Date(p.los).getTime() }));
  const acts = schedule.filter((a) => {
    const st = a.state_name || "PLANNED";
    return st !== "CANCELLED" && st !== "FAILED";
  });
  const isDump = (a) => /dump|downlink/i.test(a.name || "");
  const genBefore = (tMs) => acts
    .filter((a) => !isDump(a) && a.start.getTime() < tMs)
    .reduce((s, a) => s + (Number(a.data_volume_mb) || 0), 0);
  const dumpedBefore = (tMs) => passes
    .filter((p) => p.dump_scheduled && p.losMs <= tMs)
    .reduce((s, p) => s + (Number(p.planned_dump_mb) || 0), 0);
  const backlogAt = (tMs) => Math.max(
    0, (Number(d.onboard_data_mb) || 0) + genBefore(tMs) - dumpedBefore(tMs));

  const perPass = new Map();
  for (const p of passes) {
    if (!p.dump_scheduled || p.losMs < now) continue;
    const backlogMb = backlogAt(p.aosMs);
    const capacityMb = Number(p.capacity_mb) || 0;
    perPass.set(p.pass_id, {
      backlogMb, capacityMb,
      ratio: backlogMb > 0 ? capacityMb / backlogMb : null,
      fits: backlogMb <= capacityMb + 1e-6 });
  }

  const dumps = [];
  for (const a of acts) {
    if (!isDump(a)) continue;
    const startMs = a.start.getTime();
    const endMs = startMs + (a.durationMin || 0) * 60000;
    if (endMs < now) continue;
    const over = passes.filter((p) => p.aosMs < endMs && p.losMs > startMs);
    const achievableMb = over.reduce(
      (s, p) => s + (Number(p.capacity_mb) || 0), 0);
    const backlogMb = backlogAt(startMs);
    dumps.push({
      name: a.name, startMs,
      station: over.map((p) => p.gs_name).join(" + ") || null,
      inPass: over.length > 0,
      achievableMb, backlogMb,
      ratio: backlogMb > 0 ? achievableMb / backlogMb : null,
      fits: over.length > 0 && backlogMb <= achievableMb + 1e-6 });
  }
  return { perPass, dumps };
}

/* Fit verdict: "Will not fit" is an alarm (glyph + text + colour). */
function fitChip(v) {
  if (!v) return renderNoData();
  if (v.backlogMb <= 1e-6) return "<span class=\"fit ok\">" + t("Fits (no backlog)") + "</span>";
  const r = v.ratio === null ? null : v.ratio.toFixed(2);
  return v.fits
    ? "<span class=\"fit ok\">" + t("Fits") + " " + r + "×</span>"
    : "<span class=\"fit is-alarm\">" + glyph("alarm-up") + t("Will not fit") + (r !== null ? " " + r + "×" : "") + "</span>";
}

async function loadDataBudget() {
  try {
    const res = await fetch("/api/budget/data");
    if (!res.ok) return;
    dataBudget = await res.json();
    renderDataBudget(dataBudget);
  } catch (e) { /* keep last render */ }
}

function renderDataBudget(d) {
  const panel = $("dataBudgetPanel");
  if (d.utilization_percent === undefined) {
    panel.innerHTML = "<div class=\"nocompute\"><b>" + glyph("warn-up") + t("Data budget unavailable") + "</b><span>"
      + esc(d.reason || d.error || tText("no utilisation figure returned")) + "</span></div>";
    return;
  }
  const util = d.utilization_percent || 0;
  const warnAt = warnUtil();
  const lim = { yellow_high: warnAt, red_high: 100, lo: 0, hi: 100 };
  $("dataMeta").textContent = d.horizon_hours ? tText("{{h}} h horizon", { h: num(d.horizon_hours, 1) }) : "";
  let html = "<div class=\"bgrid\">"
    + renderGauge(util, lim, { label: tText("Storage now"), units: "%", digits: 1 })
    + renderGauge(d.peak_utilization_percent ?? util, lim, { label: tText("Peak fill"), units: "%", digits: 1 })
    + "<div class=\"kv\"><span>" + t("Onboard") + "</span><span>" + esc(num(d.onboard_data_mb, 0) ?? "?") + " / "
    + esc(num(d.storage_capacity_mb, 0) ?? "?") + " MB</span>"
    + "<span>" + t("Planned generation") + "</span><span>" + esc(num(d.planned_generation_mb, 1) ?? "0") + " MB</span>"
    + "<span>" + t("Planned downlink") + "</span><span>" + esc(num(d.planned_downlink_mb, 1) ?? "0") + " MB</span>"
    + "<span>" + t("Backlog growth") + "</span><span>" + esc(num(d.backlog_growth_mb, 1) ?? "0") + " MB</span></div>"
    + "<div class=\"kv\"><span>" + t("Pass capacity") + "</span><span>" + esc(num(d.daily_downlink_capacity_mb, 0) ?? "?") + " MB/d</span>"
    + "<span>" + t("Effective rate") + "</span><span>" + esc(((d.effective_downlink_rate_bps || 0) / 1000).toFixed(1)) + " kbps</span>"
    + "<span>" + t("Dump-capable passes") + "</span><span>" + esc(d.passes_dump_capable ?? "?") + " / " + esc(d.passes_total ?? "?") + "</span></div>"
    + "</div>";
  html += "<div class=\"verdict\">" + (d.plan_closes === false
    ? renderChip({ kind: "alarm", label: tText("Plan does not close") })
      + ((d.days_to_drain || 0) > 0 ? "<span class=\"muted\">" + t("{{d}} days of contact needed to drain", { d: d.days_to_drain.toFixed(1) }) + "</span>" : "")
    : renderChip({ kind: "ok", label: tText("Plan closes") })) + "</div>";
  const notes = [];
  if (d.first_overflow_utc) {
    notes.push(vrow("alarm", tText("First overflow: {{utc}} ({{mb}} MB lost)",
      { utc: fmtUTC(d.first_overflow_utc, { date: true }), mb: (d.overflow_mb || 0).toFixed(0) })));
  }
  for (const w of d.warnings || []) notes.push(vrow("caution", String(w)));
  if (notes.length) html += "<div class=\"notes\">" + notes.join("") + "</div>";
  panel.innerHTML = html;

  // G3: fit verdicts from the planner's own budget machinery.
  const fit = computeFitVerdicts(d);
  const fails = fit ? fit.dumps.filter((v) => !v.fits && v.backlogMb > 1e-6).length : 0;
  $("dataFitMeta").innerHTML = !fit || !fit.dumps.length ? esc(tText("no dumps planned"))
    : fails ? renderChip({ kind: "alarm", label: tText("{{n}} will not fit", { n: fails }) })
      : esc(tText("{{n}} dumps, all fit", { n: fit.dumps.length }));
  if (fails) $("dataFit").open = true;
  $("dataFitBody").innerHTML = fit && fit.dumps.length
    ? "<table class=\"ds-table dense\"><thead><tr><th>" + t("Dump") + "</th><th class=\"n\">"
      + t("Achievable / backlog") + "</th><th>" + t("Verdict") + "</th></tr></thead><tbody>"
      + fit.dumps.slice(0, 8).map((v) => "<tr><td>" + esc(v.name) + " " + hhmm(new Date(v.startMs)) + "Z"
        + (v.station ? " · " + esc(v.station) : "") + "</td><td class=\"n\">" + v.achievableMb.toFixed(1) + " / "
        + v.backlogMb.toFixed(1) + " MB</td><td>"
        + (v.inPass ? fitChip(v) : "<span class=\"fit is-alarm\">" + glyph("alarm-up") + t("Will not fit: outside every pass") + "</span>")
        + "</td></tr>").join("") + "</tbody></table>"
    : renderNoData({ label: tText("no dumps planned") });

  const passes = (d.pass_downlink || []).filter((p) => new Date(p.los).getTime() > simNow());
  $("dataPassBody").innerHTML = passes.length
    ? "<table class=\"ds-table dense\"><thead><tr><th>" + t("Station") + "</th><th class=\"n\">AOS</th><th class=\"n\">"
      + t("Duration") + "</th><th class=\"n\">" + t("Capacity") + "</th><th class=\"n\">" + t("Planned dump")
      + "</th><th>" + t("Verdict") + "</th></tr></thead><tbody>"
      + passes.slice(0, 5).map((p) => {
        const v = fit ? fit.perPass.get(p.pass_id) : null;
        return "<tr><td>" + esc(p.gs_name) + "</td><td class=\"n\">" + fmtUTC(p.aos, { seconds: false })
          + "</td><td class=\"n\">" + (p.duration_s / 60).toFixed(1) + " min</td><td class=\"n\">"
          + p.capacity_mb.toFixed(1) + " MB</td><td class=\"n\">"
          + (p.dump_scheduled ? p.planned_dump_mb.toFixed(1) + " MB" : renderNoData({ label: tText("no dump") }))
          + "</td><td>" + (p.dump_scheduled ? fitChip(v) : "") + "</td></tr>";
      }).join("") + "</tbody></table>"
    : renderNoData();
}

/* ── Last-pass RF rollup (G14 display half) ───────────────────────────── */
/* Reads the rfsim pass-rollup store cross-origin at the CONFIGURED
 * services.rfsim_url (planning/planner.yaml — additive, default unset).
 * No URL configured is a DESIGNED absent state; unreachable renders an
 * explicit notice — never stale numbers, never a guessed host. */
async function loadPassRollups() {
  const elOut = $("passRollupPanel");
  if (!elOut) return;
  const base = services && services.rfsim_url;
  if (!base) {
    elOut.innerHTML = "<span class=\"muted\">"
      + t("No rfsim URL configured ({{where}}) — achieved pass rollups are not shown.",
        { where: "planning/planner.yaml services.rfsim_url" }) + "</span>";
    return;
  }
  try {
    const res = await fetch(serviceUrl(base, "api/pass-rollups?limit=5"));
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    const rollups = data.rollups || [];
    const last = rollups.length ? rollups[rollups.length - 1] : null;
    const nd = renderNoData();
    let html = "";
    if (!last) {
      html += "<span class=\"muted\">" + t("No completed passes recorded yet.") + "</span>";
    } else {
      const lock = last.locked
        ? ((last.lock_delay_s === null || last.lock_delay_s === undefined)
          ? t("locked") : "+" + Number(last.lock_delay_s).toFixed(1) + " s")
        : "<span class=\"fit is-alarm\">" + glyph("alarm-up") + t("no lock") + "</span>";
      const has = (v) => v !== null && v !== undefined;
      html += "<div class=\"kv\">"
        + "<span>" + t("Station") + "</span><span>" + esc(last.gs_name || "?") + "</span>"
        + "<span>" + t("Lock delay") + "</span><span>" + lock + "</span>"
        + "<span>" + t("Mean {{q}}", { q: "Eb/N0" }) + "</span><span>" + (has(last.mean_eb_n0_db) ? Number(last.mean_eb_n0_db).toFixed(1) + " dB" : nd) + "</span>"
        + "<span>FER</span><span>" + (has(last.fer) ? Number(last.fer).toFixed(4) : nd) + "</span>"
        + "<span>" + t("Volume") + "</span><span>" + (has(last.data_volume_bytes) ? (Number(last.data_volume_bytes) / 1024).toFixed(1) + " kB" : nd) + "</span>"
        + "<span>" + t("Duration") + "</span><span>" + (has(last.duration_s) ? Number(last.duration_s).toFixed(0) + " s" : nd) + "</span>"
        + "</div>";
    }
    if (data.active) {
      html += "<div class=\"verdict\">" + renderChip({ kind: "active", label: data.active.first_lock_ts === null
        ? tText("Pass in progress: {{gs}} (not locked yet)", { gs: data.active.gs_name || "?" })
        : tText("Pass in progress: {{gs}} (locked)", { gs: data.active.gs_name || "?" }) }) + "</div>";
    }
    elOut.innerHTML = html;
  } catch (e) {
    elOut.innerHTML = vrow("caution", tText("rfsim at {{base}} unreachable — no achieved rollup.", { base: String(base) }));
  }
}

/* ── Imaging: targets list + opportunities ────────────────────────────── */
async function loadImagingTargets() {
  try {
    const res = await fetch("/api/imaging/targets");
    if (!res.ok) return;
    const targets = (await res.json()).targets || [];
    const out = $("imagingTargets");
    $("targetCount").textContent = String(targets.length);
    if (!targets.length) {
      out.innerHTML = "<span class=\"muted\">" + t("No imaging targets configured.") + "</span>";
      return;
    }
    out.innerHTML = "<table class=\"ds-table dense\"><thead><tr><th>" + t("Target") + "</th><th class=\"n\">"
      + t("Location") + "</th><th>" + t("Priority") + "</th></tr></thead><tbody>"
      + targets.map((tg) => {
        const tid = tg.target_id || tg.id;
        const nm = tg.name ? (tid ? tdb("target:" + tid + ":name", tg.name) : tg.name) : (tid || "?");
        const where = (tg.lat !== undefined && tg.lon !== undefined)
          ? tg.lat.toFixed(2) + "°, " + tg.lon.toFixed(2) + "°"
          : (tg.lat_min !== undefined
            ? tg.lat_min.toFixed(1) + "…" + (tg.lat_max ?? 0).toFixed(1) + "°" : "");
        return "<tr><td>" + esc(nm) + "</td><td class=\"n\">" + esc(where) + "</td><td>"
          + esc(prioText(tg.priority)) + "</td></tr>";
      }).join("") + "</tbody></table>";
  } catch (e) { /* keep last */ }
}

async function loadImagingOpportunities() {
  try {
    const res = await fetch("/api/imaging/opportunities");
    if (!res.ok) return;
    imagingOpps = (await res.json()).opportunities || [];
    renderImagingOpps();
  } catch (e) { /* keep last */ }
}

function renderImagingOpps() {
  const panel = $("imagingOpportunitiesPanel");
  if (!imagingOpps.length) {
    panel.innerHTML = "<div class=\"ds-panel-b muted\">" + t("No opportunities in the horizon.") + "</div>";
    return;
  }
  panel.innerHTML = "<table class=\"ds-table dense\"><thead><tr><th>" + t("Target") + "</th><th class=\"n\">"
    + t("Capture (UTC)") + "</th><th class=\"n\">" + t("Access") + "</th><th class=\"n\">" + t("Off-nadir")
    + "</th><th class=\"n\">" + t("Sun el.") + "</th><th><span class=\"ds-sr\">" + t("Action") + "</span></th></tr></thead><tbody>"
    + imagingOpps.slice(0, 8).map((opp) => {
      const captureUtc = opp.capture_utc || opp.start_utc;
      const nm = opp.target_id ? tdb("target:" + opp.target_id + ":name", opp.target_name) : opp.target_name;
      return "<tr><td>" + esc(nm) + (opp.priority === "high" ? " <small>" + t("high priority") + "</small>" : "")
        + "</td><td class=\"n\">" + fmtUTC(captureUtc) + "</td><td class=\"n\">"
        + esc(minPart(Math.round((opp.duration_s || 0) / 60))) + "</td><td class=\"n\">"
        + (opp.off_nadir_deg !== undefined ? opp.off_nadir_deg.toFixed(1) + "°" : "?") + "</td><td class=\"n\">"
        + (opp.solar_elevation_deg !== undefined ? opp.solar_elevation_deg.toFixed(0) + "°" : "?") + "</td><td>"
        // Eight buttons all named "Schedule" are indistinguishable to a screen
        // reader (R3 audit A6): the accessible name says which opportunity.
        + "<button type=\"button\" class=\"ds-btn sm\" data-act=\"schedule-imaging\" data-target=\"" + esc(opp.target_id)
        + "\" data-start=\"" + esc(captureUtc) + "\" aria-label=\"" + esc(tText("Schedule {{target}} at {{t}}Z", {
          target: nm, t: fmtUTC(captureUtc) })) + "\">" + t("Schedule") + "</button></td></tr>";
    }).join("") + "</tbody></table>";
}

async function scheduleImagingActivity(targetId, startTime) {
  try {
    const res = await fetch("/api/imaging/schedule", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_id: targetId, start_time: startTime }) });
    if (res.ok) { notify("ok", tText("Imaging activity scheduled.")); mainPoller.kick(); }
    else {
      const err = await res.json().catch(() => ({}));
      notify("alarm", tText("Failed to schedule imaging activity: {{reason}}", { reason: err.error || res.status }));
    }
  } catch (e) { notify("alarm", tText("Error scheduling imaging activity: {{e}}", { e: String(e) })); }
}

/* ── Two-step buttons that survive a language change ──────────────────── */
/* armButton() remembers the label it was bound with, so after the language
 * changes the button is cloned (dropping the old binding) and armed again
 * with the translated label. */
function armStatic(id, onExecute) {
  const old = $(id);
  const fresh = old.cloneNode(true);
  old.replaceWith(fresh);
  armButton(fresh, { seconds: 5, onExecute });
}
function armStatics() {
  armStatic("btnClearSchedule", clearSchedule);
  armStatic("btnUpload", uploadToMCS);
}

/* ── Wiring + init ────────────────────────────────────────────────────── */
const mainPoller = poller(pollAPIs, 30000);            // 30 s main poll
const scPoller = poller(loadSpacecraftState, 5000);    // 5 s position
const tsPoller = poller(loadTimeSource, 5000);         // 5 s clock anchor
const trackPoller = poller(loadGroundTrack, 120000);   // 120 s track

function wire() {
  $("btnAddActivity").addEventListener("click", () => openModal(null));
  $("btnModalClose").addEventListener("click", closeModal);
  $("btnModalCancel").addEventListener("click", closeModal);
  $("btnModalSubmit").addEventListener("click", submitActivity);
  $("modalOverlay").addEventListener("click", (e) => {
    if (e.target === $("modalOverlay")) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && $("modalOverlay").classList.contains("active")) closeModal();
  });
  $("actType").addEventListener("change", onActivityTypeChange);
  for (const ev of ["input", "change"]) {
    $("actStartTime").addEventListener(ev, () => { updateStartTimeHint(); updateSubmitState(); });
  }
  $("templateSelect").addEventListener("change", updateScheduleControls);
  $("btnLoadTemplate").addEventListener("click", loadStandardActivities);
  $("btnValidate").addEventListener("click", validateSchedule);
  $("btnValidateConstraints").addEventListener("click", validateConstraints);
  $("socInput").addEventListener("keydown", (e) => { if (e.key === "Enter") validateConstraints(); });
  $("uploadMode").addEventListener("click", (e) => {
    const b = e.target.closest("[data-mode]");
    if (!b) return;
    uploadMode = b.dataset.mode;
    for (const x of $("uploadMode").querySelectorAll("[data-mode]")) {
      x.setAttribute("aria-pressed", String(x === b));
    }
    updateScheduleControls();
  });
  for (const details of document.querySelectorAll("details.cx")) {
    details.addEventListener("toggle", () => {
      if (details.open) loadDomainConstraint(details);
    });
  }
  // Delegated row actions (rows are re-rendered every poll; Delete is armed
  // per render in updateActivityList).
  $("activityList").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-act=\"edit\"]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    const a = schedule.find((x) => Number(x.id) === id);
    if (a) openModal(a);
  });
  $("imagingOpportunitiesPanel").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-act=\"schedule-imaging\"]");
    if (btn) scheduleImagingActivity(btn.dataset.target, btn.dataset.start);
  });
  let rz = null;
  window.addEventListener("resize", () => { clearTimeout(rz); rz = setTimeout(drawTimeline, 120); });
}

async function init() {
  await I18n.ready;            // English: immediate; else bounded catalog load
  mountLangToggle($("lang-toggle"));
  // Static markup (data-i18n*) is re-applied by i18n.js; everything built
  // here in JS is rebuilt in the new language. The budget / imaging /
  // rollup panels are re-rendered by kicking the main poll (server data is
  // refetched, never re-labelled in place).
  onLangChange(() => {
    updateClock(); updateClockBadge(); renderApiChip(); socHint(); updateStartTimeHint();
    if ($("modalOverlay").classList.contains("active")) $("modalTitle").textContent = modalTitle();
    armStatics();
    loadActivityTypes(); loadPlanTemplates(); renderActTypeInfo(); renderOrbitFacts();
    $("activityList").innerHTML = "";
    redraw(); updateActivityList();
    for (const d of [$("scheduleValidation"), $("constraintsResult")]) d.innerHTML = "";
    for (const d of document.querySelectorAll("details.cx[open]")) loadDomainConstraint(d);
    mainPoller.kick(); scPoller.kick();
  });
  socHint();
  armStatics();
  wire();
  renderOrbitFacts();
  updateSpacecraftMarker();
  updateClock();
  setInterval(updateClock, 1000);                       // 1 s clock + countdowns
  loadActivityTypes();
  loadPlanTemplates();
  try { await loadPlannerConfig(); } catch (e) { /* readouts say "not served" */ }
  // Clock + stations before first paint (hard deps of the timeline).
  await loadTimeSource();
  await loadGroundStations();
  await initMap();
  await loadGroundTrack();
  redraw(); updateActivityList();
  mainPoller.start(); scPoller.start(); tsPoller.start(); trackPoller.start();
  setInterval(redraw, 10000);                           // 10 s picture
}

document.addEventListener("DOMContentLoaded", init);
