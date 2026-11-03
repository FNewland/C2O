/* ============================================================================
 * SMO MCS MODERN CONSOLE — mcs.js (execution plan §2.1)
 * ============================================================================
 * One ES module, no build step. Shared vocabulary from /static/shared/
 * (frozen Agent-1 contract): components.js + format.js. All rendering is
 * string-composition + innerHTML; this module owns DOM insertion.
 *
 * SECTIONS (search for "═══"):
 *   1. TIME            — simNow(), the single time primitive (M3)
 *   2. STATE           — module globals, catalogs, ring buffers
 *   3. UTIL            — helpers
 *   4. TRANSPORT       — WS /ws?position= + 3 s reconnect, REST fallback
 *   5. SA HEADER       — clocks, four cards, TRAINING chip, contingency strip
 *   6. NAV             — 62 px rail, pages, position filtering, keyboard
 *   7. SCHEMATICS      — schematics.svg mounting + bindSchematic
 *   8. OVERVIEW (L1)   — schematic-as-navigation, timeline, map, board
 *   9. SUBSYSTEM (L2)  — one skeleton instantiated 7×
 *  10. FRESHNESS       — display-wide staleness gate (P4)
 *  11. CMD             — builder + codec + quick cmds + S15 + HK + verification
 *  12. DIAG (L4)       — S3/S11/S6/S15/S12/S19/S9 + PARAMS panel
 *  13. FDIR            — strip + shared S12/S19 mounts + autonomy panel (M4)
 *  14. PROC            — runner + doc viewer + override + builder
 *  15. TRND            — archive trends (Chart.js, vendor-guarded)
 *  16. MAN             — operations manual
 *  17. DRAWER          — bottom log drawer (5 tabs, scroll lock)
 *  18. ALARMS          — docked alarm drawer + causal chain (P7/P9)
 *  19. DISPLAY CONFIG  — operational display config from /api/display-config
 *  20. BOOT
 *
 * House rules honoured here:
 *  - Date.now() appears ONLY inside section 1 (TIME). Everything else asks
 *    simNow()/simNowMs(). (Report 2 M3.)
 *  - The page polls /api/state — never the sim-named route (M12) and never
 *    reads the sim-clock-jump field (M10).
 *  - TRAINING chip only when the ground clock is simulator time (M1/M11).
 *  - sc_mode renderings are TM-derived (0x0700 / obdh.mode) and carry a
 *    provenance sub-label (M5-M8).
 * ============================================================================ */

import {
  esc, glyph, freshness, limitClass, renderParam, renderDeviationBar,
  renderSparkline, renderAndTable, renderChip, renderStepper, renderAlarmRow,
  renderEventRow, bindSchematic, poller, wsClient, mountLangToggle,
  renderValue, renderNoData, renderBanner, armButton,
} from "/static/shared/components.js";
import { fmtUTC, fmtMET, fmtCUC, fmtAge, fmtHex } from "/static/shared/format.js";
// UI language (EN|FR). t() for HTML strings, tText() for textContent;
// identifiers (mnemonics, hex, modes, PUS labels) never go through t().
// See docs/i18n/UI_I18N_GUIDE.md.
import { I18n, t, tText, tdb, getLang, onLangChange } from "/static/shared/i18n.js";
// One derivation of contact, mode and value age for every panel (R3 #10).
import { linkState as _linkState, modeState, linkLimited, FDIR_LEVELS } from "/static/shared/state.js";
// Participant logbook (LOGBOOK_SPEC.md): docked panel + "Log this" buttons.
import { mountLogbook, renderLogThis } from "/static/shared/logbook.js";
import { dockPanel } from "/static/shared/dock.js";

/* ═══ 1. TIME — the single time primitive ═════════════════════════════════ */
/* simNow() = server-anchored mission clock, advancing at the published rate.
 * The ONLY place Date.now() may be called (checked by
 * tests/test_mcs/test_modern_page_behaviour.py). In real mode speed is 1.0
 * and this degenerates to wall-clock UTC. */

let _anchorMs = null;       // mission epoch ms at anchor
let _anchorWallMs = null;   // wall ms at anchor            (Date.now domain)
let _speed = 1.0;

function _wallNowMs() { return Date.now(); }   // sole Date.now() call site

export function adoptServerClock(data) {
  if (!data) return;
  const iso = data.sim_time || data.ground_utc;
  if (iso) {
    const t = Date.parse(iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z");
    if (Number.isFinite(t)) { _anchorMs = t; _anchorWallMs = _wallNowMs(); }
  }
  if (typeof data.speed === "number" && Number.isFinite(data.speed)) _speed = data.speed;
}

export function simNowMs() {
  if (_anchorMs === null) return _wallNowMs();
  return _anchorMs + (_wallNowMs() - _anchorWallMs) * _speed;
}
export function simNow() { return new Date(simNowMs()); }
export function simNowSec() { return simNowMs() / 1000; }

/* ═══ 2. STATE ════════════════════════════════════════════════════════════ */

const S = {
  state: {},               // latest WS/REST state document
  positions: {},           // /api/positions
  position: "flight_director",
  paramCatalog: [],        // /api/param-catalog parameters[]
  paramByHex: {},          // hex -> catalog def
  limits: {},              // /api/limits limits{}
  tcCatalog: [],           // /api/tc-catalog commands[] (position-filtered flags)
  tcCatalogAll: [],        // unfiltered (flight_director view) for authority display
  quickCommands: [],       // /api/tc-catalog quick_commands[]
  clientConfig: {},        // /api/client-config
  procCards: null,         // /api/procedure/cards (per position)
  procCardOpen: "",        // expanded card id
  displayConfig: {},       // /api/display-config (capture gates, health baselines)
  timeMode: "unknown",     // "sim" | "real" | "unknown"  (see resolveTimeMode)
  wsConnected: false,
  page: "ovr",
  alarms: [],              // /api/alarms journal (client copy)
  contacts: [],            // /api/contacts (normalised)
  contactSchedule: [],     // /api/displays/contact-schedule passes
  groundStations: [],
  hkStructures: null,
  memoryMap: null,
  failureCodes: {},
  fdir: null,              // /api/fdir
  verifLog: [],
  cmdHistory: [],          // local ring
  events: [],              // event log ring
  tmLog: [],               // packet log ring
  subsysEvents: { eps: [], tcs: [], aocs: [], ttc: [], payload: [], prop: [], obdh: [], orbital: [] },
  handover: [],
  goNoGo: null,
  series: {},              // hex -> ring buffer for sparklines
  manual: null,
  manualOpen: "",        // path of the open section (active-item highlight)
  manualBodies: {},      // path -> markdown, cached so search covers body text

  procStatus: null,
  s11Schedule: null,
  armed: {},               // cmd name -> armed flag (arm→execute)
  chartStale: false,       // display-wide staleness gate verdict
  chainOpen: "",           // alarm id of the open causal-chain overlay (re-render on language switch)
  // ── POSITION_NEEDS gap surfaces (G1–G9, G12, G15) ──
  faultGraph: null,        // /api/fault-graph (G6 first-out grouping)
  gonogoMatrix: null,      // /api/gonogo-matrix (G7 call-matrix context)
  consoleLog: [],          // /api/console-log merged stream (G8)
  conlogKind: "all",       // LOG tab kind filter
  burnPlan: null,          // planner orbit_manoeuvre join (G9)
  linkPred: null,          // /api/displays/link-prediction (G5)
  linkMeasured: [],        // [{t, eb, rssi}] measured ring for the overlay
  blindTc: { enabled: false, armPending: false },   // G12
  alarmGroupsOpen: {},     // rootAlarmId -> expanded (G6)
};

const RING = 300;
const EVENT_SUBSYSTEM_RANGES = {
  orbital: [0x0001, 0x00FF], eps: [0x0100, 0x01FF], aocs: [0x0200, 0x02FF],
  obdh: [0x0300, 0x03FF], tcs: [0x0400, 0x04FF], ttc: [0x0500, 0x05FF],
  payload: [0x0600, 0x06FF], prop: [0x0800, 0x08FF],
};
const AOCS_MODES = ["OFF", "SAFE_BOOT", "DETUMBLE", "COARSE_SUN", "NOMINAL",
  "FINE_POINT", "SLEW", "DESAT", "ECLIPSE", "INERTIAL"];
const SC_MODES = ["NOMINAL", "SAFE", "EMERGENCY", "SCIENCE"];

/* Modern page id ↔ classic tab id (positions.yaml speaks classic ids). */
const PAGE_TO_CLASSIC = {
  ovr: "overview", eps: "eps", tcs: "tcs", aocs: "aocs", ttc: "ttc",
  pld: "payload", prp: "prop", obd: "obdh", cmd: "commanding", fdir: "fdir",
  proc: "procedures", trnd: "trends", diag: "pus", man: "manual",
};
const SUB_PAGES = ["eps", "tcs", "aocs", "ttc", "pld", "prp", "obd"];
const PAGE_SUBSYSTEM = { eps: "eps", tcs: "tcs", aocs: "aocs", ttc: "ttc",
  pld: "payload", prp: "prop", obd: "obdh" };
const RAIL = [
  ["ovr", "OVR"], ["eps", "EPS"], ["tcs", "TCS"], ["aocs", "AOC"], ["ttc", "TTC"],
  ["pld", "PLD"], ["prp", "PRP"], ["obd", "OBD"], ["|", ""],
  ["cmd", "CMD"], ["fdir", "FDR"], ["proc", "PRC"], ["trnd", "TRD"],
  // "PUS", not "DIA": the classic console's top-level tab was "PUS SERVICES"
  // and operators look for that name. The page id stays `diag`.
  ["diag", "PUS"], ["man", "MAN"],
];

// English text is the i18n key: display via tText(POSITION_INFO[p].title).
const POSITION_INFO = {
  flight_director: { title: "FLIGHT DIRECTOR" },
  eps_tcs: { title: "POWER & THERMAL" },
  aocs: { title: "FLIGHT DYNAMICS / AOCS" },
  ttc: { title: "TT&C" },
  payload_ops: { title: "PAYLOAD OPERATIONS" },
  fdir_systems: { title: "FDIR / SYSTEMS" },
  propulsion: { title: "PROPULSION" },
};

/* ═══ 3. UTIL ═════════════════════════════════════════════════════════════ */

const $ = (id) => document.getElementById(id);
function setText(id, v) { const el = $(id); if (el) el.textContent = v; }
function setHTML(id, v) { const el = $(id); if (el) el.innerHTML = v; }
function show(id, on) { const el = $(id); if (el) el.classList.toggle("hide", !on); }
function num(v, dp = 1) {
  if (v === null || v === undefined || !Number.isFinite(Number(v))) return "—";
  return Number(v).toFixed(dp);
}
function hex4(v) { return fmtHex(v, 4); }
async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}
async function postJSON(url, body) {
  const r = await fetch(url, { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}) });
  let j = null;
  try { j = await r.json(); } catch (e) { /* non-JSON */ }
  return { ok: r.ok, status: r.status, json: j };
}
function announce(msg) { setText("alert-live", msg); }
/* Link-freshness word for the SEE card (server/verdict value stays English in logic). */
function linkWord(w) {
  return w === "FRESH" ? tText("FRESH") : w === "DEGRADED" ? tText("DEGRADED")
    : w === "STALE" ? tText("STALE") : w;
}
function tsShort() { return fmtUTC(simNow(), { seconds: true }); }
function paramVal(hexId) {
  const p = S.state.params;
  return p ? p[hexId] : undefined;
}
function paramAge(hexId) {
  const ages = S.state.params_age;
  if (!ages) return undefined;
  return ages[String(parseInt(hexId, 16))];
}
/* Composite values object for renderAndTable / renderParam callers. */
// The alphanumeric table can run to ~150 rows per subsystem, so it refreshes
// on a paint budget rather than on every state message. preservingUi keeps
// scroll position and any focused control across the rebuild.
let _andLastRender = 0;
function refreshAndTable(pageId, params) {
  const host = $(`${pageId}-and`);
  if (!host) return;
  const now = (typeof performance !== "undefined" && performance.now)
    ? performance.now() : 0;
  if (now - _andLastRender < 900) return;
  _andLastRender = now;
  preservingUi(`${pageId}-and`, () =>
    setHTML(`${pageId}-and`, renderAndTable(params, liveValues())));
}
function liveValues() {
  return {
    params: S.state.params || {},
    ages: S.state.params_age || {},
    limitState: S.state.param_limit_state || {},
    limits: S.limits,
    // Engineering values + the cadence-aware four-state verdict, so the
    // alphanumeric table reads like the rest of the console: state names
    // instead of codes, and NOT ENABLED instead of a frozen number for a SID
    // nobody has switched on.
    states: paramStatesMap(),
    verdicts: paramVerdictMap(),
  };
}
/* {hex: {code: name}} for every catalogued parameter that has state codes. */
function paramStatesMap() {
  const out = {};
  for (const p of S.paramCatalog || []) {
    if (p.states && Object.keys(p.states).length) out[p.hex] = p.states;
  }
  // Sentinels read as words in the tables and schematics too.
  for (const [hex, m] of Object.entries(SENTINELS)) {
    out[hex] = { ...(out[hex] || {}) };
    for (const [code, label] of Object.entries(m)) out[hex][code] = tText(label);
  }
  return out;
}
/* {hex: 'fresh'|'degraded'|'stale'|'disabled'} for the catalogue. */
function paramVerdictMap() {
  const out = {};
  for (const p of S.paramCatalog || []) out[p.hex] = paramFreshness(p.hex);
  return out;
}
/* Page-level param triad: catalog + live + limits joined (P3). */
/* ── Engineering values ───────────────────────────────────────────────────
 *
 * Field report 2026-08-20: "check in the new version that parameters are
 * displayed in engineering values, e.g. for AOCS mode - but this may be a
 * generic issue - at the minute only the raw values seem to display".
 *
 * It was generic. Every catalogue-driven surface here formatted values with a
 * plain numeric formatter, so aocs.mode read `4` instead of `NOMINAL`. Two
 * widgets (the AOCS mode chain and the SA-header mode chip) had their own
 * hardcoded arrays -- a third copy of codes that already live in config.
 *
 * /api/param-catalog now serves a `states` map for every parameter whose codes
 * are documented in configuration (see smo_common/telemetry/eng_values.py).
 * This is the one place that turns a raw value into what an operator reads.
 *
 * The raw code is kept in parentheses on purpose: procedures, packet dumps and
 * S12 limit definitions all quote the number, so hiding it would break the
 * cross-check an operator actually performs.
 */
export function paramStates(hexId) {
  const st = (S.paramByHex[hexId] || {}).states;
  return st && Object.keys(st).length ? st : null;
}
/* Sentinel values (R3 / wave 2): a saturated counter is a STATE, not a
 * number. obdh.time_since_sync_s holds UINT32_MAX until the first sync;
 * printing "4294967295 s" reads as a 136-year-old sync. */
const UINT32_MAX = 4294967295;
// English text is the i18n key (sentinel labels, translated via tText)
const SENTINELS = { "0x0A14": { [UINT32_MAX]: "never synced" } };
export function sentinelLabel(hexId, raw) {
  const n = Number(raw);
  if (raw === null || raw === undefined || raw === "" || !Number.isFinite(n)) return null;
  const m = SENTINELS[hexId];
  if (m && m[n] !== undefined) return tText(m[n]);
  if (n === UINT32_MAX) return tText("not set");
  return null;
}
export function engValue(hexId, raw) {
  if (raw === undefined || raw === null) return "—";
  const sl = sentinelLabel(hexId, raw);
  if (sl) return sl;
  const st = paramStates(hexId);
  if (!st) return null;                 // not enumerated: caller formats numerically
  const code = Math.round(Number(raw));
  if (!Number.isFinite(code)) return String(raw);
  const name = st[String(code)];
  return name ? `${name} (${code})` : `UNKNOWN (${code})`;
}
export function paramTriad(hexId) {
  const def = S.paramByHex[hexId] || { hex: hexId, name: hexId };
  const band = S.limits[hexId] ? { ...S.limits[hexId] } : null;
  const st = (S.state.param_limit_state || {})[hexId];
  const age = paramAge(hexId);
  // Freshness is judged HERE with the cadence-aware verdict (passed down as
  // `verdict`, which wins over the shared flat rule); age_s only labels it.
  const raw = paramVal(hexId);
  const has = raw !== undefined && raw !== null && raw !== "";
  const fr = has ? paramFreshness(hexId) : "nodata";
  // The shared triad owns the four data states (live / degraded / stale with
  // the LAST value kept + age chip / no data / not enabled); the MCS only
  // hands it its cadence-aware verdict and the age (wave 2: the page-local
  // regex post-processing of the markup is retired).
  const lim = { ...(band || {}), verdict: fr === "disabled" ? "disabled" : fr };
  if (st) lim.state = st;
  if (age !== undefined) lim.age_s = age;
  const eng = has ? engValue(hexId, raw) : null;
  // The engineering STRING rides in `def.eng`; the numeric value is still
  // passed as the value so limits, banding and the deviation bar keep working.
  // Units are dropped for a discrete parameter: a state name has no unit.
  return eng !== null ? renderParam({ ...def, units: "", eng }, raw, lim)
    : renderParam(def, raw, lim);
}
/* Where the station-measured link figures came from (M1). RSSI, margin,
   BER, Eb/N0 and AGC are the ground receiver's monitoring data, not
   spacecraft TM; with no signal there are no numbers, and this says why. */
export function stationLinkNote() {
  const st = (S.state || {}).station_link;
  const ids = "0x0502 · 0x0503 · 0x050C · 0x0519 · 0x051A";
  if (!st || !st.source) {
    return `${t("Station-measured ({{ids}}): no station monitoring data", { ids })}`;
  }
  const src = st.source === "radio" ? tText("station receiver (RF bridge)")
    : tText("station receiver (simulated from the link budget; no RF bridge)");
  if (!st.signal) {
    return `${t("Station-measured ({{ids}}) from {{src}}: no signal", { ids, src })}` +
      (st.reason ? ` — ${esc(st.reason)}` : "");
  }
  const band = st.band === "UHF" ? ` · ${t("UHF beacon")}` : "";
  return `${t("Station-measured ({{ids}}) from {{src}}, not spacecraft TM", { ids, src })}${band}`;
}
function pushSeries(hexId, v) {
  if (!Number.isFinite(Number(v))) return;
  const s = S.series[hexId] || (S.series[hexId] = []);
  s.push(Number(v));
  if (s.length > 120) s.shift();
}
/* ── Cadence-aware staleness ──────────────────────────────────────────────
 *
 * Field report 2026-08-20: "check the stale telemetry mechanism ... both in
 * the old and new versions of the UI".
 *
 * The modern console was judging EVERY parameter against a flat 5 s / 15 s
 * threshold (`freshness()` in the shared component library). That is exactly
 * the defect configs/eosat1/mcs/staleness.yaml was written to kill: HK SID 3
 * (TCS) has interval_s 60, so the thermal displays read STALE for ~45 s out of
 * every 60, and SID 11 (beacon, 30 s) read STALE for 22 s out of every 30 --
 * during the one mission phase where the beacon is the ONLY telemetry there
 * is. Classic was fixed; modern was never wired up, and still fetched
 * /api/client-config without reading the cadence join out of it.
 *
 * This is the classic algorithm, deliberately identical so the two consoles
 * cannot disagree about whether a value is current:
 *
 *     fresh    while age <= max(floor_fresh_s, interval_s * fresh_factor)
 *     degraded while age <= max(floor_stale_s, interval_s * stale_factor)
 *     stale    beyond that
 *
 * plus the fourth state the policy file defines: NOT ENABLED, when every HK
 * structure carrying the parameter is disabled. A value with no enabled source
 * is not stale telemetry -- it is telemetry nobody has asked for, and the
 * remedy is TC(3,5), not chasing a link fault. Rendering that as "stale" is
 * the silent lie the four-state model exists to prevent.
 *
 * Ages are SIM seconds as served (params_age / subsystem_staleness /
 * hk_sid_age_s). Never re-age them against the browser wall clock.
 */
const STALE_POLICY_FALLBACK = {
  stale_factor: 1.5, fresh_factor: 0.9,
  floor_fresh_s: 10.0, floor_stale_s: 20.0,
  aperiodic_fresh_s: 300.0, aperiodic_stale_s: 900.0,
};
function stalePolicy() {
  return Object.assign({}, STALE_POLICY_FALLBACK, (S.clientConfig || {}).staleness || {});
}
export function stalenessThresholds(intervalS) {
  const pol = stalePolicy();
  if (intervalS === null || intervalS === undefined || !(Number(intervalS) > 0)) {
    return { fresh: pol.aperiodic_fresh_s, stale: pol.aperiodic_stale_s,
             aperiodic: true, interval_s: null };
  }
  const iv = Number(intervalS);
  const fresh = Math.max(pol.floor_fresh_s, iv * pol.fresh_factor);
  const stale = Math.max(pol.floor_stale_s, iv * pol.stale_factor, fresh);
  return { fresh, stale, aperiodic: false, interval_s: iv };
}
export function ageVerdict(ageS, intervalS) {
  const th = stalenessThresholds(intervalS);
  const age = Number(ageS);
  if (!Number.isFinite(age)) return "stale";
  if (age <= th.fresh) return "fresh";
  if (age <= th.stale) return "degraded";
  return "stale";
}
// Cadence for one parameter, from the /api/client-config join. null => aperiodic.
function paramInterval(hexId) {
  const cad = ((S.clientConfig || {}).param_cadence || {})[hexId] ||
              ((S.clientConfig || {}).param_cadence || {})[String(parseInt(hexId, 16))];
  if (!cad) return null;
  return Array.isArray(cad) ? cad[0] : cad.interval_s;
}
function paramSids(hexId) {
  const cad = ((S.clientConfig || {}).param_cadence || {})[hexId] ||
              ((S.clientConfig || {}).param_cadence || {})[String(parseInt(hexId, 16))];
  if (!cad) return [];
  return (Array.isArray(cad) ? cad.slice(1) : cad.sids) || [];
}
/** 'fresh' | 'degraded' | 'stale' | 'disabled' for one parameter. */
export function paramFreshness(hexId) {
  const sids = paramSids(hexId);
  if (sids.length) {
    const en = S.state.hk_enabled || {};
    // only claim "disabled" when we actually know the enable state
    const known = sids.filter((sid) => en[String(sid)] !== undefined);
    if (known.length && known.every((sid) => !en[String(sid)])) return "disabled";
  }
  return ageVerdict(paramAge(hexId), paramInterval(hexId));
}
export function paramIsStale(hexId) {
  const v = paramFreshness(hexId);
  return v === "stale" || v === "disabled";
}
function spark(hexId, cls = "") {
  const stale = paramIsStale(hexId);
  return renderSparkline(S.series[hexId] || [], { stale, cls, w: 110, h: 24 });
}
/* Spacecraft mode, TM-derived with provenance (M5-M8). */
export function scModeInfo() {
  // M8 disposition: obdh.mode (0x0300) PRIMARY, FDIR level (0x0700)
  // secondary escalation — never raw sim sc_mode. 0x0700 is fdir.level
  // (0 nominal … 3 critical), NOT a mode enum: reading it as one decoded
  // 3 -> "EMERGENCY" and 0 -> "NOMINAL" whatever the OBC said (2026-08c
  // item 7; regressed by bb09265, restored 2026-11-01).
  // The derivation itself lives in /static/shared/state.js (modeState) so
  // the header, overview, FDIR page and banner can never disagree.
  const m = modeState(S.state, { trainingTruth: S.timeMode === "sim" });
  if (m.mode === null) return { label: "—", src: tText("not downlinked") };
  return { label: m.mode,
           src: m.source === "SIM (training)" ? tText("SIM (training)") : m.source };
}

/* FDIR alert level 0x0700 (0 nominal … 3 critical) — the banner's
 * SECONDARY driver per M8: a warning/critical FDIR level raises the strip
 * even when the OBC still reports a nominal mode. */
export function fdirLevelInfo() {
  return modeState(S.state).fdirLevel;
}

/* Contact verdict for every panel (header TALK card, overview orbit bar,
 * pass table, ground-station card, HIGH-rate policy). A frame-lock reading
 * counts only while it is itself current (cadence-aware verdict). */
export function linkState(st = S.state) {
  return _linkState(st, { lockFresh: (hex) => paramFreshness(hex) === "fresh"
    || paramFreshness(hex) === "degraded", policy: stalePolicy() });
}

/* One value in its data state (UI brief §1.3), through the shared
 * renderValue so every readout on the console looks the same:
 *   live      value + unit (caution/alarm: colour + triangle + H/HH/L/LL)
 *   degraded  value + unit + amber age chip
 *   stale     LAST value, dimmed italic, + age chip ("82.1 % · 59 s")
 *   no data   the "no data" tag — never an em-dash
 *   disabled  "not enabled" (the HK SID carrying it is switched off)
 * The MCS supplies its cadence-aware verdict; sentinels read as words. */
export function valueCell(hexId, digits = 2, units = "", opts = {}) {
  const raw = opts.value !== undefined ? opts.value : paramVal(hexId);
  const has = raw !== undefined && raw !== null && raw !== "";
  const fr = !has ? "nodata"
    : opts.fresh || (hexId ? paramFreshness(hexId) : "fresh");
  if (fr === "nodata") return renderNoData();
  const n = Number(raw);
  const eng = hexId ? engValue(hexId, raw) : null;
  const engTxt = eng !== null && eng !== undefined ? String(eng)
    : (Number.isFinite(n) ? undefined : String(raw));
  return renderValue(Number.isFinite(n) ? n : 0, {
    units: engTxt === undefined ? units : "", digits, eng: engTxt,
    ageS: hexId ? paramAge(hexId) : undefined,
    verdict: fr === "disabled" ? "disabled" : fr,
    limitState: hexId ? (S.state.param_limit_state || {})[hexId] : undefined,
  });
}

/* ═══ 4. TRANSPORT ════════════════════════════════════════════════════════ */

let ws = null;
let restFallback = null;

function handleState(data) {
  S.state = data || {};
  adoptServerClock(S.state);
  if (S.state.schedule) S.s11Schedule = S.state.schedule;
  // feed sparkline rings for every schematic/triad param we track
  const p = S.state.params || {};
  for (const hexId of TRACKED_SERIES) pushSeries(hexId, p[hexId]);
  // measured Eb/N0 + RSSI ring for the predicted-vs-measured overlay (G5).
  // Timestamped (sim time), unlike the sparkline rings, because it must be
  // drawn against the prediction's absolute time axis.
  const eb = Number(p["0x0519"]), rssi = Number(p["0x0502"]);
  if (Number.isFinite(eb)) {
    S.linkMeasured.push({ t: simNowSec(), eb, rssi: Number.isFinite(rssi) ? rssi : null });
    if (S.linkMeasured.length > 300) S.linkMeasured.shift();
  }
  if (PIC) PIC.onState();
  updateChartGate();
  updateSaHeader();
  updateRailHealth();
  updateContingency();
  updateTrainingChip();
  lbWatchSimStatus();
  renderCurrentPage(false);
  // The drawer used to be driven ONLY by handleTMPacket, so on a quiet link --
  // or in bootloader mode, where only SID 11 flows -- CMD HISTORY and the
  // event/TM logs froze (field report 2026-08-20). State packets arrive on a
  // fixed cadence; renderBottomDrawer() no-ops when the drawer is shut.
  renderBottomDrawer();
}

function handleTMPacket(pkt) {
  if (!pkt) return;
  const ts = tsShort();
  S.tmLog.unshift(packetRowText(pkt, ts));
  if (S.tmLog.length > RING) S.tmLog.length = RING;
  if (pkt.event) {
    const sevMap = { 1: "info", 2: "warn", 3: "warn", 4: "alarm" };
    const msg = eventText(pkt.event);
    pushEvent({ ts, sev: pkt.event.rejection ? "warn" : (sevMap[pkt.event.severity] || "info"),
      label: pkt.event.rejection ? "REJECT" : `EVT`, msg,   // tag codes; REJECT translated at render
      instructor: /^INSTRUCTOR OVERRIDE/.test(pkt.event.description || "") });
    routeEvent(msg, pkt.event.event_id);
    if (pkt.event.severity >= 3) announce(tText("Alarm: event {{id}} — {{desc}}",
      { id: hex4(pkt.event.event_id), desc: pkt.event.description || "" }));   // on-board aux text: English
  }
  if (pkt.monitoring) {
    const m = pkt.monitoring;
    pushEvent({ ts, sev: m.transition === "out_of_limits" ? "warn" : "nom",
      label: m.transition === "out_of_limits" ? "OOL" : "NOM",
      msg: `S12 ${hex4(m.param_id)} = ${num(m.value, 2)} [${m.transition}]` });
    if (S.page === "fdir" || S.page === "diag") loadFdir();
  }
  if (pkt.schedule) { S.s11Schedule = pkt.schedule; renderS11Table(); }
  if (pkt.monitor_defs || pkt.ea_defs || pkt.fdir_journal) loadFdir();
  if (pkt.memory_dump) renderMemoryDump(pkt.memory_dump);
  if (pkt.memory_check) renderMemoryCheck(pkt.memory_check);
  if (pkt.verification) {
    const v = pkt.verification;
    const okSub = v.subtype === 1 || v.subtype === 7;
    pushEvent({ ts, sev: okSub ? "nom" : "alarm", label: `S1.${v.subtype}`,
      msg: `TC(${v.tc_service},${v.tc_subtype}) ${okSub ? "OK" : tText("FAILED")}` +
           (v.code !== undefined ? ` code ${hex4(v.code)}` : "") });
    noteVerification(v);
  }
  renderBottomDrawer();
}

/* Audible cue on a NEW alarm (classic playAlarmBeep capability; Agent 5
 * inventory fix). WebAudio, one short tone, swallowed silently when the
 * browser blocks audio before a user gesture. */
/* Alarm sound on/off, remembered per browser (operator preference only —
 * the visual and screen-reader cues never switch off). */
const ALARM_SOUND_KEY = "c2o.mcs.alarmSound";
export function alarmSoundOn() {
  try { return localStorage.getItem(ALARM_SOUND_KEY) !== "off"; } catch (e) { return true; }
}
export function setAlarmSound(on) {
  try { localStorage.setItem(ALARM_SOUND_KEY, on ? "on" : "off"); } catch (e) { /* not persisted */ }
  playAlarmBeep._muted = !on;
  renderAlarmSoundBtn();
}
function renderAlarmSoundBtn() {
  const b = $("alarm-sound");
  if (!b) return;
  const on = !playAlarmBeep._muted && alarmSoundOn();
  b.textContent = on ? "🔔" : "🔕";
  b.setAttribute("aria-pressed", String(!on));
  const lbl = on ? tText("Alarm sound on — click to mute") : tText("Alarm sound muted — click to unmute");
  b.setAttribute("aria-label", lbl);
  b.title = lbl;
}
function playAlarmBeep() {
  if (playAlarmBeep._muted || !alarmSoundOn()) return;
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    if (!playAlarmBeep._ctx) playAlarmBeep._ctx = new AC();
    const ctx = playAlarmBeep._ctx;
    const osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.frequency.value = 880; gain.gain.value = 0.06;
    osc.connect(gain); gain.connect(ctx.destination);
    osc.start(); osc.stop(ctx.currentTime + 0.15);
  } catch (e) { /* audio unavailable — visual + live-region cues remain */ }
}

function handleAlarmMsg(alarm) {
  if (!alarm) return;
  const i = S.alarms.findIndex((a) => a.id === alarm.id);
  const isNew = i < 0;
  if (i >= 0) S.alarms[i] = alarm; else S.alarms.unshift(alarm);
  renderAlarmDrawer();
  updateSaHeader();
  if (isNew) playAlarmBeep();
  announce(tText("Alarm: {{sub}} {{msg}}", { sub: alarm.subsystem || "",
    msg: alarm.message || [alarm.name, alarm.value, alarm.units, alarm.limit].filter((x) => x !== undefined && x !== "").join(" ") }));
}
function handleAlarmCleared(msg) {
  const ids = msg.ids || (msg.id !== undefined ? [msg.id] : []);
  for (const id of ids) {
    const a = S.alarms.find((x) => x.id === id);
    if (a) a.rtn = true;
  }
  renderAlarmDrawer();
}

export function connectWS() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  if (ws) ws.close();
  ws = wsClient(`${proto}//${location.host}/ws?position=${encodeURIComponent(S.position)}`, {
    state: (m) => handleState(m.data),
    tm: (m) => handleTMPacket(m.packet),
    alarm: (m) => handleAlarmMsg(m.alarm),
    alarm_cleared: (m) => handleAlarmCleared(m),
    go_nogo_poll: (m) => handleGoNoGo(m),
    go_nogo_status: (m) => handleGoNoGo(m),
    go_nogo_result: (m) => handleGoNoGo(m),
    _open() { S.wsConnected = true; wsDot(true); },
    _close() { S.wsConnected = false; wsDot(false); },
    _unknown() { /* forward-compatible: ignore */ },
  });
}
function wsDot(on) { const el = $("ws-dot"); if (el) el.classList.toggle("on", on); }
function setPosition(pos) {
  S.position = pos;
  try { localStorage.setItem("mcs.position", pos); } catch (e) { /* private mode */ }
  if (ws && ws.readyState() === 1) ws.send({ type: "set_position", position: pos });
  else connectWS();
  loadTcCatalog();     // server filters `allowed` per position
  applyPositionFilter();
  renderCurrentPage(true);
}

/* REST fallback: /api/state every 2 s ONLY while the WS is down (classic
 * cadence preserved; route per M12 — never the sim-named one). */
function startRestFallback() {
  restFallback = poller(async () => {
    if (S.wsConnected) return;
    handleState(await getJSON("/api/state"));
  }, 2000);
  restFallback.start();
}

/* Time-source resolution (M1). Preferred: the MCS's own /api/client-config
 * `time_source` field (additive server change, Agent 5) — no cross-origin
 * call needed. Fallbacks kept: the planner's /api/time-source via the
 * configured planner base (M13), then the published speed (a rate ≠ 1.0 can
 * only be simulation). Unknown -> chip hidden. */
async function resolveTimeMode() {
  const cc = S.clientConfig || {};
  if (cc.time_source === "real" || cc.time_source === "sim") {
    S.timeMode = cc.time_source;
    updateTrainingChip();
    return;
  }
  const base = S.clientConfig.planner_url;
  if (base) {
    try {
      const t = await getJSON(`${base}/api/time-source`);
      if (t && (t.time_source === "real" || t.time_source === "sim")) {
        S.timeMode = t.time_source;
        updateTrainingChip();
        return;
      }
    } catch (e) { /* planner unreachable — fall through */ }
  }
  S.timeMode = "unknown";
  updateTrainingChip();
}

export function trainingChipState() {
  const speed = Number(S.state.speed);
  const simEvidence = S.timeMode === "sim" ||
    (S.timeMode === "unknown" && Number.isFinite(speed) && speed !== 1.0);
  if (S.timeMode === "real" || !simEvidence) return { visible: false, text: "" };
  const paused = Number.isFinite(speed) && speed === 0;
  const text = paused ? tText("TRAINING · PAUSED")
    : tText("TRAINING · SIM x{{speed}}", { speed: Number.isFinite(speed) ? speed : 1 });
  return { visible: true, text };
}
function updateTrainingChip() {
  const c = trainingChipState();
  const el = $("training-chip");
  if (!el) return;
  el.classList.toggle("hide", !c.visible);
  el.textContent = c.text;
}

/* ═══ 5. SA HEADER ════════════════════════════════════════════════════════ */

function startClocks() {
  setInterval(() => {
    setText("utc-clock", fmtUTC(simNow(), { seconds: true }));
    // strip the shared formatter's "MET " prefix — this clock already has a
    // MET label above it (Agent 5 screenshot fix: read "MET MET 000/…")
    setText("met-clock", fmtMET(S.state.met_s).replace(/^MET /, ""));
    const tc = S.state.time_correlation || {};
    const cuc = fmtCUC(tc.sc_cuc_coarse, tc.sc_cuc_fine, tc.epoch);
    setText("sc-time-clock", cuc.utc === "—" ? "—" : cuc.utc.slice(11));
    updateNextCard();     // countdowns re-derive every second on simNow()
  }, 1000);
  // The PUS panels' fetched inputs -- S12 monitor definitions, S19 rules, the
  // HK structure table -- used to refresh only on an S12 transition event or a
  // tab click, so a monitor that changed quietly never showed. Poll them while
  // a page that renders them is actually on screen.
  setInterval(() => {
    if (S.page === "fdir" || S.page === "diag") loadFdir();
    if (S.page === "diag" && diagTab === "s3") loadHkStructures();
  }, 5000);
}

/* The annunciator (one cell per SA question): shape + word + detail, so
 * the verdict reads in greyscale and without reading any number.
 *   ok       check          caution  hollow triangle
 *   alarm    filled triangle stale   dashed ring, italic word
 *   nodata   hollow ring     active  accent run mark (pass in progress) */
const SA_GLYPH = { ok: "ack", caution: "warn-up", alarm: "alarm-up", stale: "stale",
  nodata: "off", active: "run", neutral: "" };
function saCell(id, state, value, sub) {
  const card = $(id);
  if (card) card.className = "sacard is-" + state;
  const g = SA_GLYPH[state] || "";
  setHTML(`${id}-dot`, g ? glyph(g) : "");
  setText(`${id}-v`, value);
  if (sub !== undefined) setText(`${id}-s`, sub);
}

export function updateSaHeader() {
  const st = S.state;
  const sa = st.sa || {};
  // SEE — link freshness, TM tier active vs commanded, store fill
  const age = sa.last_frame_age_s;
  const fr = freshness(age);
  const noTm = age === undefined || age === null;
  const word = { fresh: tText("Live"), degraded: tText("Late"), stale: tText("Stale") }[fr] || tText("Stale");
  const tierBits = [];
  if (sa.tm_tier_name || sa.tm_tier !== undefined) {
    // rate tiers (BEACON/LOW/HIGH) are identifiers; server reason text stays English
    tierBits.push(tText("tier {{tier}}", { tier: String(sa.tm_tier_name || sa.tm_tier) }));
    if (sa.tm_tier_demoted) tierBits.push(`cmd ${sa.tm_tier_cmd_name || sa.tm_tier_cmd} — ${sa.tm_tier_demotion_reason || tText("demoted")}`);
  }
  if (sa.store_fill_pct !== undefined && sa.store_fill_pct !== null)
    tierBits.push(tText("store {{pct}} % ({{src}})",
      { pct: num(sa.store_fill_pct, 0), src: sa.store_fill_source || "" }));
  saCell("sa-see", noTm ? "nodata" : fr === "fresh" ? "ok" : fr === "degraded" ? "caution" : "stale",
    noTm ? tText("No telemetry") : `${word} · ${fmtAge(age)}`,
    tierBits.join(" · ") || tText("awaiting HK"));

  // TALK — lock chain, last TC verdict, GS in contact
  const p = st.params || {};
  // linkState(): the ONE contact verdict (shared state.js). A frame-lock
  // reading left over from the previous pass no longer claims contact.
  const ls = linkState(st);
  const inContact = ls.contact;
  const lk = (on) => (on ? "✓" : "✗");
  const lockTxt = tText("carrier {{c}} · bit {{b}} · frame {{f}}",
    { c: lk(ls.locks.carrier), b: lk(ls.locks.bit), f: lk(ls.locks.frame) });
  const lastV = S.verifLog[0];
  saCell("sa-talk", inContact ? "ok" : "nodata",
    inContact ? (ls.gs ? tText("In contact · {{gs}}", { gs: ls.gs }) : tText("In contact"))
      : tText("No contact"),
    lockTxt + (lastV ? " · " + tText("last TC {{v}}", { v: lastV.verdict }) : ""));

  // WELL — sc mode (TM-derived + provenance), alarm counts, load shed
  const mode = scModeInfo();
  // One alarm store feeds every count (P7.5): de-duplicated groups.
  const counts = alarmSummary();
  const unack = counts.unacked;
  const shed = p["0x0134"];
  // G1: SoC-at-eclipse-exit is one of the two header-grade projections.
  // Valid -> the number (ground-derived); invalid -> nothing here (the EPS
  // page carries the full INVALID row with its reason).
  const socExit = derivedEntry("eps.soc_at_eclipse_exit_pred");
  const modeBad = mode.label === "EMERGENCY" ? "alarm" : mode.label === "SAFE" ? "caution" : "";
  const wellState = counts.alarm || modeBad === "alarm" ? "alarm"
    : counts.warn || modeBad ? "caution" : mode.label === "—" ? "nodata" : "ok";
  const tally = [counts.alarm ? tText("{{count}} alarm", { count: counts.alarm, plural: "{{count}} alarms" }) : "",
    counts.warn ? tText("{{count}} caution", { count: counts.warn, plural: "{{count}} cautions" }) : ""]
    .filter(Boolean).join(", ");
  saCell("sa-well", wellState, mode.label === "—" ? tText("Mode unknown")
      : mode.label + (tally ? " · " + tally : ""),
    tText("{{n}} unacknowledged · mode from {{src}}", { n: unack, src: mode.src }) +
    (Number(shed) > 0 ? " · " + tText("LOAD SHED L{{n}}", { n: shed }) : "") +
    (socExit && socExit.valid
      ? " · " + tText("SoC@ecl-exit {{v}} % (gnd)", { v: num(socExit.value, 0) }) : ""));
  setText("alarm-unack-n", String(unack));
  const ab = $("alarms-btn");
  if (ab) {
    ab.classList.toggle("is-alarm", unack > 0 && counts.alarm > 0);
    ab.classList.toggle("is-caution", unack > 0 && !counts.alarm);
    setHTML("alarm-btn-g", unack > 0 ? glyph(counts.alarm ? "alarm-up" : "warn-up") : "");
    ab.setAttribute("aria-label", tText("{{n}} unacknowledged alarms — open the alarm journal", { n: unack }));
  }
  setText("alarm-drawer-unack", tText("{{n}} unacknowledged", { n: unack }));

  updateNextCard();
}

function updateNextCard() {
  // NEXT — next AOS/LOS countdown, next eclipse, next scheduled activity
  const nowS = simNowSec();
  let cur = null, next = null;
  for (const c of S.contactSchedule) {
    const aos = c.aos_time, los = c.los_time;
    if (aos === undefined || los === undefined) continue;
    if (aos <= nowS && nowS < los) cur = c;
    else if (aos > nowS && (!next || aos < next.aos_time)) next = c;
  }
  const cd = (t) => {
    const d = Math.max(0, t - nowS);
    const h = Math.floor(d / 3600), m = Math.floor((d % 3600) / 60), s2 = Math.floor(d % 60);
    const mmss = `${String(m).padStart(2, "0")}:${String(s2).padStart(2, "0")}`;
    return h ? `${h}:${mmss}` : mmss;
  };
  let v = tText("No pass scheduled"), sub = tText("no pass schedule"), state = "nodata";
  // The track drains over the last hour before AOS (or across the pass to LOS).
  let frac = null;
  if (cur) {
    v = tText("LOS in {{t}}", { t: cd(cur.los_time) });
    sub = tText("{{gs}} pass in progress", { gs: cur.ground_station || "" });
    state = "active";
    frac = (cur.los_time - nowS) / Math.max(1, cur.los_time - cur.aos_time);
  } else if (next) {
    v = tText("AOS in {{t}}", { t: cd(next.aos_time) });
    sub = tText("{{gs}}, max elevation {{el}}°", { gs: next.ground_station || "", el: num(next.max_elevation, 0) });
    state = "neutral";
    frac = Math.min(1, (next.aos_time - nowS) / 3600);
  }
  const ecl = S.state.time_to_eclipse_entry_s ?? S.state.next_eclipse_s ?? (S.state.orbit || {}).next_eclipse_s;
  if (ecl !== undefined && ecl !== null && Number(ecl) > 0) sub += " · " + tText("eclipse in {{t}}", { t: fmtAge(ecl) });
  // G1/G3: pass-fit ratio (backlog ÷ capacity) is the second header-grade
  // projection — it answers "will this pass be enough?" next to the AOS/LOS
  // countdown it depends on.
  const fit = derivedEntry("ttc.pass_fit_ratio");
  if (fit && fit.valid) {
    sub += " · " + (Number(fit.value) > 1.0
      ? tText("fit {{r}} WON'T FIT (gnd)", { r: num(fit.value, 2) })
      : tText("fit {{r}} fits (gnd)", { r: num(fit.value, 2) }));
    if (Number(fit.value) > 1.0 && state !== "nodata") state = "caution";
  }
  saCell("sa-next", state, v, sub);
  const tr = $("sa-next-track");
  if (tr) {
    tr.classList.toggle("hide", frac === null);
    tr.classList.toggle("los", !!cur);
    const bar = tr.querySelector ? tr.querySelector("i") : null;
    if (bar && frac !== null) bar.style.width = `${(Math.max(0, Math.min(1, frac)) * 100).toFixed(1)}%`;
  }
}


function updateContingency() {
  // M8: obdh.mode primary, 0x0700 secondary — never raw sim sc_mode.
  const mode = scModeInfo();
  const badMode = mode.label === "SAFE" || mode.label === "EMERGENCY";
  const lvl = fdirLevelInfo();
  const badFdir = lvl !== null && lvl >= 2;
  const el = $("contingency-banner");
  if (!el) return;
  const bad = badMode || badFdir;
  el.classList.toggle("hide", !bad);
  // Glyph + colour + text (P6): the strip reads in greyscale too.
  const say = (txt) => { el.innerHTML = glyph("alarm-up") + `<span>${esc(txt)}</span>`; };
  if (badMode) say(tText("Contingency: spacecraft mode {{mode}} (source: {{src}}). Open FDIR for the recovery state and the alarm drawer for the journal.",
    { mode: mode.label, src: mode.src }));
  else if (badFdir) say(tText("Contingency: FDIR level {{lvl}} (TM fdir.level 0x0700) with OBC mode {{mode}}. Open FDIR for the recovery state and the alarm drawer for the journal.",
    { lvl: lvl >= 3 ? "CRITICAL" : "WARNING", mode: mode.label }));
}

/* ═══ 6. NAV — rail, pages, position filtering, keyboard ══════════════════ */

function buildRail() {
  const host = $("nav-rail");
  if (!host) return;
  // ARIA (R3 A6): the <nav> landmark holds ONE tablist; the visual group
  // separator is presentational (role=none, aria-hidden) so the tablist owns
  // only tabs (axe aria-required-children). Roving tabindex: the selected
  // tab is the rail's single Tab stop; arrows / Home / End move within it.
  host.innerHTML = `<div role="tablist" aria-orientation="vertical" class="rail-tabs"
      aria-label="${esc(tText("Pages"))}">` + RAIL.map(([id, label]) => {
    if (id === "|") return `<div class="sep" role="none" aria-hidden="true"></div>`;
    return `<button id="rail-${id}" data-page="${id}" role="tab" aria-selected="false"
      aria-controls="page-${id}" tabindex="-1"
      title="${esc(pageTitle(id))}">${esc(label)}<span class="hd" id="rail-hd-${id}"></span></button>`;
  }).join("") + `</div>`;
  host.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-page]");
    if (b) showPage(b.dataset.page);
  });
  host.addEventListener("keydown", (e) => {
    if (e.key === "Home" || e.key === "End") {
      e.preventDefault();
      const vis = visiblePages();
      const id = e.key === "Home" ? vis[0] : vis[vis.length - 1];
      showPage(id);
      const b = $(`rail-${id}`);
      if (b) b.focus();
      return;
    }
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight" &&
        e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
    e.preventDefault();
    const dir = (e.key === "ArrowRight" || e.key === "ArrowDown") ? 1 : -1;
    navRelative(dir);
  });
}
// English text is the i18n key (rail tooltips; the rail codes OVR/EPS/... are identifiers).
const PAGE_TITLES = { ovr: "Overview (L1)", eps: "Electrical power", tcs: "Thermal control",
  aocs: "Attitude & orbit control", ttc: "Telemetry, tracking & command",
  pld: "Payload", prp: "Propulsion", obd: "On-board data handling",
  cmd: "Commanding", fdir: "FDIR", proc: "Procedures", trnd: "Trends",
  diag: "PUS services — S3 HK · S11 schedule · S6 memory · S15 stores · S12 monitoring · S19 event-action · S9 time · parameters",
  man: "Operations manual" };
function pageTitle(id) {
  return PAGE_TITLES[id] ? tText(PAGE_TITLES[id]) : id;
}
/* Language switch: the rail is built once, so only its tooltips are redone. */
function retitleRail() {
  for (const [id] of RAIL) {
    const b = id !== "|" ? $(`rail-${id}`) : null;
    if (b) b.setAttribute("title", pageTitle(id));
  }
}
function visiblePages() {
  return RAIL.filter(([id]) => id !== "|").map(([id]) => id)
    .filter((id) => railVisibleForPosition(id, S.positions[S.position], S.position === "flight_director"));
}
function navRelative(dir) {
  const vis = visiblePages();
  const i = vis.indexOf(S.page);
  const nxt = vis[(i + dir + vis.length) % vis.length];
  showPage(nxt);
  const b = $(`rail-${nxt}`);
  if (b) b.focus();
}

/* Position filtering of the rail (classic tabVisibleForPosition, mapped). */
export function railVisibleForPosition(pageId, pos, seeAll) {
  if (seeAll) return true;
  if (!pos) return true;
  const classic = PAGE_TO_CLASSIC[pageId];
  const visibleTabs = pos.visible_tabs || [];
  const subsystems = pos.subsystems || [];
  if (pageId === "fdir") return subsystems.includes("fdir");
  return visibleTabs.includes(classic);
}

export function applyPositionFilter() {
  const pos = S.positions[S.position];
  const seeAll = S.position === "flight_director";
  for (const [id] of RAIL) {
    if (id === "|") continue;
    const b = $(`rail-${id}`);
    if (b) b.hidden = !railVisibleForPosition(id, pos, seeAll);
  }
  if (!railVisibleForPosition(S.page, pos, seeAll)) showPage("ovr");
  // overview schematic node filtering
  const overview = pos ? (pos.overview_subsystems || pos.subsystems || []) : [];
  for (const [pageId, sub] of Object.entries(PAGE_SUBSYSTEM)) {
    const node = $(`ovr-node-${pageId === "pld" ? "pld" : pageId}`);
    if (node) node.style.display = (seeAll || overview.includes(sub)) ? "" : "none";
  }
  renderQuickCommands();     // in-place quick commands re-filter
  renderManual();            // manual section filter
  if (S.page === "man") loadProcedureCards();   // cards are per position
  const pi = POSITION_INFO[S.position] || {};
  setText("pos-detail", pi.title ? tText(pi.title) : S.position);
}

function updateRailHealth() {
  // Rail badges are links into the ONE alarm store (P7.5): active
  // de-duplicated alarms per subsystem, P1–P2 as "a", P3–P4 as "w".
  const summ = alarmSummary();
  for (const [pageId, sub] of Object.entries(PAGE_SUBSYSTEM)) {
    const el = $(`rail-hd-${pageId}`);
    if (!el) continue;
    const c = summ.bySub[sub] || { w: 0, a: 0 };
    // corner pip: triangle (filled alarm / hollow caution) + NUMERAL — never
    // colour alone (P6), and outside the label box so it never overlaps it
    if (c.a) { el.className = "hd a"; el.innerHTML = glyph("alarm-up") + String(c.a); }
    else if (c.w) { el.className = "hd w"; el.innerHTML = glyph("warn-up") + String(c.w); }
    else { el.className = "hd"; el.textContent = ""; }
  }
  const alarmsHd = $("rail-hd-fdir");
  if (alarmsHd) {
    const unack = summ.unacked;
    alarmsHd.className = unack ? "hd a" : "hd";
    alarmsHd.innerHTML = unack ? glyph("alarm-up") + String(unack) : "";
  }
}

export function showPage(id) {
  if (!id) return;
  S.page = id;
  for (const [pid] of RAIL) {
    if (pid === "|") continue;
    const sec = $(`page-${pid}`);
    if (sec) sec.classList.toggle("hide", pid !== id);
    const b = $(`rail-${pid}`);
    if (b) {
      b.classList.toggle("on", pid === id);
      b.setAttribute("aria-selected", pid === id ? "true" : "false");
      b.setAttribute("tabindex", pid === id ? "0" : "-1");    // roving tabindex
    }
  }
  const work = $("main");
  if (work) work.scrollTop = 0;
  renderCurrentPage(true);
}

function initKeyboard() {
  const REGIONS = ["top-bar", "nav-rail", "main", "bottom-drawer"];
  document.addEventListener("keydown", (e) => {
    const tag = (e.target && e.target.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "select" || tag === "textarea";
    if (e.key === "F6") {
      e.preventDefault();
      const cur = REGIONS.findIndex((r) => $(r) && $(r).contains(document.activeElement));
      const nxt = $(REGIONS[(cur + 1 + REGIONS.length) % REGIONS.length]);
      if (nxt) { nxt.setAttribute("tabindex", "-1"); nxt.focus(); }
      return;
    }
    if (e.key === "Escape") {
      if ($("help-overlay") && $("help-overlay").classList.contains("open")) { toggleHelp(false); return; }
      if ($("chain-overlay") && $("chain-overlay").classList.contains("open")) { toggleChain(false); return; }
      if ($("alarm-drawer") && $("alarm-drawer").classList.contains("open")) { toggleAlarmDrawer(false); return; }
      if (S.page !== "ovr") showPage("ovr");
      return;
    }
    if (typing) return;
    if (e.key === "?") { toggleHelp(); return; }
    if (e.key.toLowerCase() === "a") { toggleAlarmDrawer(true); return; }
    if (e.key.toLowerCase() === "k") { ackFirstUnacked(); return; }
  });
}

/* ═══ 7. SCHEMATICS ═══════════════════════════════════════════════════════ */

let schematicsDoc = null;   // raw svg text -> symbol innerHTML by id
const TRACKED_SERIES = ["0x0101", "0x0105", "0x0135", "0x0217", "0x025B", "0x0502",
  "0x0503", "0x0406", "0x0407", "0x0408", "0x0601", "0x0604", "0x0B01", "0x0302", "0x0312"];

async function loadSchematics() {
  try {
    const txt = await (await fetch("/static/modern/schematics.svg")).text();
    schematicsDoc = {};
    const re = /<symbol id="([^"]+)" viewBox="([^"]+)">([\s\S]*?)<\/symbol>/g;
    let m;
    while ((m = re.exec(txt))) schematicsDoc[m[1]] = { viewBox: m[2], body: m[3] };
  } catch (e) { schematicsDoc = {}; }
}
function schematicMarkup(symbolId) {
  const sym = schematicsDoc && schematicsDoc[symbolId];
  if (!sym) return `<div class="ds-banner stale">${t("schematic unavailable")}</div>`;
  // Drawn at no less than 1:1 (min-width = viewBox width): the 12 px labels
  // in the drawing then never render below the 12 px floor. A narrower card
  // scrolls the drawing sideways instead of shrinking its text.
  const vbW = Number(String(sym.viewBox).split(/\s+/)[2]) || 0;
  // tabindex: a drawing wider than its card scrolls, and a scroll region
  // must be reachable from the keyboard (axe scrollable-region-focusable).
  return `<div class="stage" tabindex="0" role="group" aria-label="${esc(tText("Schematic"))}"><svg class="sc" viewBox="${esc(sym.viewBox)}" ` +
         (vbW ? `style="min-width:${vbW}px;max-width:${Math.round(vbW * 1.25)}px" ` : "") +
         `data-schematic="${esc(symbolId)}">${sym.body}</svg></div>`;
}
function bindPageSchematic(pageId) {
  const sec = $(`page-${pageId}`);
  if (!sec || !sec.querySelectorAll) return;
  // Hand the schematic the catalogue states and the four-state verdict as
  // well as the raw state, so its value boxes read like the rest of the
  // console (AOCS CORE -> "COARSE_SUN (3)", not "3").
  const schState = { ...S.state, param_states: paramStatesMap(),
                     param_verdicts: paramVerdictMap() };
  sec.querySelectorAll("svg[data-schematic]").forEach((svg) => {
    bindSchematic(svg, schState);
    holdSchematicValues(svg);
  });
}
/* After the shared binder: a stale node keeps its last value, dimmed and
 * italic with its age ("82.1 % · 59 s"); a node never received reads
 * "no data" instead of an em-dash (R3 A4). */
function holdSchematicValues(svg) {
  const p = S.state.params || {};
  svg.querySelectorAll("[data-param]").forEach((node) => {
    const hex = node.getAttribute("data-param");
    const vl = node.querySelector(".vl");
    if (!vl) return;
    node.classList.remove("held", "nodata");
    const oldTip = node.querySelector("title.held-age");
    if (oldTip && oldTip.remove) oldTip.remove();
    const raw = p[hex];
    if (raw === undefined || raw === null || raw === "") {
      // compact form: the schematic box has room for ~6 characters
      node.classList.add("nodata");
      vl.textContent = tText("no data", { context: "short" });
      return;
    }
    const fr = paramFreshness(hex);
    if (fr !== "stale") return;
    const units = node.getAttribute("data-units") || "";
    const eng = engValue(hex, raw);
    const n = Number(raw);
    const v = eng !== null && eng !== undefined ? String(eng)
      : (Number.isFinite(n) ? num(n, Math.abs(n) >= 100 ? 0 : 1) : String(raw)) + (units ? " " + units : "");
    const age = paramAge(hex);
    node.classList.add("held");
    // The schematic box is too narrow for "value · age": the value is held
    // (dimmed, italic, dashed box from the shared .stale rule) and the age
    // rides in the node's tooltip; the triads and tables carry the chip.
    vl.textContent = v;
    const tip = age !== undefined ? tText("last received {{age}} ago", { age: fmtAge(age) }) : tText("age unknown");
    let ttl = node.querySelector("title.held-age");
    if (!ttl && node.ownerDocument && node.ownerDocument.createElementNS) {
      ttl = node.ownerDocument.createElementNS("http://www.w3.org/2000/svg", "title");
      ttl.setAttribute("class", "held-age");
      node.insertBefore(ttl, node.firstChild);
    }
    if (ttl) ttl.textContent = tip;
  });
}

/* schematic-as-navigation: one document-level listener for ds-nav */
function initSchematicNav() {
  document.addEventListener("ds-nav", (e) => {
    const page = e.detail && e.detail.page;
    if (page) showPage(page);
  });
}

/* ═══ 8. OVERVIEW (L1) ════════════════════════════════════════════════════ */

function buildOverviewPage() {
  return `
  <div class="pad" id="page-ovr" role="tabpanel" aria-label="Overview" data-i18n-aria-label>
    <div class="pghd">
      <div><h1 class="pt" data-i18n>Spacecraft overview</h1>
        <p class="sub"><span data-i18n="Click the block you are concerned about to open its subsystem.">Click the block you are concerned about to open its subsystem.</span>
          <span data-i18n="Position:">Position:</span> <span id="pos-detail"></span></p></div>
      <div class="orbit" id="ovr-orbit-bar" aria-live="off"></div>
    </div>
    <!-- L1: the schematic is the navigation; the contact strip says what is
         next. Columns scroll internally on a short screen. -->
    <div class="g ovr-grid">
      <div class="g ovr-left" tabindex="0" aria-label="Schematic and contacts" data-i18n-aria-label="Schematic and contacts">
        <div class="ds-card ovr-schem-card"><h2><span data-i18n="EOSAT-1 overview">EOSAT-1 overview</span>
          <span class="r" data-i18n="grey is nominal; colour marks a deviation">grey is nominal; colour marks a deviation</span></h2>
          <div class="bd" id="ovr-schematic"></div></div>

        <div class="ds-card"><h2><span data-i18n="Contacts, next 12 h">Contacts, next 12 h</span>
          <span class="r" id="ovr-timeline-src">/api/contacts</span></h2>
          <div class="bd">
            <canvas id="ovr-timeline" height="56" style="width:100%" role="img"
              aria-label="Contact windows over the next 12 hours" data-i18n-aria-label="Contact windows over the next 12 hours"></canvas>
            <div class="tl-leg" id="ovr-timeline-legend"></div>
            <div class="scroll-y" style="max-height:168px;margin-top:8px">
              <table class="plain" id="ovr-pass-table"></table></div>
          </div></div>
      </div>
      <div class="g ovr-right" tabindex="0" aria-label="Ground track and system board" data-i18n-aria-label="Ground track and system board">
        <div class="ds-card" id="ovr-power-card"><h2><span data-i18n="Power">Power</span>
          <span class="r" data-i18n="line width is power on a fixed scale">line width is power on a fixed scale</span></h2>
          <div class="bd" id="ovr-power"><span class="ds-meta" data-i18n>awaiting data…</span></div></div>
        <div class="ds-card"><h2 data-i18n="Ground track">Ground track</h2>
          <div class="bd" id="ovr-map" style="min-height:180px"></div></div>
        <div class="ds-card"><h2><span data-i18n="System board">System board</span> <span class="r">/api/displays/system-overview</span></h2>
          <div class="bd" id="ovr-board"></div></div>
      </div>
    </div>
  </div>`;
}

/* Sub-satellite point: state.lat / state.lon / state.alt_km (the MCS
 * /api/state names; `lat_deg` was never served, so the bar read "—"). */
function orbitPoint(st = S.state) {
  const o = st.orbit || {};
  const pick = (...xs) => xs.find((x) => x !== undefined && x !== null && Number.isFinite(Number(x)));
  return { lat: pick(st.lat, st.lat_deg, o.lat, o.lat_deg), lon: pick(st.lon, st.lon_deg, o.lon, o.lon_deg),
           alt: pick(st.alt_km, o.alt_km) };
}

function updateOverview() {
  // orbit strip: where the spacecraft is, with ground-derived values labelled
  const st = S.state;
  const pt = orbitPoint(st);
  const rv = (v, u, d) => valueCell(null, d, u, { value: v, fresh: v === undefined ? "nodata" : "fresh" });
  const ecl = st.in_eclipse ?? st.eclipse ?? paramVal("0x0108");
  const eclKnown = ecl !== undefined && ecl !== null;
  const contact = linkState(st).contact;
  setHTML("ovr-orbit-bar",
    `<span><span class="k">${t("Lat")}</span>${rv(pt.lat, "°", 2)}</span>` +
    `<span><span class="k">${t("Lon")}</span>${rv(pt.lon, "°", 2)}</span>` +
    `<span><span class="k">${t("Alt")}</span>${rv(pt.alt, "km", 0)}</span>` +
    `<span class="ds-src" title="${esc(tText("computed on the ground from the orbit state, not downlinked"))}">${t("ground")}</span>` +
    (eclKnown ? renderChip({ kind: "neutral", label: Number(ecl) ? tText("Eclipse") : tText("Sunlit") }) : renderNoData()) +
    renderChip(contact ? { kind: "ok", glyph: "lock", label: tText("In contact") } : { kind: "off", label: tText("No contact") }));
  // pictorial synoptic + power summary (shared/ui-viz); the schematic is
  // the fallback when the shared modules are not available
  if (PIC && PIC.render("ovr")) {
    renderContactTimeline();
    renderPassTable();
    renderGroundTrack();
    return;
  }
  // schematic
  const host = $("ovr-schematic");
  if (host && !host.dataset.mounted && schematicsDoc) {
    host.innerHTML = schematicMarkup("sch-ovr");
    host.dataset.mounted = "1";
    I18n.applyDom(host);          // SVG <text data-i18n> (schematics.svg) is markup: translate after mount
  }
  const mode = scModeInfo();
  const modeEl = document.getElementById("sch-ovr-mode");
  if (modeEl) modeEl.textContent = mode.label;
  bindPageSchematic("ovr");
  renderContactTimeline();
  renderPassTable();
  renderGroundTrack();
}

/* Contact strip: the next 12 h (and the last 1 h) as bars on one line, the
 * next pass in the accent, NOW as a full-height tick, hour ticks below.
 * Colours come from the tokens so the light theme follows. */
function cssVar(name, fallback) {
  try {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  } catch (e) { return fallback; }
}
function renderContactTimeline() {
  const cv = $("ovr-timeline");
  if (!cv || !cv.getContext) return;
  const ctx = cv.getContext("2d");
  if (!ctx || !ctx.fillRect) return;
  const dpr = (typeof window !== "undefined" && window.devicePixelRatio) || 1;
  const W = cv.clientWidth || 800, H = 56;
  cv.width = W * dpr; cv.height = H * dpr;
  if (ctx.setTransform) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const nowS = simNowSec();
  const t0 = nowS - 3600, t1 = nowS + 12 * 3600;
  const x = (tt) => ((tt - t0) / (t1 - t0)) * W;
  const C = { track: cssVar("--s3", "#262C36"), pass: cssVar("--fill", "#7F8A98"),
    next: cssVar("--accent", "#5CC6EB"), now: cssVar("--val", "#F5F7FA"),
    tick: cssVar("--line-2", "#3B4450"), lbl: cssVar("--tx3", "#9BA7B4") };
  const font = cssVar("--font-mono", "monospace");
  ctx.fillStyle = C.track; ctx.fillRect(0, 14, W, 14);
  // hour ticks + labels every 2 h
  ctx.font = `12px ${font}`; ctx.textBaseline = "top";
  for (let h = -1; h <= 12; h++) {
    const xx = Math.round(x(nowS + h * 3600)) + 0.5;
    ctx.fillStyle = C.tick; ctx.fillRect(xx, 30, 1, 4);
    if (h > 0 && h % 2 === 0 && xx < W - 30) {
      ctx.fillStyle = C.lbl; ctx.fillText(`+${h} h`, xx - 12, 38);
    }
  }
  const src = S.contacts.length ? S.contacts : S.contactSchedule;
  let nextAos = Infinity;
  for (const c of src) {
    const aos = c.aos_utc ?? c.aos_time;
    if (aos > nowS && aos < nextAos) nextAos = aos;
  }
  const stations = new Set();
  for (const c of src) {
    const aos = c.aos_utc ?? c.aos_time, los = c.los_utc ?? c.los_time;
    if (aos === undefined || los === undefined || los < t0 || aos > t1) continue;
    stations.add(c.ground_station || "GS");
    const isNext = aos === nextAos || (aos <= nowS && nowS < los);
    ctx.fillStyle = isNext ? C.next : C.pass;
    ctx.fillRect(x(aos), 14, Math.max(2, x(los) - x(aos)), 14);
  }
  ctx.fillStyle = C.now; ctx.fillRect(Math.round(x(nowS)) - 1, 6, 2, 28);
  ctx.fillStyle = C.lbl; ctx.textBaseline = "alphabetic";
  ctx.fillText(tText("now"), Math.round(x(nowS)) + 4, 11);
  setHTML("ovr-timeline-legend",
    `<span><i class="now"></i>${t("now")}</span>` +
    `<span><i class="next"></i>${t("next or current pass")}</span>` +
    `<span><i class="pass"></i>${t("later passes")}</span>` +
    (stations.size ? `<span>${esc([...stations].join(", "))}</span>` : `<span>${t("no passes in the next 12 h")}</span>`));
}

function renderPassTable() {
  const nowS = simNowSec();
  const rows = S.contactSchedule.slice(0, 8).map((c, i) => {
    const aos = c.aos_time, los = c.los_time;
    const dur = aos !== undefined && los !== undefined ? Math.round((los - aos) / 60) : null;
    const inPass = aos <= nowS && nowS < los;
    const status = los < nowS ? renderChip({ kind: "off", label: tText("past") })
      : inPass ? renderChip({ kind: "active", label: tText("in progress") })
      : renderChip({ kind: "neutral", label: tText("upcoming") });
    return `<tr${inPass ? ' class="is-active"' : ""}><td class="mono">${i + 1}</td><td>${esc(c.ground_station || "")}</td>
      <td class="mono">${fmtUTC(aos, { date: false })}</td>
      <td class="mono">${fmtUTC(los, { date: false })}</td>
      <td class="mono num">${dur === null ? renderNoData() : dur + " min"}</td>
      <td class="mono num">${valueCell(null, 0, "°", { value: c.max_elevation })}</td><td>${status}</td></tr>`;
  }).join("");
  setHTML("ovr-pass-table",
    `<thead><tr><th>#</th><th>${t("Station")}</th><th>AOS</th><th>LOS</th><th class="n">${t("Duration")}</th>` +
    `<th class="n">${t("Max el")}</th><th>${t("Status")}</th></tr></thead>` +
    `<tbody>${rows || `<tr><td colspan="7">${t("no pass schedule")}</td></tr>`}</tbody>`);
}

let worldMap = null;
function renderGroundTrack() {
  const host = $("ovr-map");
  if (!host) return;
  const { lat, lon } = orbitPoint();
  if (typeof SvgWorldMap === "undefined") {
    // Vendor asset guard (plan R3): designed absence, never an exception.
    host.innerHTML = `<div class="ds-banner stale">${t("map library not installed ({{path}})",
      { path: "/static/vendor/js/svg-world-map.js" })}</div>
      <div class="mono" style="margin-top:8px;font-size:13px">
      ${t("subsatellite point: {{lat}}°, {{lon}}°", { lat: num(lat, 2), lon: num(lon, 2) })}</div>`;
    return;
  }
  try {
    if (!worldMap) { host.innerHTML = ""; worldMap = new SvgWorldMap(host); }
    // One spacecraft marker, MOVED each tick (it used to be re-added every
    // second under a layer name the library ignores, so markers piled up);
    // stations drawn once, as grey rings. Colours: accent = the thing you
    // are tracking; grey = context (P1).
    const acc = cssVar("--accent", "#5CC6EB"), grey = cssVar("--fill", "#7F8A98");
    if (lat !== undefined && lon !== undefined && worldMap.addMarker) {
      if (!S.mapSc) S.mapSc = worldMap.addMarker(lat, lon, { radius: 4, color: acc, strokeColor: cssVar("--bg", "#0B0D10") });
      else if (S.mapSc.setLatLng) S.mapSc.setLatLng(lat, lon);
    }
    if (!S.mapGsDrawn && S.groundStations.length && worldMap.addMarker) {
      for (const gs of S.groundStations)
        worldMap.addMarker(gs.lat ?? gs.lat_deg, gs.lon ?? gs.lon_deg, { radius: 3, color: "none", strokeColor: grey });
      S.mapGsDrawn = true;
    }
  } catch (e) {
    host.innerHTML = `<div class="ds-banner stale">${t("map render failed — {{err}}", { err: String(e.message || e) })}</div>`;
  }
}

// English text is the i18n key (system-overview key_parameters names)
const BOARD_NAMES = ["Battery SoC", "Attitude Error", "FPA Temperature", "Link Margin", "Storage %"];
async function refreshSystemBoard() {
  try {
    // Server shape: subsystem_health[{name,status,description}],
    // key_parameters[{name,value,units,status,param_id}] (the old reads of
    // `subsystems` / `id` / `state` matched nothing, so the chips never drew).
    const d = await getJSON("/api/displays/system-overview");
    const subs = d.subsystem_health || [];
    const chips = subs.map((s2) => renderChip({
        kind: /alarm|red/i.test(s2.status || "") ? "alarm"
          : /warn|yellow/i.test(s2.status || "") ? "warn" : "neutral",
        label: String(s2.name || "?").toUpperCase(), title: s2.description || "" })).join(" ");
    const params = d.key_parameters || [];
    const rows = params.slice(0, 12).map((r) => {
      const hexId = r.param_id || null;
      const live = hexId && paramVal(hexId) !== undefined;
      return `<tr><td>${esc(BOARD_NAMES.includes(r.name) ? tText(r.name) : String(r.name || ""))}</td>
        <td class="mono hexid">${esc(hexId || "")}</td>
        <td class="num">${live ? valueCell(hexId, 1, r.units || "")
          : valueCell(null, 1, r.units || "", { value: r.value ?? undefined,
              fresh: r.value === null || r.value === undefined ? "nodata" : "fresh" })}</td></tr>`;
    }).join("");
    setHTML("ovr-board", (chips ? `<div class="row">${chips}</div>` : "") +
      (rows ? `<table class="plain" style="margin-top:8px"><tbody>${rows}</tbody></table>` : "") +
      `<div style="font-size:12px;color:var(--tx3);margin-top:6px">${t("source: {{src}}", { src: "/api/displays/system-overview" })}</div>`);
  } catch (e) {
    setHTML("ovr-board", `<div class="ds-banner stale">${t("system overview unavailable")}</div>`);
  }
}

/* ═══ 9. SUBSYSTEM PAGES (L2) — one skeleton × 7 ══════════════════════════ */

/* Per-subsystem composition: schematic symbol, key-param triads, stepper
 * definition, equipment cards. AND table + quick commands + events + dump
 * playback are identical machinery for all seven. */
const L2 = {
  eps: { title: "Electrical power", sym: "sch-eps",
    key: ["0x0101", "0x0105", "0x0100", "0x0109", "0x0102", "0x0135", "0x0120"],
    stepper: () => {
      const stage = Number(paramVal("0x0134"));
      return { label: tText("Load shed ladder"), src: "0x0134",
        states: ["L0 NOMINAL", "L1 PAYLOAD", "L2 NON-ESS", "L3 SURVIVAL"],
        active: Number.isFinite(stage) ? stage : -1 };
    },
    equipment: [["SA-A", "0x0103", "A"], ["SA-B", "0x0104", "A"], ["BATTERY", "0x0101", "%"],
      ["BUS", "0x0105", "V"], ["MPPT", "0x0122", ""], ["LOAD", "0x0148", "A"]] },
  tcs: { title: "Thermal control", sym: "sch-tcs",
    key: ["0x0406", "0x0407", "0x0408", "0x0409", "0x0411", "0x041A"],
    stepper: () => ({ label: tText("FPA cooldown"), src: "0x040C", states: ["OFF", "COOLING", "REGULATING"],
      active: Number(paramVal("0x040C")) > 0 ? (Number(paramVal("0x0425")) > 0 ? 2 : 1) : 0 }),
    equipment: [["HTR BAT", "0x040A", ""], ["HTR OBC", "0x040B", ""], ["COOLER FPA", "0x040C", ""],
      ["HTR THR", "0x041B", ""], ["DUTY BAT", "0x040E", "%"], ["DUTY OBC", "0x040F", "%"]] },
  aocs: { title: "Attitude & orbit control", sym: "sch-aocs",
    key: ["0x0217", "0x0204", "0x0205", "0x0206", "0x025B", "0x0282", "0x02C5"],
    stepper: () => {
      const m = Number(paramVal("0x020F"));
      // states from the catalogue (ultimately aocs/aocs_mode_codes.yaml, which
      // calls itself canonical); AOCS_MODES stays as the pre-fetch fallback.
      const cat = paramStates("0x020F");
      const names = cat ? Object.keys(cat).map(Number).sort((x, y) => x - y).map((k) => cat[String(k)])
                        : AOCS_MODES;
      return { label: tText("AOCS mode chain"), src: "0x020F", states: names,
        active: Number.isFinite(m) ? m : -1 };
    },
    equipment: [["RW1", "0x0207", "RPM"], ["RW2", "0x0208", "RPM"], ["RW3", "0x0209", "RPM"],
      ["RW4", "0x020A", "RPM"], ["ST1", "0x0241", "stars"], ["ST2", "0x0242", "stars"],
      ["GYRO", "0x0273", "°C"], ["GPS", "0x0276", "sats"]] },
  ttc: { title: "Telemetry, tracking & command", sym: "sch-ttc",
    // 0x0502/0x0503/0x050C/0x0519/0x051A are STATION-measured (M1): they
    // come from the ground receiver's monitoring feed (`station_link`), not
    // from the spacecraft, and the note under the card says so.
    key: ["0x0502", "0x0503", "0x050C", "0x0519", "0x051A", "0x050F", "0x0506"],
    stepper: () => {
      const locks = [paramVal("0x0510"), paramVal("0x0511"), paramVal("0x0512")]
        .map((v) => Number(v) >= 1);
      const active = locks[2] ? 3 : locks[1] ? 2 : locks[0] ? 1 : 0;
      return { label: tText("Link lock chain"), src: "0x0510",
        states: [tText("NO SIGNAL"), tText("CARRIER"), "BIT", tText("FRAME")], active };
    },
    equipment: [["XPDR", "0x0507", "°C"], ["PA", "0x050F", "°C"], ["PA ON", "0x0516", ""],
      ["BEACON", "0x0526", ""], ["TIER", "0x0539", ""], ["TIER CMD", "0x053A", ""]] },
  pld: { title: "Payload", sym: "sch-pld",
    key: ["0x0601", "0x0604", "0x0605", "0x0616", "0x0602", "0x060D"],
    stepper: () => ({ label: tText("Instrument state"), src: "0x0600",
      states: ["OFF", "STANDBY", "IMAGING", "CAL", "TRANSFER"],
      active: (() => { const m = Number(paramVal("0x0600")); return Number.isFinite(m) ? Math.min(m, 4) : -1; })() }),
    equipment: [["FPA", "0x0601", "°C"], ["COOLER", "0x0602", "W"], ["STORE", "0x0604", "%"],
      ["IMAGES", "0x0605", ""], ["SNR", "0x0616", "dB"], ["FPA READY", "0x0610", ""]] },
  prp: { title: "Propulsion", sym: "sch-prp",
    key: ["0x0B01", "0x0B03", "0x0B04", "0x0B05", "0x0B0C", "0x0B16"],
    stepper: () => {
      const st2 = Number(paramVal("0x0B0D"));
      return { label: tText("Burn sequence"), src: "0x0B0D",
        states: ["IDLE", "ARMED", "BURNING", "COMPLETE"],
        active: Number.isFinite(st2) ? Math.min(st2, 3) : 0 };
    },
    equipment: [["TANK", "0x0B01", "bar"], ["LATCH A", "0x0B06", ""], ["LATCH B", "0x0B07", ""],
      ["FCV", "0x0B08", ""], ["CATBED", "0x0B05", "°C"], ["INHIBIT", "0x0B15", ""]] },
  obd: { title: "On-board data handling", sym: "sch-obd",
    // 0x0307 tm_pkt_count and the TC counters (2026-08c item 7): the packet
    // counters existed in TM but were shown nowhere on the OBDH page.
    key: ["0x0302", "0x0303", "0x0307", "0x0304", "0x0312", "0x0313", "0x0319", "0x0308"],
    stepper: () => ({ label: tText("Active OBC"), src: "0x030C",
      states: ["OBC-A", "OBC-B"],
      active: Number(paramVal("0x030C")) === 1 ? 1 : 0 }),
    equipment: [["CPU", "0x0302", "%"], ["MEM", "0x0303", "%"], ["HKTM BUF", "0x0312", "%"],
      ["EVT BUF", "0x0313", "%"], ["SEU", "0x0319", ""], ["CAN", "0x0A11", ""],
      ["TM PKTS", "0x0307", ""], ["TC REJ", "0x0306", ""]] },
};

function buildSubsystemPage(pageId) {
  const cfg = L2[pageId];
  const sub = PAGE_SUBSYSTEM[pageId];
  return `
  <!-- l2-* classes (Agent 5 screenshot fix): L2 pages are viewport-fit —
       the two columns scroll internally, the work area itself never
       scrolls (plan §2.1 "L1/L2 fit 1366×768 without scroll"). -->
  <div class="pad hide l2-page" id="page-${pageId}" role="tabpanel" aria-label="${esc(cfg.title)}" data-i18n-aria-label>
    <div class="pghd">
      <div><h1 class="pt" data-i18n>${esc(cfg.title)}</h1>
        <p class="sub"><span data-i18n="Subsystem">Subsystem</span> <span class="mono">${esc(sub)}</span> ·
          <a href="#" data-alarm-filter="${esc(sub)}" data-i18n>alarms for this subsystem</a></p></div>
      <button class="ds-btn ghost" data-page-nav="ovr" data-i18n>← Overview</button>
    </div>
    <div class="g l2-grid">
      <div class="g l2-col">
        ${pageId === "eps" ? `<div class="ds-card"><h2><span data-i18n>Power flow</span>
          <span class="r" data-i18n>arrays to bus to loads and battery; raw values in Parameters below</span></h2>
          <div class="bd" id="eps-flow"><span class="ds-meta" data-i18n>awaiting data…</span></div></div>` : ""}
        ${pageId === "aocs" ? `<div class="ds-card"><h2><span data-i18n>Attitude</span>
          <span class="r" data-i18n>interpreted from the quaternions; raw values in Parameters below</span></h2>
          <div class="bd"><div id="att3d" hidden></div>
            <div id="aocs-att2d"><span class="ds-meta" data-i18n>awaiting data…</span></div></div></div>` : ""}
        <div class="ds-card"><h2 data-i18n>Schematic <span class="r" data-i18n>click a block to navigate; values live</span></h2>
          <div class="bd" id="${pageId}-schematic"></div></div>
        <div class="ds-card"><h2 data-i18n>Parameters <span class="r" data-i18n>AND — generated from /api/param-catalog (P10)</span></h2>
          <div class="bd scroll-y" style="max-height:300px" id="${pageId}-and"></div></div>
        <div class="ds-card"><h2 data-i18n>Stored TM playback <span class="r" data-i18n>S15 dump → /api/tm-dump-data</span></h2>
          <div class="bd" id="${pageId}-dump">
            <div class="row">
              <button class="ds-btn" data-dump-request="${esc(sub)}" data-i18n>REQUEST DUMP (S15)</button>
              <span id="${pageId}-dump-status" style="font-size:12px;color:var(--tx3)"><span data-i18n>no dump loaded</span></span>
            </div>
            <canvas id="${pageId}-dump-chart" height="120" class="hide"></canvas>
            <input type="range" id="${pageId}-dump-scrub" class="hide" style="width:100%" min="0" max="100" value="100"
              aria-label="Playback position" data-i18n-aria-label>
          </div></div>
      </div>
      <div class="g l2-col" style="align-content:start">
        <div class="ds-card"><h2 data-i18n>Key parameters</h2>
          <div class="bd" id="${pageId}-params"></div>
          ${pageId === "ttc" ? `<div class="bd ds-meta" id="ttc-station-note"></div>` : ""}</div>
        ${(DERIVED_BY_PAGE[pageId] || []).length || FIT_PAGES.includes(pageId) ? `
        <div class="ds-card"><h2 data-i18n>Projections <span class="r" data-i18n>ground-derived · not downlinked</span></h2>
          <div class="bd">
            <div id="${pageId}-derived"></div>
          </div></div>` : ""}
        ${pageId === "pld" ? `<div class="ds-card"><h2 data-i18n>Capture readiness (NOM-002)
          <span class="r" data-i18n>gates from display_config.yaml</span></h2>
          <div class="bd">
            <div id="pld-capture"></div>
          </div></div>` : ""}
        ${pageId === "aocs" ? `<div class="ds-card"><h2 data-i18n>FINE-entry readiness
          <span class="r" data-i18n>aocs.fine_ready 0x02C5 decoded</span></h2>
          <div class="bd">
            <div id="aocs-fineready"></div>
          </div></div>
        <div class="ds-card"><h2 data-i18n>Magnetometer &amp; MTQ
          <span class="r" data-i18n>measured B (0x020B-0D) beside the duties it drives</span></h2>
          <div class="bd" id="aocs-magmtq"></div></div>
        <div class="ds-card"><h2 data-i18n>GPS navigation (PVT)
          <span class="r" data-i18n>valid only with a 3D fix — zeros otherwise</span></h2>
          <div class="bd" id="aocs-gpsnav"></div></div>` : ""}
        ${pageId === "obd" ? `<div class="ds-card"><h2 data-i18n>Software state
          <span class="r">obdh.sw_image 0x0311 · obdh.mode 0x0300</span></h2>
          <div class="bd" id="obd-swstate"></div></div>` : ""}
        ${pageId === "prp" ? `<div class="ds-card"><h2 data-i18n>Arm interlocks
          <span class="r" data-i18n>prop.arm_inhibit_mask 0x0B15 decoded</span></h2>
          <div class="bd">
            <div id="prp-inhibit"></div>
          </div></div>
        <div class="ds-card"><h2 data-i18n>Loaded vs planned burn
          <span class="r" data-i18n>TM 0x0B0E/0x0B10 vs planner orbit_manoeuvre</span></h2>
          <div class="bd">
            <div id="prp-burnplan"><span data-i18n>awaiting planner…</span></div>
          </div></div>` : ""}
        ${pageId === "ttc" ? `<div class="ds-card"><h2 data-i18n>Predicted vs measured link
          <span class="r">/api/displays/link-prediction</span></h2>
          <div class="bd">
            <div id="ttc-linkpred-now"></div>
            <canvas id="ttc-linkpred-chart" height="140" class="hide"></canvas>
          </div></div>
        <div class="ds-card"><h2 data-i18n>Blind commanding (CON-004)
          <span class="r" data-i18n>requires FD GO — armed toggle</span></h2>
          <div class="bd">
            <div class="row">
              <button class="ds-btn danger" data-blind-toggle="1" id="ttc-blind-btn">ENABLE BLIND-TC</button>
              <span id="ttc-blind-status" style="font-size:12.5px;color:var(--tx3)"></span>
            </div>
          </div></div>` : ""}
        <div class="ds-card"><h2 id="${pageId}-stepper-title">Mode</h2>
          <div class="bd" id="${pageId}-stepper"></div></div>
        <div class="ds-card"><h2 data-i18n>Equipment</h2>
          <div class="eqg" id="${pageId}-equip"></div></div>
        <div class="ds-card"><h2 data-i18n>Command <span class="r" data-i18n>in place · position-gated (P9)</span></h2>
          <div class="bd" id="${pageId}-quick">
            <div id="${pageId}-quick-list"></div></div></div>
        ${pageId === "ttc" ? `<div class="ds-card"><h2 data-i18n>Ground station network
          <span class="r">/api/ground-stations</span></h2>
          <div class="bd" id="ttc-gs-panel"><span data-i18n>awaiting station list…</span></div></div>` : ""}
        ${pageId === "eps" ? `<div class="ds-card"><h2 data-i18n>Power budget
          <span class="r">/api/displays/power-budget</span></h2>
          <div class="bd" id="eps-power-budget"><span data-i18n>awaiting data…</span></div></div>` : ""}
        <div class="ds-card"><h2 data-i18n>Events</h2>
          <div class="bd scroll-y" style="max-height:180px" id="${pageId}-events"></div></div>
      </div>
    </div>
  </div>`;
}

/* Ground-station network board (classic TTC "GROUND STATION STATUS" panel;
 * Agent 5 inventory fix). Station list from /api/ground-stations; the
 * station currently in contact (state.sa.gs_in_contact / state.in_contact)
 * is marked and carries the live elevation from the geometry params. */
function renderGsNetwork() {
  const host = $("ttc-gs-panel");
  if (!host) return;
  if (!S.groundStations.length) {
    host.innerHTML = `<div class="ds-banner stale">${t("station list unavailable ({{src}})", { src: "/api/ground-stations" })}</div>`;
    return;
  }
  const ls = linkState();
  const activeGs = ls.contact ? ls.gs : null;
  const el = paramVal("0x050A"), rng = paramVal("0x0509"); // ttc.contact_elevation / ttc.range_km
  host.innerHTML = `<table class="plain"><tbody>` + S.groundStations.map((g) => {
    const nm = g.name || g.id || "GS";
    const live = activeGs && nm === activeGs;
    return `<tr${live ? ' class="is-active"' : ""}><td>${live ? renderChip({ kind: "ok", glyph: "lock", label: nm })
        : esc(nm)}</td>
      <td class="mono">${num(g.lat_deg ?? g.lat, 1)}° / ${num(g.lon_deg ?? g.lon, 1)}°</td>
      <td class="mono">${live ? `EL ${num(el, 0)}° · ${num(rng, 0)} km` : `<span class="ds-meta">${t("not in view")}</span>`}</td></tr>`;
  }).join("") + `</tbody></table>`;
}

/* Power budget board (classic EPS tab capability; Agent 5 inventory fix —
 * checklist row "POWER BUDGET board <- /api/displays/power-budget"). */
async function refreshPowerBudget() {
  const host = $("eps-power-budget");
  if (!host || S.page !== "eps") return;
  try {
    const d = await getJSON("/api/displays/power-budget");
    if (!d.has_data) { host.innerHTML = `<div class="ds-banner stale">${t("no power telemetry yet")}</div>`; return; }
    const row = (k2, v) => `<tr><td>${esc(k2)}</td><td class="mono">${v === null || v === undefined || v === "" ? renderNoData() : esc(String(v))}</td></tr>`;
    const per = Object.entries(d.per_subsystem_power || {})
      .map(([k2, v]) => row(k2.toUpperCase(), `${num(v, 1)} W`)).join("");
    host.innerHTML = `<table class="plain"><tbody>` +
      row(tText("GENERATION"), `${num(d.power_gen_w, 1)} W`) +
      row(tText("CONSUMPTION"), `${num(d.power_cons_w, 1)} W`) +
      row(tText("MARGIN"), `${num(d.power_margin_w, 1)} W`) +
      row("SOC", `${num(d.battery_soc_percent, 1)} % (${esc(d.soc_trend || "")})`) +
      row(tText("LOAD SHED"), d.load_shedding_label || null) +
      per + `</tbody></table>` +
      (d.breakdown_note ? `<div style="font-size:12px;color:var(--tx3);margin-top:6px">${esc(d.breakdown_note)}</div>` : "");
  } catch (e) {
    host.innerHTML = `<div class="ds-banner stale">${t("power budget unavailable")}</div>`;
  }
}

function updateSubsystemPage(pageId, full) {
  const cfg = L2[pageId];
  const sub = PAGE_SUBSYSTEM[pageId];
  const host = $(`${pageId}-schematic`);
  if (host && !host.dataset.mounted && schematicsDoc) {
    host.innerHTML = schematicMarkup(cfg.sym);
    host.dataset.mounted = "1";
    I18n.applyDom(host);          // SVG <text data-i18n> in the mounted symbol
  }
  bindPageSchematic(pageId);
  if (PIC && (pageId === "eps" || pageId === "aocs")) PIC.render(pageId);
  // key param triads + embedded sparklines
  setHTML(`${pageId}-params`, cfg.key.map((h) =>
    `<div class="kp">${paramTriad(h)}${spark(h)}</div>`).join(""));
  if (pageId === "ttc") setHTML("ttc-station-note", stationLinkNote());
  // stepper (ONE component for all chains — P5)
  const stp = cfg.stepper();
  // A chain widget reads as "this IS the state right now". Without a staleness
  // check it kept asserting the last known step forever after its driving
  // parameter went silent (field report 2026-08-20) -- the most confident
  // possible way to show nothing.
  const stpFr = stp.src ? paramFreshness(stp.src) : "fresh";
  const stpDead = stpFr === "stale" || stpFr === "disabled";
  setHTML(`${pageId}-stepper-title`, esc(stp.label) + (stpDead
    ? " " + renderChip(stpFr === "disabled" ? { kind: "off", label: tText("HK disabled (TC 3,5)") }
                                            : { kind: "stale", label: tText("stale") }) : ""));
  setHTML(`${pageId}-stepper`,
    renderStepper(stp.states, stpDead ? -1 : stp.active));
  // equipment cards
  // Equipment: a hairline grid of shared readouts (stale keeps the last
  // value with its age; never received reads "no data").
  setHTML(`${pageId}-equip`, cfg.equipment.map(([nm, h, u]) =>
    `<div class="eq"><span class="nm">${esc(nm)}<span class="hexid">${esc(h)}</span></span>` +
    `${valueCell(h, 1, u)}</div>`).join(""));
  // AND table from the catalog (never drifts from the dictionary).
  //
  // Field report 2026-08-20: "in the AOCS tab with the list of parameters I
  // have aocs.mode as 2 ... and the display at the top of the AOCS page says
  // AOCS CORE MODE 3". Both read the SAME telemetry dict -- the table was
  // simply rebuilt only when `full` was set, which happens on navigation, so
  // it froze at the values present when the page was opened while the
  // schematic kept updating every second. Two numbers, one source, one of them
  // minutes old. Its Age column froze with it, so it never even aged into
  // looking stale. Same defect as the DIAG panels, same treatment.
  const andParams = S.paramCatalog.filter((p) => p.subsystem === sub);
  if (full) {
    setHTML(`${pageId}-and`, renderAndTable(andParams, liveValues()));
    renderQuickCommands();
  } else {
    refreshAndTable(pageId, andParams);
  }
  // POSITION_NEEDS gap surfaces on their owning pages
  renderDerivedCard(pageId);                                     // G1 + G3
  if (pageId === "aocs") setHTML("aocs-fineready",
    renderBitmaskChips("0x02C5", { clearLabel: tText("READY FOR FINE") }));   // G2
  if (pageId === "aocs") { renderMagMtq(); renderGpsNav(); }     // 2026-08c 1+2
  if (pageId === "obd") renderObdSwState();                      // 2026-08c 7
  if (pageId === "prp") {
    setHTML("prp-inhibit",
      renderBitmaskChips("0x0B15", { clearLabel: tText("ARM PERMITTED") }));  // G2
    renderBurnCard();                                            // G9
  }
  if (pageId === "pld") renderCaptureCard();                     // G4 (+G2)
  if (pageId === "ttc") { renderBlindTc(); renderLinkOverlay(); } // G12 + G5
  if (pageId === "ttc") renderGsNetwork();
  setHTML(`${pageId}-events`, (S.subsysEvents[sub] || []).slice(-30).reverse()
    .map((e) => `<div class="logrow">${esc(e)}</div>`).join("") ||
    `<div class="logrow nom">${t("No events")}</div>`);
}

/* Two-column readout table: label + hex, value + unit (restored 2026-11-01
 * from cff5046 with the shared value cell, so stale/no-data read the same
 * as everywhere else). */
function readoutRows(rows) {
  return `<table class="plain"><tbody>` + rows.map(([k, h, u, d]) =>
    `<tr><td>${esc(k)} <span class="mono hexid">${esc(h)}</span></td>
      <td class="mono num">${valueCell(h, d, u)}</td></tr>`).join("") + `</tbody></table>`;
}

/* — 2026-08c item 1: measured field beside the MTQ duties it drives — */
function renderMagMtq() {
  const host = $("aocs-magmtq");
  if (!host) return;
  const valid = Number(paramVal("0x025C")) >= 1;
  host.innerHTML =
    `<p class="note${valid ? "" : " bad"}">${valid
      ? t("MAG VALID — measured body-frame field (IGRF + bias + noise)")
      : t("MAG INVALID (unit off / failed / AOCS dark) — B reads 0, B-dot is blind")}
      · ${t("single-string unit, no redundant B mag")}</p>` +
    readoutRows([["Bx", "0x020B", "nT", 0], ["By", "0x020C", "nT", 0],
      ["Bz", "0x020D", "nT", 0], ["|B|", "0x0277", "nT", 0],
      [tText("MTQ X duty"), "0x0258", "%", 1], [tText("MTQ Y duty"), "0x0259", "%", 1],
      [tText("MTQ Z duty"), "0x025A", "%", 1], [tText("MTQ enabled"), "0x025E", "", 0]]);
}

/* — 2026-08c item 2: GPS receiver PVT (LEOP-003 orbit determination) — */
function renderGpsNav() {
  const host = $("aocs-gpsnav");
  if (!host) return;
  const fix = Number(paramVal("0x0274"));
  const FIX = ["NO FIX", "2D", "3D", "3D+VEL"];
  const ok = fix >= 2;
  host.innerHTML =
    `<p class="note${ok ? "" : " warn"}">${t("FIX {{fix}} · {{n}} sats · PDOP {{pdop}}",
      { fix: FIX[fix] || "—", n: num(paramVal("0x0276"), 0), pdop: num(paramVal("0x0275"), 1) })}${ok ? ""
      : " — " + t("position and velocity read zero until the receiver holds a 3D fix")}</p>` +
    readoutRows([[tText("Latitude"), "0x0210", "°", 3], [tText("Longitude"), "0x0211", "°", 3],
      [tText("Altitude"), "0x0212", "km", 1],
      ["ECEF X", "0x0231", "m", 0], ["ECEF Y", "0x0232", "m", 0], ["ECEF Z", "0x0233", "m", 0],
      ["Vel X", "0x0234", "m/s", 1], ["Vel Y", "0x0235", "m/s", 1], ["Vel Z", "0x0236", "m/s", 1]]);
}

/* — 2026-08c item 7: OBDH software state (bootloader vs application) — */
function renderObdSwState() {
  const host = $("obd-swstate");
  if (!host) return;
  const img = Number(paramVal("0x0311"));
  const mode = Number(paramVal("0x0300"));
  const MODES = ["NOMINAL", "SAFE", "EMERGENCY"];
  const ND = renderNoData();
  const imgLabel = img === 0 ? "BOOTLOADER" : img === 1 ? "APPLICATION" : ND;
  const modeLabel = MODES[mode] ?? (Number.isFinite(mode) ? `MODE_${mode}` : ND);
  /* Boot progress (0x0A15 / 0x0A16). OBC_BOOT_APP's S1.7 lands when the
     10 s CRC window CLOSES, so the window itself has to be visible: sw_image
     alone reads 0 both for "in the bootloader" and for "boot in flight". */
  const bstate = Number(paramVal("0x0A15"));
  const bleft = Number(paramVal("0x0A16"));
  const BOOT_STATES = ["BOOTLOADER", "VERIFYING", "APPLICATION", "FAILED"];
  const bootLabel = BOOT_STATES[bstate] ?? ND;
  const booting = bstate === 1;
  const bootFailed = bstate === 3;
  const bad = mode >= 1 || img === 0;
  const row = (k, h, v, cls) => `<tr><td>${esc(k)} <span class="mono hexid">${h}</span></td>
    <td class="mono${cls ? " " + cls : ""}">${v}</td></tr>`;
  host.innerHTML =
    `<table class="plain"><tbody>` +
    row(tText("Running image"), "0x0311", imgLabel, img === 0 ? "v-warn" : "") +
    row(tText("Boot state"), "0x0A15",
      bootLabel + (booting && Number.isFinite(bleft) ? " · " + tText("{{s}} s left", { s: num(bleft, 0) }) : ""),
      bootFailed ? "v-alarm" : booting ? "v-warn" : "") +
    row(tText("OBC mode"), "0x0300", modeLabel, mode >= 1 ? "v-alarm" : "") +
    row(tText("Active OBC"), "0x030C", Number(paramVal("0x030C")) === 1 ? "OBC-B" : "OBC-A") +
    row(tText("Reboot count"), "0x030A", num(paramVal("0x030A"), 0)) +
    `</tbody></table>` +
    (booting ? `<p class="note warn">${t("Application boot in progress — the OBC is verifying the image CRC. Only the bootloader TC subset is accepted until it finishes; the S1.7 for OBC_BOOT_APP arrives when it does.")}</p>` : "") +
    (bootFailed ? `<p class="note bad">${t("Last OBC_BOOT_APP failed its image CRC — see the BOOT_FAILURE event. The OBC is held in the bootloader.")}</p>` : "") +
    (bad ? `<p class="note warn">${img === 0 && !booting
      ? t("Bootloader: minimal TC subset, UHF beacon only — send OBC_BOOT_APP (S8 func 55) to run the application.") + " " : ""}${mode >= 1
      ? t("OBC in {{mode}} — the contingency banner is driven from this parameter (M8).", { mode: modeLabel }) : ""}</p>` : "");
}

/* ═══ 9b. POSITION-NEEDS GAP SURFACES (G1–G9, G12, G15) ═══════════════════ */
/* The L3 tier POSITION_NEEDS §6 found missing: ground-derived projections
 * (G1), bitmask decoders (G2), fit verdict (G3), capture-readiness composite
 * (G4), predicted-vs-measured link (G5), first-out alarm grouping (G6),
 * GO/NO-GO call-matrix context (G7), console log (G8), loaded-vs-planned
 * burn (G9), blind-TC tracking (G12), baseline-vs-now health (G15).
 * Everything here renders honest absence: a missing endpoint, an invalid
 * projection or an unreachable planner is a designed state with a reason,
 * never a fabricated number. */

/* — G1: derived-parameter rows (server block `state.derived`, 0x0803-0x080A) — */
const DERIVED_BY_PAGE = {
  eps: ["eps.soc_at_eclipse_exit_pred", "eps.time_to_soc_yellow"],
  aocs: ["aocs.time_to_mom_70pct"],
  obd: ["obdh.time_to_buf_full", "obdh.time_offset_ms"],
  ttc: ["ttc.pass_data_capacity_bytes"],
  prp: ["prop.catbed_ready_eta"],
};
const FIT_PAGES = ["ttc", "pld"];           // G3 verdict line lives here
// English text is the i18n key: display via tText(DERIVED_LABELS[name]).
const DERIVED_LABELS = {
  "eps.soc_at_eclipse_exit_pred": "SoC at eclipse exit (predicted)",
  "eps.time_to_soc_yellow": "Time to SoC yellow limit",
  "aocs.time_to_mom_70pct": "Time to 70 % momentum",
  "obdh.time_to_buf_full": "Time to buffer full",
  "obdh.time_offset_ms": "OBC − ground time offset",
  "ttc.pass_data_capacity_bytes": "Pass data capacity",
  "prop.catbed_ready_eta": "Catbed ready ETA",
  "ttc.pass_fit_ratio": "Pass fit ratio",
};
export function derivedEntry(name) {
  const d = S.state.derived;
  return (d && d[name]) ? d[name] : null;
}
export function fmtDerivedValue(ent) {
  if (!ent || !ent.valid || ent.value === null || ent.value === undefined) return "—";
  const v = Number(ent.value);
  const u = String(ent.units || "");
  if (u === "s") return fmtAge(v);
  if (u === "bytes") return v >= 1e6 ? `${(v / 1e6).toFixed(1)} MB` : `${Math.round(v / 1e3)} kB`;
  if (u === "ms") return `${num(v, 0)} ms`;
  if (u === "ratio") return num(v, 2);
  return `${num(v, 1)}${u ? " " + u : ""}`;
}
const GND_MARK = (id) =>
  `<span class="ds-badge" title="${t("ground-derived {{id}} — computed by the MCS from archive trend + orbit state; NOT downlinked from the spacecraft",
    { id: id || "0x08xx" })}">${t("GND")}</span>`;
export function renderDerivedRow(name) {
  const ent = derivedEntry(name);
  const label = DERIVED_LABELS[name] ? tText(DERIVED_LABELS[name]) : name;
  if (!ent) {
    return `<div class="logrow nom">${t("{{label}} — no derived block in /api/state (server predates POSITION_NEEDS G1?)",
      { label })}</div>`;
  }
  const head = `<span style="font-size:12px;color:var(--tx3)">${esc(label)} ` +
               `<span class="mono">${esc(ent.id)}</span></span>`;
  if (!ent.valid) {
    // The server NEVER sends a number when invalid; say why, prominently.
    return `<div class="row derived-row" style="justify-content:space-between;gap:6px">
      ${head}
      <span style="font-size:12px;color:var(--stale)">${t("INVALID — {{reason}}", { reason: ent.reason || tText("no reason given") })}
        ${GND_MARK(ent.id)}</span></div>`;
  }
  return `<div class="row derived-row" style="justify-content:space-between;gap:6px">
    ${head}
    <span class="mono" style="font-size:14px;font-weight:600">${fmtDerivedValue(ent)}
      ${GND_MARK(ent.id)}</span></div>`;
}
/* — G3: the "will it fit" verdict line — */
export function fitVerdictLine() {
  const ent = derivedEntry("ttc.pass_fit_ratio");
  if (!ent) return `<div class="logrow nom">${t("PASS FIT — no derived block")}</div>`;
  if (!ent.valid) {
    return `<div class="logrow" style="color:var(--stale)">${t("PASS FIT — INVALID: {{reason}}", { reason: ent.reason || "" })}` +
           ` ${GND_MARK(ent.id)}</div>`;
  }
  const r = Number(ent.value);
  const wont = r > 1.0;
  const tight = !wont && r > 0.9;
  const chip = renderChip({
    kind: wont ? "alarm" : tight ? "warn" : "ok",
    label: wont ? tText("will NOT fit") : tight ? tText("fits (tight)") : tText("fits"),
    title: tText("backlog ÷ (tier rate × time to LOS); > 1.0 means the queued data will not move this pass"),
  });
  return `<div class="row" style="gap:8px;align-items:center">
    <span class="mono" style="font-size:14px;font-weight:600">${t("PASS FIT {{r}}", { r: num(r, 2) })}</span>
    ${chip} ${GND_MARK(ent.id)}</div>`;
}
function renderDerivedCard(pageId) {
  const host = $(`${pageId}-derived`);
  if (!host) return;
  const rows = (DERIVED_BY_PAGE[pageId] || []).map(renderDerivedRow).join("");
  const fit = FIT_PAGES.includes(pageId) ? fitVerdictLine() : "";
  host.innerHTML = rows + fit ||
    `<div class="logrow nom">${t("no projections for this subsystem")}</div>`;
}

/* — G2: bitmask decoders (0x02C5 fine_ready, 0x0B15 arm_inhibit_mask) —
 * The bit legends ARE parsed from the served /api/param-catalog descriptions
 * (decision per POSITION_NEEDS G2: both descriptions follow the "bitN label,
 * bitN label" / "bN label" convention and are the single source of truth —
 * a separate config table would drift from the dictionary). */
export function parseBitLegend(description) {
  const s = String(description || "");
  const re = /\b(?:bit|b)(\d+)\b[ :=-]*/g;
  const marks = [];
  let m;
  while ((m = re.exec(s))) marks.push({ bit: Number(m[1]), end: re.lastIndex, start: m.index });
  const out = [];
  for (let i = 0; i < marks.length; i++) {
    let label = s.slice(marks[i].end, i + 1 < marks.length ? marks[i + 1].start : s.length);
    // strip teaching parentheticals (kept in the catalogue, too long for a chip)
    label = label.replace(/\s*\(([^)]{25,})\)/g, "");
    label = label.replace(/[,;.\s]+$/, "").replace(/^[,;\s]+/, "").trim();
    if (label) out.push({ bit: marks[i].bit, label });
  }
  return out;
}
export function renderBitmaskChips(hexId, opts = {}) {
  const def = S.paramByHex[hexId] || {};
  const legend = parseBitLegend(def.description);
  if (!legend.length) {
    return `<div class="ds-banner stale">${t("no bit legend in the parameter catalogue for {{id}} — cannot decode",
      { id: hexId })}</div>`;
  }
  const raw = paramVal(hexId);
  const stale = paramIsStale(hexId);
  if (raw === undefined || raw === null || stale) {
    return `<div class="ds-banner stale">${t("{{name}} not in current TM ({{why}}) — chips withheld rather than guessed",
      { name: def.name || hexId, why: stale ? tText("stale") : tText("never seen") })}</div>`;
  }
  const mask = Number(raw) >>> 0;
  const legendMask = legend.reduce((a, b) => a | (1 << b.bit), 0);
  const allClear = (mask & legendMask) === 0;
  const chips = legend.map((b) => {
    const set = (mask >> b.bit) & 1;
    return renderChip({ kind: set ? "alarm" : "ok",
      label: `b${b.bit} ${b.label}`,
      title: set ? tText("bit {{n}} SET — {{label}} is blocking/failing", { n: b.bit, label: b.label })
                 : tText("bit {{n}} clear — {{label}} OK", { n: b.bit, label: b.label }) });
  }).join(" ");
  const verdict = renderChip({ kind: allClear ? "ok" : "alarm",
    label: allClear ? (opts.clearLabel || tText("ALL CLEAR"))
      : tText("{{count}} BLOCKING", { count: countBits(mask & legendMask) }) });
  return `<div class="row" style="gap:6px;margin-bottom:6px">
      <span class="mono" style="font-size:13px">${esc(def.name || hexId)} = 0x${mask.toString(16).toUpperCase().padStart(4, "0")}</span>
      ${verdict}</div>
    <div class="row" style="gap:4px">${chips}</div>`;
}
function countBits(v) { let n = 0; for (let x = v >>> 0; x; x >>= 1) n += x & 1; return n; }

/* — G4: capture-readiness composite (NOM-002 gates, table in
 *      display_config.yaml capture_gates so ops can tune it) — */
export function captureGateTable() {
  const g = (S.displayConfig || {}).capture_gates;
  return Array.isArray(g) ? g : [];
}
export function evalCaptureGate(g) {
  const v = paramVal(g.param);
  const stale = paramIsStale(g.param);
  if (v === undefined || v === null || stale) {
    return { state: "unknown", actual: null,
             why: stale ? tText("telemetry stale") : tText("parameter not in TM") };
  }
  const n = Number(v);
  let pass = false;
  const val = Number(g.value);
  switch (String(g.op)) {
    case "eq": pass = n === val; break;
    case "ne": pass = n !== val; break;
    case "gt": pass = n > val; break;
    case "ge": pass = n >= val; break;
    case "lt": pass = n < val; break;
    case "le": pass = n <= val; break;
    case "range": pass = n >= Number(g.min) && n <= Number(g.max); break;
    default: return { state: "unknown", actual: n, why: tText("unknown op {{op}}", { op: String(g.op) }) };
  }
  return { state: pass ? "pass" : "fail", actual: n };
}
export function computeCaptureReadiness() {
  const gates = captureGateTable();
  if (!gates.length) return { available: false };
  const rows = gates.map((g) => ({ ...g, ...evalCaptureGate(g) }));
  const composite = rows.some((r) => r.state === "fail") ? "NO-GO"
    : rows.some((r) => r.state === "unknown") ? "UNKNOWN" : "GO";
  return { available: true, rows, composite };
}
function renderCaptureCard() {
  const host = $("pld-capture");
  if (!host) return;
  const c = computeCaptureReadiness();
  if (!c.available) {
    host.innerHTML = `<div class="ds-banner stale">${t("no gate table — add {{key}} to {{file}}",
      { key: "capture_gates", file: "configs/<mission>/mcs/display_config.yaml" })}</div>`;
    return;
  }
  const chips = c.rows.map((r) => renderChip({
    kind: r.state === "pass" ? "ok" : r.state === "fail" ? "alarm" : "stale",
    label: `${r.label || r.param}${r.actual === null ? "" : ` = ${num(r.actual, 1)}`}`,
    title: r.why || `${r.param} ${r.op} ${r.value ?? `${r.min}…${r.max}`}` })).join(" ");
  const cls = c.composite === "GO" ? "var(--ok)"
    : c.composite === "NO-GO" ? "var(--alarm)" : "var(--stale)";
  host.innerHTML = `
    <div class="row" style="gap:10px;align-items:center;margin-bottom:6px">
      <span class="mono" style="font-size:18px;font-weight:700;color:${cls}">${c.composite === "UNKNOWN" ? t("UNKNOWN") : c.composite}</span>
      <span style="font-size:12px;color:var(--tx3)">${t("capture readiness — all gates from three subsystems, one verdict")}</span>
    </div>
    <div class="row" style="gap:4px">${chips}</div>
    <div style="margin-top:8px;font-size:12px;color:var(--tx3)">${t("FINE-entry preconditions (aocs.fine_ready — PL4: bit4 set means a desat is coming):")}</div>
    ${renderBitmaskChips("0x02C5", { clearLabel: tText("READY FOR FINE") })}`;
}

/* — G5: predicted-vs-measured link overlay (TTC page) — */
async function loadLinkPrediction() {
  if (S.page !== "ttc") return;
  try { S.linkPred = await getJSON("/api/displays/link-prediction"); }
  catch (e) { S.linkPred = { available: false, reason: tText("link-prediction endpoint unreachable") }; }
  renderLinkOverlay();
}
export function linkNowReadout() {
  const lp = S.linkPred;
  if (!lp || !lp.available) {
    return { available: false, reason: (lp && lp.reason) || tText("no prediction loaded") };
  }
  const tierIdx = Number(paramVal("0x0539"));
  const tierName = ["SAFE", "LOW", "HIGH"][tierIdx] ||
    ((lp.tiers && lp.tiers[0]) ? lp.tiers[0].name : "LOW");
  const nowP = lp.now;
  const predicted = nowP && nowP.tiers && nowP.tiers[tierName]
    ? Number(nowP.tiers[tierName].eb_n0_db) : null;
  const measured = Number(paramVal("0x0519"));
  const haveMeasured = Number.isFinite(measured) &&
    !paramIsStale("0x0519");
  return {
    available: true, tierName,
    predicted: Number.isFinite(predicted) ? predicted : null,
    measured: haveMeasured ? measured : null,
    delta: Number.isFinite(predicted) && haveMeasured ? measured - predicted : null,
    pass: lp.pass || null,
  };
}
function renderLinkOverlay() {
  const host = $("ttc-linkpred-now");
  if (!host) return;
  const r = linkNowReadout();
  if (!r.available) {
    host.innerHTML = `<div class="ds-banner stale">${t("prediction unavailable — {{reason}}", { reason: r.reason })}</div>`;
    const cv0 = $("ttc-linkpred-chart");
    if (cv0) cv0.classList.add("hide");
    return;
  }
  const dChip = r.delta === null ? "" : renderChip({
    kind: r.delta < -6 ? "alarm" : r.delta < -3 ? "warn" : "ok",
    label: `Δ ${r.delta >= 0 ? "+" : ""}${num(r.delta, 1)} dB`,
    title: tText("measured minus predicted Eb/N0 at the current geometry — a large negative delta is a real loss (pointing, weather, hardware), not physics") });
  host.innerHTML = `
    <div class="row" style="gap:8px;font-size:13px">
      <span>${t("{{gs}} {{which}} pass · tier {{tier}}",
        { gs: (r.pass || {}).gs_name || "", which: (r.pass || {}).which || "", tier: String(r.tierName) })}</span>
      <span class="mono">${t("predicted-now {{v}}",
        { v: r.predicted === null ? tText("— (not in pass)") : num(r.predicted, 1) + " dB" })}</span>
      <span class="mono">${t("measured-now {{v}}", { v: r.measured === null ? "—" : num(r.measured, 1) + " dB" })}</span>
      ${dChip}
    </div>`;
  drawLinkOverlayChart();
}
let linkChart = null;
function drawLinkOverlayChart() {
  const cv = $("ttc-linkpred-chart");
  if (!cv) return;
  const lp = S.linkPred;
  if (typeof Chart === "undefined" || !lp || !lp.available) {
    cv.classList.add("hide");
    return;   // the now-readout above is the vendor-guard fallback
  }
  cv.classList.remove("hide");
  const series = (lp.series && lp.series.eb_n0_db) || {};
  const r = linkNowReadout();
  const pred = series[r.tierName] || [];
  const datasets = [
    { label: tText("predicted Eb/N0 ({{tier}})", { tier: r.tierName }), pointRadius: 0, borderWidth: 1.2,
      borderDash: [5, 4], borderColor: "#8A93A0",
      data: pred.map((p) => ({ x: p[0] * 1000, y: p[1] })) },
    { label: tText("measured Eb/N0 (0x0519)"), pointRadius: 1.5, borderWidth: 1.5,
      borderColor: "#E6E9ED", showLine: true,
      data: S.linkMeasured.map((p) => ({ x: p.t * 1000, y: p.eb })) },
  ];
  if (linkChart) linkChart.destroy();
  linkChart = new Chart(cv.getContext("2d"), {
    type: "line", data: { datasets },
    options: { animation: false,
      scales: { x: { type: "linear", ticks: { callback: (v) => fmtUTC(v / 1000) } } },
      plugins: { legend: { labels: { boxWidth: 10 } } } },
  });
}

/* — G6: first-out alarm grouping from /api/fault-graph — */
async function loadFaultGraph() {
  try { S.faultGraph = await getJSON("/api/fault-graph"); }
  catch (e) { S.faultGraph = null; }
}
export function groupAlarmsByAncestry(alarms, graph, minSize = 4) {
  const rest = alarms.slice();
  if (!graph || !graph.available || !Array.isArray(graph.edges) || !graph.edges.length) {
    return { groups: [], rest };
  }
  const byParam = {};
  for (const n of graph.nodes || []) if (n.param_id) byParam[n.param_id] = n;
  // transitive descendant sets (graph is small — tens of nodes)
  const children = {};
  for (const e of graph.edges) (children[e.parent] = children[e.parent] || []).push(e.child);
  const desc = {};
  for (const id of Object.keys(children)) {
    const seen = new Set();
    const stack = [...children[id]];
    while (stack.length) {
      const c = stack.pop();
      if (seen.has(c)) continue;
      seen.add(c);
      for (const g of children[c] || []) stack.push(g);
    }
    desc[id] = seen;
  }
  const active = alarms.filter((a) => !a.rtn);
  const entries = active
    .map((a) => ({ a, n: alarmParamHex(a) ? byParam[alarmParamHex(a)] : null }))
    .filter((e) => e.n);
  // roots with the MOST active descendants claim their cascade first
  const activeDescCount = (e) => {
    const d = desc[e.n.id];
    return d ? entries.filter((o) => o !== e && d.has(o.n.id)).length : 0;
  };
  entries.sort((x, y) => activeDescCount(y) - activeDescCount(x));
  const used = new Set();
  const groups = [];
  for (const e of entries) {
    if (used.has(e.a.id)) continue;
    const d = desc[e.n.id];
    if (!d) continue;
    const cons = entries.filter((o) => o !== e && !used.has(o.a.id) && d.has(o.n.id));
    if (1 + cons.length >= minSize) {
      groups.push({ root: e.a, rootNode: e.n, consequents: cons.map((c) => c.a) });
      used.add(e.a.id);
      for (const c of cons) used.add(c.a.id);
    }
  }
  return { groups, rest: alarms.filter((a) => !used.has(a.id)) };
}

/* — G7: GO/NO-GO call-matrix context — */
async function loadGonogoMatrix() {
  try { S.gonogoMatrix = await getJSON("/api/gonogo-matrix"); }
  catch (e) { S.gonogoMatrix = null; }
}
export function matchGonogoRow(label) {
  const rows = (S.gonogoMatrix && S.gonogoMatrix.matrix) || [];
  const l = String(label || "").toLowerCase();
  if (!l || !rows.length) return null;
  let best = null, bestScore = 0;
  for (const r of rows) {
    const toks = String(r.situation || "").toLowerCase()
      .split(/[^a-z0-9]+/).filter((t) => t.length > 2);
    const score = toks.filter((t) => l.includes(t)).length;
    if (score > bestScore) { bestScore = score; best = r; }
  }
  return bestScore >= 1 ? best : null;
}
export function renderGonogoMatrixRow(label) {
  if (S.gonogoMatrix && S.gonogoMatrix.available === false) {
    return `<div class="logrow nom">${t("call matrix unavailable — {{reason}}", { reason: S.gonogoMatrix.reason || "" })}</div>`;
  }
  const row = matchGonogoRow(label);     // matching runs on the English config text
  if (!row) {
    return `<div class="logrow nom">${t("no matching call-matrix row for this poll — free-form poll; FD arbitrates per manual/10_desk_procedures.md")}</div>`;
  }
  const who = (p) => (POSITION_INFO[p] ? tText(POSITION_INFO[p].title) : String(p).toUpperCase());
  const responders = (Array.isArray(row.who_responds) ? row.who_responds : [row.who_responds])
    .map(who).join(", ");
  // YAML-overlay key gonogo:<who_calls>.<row index>:<field> (configs/<mission>/i18n)
  const gk = `gonogo:${row.who_calls}.${((S.gonogoMatrix && S.gonogoMatrix.matrix) || []).indexOf(row)}`;
  return `<div class="ds-card" style="margin-top:6px"><div class="bd" style="font-size:12.5px">
    <b>${esc(tdb(`${gk}:situation`, row.situation))}</b>${row.critical ? " " + renderChip({ kind: "alarm", label: tText("CRITICAL") }) : ""}<br>
    ${t("calls: <b>{{who}}</b> · must respond: <b>{{resp}}</b>", { who: who(row.who_calls), resp: responders })}<br>
    FD: ${esc(row.fd_decision ? tdb(`${gk}:fd_decision`, row.fd_decision) : "")}
    <div style="color:var(--tx3);margin-top:2px">${t("source: {{src}}", { src: "/api/gonogo-matrix (mcs/gonogo_matrix.yaml)" })}</div>
  </div></div>`;
}

/* — G8: console / mission log (LOG drawer tab) — */
async function loadConsoleLog() {
  try {
    const d = await getJSON("/api/console-log?limit=300");
    S.consoleLog = d.entries || [];
  } catch (e) { /* keep previous */ }
  if (bdTab === "conlog") renderConsoleLog();
}
export function renderConsoleLog() {
  const host = $("conlog-list");
  if (!host) return;
  const k = S.conlogKind;
  const rows = S.consoleLog
    .filter((e) => k === "all" || e.kind === k)
    .slice(-200).reverse()
    .map((e) => {
      const cls = e.kind === "gonogo" ? "warn" : e.kind === "mark" ? "nom" : "";
      return `<div class="logrow ${cls}">${fmtUTC(e.utc_epoch, { seconds: true })} ` +
        `[${esc((e.kind || "").toUpperCase())}]` +
        `${e.position ? ` [${esc(e.position)}]` : ""}` +
        `${e.source === "server" ? ` <span class="ds-badge">AUTO</span>` : ""} ` +
        `${esc(e.text || "")}${e.ref ? ` <span class="mono">(${esc(e.ref)})</span>` : ""}</div>`;
    }).join("");
  host.innerHTML = rows || `<div class="logrow nom">${t("console log empty — TC sends, verdicts, acks and GO/NO-GO results are appended by the server; MARK and notes by you")}</div>`;
}
async function postConsoleEntry(kind) {
  const el = $("conlog-input");
  const typed = el ? el.value.trim() : "";
  const text = kind === "mark" ? (typed || "MARK") : typed;
  if (!text) { announce(tText("console log: type a note first")); return; }
  const r = await postJSON("/api/console-log",
    { position: S.position, kind, text });
  if (r.ok && el) el.value = "";
  announce(r.ok ? tText("logged ({{kind}})", { kind }) : tText("console log rejected ({{status}})", { status: r.status }));
  await loadConsoleLog();
  renderConsoleLog();
}

/* — G9: loaded-vs-planned burn card (PROP page) — */
export function plannedBurnDv(activity) {
  if (!activity) return NaN;
  return Number(activity.dv_mps ?? activity.dv ?? activity.delta_v_mps ?? activity.delta_v);
}
export function burnMismatch(tmDv, plannedDv) {
  if (!Number.isFinite(tmDv) || !Number.isFinite(plannedDv)) return null;
  return Math.abs(tmDv - plannedDv) > Math.max(0.05, 0.05 * Math.abs(plannedDv));
}
async function loadBurnPlan() {
  if (S.page !== "prp") return;
  const base = S.clientConfig.planner_url;
  if (!base) {
    S.burnPlan = { available: false,
      reason: tText("planner_url not configured — confirm the burn plan by voice with FDS") };
    renderBurnCard();
    return;
  }
  try {
    const d = await getJSON(`${base}/api/schedule`);
    const acts = (d.schedule || []).filter((a) => a.name === "orbit_manoeuvre");
    // prefer the next PLANNED manoeuvre; else the most recent one
    const next = acts.find((a) => a.state_name === "PLANNED") || acts[acts.length - 1] || null;
    S.burnPlan = { available: true, activity: next, count: acts.length };
  } catch (e) {
    // planner down (the same-origin /planner proxy answers 502) is a
    // DESIGNED absent state (G9)
    S.burnPlan = { available: false,
      reason: tText("planner unreachable — confirm the burn plan by voice with FDS") };
  }
  renderBurnCard();
}
function renderBurnCard() {
  const host = $("prp-burnplan");
  if (!host) return;
  const dvTm = Number(paramVal("0x0B0E"));
  const tTm = Number(paramVal("0x0B10"));
  const tmStale = paramIsStale("0x0B0E");
  const tmRow = `<tr><td>${t("LOADED (TM)")}</td>
    <td class="mono">${tmStale || !Number.isFinite(dvTm) ? "—" : num(dvTm, 2) + " m/s"}</td>
    <td class="mono">${tmStale || !Number.isFinite(tTm) ? "—" : t("{{s}} s burn", { s: num(tTm, 0) })}</td>
    <td class="mono">0x0B0E / 0x0B10</td></tr>`;
  const bp = S.burnPlan;
  if (!bp) { host.innerHTML = `<table class="plain"><tbody>${tmRow}</tbody></table>` +
    `<div class="logrow nom">${t("planner not queried yet…")}</div>`; return; }
  if (!bp.available) {
    host.innerHTML = `<table class="plain"><tbody>${tmRow}</tbody></table>` +
      `<div class="ds-banner stale">${esc(bp.reason)}</div>`;
    return;
  }
  if (!bp.activity) {
    host.innerHTML = `<table class="plain"><tbody>${tmRow}</tbody></table>` +
      `<div class="logrow nom">${t("no orbit_manoeuvre activity in the plan")}` +
      `${Number.isFinite(dvTm) && dvTm > 0 && !tmStale
        ? " — " + t("a burn is LOADED on board with nothing planned: query FDS")
        : ""}</div>`;
    return;
  }
  const a = bp.activity;
  const dvPlan = plannedBurnDv(a);
  const planRow = `<tr><td>${t("PLANNED (FDS)")}</td>
    <td class="mono">${Number.isFinite(dvPlan) ? num(dvPlan, 2) + " m/s" : t("— (no ΔV in activity)")}</td>
    <td class="mono">${a.start_time ? esc(String(a.start_time)) : "—"}</td>
    <td class="mono">${esc(a.procedure_ref || "")} #${a.id ?? "—"} ${esc(a.state_name || "")}</td></tr>`;
  const mism = burnMismatch(dvTm, dvPlan);
  const verdict = mism === null
    ? `<div class="logrow nom">${t("not comparable — {{why}}; cross-check with FDS on the loop",
        { why: tmStale || !Number.isFinite(dvTm) ? tText("no burn loaded in TM") : tText("activity carries no ΔV value") })}</div>`
    : mism
      ? `<div class="ds-banner alarm">${t("MISMATCH — loaded ΔV {{tm}} m/s ≠ planned {{plan}} m/s. Do NOT arm until FDS confirms which is right (PR4).",
          { tm: num(dvTm, 2), plan: num(dvPlan, 2) })}</div>`
      : `<div class="row" style="margin-top:4px">${renderChip({ kind: "ok", label: tText("LOADED = PLANNED") })}</div>`;
  host.innerHTML = `<table class="plain"><tbody>${tmRow}${planRow}</tbody></table>${verdict}`;
}

/* — G12: blind-TC mode (TT&C toggle, armed confirm, history tagging) — */
let blindArmTimer = null;
export function blindTcState() { return { ...S.blindTc }; }
export function toggleBlindTc() {
  if (S.blindTc.enabled) {
    S.blindTc.enabled = false;
    postJSON("/api/console-log", { position: S.position, kind: "note",
      text: "BLIND-TC mode DISABLED — TM confirmation restored" });
    announce(tText("Blind-TC mode disabled"));
  } else if (!S.blindTc.armPending) {
    S.blindTc.armPending = true;
    announce(tText("Blind-TC ARM — press again within {{s}} s to confirm. FD GO required (CON-004).", { s: 8 }));
    blindArmTimer = setTimeout(() => { S.blindTc.armPending = false; renderBlindTc(); }, 8000);
  } else {
    if (blindArmTimer) { clearTimeout(blindArmTimer); blindArmTimer = null; }
    S.blindTc.armPending = false;
    S.blindTc.enabled = true;
    postJSON("/api/console-log", { position: S.position, kind: "note",
      text: "BLIND-TC mode ENABLED (FD GO per CON-004) — subsequent commands are " +
            "sent WITHOUT TM confirmation and tagged BLIND until a readback confirms" });
    announce(tText("BLIND-TC MODE ENABLED — commands are now tagged BLIND"));
  }
  renderBlindTc();
}
function renderBlindTc() {
  const btn = $("ttc-blind-btn");
  const st = $("ttc-blind-status");
  if (btn) {
    btn.textContent = S.blindTc.enabled ? tText("DISABLE BLIND-TC")
      : S.blindTc.armPending ? tText("CONFIRM BLIND-TC (armed)") : tText("ENABLE BLIND-TC");
    btn.classList.toggle("armed", S.blindTc.armPending);
  }
  if (st) {
    st.innerHTML = S.blindTc.enabled
      ? `<span class="blind-chip">${t("BLIND-TC ACTIVE")}</span> ${t("commands go up without TM readback — log every send")}`
      : S.blindTc.armPending ? t("armed — second press enables (voice FD GO first)")
      : t("off — commands verify normally via S1 reports");
  }
}
export function blindHistoryChip(h) {
  if (!h || !h.blind) return "";
  return h.blind === "confirmed"
    ? `<span class="blind-chip confirmed" title="${t("sent blind; a later TM readback (S1) confirmed it")}">BLIND ✓ TM</span>`
    : `<span class="blind-chip" title="${t("sent in blind-TC mode — NO telemetry confirmation yet (CON-004)")}">BLIND</span>`;
}

/* — G15: baseline-vs-now health card (TRND page; baselines from
 *        display_config.yaml health_baselines) — */
export function baselineTable() {
  const t = (S.displayConfig || {}).health_baselines;
  return (t && typeof t === "object" && !Array.isArray(t)) ? t : null;
}
export function computeBaselineDeltas() {
  const t = baselineTable();
  if (!t) return { available: false };
  const rows = Object.entries(t).map(([hexId, b]) => {
    const base = Number(b.value);
    const label = (b.label ? tdb(`baseline:${hexId}:label`, b.label) : "") ||
      (S.paramByHex[hexId] || {}).name || hexId;
    const units = b.units || (S.paramByHex[hexId] || {}).units || "";
    const raw = paramVal(hexId);
    const stale = paramIsStale(hexId);
    if (raw === undefined || raw === null || stale) {
      return { hexId, label, units, base, now: null, delta: null, drift: null,
               flag: false, state: "no-tm" };
    }
    const now = Number(raw);
    const delta = now - base;
    const drift = base !== 0 ? (delta / Math.abs(base)) * 100 : null;
    const flag = drift !== null
      ? Math.abs(drift) > 5
      : Math.abs(delta) > (Number(b.abs_flag) || 0) && delta !== 0;
    return { hexId, label, units, base, now, delta, drift, flag, state: "ok" };
  });
  return { available: true, rows,
           flagged: rows.filter((r) => r.flag).length };
}
export function renderBaselineCard() {
  const host = $("trnd-baseline");
  if (!host) return;
  const c = computeBaselineDeltas();
  if (!c.available) {
    host.innerHTML = `<div class="ds-banner stale">${t("no commissioning baseline — the instructor fills {{key}} in {{file}}",
      { key: "health_baselines", file: "configs/<mission>/mcs/display_config.yaml" })}</div>`;
    return;
  }
  const rows = c.rows.map((r) => {
    if (r.state === "no-tm") {
      return `<tr class="stale"><td>${esc(r.label)}</td><td class="mono">${esc(r.hexId)}</td>
        <td class="mono">${num(r.base, 2)}</td><td class="mono">—</td><td class="mono">—</td>
        <td>${renderChip({ kind: "stale", label: tText("NO TM") })}</td></tr>`;
    }
    const driftTxt = r.drift === null ? `Δ ${num(r.delta, 3)} ${esc(r.units)}`
      : `${r.drift >= 0 ? "+" : ""}${num(r.drift, 1)} %`;
    return `<tr><td>${esc(r.label)}</td><td class="mono">${esc(r.hexId)}</td>
      <td class="mono">${num(r.base, 2)}</td><td class="mono">${num(r.now, 2)} ${esc(r.units)}</td>
      <td class="mono">${driftTxt}</td>
      <td>${r.flag ? renderChip({ kind: "warn", label: ">5 % — NOM-011", dir: "down",
        title: tText("degraded more than 5 % against the commissioning baseline — long-term trend review (NOM-011)") })
        : renderChip({ kind: "ok", label: tText("in family") })}</td></tr>`;
  }).join("");
  host.innerHTML = `<table class="plain">
    <thead><tr><th>${t("Metric")}</th><th>ID</th><th>${t("Baseline")}</th><th>${t("Now")}</th><th>${t("Drift")}</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>
    <div style="font-size:12px;color:var(--tx3);margin-top:6px">${t("baseline: commissioning snapshot ({{file}}) · drift computed on the console, flagged {{thr}} per NOM-011",
      { file: "display_config.yaml", thr: ">5 %" })}</div>`;
}

/* ═══ 10. FRESHNESS — display-wide staleness gate (P4) ════════════════════ */

/* Promoted from the classic per-chart rule: when telemetry is stale the whole
 * display stops pretending. Sparklines get {stale:true} (line ends + cut
 * mark), dump/trend charts stop appending, values render em-dash via the
 * component layer. */
export function tmFreshness(st, subsystem) {
  const s2 = st || S.state;
  if (subsystem && s2.subsystem_staleness &&
      s2.subsystem_staleness[subsystem] !== undefined) {
    const sc = ((S.clientConfig || {}).subsystem_cadence || {})[subsystem];
    return ageVerdict(s2.subsystem_staleness[subsystem], sc ? sc.interval_s : null);
  }
  if (s2.stale) return "stale";
  return freshness(s2.last_frame_age_s);
}
function updateChartGate() { S.chartStale = tmFreshness() === "stale"; updateLinkLimited(); }
/* Training speed-up caveat (R3 A4): at ×N the downlink still runs at its
 * real bit rate, so sim-second ages grow N times faster than telemetry can
 * arrive. Rather than silently turning the console stale, say so once. */
function updateLinkLimited() {
  const el = $("linklimit-banner");
  if (!el) return;
  const ll = linkLimited(S.state, { thresholdS: stalePolicy().floor_stale_s,
    lockFresh: (hex) => paramFreshness(hex) !== "stale" });
  el.classList.toggle("hide", !ll.limited);
  if (ll.limited) el.textContent = tText("Link-limited at ×{{speed}} — the downlink runs at its real rate, so values are held at their last receipt and age in sim seconds. Slow the simulation to see live values.",
    { speed: num(ll.speed, 0) });
}

/* ═══ 11. CMD — commanding page ═══════════════════════════════════════════ */
/* Catalogue codec adapted from the classic console (same wire behaviour):
 * big-endian by default, S8.1 func_id octet first, linear calibration. */

function catFieldWidth(t) {
  return { uint8: 1, int8: 1, uint16: 2, int16: 2, uint32: 4, int32: 4,
    float32: 4, float64: 8 }[t] ?? null;   // null => variable hex tail
}
function catCal(f) { return f.calibration || {}; }
function catIsFloat(f) { return String(f.type || "").toLowerCase().indexOf("float") === 0; }
/* Engineering value -> raw wire value. The ENCODER owns the unit conversion
 * (classic parity): the operator types -15 °C, the wire carries centi-kelvin.
 * Integer types are rounded like the classic encoder; a variable hex tail
 * (`bytes` fields) passes through untouched. */
function catEngToRaw(f, eng) {
  if (catFieldWidth(String(f.type || "uint8").toLowerCase()) == null) return eng;
  if (catIsFloat(f)) return Number(eng);
  const cal = catCal(f);
  const ct = String(cal.type || "").toLowerCase();
  if (ct === "linear") {
    const scale = cal.scale != null ? cal.scale : 1;
    const offset = cal.offset != null ? cal.offset : 0;
    return Math.round((Number(eng) - offset) / scale);
  }
  if (ct === "polynomial") {
    const c = cal.coefficients || [];
    return Math.round((Number(eng) - (c[0] || 0)) / (c.length > 1 ? c[1] : 1));
  }
  return Math.round(Number(eng));
}
function catRawToEng(f, raw) {
  if (catIsFloat(f)) return Number(raw);
  const cal = catCal(f);
  const ct = String(cal.type || "").toLowerCase();
  if (ct === "linear") {
    const scale = cal.scale != null ? cal.scale : 1;
    const offset = cal.offset != null ? cal.offset : 0;
    return Number(raw) * scale + offset;
  }
  if (ct === "polynomial") {
    const c = cal.coefficients || [];
    let v = 0;
    for (let i = 0; i < c.length; i++) v += c[i] * Math.pow(Number(raw), i);
    return v;
  }
  return raw;
}
function catFieldDefault(f) {
  if (f.default !== undefined && f.default !== null) return f.default;
  if (f.range && f.range.min !== undefined) return f.range.min;
  if (f.min !== undefined) return f.min;
  if ((f.enum || []).length) return f.enum[0].value;
  return 0;
}
/* Length validation against the schema. Returns the reason the ground must
 * NOT send this packet, or null when the data field is long enough.
 *
 * 2026-08 command-safety defect: the typed-field editor always encodes one
 * value per declared field, but the hex box is free text that goes to
 * /api/pus-command verbatim. A TTC_SET_BEACON_MODE of bare "46" left the
 * console and turned beacon mode ON in the spacecraft. Tell the operator
 * BEFORE the packet is built, naming the missing field. (Regressed by
 * bb09265, restored 2026-11-01.) */
export function catLengthError(cmd, hexStr) {
  if (!cmd || !Array.isArray(cmd.fields) || !cmd.fields.length) return null;
  const octets = String(hexStr || "").replace(/[\s,]+/g, "").length / 2;
  const prefix = (Number(cmd.service) === 8 && Number(cmd.subtype) === 1
    && cmd.func_id != null) ? 1 : 0;
  let need = prefix;
  for (const f of cmd.fields) {
    const w = catFieldWidth(String(f.type || "uint8").toLowerCase());
    if (w == null) return null;              // variable tail — not our call
    need += w;
    if (octets < need) {
      return tText("{{cmd}} needs a {{w}}-byte `{{field}}`{{legend}} — the data field is {{have}} B, the schema needs {{need}} B. The spacecraft REJECTS a missing argument (S1.8 0x0003); it does not assume one.",
        { cmd: cmd.name, w, field: f.name, legend: f.description ? ` (${f.description})` : "",
          have: octets, need });
    }
  }
  return null;
}
/* Engineering-units validation (classic catFieldError parity). Returns the
 * reason the spacecraft would reject the value, or null when valid. */
export function catFieldError(f, eng) {
  if (catFieldWidth(String(f.type || "uint8").toLowerCase()) == null) return null;
  if (eng === "" || eng === null || eng === undefined) return tText("{{name}}: no value", { name: f.name });
  const val = Number(eng);
  if (!Number.isFinite(val)) return tText("{{name}}: not a number", { name: f.name });
  if (f.range && (val < f.range.min || val > f.range.max)) {
    const u = f.unit ? ` ${f.unit}` : "";
    return tText("{{name}} = {{val}}{{u}} is outside [{{min}} … {{max}}]{{u}} — the spacecraft will REJECT this (S1.8)",
      { name: f.name, val, u, min: String(f.range.min), max: String(f.range.max) });
  }
  const ct = String(catCal(f).type || "").toLowerCase();
  if (ct === "enum" && (f.enum || []).length) {
    if (!(f.enum || []).some((e) => Number(e.value) === Math.round(val)))
      return tText("{{name}} = {{val}} is not an enumerated value", { name: f.name, val });
  }
  if (ct === "bitfield" && (f.bits || []).length) {
    let allowed = 0;
    for (const b of f.bits) if (!b.reserved) allowed |= (1 << b.bit);
    if (Math.round(val) & ~allowed)
      return tText("{{name}} = {{val}} sets reserved bits",
        { name: f.name, val: `0x${Math.round(val).toString(16).toUpperCase()}` });
  }
  return null;
}
/* Format an engineering value for an input box (respects the field scale). */
export function catFormatEng(f, v) {
  if (catIsFloat(f)) return String(Math.round(Number(v) * 1e4) / 1e4);
  const cal = catCal(f);
  if (String(cal.type || "").toLowerCase() === "linear") {
    const scale = cal.scale != null ? cal.scale : 1;
    const decimals = Math.max(0, Math.ceil(-Math.log10(Math.abs(scale) || 1)));
    return Number(v).toFixed(decimals);
  }
  const n = Number(v);
  return Number.isFinite(n) ? String(Math.round(n)) : String(v);
}
/* The server speaks `criticality: "critical"|"caution"`; older fixtures used
 * a boolean `critical`. Arm→execute is required for CRITICAL only. */
export function isCritical(cmd) {
  if (!cmd) return false;
  return cmd.critical === true ||
    String(cmd.criticality || "").toLowerCase() === "critical";
}
export function catPackRaw(f, raw) {
  const t = String(f.type || "uint8").toLowerCase();
  const w = catFieldWidth(t);
  if (w == null) {
    const s2 = String(raw || "").replace(/[\s,]+/g, "");
    const out = [];
    for (let i = 0; i + 1 < s2.length + 1 && i < s2.length; i += 2)
      out.push(parseInt(s2.substr(i, 2), 16) || 0);
    return out;
  }
  const buf = new ArrayBuffer(w);
  const dv = new DataView(buf);
  const le = String(f.endian || "big").toLowerCase() === "little";
  const v = Number(raw);
  if (t === "float32") dv.setFloat32(0, v, le);
  else if (t === "float64") dv.setFloat64(0, v, le);
  else if (t === "int8") dv.setInt8(0, v);
  else if (t === "uint8") dv.setUint8(0, v & 0xFF);
  else if (t === "int16") dv.setInt16(0, v, le);
  else if (t === "uint16") dv.setUint16(0, v & 0xFFFF, le);
  else if (t === "int32") dv.setInt32(0, v, le);
  else dv.setUint32(0, v >>> 0, le);
  return Array.from(new Uint8Array(buf));
}
export function encodeCatalogCommand(cmd, args) {
  let bytes = [];
  if (Number(cmd.service) === 8 && Number(cmd.subtype) === 1 && cmd.func_id != null)
    bytes.push(Number(cmd.func_id) & 0xFF);
  for (const f of (cmd.fields || [])) {
    const eng = (args && args[f.name] !== undefined && args[f.name] !== "")
      ? args[f.name] : catFieldDefault(f);
    bytes = bytes.concat(catPackRaw(f, catEngToRaw(f, eng)));
  }
  return bytes.map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
}
export function decodeCatalogArgs(cmd, hexStr) {
  const s2 = String(hexStr || "").replace(/[\s,]+/g, "");
  if (s2.length % 2) return { ok: false, error: tText("odd number of hex digits") };
  const bytes = [];
  for (let i = 0; i < s2.length; i += 2) {
    const b = parseInt(s2.substr(i, 2), 16);
    if (isNaN(b)) return { ok: false, error: tText("bad hex at octet {{i}}", { i: i / 2 }) };
    bytes.push(b);
  }
  const values = {};
  let pos = 0;
  for (const f of (cmd.fields || [])) {
    const t = String(f.type || "uint8").toLowerCase();
    const w = catFieldWidth(t);
    if (w == null) {
      values[f.name] = bytes.slice(pos)
        .map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
      pos = bytes.length;
      continue;
    }
    if (pos + w > bytes.length)
      return { ok: false, error: tText("{{n}} byte(s) is too short for {{name}}", { n: bytes.length, name: f.name }) };
    const dv = new DataView(new Uint8Array(bytes.slice(pos, pos + w)).buffer);
    const le = String(f.endian || "big").toLowerCase() === "little";
    let raw;
    if (t === "float32") raw = dv.getFloat32(0, le);
    else if (t === "float64") raw = dv.getFloat64(0, le);
    else if (t === "int8") raw = dv.getInt8(0);
    else if (t === "uint8") raw = dv.getUint8(0);
    else if (t === "int16") raw = dv.getInt16(0, le);
    else if (t === "uint16") raw = dv.getUint16(0, le);
    else if (t === "int32") raw = dv.getInt32(0, le);
    else raw = dv.getUint32(0, le);
    values[f.name] = catRawToEng(f, raw);
    pos += w;
  }
  if (pos !== bytes.length)
    return { ok: false, error: tText("{{n}} trailing byte(s)", { n: bytes.length - pos }) };
  return { ok: true, values };
}
export function sidToHex(sid) {
  const v = Number(sid) & 0xFFFF;
  return [(v >> 8) & 0xFF, v & 0xFF]
    .map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
}
export function provenanceText(cmd) {
  if (!cmd) return "";
  let head = `S${cmd.service}.${cmd.subtype}`;
  if (cmd.func_id != null) head += ` func ${cmd.func_id} (0x${Number(cmd.func_id).toString(16).toUpperCase().padStart(2, "0")})`;
  const bits = [head];
  const exp = cmd.expected_data_bytes != null ? cmd.expected_data_bytes : cmd.expected_bytes;
  if (exp != null) bits.push(tText("{{n}} data bytes", { n: exp }));
  else if (cmd.variable_length) bits.push(tText("variable length") + (cmd.minimum != null ? ` (≥${cmd.minimum} B)` : ""));
  if (isCritical(cmd)) bits.push(tText("CRITICAL — arm→execute"));
  else if (cmd.criticality) bits.push(String(cmd.criticality).toUpperCase());
  if (cmd.readback) {
    const rb = cmd.readback;
    if (rb && typeof rb === "object")
      bits.push(tText("readback {{what}}",
        { what: `${rb.description || ""}${rb.param_id != null ? ` (${fmtHex(rb.param_id, 4)})` : ""}` }).trim());
    else bits.push(tText("readback {{what}}", { what: rb }));
  }
  if (cmd.description) bits.push(tdb(`tc:${cmd.name}:description`, cmd.description));
  return bits.join(" · ");
}

function buildCmdPage() {
  return `
  <div class="pad hide" id="page-cmd" role="tabpanel" aria-label="Commanding" data-i18n-aria-label>
    <h1 class="pt" data-i18n>Commanding</h1>
    <p class="sub" data-i18n>PUS telecommand builder · verification is a stepper attached to the
      command, not a separate log (P9)</p>
    <div class="g" style="grid-template-columns:minmax(0,1fr) 420px;align-items:start">
      <div class="g">
        <div class="ds-card"><h2 data-i18n>Command builder <span class="r" id="cmd-authority"></span></h2>
          <div class="bd">
            <div class="row">
              <div class="fld"><label for="cmd-catalog" data-i18n>Catalogue command</label>
                <select id="cmd-catalog" class="in" style="min-width:280px"></select></div>
              <div class="fld"><label for="cmd-service" data-i18n>Service</label>
                <select id="cmd-service" class="in">
                  ${[3, 5, 6, 8, 9, 11, 12, 15, 17, 19, 20].map((s2) => `<option>${s2}</option>`).join("")}
                </select></div>
              <div class="fld"><label for="cmd-subtype" data-i18n>Subtype</label>
                <input id="cmd-subtype" class="in" type="number" min="1" max="255" value="1" style="width:70px"></div>
              <div class="fld"><label for="cmd-name" data-i18n>Name</label>
                <input id="cmd-name" class="in" placeholder="optional" data-i18n-placeholder></div>
            </div>
            <div id="cmd-fields" class="g" style="grid-template-columns:repeat(auto-fill,minmax(200px,1fr));margin-top:8px"></div>
            <div id="cmd-raw-preview" class="mono" style="font-size:12px;color:var(--info);margin-top:6px"></div>
            <div id="cmd-field-errors" style="font-size:12px;color:var(--alarm)"></div>
            <div class="row" style="margin-top:8px">
              <div class="fld" style="flex:1"><label for="cmd-data" data-i18n>Data (hex) — live from the fields; paste hex to decode; Enter sends</label>
                <input id="cmd-data" class="in mono" placeholder="AA BB …"></div>
              <span id="cmd-bytes-chip" class="ds-badge"></span>
            </div>
            <div id="cmd-provenance" style="font-size:12px;color:var(--tx3);margin:6px 0"></div>
            <div class="row" data-why-out="cmd-send-why">
              <button class="ds-btn" id="cmd-pack" data-i18n="Pack from fields">Pack from fields</button>
              <button class="ds-btn" id="cmd-decode" data-i18n="Decode hex into fields">Decode hex into fields</button>
              <span style="flex:1"></span>
              <!-- Routine and caution commands: one press. Critical commands
                   (catalogue criticality "critical"): the amber-striped
                   button arms on the first press and sends on the second,
                   within 8 s (armButton). -->
              <button class="ds-btn primary" id="cmd-send" data-i18n="Send">Send</button>
              <button class="ds-btn critical hide" id="cmd-send-crit" data-i18n="Send critical command">Send critical command</button>
              ${renderLogThis({}, { kind: "decision" })}
            </div>
            <div class="why-off" id="cmd-send-why" aria-live="polite" style="text-align:right"></div>
            <div id="cmd-verif-stepper" style="margin-top:10px"></div>
            <div id="cmd-result" style="font-size:12.5px;margin-top:6px"></div>
          </div></div>
        <div class="ds-card"><h2><span data-i18n="Quick commands">Quick commands</span> <span class="r" data-i18n="position-gated; denied entries say who owns them">position-gated; denied entries say who owns them</span></h2>
          <div class="bd">
            <input id="qc-filter" class="in qc-filter" type="search" placeholder="Filter commands…"
              data-i18n-placeholder="Filter commands…" aria-label="Filter quick commands" data-i18n-aria-label="Filter quick commands">
            <div id="cmd-quick"></div>
            <div class="qc-legend">
              <span><span data-i18n="Routine: one press">Routine: one press</span></span>
              <span><svg aria-hidden="true"><use href="/static/shared/glyphs.svg#g-warn-up"></use></svg><span data-i18n="Caution: check the effect first">Caution: check the effect first</span></span>
              <span><span class="stripe" aria-hidden="true"></span><span data-i18n="Critical: press to arm, press again within 8 s to send">Critical: press to arm, press again within 8 s to send</span></span>
            </div>
          </div></div>
        <div class="ds-card"><h2 data-i18n>Verification log <span class="r">/api/verification-log · 5 s</span></h2>
          <div class="bd scroll-y" style="max-height:200px" id="cmd-verif-log"></div></div>
      </div>
      <div class="g" style="align-content:start">
        <div class="ds-card"><h2 data-i18n>Stored TM (S15) dump</h2><div class="bd">
          <div class="row">
            <div class="fld"><label for="s15-target" data-i18n="Subsystem">Subsystem</label>
              <select id="s15-target" class="in">
                ${["eps", "tcs", "aocs", "ttc", "payload", "prop", "obdh", "orbit", "all"]
                  .map((s2) => `<option>${s2}</option>`).join("")}</select></div>
            <div class="fld"><label for="s15-store" data-i18n>Store id</label>
              <select id="s15-store" class="in">
                <option value="">auto</option><option>1</option><option>2</option><option>3</option><option>4</option>
              </select></div>
            <button class="ds-btn" id="s15-dump" data-i18n="Dump">Dump</button>
          </div>
          <div id="s15-result" style="font-size:12px;color:var(--tx3);margin-top:6px"></div>
        </div></div>
        <div class="ds-card"><h2 data-i18n>HK SID control (S3)</h2><div class="bd">
          <div class="row">
            <div class="fld"><label for="hk-sid">SID</label>
              <input id="hk-sid" class="in" type="number" min="1" value="1" style="width:70px"></div>
            <button class="ds-btn" data-hk="enable" data-i18n="Enable (3,5)">Enable (3,5)</button>
            <button class="ds-btn" data-hk="disable" data-i18n="Disable (3,6)">Disable (3,6)</button>
            <button class="ds-btn" data-hk="oneshot" data-i18n="One-shot (3,27)">One-shot (3,27)</button>
          </div>
          <div id="hk-quick-result" style="font-size:12px;color:var(--tx3);margin-top:6px"></div>
        </div></div>
        <div class="ds-card"><h2 data-i18n>Command history</h2>
          <div class="bd scroll-y" style="max-height:280px" id="cmd-history"></div></div>
      </div>
    </div>
  </div>`;
}

function currentCatalogCmd() {
  const sel = $("cmd-catalog");
  if (!sel || !sel.value) return null;
  return S.tcCatalog.find((c) => c.name === sel.value) || null;
}

function renderCmdCatalogSelect() {
  const sel = $("cmd-catalog");
  if (!sel) return;
  const cur = sel.value;
  sel.innerHTML = `<option value="">${t("— raw service/subtype —")}</option>` +
    S.tcCatalog.map((c) => `<option value="${esc(c.name)}"${c.allowed ? "" : " data-denied=\"1\""}>` +
      `${esc(c.name)} (S${c.service},${c.subtype})${c.allowed ? "" : " 🔒"}</option>`).join("");
  if (cur) sel.value = cur;
}

/* "NOT PERMITTED — belongs to <position>" (plan §2.1): authority is shown,
 * never hidden. Which position owns a denied command is derived from
 * positions.yaml allowed_commands lists. */
export function commandAuthority(cmdName) {
  const cmd = S.tcCatalog.find((c) => c.name === cmdName);
  if (!cmd) return { allowed: false, text: tText("unknown command") };
  if (cmd.allowed) return { allowed: true, text: "" };
  const owners = [];
  for (const [pos, p] of Object.entries(S.positions)) {
    const ac = p.allowed_commands;
    if (ac === "all" || (Array.isArray(ac) && ac.includes(cmdName))) owners.push([pos, p.label || pos]);
  }
  // compare the English config labels; translate only for display
  const owner = owners.filter(([, l]) => l !== (S.positions[S.position] || {}).label)
    .map(([pos, l]) => (S.positions[pos] || {}).label ? tdb(`pos:${pos}:label`, l) : l);
  return { allowed: false,
    text: tText("NOT PERMITTED — belongs to {{owner}}",
      { owner: owner.length ? owner.join(", ") : tText("another position") }) };
}

/* Names that read far better as hex on an ops console (classic parity). */
const HEX_FIELD_NAMES = new Set([
  "param_id", "mon_id", "sid", "address", "trigger_id", "device_id", "event_id",
]);

/* One typed widget per catalogue field — the widget kind is schema-driven
 * (classic Phase E WP-4 parity): enum -> dropdown with the value NAMES,
 * bitfield -> one checkbox per bit, linear-calibrated / ranged numbers ->
 * engineering-unit number inputs with min/max/step, bytes -> hex tail. */
export function cmdFieldWidget(f, cmdName) {
  const cal = catCal(f);
  const ct = String(cal.type || "").toLowerCase();
  const unit = f.unit || f.units || "";
  const label = `${esc(f.name)}${unit ? ` (${esc(unit)})` : ""}`;
  // descriptions: YAML overlay tcarg/tcenum/tcbit:<cmd>.<field>[.<item>]:description
  const ov = `${cmdName}.${f.name}`;
  const title = esc(f.description ? tdb(`tcarg:${ov}:description`, f.description) : (f.type || ""));
  const dflt = catFieldDefault(f);
  if ((f.enum || []).length) {
    const opts = f.enum.map((e) =>
      `<option value="${esc(String(e.value))}"${String(e.value) === String(dflt) ? " selected" : ""}>` +
      `${e.value} — ${esc(e.label)}${e.description
        ? ` (${esc(tdb(`tcenum:${ov}.${e.label ?? e.value}:description`, e.description))})` : ""}</option>`).join("");
    return `<div class="fld"><label>${label}</label>
      <select class="in" data-cmd-field="${esc(f.name)}" title="${title}">${opts}</select></div>`;
  }
  if (ct === "bitfield" && (f.bits || []).length) {
    const mask = Number(dflt) || 0;
    const rows = f.bits.map((b) => b.reserved
      ? `<div style="color:var(--tx3)">${t("bit{{n}} reserved (0)", { n: b.bit })}</div>`
      : `<label style="display:block"><input type="checkbox" data-cmd-bit="${esc(f.name)}"
           data-bit="${b.bit}"${(mask >> b.bit) & 1 ? " checked" : ""}>
           bit${b.bit} ${esc(b.name)}${b.description
             ? " — " + esc(tdb(`tcbit:${ov}.${b.name ?? b.bit}:description`, b.description)) : ""}</label>`).join("");
    return `<div class="fld" data-cmd-bitfield="${esc(f.name)}"><label>${label} — ${t("flags")}</label>
      <div style="font-size:12px">${rows}
        <span class="mono" data-cmd-mask="${esc(f.name)}" style="color:var(--tx3)"></span></div></div>`;
  }
  const ty = String(f.type || "uint8").toLowerCase();
  if (catFieldWidth(ty) == null) {
    return `<div class="fld"><label>${label} — ${t("hex bytes")}</label>
      <input class="in mono" data-cmd-field="${esc(f.name)}" placeholder="00 FF …"
        value="${f.default != null ? esc(String(f.default)) : ""}" title="${title}"></div>`;
  }
  const rng = f.range || {};
  const hasRange = rng.min !== undefined || rng.max !== undefined;
  const hint = hasRange
    ? ` <span style="color:var(--tx3);font-weight:400">[${rng.min} … ${rng.max}]${unit ? " " + esc(unit) : ""}</span>` : "";
  if (HEX_FIELD_NAMES.has(f.name)) {
    return `<div class="fld"><label>${label}${hint}</label>
      <input class="in mono" data-cmd-field="${esc(f.name)}" value="${esc(String(dflt))}"
        placeholder="0xHHHH" title="${title}"></div>`;
  }
  const step = ty.indexOf("float") === 0 ? "0.01"
    : ct === "linear" ? String(Math.abs(cal.scale != null ? cal.scale : 1)) : "1";
  return `<div class="fld"><label>${label}${hint}</label>
    <input class="in" type="number" step="${step}" data-cmd-field="${esc(f.name)}"
      value="${esc(catFormatEng(f, dflt))}"
      ${rng.min !== undefined ? `min="${rng.min}"` : ""} ${rng.max !== undefined ? `max="${rng.max}"` : ""}
      title="${title}"></div>`;
}

function updateCmdBuilder() {
  const cmd = currentCatalogCmd();
  const authEl = $("cmd-authority");
  const sendBtn = $("cmd-send");
  const critBtn = $("cmd-send-crit");
  if (cmd) {
    $("cmd-service").value = String(cmd.service);
    $("cmd-subtype").value = String(cmd.subtype);
    $("cmd-name").value = cmd.name;
    setText("cmd-provenance", provenanceText(cmd));
    const auth = commandAuthority(cmd.name);
    if (authEl) { authEl.textContent = auth.text; authEl.style.color = auth.allowed ? "" : "var(--alarm)"; }
    // structured field editor (engineering units, enum names, validation)
    setHTML("cmd-fields", (cmd.fields || []).map((f) => cmdFieldWidget(f, cmd.name)).join(""));
    const critical = isCritical(cmd);
    if (sendBtn) sendBtn.classList.toggle("hide", critical);
    if (critBtn) critBtn.classList.toggle("hide", !critical);
    const live = critical ? critBtn : sendBtn;
    if (live) {
      setEnabled(live, auth.allowed, auth.text);
      setText("cmd-send-why", auth.allowed ? (critical
        ? tText("Critical command: the first press arms, the second within 8 s sends.") : "")
        : auth.text);
    }
    cmdLivePack();     // hex + length visible immediately, from the defaults
  } else {
    if (authEl) authEl.textContent = "";
    setHTML("cmd-fields", "");
    setText("cmd-provenance", tText("raw command — no catalogue entry; length not validated"));
    setText("cmd-raw-preview", "");
    setText("cmd-field-errors", "");
    if (critBtn) critBtn.classList.add("hide");
    if (sendBtn) { sendBtn.classList.remove("hide"); setEnabled(sendBtn, true); setText("cmd-send-why", ""); }
    updateBytesChip();
  }
}
function collectFieldArgs() {
  const args = {};
  const sec = $("page-cmd");
  if (!sec || !sec.querySelectorAll) return args;
  sec.querySelectorAll("#cmd-fields [data-cmd-field]").forEach((el) => {
    args[el.dataset.cmdField] = el.value;
  });
  // bitfields: assemble the mask from the checkboxes
  const masks = {};
  sec.querySelectorAll("#cmd-fields [data-cmd-bit]").forEach((el) => {
    const nm = el.dataset.cmdBit;
    if (masks[nm] === undefined) masks[nm] = 0;
    if (el.checked) masks[nm] |= (1 << Number(el.dataset.bit));
  });
  for (const [nm, mask] of Object.entries(masks)) {
    args[nm] = mask;
    sec.querySelectorAll(`[data-cmd-mask="${nm}"]`).forEach((el) => {
      el.textContent = `mask = 0x${mask.toString(16).toUpperCase().padStart(2, "0")}`;
    });
  }
  return args;
}

/* Live pack (classic refreshSchemaPreview parity): every keystroke in the
 * typed fields re-encodes engineering -> raw hex, mirrors it into the data
 * box, shows RAW ▸ preview + byte count and flags invalid fields WITH the
 * rejection reason. Non-blocking: fault-injection training may still send. */
let cmdPackGuard = false;
function cmdLivePack() {
  const cmd = currentCatalogCmd();
  if (!cmd) return;
  const args = collectFieldArgs();
  const errs = [];
  const sec = $("page-cmd");
  if (sec && sec.querySelectorAll) {
    sec.querySelectorAll("#cmd-fields [data-cmd-field]").forEach((el) => {
      const f = (cmd.fields || []).find((x) => x.name === el.dataset.cmdField);
      if (!f) return;
      const msg = catFieldError(f, args[f.name]);
      if (el.style) el.style.borderColor = msg ? "var(--alarm)" : "";
      if (msg) errs.push(msg);
    });
  }
  const hex = encodeCatalogCommand(cmd, args);
  cmdPackGuard = true;
  const dataEl = $("cmd-data");
  if (dataEl) dataEl.value = hex;
  cmdPackGuard = false;
  setText("cmd-raw-preview", hex ? `RAW ▸ ${hex}` : "");
  setText("cmd-field-errors", errs.join("  ·  "));
  updateBytesChip();
}

/* Reverse decode (classic reverseDecodeIntoFields parity): hex typed or
 * pasted into the data box is decoded against the schema back into the
 * typed fields in ENGINEERING units. For S8.1, octet 0 identifies the
 * command; the builder auto-switches to it. */
function cmdReverseDecode() {
  if (cmdPackGuard) return;
  updateBytesChip();
  const raw = String($("cmd-data") ? $("cmd-data").value : "").replace(/[\s,]+/g, "");
  if (!raw || raw.length % 2) return;
  const svc = Number($("cmd-service") ? $("cmd-service").value : 0);
  const sub = Number($("cmd-subtype") ? $("cmd-subtype").value : 0);
  let cmd = currentCatalogCmd();
  let body = raw;
  if (svc === 8 && sub === 1) {
    const fid = parseInt(raw.slice(0, 2), 16);
    if (!Number.isFinite(fid)) return;
    const match = S.tcCatalog.find((c) => Number(c.service) === 8 &&
      Number(c.subtype) === 1 && Number(c.func_id) === fid);
    if (!match) {
      setText("cmd-raw-preview", tText("✗ func {{id}} is not in the catalogue",
        { id: `0x${fid.toString(16).toUpperCase().padStart(2, "0")}` }));
      return;
    }
    if (!cmd || cmd.name !== match.name) {
      const sel = $("cmd-catalog");
      if (sel) sel.value = match.name;
      const keep = $("cmd-data") ? $("cmd-data").value : "";
      updateCmdBuilder();                 // re-render typed fields for it
      const dataEl = $("cmd-data");
      if (dataEl) dataEl.value = keep;    // defaults overwrote the paste
    }
    cmd = match;
    body = raw.slice(2);
  }
  if (!cmd || !Array.isArray(cmd.fields)) return;
  if (!cmd.fields.length) {
    setText("cmd-raw-preview", body.length ? tText("✗ {{name}} takes no arguments", { name: cmd.name })
      : tText("DECODED ✓ {{name}}", { name: cmd.name }));
    return;
  }
  const r = decodeCatalogArgs(cmd, body);
  if (!r.ok) { setText("cmd-raw-preview", tText("✗ decode: {{err}}", { err: r.error })); return; }
  applyDecodedValues(cmd, r.values);
  setText("cmd-raw-preview", tText("DECODED ✓ {{name}}", { name: cmd.name }));
  setText("cmd-field-errors", "");
  updateBytesChip();
}
function applyDecodedValues(cmd, values) {
  const sec = $("page-cmd");
  if (!sec || !sec.querySelectorAll) return;
  sec.querySelectorAll("#cmd-fields [data-cmd-field]").forEach((el) => {
    const f = (cmd.fields || []).find((x) => x.name === el.dataset.cmdField);
    if (!f || values[f.name] === undefined) return;
    if (HEX_FIELD_NAMES.has(f.name))
      el.value = "0x" + Math.round(Number(values[f.name])).toString(16).toUpperCase();
    else if ((f.enum || []).length) el.value = String(Math.round(Number(values[f.name])));
    else if (catFieldWidth(String(f.type || "uint8").toLowerCase()) == null)
      el.value = String(values[f.name]);
    else el.value = catFormatEng(f, values[f.name]);
  });
  // bitfields back into checkboxes
  sec.querySelectorAll("#cmd-fields [data-cmd-bit]").forEach((el) => {
    const nm = el.dataset.cmdBit;
    if (values[nm] === undefined) return;
    el.checked = !!((Number(values[nm]) >> Number(el.dataset.bit)) & 1);
  });
}
function updateBytesChip() {
  const cmd = currentCatalogCmd();
  const chip = $("cmd-bytes-chip");
  if (!chip) return;
  const entered = String($("cmd-data") ? $("cmd-data").value : "").replace(/[\s,]+/g, "").length / 2;
  const exp = cmd ? (cmd.expected_data_bytes != null ? cmd.expected_data_bytes : cmd.expected_bytes) : null;
  if (!cmd || exp == null) {
    if (cmd && cmd.variable_length) {
      chip.textContent = `${entered} B (variable${cmd.minimum != null ? `, ≥${cmd.minimum}` : ""})`;
      chip.className = "ds-badge" + (cmd.minimum != null && entered < cmd.minimum ? " warn" : "");
    } else { chip.textContent = `${entered} B`; chip.className = "ds-badge"; }
    return;
  }
  chip.textContent = `${entered} / ${exp} B`;
  chip.className = "ds-badge" + (entered === exp ? "" : " warn");
}

async function sendCommand(opts = {}) {
  const cmd = currentCatalogCmd();
  const service = Number($("cmd-service").value);
  const subtype = Number($("cmd-subtype").value);
  const data = $("cmd-data").value.trim();
  const name = $("cmd-name").value.trim() || (cmd ? cmd.name : "");
  if (cmd) {
    // Length gate BEFORE anything else: a short data field is not a command
    // with a default, it is a command the spacecraft will refuse (and used
    // to execute in the dangerous direction). It never leaves the ground.
    const lenErr = catLengthError(cmd, data);
    if (lenErr) {
      setHTML("cmd-result", `<span style="color:var(--alarm)">${esc(tText("not sent — {{why}}", { why: lenErr }))}</span>`);
      setText("cmd-field-errors", lenErr);
      return;
    }
    const auth = commandAuthority(cmd.name);
    if (!auth.allowed) { setHTML("cmd-result", `<span style="color:var(--alarm)">${esc(auth.text)}</span>`); return; }
    // Critical: only the armed button's second press (armButton onExecute)
    // reaches here with confirmed set.
    if (isCritical(cmd) && !opts.confirmed && !S.armed[cmd.name]) {
      setHTML("cmd-result", `<span class="v-warn">${t("Critical command: press it once to arm, then again within 8 s to send.")}</span>`);
      return;
    }
    // 2026-08c item 5: GROUND-side HIGH-rate elevation policy (arm-through).
    const rateByte = parseInt(String(data).replace(/[^0-9a-fA-F]/g, "").slice(0, 2), 16);
    const ghWarn = groundHighRateWarning(cmd.name, rateByte);
    if (ghWarn) {
      const gk = "ghp:" + cmd.name;
      if (!S.armed[gk]) {
        S.armed[gk] = true;
        setHTML("cmd-result", `<span style="color:var(--warn)">${esc(ghWarn)} ${t("SEND again within 8 s to override the ground hold.")}</span>`);
        setTimeout(() => { S.armed[gk] = false; }, 8000);
        return;
      }
      S.armed[gk] = false;
    }
  }
  setHTML("cmd-verif-stepper", renderStepper([tText("BUILD"), tText("SENT"), "ACCEPT (S1.1)", "EXEC (S1.7)"], 1));
  const r = await sendPus({
    service, subtype, data_hex: data, name, position: S.position });
  const ok = r.ok && (!r.json || r.json.status !== "rejected");
  // (history is recorded by sendPus() for every send, builder included)
  const reason = (r.json && (r.json.reason || r.json.error)) || `HTTP ${r.status}`;   // server text: English
  setHTML("cmd-result", ok
    ? t("sent {{tc}}", { tc: `TC(${service},${subtype})` }) + (name ? " — " + esc(name) : "")
    : `<span style="color:var(--alarm)">${t("rejected — {{reason}}", { reason })}</span>`);
  if (cmd && isCritical(cmd)) { S.armed[cmd.name] = false; updateCmdBuilder(); }
  renderBottomDrawer();
}

function noteVerification(v) {
  const okSub = v.subtype === 1 || v.subtype === 7;
  // G12: any TM readback (an S1 verification report IS telemetry from the
  // spacecraft) confirms the oldest still-pending blind command.
  if (okSub) {
    const pending = S.cmdHistory.filter((h) => h.blind === "pending");
    if (pending.length) {
      pending[pending.length - 1].blind = "confirmed";
      renderCmdHistory();
    }
  }
  S.verifLog.unshift({ ts: tsShort(),
    verdict: `S1.${v.subtype} ${okSub ? "OK" : "FAIL"}`,
    text: `TC(${v.tc_service},${v.tc_subtype})` +
          (v.code !== undefined ? ` code ${hex4(v.code)}` : "") });
  if (S.verifLog.length > 80) S.verifLog.length = 80;
  const stepIdx = v.subtype === 1 ? 2 : v.subtype === 7 ? 3 : 2;
  const fail = !okSub;
  setHTML("cmd-verif-stepper", renderStepper(
    [tText("BUILD"), tText("SENT"), fail && v.subtype === 2 ? { label: "ACCEPT (S1.1)", fail: true } : "ACCEPT (S1.1)",
     fail && v.subtype === 8 ? { label: "EXEC (S1.7)", fail: true } : "EXEC (S1.7)"], stepIdx));
  renderVerifLog();
}
function renderVerifLog() {
  setHTML("cmd-verif-log", S.verifLog.map((v) =>
    `<div class="logrow ${v.verdict.includes("FAIL") ? "alarm" : ""}">` +
    `${esc(v.ts)} ${esc(v.verdict)} ${esc(v.text)}</div>`).join("") ||
    `<div class="logrow nom">${t("no verification reports yet")}</div>`);
}
// EVERY telecommand this console sends goes out through here.
//
// Field report 2026-08-20: the PUS service panels commanded the spacecraft
// but left no trace in the CMD HISTORY window. They posted to
// /api/pus-command directly, and only two of the twenty call sites in this
// module also called noteHistory() -- the command builder and the quick
// commands. So an S3 ENABLE ALL, an S9 SET SC TIME or an S12 monitor change
// went to the spacecraft and showed up nowhere on the ground: both a
// usability failure and a hole in the decision record.
//
// The recording now happens at the transport instead of at each call site,
// so a new panel cannot forget to do it.
async function sendPus(body) {
  const b = Object.assign({ position: S.position }, body);
  const r = await postJSON("/api/pus-command", b);
  const ok = r.ok && (!r.json || r.json.status !== "rejected");
  const reason = (r.json && (r.json.reason || r.json.error)) || `HTTP ${r.status}`;
  noteHistory({ ts: tsShort(), name: b.name || `S${b.service},${b.subtype}`,
    service: b.service, subtype: b.subtype, data: b.data_hex || "",
    verdict: ok ? tText("sent") : tText("rejected: {{reason}}", { reason }) });
  return r;
}
function noteHistory(h) {
  // G12: while blind-TC mode is active, every send is tagged BLIND and stays
  // "pending" (visually distinct) until a TM readback confirms it.
  if (S.blindTc.enabled && !h.blind) h.blind = "pending";
  S.cmdHistory.unshift(h);
  if (S.cmdHistory.length > RING) S.cmdHistory.length = RING;
  renderCmdHistory();
}
function cmdHistoryRow(c) {
  return `<div class="logrow">${esc(c.ts)} ${esc(c.name)} ` +
    `<span class="mono">${esc(c.data || "")}</span> — ${esc(c.verdict)}` +
    (c.blind ? " " + blindHistoryChip(c) : "") + `</div>`;
}
function renderCmdHistory() {
  setHTML("cmd-history", S.cmdHistory.slice(0, 60).map(cmdHistoryRow).join(""));
}

/* Quick commands: grouped grid, critical styling, position filtering; shown
 * on CMD and mirrored per-subsystem in place on every L2 page. */
function renderQuickCommands() {
  const groups = {};
  for (const q of S.quickCommands) {
    const g = q.group || q.subsystem || "GENERAL";
    (groups[g] = groups[g] || []).push(q);
  }
  // Stable identity per entry, independent of whether config gave it a
  // `name:`. Stamped here so the CMD grid and the per-subsystem mirrors agree.
  S.quickCommands.forEach((q, i) => { q._qi = i; });
  const btn = (q) => {
    const cmd = S.tcCatalog.find((c) => c.name === q.command);
    const auth = commandAuthority(q.command);
    const critical = isCritical(cmd);
    const caution = !critical && String((cmd || {}).criticality || "").toLowerCase() === "caution";
    const lbl = quickLabel(q);
    if (!auth.allowed) {
      // Disabled with its reason (hover and focus), not a lookalike chip.
      return `<button class="ds-btn" aria-disabled="true" data-reason="${esc(auth.text)}"
        aria-label="${esc(lbl + ": " + auth.text)}">${esc(lbl)}</button>`;
    }
    // data-quick carries the quick ENTRY name (unique), not the catalogue
    // command name: several quick entries share a command with different
    // preset args (AOCS_SET_MODE mode=2/3/4/5) and the args must survive.
    // FIELD DEFECT 2026-08-20: this carried `q.name || q.command`, and
    // sendQuick resolved it with .find() -- which returns the FIRST match.
    // Shipped entries without a `name:` collided on their bare command name,
    // so BOTH buttons of a pair fired the first entry's args: "DL Mode OFF"
    // sent TTC_SET_DOWNLINK_MODE(on=1) and "GPS Rx Off" sent
    // S2_AOCS_GPS_RECEIVER(state=1). Neither could be turned off from the
    // console, silently, while the button reported success. An index cannot
    // collide -- fixed by construction, not by config hygiene.
    const tip = esc(provenanceText(cmd));
    if (critical) {
      // armButton() wires the two-step after render (data-quick-crit, so the
      // delegated one-press handler never sees it).
      return `<button class="ds-btn critical" data-quick-crit="${q._qi}" title="${tip}"
        aria-label="${esc(tText("{{name}}, critical: press twice to send", { name: lbl }))}">${esc(lbl)}</button>`;
    }
    return `<button class="ds-btn" data-quick="${q._qi}" title="${tip}"` +
      (caution ? ` aria-label="${esc(tText("{{name}}, caution", { name: lbl }))}"` : "") + `>` +
      (caution ? glyph("warn-up") : "") + `${esc(lbl)}</button>`;
  };
  // Progressive disclosure: one collapsible group per subsystem, with a
  // count; open/closed survives re-renders; the filter narrows by label.
  const f = (S.qcFilter || "").toLowerCase();
  const match = (q) => !f || quickLabel(q).toLowerCase().includes(f) || String(q.command).toLowerCase().includes(f);
  S.qcOpen = S.qcOpen || {};
  setHTML("cmd-quick", Object.entries(groups).map(([g, qs]) => {
    const vis = qs.filter(match);
    if (!vis.length) return "";
    const nCrit = vis.filter((q) => isCritical(S.tcCatalog.find((c) => c.name === q.command))).length;
    const open = f || S.qcOpen[g] !== false;
    return `<details class="ds-disclosure qc-grp" data-qc-group="${esc(g)}"${open ? " open" : ""}>` +
      `<summary>${esc(tdb(`qcgroup:${g}:group`, g))}<span class="r">${vis.length}` +
      (nCrit ? ` · ${esc(tText("{{count}} critical", { count: nCrit }))}` : "") + `</span></summary>` +
      `<div class="bd"><div class="row">${vis.map(btn).join("")}</div></div></details>`;
  }).join("") ||
    `<div class="logrow nom">${f ? t("no command matches the filter") : t("no quick commands for this position")}</div>`);
  // per-subsystem in-place mirrors
  for (const pageId of SUB_PAGES) {
    const sub = PAGE_SUBSYSTEM[pageId];
    const mine = S.quickCommands.filter((q) => {
      const cmd = S.tcCatalog.find((c) => c.name === q.command) || {};
      const g = String(q.group || q.subsystem || cmd.subsystem || "").toLowerCase();
      return g.includes(sub) || (sub === "payload" && g.includes("pld")) ||
             (sub === "prop" && (g.includes("prop") || g.includes("prp")));
    });
    setHTML(`${pageId}-quick-list`, mine.length
      ? `<div class="row">${mine.map(btn).join("")}</div>`
      : `<div class="logrow nom">${t("no quick commands for {{sub}} — full builder on CMD", { sub })}</div>`);
  }
  wireCriticalQuick();
}
/* Critical quick commands: arm on the first press, send on the second within
 * 8 s (shared armButton: amber border, "Confirm: …", countdown, Esc cancels). */
function wireCriticalQuick() {
  if (typeof document === "undefined" || !document.querySelectorAll) return;
  document.querySelectorAll("[data-quick-crit]").forEach((b) => {
    armButton(b, { seconds: 8, onExecute: () => sendQuick(b.dataset.quickCrit, { confirmed: true }) });
  });
}

/* Quick-command label: YAML overlay qc:<name|command>:label, else the mnemonic. */
function quickLabel(q) {
  return q.label ? tdb(`qc:${q.name || q.command}:label`, q.label) : q.command;
}

/* 2026-08c item 5: the 10° HIGH-tier elevation rule is a GROUND policy —
 * the spacecraft accepts TTC_SET_DATA_RATE(HIGH) whenever its own link
 * state permits; it cannot know station elevation. The MCS warns
 * (arm-through) when HIGH is commanded below the policy threshold, from the
 * ground's contact geometry (0x050A) against ttc.yaml
 * tm_rate_tiers[HIGH].min_elevation_deg. */
function groundHighRateWarning(cmdName, rateVal) {
  if (cmdName !== "TTC_SET_DATA_RATE" || Number(rateVal) !== 1) return null;
  const ladder = S.state.tm_rate_ladder || [];
  const high = ladder.find((tr) => String(tr.name || "").toUpperCase() === "HIGH");
  const gate = high && Number(high.min_elevation_deg) > 0
    ? Number(high.min_elevation_deg) : 10;
  const el = Number(paramVal("0x050A"));
  const inContact = linkState(S.state).contact;
  if (inContact && Number.isFinite(el) && el >= gate) return null;
  const why = (!inContact || !Number.isFinite(el))
    ? tText("no station in contact — pass elevation unknown")
    : tText("current pass elevation {{el}}° is below {{gate}}°", { el: num(el, 1), gate: num(gate, 0) });
  return tText("GROUND policy hold (ttc.yaml HIGH min_elevation_deg {{gate}}°): {{why}}. The spacecraft will ACCEPT HIGH — there is no on-board elevation gate — but below the policy elevation the atmospheric loss and G/T de-rate cost real margin and raise BER.",
    { gate: num(gate, 0), why });
}

async function sendQuick(key, opts = {}) {
  // `key` is the quick ENTRY name; fall back to a bare catalogue name so
  // older callers keep working.
  // `key` is the entry's index (see renderQuickCommands). Numeric first; the
  // name lookup survives only for older callers, and is NOT what buttons use.
  const _i = Number(key);
  const q = (Number.isInteger(_i) && S.quickCommands[_i])
    || S.quickCommands.find((x) => (x.name || x.command) === key)
    || { command: key };
  const cmd = S.tcCatalog.find((c) => c.name === q.command);
  if (!cmd) return;
  const auth = commandAuthority(q.command);
  if (!auth.allowed) { announce(auth.text); return; }
  const ghWarn = groundHighRateWarning(q.command, (q.args || {}).rate);
  if (ghWarn) {
    const gk = "ghp:" + key;
    if (!S.armed[gk]) {
      S.armed[gk] = true;
      announce(tText("HOLD — {{why}} Press again within 8 s to send anyway.", { why: ghWarn }));
      setTimeout(() => { S.armed[gk] = false; }, 8000);
      return;
    }
    S.armed[gk] = false;
  }
  if (isCritical(cmd) && !opts.confirmed) {
    // arm→execute in place: first press arms, second within 8 s executes
    if (!S.armed[key]) {
      S.armed[key] = true;
      announce(tText("{{name}} ARMED — press again to execute", { name: q.label ? quickLabel(q) : cmd.name }));
      setTimeout(() => { S.armed[key] = false; }, 8000);
      return;
    }
    S.armed[key] = false;
  }
  // The quick entry's preset args ride through the SAME encoder as the
  // builder (AOCS_DETUMBLE is AOCS_SET_MODE with mode=2, not the default).
  const data = encodeCatalogCommand(cmd, q.args || {});
  const r = await sendPus({
    service: cmd.service, subtype: cmd.subtype, data_hex: data, name: cmd.name, position: S.position });
  announce(r.ok ? tText("{{name}} sent", { name: cmd.name }) : tText("{{name}} rejected", { name: cmd.name }));
}

/* ═══ 12. DIAG (L4) — PUS service panels + PARAMS ═════════════════════════ */

const DIAG_TABS = [["s3", "S3 HK"], ["s11", "S11 SCHED"], ["s6", "S6 MEMORY"],
  ["s15", "S15 STORES"], ["s12", "S12 MONITOR"], ["s19", "S19 EVT-ACT"],
  ["s9", "S9 TIME"], ["params", "PARAMS"]];

function buildDiagPage() {
  return `
  <div class="pad hide" id="page-diag" role="tabpanel" aria-label="Diagnostics" data-i18n-aria-label>
    <div class="pghd">
      <div><h1 class="pt" data-i18n>PUS services</h1>
        <p class="sub" data-i18n>All seven service panels from the classic PUS SERVICES tab —
          S3 housekeeping · S11 scheduler · S6 memory · S15 stores · S12 monitoring ·
          S19 event-action · S9 time — plus the parameter catalog. S12/S19 tables are
          the same renderer FDIR mounts (one implementation, two mounts).</p></div>
      <div class="fld"><label for="hdr-param-search" data-i18n>Parameter search (global)</label>
        <input id="hdr-param-search" class="in" placeholder="name or 0xHHHH" data-i18n-placeholder style="min-width:240px"></div>
    </div>
    <div class="ds-tabs" role="tablist" id="diag-tabs" aria-label="PUS service panels" data-i18n-aria-label="PUS service panels">
      ${DIAG_TABS.map(([id, l], i) =>
        `<button class="ds-tab" role="tab" data-diag="${id}" aria-selected="${i === 0}">${l}</button>`).join("")}
    </div>
    <div style="margin-top:12px">
      <div id="diag-s3" class="diag-pane"></div>
      <div id="diag-s11" class="diag-pane hide"></div>
      <div id="diag-s6" class="diag-pane hide"></div>
      <div id="diag-s15" class="diag-pane hide"></div>
      <div id="diag-s12" class="diag-pane hide"></div>
      <div id="diag-s19" class="diag-pane hide"></div>
      <div id="diag-s9" class="diag-pane hide"></div>
      <div id="diag-params" class="diag-pane hide"></div>
    </div>
  </div>`;
}

let diagTab = "s3";
function selectDiagTab(id) {
  diagTab = id;
  for (const [tid] of DIAG_TABS) {
    show(`diag-${tid}`, tid === id);
    const b = document.querySelector ? document.querySelector(`[data-diag="${tid}"]`) : null;
    if (b) b.setAttribute("aria-selected", tid === id ? "true" : "false");
  }
  renderDiag();
}

/* ── Live re-render of panels that used to update only on a click ─────────
 *
 * Field report 2026-08-20: "the PUS windows and the bottom windows do not
 * refresh properly - they need a user click to refresh".
 *
 * True, and by construction: renderCurrentPage(full) rebuilt the DIAG page
 * only when `full` was set, and `full` is set on navigation, not on the state
 * cadence. So HK ages, the S15 store fill, the S11 schedule, S12 monitor
 * values and every PARAMS value sat frozen at whatever they were when the tab
 * was opened. A console that shows a stale number as though it were live is
 * worse than one that shows nothing.
 *
 * These panels were left click-only for a real reason: they carry form inputs
 * and scrollable tables, and a naive rebuild throws away what the operator is
 * typing and where they have scrolled. So the rebuild is wrapped -- focus,
 * caret and scroll offsets are captured and restored around it, and a refresh
 * is SKIPPED outright while a dropdown inside the panel has focus, because
 * re-rendering under an open <select> yanks the rug mid-selection.
 */
function preservingUi(hostId, fn) {
  const host = $(hostId);
  if (!host) { fn(); return true; }
  const act = document.activeElement;
  if (act && host.contains(act) && (act.tagName === "SELECT" || act.tagName === "OPTION")) {
    return false;                       // operator is mid-interaction: leave it alone
  }
  const actId = act && host.contains(act) ? act.id : null;
  let selS = null, selE = null;
  if (actId) { try { selS = act.selectionStart; selE = act.selectionEnd; } catch (e) { /* not a text field */ } }
  // Scroll offsets are captured POSITIONALLY, not by id: the scrolling element
  // in these panels is usually an anonymous <div class="scroll-y"> with no id,
  // so an id-keyed capture silently restored nothing. A re-render of the same
  // panel reproduces the same element order, so index alignment holds; if the
  // shape changed (different tab, different row count) the lengths differ and
  // restoration is skipped rather than applied to the wrong element.
  const hostTop = host.scrollTop;
  const before = Array.prototype.map.call(host.querySelectorAll("*"), (el) => el.scrollTop);
  fn();
  host.scrollTop = hostTop;
  const after = host.querySelectorAll("*");
  if (after.length === before.length) {
    for (let i = 0; i < after.length; i++) {
      if (before[i]) after[i].scrollTop = before[i];
    }
  }
  if (actId) {
    const el2 = $(actId);
    if (el2) {
      el2.focus();
      if (selS !== null && el2.setSelectionRange) {
        try { el2.setSelectionRange(selS, selE); } catch (e) { /* not selectable */ }
      }
    }
  }
  return true;
}

// The PARAMS table can be ~400 rows, so the re-render is throttled. This is a
// PAINT budget, not a telemetry age: performance.now() is the right clock (and
// keeps simNow() the single wall-clock reader, disposition M3). Telemetry
// ages are still judged in sim seconds, by ageVerdict() above.
let _diagLastRender = 0;
function refreshDiagLive() {
  const now = (typeof performance !== "undefined" && performance.now)
    ? performance.now() : 0;
  if (now - _diagLastRender < 900) return;
  _diagLastRender = now;
  preservingUi(`diag-${diagTab}`, renderDiag);
}

function renderDiag() {
  if (diagTab === "s3") renderS3Panel();
  else if (diagTab === "s11") renderS11Panel();
  else if (diagTab === "s6") renderS6Panel();
  else if (diagTab === "s15") renderS15Panel();
  else if (diagTab === "s12") setHTML("diag-s12", renderS12Block("diag"));
  else if (diagTab === "s19") setHTML("diag-s19", renderS19Block("diag"));
  else if (diagTab === "s9") renderS9Panel();
  else if (diagTab === "params") renderParamsPanel();
}

/* — S3 HK manager — */
async function loadHkStructures() {
  try { S.hkStructures = await getJSON("/api/hk-structures"); }
  catch (e) { S.hkStructures = null; }
}
function hkObserved(sid) {
  const meta = ((S.hkStructures || {}).structures || []).find((s2) => Number(s2.sid) === Number(sid)) || {};
  const ages = S.state.hk_sid_age_s || {};
  // live state age first, then the /api/hk-structures observed snapshot
  const age = ages[String(sid)] !== undefined ? ages[String(sid)]
    : (meta.last_seen_age_s === null ? undefined : meta.last_seen_age_s);
  const interval = meta.interval_s || 60;
  if (age === undefined || age === null) return { label: tText("NEVER SEEN"), cls: "stale" };
  if (age <= interval * 2.5 + 1) return { label: tText("PERIODIC · {{age}}", { age: fmtAge(age) }), cls: "ok" };
  return { label: tText("SILENT · {{age}}", { age: fmtAge(age) }), cls: "warn" };
}
/** The enable bit the SPACECRAFT reported for a SID, or undefined. */
function hkEnabledBit(sid) {
  const rep = S.state.hk_enabled || {};
  if (rep[String(sid)] !== undefined) return !!rep[String(sid)];
  const meta = ((S.hkStructures || {}).structures || [])
    .find((s2) => Number(s2.sid) === Number(sid)) || {};
  return meta.enabled === null || meta.enabled === undefined
    ? undefined : !!meta.enabled;
}

/**
 * "Who turned my SIDs off?" A boot or a bootloader entry legitimately
 * replaces the on-board HK enable set with simulation.yaml
 * `default_enabled_sids`. The spacecraft raises S5 0x0056 and publishes the
 * same record (state.hk_enable_reset), which is printed here as an explicit
 * banner naming the SIDs it silenced and the fix (HK_ENABLE, TC 3,5).
 */
function hkEnableSummaryHtml() {
  const structures = ((S.hkStructures || {}).structures) || [];
  const on = [], off = [];
  for (const s2 of structures) {
    const bit = hkEnabledBit(s2.sid);
    if (bit === true) on.push(s2.sid);
    else if (bit === false) off.push(s2.sid);
  }
  const known = on.length || off.length;
  const line = known
    ? t("<strong>Enable set reported by the spacecraft:</strong> enabled [{{on}}] · disabled [{{off}}]",
      { on: on.join(", ") || "—", off: off.join(", ") || "—" })
    : t("Enable set not reported by the spacecraft — the Observed column is inferred from arriving telemetry.");
  const rst = S.state.hk_enable_reset;
  let why = "";
  if (rst && rst.reason) {
    const dis = rst.sids_disabled || [];
    why = `<div class="ds-banner warn" role="alert" style="margin-top:6px;white-space:normal;line-height:1.5">
      <strong>${t("The spacecraft reset the HK enable set itself")}</strong> — ${t("no HK_DISABLE was sent.")}<br>
      ${t("Reason: {{r}}", { r: String(rst.reason) })}<br>
      ${dis.length
        ? t("SID(s) switched off: <strong>{{sids}}</strong>. Periodic HK and S15 storage stopped for those SIDs, so a dump spanning this moment has a real gap. Re-send HK_ENABLE (TC 3,5) for each one.", { sids: dis.join(", ") })
        : t("No commanded SID was switched off by this reset.")}
    </div>`;
  }
  return `<div style="margin-bottom:8px;font-size:12px">${line}${why}</div>`;
}

function renderS3Panel() {
  const structures = ((S.hkStructures || {}).structures) || [];
  const rows = structures.map((s2) => {
    const obs = hkObserved(s2.sid);
    // /api/hk-structures serves `param_count`; older fixtures a list
    const nParams = s2.param_count ?? (s2.parameters || []).length;
    const bit = hkEnabledBit(s2.sid);
    const enChip = bit === undefined
      ? renderChip({ kind: "stale", label: tText("NOT REPORTED") })
      : renderChip({ kind: bit ? "ok" : "warn", label: bit ? tText("ENABLED") : tText("DISABLED") });
    return `<tr><td class="mono">${s2.sid}</td><td>${esc(s2.name || "")}</td>
      <td class="mono">${s2.apid ?? "—"}</td>
      <td class="mono">${s2.interval_s ?? "—"} s</td>
      <td class="mono">${nParams}</td>
      <td>${enChip}</td>
      <td>${renderChip({ kind: obs.cls === "ok" ? "ok" : obs.cls === "warn" ? "warn" : "stale", label: obs.label })}</td>
      <td class="s3-acts"><button class="ds-btn" data-s3="enable" data-sid="${s2.sid}"
            aria-label="${esc(tText("Enable SID {{sid}} (TC 3,5)", { sid: s2.sid }))}" title="${esc(tText("Enable SID {{sid}} (TC 3,5)", { sid: s2.sid }))}">${t("Enable")}</button>
          <button class="ds-btn" data-s3="disable" data-sid="${s2.sid}"
            aria-label="${esc(tText("Disable SID {{sid}} (TC 3,6)", { sid: s2.sid }))}" title="${esc(tText("Disable SID {{sid}} (TC 3,6)", { sid: s2.sid }))}">${t("Disable")}</button>
          <button class="ds-btn" data-s3="oneshot" data-sid="${s2.sid}"
            aria-label="${esc(tText("Request SID {{sid}} once (TC 3,27)", { sid: s2.sid }))}" title="${esc(tText("Request SID {{sid}} once (TC 3,27)", { sid: s2.sid }))}">${t("Request")}</button></td></tr>`;
  }).join("");
  setHTML("diag-s3", `
    <div class="ds-card"><h2>${t("Housekeeping manager (S3)")}</h2><div class="bd">
      ${hkEnableSummaryHtml()}
      <div class="row" style="margin-bottom:8px">
        <button class="ds-btn" id="s3-req-all">${t("REQUEST ALL (ONE-SHOT)")}</button>
        <button class="ds-btn" id="s3-en-all">${t("ENABLE ALL")}</button>
        <button class="ds-btn" id="s3-dis-all">${t("DISABLE ALL")}</button>
        <button class="ds-btn" id="s3-reload">${t("RELOAD DEFINITIONS")}</button>
      </div>
      <table class="plain"><thead><tr><th>SID</th><th>${t("Name")}</th><th>APID</th><th>${t("Interval")}</th>
        <th>${t("Params")}</th><th>${t("Enabled")}</th><th>${t("Observed")}</th><th></th></tr></thead>
        <tbody>${rows || `<tr><td colspan="8">${t("no HK structures")}</td></tr>`}</tbody></table>
    </div></div>`);
}
async function s3Command(action, sid) {
  const map = { enable: [3, 5], disable: [3, 6], oneshot: [3, 27] };
  const [svc, sub] = map[action];
  await sendPus({ service: svc, subtype: sub,
    data_hex: sidToHex(sid), name: `HK_${action.toUpperCase()}_SID${sid}`, position: S.position });
  announce(tText("{{name}} sent", { name: `S3 ${action} SID ${sid}` }));
}

/* — S11 scheduler — */
function renderS11Panel() {
  setHTML("diag-s11", `
    <div class="ds-card"><h2>${t("On-board schedule (S11)")}</h2><div class="bd">
      <div class="row" style="margin-bottom:8px">
        <button class="ds-btn" data-s11="refresh">REFRESH LIST (11,17)</button>
        <button class="ds-btn" data-s11="enable">ENABLE (11,13)</button>
        <button class="ds-btn" data-s11="disable">DISABLE (11,9)</button>
        <button class="ds-btn danger" data-s11="clear">${t("CLEAR ALL")}</button>
      </div>
      <div class="row">
        <div class="fld"><label for="s11-mode">${t("Time-tag mode")}</label>
          <select id="s11-mode" class="in">
            <option value="abs">${t("Absolute UTC")}</option>
            <option value="rel">${t("Relative now+N min")}</option>
            <option value="cuc">${t("Raw CUC seconds")}</option></select></div>
        <div class="fld"><label for="s11-time">${t("Time value")}</label>
          <input id="s11-time" class="in mono" placeholder="YYYY-MM-DDTHH:MM:SS / min / s"></div>
        <button class="ds-btn" id="s11-now">${t("NOW")}</button>
        <div class="fld"><label for="s11-cmd">${t("Catalogue command")}</label>
          <select id="s11-cmd" class="in" style="min-width:220px">
            <option value="">${t("— raw svc,sub —")}</option>
            ${S.tcCatalog.map((c) => `<option value="${esc(c.name)}">${esc(c.name)} (S${c.service},${c.subtype})</option>`).join("")}
          </select></div>
        <div class="fld"><label for="s11-svc">Svc,Sub</label>
          <input id="s11-svc" class="in mono" style="width:80px" placeholder="8,1"></div>
        <div class="fld"><label for="s11-data">${t("Data hex")}</label>
          <input id="s11-data" class="in mono" placeholder="24 …"></div>
        <button class="ds-btn primary" id="s11-add">ADD (11,4)</button>
      </div>
      <div style="font-size:12px;color:var(--tx3);margin-top:4px">
        ${t("Pick a catalogue command to pre-fill Svc,Sub and its default-argument hex (build non-default arguments on the CMD page and paste the hex here).")}</div>
      <div id="s11-preview" class="mono" style="font-size:12px;color:var(--tx3);margin:6px 0"></div>
      <table class="plain" id="s11-table"></table>
    </div></div>`);
  renderS11Table();
  loadS11Schedule();      // last TM(11,18) report from /api/schedule
  s11UpdatePreview();
}
export function s11CucSeconds(mode, value) {
  // live CUC preview: mission epoch J2000 unless the server tells us otherwise
  const epochIso = (S.state.time_correlation || {}).epoch || "2000-01-01T12:00:00Z";
  const epochMs = Date.parse(epochIso);
  if (mode === "cuc") return Number(value) || 0;
  if (mode === "rel") return Math.round((simNowMs() + (Number(value) || 0) * 60000 - epochMs) / 1000);
  const t = Date.parse(String(value).endsWith("Z") ? value : value + "Z");
  if (!Number.isFinite(t)) return null;
  return Math.round((t - epochMs) / 1000);
}
// Write a result or a refusal where the operator is actually looking.
//
// Field report 2026-08-20: ADD (11,4) "did nothing". It was in fact refusing —
// with an empty Svc,Sub you cannot build a valid time-tagged command — but it
// said so only through announce(), which writes to the screen-reader-only live
// region. A refusal nobody can see is indistinguishable from a dead button, so
// the reason now lands in the panel's own preview line, in the alarm colour.
function panelResult(id, msg, bad) {
  const el = $(id);
  if (el) {
    el.textContent = msg;
    el.style.color = bad ? "var(--alarm)" : "var(--tx3)";
  }
  announce(msg);
}
function s11UpdatePreview() {
  const mode = $("s11-mode") ? $("s11-mode").value : "abs";
  const v = $("s11-time") ? $("s11-time").value : "";
  const cuc = s11CucSeconds(mode, v);
  const el = $("s11-preview");
  if (el) el.style.color = "var(--tx3)";      // clear any previous refusal
  setText("s11-preview", cuc === null ? "CUC —" : `CUC ${cuc} (0x${(cuc >>> 0).toString(16).toUpperCase()})`);
}
async function loadS11Schedule() {
  try {
    const d = await getJSON("/api/schedule");
    if (d && !d.never_reported) S.s11Schedule = d;
  } catch (e) { /* offline */ }
  renderS11Table();
}
function s11EntryUtc(e) {
  // TM(11,18) rows carry exec_time_cuc (mission-epoch seconds)
  if (e.time_utc) return String(e.time_utc);
  const cuc = e.exec_time_cuc ?? e.cuc;
  if (cuc === undefined || cuc === null) return "";
  const epochIso = (S.state.time_correlation || {}).epoch || "2000-01-01T12:00:00Z";
  return fmtUTC(new Date(Date.parse(epochIso) + Number(cuc) * 1000), { date: true });
}
function renderS11Table() {
  const sch = S.s11Schedule;
  const rows = ((sch && sch.entries) || []).map((e) => {
    const cuc = e.exec_time_cuc ?? e.cuc;
    const cmd = S.tcCatalog.find((c) => Number(c.service) === Number(e.service) &&
      Number(c.subtype) === Number(e.subtype) &&
      (Number(c.service) !== 8 || Number(c.subtype) !== 1 ||
       (e.data_hex || "").slice(0, 2) === (c.func_id != null
         ? Number(c.func_id).toString(16).toUpperCase().padStart(2, "0") : "")));
    return `<tr>
    <td class="mono">${e.id ?? "—"}</td>
    <td class="mono">${esc(s11EntryUtc(e))}</td>
    <td class="mono">${cuc ?? "—"}</td>
    <td class="mono">S${e.service},${e.subtype}${cmd ? " " + esc(cmd.name) : ""}</td>
    <td class="mono">${esc(e.data || e.data_hex || "")}</td>
    <td><button class="ds-btn" data-s11-del="${e.id}">✕</button></td></tr>`;
  }).join("");
  setHTML("s11-table", `<thead><tr><th>ID</th><th>${t("Exec (UTC)")}</th><th>CUC</th><th>TC</th><th>${t("Data")}</th><th></th></tr></thead>
    <tbody>${rows || `<tr><td colspan="6">${sch ? t("schedule empty") : t("no schedule report — REFRESH (11,17)")}</td></tr>`}</tbody>` +
    (sch ? `<caption style="caption-side:bottom;text-align:left;font-size:12px;color:var(--tx3)">
      ${t("schedule {{state}} · {{count}} entries", { state: sch.enabled ? tText("ENABLED") : tText("DISABLED"),
        count: sch.count ?? ((sch.entries || []).length) })}` +
      `${sch.next_id != null ? " · " + t("next id {{id}}", { id: sch.next_id }) : ""}</caption>` : ""));
}
async function s11Command(action) {
  const map = { refresh: [11, 17, ""], enable: [11, 13, ""], disable: [11, 9, ""], clear: [11, 3, ""] };
  const [svc, sub, data] = map[action];
  await sendPus({ service: svc, subtype: sub, data_hex: data,
    name: `S11_${action.toUpperCase()}`, position: S.position });
  announce(tText("{{name}} sent", { name: `S11 ${action}` }));
  if (action === "refresh") setTimeout(loadS11Schedule, 800);
}
async function s11Add() {
  const mode = $("s11-mode").value;
  const cuc = s11CucSeconds(mode, $("s11-time").value);
  const svcSub = String($("s11-svc").value || "").split(",").map((x) => Number(x.trim()));
  const badTime = cuc === null;
  const badSvc = svcSub.length !== 2 || svcSub.some((x) => !Number.isFinite(x));
  if (badTime || badSvc) {
    panelResult("s11-preview", tText("ADD refused — {{why}}", { why:
      badTime && badSvc
        ? tText("no time value and no Svc,Sub. Pick a catalogue command (it fills both), or press NOW and type Svc,Sub.")
        : badTime ? tText("the time value is empty or unparseable for this time-tag mode. Press NOW for a starting point.")
        : tText("Svc,Sub is empty. Pick a catalogue command to fill it, or type it (e.g. 8,1).") }), true);
    return;
  }
  const dataHex = String($("s11-data").value || "").replace(/[\s,]+/g, "");
  const cucBytes = [(cuc >>> 24) & 255, (cuc >>> 16) & 255, (cuc >>> 8) & 255, cuc & 255];
  const payload = cucBytes.concat([svcSub[0], svcSub[1]])
    .map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ") +
    (dataHex ? " " + dataHex.replace(/(..)/g, "$1 ").trim() : "");
  await sendPus({ service: 11, subtype: 4, data_hex: payload,
    name: "S11_ADD", position: S.position });
  panelResult("s11-preview",
    tText("ADD sent — CUC {{cuc}} ({{hex}}), {{tc}}",
      { cuc, hex: `0x${(cuc >>> 0).toString(16).toUpperCase()}`, tc: `S${svcSub[0]},${svcSub[1]}` }) +
    (dataHex ? " " + tText("+ {{n}} arg byte(s)", { n: dataHex.length / 2 }) : ""), false);
}
async function s11Delete(id) {
  const v = Number(id) >>> 0;
  const data = [(v >>> 8) & 255, v & 255].map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
  await sendPus({ service: 11, subtype: 5, data_hex: data,
    name: `S11_DELETE_${id}`, position: S.position });
}

/* — S6 memory — */
async function loadMemoryMap() {
  try { S.memoryMap = await getJSON("/api/memory-map"); }
  catch (e) { S.memoryMap = null; }
}
export function crc16Ccitt(hexStr) {
  const s2 = String(hexStr || "").replace(/[\s,]+/g, "");
  let crc = 0xFFFF;
  for (let i = 0; i < s2.length; i += 2) {
    const b = parseInt(s2.substr(i, 2), 16) || 0;
    crc ^= b << 8;
    for (let k = 0; k < 8; k++)
      crc = crc & 0x8000 ? ((crc << 1) ^ 0x1021) & 0xFFFF : (crc << 1) & 0xFFFF;
  }
  return crc;
}
function renderS6Panel() {
  const regions = ((S.memoryMap || {}).regions) || [];
  setHTML("diag-s6", `
    <div class="ds-card"><h2>${t("Memory (S6)")}</h2><div class="bd">
      <div class="row">
        <div class="fld"><label for="s6-region">${t("Region")}</label>
          <select id="s6-region" class="in">${regions.map((r) =>
            `<option value="${esc(String(r.start ?? r.address ?? 0))}">${esc(r.name || "region")}</option>`).join("")}
          </select></div>
        <div class="fld"><label for="s6-addr">${t("Address (hex)")}</label>
          <input id="s6-addr" class="in mono" value="0" style="width:110px"></div>
        <div class="fld"><label for="s6-len">${t("Length")}</label>
          <input id="s6-len" class="in" type="number" value="64" style="width:80px"></div>
        <div class="fld"><label for="s6-memid">${t("Memory id")}</label>
          <input id="s6-memid" class="in" type="number" value="1" style="width:60px"></div>
        <button class="ds-btn" id="s6-dump">DUMP (6,5)</button>
        <button class="ds-btn" id="s6-crc">CRC CHECK (6,9)</button>
      </div>
      <div class="row" style="margin-top:8px">
        <div class="fld" style="flex:1"><label for="s6-patch">${t("Patch data (hex)")}</label>
          <input id="s6-patch" class="in mono" placeholder="DE AD …"></div>
        <input type="file" id="s6-file" aria-label="${t("Patch file")}">
        <button class="ds-btn" id="s6-load">1. LOAD (6,2)</button>
        <button class="ds-btn" id="s6-verify">2. VERIFY (6,9)</button>
        <button class="ds-btn" id="s6-readback">READ BACK (6,5)</button>
        <span id="s6-localcrc" class="mono" style="font-size:12px;color:var(--tx3)"></span>
      </div>
      <table class="plain" style="margin-top:8px"><thead><tr><th>${t("Region")}</th><th>${t("Start")}</th><th>${t("Size")}</th><th>${t("Writable")}</th></tr></thead>
        <tbody>${regions.map((r) => `<tr><td>${esc(r.name || "")}</td>
          <td class="mono">0x${Number(r.start ?? r.address ?? 0).toString(16).toUpperCase().padStart(8, "0")}</td>
          <td class="mono">${r.size ?? r.length ?? "—"}</td><td>${r.writable ? t("yes") : t("no")}</td></tr>`).join("") ||
          `<tr><td colspan="4">${t("memory map unavailable")}</td></tr>`}</tbody></table>
      <div id="s6-dump-view" class="mono" style="font-size:12px;margin-top:8px;white-space:pre-wrap"></div>
      <div id="s6-check-view" class="mono" style="font-size:12px;margin-top:4px"></div>
    </div></div>`);
}
function s6AddrBytes() {
  const memId = Number($("s6-memid").value) & 0xFF;
  const addr = parseInt($("s6-addr").value, 16) >>> 0;
  const len = Number($("s6-len").value) >>> 0;
  const b = [memId,
    (addr >>> 24) & 255, (addr >>> 16) & 255, (addr >>> 8) & 255, addr & 255,
    (len >>> 24) & 255, (len >>> 16) & 255, (len >>> 8) & 255, len & 255];
  return b.map((x) => x.toString(16).toUpperCase().padStart(2, "0")).join(" ");
}
async function s6Command(subtype, extraHex) {
  const data = s6AddrBytes() + (extraHex ? " " + extraHex : "");
  await sendPus({ service: 6, subtype, data_hex: data,
    name: `S6_${subtype}`, position: S.position });
  announce(tText("{{name}} sent", { name: `S6.${subtype}` }));
}
function renderMemoryDump(d) {
  const bytes = d.data || d.bytes || [];
  const hexRows = [];
  for (let i = 0; i < bytes.length; i += 16) {
    const chunk = bytes.slice(i, i + 16);
    hexRows.push(`0x${(Number(d.address) + i).toString(16).toUpperCase().padStart(8, "0")}  ` +
      chunk.map((b) => Number(b).toString(16).toUpperCase().padStart(2, "0")).join(" "));
  }
  setHTML("s6-dump-view", esc(hexRows.join("\n")) || t("empty dump"));
}
function renderMemoryCheck(c) {
  setHTML("s6-check-view", `CRC 0x${Number(c.address).toString(16).toUpperCase().padStart(8, "0")} ` +
    `(${c.length} B) = <b>0x${Number(c.crc).toString(16).toUpperCase().padStart(4, "0")}</b>`);
}

/* — S15 storage — */
function renderS15Panel() {
  const stores = [[1, "HK_Store"], [2, "Event_Store"], [3, "Science_Store"], [4, "Alarm_Store"]];
  const status = S.state.storage_status || [];
  setHTML("diag-s15", `
    <div class="row" style="margin-bottom:8px">
      <button class="ds-btn" data-s15st="refresh">REFRESH STATUS (15,13)</button></div>
    <div class="g" style="grid-template-columns:repeat(auto-fill,minmax(240px,1fr))">
    ${stores.map(([id, nm]) => {
      const st2 = status.find((s3) => Number(s3.id) === id) || {};
      const detail = st2.count !== undefined
        ? `${st2.count}${st2.capacity ? " / " + st2.capacity : ""} ${tText("packets")} · ${st2.enabled ? tText("ENABLED") : tText("disabled")}` +
          `${st2.circular ? " · " + tText("circular") : ""}${st2.wrap_count ? " · " + tText("{{n}} wraps", { n: st2.wrap_count }) : ""}`
        : "";
      return `<div class="ds-card"><h2>${id} · ${esc(st2.name || nm)}</h2><div class="bd">
        <div class="mono" style="font-size:14px">${st2.fill_pct !== undefined ? t("{{v}} % full", { v: num(st2.fill_pct, 1) }) : t("no report — REFRESH STATUS (15,13)")}
          ${st2.overflow ? renderChip({ kind: "alarm", label: tText("OVERFLOW") }) : ""}</div>
        ${detail ? `<div style="font-size:12px;color:var(--tx3)">${esc(detail)}</div>` : ""}
        <div class="row" style="margin-top:6px">
          <button class="ds-btn" data-s15st="enable" data-store="${id}">EN (15,1)</button>
          <button class="ds-btn" data-s15st="disable" data-store="${id}">DIS (15,2)</button>
          <button class="ds-btn" data-s15st="dump" data-store="${id}">DUMP (15,9)</button>
          <button class="ds-btn danger" data-s15st="clear" data-store="${id}">${t("CLEAR")}</button>
        </div></div></div>`;
    }).join("")}
    </div>`);
}
async function s15StoreCommand(action, storeId) {
  const map = { enable: 1, disable: 2, dump: 9, clear: 11, refresh: 13 };
  const subtype = map[action];
  const data = storeId ? (Number(storeId) & 0xFF).toString(16).toUpperCase().padStart(2, "0") : "";
  await sendPus({ service: 15, subtype, data_hex: data,
    name: `S15_${action.toUpperCase()}`, position: S.position });
  announce(tText("{{name}} sent", { name: `S15 ${action}` }));
}

/* — S9 time — */
function renderS9Panel() {
  const tc = S.state.time_correlation || {};
  const cuc = fmtCUC(tc.sc_cuc_coarse, tc.sc_cuc_fine, tc.epoch);
  const stateCls = tc.offset_state === "alarm" ? "alarm" : tc.offset_state === "warning" ? "warn" : "ok";
  setHTML("diag-s9", `
    <div class="ds-card"><h2>${t("Time correlation (S9)")}</h2><div class="bd">
      <table class="plain"><tbody>
        <tr><td>${t("Ground (mission clock)")}</td><td class="mono">${fmtUTC(simNow(), { date: true })}</td></tr>
        <tr><td>${t("OBC UTC ({{src}})", { src: `TM 0x0309${tc.cuc_fine_available ? " + " + tText("fine") : ""}` })}</td><td class="mono">${esc(cuc.utc)}</td></tr>
        <tr><td>${t("OBC CUC raw")}</td><td class="mono">${esc(cuc.raw)}</td></tr>
        <tr><td>${t("Offset (sc − ground)")}</td><td class="mono">${tc.offset_s === null || tc.offset_s === undefined ? "—" : num(tc.offset_s, 3) + " s"}
          ${renderChip({ kind: stateCls, label: tc.offset_state && tc.offset_state !== "unknown" ? String(tc.offset_state).toUpperCase() : tText("UNKNOWN") })}</td></tr>
        <tr><td>${t("Time reference")}</td><td class="mono">${esc(tc.time_ref_name || "—")}</td></tr>
        <tr><td>${t("Since last sync")}</td><td class="mono">${tc.never_synced ? t("NEVER SYNCED") : fmtAge(tc.time_since_sync_s)}</td></tr>
      </tbody></table>
      <div class="row" style="margin-top:8px">
        <button class="ds-btn" id="s9-report">REQUEST TIME REPORT (9,2)</button>
        <button class="ds-btn" id="s9-sync">${t("SYNC TIME TO GROUND")}</button>
        <div class="fld"><label for="s9-set">${t("Set SC time (UTC)")}</label>
          <input id="s9-set" class="in mono" placeholder="YYYY-MM-DDTHH:MM:SS"></div>
        <button class="ds-btn" id="s9-set-now">${t("NOW")}</button>
        <button class="ds-btn" id="s9-set-send">${t("SET SC TIME")}</button>
      </div>
      <div id="s9-preview" class="mono" style="font-size:12px;color:var(--tx3);margin-top:6px"></div>
    </div></div>`);
  s9UpdatePreview();
}
function s9CucFor(iso) {
  const epochIso = (S.state.time_correlation || {}).epoch || "2000-01-01T12:00:00Z";
  const t = iso ? Date.parse(String(iso).endsWith("Z") ? iso : iso + "Z") : simNowMs();
  if (!Number.isFinite(t)) return null;
  return Math.round((t - Date.parse(epochIso)) / 1000);
}
function s9UpdatePreview() {
  const cuc = s9CucFor($("s9-set") ? $("s9-set").value : "");
  const el = $("s9-preview");
  if (el) el.style.color = "var(--tx3)";      // clear any previous refusal
  setText("s9-preview", cuc === null ? "CUC —" : `CUC ${cuc} (0x${(cuc >>> 0).toString(16).toUpperCase().padStart(8, "0")})`);
}
async function s9SetTime(iso) {
  const cuc = s9CucFor(iso);
  if (cuc === null) {
    panelResult("s9-preview",
      tText("SET SC TIME refused — the time value is empty or unparseable. Press NOW to fill it."), true);
    return;
  }
  const v = cuc >>> 0;
  const data = [(v >>> 24) & 255, (v >>> 16) & 255, (v >>> 8) & 255, v & 255]
    .map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
  await sendPus({ service: 9, subtype: 1, data_hex: data,
    name: "S9_SET_TIME", position: S.position });
  panelResult("s9-preview",
    tText("SET SC TIME sent — CUC {{cuc}} ({{hex}})", { cuc: v, hex: `0x${v.toString(16).toUpperCase().padStart(8, "0")}` }), false);
}

/* — PARAMS panel (classic ON-DEMAND TM tab relocated here) — */
let paramsFilter = "";
let paramsOnDemandOnly = false;
function renderParamsPanel() {
  const f = paramsFilter.toLowerCase();
  const list = S.paramCatalog.filter((p) =>
    (!paramsOnDemandOnly || p.on_demand) &&
    (!f || (p.name || "").toLowerCase().includes(f) || (p.hex || "").toLowerCase().includes(f)));
  const rows = list.slice(0, 400).map((p) => {
    // One readout per row in its data state: live, stale (last value kept,
    // dim italic, age), never received ("no data"), HK disabled
    // ("not enabled"); sentinels read as words ("never synced").
    return `<tr>
      <td class="mono hexid">${esc(p.hex)}</td><td>${esc(p.name)}</td><td>${esc(p.subsystem)}</td>
      <td>${p.in_hk ? "HK" : ""}</td><td>${p.on_demand ? "OD" : ""}</td>
      <td class="num">${valueCell(p.hex, null, p.units || "")}</td>
      <td>${p.origin !== "station" && (p.on_demand || !p.in_hk)
        ? `<button class="ds-btn sm" data-od-get="${esc(p.hex)}"
            aria-label="${esc(tText("Fetch {{name}} on demand, TC(20,3)", { name: p.name }))}">${t("Get")} (20,3)</button>` : ""}</td></tr>`;
  }).join("");
  setHTML("diag-params", `
    <div class="ds-card"><h2>${t("Parameter catalog · TC(20,3) on-demand fetch")}</h2><div class="bd">
      <div class="row" style="margin-bottom:6px">
        <input id="params-filter" class="in" placeholder="${t("filter…")}" aria-label="${t("Filter parameters")}" value="${esc(paramsFilter)}">
        <label style="font-size:12px"><input type="checkbox" id="params-od" ${paramsOnDemandOnly ? "checked" : ""}> ${t("on-demand only")}</label>
        <button class="ds-btn" id="params-refresh">${t("Refresh")}</button>
        <span style="font-size:12px;color:var(--tx3)">${t("{{count}} parameters", { count: list.length })}</span>
      </div>
      <div class="scroll-y" style="max-height:420px">
      <table class="plain"><thead><tr><th>ID</th><th>${t("Name")}</th><th>${t("Subsys")}</th>
        <th>HK</th><th>OD</th><th class="n">${t("Value")}</th><th><span class="ds-sr">${t("Action")}</span></th></tr></thead><tbody>${rows}</tbody></table>
      </div></div></div>`);
}
async function onDemandGet(hexId) {
  const pid = parseInt(hexId, 16) >>> 0;
  const data = [(pid >>> 8) & 255, pid & 255]
    .map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
  await sendPus({ service: 20, subtype: 3, data_hex: data,
    name: `OD_GET_${hexId}`, position: S.position });
  setTimeout(async () => {
    try { handleState(await getJSON("/api/state")); renderDiag(); } catch (e) { /* offline */ }
  }, 250);
}

/* ═══ 13. FDIR — shared S12/S19 renderers, autonomy per M4 ════════════════ */

async function loadFdir() {
  try { S.fdir = await getJSON("/api/fdir"); }
  catch (e) { S.fdir = null; }
  if (S.page === "fdir") renderFdirPage();
  if (S.page === "diag" && (diagTab === "s12" || diagTab === "s19")) renderDiag();
}

/* ONE implementation, two mounts (FDIR + DIAG). */
let s12Filter = "";
let s12OolOnly = false;
export function renderS12Block(mount) {
  const monitors = ((S.fdir || {}).monitors) || ((S.fdir || {}).s12) || [];
  // /api/fdir marks a violated monitor with status "VIOLATION"; older
  // fixtures use out_of_limits. Accept both (this was one of the "content is
  // not available" data-path breaks — OOL state never rendered live).
  const isOol = (m) => !!m.out_of_limits || m.state === "out_of_limits" ||
    /viol|out/i.test(String(m.status || ""));
  const f = s12Filter.toLowerCase();
  const list = monitors.filter((m) =>
    (!s12OolOnly || isOol(m)) &&
    (!f || JSON.stringify(m).toLowerCase().includes(f)));
  const rows = list.map((m) => `<tr class="${isOol(m) ? "a" : ""}">
    <td class="mono">${m.mon_id ?? m.id ?? "—"}</td>
    <td class="mono">${hex4(m.param_id)}</td>
    <td>${esc(m.name || m.param_name ||
      (S.paramByHex[hex4(m.param_id)] ? S.paramByHex[hex4(m.param_id)].name : ""))}</td>
    <td>${esc(String(m.check_type_name ?? m.check_type ?? m.type ?? ""))}</td>
    <td class="mono">${num(m.low_limit ?? m.low, 2)}</td>
    <td class="mono">${num(m.high_limit ?? m.high, 2)}</td>
    <td class="mono">${m.current_value === null || m.current_value === undefined
      ? "—" : num(m.current_value, 2)}</td>
    <td>${m.enabled ? "EN" : "dis"}</td>
    <td>${isOol(m) ? renderChip({ kind: "alarm", label: "OOL" })
      : esc(String(m.status || ""))}</td>
    <td><button class="ds-btn" data-s12row="enable" data-mid="${m.mon_id ?? m.id}">EN</button>
        <button class="ds-btn" data-s12row="disable" data-mid="${m.mon_id ?? m.id}">DIS</button>
        <button class="ds-btn" data-s12row="delete" data-mid="${m.mon_id ?? m.id}">✕</button></td></tr>`).join("");
  return `
    <div class="ds-card"><h2>${t("On-board monitoring (S12)")} <span class="r">${t("{{mount}} mount — one renderer", { mount })}</span></h2>
      <div class="bd">
      <div class="row" style="margin-bottom:6px">
        <button class="ds-btn" data-s12="refresh">REFRESH (12,12)</button>
        <button class="ds-btn" data-s12="enable">ENABLE MON (12,1)</button>
        <button class="ds-btn" data-s12="disable">DISABLE MON (12,2)</button>
        <input class="in" data-s12filter placeholder="${t("filter…")}" value="${esc(s12Filter)}">
        <label style="font-size:12px"><input type="checkbox" data-s12ool ${s12OolOnly ? "checked" : ""}> ${t("out-of-limits only")}</label>
      </div>
      <div class="row" style="margin-bottom:6px">
        <input class="in mono" id="s12-add-mid-${mount}" placeholder="${t("mon id")}" style="width:70px">
        <input class="in mono" id="s12-add-pid-${mount}" placeholder="${t("param 0xHHHH")}" style="width:110px">
        <select class="in" id="s12-add-type-${mount}" aria-label="${t("Check type")}"><option value="0">${t("absolute")}</option><option value="1">${t("delta")}</option></select>
        <input class="in mono" id="s12-add-low-${mount}" placeholder="${t("low")}" style="width:80px">
        <input class="in mono" id="s12-add-high-${mount}" placeholder="${t("high")}" style="width:80px">
        <button class="ds-btn" data-s12add="${mount}">ADD (12,6)</button>
      </div>
      <table class="plain"><thead><tr><th>${t("Mon")}</th><th>${t("Param")}</th><th>${t("Name")}</th><th>${t("Check")}</th>
        <th>${t("Low")}</th><th>${t("High")}</th><th>${t("Value")}</th><th>En</th><th>${t("State")}</th><th></th></tr></thead>
        <tbody>${rows || `<tr><td colspan="10">${t("no monitor table — REFRESH (12,12)")}</td></tr>`}</tbody></table>
      </div></div>`;
}
export function renderS19Block(mount) {
  // /api/fdir serves the rule table under `rules` (row shape: ea_id, name,
  // trigger_kind_name, trigger_label, action_label, fire_count). The old
  // code only read `ea_rules`/`s19`, so the LIVE rule table always rendered
  // "no rule table" — the core of defect "PUS content is not available".
  const rules = ((S.fdir || {}).ea_rules) || ((S.fdir || {}).s19) ||
                ((S.fdir || {}).rules) || [];
  const actions = S.tcCatalog.map((c) => c.name);
  const rows = rules.map((r) => `<tr>
    <td class="mono">${r.ea_id ?? r.id ?? "—"}</td>
    <td>${esc(String(r.name || ""))}</td>
    <td>${esc(String(r.trigger_kind_name ||
      (Number(r.trigger_kind) === 1 ? tText("S12 param") : tText("S5 event"))))}</td>
    <td class="mono">${esc(String(r.trigger_label || hex4(r.trigger_value ?? r.trigger_id)))}</td>
    <td>${esc(String(r.action || r.action_name || r.action_label ||
      (r.action_func_id != null ? `func ${r.action_func_id}` : "")))}</td>
    <td>${r.enabled ? "EN" : "dis"}</td>
    <td class="mono">${r.fire_count ?? "—"}</td>
    <td><button class="ds-btn" data-s19row="enable" data-eid="${r.ea_id ?? r.id}">EN</button>
        <button class="ds-btn" data-s19row="disable" data-eid="${r.ea_id ?? r.id}">DIS</button>
        <button class="ds-btn" data-s19row="delete" data-eid="${r.ea_id ?? r.id}">✕</button></td></tr>`).join("");
  return `
    <div class="ds-card"><h2>${t("Event-action rules (S19)")} <span class="r">${t("{{mount}} mount — one renderer", { mount })}</span></h2>
      <div class="bd">
      <div class="row" style="margin-bottom:6px">
        <button class="ds-btn" data-s19="refresh">REFRESH (19,8)</button>
        <input class="in mono" id="s19-add-eid-${mount}" placeholder="${t("EA id")}" style="width:70px">
        <select class="in" id="s19-add-kind-${mount}" aria-label="${t("Trigger kind")}">
          <option value="0">${t("0 — S5 event id")}</option><option value="1">${t("1 — S12 parameter id")}</option></select>
        <input class="in mono" id="s19-add-trig-${mount}" placeholder="${t("trigger 0xHHHH")}" style="width:110px">
        <select class="in" id="s19-add-action-${mount}" aria-label="${t("Action")}">${actions.map((a) => `<option>${esc(a)}</option>`).join("")}</select>
        <button class="ds-btn" data-s19add="${mount}">ADD RULE (19,1)</button>
      </div>
      <table class="plain"><thead><tr><th>EA</th><th>${t("Name")}</th><th>${t("Kind")}</th><th>${t("Trigger")}</th>
        <th>${t("Action")}</th><th>En</th><th>${t("Fires")}</th><th></th></tr></thead>
        <tbody>${rows || `<tr><td colspan="8">${t("no rule table — REFRESH (19,8)")}</td></tr>`}</tbody></table>
      </div></div>`;
}

function buildFdirPage() {
  return `
  <div class="pad hide" id="page-fdir" role="tabpanel" aria-label="FDIR">
    <h1 class="pt" data-i18n>Fault detection, isolation &amp; recovery</h1>
    <p class="sub" data-i18n-html>What the spacecraft <em>told</em> us (S5 / S12 / S19 / mode), plus recovery controls.</p>
    <div class="ds-card"><h2 data-i18n>FDIR state</h2><div class="bd row" id="fdir-strip" style="gap:18px"></div></div>
    <div class="row" style="margin:10px 0">
      <button class="ds-btn" id="fdir-refresh-all" data-i18n>REFRESH ALL</button>
      <button class="ds-btn" data-s12="refresh">REPORT MONITORS (12,12)</button>
      <button class="ds-btn" data-s19="refresh">REPORT RULES (19,8)</button>
      <button class="ds-btn" data-s12="enable">ENABLE MONITORING (12,1)</button>
      <button class="ds-btn" data-s12="disable">DISABLE MONITORING (12,2)</button>
      <button class="ds-btn" id="fdir-ack-all" data-i18n>ACK ALL ALARMS</button>
    </div>
    <div id="fdir-autonomy-host"></div>
    <div class="g" style="grid-template-columns:1fr;margin-top:10px">
      <div id="fdir-s12"></div>
      <div id="fdir-s19"></div>
      <div class="ds-card"><h2 data-i18n>Alarm / anomaly journal</h2><div class="bd">
        <div class="row" style="font-size:12px;margin-bottom:6px">
          ${["s5:S5 events", "s12:S12 transitions", "s19:S19 rule fires", "tcrej:TC rejections", "mode:mode changes"]
            .map((x) => { const [k, l] = x.split(":");
              return `<label data-i18n><input type="checkbox" data-fdir-j="${k}" checked> ${l}</label>`; }).join(" ")}
        </div>
        <div class="scroll-y" style="max-height:240px" id="fdir-journal"></div>
      </div></div>
    </div>
  </div>`;
}

function renderFdirPage() {
  const d = S.fdir || {};
  // /api/fdir nests the summary under `state` (fdir_level, safe_latched,
  // load_shed_stage, monitors_out_of_limits); the old flat keys never
  // existed, so the whole strip rendered "—". Accept both shapes.
  const fst = d.state || {};
  const mode = scModeInfo();
  const oolCount = fst.monitors_out_of_limits ??
    (d.monitors || []).filter((m) => m.out_of_limits ||
      /viol|out/i.test(String(m.status || ""))).length;
  const strip = [
    // Same source as the contingency banner (modeState): TM fdir.level 0x0700.
    [tText("FDIR LEVEL"), fdirLevelInfo() !== null
      ? (FDIR_LEVELS[fdirLevelInfo()] ?? String(fdirLevelInfo()))
      : (fst.fdir_level ?? d.fdir_level ?? "—"),
      fdirLevelInfo() !== null ? "TM 0x0700" : ""],
    [tText("SC MODE"), mode.label, tText("src: {{src}}", { src: mode.src })],
    [tText("LATCHED"), (fst.safe_latched ?? d.latched_safe) ? "SAFE"
      : (fst.emergency_latched ?? d.latched_emergency) ? "EMERG" : "—",
      fst.latch_source || ""],
    [tText("LOAD SHED"), fst.load_shed_stage ?? paramVal("0x0134") ?? "—", ""],
    [tText("MONITORS OOL"), oolCount, ""],
    // Two different quantities, labelled as such: the spacecraft's own
    // FDIR alarm count (TM) and the ground alarm store (the drawer).
    [tText("GROUND ALARMS"), alarmSummary().active, tText("{{n}} unacknowledged", { n: alarmSummary().unacked })],
    [tText("ON-BOARD ALARMS"), paramVal("0x0701") ?? (d.active_alarms || []).length, "TM 0x0701"],
  ];
  setHTML("fdir-strip", strip.map(([k, v, s2]) => `
    <div><div style="font-size:12px;letter-spacing:1px;color:var(--tx3)">${esc(k)}</div>
    <div class="mono" style="font-size:16px;font-weight:600">${esc(String(v))}</div>
    ${s2 ? `<div style="font-size:12px;color:var(--tx3)">${esc(s2)}</div>` : ""}</div>`).join(""));

  // M4: SIMULATED ON-BOARD AUTONOMY — sim mode only, retitled; real mode
  // shows the TM-derived story instead (designed empty state, not accident).
  const host = $("fdir-autonomy-host");
  if (host) {
    if (S.timeMode === "sim" && (S.state.sim_health || {}).fdir) {
      const a = S.state.sim_health.fdir;
      host.innerHTML = `<div class="ds-card"><h2>${t("SIMULATED ON-BOARD AUTONOMY")}
        <span class="r">${t("instructor truth — not downlinked")}</span></h2><div class="bd">
        <div class="row" style="gap:18px">
          <div>${t("active faults:")} <b class="mono">${(a.active_faults || []).length}</b></div>
          <div>${t("pending cascades:")} <b class="mono">${(a.pending_cascades || []).length}</b></div>
          <div>${t("recovery attempts:")} <b class="mono">${(a.recovery_attempts || []).length || (a.recoveries || []).length || 0}</b></div>
        </div>
        ${(a.procedures || []).map((p) => `<div style="margin-top:6px;font-size:12.5px">
          ${p.name ? esc(p.name) : t("on-board procedure")} — ${num(p.progress, 0)} %</div>`).join("")}
        </div></div>`;
    } else {
      host.innerHTML = `<div class="ds-card"><h2>${t("On-board autonomy — as telemetered")}</h2>
        <div class="bd" style="font-size:13px;color:var(--tx2)">
        ${t("A real spacecraft does not downlink its fault-cascade queue. The honest ground view is what it <em>told</em> us: S5 events (drawer below), S12 monitor transitions (table), S19 rule fires, and the mode itself ({{mode}}, {{src}}).",
          { mode: mode.label, src: mode.src })}</div></div>`;
    }
  }
  setHTML("fdir-s12", renderS12Block("fdir"));
  setHTML("fdir-s19", renderS19Block("fdir"));
  renderFdirJournal();
}
const fdirJournalFilter = { s5: true, s12: true, s19: true, tcrej: true, mode: true };
function renderFdirJournal() {
  const j = ((S.fdir || {}).journal) || [];
  const rows = j.filter((e) => {
    const kind = String(e.kind || e.type || "").toLowerCase();
    if (kind.includes("rej")) return fdirJournalFilter.tcrej;
    if (kind.includes("s12") || kind.includes("monitor")) return fdirJournalFilter.s12;
    if (kind.includes("s19") || kind.includes("rule")) return fdirJournalFilter.s19;
    if (kind.includes("mode")) return fdirJournalFilter.mode;
    return fdirJournalFilter.s5;
  }).slice(-80).reverse().map((e) => renderEventRow({
    severity: e.severity, subsystem: e.subsystem, utc: e.utc || fmtUTC(e.timestamp),
    description: e.text || e.message || e.description })).join("");
  setHTML("fdir-journal", rows || `<div class="logrow nom">${t("journal empty")}</div>`);
}

/* ═══ 14. PROC — procedures ═══════════════════════════════════════════════ */

function buildProcPage() {
  return `
  <div class="pad hide" id="page-proc" role="tabpanel" aria-label="Procedures" data-i18n-aria-label>
    <h1 class="pt" data-i18n>Procedures</h1>
    <p class="sub" data-i18n>Loader · step-by-step runner · document viewer · manual override · builder.
      Reachable from any alarm row (P7.6).</p>
    <div class="g" style="grid-template-columns:minmax(0,1fr) 420px;align-items:start">
      <div class="g">
        <div class="ds-card"><h2 data-i18n>Load &amp; run</h2><div class="bd">
          <div class="row">
            <div class="fld"><label for="proc-source" data-i18n>Source</label>
              <select id="proc-source" class="in">
                <option value="activity" data-i18n>Activity type</option>
                <option value="ops" data-i18n>Ops procedure</option>
                <option value="saved" data-i18n>Saved procedure</option></select></div>
            <div class="fld"><label for="proc-type" data-i18n>Procedure</label>
              <select id="proc-type" class="in" style="min-width:260px"></select></div>
            <label style="font-size:12px" data-i18n><input type="checkbox" id="proc-stepwise" checked> step-by-step</label>
          </div>
          <!-- Enabled from the runner's state machine (R3 A5): a disabled
               control stays focusable and says why on hover and focus. -->
          <div class="ctl-grp" style="margin-top:8px" role="group" aria-label="Procedure controls"
            data-i18n-aria-label data-why-out="proc-why">
            <button class="ds-btn primary" data-proc="load" id="proc-btn-load" data-i18n="Load">Load</button>
            <button class="ds-btn" data-proc="start" id="proc-btn-start" data-i18n="Start">Start</button>
            <button class="ds-btn" data-proc="pause" id="proc-btn-pause" data-i18n="Pause">Pause</button>
            <button class="ds-btn" data-proc="resume" id="proc-btn-resume" data-i18n="Resume">Resume</button>
            <button class="ds-btn" data-proc="step" id="proc-btn-step" data-i18n="Step">Step</button>
            <button class="ds-btn" data-proc="skip" id="proc-btn-skip" data-i18n="Skip">Skip</button>
            <!-- critical: shared two-step (armButton), wired at boot -->
            <button class="ds-btn critical" id="proc-btn-abort" data-i18n="Abort">Abort</button>
            <!-- the card's live checklist in the logbook (ops workbook) -->
            <button class="ds-btn" id="proc-btn-checklist" data-act="checklist" data-i18n="Checklist">Checklist</button>
            ${renderLogThis({}, { kind: "decision" })}
          </div>
          <div class="why-off" id="proc-why" aria-live="polite"></div>
          <div id="proc-exec-status" style="margin-top:10px"></div>
          <div class="scroll-y" style="max-height:220px;margin-top:6px" id="proc-exec-log"></div>
        </div></div>
        <div class="ds-card"><h2 data-i18n>Procedure document</h2>
          <div class="bd scroll-y" style="max-height:320px" id="proc-doc"><span data-i18n>select a procedure…</span></div></div>
      </div>
      <div class="g" style="align-content:start">
        <div class="ds-card"><h2 data-i18n>Manual override <span class="r" data-i18n>arbitrary TC during a run</span></h2>
          <div class="bd"><div class="row" style="align-items:flex-end">
            <div class="fld"><label for="proc-ov-svc" data-i18n>Service</label>
              <input id="proc-ov-svc" class="in mono" inputmode="numeric" style="width:64px"></div>
            <div class="fld"><label for="proc-ov-sub" data-i18n>Subtype</label>
              <input id="proc-ov-sub" class="in mono" inputmode="numeric" style="width:64px"></div>
            <div class="fld" style="flex:1"><label for="proc-ov-data" data-i18n>Data (hex)</label>
              <input id="proc-ov-data" class="in mono" placeholder="AA BB …"></div>
            <button class="ds-btn" id="proc-ov-send" data-i18n="Send override">Send override</button>
          </div><div id="proc-ov-result" style="font-size:12px;color:var(--tx3);margin-top:6px"></div></div></div>
        <div class="ds-card"><h2 data-i18n>Procedure builder</h2><div class="bd">
          <div class="row">
            <input id="pb-name" class="in" placeholder="procedure name" data-i18n-placeholder style="flex:1">
            <select id="pb-step-type" class="in" aria-label="Step type" data-i18n-aria-label>
              <option value="command" data-i18n>Command</option><option value="tlm_check" data-i18n>Telemetry check</option>
              <option value="wait" data-i18n>Wait</option><option value="gonogo">GO-NO-GO</option>
              <option value="note" data-i18n>Note</option></select>
            <button class="ds-btn" id="pb-add" data-i18n="Add step">Add step</button>
          </div>
          <div id="pb-step-fields" class="row" style="margin-top:6px"></div>
          <ol id="pb-steps" style="margin:8px 0 0 18px;font-size:13px"></ol>
          <div class="row" style="margin-top:8px">
            <button class="ds-btn" id="pb-save" data-i18n="Save procedure">Save procedure</button>
            <button class="ds-btn" id="pb-run" data-i18n="Run these steps">Run these steps</button>
            <button class="ds-btn" id="pb-clear" data-i18n="Clear">Clear</button>
            <select id="pb-saved" class="in" aria-label="Saved procedures" data-i18n-aria-label><option value="" data-i18n>— load saved —</option></select>
          </div>
          <div id="pb-result" style="font-size:12px;color:var(--tx3);margin-top:6px"></div>
        </div></div>
      </div>
    </div>
  </div>`;
}

const pb = { steps: [] };
let procPoll = null;
async function loadProcSources() {
  const src = $("proc-source") ? $("proc-source").value : "activity";
  const sel = $("proc-type");
  if (!sel) return;
  try {
    let opts = [];
    if (src === "activity") {
      const d = await getJSON("/api/procedure/activity-types");
      opts = (d.activity_types || d.types || []).map((t) => [t.id || t.name || t, t.label || t.name || t]);
    } else if (src === "ops") {
      const d = await getJSON("/api/procedures");
      opts = (d.procedures || []).map((p) => [p.path || p.id || p, p.name || p.path || p]);
    } else {
      const d = await getJSON("/api/procedure/custom");
      opts = (d.procedures || []).map((p) => [p.id || p.name, p.name || p.id]);
      const saved = $("pb-saved");
      if (saved) saved.innerHTML = `<option value="">${t("— load saved —")}</option>` +
        opts.map(([v, l]) => `<option value="${esc(String(v))}">${esc(String(l))}</option>`).join("");
    }
    sel.innerHTML = opts.map(([v, l]) => `<option value="${esc(String(v))}">${esc(String(l))}</option>`).join("");
  } catch (e) { sel.innerHTML = `<option value="">${t("unavailable")}</option>`; }
  loadProcDoc();
  updateProcButtons();
}
async function loadProcDoc() {
  const src = $("proc-source") ? $("proc-source").value : "activity";
  const v = $("proc-type") ? $("proc-type").value : "";
  if (src !== "ops" || !v) { return; }
  try {
    // ?lang= is DISPLAY-only (i18n S0): the server returns the translated
    // document when one exists, else English. Execution never reads this.
    const txt = await (await fetch(
      `/api/procedures/${encodeURIComponent(v)}?lang=${getLang()}`)).text();
    // Same JSON-as-markdown defect as the manual viewer (2026-08-20): the
    // response is the {title, content_md} envelope, not bare markdown.
    let md = txt;
    try { const j = JSON.parse(txt); if (j && typeof j === "object") md = j.content_md || ""; }
    catch (e) { /* plain markdown */ }
    setHTML("proc-doc", renderMarkdown(md));
  } catch (e) { setHTML("proc-doc", t("document unavailable")); }
}
/* Explicit heading anchors (author ruling Q33, 2026-10-30): the EN and FR
 * manuals carry pandoc-style `{#id}` attribute blocks at the end of heading
 * lines, with the same id in both languages. The viewer uses the id as the
 * heading's HTML id and never shows the `{#id}` text; `[text](#id)` links
 * scroll to it (see the [data-man-anchor] click handler). */
const MD_HEADING_ATTR = /[ \t]*\{#([A-Za-z0-9_][\w.:-]*)(?:[ \t][^}]*)?\}[ \t]*$/;
function mdHeading(tag) {
  return (_m, text) => {
    const a = text.match(MD_HEADING_ATTR);
    if (!a) return `<${tag}>${text}</${tag}>`;
    return `<${tag} id="${a[1]}">${text.slice(0, a.index)}</${tag}>`;
  };
}
export function renderMarkdown(md) {
  // Small, safe markdown subset (headings, bold, code, lists, in-document
  // links) — classic parity.
  let h = esc(md);
  h = h.replace(/^### (.*)$/gm, mdHeading("h4"))
       .replace(/^## (.*)$/gm, mdHeading("h3"))
       .replace(/^# (.*)$/gm, mdHeading("h2"))
       .replace(/\[([^\]\n]+)\]\(#([A-Za-z0-9_][\w.:-]*)\)/g,
                '<a href="#$2" data-man-anchor="$2">$1</a>')
       .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
       .replace(/`([^`]+)`/g, "<code>$1</code>")
       .replace(/^---+$/gm, "<hr>")
       .replace(/^[-*] (.*)$/gm, "<li>$1</li>");
  // GFM tables. The shipped manual is table-heavy (the command reference alone
  // is >1000 table lines), so without this the page renders as a wall of pipes.
  h = h.replace(
    /^\|(.+)\|[ \t]*\n\|[ \t]*:?-{2,}[-:| \t]*\|[ \t]*\n((?:\|.*\|[ \t]*\n?)+)/gm,
    (_m, head, body) => {
      const cells = (row) => row.trim().replace(/^\||\|$/g, "").split("|");
      const th = cells(head).map((c) => `<th>${c.trim()}</th>`).join("");
      const tr = body.trim().split("\n").map((r) =>
        `<tr>${cells(r).map((c) => `<td>${c.trim()}</td>`).join("")}</tr>`).join("");
      return `<table class="man-tbl"><thead><tr>${th}</tr></thead>` +
             `<tbody>${tr}</tbody></table>\n`;
    });
  h = h.replace(/(<li>[\s\S]*?<\/li>)(?!\s*<li>)/g, "<ul>$1</ul>")
       .replace(/\n{2,}/g, "<br><br>");
  return `<div style="font-size:13px;line-height:1.55">${h}</div>`;
}
/* Procedure controls follow the runner's state machine (procedure_runner.py:
 * IDLE → LOADED → RUNNING ⇄ PAUSED → COMPLETED / ABORTED / FAILED). Each
 * action is enabled only in the states the server accepts it from; the
 * reason is shown on hover and focus (UI brief §1.3, R3 A5). */
const PROC_ALLOWED = {
  load: ["IDLE", "LOADED", "COMPLETED", "ABORTED", "FAILED"],
  start: ["LOADED"], pause: ["RUNNING"], resume: ["PAUSED"],
  step: ["RUNNING", "PAUSED"], skip: ["RUNNING", "PAUSED"], abort: ["RUNNING", "PAUSED"],
};
export function procButtonState(action, state, hasSelection = true) {
  const st = String(state || "IDLE").toUpperCase();
  const live = st === "RUNNING" || st === "PAUSED";
  if ((PROC_ALLOWED[action] || []).includes(st)) {
    if (action === "load" && !hasSelection) return { ok: false, reason: tText("Select a procedure first") };
    return { ok: true, reason: "" };
  }
  if (action === "load") return { ok: false, reason: tText("A procedure is running — abort it before loading another") };
  if (st === "LOADED") return { ok: false, reason: tText("Loaded but not started — press START") };
  if (action === "start" && live) return { ok: false, reason: st === "PAUSED"
    ? tText("Paused — press RESUME") : tText("Already running") };
  if (action === "pause" && st === "PAUSED") return { ok: false, reason: tText("Already paused") };
  if (action === "resume" && st === "RUNNING") return { ok: false, reason: tText("Not paused") };
  if (st === "IDLE") return { ok: false, reason: tText("No procedure loaded") };
  return { ok: false, reason: tText("No procedure running ({{state}})", { state: st }) };
}
/* Enabled/disabled with a reason. aria-disabled (not `disabled`) keeps the
 * control focusable so keyboard users get the reason too; clicks on it are
 * swallowed by the capture handler in initDelegatedEvents. */
export function setEnabled(el, ok, reason = "") {
  if (!el) return;
  el.disabled = false;
  if (ok) {
    el.removeAttribute("aria-disabled");
    el.removeAttribute("data-reason");
    if (el.dataset) delete el.dataset.why;
    if (el.getAttribute("title") === el.__whyTitle) el.removeAttribute("title");
  } else {
    el.setAttribute("aria-disabled", "true");
    if (el.dataset) el.dataset.why = reason;
    // The shared reason tip (components.js installReasonTips) shows
    // data-reason on hover AND keyboard focus; no native title on top.
    el.setAttribute("data-reason", reason);
    if (el.getAttribute("title") === el.__whyTitle) el.removeAttribute("title");
  }
}
function showWhy(el) {
  const grp = el && el.closest ? el.closest("[data-why-out]") : null;
  const out = grp ? $(grp.dataset.whyOut) : null;
  if (out) out.textContent = el.getAttribute && el.getAttribute("aria-disabled") === "true"
    ? (el.dataset.why || "") : "";
}
function updateProcButtons() {
  const st = (S.procStatus || {}).state || "IDLE";
  const hasSel = !!($("proc-type") && $("proc-type").value);
  for (const a of Object.keys(PROC_ALLOWED)) {
    const r = procButtonState(a, st, hasSel);
    setEnabled($(`proc-btn-${a}`), r.ok, r.reason);
  }
  const why = $("proc-why");
  if (why) why.textContent = st === "IDLE" ? tText("No procedure loaded: choose one and press Load.") : "";
  const hasCard = !!lbProcedureId();
  setEnabled($("proc-btn-checklist"), hasCard,
    hasCard ? "" : tText("Choose an ops procedure (Source: Ops procedure) to get its checklist"));
}
async function refreshProcStatus() {
  try { S.procStatus = await getJSON("/api/procedure/status"); } catch (e) { /* offline */ }
  renderProcStatus();
}

async function procAction(action) {
  const gate = procButtonState(action, (S.procStatus || {}).state,
    !!($("proc-type") && $("proc-type").value));
  if (!gate.ok) { announce(gate.reason); return; }
  // ABORT is critical: it only reaches here from the armed button's second
  // press (shared armButton, wired at boot), so no extra arming step here.
  if (action === "load") {
    const source = $("proc-source").value, id = $("proc-type").value;
    const body = { source, id, step_by_step: $("proc-stepwise").checked };
    if (source === "activity") body.activity_type = id;
    if (source === "ops") body.path = id;
    const r = await postJSON("/api/procedure/load", body);
    if (r.ok && r.json && r.json.runnable === false) {
      // A card the console cannot run: it is worked by hand, step by step,
      // from its live checklist in the logbook.
      setHTML("proc-exec-status", `<div class="logrow nom">${t("{{id}} is worked by hand: confirm each step in its checklist (Logbook › Workbook).",
        { id: r.json.procedure_id })}</div>`);
      if (LB) LB.openChecklist(r.json.procedure_id);
      return;
    }
    setHTML("proc-exec-status", r.ok ? t("loaded") :
      `<span style="color:var(--alarm)">${t("load failed ({{status}})", { status: r.status })}</span>`);
    startProcPolling();
    refreshProcStatus();
    return;
  }
  const r = await postJSON(`/api/procedure/${action}`, {});
  if (!r.ok) setHTML("proc-exec-status", `<span style="color:var(--alarm)">${t("{{action}} failed ({{status}})", { action, status: r.status })}</span>`);
  if (action === "start") {
    startProcPolling();
    // the running card's checklist opens beside the console; the runner
    // ticks its steps as they complete
    const id = lbProcedureId();
    if (r.ok && id && LB) LB.openChecklist(id);
  }
  refreshProcStatus();
}
function startProcPolling() {
  if (procPoll) return;
  procPoll = poller(async () => {
    const st = await getJSON("/api/procedure/status");
    S.procStatus = st;
    renderProcStatus();
    // poll while the runner can still change; one last render after it ends
    if (!st || !["LOADED", "RUNNING", "PAUSED"].includes(String(st.state || ""))) {
      procPoll.stop(); procPoll = null;
    }
  }, 2000);
  procPoll.start();
}
function renderProcStatus() {
  const st = S.procStatus || {};
  // procedure_runner.status(): procedure_name, state, current_step,
  // step_results [{index, description, result}] (the old reads of
  // st.steps / st.name never matched it, so the stepper stayed empty)
  const steps = st.step_results || st.steps || [];
  const idx = st.current_step ?? st.step_index ?? -1;
  setHTML("proc-exec-status",
    `<div style="font-size:13px">${esc(st.procedure_name || st.name || st.procedure || tText("no procedure loaded"))} — ` +
    `<b>${esc(String(st.state || st.status || "idle").toUpperCase())}</b></div>` +
    renderStepper(steps.map((s2) => (s2.description || s2.name || tText("step"))), Number(idx)));
  updateProcButtons();   // (also called after loadProcSources)
  if (LB && st.state && st.state !== "IDLE") LB.onRunner({ ...st, procedure_id: lbProcedureId() });
  // runner log rows: {timestamp (sim epoch s), step, action, detail}
  setHTML("proc-exec-log", (st.log || []).slice(-50).reverse()
    .map((l) => `<div class="logrow">${typeof l === "string" ? esc(l) : l.action
      ? `<span class="mono">${esc(fmtUTC(l.timestamp))}</span> ${l.step >= 0 ? `<span class="mono">#${Number(l.step) + 1}</span> ` : ""}` +
        `${esc(l.action)}${l.detail ? ` — ${esc(l.detail)}` : ""}`
      : esc(l.text || JSON.stringify(l))}</div>`).join(""));
}
function pbFieldMarkup() {
  const kind = $("pb-step-type") ? $("pb-step-type").value : "command";
  const f = {
    // Visible labels on every field (R3 A5); placeholders only show format.
    command: `<div class="fld"><label for="pb-f-svc">${t("Service,subtype")}</label>
        <input class="in mono" id="pb-f-svc" placeholder="8,1" style="width:80px"></div>
      <div class="fld" style="flex:1"><label for="pb-f-data">${t("Data (hex)")}</label>
        <input class="in mono" id="pb-f-data" placeholder="AA BB …"></div>`,
    tlm_check: `<div class="fld" style="flex:1"><label for="pb-f-param">${t("Parameter")}</label>
        <input class="in mono" id="pb-f-param" placeholder="${t("param (name or 0xHHHH)")}"></div>
      <div class="fld"><label for="pb-f-op">${t("Check")}</label>
        <select class="in" id="pb-f-op"><option>==</option><option>&lt;</option><option>&gt;</option></select></div>
      <div class="fld"><label for="pb-f-val">${t("value")}</label>
        <input class="in mono" id="pb-f-val" style="width:90px"></div>`,
    wait: `<div class="fld"><label for="pb-f-wait">${t("seconds")}</label>
        <input class="in" id="pb-f-wait" type="number" min="0" style="width:110px"></div>`,
    gonogo: `<div class="fld" style="flex:1"><label for="pb-f-label">${t("poll label")}</label>
        <input class="in" id="pb-f-label"></div>`,
    note: `<div class="fld" style="flex:1"><label for="pb-f-note">${t("note text")}</label>
        <input class="in" id="pb-f-note"></div>`,
  }[kind];
  return f || "";
}
function pbAddStep() {
  const t = $("pb-step-type").value;
  const step = { type: t };
  if (t === "command") {
    const [svc, sub] = String($("pb-f-svc").value || "").split(",").map((x) => Number(x));
    step.service = svc; step.subtype = sub; step.data = $("pb-f-data").value;
  } else if (t === "tlm_check") {
    step.param = $("pb-f-param").value; step.op = $("pb-f-op").value; step.value = $("pb-f-val").value;
  } else if (t === "wait") step.seconds = Number($("pb-f-wait").value);
  else if (t === "gonogo") step.label = $("pb-f-label").value;
  else step.text = $("pb-f-note").value;
  pb.steps.push(step);
  renderPbSteps();
}
function renderPbSteps() {
  setHTML("pb-steps", pb.steps.map((s2, i) =>
    `<li>${esc(s2.type)} — ${esc(JSON.stringify(s2))}
      <button class="ds-btn" data-pb-del="${i}">✕</button></li>`).join(""));
}
async function pbSave() {
  const r = await postJSON("/api/procedure/save",
    { name: $("pb-name").value || "unnamed", steps: pb.steps });
  setText("pb-result", r.ok ? tText("saved") : tText("save failed ({{status}})", { status: r.status }));
  loadProcSources();
}
async function pbRun() {
  const r = await postJSON("/api/procedure/load",
    { source: "inline", name: $("pb-name").value || "builder steps",
      steps: pb.steps, step_by_step: true });
  setText("pb-result", r.ok ? tText("loaded — use runner controls") : tText("run failed ({{status}})", { status: r.status }));
  startProcPolling();
}

/* ═══ 15. TRND — archive trends (Chart.js, vendor-guarded) ════════════════ */

function buildTrndPage() {
  return `
  <div class="pad hide" id="page-trnd" role="tabpanel" aria-label="Trends" data-i18n-aria-label>
    <h1 class="pt" data-i18n>Trends</h1>
    <p class="sub" data-i18n>Ground archive · eclipse/contact context · alarm &amp; event markers (P8)</p>
    <div id="trnd-provenance"></div>
    <div class="g" style="grid-template-columns:280px minmax(0,1fr);align-items:start">
      <div class="g" style="align-content:start">
        <div class="ds-card"><h2 data-i18n>Query</h2><div class="bd">
          <div class="fld"><label for="trnd-window" data-i18n>Window</label>
            <select id="trnd-window" class="in">
              <option value="900">15 m</option><option value="3600" selected>1 h</option>
              <option value="10800">3 h</option><option value="21600">6 h</option>
              <option value="43200">12 h</option><option value="86400">24 h</option>
              <option value="604800" data-i18n>7 d</option></select></div>
          <div class="fld" style="margin-top:6px"><label for="trnd-filter" data-i18n>Parameter filter</label>
            <input id="trnd-filter" class="in" placeholder="filter…" data-i18n-placeholder></div>
          <div style="font-size:12px;margin-top:6px">
            <label data-i18n><input type="checkbox" id="trnd-bands" checked> limit bands</label><br>
            <label data-i18n><input type="checkbox" id="trnd-shade" checked> eclipse/contact shading</label><br>
            <label data-i18n><input type="checkbox" id="trnd-markers" checked> event + alarm markers</label><br>
            <label data-i18n><input type="checkbox" id="trnd-norm"> normalise 0–100 %</label>
          </div>
          <div class="row" style="margin-top:8px">
            <button class="ds-btn primary" id="trnd-refresh" data-i18n>REFRESH</button>
            <button class="ds-btn" id="trnd-csv" data-i18n>EXPORT CSV</button>
          </div>
          <select id="trnd-params" class="in" multiple size="12" style="width:100%;margin-top:8px"
            aria-label="Parameters to trend" data-i18n-aria-label></select>
        </div></div>
        <div class="ds-card"><h2 data-i18n>Subsystem playback</h2><div class="bd row">
          <select id="trnd-playback-sub" class="in" aria-label="Subsystem" data-i18n-aria-label>
            ${["eps", "tcs", "aocs", "ttc", "payload", "prop", "obdh"].map((s2) => `<option>${s2}</option>`).join("")}</select>
          <button class="ds-btn" id="trnd-playback" data-i18n>LOAD SUBSYSTEM</button>
        </div></div>
      </div>
      <div class="g">
        <div class="ds-card"><h2 data-i18n>Chart</h2><div class="bd">
          <div id="trnd-chart-host"><canvas id="trnd-chart" height="240"></canvas></div></div></div>
        <div class="ds-card"><h2 data-i18n>Alarms in window</h2>
          <div class="bd scroll-y" style="max-height:150px" id="trnd-alarms"></div></div>
        <div class="ds-card"><h2 data-i18n>Events in window</h2>
          <div class="bd scroll-y" style="max-height:150px" id="trnd-events"></div></div>
        <div class="ds-card"><h2 data-i18n>Command history (archived)</h2>
          <div class="bd scroll-y" style="max-height:150px" id="trnd-cmds"></div></div>
        <div class="ds-card"><h2 data-i18n>Baseline vs now — health (NOM-011)
          <span class="r" data-i18n>baseline: display_config.yaml commissioning snapshot</span></h2>
          <div class="bd">
            <div id="trnd-baseline"></div>
          </div></div>
      </div>
    </div>
  </div>`;
}

let trndChart = null;
let trndLastSeries = [];
function archiveBanner(status, detail) {
  // four-state provenance: ok / unavailable / failed / legacy
  const map = {
    ok: ["", ""],
    unavailable: ["stale", tText("ARCHIVE UNAVAILABLE — server has no archive database")],
    failed: ["alarm", tText("ARCHIVE QUERY FAILED — {{detail}}", { detail: detail || "" })],
    legacy: ["warn", tText("LEGACY ARCHIVE — schema predates provenance fields")],
  };
  const [cls, text] = map[status] || map.failed;
  setHTML("trnd-provenance", text ? `<div class="ds-banner ${cls}">${esc(text)}</div>` : "");
}
async function loadTrndParamNames() {
  try {
    const d = await getJSON("/api/archive/param-names");
    const names = d.names || d.parameters || [];
    const f = ($("trnd-filter") ? $("trnd-filter").value : "").toLowerCase();
    const sel = $("trnd-params");
    if (sel) sel.innerHTML = names.filter((n) => !f || String(n).toLowerCase().includes(f))
      .map((n) => `<option>${esc(String(n))}</option>`).join("");
    archiveBanner(d.status || "ok", d.detail);
  } catch (e) { archiveBanner("unavailable"); }
}
function trndSelected() {
  const sel = $("trnd-params");
  if (!sel || !sel.selectedOptions) return [];
  return Array.from(sel.selectedOptions).map((o) => o.value);
}
async function refreshTrend() {
  const names = trndSelected();
  const win = Number($("trnd-window").value);
  const end = simNowSec(), start = end - win;
  const series = [];
  try {
    for (const name of names.slice(0, 6)) {
      const d = await getJSON(`/api/archive/parameters?name=${encodeURIComponent(name)}` +
        `&start=${start}&end=${end}&limit=5000`);
      series.push({ name, rows: d.rows || d.data || [] });
      if (d.status && d.status !== "ok") { archiveBanner(d.status, d.detail); }
    }
    if ($("trnd-shade") && $("trnd-shade").checked) {
      for (const ctxName of ["orbit.eclipse", "orbit.contact"]) {
        try {
          const d = await getJSON(`/api/archive/parameters?name=${encodeURIComponent(ctxName)}` +
            `&start=${start}&end=${end}&limit=5000`);
          series.push({ name: ctxName, rows: d.rows || d.data || [], context: true });
        } catch (e) { /* context series optional */ }
      }
    }
    trndLastSeries = series;
    drawTrendChart(series);
    archiveBanner("ok");
  } catch (e) { archiveBanner("failed", String(e.message || e)); }
  loadArchiveTables(start, end);
}
function drawTrendChart(series) {
  const host = $("trnd-chart-host");
  if (typeof Chart === "undefined") {
    // vendor guard (R3): designed absence + textual latest values
    if (host) host.innerHTML = `<div class="ds-banner stale">${t("Chart.js not installed ({{path}}) — latest archive values:",
      { path: "/static/vendor/js/chart.umd.min.js" })}</div>` +
      `<table class="plain">${series.filter((s2) => !s2.context).map((s2) => {
        const last = s2.rows[s2.rows.length - 1];
        return `<tr><td>${esc(s2.name)}</td><td class="mono">${last ? num(last.value ?? last[1], 3) : "—"}</td></tr>`;
      }).join("")}</table>`;
    return;
  }
  const cv = $("trnd-chart");
  if (!cv) return;
  const norm = $("trnd-norm") && $("trnd-norm").checked;
  const datasets = series.filter((s2) => !s2.context).map((s2, i) => {
    let pts = s2.rows.map((r) => ({ x: (r.ts ?? r.t ?? r[0]) * 1000, y: r.value ?? r.v ?? r[1] }));
    if (norm && pts.length) {
      const ys = pts.map((p) => p.y), mn = Math.min(...ys), mx = Math.max(...ys), sp = (mx - mn) || 1;
      pts = pts.map((p) => ({ x: p.x, y: ((p.y - mn) / sp) * 100 }));
    }
    return { label: s2.name, data: pts, borderColor: `hsl(${i * 60},15%,${60 + i * 5}%)`,
      pointRadius: 0, borderWidth: 1.5 };
  });
  if (trndChart) trndChart.destroy();
  trndChart = new Chart(cv.getContext("2d"), {
    type: "line", data: { datasets },
    options: { animation: false, responsive: true,
      scales: { x: { type: "linear", ticks: { callback: (v) => fmtUTC(v / 1000) } } },
      plugins: { legend: { labels: { boxWidth: 10 } } } },
  });
}
async function loadArchiveTables(start, end) {
  const q = `?start=${start}&end=${end}`;
  try {
    const a = await getJSON(`/api/archive/alarms${q}`);
    setHTML("trnd-alarms", (a.alarms || a.rows || []).slice(-40).reverse().map((r) =>
      renderAlarmRow({ ...r, utc: fmtUTC(r.timestamp) })).join("") || `<div class="logrow nom">${t("none")}</div>`);
  } catch (e) { setHTML("trnd-alarms", `<div class="logrow nom">${t("archive alarms unavailable")}</div>`); }
  try {
    const ev = await getJSON(`/api/archive/events${q}`);
    setHTML("trnd-events", (ev.events || ev.rows || []).slice(-40).reverse().map((r) =>
      renderEventRow({ ...r, utc: fmtUTC(r.timestamp) })).join("") || `<div class="logrow nom">${t("none")}</div>`);
  } catch (e) { setHTML("trnd-events", `<div class="logrow nom">${t("archive events unavailable")}</div>`); }
  try {
    const c = await getJSON(`/api/archive/commands${q}`);
    setHTML("trnd-cmds", (c.commands || c.rows || []).slice(-40).reverse().map((r) =>
      `<div class="logrow">${fmtUTC(r.timestamp)} ${esc(r.name || `S${r.service},${r.subtype}`)} — ${esc(r.verdict || r.status || "")}</div>`).join("") ||
      `<div class="logrow nom">${t("none")}</div>`);
  } catch (e) { setHTML("trnd-cmds", `<div class="logrow nom">${t("archive commands unavailable")}</div>`); }
}
function exportTrendCsv() {
  const lines = ["series,ts,value"];
  for (const s2 of trndLastSeries) {
    if (s2.context) continue;
    for (const r of s2.rows) lines.push(`${s2.name},${r.ts ?? r[0]},${r.value ?? r[1]}`);
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "trend_export.csv";
  a.click();
}
async function loadSubsystemPlayback() {
  const sub = $("trnd-playback-sub").value;
  try {
    const d = await getJSON(`/api/archive/playback?subsystem=${encodeURIComponent(sub)}`);
    const series = (d.parameters || d.series || []).map((p) => ({
      name: p.name, rows: p.rows || p.samples || [] }));
    trndLastSeries = series;
    drawTrendChart(series);
    archiveBanner(d.status || "ok", d.detail);
  } catch (e) { archiveBanner("failed", String(e.message || e)); }
}

/* ═══ 16. MAN — operations manual ═════════════════════════════════════════ */

function buildManPage() {
  return `
  <div class="pad hide" id="page-man" role="tabpanel" aria-label="Manual" data-i18n-aria-label>
    <h1 class="pt" data-i18n>Operations manual</h1>
    <p class="sub" data-i18n>Sections filtered to your position; search covers titles and body text.</p>
    <div class="g" style="grid-template-columns:300px minmax(0,1fr);align-items:start">
      <div class="ds-card"><h2 data-i18n>Contents</h2><div class="bd">
        <input id="man-search" class="in" placeholder="search…" data-i18n-placeholder style="width:100%;margin-bottom:8px">
        <div id="man-toc" class="scroll-y" style="max-height:480px"></div>
        <div class="sub" style="margin-top:6px">sections <span id="man-count">0/0</span></div></div></div>
      <div class="ds-card"><h2 id="man-title">—</h2>
        <div class="bd scroll-y" style="max-height:560px" id="man-body"><span data-i18n>select a section…</span></div></div>
    </div>
    <div class="ds-card" style="margin-top:12px"><h2 data-i18n>Procedure cards — your position</h2>
      <div class="bd">
        <div class="row" style="gap:10px;align-items:center;margin-bottom:8px">
          <label class="sub" data-i18n><input type="checkbox" id="pcard-mine-only" checked>
            only cards my position is required for</label>
          <input id="pcard-search" class="in" placeholder="filter cards…" data-i18n-placeholder style="max-width:260px">
          <span class="sub" id="pcard-count"></span>
        </div>
        <div id="pcard-list" class="scroll-y" style="max-height:520px"></div>
      </div></div>
    <div class="ds-card" style="margin-top:12px"><h2><span data-i18n>Course PDFs</span>
      <span class="r" data-i18n>textbooks · workbooks · references</span></h2>
      <div class="bd scroll-y" style="max-height:520px" id="man-downloads"></div></div>
  </div>`;
}

/* ── Procedure cards, per position ────────────────────────────────────────
 *
 * Field report 2026-08-20: "could the MAN page display the procedure cards per
 * position with the specific steps to be executed by that position highlighted
 * somehow (so this changes by position)?"
 *
 * Two grades of attribution, shown differently because they are not equally
 * certain:
 *
 *   * the ROLE line and which cards are relevant come from
 *     procedure_index.yaml's `required_positions` / `position_roles` -- a
 *     human wrote those, they are exact;
 *   * the per-step highlight is DERIVED, by joining each command step's
 *     func_id against the position's commanding authority in positions.yaml.
 *
 * Only the func_id grain is used. Service-level authority looked tempting and
 * is useless: every position may send S17 pings and S3 HK requests, so a
 * service match attributed CONNECTION_TEST to six positions at once and
 * highlighted nearly every step of every card. A highlight that is always on
 * is not a highlight.
 *
 * Steps with no owner at this grain -- GO/NO-GO calls, telemetry checks, and
 * commands anyone may send -- are shown plainly and never highlighted. The
 * card says so, so an operator does not read "not highlighted" as "not mine".
 */
async function loadProcedureCards() {
  try {
    S.procCards = await getJSON(
      `/api/procedure/cards?position=${encodeURIComponent(S.position)}`);
  } catch (e) { S.procCards = null; }
  renderProcedureCards();
}
function renderProcedureCards() {
  const host = $("pcard-list");
  if (!host) return;
  const data = S.procCards || {};
  const all = data.cards || [];
  const mineOnly = $("pcard-mine-only") ? $("pcard-mine-only").checked : true;
  const f = ($("pcard-search") ? $("pcard-search").value : "").toLowerCase();
  const cards = all.filter((c) => (!mineOnly || c.relevant) &&
    (!f || `${c.id} ${c.name} ${c.category}`.toLowerCase().includes(f)));
  setText("pcard-count", tText("{{n}}/{{m}} cards", { n: cards.length, m: all.length }));
  if (!cards.length) {
    host.innerHTML = `<div class="logrow nom">${t("no procedure cards for this position")}</div>`;
    return;
  }
  host.innerHTML = cards.map((c) => {
    const open = S.procCardOpen === c.id;
    // YAML overlay proc:<id>:name / proc:<id>:position_roles.<position>
    const roleLine = c.my_role
      ? `<div class="sub" style="margin:2px 0 6px">${t("Your role: {{role}}",
          { role: tdb(`proc:${c.id}:position_roles.${S.position}`, c.my_role) })}</div>`
      : (c.relevant
          ? `<div class="sub" style="margin:2px 0 6px">${t("Your position is required; no per-position role recorded for this card.")}</div>`
          : "");
    const mineChip = c.my_step_count
      ? `<span class="ds-badge">${t("{{count}} step yours", { count: c.my_step_count, plural: "{{count}} steps yours" })}</span>`
      : "";
    const body = open ? `
      ${roleLine}
      <div class="sub" style="margin-bottom:6px">${t("Required: {{list}}",
        { list: (c.required_positions || []).join(", ") || "—" })}</div>
      <table class="plain man-tbl"><tr><th>#</th><th>${t("Step")}</th><th>${t("Owner")}</th></tr>
      ${(c.steps || []).map((st) => {
        const own = (st.owners || []).join(", ");
        return `<tr class="${st.mine ? "pcard-mine" : ""}">
          <td class="mono">${st.index + 1}</td>
          <td>${st.mine ? "<b>" : ""}${esc(st.description || st.mnemonic || st.type)}${st.mine ? "</b>" : ""}</td>
          <td class="sub">${esc(own || "—")}</td></tr>`;
      }).join("")}</table>
      <div class="sub" style="margin-top:6px">${t("Highlighted steps are attributed by commanding authority (func id). Unhighlighted steps are calls, checks, or commands any position may send — not necessarily someone else's.")}</div>` : "";
    return `<div class="ds-card" style="border-radius:6px;margin-bottom:6px"><div class="bd" style="padding:8px 10px">
      <a href="#" data-pcard="${esc(c.id)}" style="font-weight:600">${esc(c.id)} — ${esc(c.name ? tdb(`proc:${c.id}:name`, c.name) : c.name)}</a>
      ${mineChip}
      <span class="sub"> ${t("{{cat}} · {{count}} steps", { cat: c.category || "", count: (c.steps || []).length })}</span>
      ${body}</div></div>`;
  }).join("");
}
async function loadManual() {
  // Course PDFs (GET /api/downloads, student list): shared renderer, mounted once.
  const dl = $("man-downloads");
  if (dl && !dl.dataset.mounted) {
    dl.dataset.mounted = "1";
    import("/static/shared/downloads.js").then((m) => m.mountDownloads(dl)).catch(() => {});
  }
  try { S.manual = await getJSON("/api/manual"); }
  catch (e) { S.manual = null; }
  renderManual();
}
function manualSectionsForPosition() {
  // FIELD FIX 2026-08-20: the server serves {"pages":[{name,path,...}]} --
  // this read `.sections` and `.title`, neither of which exists, so the TOC
  // was ALWAYS empty ("no sections") and the manual looked absent. Accept the
  // served shape; keep `.sections` tolerated so an old fixture cannot silently
  // resurrect the bug (a test asserts a .sections payload yields NO entries).
  const secs = ((S.manual || {}).pages) || [];
  const pos = S.positions[S.position];
  if (S.position === "flight_director" || !pos ||
      !pos.manual_sections || !pos.manual_sections.length ||
      pos.manual_sections === "all" || pos.manual_sections[0] === "all")
    return secs;
  // Classic's rule: the position's stems, PLUS the two everyone needs.
  const always = ["00_mission_overview", "09_command_reference"];
  return secs.filter((s2) => {
    const stem = String(s2.path || s2.filename || "").replace(/\.md$/, "");
    return always.some((a) => stem.includes(a)) ||
           pos.manual_sections.some((m) => stem.includes(m));
  });
}
function manualTitle(s2) { return s2.name || s2.title || s2.path || tText("(untitled)"); }
function renderManual() {
  const host = $("man-toc");
  if (!host) return;
  const f = ($("man-search") ? $("man-search").value : "").toLowerCase();
  const all = manualSectionsForPosition();
  const secs = all.filter((s2) => {
    if (!f) return true;
    if (manualTitle(s2).toLowerCase().includes(f)) return true;
    const body = S.manualBodies[String(s2.path || "")];   // body-text search
    return body ? body.toLowerCase().includes(f) : false;
  });
  const cur = S.manualOpen || "";
  host.innerHTML = secs.map((s2) => {
    const path = String(s2.path || s2.filename || "");
    const on = path === cur ? ' style="font-weight:700"' : "";
    return `<div class="man-toc-item"><a href="#" data-man="${esc(path)}"${on}>` +
           `${esc(manualTitle(s2))}</a></div>`;
  }).join("") || `<div class="logrow nom">${t("no sections")}</div>`;
  setText("man-count", `${secs.length}/${all.length}`);
}
/** In-document `#id` link: scroll to the heading carrying that id inside the
 * same rendered document (manual or procedure view), never the page hash. */
function scrollToManualAnchor(link, id) {
  const host = (link.closest && link.closest("#man-body, #proc-doc")) || document;
  const target = host.querySelector(`[id="${id}"]`);
  if (target && target.scrollIntoView) target.scrollIntoView({ block: "start" });
  return target || null;
}
async function openManualSection(path) {
  // FIELD FIX 2026-08-20: this took .text() of a JSON response and rendered the
  // envelope as markdown, and encodeURIComponent() destroyed the slashes in a
  // nested path. Decode properly, encode per segment.
  try {
    const url = "/api/manual/" +
      String(path).split("/").map(encodeURIComponent).join("/") +
      "?lang=" + getLang();             // display-only translation (i18n S0)
    const data = await (await fetch(url)).json();
    const md = data.content_md || "";
    S.manualOpen = path;
    S.manualBodies[path] = md;          // cache for body-text search
    setText("man-title", data.title || path);
    setHTML("man-body", renderMarkdown(md));
    renderManual();                      // refresh active-item highlight
  } catch (e) { setHTML("man-body", t("section unavailable")); }
}

/* ═══ 17. DRAWER — bottom log drawer ══════════════════════════════════════ */

let bdTab = "events";
let bdOpen = false;
const logLock = { events: false, tm: false };   // scroll lock per pane

function packetRowText(pkt, ts) {
  const sid = pkt.hk_decoded ? pkt.hk_decoded.sid : "";
  const rid = pkt.event ? pkt.event.event_id : "";
  return `${ts}  TM(${pkt.service},${pkt.subtype})  ` +
         `${sid !== "" ? "SID " + sid : rid !== "" ? "RID " + hex4(rid) : ""}  ` +
         `${pkt.length !== undefined ? pkt.length + " B" : ""}`;
}
function eventText(evt) {
  return `${hex4(evt.event_id)} ${evt.name || ""} — ${evt.description || ""}`.trim();
}
function pushEvent(e) {
  S.events.unshift(e);
  if (S.events.length > RING) S.events.length = RING;
}
function routeEvent(msg, eventId) {
  const id = Number(eventId);
  if (!Number.isFinite(id)) return;
  for (const [sub, [lo, hi]] of Object.entries(EVENT_SUBSYSTEM_RANGES)) {
    if (id >= lo && id <= hi) {
      const buf = S.subsysEvents[sub];
      buf.push(msg);
      if (buf.length > 100) buf.shift();
      return;
    }
  }
}
function eventPassesFilter(e) {
  const f = $("evt-sev-filter") ? $("evt-sev-filter").value : "all";
  if (f === "all") return true;
  if (f === "warnplus") return e.sev === "warn" || e.sev === "alarm";
  return e.sev === f;
}
export function renderBottomDrawer() {
  if (!bdOpen) return;
  if (bdTab === "events") {
    const rows = S.events.filter(eventPassesFilter).slice(0, 120);
    setHTML("bdp-events",
      (logLock.events ? `<span class="jump-chip" id="events-jump">${t("{{n}} rows · jump to latest", { n: S.events.length })}</span>` : "") +
      rows.map((e) => `<div class="logrow ${e.sev}">${esc(e.ts)} [${esc(e.label === "REJECT" ? tText("REJECT") : e.label)}] ${esc(e.msg)}` +
        `${e.instructor && S.timeMode !== "real" ? ` <span class="ds-badge">${t("INSTRUCTOR")}</span>` : ""}</div>`).join(""));
  } else if (bdTab === "tm") {
    setHTML("bdp-tm", S.tmLog.slice(0, 120).map((r) => `<div class="logrow">${esc(r)}</div>`).join(""));
  } else if (bdTab === "cmdhist") {
    setHTML("bdp-cmdhist", S.cmdHistory.slice(0, 120).map(cmdHistoryRow).join("") ||
      `<div class="logrow nom">${t("no commands this session")}</div>`);
  } else if (bdTab === "conlog") {
    renderConsoleLog();
  } else if (bdTab === "handover") {
    setHTML("handover-list", S.handover.map((h) =>
      `<div class="logrow">${esc(h.ts || "")} [${esc(h.position || "")}] ${esc(h.text || h.note || "")}</div>`).join("") ||
      `<div class="logrow nom">${t("no handover notes")}</div>`);
  } else if (bdTab === "gonogo") {
    renderGoNoGo();
  }
}
function selectBdTab(id, open = true) {
  // `open=false` selects the tab without expanding — used at init so the
  // drawer boots COLLAPSED to its 24 px strip (chrome budget, plan §2.1;
  // Agent 5 screenshot fix: it used to boot expanded and cost the work
  // area ~170 px at 1366×768).
  bdTab = id;
  if (open) {
    bdOpen = true;
    $("bottom-drawer").classList.add("open");
    $("bd-toggle").setAttribute("aria-expanded", "true");
  }
  for (const t of ["events", "tm", "cmdhist", "conlog", "handover", "gonogo"]) {
    show(`bdp-${t}`, t === id);
    const b = document.querySelector ? document.querySelector(`[data-bd="${t}"]`) : null;
    if (b) b.setAttribute("aria-selected", t === id ? "true" : "false");
  }
  renderBottomDrawer();
}
async function loadHandover() {
  try { S.handover = (await getJSON("/api/handover")).notes || []; }
  catch (e) { /* keep */ }
  renderBottomDrawer();
}
async function addHandoverNote() {
  const el = $("handover-input");
  const text = el ? el.value.trim() : "";
  if (!text) return;
  await postJSON("/api/handover", { text, position: S.position });
  if (el) el.value = "";
  loadHandover();
}
function handleGoNoGo(msg) {
  S.goNoGo = msg;
  if (msg.type === "go_nogo_poll") {
    selectBdTab("gonogo");
    announce(tText("GO/NO-GO poll: {{label}} — respond from the drawer", { label: msg.label || "" }));
  }
  renderGoNoGo();
}
export function renderGoNoGo() {
  const g = S.goNoGo;
  if (!g) { setHTML("gonogo-status", `<div class="logrow nom">${t("no active poll")}</div>`); return; }
  const resp = g.responses || {};
  // G7: an open poll carries its call-matrix row — who calls, who must
  // respond, and the FD criticality note — beside the response buttons.
  const matrixHtml = g.active ? renderGonogoMatrixRow(g.label) : "";
  setHTML("gonogo-status",
    `<div style="font-size:13px;margin:4px 0"><b>${esc(g.label || "GO/NO-GO")}</b>` +
    ` — ${g.active ? t("OPEN") : (g.result ? t("RESULT: {{r}}", { r: g.result }) : t("closed"))}</div>` +
    Object.entries(resp).map(([pos, r]) => renderChip({
      kind: r === "GO" ? "ok" : r === "NOGO" ? "alarm" : "warn",
      label: `${POSITION_INFO[pos] ? tText(POSITION_INFO[pos].title) : pos}: ${r}` })).join(" ") +
    matrixHtml);
}
async function goNoGoRespond(response) {
  await postJSON("/api/go-nogo/respond", { position: S.position, response });
}
async function goNoGoStart() {
  await postJSON("/api/go-nogo/poll", { label: ($("gonogo-label") || {}).value || "GO/NO-GO" });
}

/* ═══ 18. ALARMS — docked drawer + causal chain ═══════════════════════════ */

const ALARM_FILTER_KEY = "mcs.alarmFilters";
function restoreAlarmFilters() {
  try {
    const f = JSON.parse(localStorage.getItem(ALARM_FILTER_KEY) || "{}");
    if ($("alarm-f-sub") && f.sub !== undefined) $("alarm-f-sub").value = f.sub;
    if ($("alarm-f-sev") && f.sev !== undefined) $("alarm-f-sev").value = f.sev;
  } catch (e) { /* corrupted storage */ }
}
function persistAlarmFilters() {
  try {
    localStorage.setItem(ALARM_FILTER_KEY, JSON.stringify({
      sub: $("alarm-f-sub") ? $("alarm-f-sub").value : "",
      sev: $("alarm-f-sev") ? $("alarm-f-sev").value : "0" }));
  } catch (e) { /* private mode */ }
}
export function filteredAlarms() {
  const sub = $("alarm-f-sub") ? $("alarm-f-sub").value : "";
  const sevMin = Number($("alarm-f-sev") ? $("alarm-f-sev").value : 0);
  return S.alarms.filter((a) =>
    (!sub || a.subsystem === sub) && (!sevMin || Number(a.severity) >= sevMin));
}
/* ── One alarm store (P7.5, R3 A3) ────────────────────────────────────────
 * S.alarms is the journal; EVERY count on the page (header button, IS-IT-
 * WELL card, rail badges, FDIR page, drawer) is derived here from it, so
 * they cannot disagree (the audit saw header 34, FDIR 0, rail 34).
 * Repeats of the same (parameter, direction) or (subsystem, message)
 * collapse into one row with ×N and the last-occurrence time. */
export function alarmParamHex(a) {
  if (a.param_id !== undefined && a.param_id !== null) return hex4(a.param_id);
  return a.parameter ? String(a.parameter) : null;
}
function alarmDir(a) {
  const s = String(a.limit_status || a.status || "").toLowerCase();
  return s.endsWith("high") ? "high" : s.endsWith("low") ? "low" : "";
}
export function alarmPriority(a) {
  if ([1, 2, 3, 4].includes(Number(a.priority))) return Number(a.priority);
  const s = String(a.limit_status || "").toLowerCase();
  if (s.startsWith("red")) return 2;
  if (s.startsWith("yellow")) return 3;
  const sev = Number(a.severity);
  return sev >= 3 ? 2 : sev === 2 ? 3 : 4;
}
export function alarmKey(a) {
  const h = alarmParamHex(a);
  return h ? `p:${h}:${alarmDir(a)}` : `m:${a.subsystem || ""}:${a.message || a.event_id || a.id}`;
}
export function alarmGroups(list = S.alarms) {
  const by = new Map();
  for (const a of list) {
    const k = alarmKey(a);
    let g = by.get(k);
    if (!g) { g = { key: k, items: [] }; by.set(k, g); }
    g.items.push(a);
  }
  const out = [];
  for (const g of by.values()) {
    const items = g.items.slice().sort((x, y) => Number(y.timestamp || 0) - Number(x.timestamp || 0));
    const latest = items[0];
    out.push({
      ...latest,
      id: latest.id,
      // any occurrence's procedure link (repeats may not all carry one)
      procedure: latest.procedure || (items.find((x) => x.procedure) || {}).procedure,
      ids: items.map((x) => x.id),
      count: items.length,
      first_ts: Number(items[items.length - 1].timestamp || 0),
      last_ts: Number(latest.timestamp || 0),
      acknowledged: items.every((x) => x.acknowledged),
      rtn: items.every((x) => x.rtn),
      pri: Math.min(...items.map(alarmPriority)),
    });
  }
  return out.sort((x, y) => (x.acknowledged - y.acknowledged) || (x.pri - y.pri) || (y.last_ts - x.last_ts));
}
/** Every alarm count on the page comes from here. */
export function alarmSummary(list = S.alarms) {
  const groups = alarmGroups(list);
  const active = groups.filter((g) => !g.rtn);
  const bySub = {};
  for (const g of active) {
    const sub = String(g.subsystem || "").toLowerCase();
    const c = bySub[sub] || (bySub[sub] = { a: 0, w: 0 });
    if (g.pri <= 2) c.a++; else c.w++;
  }
  return {
    groups, active: active.length,
    unacked: groups.filter((g) => !g.acknowledged).length,
    alarm: active.filter((g) => g.pri <= 2).length,
    warn: active.filter((g) => g.pri > 2).length,
    raw: list.length, bySub,
  };
}
/* Parse the limit the server describes ("RED_HIGH > 6.0") into a threshold
 * and soft/hard kind; fall back to the band. */
function alarmLimit(a) {
  const st = String(a.limit_status || "").toLowerCase();
  const kind = st.startsWith("red") ? "hard" : st.startsWith("yellow") ? "soft" : "";
  const m = /([-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)\s*$/i.exec(String(a.limit || ""));
  let thr = m ? Number(m[1]) : null;
  if (thr === null && a.band && st) thr = a.band[st] ?? null;
  return { kind, thr, dir: alarmDir(a) };
}
/* Where an alarm came from, so an operator can find what to tune or
 * disable: a ground limit (mcs/limits.yaml), an on-board S12 monitor
 * (disable it by mon_id on the FDIR page) or an S5 event. */
export function alarmSourceHtml(a) {
  const src = String(a.source || "").toUpperCase();
  if (src === "LIMIT") {
    return `<span class="src" title="${esc(tText("Ground limit check in the MCS. Change the band in {{file}}.", { file: a.config_file || "mcs/limits.yaml" }))}">` +
      `${t("ground limit")} ${esc(alarmParamHex(a) || a.parameter || "")} · <span class="mono">${esc(a.config_file || "mcs/limits.yaml")}</span></span>`;
  }
  if (src === "S12") {
    const mid = a.mon_id;
    const label = mid !== undefined && mid !== null
      ? tText("on-board monitor #{{id}}", { id: String(mid) }) : t("on-board monitor");
    const nm = a.monitor_name ? ` ${esc(a.monitor_name)}` : "";
    return `<span class="src">` +
      (mid !== undefined && mid !== null
        ? `<a href="#" data-mon-trace="${esc(String(a.monitor_name || mid))}" title="${esc(tText("Open the S12 monitor table on the FDIR page; disable it there with DIS (12,4)."))}">${esc(label)}</a>`
        : esc(label)) +
      `${nm}${a.limit ? ` · <span class="mono">${esc(String(a.limit))}</span>` : ""}</span>`;
  }
  if (src === "S5") {
    return `<span class="src">${t("on-board event")} <span class="mono">${esc(String(a.event_id ?? a.parameter ?? ""))}</span></span>`;
  }
  return "";
}
/* Row: [P#] PARAM-NAME value unit ▲ limit (soft|hard) ×N
 *      first line is the fact; second line time · age · procedure + actions
 *      (actions sit on their own line, so they never overlap wrapped text). */
export function alarmRowHtml(g) {
  const a = g;
  const pri = a.pri || alarmPriority(a);
  const cls = ["ds-alarm-row", `p${pri}`, "mcs-al", a.acknowledged ? "acked" : "unacked", a.rtn ? "rtn" : ""]
    .filter(Boolean).join(" ");
  const hexId = alarmParamHex(a);
  const def = hexId ? S.paramByHex[hexId] : null;
  const pname = a.name || (def && def.name) || "";
  const units = a.units || (def && def.units) || "";
  const lim = alarmLimit(a);
  const filled = lim.kind === "hard";
  const arrow = lim.dir === "high" ? (filled ? "▲" : "△") : lim.dir === "low" ? (filled ? "▼" : "▽") : "";
  let fact;
  if (pname) {
    const v = Number(a.value);
    const sl = sentinelLabel(hexId, a.value);
    const vTxt = sl ? esc(sl) : Number.isFinite(v) ? num(v, Math.abs(v) >= 100 ? 0 : 2) : esc(String(a.value ?? ""));
    fact = `<span class="pn mono">${esc(pname)}</span>` +
      ` <span class="pv mono">${vTxt}${units && !sl ? " " + esc(units) : ""}</span>` +
      (arrow ? ` <span class="lim mono" title="${esc(String(a.limit || ""))}">${arrow} ${lim.thr !== null ? num(lim.thr, Math.abs(lim.thr) >= 100 ? 0 : 2) : ""}` +
        `${lim.kind ? ` <small>${lim.kind === "hard" ? t("hard") : t("soft")}</small>` : ""}</span>` : "");
  } else {
    fact = `<span class="pn">${esc(String(a.subsystem || "").toUpperCase())}</span> ` +
      `<span class="pv">${esc(String(a.message || a.description || a.id))}</span>`;
  }
  const age = Math.max(0, simNowSec() - a.last_ts);
  const ids = (a.ids || [a.id]).join(",");
  const proc = a.procedure
    ? `<a href="#" class="proc" data-act="procedure" data-proc="${esc(a.procedure.file || a.procedure.path || a.procedure.id || "")}"
        title="${esc(a.procedure.name || "")}">${esc(a.procedure.id || a.procedure.name || tText("procedure"))}</a>` : "";
  const label = pname || String(a.message || a.id);
  return `<div class="${cls}" data-id="${esc(String(a.id))}">
    <span class="pri mono" aria-label="${esc(tText("priority {{p}}", { p: pri }))}">P${pri}</span>
    <span class="fact">${fact}${pname && a.message ? ` <small class="why">${esc(String(a.message))}</small>` : ""}${a.count > 1 ? ` <span class="rep mono" title="${esc(tText("{{n}} occurrences since {{t}}", { n: String(g.ids ? g.ids.length : 1), t: fmtUTC(a.first_ts) }))}">×${a.count}</span>` : ""}</span>
    <span class="meta"><span class="mono">${esc(fmtUTC(a.last_ts, { date: false }))}</span> · ${esc(tText("{{age}} ago", { age: fmtAge(age) }))}${proc ? " · " + proc : ""}${a.rtn ? " · " + t("returned to normal") : ""}${alarmSourceHtml(a) ? " · " + alarmSourceHtml(a) : ""}</span>
    <span class="act">${a.acknowledged ? `<span class="ackd">${t("acknowledged")}</span>`
      : `<button class="ds-btn" data-act="ack" data-id="${esc(String(a.id))}" data-ids="${esc(ids)}"
          aria-label="${esc(tText("Acknowledge {{name}}", { name: label }))}">${t("ACK")}</button>`}
      <button class="ds-btn" data-chain="${esc(String(a.id))}" title="${t("causal chain (P9)")}"
        aria-label="${esc(tText("Causal chain for {{name}}", { name: label }))}">⛓</button>
      <button class="ds-btn" data-act="ticket" data-id="${esc(String(a.id))}"
        title="${esc(tText("File an anomaly ticket from this alarm (logbook)"))}"
        aria-label="${esc(tText("Anomaly ticket for {{name}}", { name: label }))}">${t("Ticket")}</button>
      ${renderLogThis({ alarm_id: a.id, ...(hexId ? { param: hexId } : {}) }, { kind: "decision", iconOnly: true })}</span>
  </div>`;
}
export function renderAlarmDrawer() {
  // G6: when ≥4 active alarms share fault-graph ancestry, collapse the
  // cascade to its first-out root; the consequents expand on demand.
  const { groups, rest } = groupAlarmsByAncestry(alarmGroups(filteredAlarms()), S.faultGraph);
  const semantics = (S.faultGraph && S.faultGraph.edge_semantics) ||
    tText("edges are inferred fault-to-fault ancestry from fdir/fault_propagation.yaml");
  const groupHtml = groups.map((g) => {
    const gid = String(g.root.id);
    const open = !!S.alarmGroupsOpen[gid];
    return `<div class="alarm-group">
      <div class="alarm-group-hd">
        <b>${t("FIRST-OUT ROOT")}</b> ${esc(g.rootNode.id)}
        <span> ${t("+ {{n}} consequent", { n: g.consequents.length })}</span>
        <button class="ds-btn" data-group="${esc(gid)}" aria-expanded="${open}">
          ${open ? t("collapse") : t("expand")}</button>
        <div class="alarm-group-note" title="${esc(semantics)}">${t("grouping is INFERRED from the ground fault-propagation model, not telemetered — verify with the S5 event order")}</div>
      </div>
      ${alarmRowHtml(g.root)}
      ${open ? `<div class="alarm-group-kids">${g.consequents.map(alarmRowHtml).join("")}</div>` : ""}
    </div>`;
  }).join("");
  const rows = rest.map(alarmRowHtml).join("");
  setHTML("alarm-list", groupHtml + rows ||
    `<div class="logrow nom" style="padding:14px">${t("no alarms match the filters")}</div>`);
  updateRailHealth();
}
// The alarm journal stands in the right dock (shared dock.js) beside the
// logbook and the voice loops instead of on top of them.
let alarmDock = null;
export function toggleAlarmDrawer(open, opts = {}) {
  const d = $("alarm-drawer");
  if (!d) return;
  if (!alarmDock) {
    alarmDock = dockPanel(d, { width: 540, min: 360, order: 1,
      close: ({ evicted }) => toggleAlarmDrawer(false, { evicted }) });
  }
  const on = open === undefined ? !d.classList.contains("open") : open;
  d.classList.toggle("open", on);
  const btn = $("alarms-btn");
  if (btn) btn.setAttribute("aria-expanded", String(on));
  if (on) alarmDock.opened(); else if (!opts.evicted) alarmDock.closed();
  if (on) {
    renderAlarmDrawer();
    // focus trap entry: focus the first control
    const first = d.querySelector ? d.querySelector("select,button") : null;
    if (first) first.focus();
  }
}
export async function ackAlarm(id, ids) {
  // A de-duplicated row acknowledges every occurrence it stands for.
  const all = (ids && ids.length ? ids : [id]).map(String);
  const todo = S.alarms.filter((x) => all.includes(String(x.id)) && !x.acknowledged);
  for (const a of todo) a.acknowledged = true;
  if (!todo.length && !S.alarms.some((x) => String(x.id) === String(id))) todo.push({ id });
  renderAlarmDrawer();
  updateSaHeader();
  for (const a of todo) {
    await postJSON(`/api/alarms/${encodeURIComponent(a.id)}/ack`, { position: S.position });
  }
}
export async function ackAllAlarms() {
  for (const a of filteredAlarms()) {
    if (!a.acknowledged) await ackAlarm(a.id);
  }
}
function ackFirstUnacked() {
  const g = alarmGroups(filteredAlarms()).find((x) => !x.acknowledged);
  if (g) { ackAlarm(g.id, g.ids); announce(tText("acknowledged {{sub}} {{msg}}", { sub: g.subsystem || "", msg: String(g.name || g.message || g.id) })); }
}
async function loadAlarms() {
  try { S.alarms = (await getJSON("/api/alarms")).alarms || []; }
  catch (e) { /* keep client copy */ }
  renderAlarmDrawer();
  updateSaHeader();
}
function openProcedureFromAlarm(procPath) {
  showPage("proc");
  const sel = $("proc-source");
  if (sel) { sel.value = "ops"; loadProcSources().then(() => {
    const t = $("proc-type");
    if (t) { t.value = procPath; loadProcDoc(); }
  }); }
}

/* Causal chain (P9, Mockup C spine): alarm → parameter → limit → recent
 * commands → S5 events, assembled client-side. */
export async function openCausalChain(alarmId) {
  const a = S.alarms.find((x) => String(x.id) === String(alarmId));
  if (!a) return;
  S.chainOpen = String(alarmId);      // re-rendered on a language switch
  toggleChain(true);
  const hexId = alarmParamHex(a);
  const def = hexId ? S.paramByHex[hexId] : null;
  let limitsHtml = `<i>${t("no ground limit involved")}</i>`;
  try {
    const lim = await getJSON("/api/limits");
    const band = hexId ? lim.limits[hexId] : null;
    if (band) limitsHtml = renderDeviationBar(Number(a.value), band) +
      `<div class="mono" style="font-size:12px;margin-top:14px">${t("yellow {{yl}}…{{yh}} · red {{rl}}…{{rh}} {{u}}",
        { yl: num(band.yellow_low, 2), yh: num(band.yellow_high, 2), rl: num(band.red_low, 2),
          rh: num(band.red_high, 2), u: band.units || "" })}</div>`;
  } catch (e) { limitsHtml = `<i>${t("limits unavailable")}</i>`; }
  const end = simNowSec(), start = end - 1800;
  let cmdsHtml = "", evtsHtml = "";
  try {
    const c = await getJSON(`/api/archive/commands?start=${start}&end=${end}`);
    cmdsHtml = (c.commands || c.rows || []).slice(-8).reverse().map((r) =>
      `<div class="logrow">${fmtUTC(r.timestamp)} ${esc(r.name || `S${r.service},${r.subtype}`)} — ${esc(r.verdict || r.status || "")}</div>`).join("") ||
      `<div class="logrow nom">${t("no commands in the last 30 min")}</div>`;
  } catch (e) { cmdsHtml = `<div class="logrow nom">${t("command archive unavailable")}</div>`; }
  try {
    const ev = await getJSON(`/api/archive/events?start=${start}&end=${end}`);
    evtsHtml = (ev.events || ev.rows || []).slice(-8).reverse().map((r) =>
      renderEventRow({ ...r, utc: fmtUTC(r.timestamp) })).join("") ||
      `<div class="logrow nom">${t("no S5 events in the last 30 min")}</div>`;
  } catch (e) { evtsHtml = `<div class="logrow nom">${t("event archive unavailable")}</div>`; }
  setHTML("chain-body", `
    ${renderStepper([tText("COMMANDS (30 min)"), tText("S5 EVENTS"), tText("PARAMETER"), tText("GROUND LIMIT"), tText("ALARM")], 4)}
    <div class="g" style="grid-template-columns:1fr 1fr;margin-top:12px">
      <div class="ds-card"><h2>${t("1 · Recent commands")}</h2><div class="bd">${cmdsHtml}</div></div>
      <div class="ds-card"><h2>${t("2 · S5 events")}</h2><div class="bd">${evtsHtml}</div></div>
      <div class="ds-card"><h2>${t("3 · Parameter")}</h2><div class="bd">
        ${def ? paramTriad(hexId) : `<i>${t("no parameter attached to this alarm")}</i>`}</div></div>
      <div class="ds-card"><h2>${t("4 · Ground limit")}</h2><div class="bd">${limitsHtml}</div></div>
    </div>
    <div class="ds-card" style="margin-top:10px"><h2>${t("5 · The alarm")}</h2><div class="bd">
      ${alarmRowHtml(alarmGroups([a])[0])}
      <p style="font-size:12.5px;color:var(--tx2);margin-top:8px">${t("Read the chain backwards: did a command (1) or an on-board event (2) move the parameter (3) across the ground limit (4) to raise this alarm (5)? This is the mental model the console teaches (P9).")}</p>
    </div></div>`);
}
function toggleChain(open) {
  const o = $("chain-overlay");
  if (open === false) S.chainOpen = "";
  if (o) o.classList.toggle("open", open === undefined ? !o.classList.contains("open") : open);
}
function toggleHelp(open) {
  const o = $("help-overlay");
  if (o) o.classList.toggle("open", open === undefined ? !o.classList.contains("open") : open);
}

/* Focus trap for the alarm drawer (B3): Tab cycles inside while open. */
function initFocusTrap() {
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const d = $("alarm-drawer");
    if (!d || !d.classList.contains("open") || !d.querySelectorAll) return;
    if (!d.contains(document.activeElement)) return;
    const els = Array.from(d.querySelectorAll("button,select,a,[tabindex]"))
      .filter((x) => !x.hidden && !x.disabled);
    if (!els.length) return;
    const first = els[0], last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
}

/* ═══ 19. DISPLAY CONFIG — operational display config ═════════════════════ */

/* Two operational tables live here (NOT training content — the guided
 * teaching layer was retired by the 2026-08-19 ruling): the NOM-002
 * capture-readiness gates (G4) and the commissioning health baselines
 * (G15). Source: configs/<mission>/mcs/display_config.yaml via
 * /api/display-config. */
async function loadDisplayConfig() {
  try { S.displayConfig = (await getJSON("/api/display-config")) || {}; }
  catch (e) { S.displayConfig = {}; }
}
function setGreyscale(on) {
  document.documentElement.setAttribute("data-greyscale", on ? "1" : "0");
  const b = $("grey-btn");
  if (b) b.setAttribute("aria-pressed", on ? "true" : "false");
}
function setTheme(light) {
  document.documentElement.setAttribute("data-theme", light ? "light" : "dark");
  const seg = $("theme-seg");
  if (seg && seg.querySelectorAll) seg.querySelectorAll("[data-theme-set]").forEach((b) =>
    b.setAttribute("aria-pressed", String((b.dataset.themeSet === "light") === light)));
  try { localStorage.setItem("mcs.theme", light ? "light" : "dark"); } catch (e) { /* */ }
}

/* ═══ 20. BOOT ════════════════════════════════════════════════════════════ */

/* S15 dump playback shared by the CMD panel and all seven L2 containers. */
const dumpState = {};   // sub -> {rows, chart}
async function requestTmDump(sub, storeId) {
  const r = await postJSON("/api/tm-dump", { subsystem: sub, store_id: storeId || undefined });
  if (!r.ok) { announce(tText("dump request failed ({{status}})", { status: r.status })); return; }
  setTimeout(() => loadDumpData(sub), 1200);
}
async function loadDumpData(sub) {
  try {
    const d = await getJSON(`/api/tm-dump-data?subsystem=${encodeURIComponent(sub)}`);
    const rows = d.rows || d.samples || d.data || [];
    dumpState[sub] = { rows };
    renderDumpChart(sub);
  } catch (e) {
    const pageId = Object.keys(PAGE_SUBSYSTEM).find((k) => PAGE_SUBSYSTEM[k] === sub);
    if (pageId) setText(`${pageId}-dump-status`, tText("dump data unavailable"));
  }
}
function renderDumpChart(sub) {
  const pageId = Object.keys(PAGE_SUBSYSTEM).find((k) => PAGE_SUBSYSTEM[k] === sub);
  if (!pageId) return;
  const st = dumpState[sub];
  const statusEl = `${pageId}-dump-status`;
  if (!st || !st.rows.length) { setText(statusEl, tText("dump empty")); return; }
  setText(statusEl, tText("{{n}} samples", { n: st.rows.length }));
  const cv = $(`${pageId}-dump-chart`);
  const scrub = $(`${pageId}-dump-scrub`);
  if (typeof Chart === "undefined") {
    setText(statusEl, tText("{{n}} samples — Chart.js not installed; latest: {{json}}",
      { n: st.rows.length, json: JSON.stringify(st.rows[st.rows.length - 1]).slice(0, 120) }));
    return;
  }
  if (cv) cv.classList.remove("hide");
  if (scrub) scrub.classList.remove("hide");
  const frac = scrub ? Number(scrub.value) / 100 : 1;
  const upto = Math.max(2, Math.floor(st.rows.length * frac));
  const keys = Object.keys(st.rows[0]).filter((k) => k !== "ts" && k !== "t" &&
    Number.isFinite(Number(st.rows[0][k]))).slice(0, 4);
  const datasets = keys.map((k, i) => ({
    label: k, pointRadius: 0, borderWidth: 1.5,
    borderColor: `hsl(${i * 70},15%,${60 + i * 5}%)`,
    data: st.rows.slice(0, upto).map((r) => ({ x: (r.ts ?? r.t) * 1000, y: Number(r[k]) })) }));
  if (st.chart) st.chart.destroy();
  st.chart = new Chart(cv.getContext("2d"), {
    type: "line", data: { datasets },
    options: { animation: false, scales: { x: { type: "linear",
      ticks: { callback: (v) => fmtUTC(v / 1000) } } } } });
}

async function loadTcCatalog() {
  try {
    const d = await getJSON(`/api/tc-catalog?position=${encodeURIComponent(S.position)}`);
    S.tcCatalog = d.commands || [];
    S.quickCommands = d.quick_commands || [];
  } catch (e) { /* keep old */ }
  renderCmdCatalogSelect();
  renderQuickCommands();
  updateCmdBuilder();
}

function renderCurrentPage(full) {
  if (S.page === "ovr") updateOverview();
  else if (SUB_PAGES.includes(S.page)) {
    updateSubsystemPage(S.page, full);
    if (full && S.page === "ttc") loadLinkPrediction();   // G5 warm fetch
    if (full && S.page === "prp") loadBurnPlan();         // G9 warm fetch
  }
  else if (S.page === "cmd") { if (full) { renderCmdCatalogSelect(); updateCmdBuilder(); renderQuickCommands(); renderVerifLog(); } }
  else if (S.page === "diag") { if (full) { renderDiag(); loadFdir(); } else refreshDiagLive(); }
  else if (S.page === "fdir") { if (full) loadFdir(); else renderFdirPage(); }
  else if (S.page === "proc") { if (full) { loadProcSources(); refreshProcStatus(); } }
  else if (S.page === "trnd") { if (full) loadTrndParamNames(); renderBaselineCard(); }
  else if (S.page === "man") { if (full) { loadManual(); loadProcedureCards(); } }
}

/* The page skeletons are built ONCE, in English, with data-i18n* marks on
 * their static text; i18n.js translates them here and again on every language
 * switch (setLang -> applyDom), so typed inputs and mounted schematics survive
 * a switch. Everything rendered later goes through t()/tText() instead. The
 * keys of those marks are listed in TEMPLATE_I18N_KEYS for `i18n check`. */
function buildPages() {
  const host = $("pages");
  if (!host) return;
  host.innerHTML =
    buildOverviewPage() +
    SUB_PAGES.map(buildSubsystemPage).join("") +
    buildCmdPage() + buildFdirPage() + buildProcPage() +
    buildTrndPage() + buildDiagPage() + buildManPage();
  I18n.applyDom(host);
  // Scrolling regions must be reachable by keyboard (axe
  // scrollable-region-focusable): make each one a focus stop.
  if (host.querySelectorAll) host.querySelectorAll(".scroll-y").forEach((el) => {
    if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "0");
  });
}
// The data-i18n / -aria-label / -placeholder / -html texts of the page skeletons
// above, listed for `i18n check` (its table scan reads <= 2000 chars per table).
// i18n-keys
const _TPL_KEYS_1 = [
  "Overview", "Spacecraft overview",
  "The schematic is the navigation — click the thing you are worried about. Position:",
  "EOSAT-1 · functional schematic", "grey is nominal — colour marks deviation (P1)",
  "Contact windows (24 h)", "Ground track", "System board", "Electrical power", "Thermal control",
  "Attitude & orbit control", "Telemetry, tracking & command", "Payload", "Propulsion",
  "On-board data handling", "Level 2 · subsystem", "alarms for this subsystem", "← Overview", "Schematic",
  "click a block to navigate; values live", "Parameters", "AND — generated from /api/param-catalog (P10)",
  "Stored TM playback", "S15 dump → /api/tm-dump-data", "REQUEST DUMP (S15)", "no dump loaded",
  "Playback position", "Key parameters", "Projections", "ground-derived · not downlinked",
  "Capture readiness (NOM-002)", "gates from display_config.yaml", "FINE-entry readiness",
  "aocs.fine_ready 0x02C5 decoded", "Arm interlocks", "prop.arm_inhibit_mask 0x0B15 decoded",
  "Loaded vs planned burn", "TM 0x0B0E/0x0B10 vs planner orbit_manoeuvre", "awaiting planner…",
  "Predicted vs measured link", "Blind commanding (CON-004)", "requires FD GO — armed toggle", "Equipment",
  "Command", "in place · position-gated (P9)", "Ground station network", "awaiting station list…",
  "Power budget", "awaiting data…", "Events", "Commanding",
  "PUS telecommand builder · verification is a stepper attached to the command, not a separate log (P9)",
  "Command builder", "Catalogue command", "Service", "Subtype", "Name", "optional",
];
// i18n-keys
const _TPL_KEYS_2 = [
  "Data (hex) — live from the fields; paste hex to decode; Enter sends", "Quick commands", "position-gated; denied entries say who owns them",
  "Verification log", "Stored TM (S15) dump", "Subsystem", "Store id", "HK SID control (S3)",
  "Command history", "Diagnostics", "PUS services",
  "All seven service panels from the classic PUS SERVICES tab — S3 housekeeping · S11 scheduler · S6 memory · S15 stores · S12 monitoring · S19 event-action · S9 time — plus the parameter catalog. S12/S19 tables are the same renderer FDIR mounts (one implementation, two mounts).",
  "Parameter search (global)", "name or 0xHHHH", "Fault detection, isolation & recovery",
  "What the spacecraft <em>told</em> us (S5 / S12 / S19 / mode), plus recovery controls.", "FDIR state",
  "REFRESH ALL", "ACK ALL ALARMS", "Alarm / anomaly journal", "S5 events", "S12 transitions",
  "S19 rule fires", "TC rejections", "mode changes", "Procedures",
  "Loader · step-by-step runner · document viewer · manual override · builder. Reachable from any alarm row (P7.6).",
  "Load & run", "Source", "Activity type", "Ops procedure", "Saved procedure", "Procedure", "step-by-step",
  "LOAD", "Procedure document", "select a procedure…",
  "Manual override", "arbitrary TC during a run", "data hex", "Procedure builder",
  "procedure name", "Telemetry check", "Wait", "Note", ];
// i18n-keys
const _TPL_KEYS_3 = [
  "CLEAR", "— load saved —", "Trends",
  "Ground archive · eclipse/contact context · alarm & event markers (P8)", "Query", "Window", "7 d",
  "Parameter filter", "filter…", "limit bands", "eclipse/contact shading", "event + alarm markers",
  "normalise 0–100 %", "REFRESH", "EXPORT CSV", "Parameters to trend", "Subsystem playback",
  "LOAD SUBSYSTEM", "Chart", "Alarms in window", "Events in window", "Command history (archived)",
  "Baseline vs now — health (NOM-011)", "baseline: display_config.yaml commissioning snapshot", "Manual",
  "Operations manual", "Sections filtered to your position; search covers titles and body text.", "Contents",
  "search…", "select a section…", "Procedure cards — your position",
  "only cards my position is required for", "filter cards…",
  "Course PDFs", "textbooks · workbooks · references",
];
// i18n-keys
const _TPL_KEYS_4 = [
  "Magnetometer & MTQ", "measured B (0x020B-0D) beside the duties it drives",
  "GPS navigation (PVT)", "valid only with a 3D fix — zeros otherwise", "Software state",
  "Procedure controls", "Data (hex)", "Service", "Subtype", "Step type", "Saved procedures", "Subsystem",
  "EOSAT-1 overview", "Power", "line width is power on a fixed scale", "Power flow",
  "arrays to bus to loads and battery; raw values in Parameters below", "Attitude",
  "interpreted from the quaternions; raw values in Parameters below",
  ];
const TEMPLATE_I18N_KEYS = [..._TPL_KEYS_1, ..._TPL_KEYS_2, ..._TPL_KEYS_3, ..._TPL_KEYS_4];

function initDelegatedEvents() {
  // A control in the disabled state never acts: swallow the click before
  // any handler sees it, and say why (R3 A5).
  document.addEventListener("click", (e) => {
    const off = e.target.closest ? e.target.closest('[aria-disabled="true"]') : null;
    if (!off) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    showWhy(off);
    if (off.dataset.why) announce(off.dataset.why);
  }, true);
  for (const ev of ["focusin", "mouseover"]) {
    document.addEventListener(ev, (e) => {
      const b = e.target.closest ? e.target.closest("[data-why-out] button") : null;
      if (b) showWhy(b);
    });
  }
  document.addEventListener("click", (e) => {
    const t = e.target.closest ? e.target.closest("[data-man-anchor],[data-page-nav],[data-quick],[data-alarm-filter],[data-dump-request],[data-chain],[data-act],[data-proc],[data-s3],[data-s11],[data-s11-del],[data-s12],[data-s12row],[data-s12add],[data-s19],[data-s19row],[data-s19add],[data-s15st],[data-od-get],[data-man],[data-gonogo],[data-hk],[data-pb-del],[data-diag],[data-bd],[data-blind-toggle],[data-group],[data-conlog],[data-mon-trace]") : null;
    if (!t) return;
    const d = t.dataset;
    if (d.manAnchor) { e.preventDefault(); return scrollToManualAnchor(t, d.manAnchor); }
    if (d.pageNav) return showPage(d.pageNav);
    if (d.blindToggle) return toggleBlindTc();
    if (d.monTrace !== undefined) {
      e.preventDefault();
      s12Filter = String(d.monTrace);
      toggleAlarmDrawer(false);
      return showPage("fdir");
    }
    if (d.group !== undefined) {
      S.alarmGroupsOpen[d.group] = !S.alarmGroupsOpen[d.group];
      return renderAlarmDrawer();
    }
    if (d.conlog) return void postConsoleEntry(d.conlog);
    if (d.quick) return void sendQuick(d.quick);
    if (d.diag) return selectDiagTab(d.diag);
    if (d.bd) return selectBdTab(d.bd);
    if (d.alarmFilter !== undefined) {
      e.preventDefault();
      const sel = $("alarm-f-sub");
      if (sel) { sel.value = d.alarmFilter; persistAlarmFilters(); }
      return toggleAlarmDrawer(true);
    }
    if (d.dumpRequest) return void requestTmDump(d.dumpRequest);
    if (d.chain) return void openCausalChain(d.chain);
    if (d.act === "ack" && d.id !== undefined) return void ackAlarm(d.id, d.ids ? d.ids.split(",") : null);
    if (d.act === "procedure") { e.preventDefault(); return openProcedureFromAlarm(d.proc); }
    if (d.act === "ticket") return void lbTicketFromAlarm(d.id);
    if (d.act === "checklist") {
      if (t.getAttribute("aria-disabled") === "true") return;
      const id = lbProcedureId();
      return void (id && LB && LB.openChecklist(id));
    }
    if (d.proc) return void procAction(d.proc);
    if (d.s3) return void s3Command(d.s3, Number(d.sid));
    if (d.s11) return void s11Command(d.s11);
    if (d.s11Del !== undefined) return void s11Delete(d.s11Del);
    if (d.s12) return void s12Command(d.s12);
    if (d.s12row) return void s12RowCommand(d.s12row, d.mid);
    if (d.s12add) return void s12Add(d.s12add);
    if (d.s19) return void sendPus({ service: 19, subtype: 8, data_hex: "",
      name: "S19_REPORT", position: S.position });
    if (d.s19row) return void s19RowCommand(d.s19row, d.eid);
    if (d.s19add) return void s19Add(d.s19add);
    if (d.s15st) return void s15StoreCommand(d.s15st, d.store);
    if (d.odGet) return void onDemandGet(d.odGet);
    if (d.man !== undefined) { e.preventDefault(); return void openManualSection(d.man); }
    if (d.gonogo) return void goNoGoRespond(d.gonogo);
    if (d.hk) {
      const sid = Number($("hk-sid").value) || 1;
      const map = { enable: [3, 5], disable: [3, 6], oneshot: [3, 27] };
      const [svc, sub] = map[d.hk];
      return void sendPus({ service: svc, subtype: sub,
        data_hex: sidToHex(sid), name: `HK_${d.hk.toUpperCase()}_SID${sid}`, position: S.position })
        .then(() => setText("hk-quick-result", tText("{{name}} sent", { name: `S3 ${d.hk} SID ${sid}` })));
    }
    if (d.pbDel !== undefined) { pb.steps.splice(Number(d.pbDel), 1); return renderPbSteps(); }
  });
  document.addEventListener("input", (e) => {
    const t = e.target;
    if (!t || !t.id) {
      if (t && t.dataset && t.dataset.s12filter !== undefined) { s12Filter = t.value; renderDiag(); if (S.page === "fdir") renderFdirPage(); }
      // typed command-builder fields: live re-pack on every keystroke
      if (t && t.dataset && (t.dataset.cmdField !== undefined || t.dataset.cmdBit !== undefined)) cmdLivePack();
      return;
    }
    if (t.id === "cmd-data") cmdReverseDecode();
    else if (t.id === "s11-time" || t.id === "s11-mode") s11UpdatePreview();
    else if (t.id === "s9-set") s9UpdatePreview();
    else if (t.id === "trnd-filter") loadTrndParamNames();
    else if (t.id === "man-search") renderManual();
    else if (t.id === "pcard-search") preservingUi("pcard-list", renderProcedureCards);
    // renderParamsPanel() replaces #diag-params, which CONTAINS this input --
    // without preservingUi the element is destroyed on the first keystroke and
    // every later character goes nowhere.
    else if (t.id === "params-filter") { paramsFilter = t.value; preservingUi("diag-params", renderParamsPanel); }
    else if (t.id === "hdr-param-search") { paramsFilter = t.value; selectDiagTab("params"); }
    else if (t.id === "s6-patch") setText("s6-localcrc", tText("local CRC16 {{crc}}",
      { crc: `0x${crc16Ccitt(t.value).toString(16).toUpperCase().padStart(4, "0")}` }));
  });
  document.addEventListener("change", (e) => {
    const t = e.target;
    if (!t || !t.id) {
      if (t && t.dataset && t.dataset.s12ool !== undefined) { s12OolOnly = t.checked; renderDiag(); if (S.page === "fdir") renderFdirPage(); }
      if (t && t.dataset && t.dataset.fdirJ) { fdirJournalFilter[t.dataset.fdirJ] = t.checked; renderFdirJournal(); }
      // enum dropdowns / bitfield checkboxes in the command builder
      if (t && t.dataset && (t.dataset.cmdField !== undefined || t.dataset.cmdBit !== undefined)) cmdLivePack();
      return;
    }
    if (t.id === "pos-select") setPosition(t.value);
    else if (t.id === "pcard-mine-only") preservingUi("pcard-list", renderProcedureCards);
    else if (t.id === "cmd-catalog") { S.armed = {}; updateCmdBuilder(); }
    else if (t.id === "alarm-f-sub" || t.id === "alarm-f-sev") { persistAlarmFilters(); renderAlarmDrawer(); }
    else if (t.id === "evt-sev-filter") renderBottomDrawer();
    else if (t.id === "conlog-kind") { S.conlogKind = t.value; renderConsoleLog(); }
    else if (t.id === "s11-cmd") {
      const cmd = S.tcCatalog.find((c) => c.name === t.value);
      if (cmd) {
        if ($("s11-svc")) $("s11-svc").value = `${cmd.service},${cmd.subtype}`;
        if ($("s11-data")) $("s11-data").value = encodeCatalogCommand(cmd, {});
      }
    }
    else if (t.id === "proc-source") loadProcSources();
    else if (t.id === "proc-type") { loadProcDoc(); updateProcButtons(); }
    else if (t.id === "pb-step-type") setHTML("pb-step-fields", pbFieldMarkup());
    else if (t.id === "pb-saved" && t.value) {
      getJSON("/api/procedure/custom").then((d) => {
        const p = (d.procedures || []).find((x) => String(x.id || x.name) === t.value);
        if (p) { pb.steps = p.steps || []; if ($("pb-name")) $("pb-name").value = p.name || ""; renderPbSteps(); }
      });
    }
    else if (t.id && t.id.endsWith("-dump-scrub")) {
      const pageId = t.id.replace("-dump-scrub", "");
      renderDumpChart(PAGE_SUBSYSTEM[pageId]);
    }
    else if (t.id === "s6-file" && t.files && t.files[0]) {
      t.files[0].arrayBuffer().then((buf) => {
        const bytes = Array.from(new Uint8Array(buf));
        const hexStr = bytes.map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
        if ($("s6-patch")) $("s6-patch").value = hexStr;
        setText("s6-localcrc", tText("local CRC16 {{crc}}",
          { crc: `0x${crc16Ccitt(hexStr).toString(16).toUpperCase().padStart(4, "0")}` }));
      });
    }
  });
  document.addEventListener("click", (e) => {
    const a = e.target && e.target.closest ? e.target.closest("[data-pcard]") : null;
    if (!a) return;
    e.preventDefault();
    const id = a.dataset.pcard;
    S.procCardOpen = (S.procCardOpen === id) ? "" : id;
    preservingUi("pcard-list", renderProcedureCards);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    if (e.target && e.target.id === "cmd-data") { e.preventDefault(); sendCommand(); }
    // keyboard flow: Tab through the typed fields, Enter sends (the hex is
    // already live-packed); critical commands still require ARM first.
    if (e.target && e.target.dataset && e.target.dataset.cmdField !== undefined &&
        e.target.tagName !== "SELECT") { e.preventDefault(); sendCommand(); }
    if (e.target && e.target.id === "handover-input") { e.preventDefault(); addHandoverNote(); }
    if (e.target && e.target.id === "conlog-input") { e.preventDefault(); postConsoleEntry("note"); }
  });
  // Button bindings by id, resolved through DELEGATION rather than by binding a
  // listener to the element at init.
  //
  // Field report 2026-08-20: sixteen PUS-panel controls (s3-en-all, s6-dump,
  // s9-report, s11-add, params-refresh, ...) posted nothing at all. The reason
  // was that this helper used to be
  //     const on = (id, fn) => { const el = $(id); if (el) el.addEventListener(...) };
  // and it runs once at init — but the S3/S6/S9/S11/params panels are rendered
  // LAZILY when their diag tab is first clicked. At init those elements do not
  // exist, `if (el)` silently skipped them, and no listener was ever attached.
  // Every control that did work used data-* delegation. So: same call sites,
  // same ids, but the handler is looked up on the click instead.
  const _clickById = new Map();
  const on = (id, fn) => { _clickById.set(id, fn); };
  document.addEventListener("click", (e) => {
    let el = e.target;
    while (el && el !== document) {
      if (el.id && _clickById.has(el.id)) { _clickById.get(el.id)(e); return; }
      el = el.parentElement;
    }
  });
  on("alarms-btn", () => toggleAlarmDrawer());
  on("alarm-close", () => toggleAlarmDrawer(false));
  on("alarm-ack-all", () => ackAllAlarms());
  on("alarm-sound", () => setAlarmSound(!(alarmSoundOn() && !playAlarmBeep._muted)));
  renderAlarmSoundBtn();
  on("grey-btn", () => setGreyscale(document.documentElement.getAttribute("data-greyscale") !== "1"));
  document.addEventListener("click", (e) => {
    const b = e.target.closest ? e.target.closest("[data-theme-set]") : null;
    if (b) setTheme(b.dataset.themeSet === "light");
  });
  on("help-btn", () => toggleHelp());
  on("help-close", () => toggleHelp(false));
  on("chain-close", () => toggleChain(false));
  on("bd-toggle", () => {
    bdOpen = !bdOpen;
    $("bottom-drawer").classList.toggle("open", bdOpen);
    $("bd-toggle").setAttribute("aria-expanded", bdOpen ? "true" : "false");
    renderBottomDrawer();
  });
  on("handover-add", addHandoverNote);
  on("gonogo-start", goNoGoStart);
  on("cmd-send", () => sendCommand());
  if ($("proc-btn-abort")) armButton($("proc-btn-abort"), { seconds: 6,
    onExecute: () => procAction("abort") });
  // Critical commands: the shared two-step (arm, then execute within 8 s).
  if ($("cmd-send-crit")) armButton($("cmd-send-crit"), { seconds: 8,
    onExecute: () => sendCommand({ confirmed: true }) });
  document.addEventListener("input", (e) => {
    if (e.target && e.target.id === "qc-filter") { S.qcFilter = e.target.value; renderQuickCommands(); }
  });
  document.addEventListener("toggle", (e) => {
    const d = e.target;
    if (d && d.dataset && d.dataset.qcGroup !== undefined && !S.qcFilter) {
      S.qcOpen = S.qcOpen || {};
      S.qcOpen[d.dataset.qcGroup] = d.open;
    }
  }, true);
  on("cmd-pack", () => cmdLivePack());
  on("cmd-decode", () => cmdReverseDecode());
  on("s15-dump", () => requestTmDump($("s15-target").value, $("s15-store").value)
    .then(() => setText("s15-result", tText("dump requested for {{sub}}", { sub: $("s15-target").value }))));
  on("s3-req-all", () => s3All("oneshot"));
  on("s3-en-all", () => s3All("enable"));
  on("s3-dis-all", () => s3All("disable"));
  on("s3-reload", () => loadHkStructures().then(renderS3Panel));
  on("s11-now", () => { if ($("s11-mode").value === "rel") $("s11-time").value = "0";
    else $("s11-time").value = fmtUTC(simNow(), { date: true }).replace(" ", "T"); s11UpdatePreview(); });
  on("s11-add", s11Add);
  on("s6-dump", () => s6Command(5));
  on("s6-crc", () => s6Command(9));
  on("s6-load", () => {
    const patch = String($("s6-patch").value || "").replace(/[\s,]+/g, "").replace(/(..)/g, "$1 ").trim();
    s6Command(2, patch);
  });
  on("s6-verify", () => s6Command(9));
  on("s6-readback", () => s6Command(5));
  on("s9-report", () => sendPus({ service: 9, subtype: 2, data_hex: "",
    name: "S9_REPORT", position: S.position }));
  on("s9-sync", () => s9SetTime(""));
  on("s9-set-now", () => { $("s9-set").value = fmtUTC(simNow(), { date: true }).replace(" ", "T"); s9UpdatePreview(); });
  on("s9-set-send", () => s9SetTime($("s9-set").value));
  on("fdir-refresh-all", () => {
    sendPus({ service: 12, subtype: 12, data_hex: "", name: "S12_REPORT", position: S.position });
    sendPus({ service: 19, subtype: 8, data_hex: "", name: "S19_REPORT", position: S.position });
    loadFdir();
  });
  on("fdir-ack-all", ackAllAlarms);
  on("proc-ov-send", async () => {
    const r = await postJSON("/api/procedure/override-command", {
      service: Number($("proc-ov-svc").value), subtype: Number($("proc-ov-sub").value),
      data: $("proc-ov-data").value, position: S.position });
    setText("proc-ov-result", r.ok ? tText("override sent") : tText("override rejected ({{status}})", { status: r.status }));
  });
  on("pb-add", pbAddStep);
  on("pb-save", pbSave);
  on("pb-run", pbRun);
  on("pb-clear", () => { pb.steps = []; renderPbSteps(); });
  on("trnd-refresh", refreshTrend);
  on("trnd-csv", exportTrendCsv);
  on("trnd-playback", loadSubsystemPlayback);
  on("params-refresh", () => renderParamsPanel());
}
async function s3All(action) {
  const structures = ((S.hkStructures || {}).structures) || [];
  for (const s2 of structures) await s3Command(action, s2.sid);
}
async function s12Command(action) {
  const map = { refresh: [12, 12], enable: [12, 1], disable: [12, 2] };
  const [svc, sub] = map[action];
  await sendPus({ service: svc, subtype: sub, data_hex: "",
    name: `S12_${action.toUpperCase()}`, position: S.position });
  if (action === "refresh") setTimeout(loadFdir, 800);
}
async function s12RowCommand(action, monId) {
  // Simulator S12: 3 enable / 4 disable / 7 delete ONE definition, mon_id as
  // u16 (config monitors are 0x8000+). A 1-byte id was silently ignored.
  const map = { enable: 3, disable: 4, delete: 7 };
  const data = (Number(monId) & 0xFFFF).toString(16).toUpperCase().padStart(4, "0");
  await sendPus({ service: 12, subtype: map[action], data_hex: data,
    name: `S12_${action.toUpperCase()}_${monId}`, position: S.position });
  setTimeout(loadFdir, 800);
}
async function s12Add(mount) {
  const mid = Number($(`s12-add-mid-${mount}`).value) & 0xFFFF;
  const pid = parseInt($(`s12-add-pid-${mount}`).value, 16) >>> 0;
  const type = Number($(`s12-add-type-${mount}`).value) & 0xFF;
  const lo = parseFloat($(`s12-add-low-${mount}`).value);
  const hi = parseFloat($(`s12-add-high-${mount}`).value);
  const f32 = (v) => {
    const b = new ArrayBuffer(4); new DataView(b).setFloat32(0, v, false);
    return Array.from(new Uint8Array(b));
  };
  // TC(12,6) 13-byte form: mon_id u16, param_id u16, check_type u8, low f32, high f32.
  const bytes = [(mid >> 8) & 255, mid & 255, (pid >> 8) & 255, pid & 255, type, ...f32(lo), ...f32(hi)];
  await sendPus({ service: 12, subtype: 6,
    data_hex: bytes.map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" "),
    name: `S12_ADD_${mid}`, position: S.position });
  setTimeout(loadFdir, 800);
}
async function s19RowCommand(action, eaId) {
  const map = { enable: 4, disable: 5, delete: 2 };
  // ea_id is u16 on the wire; the simulator ignores a 1-byte id.
  const data = (Number(eaId) & 0xFFFF).toString(16).toUpperCase().padStart(4, "0");
  await sendPus({ service: 19, subtype: map[action], data_hex: data,
    name: `S19_${action.toUpperCase()}_${eaId}`, position: S.position });
  setTimeout(loadFdir, 800);
}
async function s19Add(mount) {
  const eid = Number($(`s19-add-eid-${mount}`).value) & 0xFF;
  const kind = Number($(`s19-add-kind-${mount}`).value) & 0xFF;
  const trig = parseInt($(`s19-add-trig-${mount}`).value, 16) >>> 0;
  const action = $(`s19-add-action-${mount}`).value;
  const cmd = S.tcCatalog.find((c) => c.name === action) || {};
  const argHex = encodeCatalogCommand(cmd, {});
  const head = [eid, kind, (trig >> 8) & 255, trig & 255, cmd.service & 255, cmd.subtype & 255]
    .map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
  await sendPus({ service: 19, subtype: 1,
    data_hex: head + (argHex ? " " + argHex : ""), name: `S19_ADD_${eid}`, position: S.position });
  setTimeout(loadFdir, 800);
}

async function loadPositions() {
  try {
    S.positions = (await getJSON("/api/positions")).positions || {};
    renderPosSelect();
  } catch (e) { /* offline */ }
}
function renderPosSelect() {
  const sel = $("pos-select");
  if (!sel) return;
  sel.innerHTML = Object.entries(S.positions).map(([id, p]) =>
    `<option value="${esc(id)}">${esc(p.label ? tdb(`pos:${id}:label`, p.label) : id)}</option>`).join("");
  sel.value = S.position;
}
async function loadParamCatalog() {
  try {
    const d = await getJSON("/api/param-catalog");
    S.paramCatalog = (d.parameters || []).map((p) => ({
      ...p, hex: p.hex || fmtHex(p.id, 4) }));
    S.paramByHex = {};
    for (const p of S.paramCatalog) S.paramByHex[p.hex] = p;
  } catch (e) { /* offline */ }
}
async function loadLimits() {
  try { S.limits = (await getJSON("/api/limits")).limits || {}; }
  catch (e) { /* offline */ }
}
async function loadContacts() {
  try {
    const d = await getJSON("/api/contacts");
    S.contacts = d.contacts || d.windows || [];
  } catch (e) { /* planner offline */ }
}
async function loadContactSchedule() {
  try {
    // R3 A1: the server field is `next_passes` (each pass: aos_time,
    // los_time, ground_station, max_elevation). Reading `d.passes` left the
    // "What's next?" card and the pass table permanently empty. Pinned by
    // tests/test_mcs/test_contact_schedule_contract.py — no fallbacks, so a
    // rename fails a test instead of blanking the screen.
    const d = await getJSON("/api/displays/contact-schedule");
    S.contactSchedule = Array.isArray(d.next_passes) ? d.next_passes : [];
  } catch (e) { /* offline */ }
}
async function loadGroundStations() {
  try {
    const d = await getJSON("/api/ground-stations");
    S.groundStations = d.stations || d.ground_stations || [];
  } catch (e) { /* offline */ }
}
async function loadFailureCodes() {
  try { S.failureCodes = (await getJSON("/api/failure-codes")).codes || {}; }
  catch (e) { /* offline */ }
}
async function loadVerifLogRest() {
  try {
    const d = await getJSON("/api/verification-log");
    const rows = d.log || d.entries || [];
    if (rows.length) {
      // Row shape (server _VERIF_ROW_DEFAULTS): seq, name ("S17.1"),
      // service, subtype, state (SENT/ACCEPTED/COMPLETED/FAILED/...),
      // error_code, error_text, reason, timestamp, position. (Agent 5 fix:
      // the previous mapping read tc_service/ok/verdict, which this API
      // never emits, rendering "TC(undefined,undefined)".)
      S.verifLog = rows.slice(0, 80).map((v) => ({
        ts: fmtUTC(v.timestamp),
        verdict: `${v.state || "?"}`,
        text: `TC(${v.service},${v.subtype})` +
              (v.name ? ` ${v.name}` : "") +
              (v.error_text ? ` — ${v.error_text}` : "") }));
      renderVerifLog();
    }
  } catch (e) { /* offline */ }
}

/* ═══ 19b. PICTORIAL VIEWS ═══════════════════════════════════════════════════
 * The shared pictorial displays (shared/ui-viz -> /static/shared/viz/) are
 * mounted by static/modern/pictorial.js, loaded with a dynamic import so the
 * console still boots (with its schematics) when they are absent. */
let PIC = null;
async function loadPictorial() {
  if (globalThis.__MCS_TEST__) return;
  try {
    const m = await import("/static/modern/pictorial.js");
    await m.init({
      state: () => S.state, limits: () => S.limits, freshness: paramFreshness,
      alarmSummary: () => alarmSummary(), scModeInfo, linkState: () => linkState(),
      nowS: simNowSec, showPage, t: tText, engValue,
      visibleSubsystems: () => {
        const pos = S.positions[S.position];
        if (!pos || S.position === "flight_director") return null;
        const list = pos.overview_subsystems || pos.subsystems || [];
        return list.length ? list : null;
      },
    });
    PIC = m;
  } catch (e) {
    PIC = null;
    try { console.warn("pictorial views unavailable; schematics kept", e); } catch (e2) { /* no console */ }
  }
}

/* ═══ LOGBOOK ═══════════════════════════════════════════════════════════════
 * The participant's private logbook (smo_common/ui/logbook.js): a header
 * button opens a docked panel; "Log this" buttons sit beside command send,
 * the procedure controls, the GO/NO-GO answers and every alarm ACK and never
 * block them. Context = page, open procedure (+ step), selected command,
 * GO/NO-GO poll, position, sim time. When the simulator goes from running
 * to stopped (speed 0 for 5 s) the end-of-session dialog offers the debrief
 * worksheet and the download, at most once every 15 minutes. */
let LB = null;
let lbProcIndex = null;               // procedure file -> id
let lbSimRunning = null, lbStopTimer = null, lbLastPrompt = -Infinity;
const PROC_ID_RE = /^(NOM|LEOP|COM|CTG|EMG)-\d{3}$/;
async function lbLoadProcIndex() {
  try {
    const d = await getJSON("/api/procedure/index");
    lbProcIndex = {};
    for (const p of d.procedures || []) if (p.id && p.file) lbProcIndex[p.file] = p.id;
  } catch (e) { lbProcIndex = {}; }
}
function lbProcedureId() {
  const st = S.procStatus || {};
  const ref = String(st.procedure_ref || "");
  if (st.state && st.state !== "IDLE" && ref) {
    if (PROC_ID_RE.test(ref)) return ref;
    if (lbProcIndex && lbProcIndex[ref]) return lbProcIndex[ref];
  }
  if (S.page === "proc" && $("proc-source") && $("proc-source").value === "ops") {
    const v = $("proc-type") ? $("proc-type").value : "";
    if (v && lbProcIndex && lbProcIndex[v]) return lbProcIndex[v];
  }
  if (S.procCardOpen && PROC_ID_RE.test(S.procCardOpen)) return S.procCardOpen;
  return "";
}
function lbContext() {
  const c = { page: S.page, position: S.position };
  const proc = lbProcedureId();
  if (proc) c.procedure = proc;
  const st = S.procStatus || {};
  if (proc && st.state && st.state !== "IDLE" && Number.isFinite(Number(st.current_step))) {
    c.step = Number(st.current_step) + 1;
  }
  if (S.page === "cmd") {
    const cmd = currentCatalogCmd();
    if (cmd && cmd.name) c.command = cmd.name;
  }
  if (bdOpen && bdTab === "gonogo" && S.goNoGo && S.goNoGo.label) c.gonogo = S.goNoGo.label;
  if (S.timeMode === "sim") c.sim_ts = simNow().toISOString().replace(/\.\d+Z$/, "Z");
  if (lbSimRunning !== null) c.sim_status = lbSimRunning ? "running" : "stopped";
  return c;
}
function lbWatchSimStatus() {
  if (!LB || S.timeMode !== "sim") return;
  const speed = Number(S.state.speed);
  if (!Number.isFinite(speed)) return;
  const running = speed > 0;
  if (lbSimRunning === true && !running && !lbStopTimer) {
    lbStopTimer = setTimeout(() => {
      lbStopTimer = null;
      if (Number(S.state.speed) === 0 && performance.now() - lbLastPrompt > 15 * 60e3) {
        lbLastPrompt = performance.now();
        LB.endSession({ reason: "stopped" });
      }
    }, 5000);
  }
  if (running && lbStopTimer) { clearTimeout(lbStopTimer); lbStopTimer = null; }
  lbSimRunning = running;
}
/* ── Ops workbook hooks (logbook "Workbook" tab) ──────────────────────────
 * readParam: a checklist step captures the observed value of each parameter
 * its card checks (engineering value, units, freshness). prefill / info: the
 * forms (worksheet_map.yaml `prefill:` keys) start from the console state —
 * the alarm, the contact schedule, the runner, the GO/NO-GO poll. The
 * operator edits or clears every prefilled field before saving. */
let lbNameHex = null, lbNameHexN = -1;
function lbHexOf(name, pid) {
  if (pid) {
    const h = "0x" + String(pid).slice(2).toUpperCase();
    if (S.paramByHex[h] || paramVal(h) !== undefined) return h;
  }
  if (lbNameHexN !== S.paramCatalog.length) {
    lbNameHex = {};
    for (const p of S.paramCatalog) if (p.name) lbNameHex[p.name] = p.hex;
    lbNameHexN = S.paramCatalog.length;
  }
  return (name && lbNameHex[name]) || (pid ? "0x" + String(pid).slice(2).toUpperCase() : null);
}
function lbReadParam(name, pid) {
  const hex = lbHexOf(name, pid);
  if (!hex) return null;
  const raw = paramVal(hex);
  if (raw === undefined || raw === null || raw === "") return { nodata: true };
  const def = S.paramByHex[hex] || {};
  const eng = engValue(hex, raw);
  const n = Number(raw);
  const text = eng !== null ? eng
    : Number.isFinite(n) ? (Number.isInteger(n) ? String(n)
      : num(n, Math.abs(n) >= 100 ? 1 : Math.abs(n) >= 1 ? 2 : 3)) : String(raw);
  const fr = paramFreshness(hex);
  return { raw, text, units: eng !== null ? "" : (def.units || ""), nodata: false,
    stale: fr === "stale" || fr === "disabled" };
}
function lbParamLine(name, pid) {
  const r = lbReadParam(name, pid);
  const v = !r || r.nodata ? tText("no data") : `${r.text}${r.units ? " " + r.units : ""}${r.stale ? " (" + tText("stale") + ")" : ""}`;
  return `${name} = ${v}`;
}
function lbPassText(p) {
  if (!p) return "";
  const hm = (x) => (x ? fmtUTC(x, { date: false }) : "—");
  return `${p.ground_station || p.station || "?"} AOS ${hm(p.aos_time)} LOS ${hm(p.los_time)}` +
    (Number.isFinite(Number(p.max_elevation)) ? ` · ${tText("max el")} ${num(p.max_elevation, 0)}°` : "");
}
function lbOpenAlarms() {
  return alarmGroups(S.alarms.filter((a) => !a.rtn)).filter((g) => !g.acknowledged || g.pri <= 2);
}
function lbAlarmLine(a) {
  const hexId = alarmParamHex(a);
  const def = hexId ? S.paramByHex[hexId] : null;
  const name = a.name || (def && def.name) || String(a.message || a.id);
  const v = a.value !== undefined && a.value !== null ? ` = ${a.value}${(a.units || (def && def.units)) ? " " + (a.units || def.units) : ""}` : "";
  return `${name}${hexId ? ` (${hexId})` : ""}${v}${a.limit ? ` · ${tText("limit")} ${a.limit}` : ""}` +
    `${a.acknowledged ? "" : ` · ${tText("not acknowledged")}`}`;
}
function lbGoNoGoText(g) {
  if (!g) return "";
  const resp = Object.entries(g.responses || {}).map(([pos, r]) =>
    `${POSITION_INFO[pos] ? tText(POSITION_INFO[pos].title) : pos} ${r}`).join(", ");
  return `${g.label || "GO/NO-GO"}: ${g.active ? tText("open") : (g.result || tText("closed"))}` + (resp ? ` — ${resp}` : "");
}
function lbPrefill(key, ctx) {
  const a = ctx.alarm || (ctx.alarm_id !== undefined ? S.alarms.find((x) => String(x.id) === String(ctx.alarm_id)) : null);
  const st = S.procStatus || {};
  const proc = lbProcedureId();
  const next = (S.contactSchedule || [])[0];
  const inContact = !!(S.state.sa && S.state.sa.in_contact);
  switch (key) {
    case "ticket_id": {
      const d = simNow();
      return `AT-${d.toISOString().slice(5, 10).replace("-", "")}-${a ? a.id : d.toISOString().slice(11, 16).replace(":", "")}`;
    }
    case "pass": return inContact ? `${(S.state.sa || {}).ground_station_name || ""} ${tText("in contact")}`.trim() : lbPassText(next);
    case "alarm_time": {
      const ts = a ? (a.first_ts || a.timestamp || a.last_ts) : null;
      return ts ? fmtUTC(ts, { date: true, seconds: true }) + ` (${tText("sim")})` : "";
    }
    case "param_value": return a ? lbAlarmLine(a) : "";
    case "fdir_rule": {
      if (!a) return "";
      const src = String(a.source || "").toUpperCase();
      if (src === "S12") return `S12 ${tText("on-board monitor")} #${a.mon_id ?? "?"}${a.monitor_name ? " " + a.monitor_name : ""}`;
      if (src === "S5") return `S5 ${tText("on-board event")} ${a.event_id ?? ""}`.trim();
      if (src === "LIMIT") return `${tText("ground limit")} (${a.config_file || "mcs/limits.yaml"})`;
      return "";
    }
    case "severity": return a && a.severity !== undefined ? String(a.severity) : "";
    case "position": return POSITION_INFO[S.position] ? `${tText(POSITION_INFO[S.position].title)} (${S.position})` : S.position;
    case "first_action": return tsShort() + ` (${tText("sim")})`;
    case "procedure": return (a && a.procedure && (a.procedure.id || a.procedure.name)) || proc || "";
    case "procedure_state":
      return st.state && st.state !== "IDLE"
        ? `${proc || st.procedure_name || ""} · ${tText("step {{n}}", { n: Number(st.current_step) + 1 })} · ${st.state}`
        : proc ? `${proc} · ${tText("open, not running")}` : "";
    case "params_top3": {
      const al = lbOpenAlarms().slice(0, 3).map(lbAlarmLine);
      if (al.length) return al.join("; ");
      return [["eps.bat_soc", "0x0101"], ["eps.bus_voltage", "0x0105"], ["aocs.mode", "0x020F"]]
        .map(([n, h]) => lbParamLine(n, h)).join("; ");
    }
    case "open_items": case "open_alarms": {
      const al = lbOpenAlarms().map(lbAlarmLine);
      const items = [...al];
      if (key === "open_items" && st.state && ["RUNNING", "PAUSED", "LOADED"].includes(st.state)) {
        items.push(`${proc || st.procedure_name} ${st.state}`);
      }
      return items.join("; ");
    }
    case "now": return tsShort() + ` (${tText("sim")})`;
    case "fdir_active":
      return lbOpenAlarms().filter((g) => ["S12", "S19", "S5"].includes(String(g.source || "").toUpperCase()))
        .map(lbAlarmLine).join("; ");
    case "phase_time": {
      const ph = lbReadParam("eps.spacecraft_phase", "0x0129");
      return `${tText("phase")} ${ph && !ph.nodata ? ph.text : "?"} · ${tsShort()} (${tText("sim")})`;
    }
    case "last_pass": return "";
    case "next_pass": case "next_aos": return lbPassText(next);
    case "gonogo_open": return S.goNoGo && S.goNoGo.active ? lbGoNoGoText(S.goNoGo) : "";
    case "gonogo": return lbGoNoGoText(S.goNoGo);
    default: return "";
  }
}
function lbInfo(kind, ctx) {
  const out = [];
  if (kind === "briefing") {
    for (const p of (S.contactSchedule || []).slice(0, 3)) {
      out.push({ label: tText("Pass"), value: lbPassText(p) });
    }
    if (!out.length) out.push({ label: tText("Pass"), value: tText("no pass in the contact schedule") });
    out.push({ label: tText("Console"), value: [["eps.bat_soc", "0x0101"], ["eps.spacecraft_phase", "0x0129"],
      ["obdh.sw_image", "0x0311"]].map(([n, h]) => lbParamLine(n, h)).join("; ") });
  } else if (kind === "scorecard" && S.goNoGo) {
    out.push({ label: "GO/NO-GO", value: lbGoNoGoText(S.goNoGo) });
  } else if (kind === "anomaly" && (ctx.alarm || ctx.alarm_id !== undefined)) {
    out.push({ label: tText("From alarm"), value: lbPrefill("param_value", ctx) });
  } else if (kind === "handover") {
    out.push({ label: tText("Position"), value: lbPrefill("position", ctx) });
    out.push({ label: tText("Console time"), value: tsShort() + ` (${tText("sim")})` });
  }
  return out;
}
function lbTicketFromAlarm(id) {
  const a = S.alarms.find((x) => String(x.id) === String(id));
  if (LB) LB.openForm("anomaly", { alarm: a || null, alarm_id: id });
}

function initLogbook() {
  const slot = $("lb-slot");
  LB = mountLogbook({ tool: "mcs", getContext: lbContext, buttonHost: slot,
    bannerHost: $("top-bar"), buttonClass: "ds-btn ghost lb-btn",
    readParam: lbReadParam, prefill: lbPrefill, info: lbInfo,
    handIn: () => ({ position: POSITION_INFO[S.position] ? `${tText(POSITION_INFO[S.position].title)} (${S.position})` : S.position }) });
  const gn = $("gonogo-logthis");
  if (gn) gn.innerHTML = renderLogThis({}, { kind: "decision" });
  lbLoadProcIndex();
}

async function boot() {
  // Catalogs first (English: resolves at once, no fetch; otherwise bounded
  // by i18n.js's load timeout) so the first render is already translated.
  // Telemetry handling starts below with connectWS(), unaffected.
  await I18n.ready;
  mountLangToggle($("lang-toggle"));
  onLangChange(onLanguageChange);
  buildRail();
  buildPages();
  initDelegatedEvents();
  initKeyboard();
  initSchematicNav();
  initFocusTrap();
  initLogbook();
  setHTML("pb-step-fields", pbFieldMarkup());
  // restore persisted prefs
  try {
    if (localStorage.getItem("mcs.theme") === "light") setTheme(true);
    const pos = localStorage.getItem("mcs.position");
    if (pos) S.position = pos;
  } catch (e) { /* private mode */ }
  restoreAlarmFilters();
  await Promise.all([loadParamCatalog(), loadLimits(), loadPositions()]);
  try { S.clientConfig = await getJSON("/api/client-config"); } catch (e) { S.clientConfig = {}; }
  await Promise.all([loadTcCatalog(), loadSchematics(), loadDisplayConfig(),
    loadHkStructures(), loadMemoryMap(), loadAlarms(), loadFailureCodes(),
    loadFaultGraph(), loadGonogoMatrix(), loadConsoleLog()]);
  await loadPictorial();
  const sel = $("pos-select");
  if (sel) sel.value = S.position;
  connectWS();
  startRestFallback();
  startClocks();
  resolveTimeMode();
  applyPositionFilter();
  showPage("ovr");
  selectBdTab("events", false);   // collapsed 24 px strip on boot
  // polling cadences preserved from the classic console
  poller(loadContactSchedule, 30000).start();       // 30 s pass schedule
  poller(loadContacts, 60000).start();              // 60 s contact windows
  poller(loadVerifLogRest, 5000).start();           // 5 s verification log
  poller(refreshSystemBoard, 5000).start();         // 5 s system overview
  poller(refreshPowerBudget, 5000).start();         // 5 s power budget (EPS page)
  poller(loadAlarms, 10000).start();                // journal reconciliation
  poller(loadHandover, 15000).start();
  poller(async () => { if (S.page === "fdir" || (S.page === "diag" && (diagTab === "s12" || diagTab === "s19"))) await loadFdir(); }, 2000).start();
  poller(resolveTimeMode, 60000).start();
  // POSITION_NEEDS gap surfaces (page-gated inside the loaders)
  poller(loadLinkPrediction, 20000).start();        // G5 — TTC page only
  poller(loadBurnPlan, 30000).start();              // G9 — PROP page only
  poller(loadConsoleLog, 15000).start();            // G8 merged stream
  poller(loadFaultGraph, 120000).start();           // G6 — config changes rarely
}

/* Language switch (smo:langchange). Static markup with data-i18n* is
 * re-applied by i18n.js itself; this re-renders the JS-built regions that do
 * not refresh on the next telemetry tick. Translators (S1) extend it. */
function onLanguageChange() {
  loadProcDoc();                                          // ?lang= document
  if (S.manualOpen) openManualSection(S.manualOpen);      // ?lang= manual
  // JS-built regions (page skeletons were re-translated by applyDom already)
  // mounted schematics (setLang's document-wide applyDom covers them too; explicit for clarity)
  document.querySelectorAll("svg[data-schematic]").forEach((svg) => I18n.applyDom(svg));
  const ovrMode = $("sch-ovr-mode");   // inside a data-i18n <text>; only re-set while OVR is showing
  if (ovrMode) ovrMode.textContent = scModeInfo().label;
  if (PIC) { PIC.relabel(); renderCurrentPage(false); }
  retitleRail();
  renderPosSelect();
  applyPositionFilter();          // position title, quick commands, manual TOC
  renderCmdCatalogSelect();
  refreshCmdBuilderText();        // not updateCmdBuilder(): that would drop typed field values
  renderVerifLog();
  renderCmdHistory();
  renderBlindTc();
  updateTrainingChip();
  updateContingency();
  updateSaHeader();
  renderAlarmDrawer();
  renderBottomDrawer();
  renderGoNoGo();
  renderProcStatus();
  renderProcedureCards();
  renderBaselineCard();
  refreshSystemBoard();           // 5 s pollers: redo now rather than show stale wording
  refreshPowerBudget();
  const pbf = $("pb-step-fields");     // placeholders only; keep anything typed
  if (pbf && !Array.from(pbf.querySelectorAll("input")).some((i) => i.value)) {
    setHTML("pb-step-fields", pbFieldMarkup());
  }
  if (S.page === "proc") loadProcSources();
  if (S.chainOpen) openCausalChain(S.chainOpen);
  renderCurrentPage(true);
}
/* Language switch: re-word the builder's provenance/authority lines in place. */
function refreshCmdBuilderText() {
  const cmd = currentCatalogCmd();
  const authEl = $("cmd-authority");
  if (cmd) {
    setText("cmd-provenance", provenanceText(cmd));
    if (authEl) authEl.textContent = commandAuthority(cmd.name).text;
  } else {
    setText("cmd-provenance", tText("raw command — no catalogue entry; length not validated"));
  }
}

/* Test hook: under the node harness (globalThis.__MCS_TEST__) nothing runs
 * automatically; the harness drives exported functions directly. */
export const __test = {
  S, adoptServerClock, simNowMs, updateSaHeader, trainingChipState,
  railVisibleForPosition, applyPositionFilter, showPage, buildRail, buildPages,
  renderAlarmDrawer, filteredAlarms, ackAlarm, ackAllAlarms, paramTriad,
  scModeInfo, fdirLevelInfo, commandAuthority, encodeCatalogCommand, decodeCatalogArgs,
  sidToHex, crc16Ccitt, s11CucSeconds, tmFreshness, handleState, handleTMPacket,
  handleAlarmMsg, renderBottomDrawer, renderS12Block,
  renderS19Block, renderMarkdown, scrollToManualAnchor, provenanceText, updateTrainingChip,
  loadSchematics, updateRailHealth,
  catFieldError, catLengthError, catFormatEng, isCritical, cmdFieldWidget,
  sendCommand, groundHighRateWarning, hkEnabledBit, hkEnableSummaryHtml,
  renderMagMtq, renderGpsNav, renderObdSwState, loadDisplayConfig,
  renderS3Panel, renderS11Table, renderS15Panel, renderS6Panel, renderS9Panel,
  renderParamsPanel, renderFdirPage, selectDiagTab, renderDiag,
  // re-exported so the node harness can pin the shared value surfaces
  renderAndTable, renderParam, liveValues,
  // POSITION_NEEDS gap surfaces (G1-G9, G12, G15)
  derivedEntry, fmtDerivedValue, renderDerivedRow, fitVerdictLine,
  parseBitLegend, renderBitmaskChips,
  captureGateTable, evalCaptureGate, computeCaptureReadiness, renderCaptureCard,
  linkNowReadout, renderLinkOverlay,
  groupAlarmsByAncestry,
  matchGonogoRow, renderGonogoMatrixRow, renderGoNoGo,
  renderConsoleLog,
  plannedBurnDv, burnMismatch, renderBurnCard,
  blindTcState, toggleBlindTc, blindHistoryChip, noteHistory, noteVerification,
  baselineTable, computeBaselineDeltas, renderBaselineCard,
  updateNextCard, renderDerivedCard,
  // one-derivation selectors, alarm store, value cell, control states (R3)
  linkState, valueCell, alarmGroups, alarmSummary, alarmRowHtml, alarmParamHex,
  procButtonState, setEnabled, sentinelLabel, orbitPoint, updateOverview, renderQuickCommands,
};

if (!globalThis.__MCS_TEST__) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
}
