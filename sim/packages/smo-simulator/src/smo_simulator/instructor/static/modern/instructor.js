/* ============================================================================
 * SMO INSTRUCTOR — modern console page logic (redesign 2026-11)
 * ============================================================================
 * docs/plan_2026-11/INSTRUCTOR_CONSOLE_DESIGN.md. ES module, no build step.
 *
 *   overview strip  <- /api/instructor/views (tiles)            1 s
 *   focus pane      <- focus.js state machine + the views bundle
 *   rail            <- /api/failure-catalog, /api/instructor/fault-menu,
 *                      views.schedule, /api/failures, /api/breakpoints
 *   timeline        <- /api/instructor/timeline?since=<seq>     2 s
 *   app bar, power  <- /api/state (truth params)                 1 s
 *   raw state, clock<- /api/instructor/snapshot                  2 s
 *
 * TRANSPORT RULES (kept from the 2026-08 page):
 *  - Every instructor command goes ONCE via POST /api/command — the
 *    synchronous error surface; a 400/403 body carries the engine's REASON.
 *  - The WebSocket is INBOUND-ONLY (state_update). This module never calls
 *    the WS client's send(). /ws is shared with rfsim and the planner, so no
 *    instructor truth is ever put on it: the truth feeds are polled.
 *  - Event-list timestamps are SIM time.
 * ========================================================================== */

import {
  esc, renderChip, renderEventRow, poller, wsClient, mountLangToggle,
  renderValue, renderNoData, renderBanner, renderTabs, mountTabs,
  setDisabled, setEnabled, armButton,
} from "/static/shared/components.js";
import { fmtUTC, fmtHex } from "/static/shared/format.js";
// UI language (EN|FR) — see docs/i18n/UI_I18N_GUIDE.md.
import { I18n, t, tText, tdb, onLangChange, getLang } from "/static/shared/i18n.js";
// Participant logbook (LOGBOOK_SPEC.md §6): the instructor's own private
// logbook; the worksheet panes only list questions, never anyone's answers.
import { mountLogbook } from "/static/shared/logbook.js";
import * as D from "/static/shared/viz/derive.js";
import * as PF from "/static/shared/viz/powerflow.js";
import { createFocus } from "/static/modern/focus.js";
import { mountTimeline } from "/static/modern/timeline.js";
import * as V from "/static/modern/views.js";
import { createDebrief } from "/static/modern/debrief.js";
import { renderScore } from "/static/modern/score.js";

/* ── constants ─────────────────────────────────────────────────────────── */

const MAX_LOG_ENTRIES = 200;
const PHASE_NAMES = ["PRE_SEPARATION", "SEPARATION_TIMER", "INITIAL_POWER_ON",
                     "BOOTLOADER_OPS", "LEOP", "COMMISSIONING", "NOMINAL"];
// One difficulty scale (BASIC / INTERMEDIATE / ADVANCED / EXPERT, as the
// scenario generator writes it); the legacy BEGINNER reads as BASIC.
// English text is the i18n key
const DIFFICULTY_LABELS = { BASIC: "BASIC", BEGINNER: "BASIC", INTERMEDIATE: "INTERMEDIATE",
                            ADVANCED: "ADVANCED", EXPERT: "EXPERT" };

/* The focus-pane views, in tab order; "|" separates run views from the
 * prep / debrief modes. English labels are i18n keys. */
const VIEWS = [
  { id: "situation", label: "Situation" },
  { id: "divergence", label: "Truth vs trainees" },
  { id: "fault", label: "Fault" },
  { id: "power", label: "Power" },
  { id: "thermal", label: "Thermal" },
  { id: "attitude", label: "Attitude" },
  { id: "orbit", label: "Orbit & link" },
  { id: "obc", label: "OBC & FDIR" },
  { id: "storage", label: "Storage" },
  { id: "raw", label: "Raw state" },
  { id: "|" },
  { id: "prep", label: "Prep" },
  { id: "debrief", label: "Debrief" },
];
// English text is the i18n key (reasons the server gives for a focus switch)
const REASON_KEYS = [
  "ok", "caution", "alarm", "injected", "nodata", "roll", "pitch", "yaw", "gradual", "intermittent", "step",
  "pass override", "Situation", "Truth vs trainees", "Fault", "Power", "Thermal", "Attitude", "Orbit & link",
  "OBC & FDIR", "Storage", "Raw state", "Prep", "Debrief","inject fired", "phase change", "spacecraft mode change", "acquisition of signal",
  "loss of signal", "eclipse entry", "FDIR recovery started", "alarm not acted on",
  "telemetry diverges from truth", "scenario started", "scenario ended", "on-board alarm"];

/* ── state ─────────────────────────────────────────────────────────────── */

let state = null;            // last /api/state (truth summary + raw params)
let snapshot = null;         // last /api/instructor/snapshot
let views = null;            // last /api/instructor/views
let scenarios = [];
let selectedScenario = null;
let activeScenarioName = null;
let scenarioStartSimMs = null;
let debriefWasActive = false;
let frozen = false;
let lastStateOkMs = null;
let failureCatalog = null;
let faultMenu = null;
let currentFailureSpec = null;
let currentFailureSub = null;
let selectedElement = null;
let batch = [];
let breakpoints = [];
let tlItems = [];
let tlSeq = 0;
let tlSeqAtLoad = null;
let tlPending = [];
let tlFaults = [];
let tlSegment = 0;
let tlWindowS = 3600;
let tlSelected = null;
let selectedFault = null;
const sparkHist = {};
const attHist = { point: [], know: [] };
const powerHist = D.createHistory(900);

const focus = createFocus("situation");
let timeline = null;
let powerView = null;
let debrief = null;

const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

/* ── helpers ───────────────────────────────────────────────────────────── */

function stateAgeS() {
  return lastStateOkMs === null ? null : (Date.now() - lastStateOkMs) / 1000;
}
function formatDuration(totalSec) {
  const m = Math.floor(totalSec / 60);
  const s = Math.floor(totalSec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
function difficultyLabel(d) {
  if (!d) return "?";
  const en = DIFFICULTY_LABELS[String(d).toUpperCase()];
  return en ? tText(en) : String(d);
}
/** Display-only clean-up of scenario names (editing leftovers). */
function cleanScenarioName(s) {
  return String(s || "").replace(/\s*\((?:corrected|corrigé)\)\s*$/i, "").replace(/^Sc[ée]nario\s+\d+\s+[—-]\s+/i, "");
}
function simNowMs() {
  if (!state || !state.sim_time) return null;
  const v = Date.parse(state.sim_time);
  return isNaN(v) ? null : v;
}
function simNowTs() { const m = simNowMs(); return m === null ? Date.now() / 1000 : m / 1000; }
/** Current SIM-time-of-day string for log rows. */
function simClock() {
  return state && state.sim_time ? fmtUTC(state.sim_time) : tText("no sim time");
}
function showToast(msg, type) {
  const el = $("toast");
  el.innerHTML = renderBanner(type === "error" ? "alarm" : "ok", msg);
  el.classList.add("show");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.classList.remove("show"), type === "error" ? 6000 : 3000);
}
function setPv(id, html) { const el = $(id); if (el) el.innerHTML = html; }

/* ── API (single command channel: POST /api/command) ───────────────────── */

async function apiGet(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`HTTP ${r.status} on ${path}`);
  return r.json();
}
async function apiPost(path, body) {
  try {
    const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" },
                                  body: JSON.stringify(body) });
    let payload = null;
    try { payload = await r.json(); } catch (e) { payload = null; }
    if (!r.ok) return payload || { status: "error", message: `HTTP ${r.status}` };
    return payload;
  } catch (e) {
    return { status: "error", message: String(e) };
  }
}
/** Send one instructor command, ONCE, over the documented HTTP path. */
function sendCommand(payload) {
  return apiPost("/api/command", payload);
}

/* ── event list (the timeline's text alternative; SIM-time stamps) ─────── */

const SEV_KIND = { 1: "info", 2: "low", 3: "high", 4: "critical" };
function addLog(severity, source, message, utc) {
  const log = $("event-log");
  const holder = document.createElement("div");
  holder.innerHTML = renderEventRow({ severity, source, text: message, utc: utc || simClock() });
  log.appendChild(holder.firstElementChild);
  while (log.children.length > MAX_LOG_ENTRIES) log.removeChild(log.firstChild);
  if (!log.hidden) log.scrollTop = log.scrollHeight;
}

/* ── WebSocket — INBOUND ONLY ──────────────────────────────────────────── */

let wsUp = false;
function setConn(up) {
  wsUp = up;
  $("conn-chip").innerHTML = renderChip(
    up ? { kind: "ok", label: tText("Live feed"), title: tText("WebSocket connected") }
       : { kind: "stale", label: tText("Feed offline"), title: tText("WebSocket disconnected: reconnecting every 3 s") });
}
function startWs() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  // Return value deliberately unused: no command is ever sent on the WS.
  wsClient(`${proto}//${location.host}/ws`, {
    _open: () => setConn(true),
    _close: () => setConn(false),
    state_update: (msg) => { if (msg.state) state = msg.state; },
  });
}

/* ── raw state browser (every parameter has a rendering home; ?sub=) ───── */

let snapshotTabs = [];
let snapshotActiveTab = null;
let snapshotTabsBuilt = false;

/** Normalise a snapshot.parameters key to "0xHHHH". */
function paramHexId(key) {
  if (/^0x/i.test(key)) return key;
  const n = parseInt(key, 10);
  return Number.isFinite(n) ? fmtHex(n, 4) : key;
}
/* Raw parameter banks, named by subsystem (screen review §8: no developer
 * buckets). Unknown banks still get a "0xNNxx" home (completeness). */
const SUB_REGIONS = {
  "00": "SYS·raw", "01": "EPS·raw", "02": "AOCS·raw", "03": "TCS·raw", "04": "OBDH·raw",
  "05": "TTC·raw", "06": "PAYLOAD·raw", "07": "FDIR·raw", "08": "ORBIT·raw",
  "09": "PROC·raw", "0A": "OBDH·raw", "0B": "PROP·raw",
};
const RAW_OWNER = { "EPS·raw": "eps", "AOCS·raw": "aocs", "TCS·raw": "tcs", "OBDH·raw": "obdh",
  "TTC·raw": "ttc", "PAYLOAD·raw": "payload", "PROP·raw": "prop" };

function formatParamValue(v) {
  if (v == null) return tText("no data");
  if (typeof v === "boolean") return v ? "TRUE" : "FALSE";
  if (typeof v === "number") {
    if (!isFinite(v)) return String(v);
    if (Number.isInteger(v)) return String(v);
    const a = Math.abs(v);
    if (a !== 0 && (a < 1e-3 || a >= 1e6)) return v.toExponential(3);
    return v.toFixed(3);
  }
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

function buildSnapshotTabs() {
  const tabsRoot = $("full-snapshot-tabs");
  const body = $("full-snapshot-body");
  if (!tabsRoot || !body || !snapshot) return;
  tabsRoot.innerHTML = "";
  body.innerHTML = "";
  snapshotTabs = [];
  const subTabs = [];
  // 1. one tab per subsystem model (generic: Object.keys, never a list)
  if (snapshot.subsystems && typeof snapshot.subsystems === "object") {
    for (const sub of Object.keys(snapshot.subsystems).sort()) {
      const st = snapshot.subsystems[sub];
      if (st == null || typeof st !== "object") continue;
      const fields = Object.keys(st).sort().map((k) => ({
        key: k, getter: () => (snapshot.subsystems[sub] ? snapshot.subsystems[sub][k] : undefined) }));
      subTabs.push({ id: "sub:" + sub, label: sub.toUpperCase(), sub, fields, cells: new Map() });
    }
  }
  // 2. raw parameters grouped by bank, each placed right after its
  //    subsystem's model tab as its "raw" sub-tab.
  const rawTabs = [];
  if (snapshot.parameters && typeof snapshot.parameters === "object") {
    const groups = {};
    for (const rawId of Object.keys(snapshot.parameters)) {
      const hex = paramHexId(rawId);
      const m = hex.match(/^0x([0-9A-Fa-f]{2})/);
      const region = m ? (SUB_REGIONS[m[1].toUpperCase()] || ("0x" + m[1].toUpperCase() + "xx")) : "OTHER·raw";
      (groups[region] = groups[region] || []).push(rawId);
    }
    for (const region of Object.keys(groups).sort()) {
      const fields = groups[region].sort((a, b) => paramHexId(a).localeCompare(paramHexId(b)))
        .map((rawId) => ({ key: paramHexId(rawId), getter: () => (snapshot.parameters ? snapshot.parameters[rawId] : undefined) }));
      rawTabs.push({ id: "raw:" + region, label: region, raw: true, owner: RAW_OWNER[region], fields, cells: new Map() });
    }
  }
  for (const st of subTabs) {
    snapshotTabs.push(st);
    for (const rt of rawTabs.filter((r) => r.owner === st.sub)) snapshotTabs.push(rt);
  }
  for (const rt of rawTabs.filter((r) => !subTabs.some((s) => s.sub === r.owner))) snapshotTabs.push(rt);

  for (const tab of snapshotTabs) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "snap-tab" + (tab.raw ? " raw" : "");
    btn.dataset.tabId = tab.id;
    btn.innerHTML = `${esc(tab.label)}<span class="count">${tab.fields.length}</span>`;
    btn.addEventListener("click", () => { snapshotActiveTab = tab.id; renderActiveSnapshotTab(); });
    tabsRoot.appendChild(btn);
  }
  const requested = new URLSearchParams(location.search).get("sub");
  if (requested) {
    const want = snapshotTabs.find((x) => x.id === requested || x.id === "sub:" + requested || x.id === "raw:" + requested);
    snapshotActiveTab = want ? want.id : (snapshotTabs.length ? snapshotTabs[0].id : null);
  } else if (snapshotTabs.length) {
    snapshotActiveTab = snapshotTabs[0].id;
  }
  populateSubsystemLauncher();
  renderActiveSnapshotTab();
}

/** Deep-dive launcher: ?sub= COMPOSES with ?ui= and ?lang=. */
function populateSubsystemLauncher() {
  const root = $("subsystem-launcher-buttons");
  if (!root) return;
  const ui = new URLSearchParams(location.search).get("ui");
  const lang = new URLSearchParams(location.search).get("lang");
  root.innerHTML = "";
  for (const tab of snapshotTabs) {
    const a = document.createElement("a");
    const q = new URLSearchParams({ sub: tab.id });
    if (ui) q.set("ui", ui);
    if (lang) q.set("lang", lang);
    a.href = "?" + q.toString();
    a.target = "_blank";
    a.rel = "noopener";
    a.innerHTML = `<span>${esc(tab.label)}</span><span class="ct">${tab.fields.length}</span>`;
    root.appendChild(a);
  }
}
function renderActiveSnapshotTab() {
  const body = $("full-snapshot-body");
  if (!body) return;
  body.innerHTML = "";
  $$("#full-snapshot-tabs .snap-tab").forEach((b) => b.classList.toggle("active", b.dataset.tabId === snapshotActiveTab));
  const tab = snapshotTabs.find((x) => x.id === snapshotActiveTab);
  if (!tab) return;
  tab.cells = new Map();
  const frag = document.createDocumentFragment();
  for (const f of tab.fields) {
    const row = document.createElement("div");
    row.className = "param-cell";
    const k = document.createElement("span"); k.className = "pkey"; k.textContent = f.key;
    const v = document.createElement("span"); v.className = "pval"; v.textContent = formatParamValue(f.getter());
    row.appendChild(k); row.appendChild(v);
    frag.appendChild(row);
    tab.cells.set(f.key, v);
  }
  body.appendChild(frag);
}
function updateActiveSnapshotTab() {
  const tab = snapshotTabs.find((x) => x.id === snapshotActiveTab);
  if (!tab) return;
  for (const f of tab.fields) {
    const cell = tab.cells.get(f.key);
    if (!cell) continue;
    const formatted = formatParamValue(f.getter());
    if (cell.textContent !== formatted) cell.textContent = formatted;
  }
}
function updateCompletenessCounter() {
  if (!snapshot) return;
  let total = 0, populated = 0;
  for (const tb of snapshotTabs) {
    total += tb.fields.length;
    for (const f of tb.fields) { const v = f.getter(); if (v !== undefined && v !== null) populated++; }
  }
  const el = $("param-completeness");
  el.textContent = tText("{{populated}}/{{total}} fields", { populated, total });
  el.title = tText("{{populated}} of {{total}} snapshot fields populated", { populated, total });
  el.classList.toggle("is-caution", total > 0 && populated / total < 0.95);
}
function updateRawSnapshot() {
  const container = $("raw-snapshot-container");
  if (snapshot && container && container.style.display === "block") {
    $("raw-snapshot-json").textContent = JSON.stringify(snapshot, null, 2);
  }
}
function performParameterSearch() {
  const query = $("param-search").value.trim().toLowerCase();
  const results = $("param-search-results");
  if (!query) { results.style.display = "none"; return; }
  if (!snapshot) return;
  const all = [];
  if (snapshot.parameters) {
    for (const [rawId, value] of Object.entries(snapshot.parameters)) {
      const hex = paramHexId(rawId);
      all.push({ id: hex, name: hex, value });
    }
  }
  if (snapshot.subsystems) {
    for (const [subName, subState] of Object.entries(snapshot.subsystems)) {
      if (subState && typeof subState === "object") {
        for (const [key, val] of Object.entries(subState)) all.push({ id: `${subName}.${key}`, name: `${subName}.${key}`, value: val });
      }
    }
  }
  const isHexQuery = query.startsWith("0x");
  const matches = all.filter((p) => (isHexQuery ? p.id.toLowerCase().includes(query)
    : p.name.toLowerCase().includes(query) || String(p.value).toLowerCase().includes(query))).slice(0, 10);
  results.innerHTML = matches.length
    ? matches.map((m) => `<div class="hit"><span class="k">${esc(m.id)}</span><span>${esc(formatParamValue(m.value))}</span></div>`).join("")
    : `<div class="no-data">${t("No parameters found")}</div>`;
  results.style.display = "block";
}

/* ── clock truth (instructor only — never downlinked) ──────────────────── */

const CUC_EPOCH_MS = Date.UTC(2000, 0, 1, 12, 0, 0);   // mission time_epoch
const UINT32_MAX = 4294967295;
function formatClockAge(sec) {
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h > 0 ? `${h}h ${String(m).padStart(2, "0")}m` : `${m}m ${String(s % 60).padStart(2, "0")}s`;
}
function updateClockTruth() {
  const c = (snapshot && snapshot.clock_truth) || null;
  const nd = renderNoData();
  if (!c) {
    ["clock-sim-utc", "clock-obc-utc", "clock-since-sync", "clock-drift", "clock-offset"].forEach((id) => setPv(id, nd));
    setPv("clock-ref", ""); $("clock-offset-note").textContent = "";
    return;
  }
  setPv("clock-ref", c.time_ref_name ? `<span class="ds-id">${esc(c.time_ref_name)}</span>` : "");
  const mono = (txt) => `<span class="ds-value" style="font-size:var(--fs-body)">${esc(txt)}</span>`;
  setPv("clock-sim-utc", c.sim_time ? mono(fmtUTC(c.sim_time, { date: true })) : nd);
  setPv("clock-obc-utc", c.obc_time_s != null ? mono(fmtUTC(new Date(CUC_EPOCH_MS + c.obc_time_s * 1000), { date: true })) : nd);
  setPv("clock-since-sync", c.time_since_sync_s == null || c.time_since_sync_s >= UINT32_MAX
    ? renderNoData({ label: tText("never synced") }) : mono(formatClockAge(c.time_since_sync_s)));
  setPv("clock-drift", c.drift_ppm == null ? nd : renderValue(c.drift_ppm, { units: "ppm", digits: 2 }));
  if (c.offset_s == null) { setPv("clock-offset", nd); $("clock-offset-note").textContent = ""; return; }
  const a = Math.abs(c.offset_s);
  // Lead with the natural scale (days for a never-set clock), the exact
  // seconds underneath — never a bare nine-digit second count.
  setPv("clock-offset", a >= 3600 ? mono(V.fmtOffset(c.offset_s))
    : renderValue(c.offset_s, { units: "s", digits: 3, limits: { yellow_low: -1, yellow_high: 1, red_low: -5, red_high: 5 } }));
  $("clock-offset-note").textContent = a >= 3600 ? tText("exactly {{s}} s", { s: Number(c.offset_s).toFixed(3) }) : "";
}

/* ── scenarios & session (Prep) ────────────────────────────────────────── */

async function loadScenarios() {
  let data = null;
  try { data = await apiGet("/api/scenarios"); } catch (e) { data = null; }
  scenarios = data ? (Array.isArray(data) ? data : (data.scenarios || [])) : [];
  renderScenarios();
}
function scnName(sc) { return cleanScenarioName(sc.id ? tdb(`scn:${sc.id}:name`, sc.name) : sc.name); }
function scnLabel(name) { const sc = scenarios.find((x) => x.name === name); return sc ? scnName(sc) : cleanScenarioName(name); }
function scnBriefing(sc) { return sc.id && sc.briefing ? tdb(`scn:${sc.id}:briefing`, sc.briefing) : sc.briefing; }
function scenarioRunState() { if (!activeScenarioName) return null; return frozen ? "paused" : "running"; }
function runChip(st) {
  return st === "running" ? renderChip({ kind: "active", label: tText("Running") })
    : st === "paused" ? renderChip({ kind: "stale", label: tText("Paused") }) : "";
}
function renderScenarios() {
  const list = $("scenario-list");
  if (!scenarios.length) { list.innerHTML = `<div class="no-data" style="padding:var(--sp-3)">${t("No scenarios available")}</div>`; return; }
  const had = list.contains(document.activeElement) ? document.activeElement.dataset.index : null;
  list.innerHTML = scenarios.map((sc, i) => `
    <button type="button" class="scn" data-index="${i}" aria-pressed="${selectedScenario === i}">
      <span>${esc(scnName(sc))}</span>
      ${activeScenarioName === sc.name ? runChip(scenarioRunState()) : ""}
      <span class="sd"><span>${esc(difficultyLabel(sc.difficulty))}</span><span>${formatDuration(sc.duration_s || 0)}</span></span>
    </button>`).join("");
  list.querySelectorAll(".scn").forEach((el) => el.addEventListener("click", () => selectScenario(parseInt(el.dataset.index, 10))));
  if (had !== null && had !== undefined) { const b = list.querySelector(`[data-index="${had}"]`); if (b) b.focus(); }
}
function updateScenarioButtons() {
  const sc = selectedScenario != null ? scenarios[selectedScenario] : null;
  const start = $("btn-start-scenario"), stop = $("btn-stop-scenario");
  if (!sc) setDisabled(start, tText("Select a scenario first"));
  else if (activeScenarioName === sc.name) setDisabled(start, tText("This scenario is already running"));
  else if (activeScenarioName) setDisabled(start, tText("Stop \"{{name}}\" first", { name: scnLabel(activeScenarioName) }));
  else setEnabled(start);
  if (!activeScenarioName) setDisabled(stop, tText("No scenario is running"));
  else setEnabled(stop);
  const st = scenarioRunState();
  $("scenario-progress").hidden = !st;
  $("progress-state").innerHTML = st ? runChip(st) : "";
  $("progress-track").classList.toggle("paused", st === "paused");
}
function selectScenario(idx) {
  selectedScenario = idx;
  const sc = scenarios[idx];
  if (!sc) return;
  $("scenario-detail").hidden = false;
  $("scenario-briefing").textContent = scnBriefing(sc) || tText("No briefing available.");
  renderScenarios();
  updateScenarioButtons();
  loadPrepWorksheets();
}
async function fetchWorksheets(ctx) {
  try {
    const r = await fetch(`/api/logbook/worksheets?tool=instructor&lang=${getLang()}` +
      `&context=${encodeURIComponent(JSON.stringify(ctx))}`, { credentials: "same-origin" });
    if (!r.ok) return [];
    return (await r.json()).worksheets || [];
  } catch (e) { return []; }
}
function worksheetListHtml(sheets, open) {
  return sheets.map((w, i) => {
    let sec = "";
    const items = w.questions.map((q) => {
      let h = "";
      if (q.section && q.section !== sec) { sec = q.section; h += `<li class="sec">${esc(sec)}</li>`; }
      return h + `<li>${esc(q.text)}</li>`;
    }).join("");
    return `<details class="ds-disclosure"${open && i === 0 ? " open" : ""}><summary>` +
      `<span class="ti"><span class="id">${esc(w.id)}</span> ${esc(w.title)}</span>` +
      `<span class="r">${t("{{n}} questions", { n: w.questions.length })}</span></summary><div class="bd"><ol>${items}</ol></div></details>`;
  }).join("");
}
let prepSeq = 0, debriefWsKey = "";
async function loadPrepWorksheets() {
  const box = $("scenario-prep");
  const sc = selectedScenario != null ? scenarios[selectedScenario] : null;
  const seq = ++prepSeq;
  if (!box || !sc || !sc.id) { if (box) box.innerHTML = ""; return; }
  const sheets = await fetchWorksheets({ scenario: sc.id, phase: "prep" });
  if (seq !== prepSeq) return;
  box.innerHTML = sheets.length
    ? `<div class="ws-h">${t("Prep worksheets")}</div><div class="ws-note">${t("From the course workbook. Participants fill these in their logbook before the pass.")}</div>` + worksheetListHtml(sheets, false)
    : `<div class="ws-note">${t("No prep worksheet for this scenario in the course workbook.")}</div>`;
}
async function loadDebriefWorksheets() {
  const box = $("debrief-ws");
  if (!box) return;
  const sc = scenarios.find((x) => x.name === (lastDebrief && lastDebrief.name)) || (selectedScenario != null ? scenarios[selectedScenario] : null);
  const ctx = { phase: "debrief", ...(sc && sc.id ? { scenario: sc.id } : {}) };
  const key = getLang() + JSON.stringify(ctx);
  if (key === debriefWsKey) return;
  debriefWsKey = key;
  const sheets = await fetchWorksheets(ctx);
  sheets.sort((a, b) => Number(!/-DB$/.test(a.id)) - Number(!/-DB$/.test(b.id)));
  box.innerHTML = sheets.length
    ? `<div class="ws-h">${t("Debrief questions")}</div><div class="ws-note">${t("Use them in the spoken debrief. Participants answer these in their logbook and download it; you never see their answers.")}</div>` + worksheetListHtml(sheets, true)
    : "";
}
async function startScenario() {
  if (selectedScenario == null) return;
  const sc = scenarios[selectedScenario];
  if (!sc) return;
  const res = await sendCommand({ type: "start_scenario", scenario: sc.name });
  if (res && res.status !== "ok") { showToast(tText("Scenario start refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  activeScenarioName = sc.name;
  scenarioStartSimMs = simNowMs();
  updateScenarioButtons();
  showToast(tText("Scenario \"{{name}}\" started", { name: scnName(sc) }), "success");
  renderScenarios();
  goView("situation");
}
async function stopScenario() {
  if (!activeScenarioName) return;
  const res = await sendCommand({ type: "stop_scenario" });
  if (res && res.status !== "ok") { showToast(tText("Stop refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  activeScenarioName = null;
  scenarioStartSimMs = null;
  updateScenarioButtons();
  renderScenarios();
  setTimeout(() => fetchDebrief(true), 1200);
}

/* ── scenario-engine debrief (score panel inside the Debrief view) ─────── */

let lastDebrief;
function renderDebrief(d) {
  lastDebrief = d;
  loadDebriefWorksheets();
  const body = $("debrief-body");
  // Score from the commands the team sent: every expected response with the
  // evidence that met it, or "not seen" (score.js, scenario_scoring.py).
  const name = d ? (d.name ? scnLabel(d.name) : "") : "";
  body.innerHTML = renderScore(d, { nd: renderNoData(), scenarioName: name });
}
async function fetchDebrief(announce) {
  let d = null;
  try { d = await apiGet("/api/scenario/debrief"); } catch (e) { return; }
  const chip = $("scenario-chip");
  if (d.active && d.current) {
    chip.innerHTML = renderChip({ kind: frozen ? "stale" : "active",
      label: frozen ? tText("Paused: {{name}}", { name: scnLabel(d.current) }) : tText("Running: {{name}}", { name: scnLabel(d.current) }),
      title: tText("A training scenario is running") });
    if (activeScenarioName !== d.current) { activeScenarioName = d.current; updateScenarioButtons(); renderScenarios(); }
  } else {
    chip.innerHTML = renderChip({ kind: "neutral", label: tText("No scenario running") });
    if (debriefWasActive && !d.active) {
      announce = true;
      if (activeScenarioName) { activeScenarioName = null; scenarioStartSimMs = null; updateScenarioButtons(); renderScenarios(); }
    }
  }
  debriefWasActive = !!d.active;
  if (d.debrief) { renderDebrief(d.debrief); if (announce) showToast(tText("Scenario debrief available"), "success"); }
  else if (announce) renderDebrief(null);
}

/* ── fault menu by control-loop element + typed form + trigger ─────────── */

/* The failure catalogue's text in the viewer's language. FAILURE_SPECS are
 * English Python; tools/gen_failure_strings.py exports them for the French
 * overlay (i18n.yaml rules failsub / fail / failparam / failval), read here
 * with tdb() like every other config prose. Identifiers stay English. */
function fSubLabel(name) {
  const c = failureCatalog && failureCatalog.subsystems.find((x) => x.name === name);
  return tdb(`failsub:${name}:label`, c ? (c.label || name.toUpperCase()) : name.toUpperCase());
}
function fLabel(sub, f) { return f ? tdb(`fail:${sub}.${f.name}:label`, f.label || f.name) : ""; }
function fText(sub, f, field) { return f && f[field] ? tdb(`fail:${sub}.${f.name}:${field}`, f[field]) : ""; }
function locParam(sub, fail, p) {
  if (!p) return p;
  const k = `${sub}.${fail}.${p.name}`;
  const out = { ...p, label: tdb(`failparam:${k}:label`, p.label || p.name) };
  if (p.description) out.description = tdb(`failparam:${k}:description`, p.description);
  if (Array.isArray(p.values) && Array.isArray(p.value_labels)) {
    out.value_labels = p.values.map((v, i) => tdb(`failval:${k}.${v}:label`, p.value_labels[i]));
  }
  return out;
}

async function loadFailureCatalog() {
  let data = null, menu = null;
  try { [data, menu] = await Promise.all([apiGet("/api/failure-catalog"), apiGet("/api/instructor/fault-menu")]); }
  catch (e) { data = data || null; }
  if (!data || !Array.isArray(data.subsystems)) {
    addLog("high", "FAIL", tText("Failure catalogue unavailable — injection form disabled"));
    $("fail-subsystem").innerHTML = `<option value="">${t("(catalogue unavailable)")}</option>`;
    setDisabled($("btn-inject"), tText("The failure catalogue did not load"));
    setDisabled($("btn-add-batch"), tText("The failure catalogue did not load"));
    return;
  }
  failureCatalog = data;
  faultMenu = menu && Array.isArray(menu.elements) ? menu : null;
  selectedElement = selectedElement || (faultMenu ? (faultMenu.elements.find((e) => e.failures.length) || {}).id : null);
  renderElements();
  updateFailureTypes();
}
function elementEntry() { return faultMenu ? faultMenu.elements.find((e) => e.id === selectedElement) : null; }
function renderElements() {
  if (!faultMenu) { $("elements").innerHTML = ""; return; }
  $("elements").innerHTML = faultMenu.elements.map((e) => `<button type="button" class="el-btn" data-el="${esc(e.id)}"
      aria-pressed="${e.id === selectedElement}"${e.failures.length ? "" : ` aria-disabled="true" data-reason="${esc(tText("No failure of this kind in the catalogue"))}"`}>
      <b>${esc(tText(e.label))}</b><span class="ct">${e.failures.length}</span></button>`).join("");
  const e = elementEntry();
  $("el-hint").textContent = e ? tText(e.hint) : "";
}
function updateSubsystemFilter() {
  const e = elementEntry();
  const subs = e ? [...new Set(e.failures.map((f) => f.subsystem))] : (failureCatalog ? failureCatalog.subsystems.map((s) => s.name) : []);
  const prev = $("fail-subsystem").value;
  const label = (s) => fSubLabel(s);
  $("fail-subsystem").innerHTML = `<option value="">${esc(tText("All subsystems"))}</option>` +
    subs.map((s) => `<option value="${esc(s)}">${esc(label(s))}</option>`).join("");
  if (subs.includes(prev)) $("fail-subsystem").value = prev;
}
function updateFailureTypes() {
  updateSubsystemFilter();
  const e = elementEntry();
  const filt = $("fail-subsystem").value;
  let list = [];
  if (e) list = e.failures.filter((f) => !filt || f.subsystem === filt);
  else if (failureCatalog) {
    for (const s of failureCatalog.subsystems) if (!filt || s.name === filt) for (const f of s.failures) list.push({ subsystem: s.name, name: f.name, label: f.label });
  }
  const prev = $("fail-type").value;
  $("fail-type").innerHTML = list.map((f) => `<option value="${esc(f.subsystem + "|" + f.name)}">${esc(fLabel(f.subsystem, f))} — ${esc(f.subsystem.toUpperCase())}</option>`).join("");
  if (list.some((f) => f.subsystem + "|" + f.name === prev)) $("fail-type").value = prev;
  updateFailureParams();
}
/** One typed control per ParamSpec (bool/enum/int/float/text). */
function renderParamControl(p, idPrefix) {
  const id = `${idPrefix}-${p.name}`;
  const unit = p.unit ? ` <span class="form-unit">${esc(p.unit)}</span>` : "";
  const bits = [];
  if (p.min !== undefined && p.min !== null) bits.push(`min ${p.min}`);
  if (p.max !== undefined && p.max !== null) bits.push(`max ${p.max}`);
  if (p.description) bits.push(esc(p.description));
  const hint = bits.length ? `<span class="form-hint">${bits.join(" · ")}</span>` : "";
  const label = `<label for="${id}">${esc(p.label || p.name)}${unit}${p.required ? " *" : ""}</label>`;
  if (p.type === "bool") {
    return `<div class="ds-field"><label class="ds-check"><input type="checkbox" id="${id}" data-param="${esc(p.name)}" data-ptype="bool"${p.default ? " checked" : ""}> ${esc(p.label || p.name)}</label>${hint}</div>`;
  }
  if (p.type === "enum") {
    const values = p.values || [];
    const labels = p.value_labels || values.map(String);
    const defaults = Array.isArray(p.default) ? p.default.map(String) : (p.default == null ? [] : [String(p.default)]);
    const opts = values.map((v, i) => `<option value="${esc(String(v))}"${defaults.includes(String(v)) ? " selected" : ""}>${esc(String(labels[i]))}</option>`).join("");
    const multi = p.multi ? ` multiple size="4" class="ds-select"` : ` class="ds-select"`;
    return `<div class="ds-field">${label}<select id="${id}" data-param="${esc(p.name)}" data-ptype="enum" data-multi="${p.multi ? "1" : ""}"${multi}>${opts}</select>${hint}</div>`;
  }
  const isNum = (p.type === "int" || p.type === "float");
  const step = p.type === "int" ? 1 : (p.step || "any");
  const attrs = [isNum ? `type="number"` : `type="text"`, isNum ? `step="${step}"` : "",
    (isNum && p.min != null) ? `min="${p.min}"` : "", (isNum && p.max != null) ? `max="${p.max}"` : "",
    (p.default != null) ? `value="${esc(String(p.default))}"` : ""].filter(Boolean).join(" ");
  return `<div class="ds-field">${label}<input class="ds-input" id="${id}" data-param="${esc(p.name)}" data-ptype="${esc(p.type)}" ${attrs}>${hint}</div>`;
}
function currentMenuEntry() {
  const e = elementEntry();
  return e ? e.failures.find((f) => f.subsystem === currentFailureSub && f.name === (currentFailureSpec && currentFailureSpec.name)) : null;
}
function updateFailureParams() {
  const [sub, name] = ($("fail-type").value || "").split("|");
  const entry = failureCatalog ? failureCatalog.subsystems.find((s) => s.name === sub) : null;
  const spec = entry ? entry.failures.find((f) => f.name === name) : null;
  currentFailureSpec = spec || null;
  currentFailureSub = spec ? sub : null;
  setInjectError("");
  const m = currentMenuEntry();
  $("fail-effect").innerHTML = spec ? `${esc(fText(sub, spec, "effect"))}${m ? ` <span class="${m.inject_class === "indication" ? "inj-chip" : "cls-chip"}">${esc(m.inject_class === "indication" ? tText("indication: a sensor lies, the truth is unchanged") : tText("physical"))}</span>` : ""}` : "";
  if (!spec) {
    $("fail-params").innerHTML = "";
    if (!batch.length) setDisabled($("btn-inject"), tText("Choose a failure first"));
    setDisabled($("btn-add-batch"), tText("Choose a failure first"));
    renderReview();
    return;
  }
  setEnabled($("btn-inject")); setEnabled($("btn-add-batch"));
  const html = [];
  if (spec.magnitude) html.push(renderParamControl(locParam(sub, spec.name, spec.magnitude), "fail-mag"));
  (spec.params || []).forEach((p) => html.push(renderParamControl(locParam(sub, spec.name, p), "fail-p")));
  if (!spec.reversible && spec.notes) html.push(`<div class="fail-effect irrev">${t("Not fully reversible: {{notes}}", { notes: fText(sub, spec, "notes") })}</div>`);
  $("fail-params").innerHTML = html.join("");
  renderReview();
}
function setInjectError(msg) {
  const el = $("fail-error");
  el.innerHTML = msg ? renderBanner("alarm", msg) : "";
  el.style.display = msg ? "block" : "none";
}
function readParamControl(p, idPrefix) {
  const el = $(`${idPrefix}-${p.name}`);
  if (!el) return { ok: true, skip: true };
  const where = `${p.label || p.name}`;
  if (p.type === "bool") return { ok: true, value: el.checked };
  if (p.type === "enum") {
    if (p.multi) {
      const vals = Array.from(el.selectedOptions).map((o) => o.value);
      if (!vals.length) return { ok: false, reason: tText("{{where}}: select at least one", { where }) };
      return { ok: true, value: vals };
    }
    if (el.value === "") return { ok: true, skip: true };
    return { ok: true, value: el.value };
  }
  const raw = (el.value || "").trim();
  if (raw === "") return p.required ? { ok: false, reason: tText("{{where}} is required", { where }) } : { ok: true, skip: true };
  if (p.type === "int" || p.type === "float") {
    const n = Number(raw);
    if (!Number.isFinite(n)) return { ok: false, reason: tText("{{where}} must be a number (got \"{{raw}}\")", { where, raw }) };
    if (p.type === "int" && !Number.isInteger(n)) return { ok: false, reason: tText("{{where}} must be a whole number (got {{num}})", { where, num: n }) };
    const u = p.unit ? ` ${p.unit}` : "";
    if (p.min != null && n < p.min) return { ok: false, reason: tText("{{where}} must be >= {{min}}{{u}} (got {{num}}{{u}})", { where, min: p.min, u, num: n }) };
    if (p.max != null && n > p.max) return { ok: false, reason: tText("{{where}} must be <= {{max}}{{u}} (got {{num}}{{u}})", { where, max: p.max, u, num: n }) };
    return { ok: true, value: n };
  }
  return { ok: true, value: raw };
}
function onsetValue() { return document.querySelector("input[name=\"fail-onset\"]:checked").value; }
function updateOnsetDurationVisibility() {
  $("onset-duration-group").style.display = (onsetValue() === "step") ? "none" : "block";
  renderReview();
}
/** Build the failure_inject payload from the form; {ok, payload|reason}. */
function readInjectForm() {
  const spec = currentFailureSpec;
  if (!spec) return { ok: false, reason: tText("No failure selected (catalogue not loaded).") };
  let subsystem = currentFailureSub;
  if (subsystem === "adcs") subsystem = "aocs";
  const onset = onsetValue();
  const payload = { subsystem, failure: spec.name, onset, onset_duration_s: parseInt($("fail-onset-dur").value, 10) || 30 };
  if (spec.magnitude) {
    const r = readParamControl(spec.magnitude, "fail-mag");
    if (!r.ok) return r;
    if (!r.skip) payload.magnitude = r.value;
  }
  for (const p of (spec.params || [])) {
    const r = readParamControl(p, "fail-p");
    if (!r.ok) return r;
    if (!r.skip) payload[p.name] = r.value;
  }
  return { ok: true, payload, label: fLabel(currentFailureSub, spec) };
}
function readTrigger() {
  const kind = $("fail-trigger").value;
  if (kind === "delay") {
    const d = Number($("fail-delay").value);
    if (!Number.isFinite(d) || d < 0) return { ok: false, reason: tText("Delay must be a number of seconds") };
    return { ok: true, trigger: { kind, delay_s: d } };
  }
  if (kind === "tc") {
    const m = ($("fail-tc").value || "").trim().match(/^(\d+)\.(\d+)(?:\.(\d+))?$/);
    if (!m) return { ok: false, reason: tText("Write the telecommand as service.subtype or service.subtype.func, e.g. 8.1.26") };
    return { ok: true, trigger: { kind, service: +m[1], subtype: +m[2], ...(m[3] ? { func_id: +m[3] } : {}) } };
  }
  return { ok: true, trigger: { kind } };
}
function triggerText(tr) {
  if (!tr) return "";
  return {
    now: () => tText("now"), delay: () => tText("in {{s}} s of sim time", { s: tr.delay_s }),
    aos: () => tText("at the next AOS"), los: () => tText("at the next LOS"),
    eclipse_entry: () => tText("at eclipse entry"), eclipse_exit: () => tText("at eclipse exit"),
    tc: () => tText("when TC {{s}}.{{t}}{{f}} is received", { s: tr.service, t: tr.subtype, f: tr.func_id != null ? "." + tr.func_id : "" }),
  }[tr.kind]();
}
function describeInject(p) {
  return Object.keys(p).filter((k) => !["subsystem", "failure", "onset", "onset_duration_s"].includes(k))
    .map((k) => `${k}=${JSON.stringify(p[k])}`).join(" ");
}
/** The confirm step: target, severity, ramp and trigger, always visible. */
function renderReview() {
  const f = readInjectForm();
  const tr = readTrigger();
  const snap = $("fail-snapshot").checked;
  const rows = [];
  if (batch.length) rows.push([tText("Batch"), batch.map((b) => `${b.subsystem}/${b.failure}`).join(", ")]);
  if (f.ok) {
    rows.push([tText("Target"), `${f.payload.subsystem.toUpperCase()} / ${f.payload.failure}`]);
    rows.push([tText("Severity"), describeInject(f.payload) || tText("as catalogued")]);
    rows.push([tText("Onset"), f.payload.onset === "step" ? tText("step (immediate)") : `${tText(f.payload.onset)} · ${f.payload.onset_duration_s} s`]);
  }
  rows.push([tText("When"), tr.ok ? triggerText(tr.trigger) : tr.reason]);
  rows.push([tText("Snapshot before"), snap ? tText("yes (kept in memory, newest six)") : tText("no")]);
  $("inject-review").innerHTML = `<dl>${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>`;
  $("batch-list").innerHTML = batch.length ? batch.map((b, i) => `<div class="item fail"><span class="fname">${esc(`${b.subsystem}/${b.failure}`)}</span>
      <button type="button" class="ds-btn sm ghost" data-act="unbatch" data-i="${i}" aria-label="${esc(tText("Remove {{what}} from the batch", { what: `${b.subsystem}/${b.failure}` }))}">${t("Remove")}</button>
      <div class="fmeta"><span>${esc(describeInject(b))}</span></div></div>`).join("") : "";
  const btn = $("btn-inject");
  const want = batch.length ? tText("Inject batch ({{n}})", { n: batch.length }) : tText("Inject");
  // armButton keeps the label it was bound with: re-bind when it changes
  if (!btn.classList.contains("is-armed") && btn.textContent.trim() !== want) {
    btn.textContent = want;
    armInject();
  }
}
function addToBatch() {
  const f = readInjectForm();
  if (!f.ok) { setInjectError(f.reason); return; }
  if (batch.length >= 8) { setInjectError(tText("At most 8 faults fire together")); return; }
  batch.push(f.payload);
  setInjectError("");
  setEnabled($("btn-inject"));
  renderReview();
}
async function injectFailure() {
  const tr = readTrigger();
  if (!tr.ok) { setInjectError(tr.reason); return; }
  const snap = $("fail-snapshot").checked;
  let injects = batch.slice();
  if (!injects.length) {
    const f = readInjectForm();
    if (!f.ok) { setInjectError(f.reason); return; }
    injects = [f.payload];
  }
  setInjectError("");
  let res;
  if (injects.length === 1 && tr.trigger.kind === "now") {
    // The established command (scenario generator, tests): failure_inject.
    res = await sendCommand({ type: "failure_inject", ...injects[0], snapshot_before: snap });
  } else {
    res = await sendCommand({ type: "failure_schedule", injects, trigger: tr.trigger, snapshot_before: snap });
  }
  if (res && res.status !== "ok") {
    setInjectError(tText("Rejected: {{reason}}", { reason: res.message || tText("unknown reason") }));
    showToast(tText("Injection rejected — see the reason above"), "error");
    return;
  }
  const what = injects.map((i) => `${i.subsystem}/${i.failure}`).join(", ");
  showToast(tr.trigger.kind === "now" ? tText("Failure injected: {{what}}", { what }) : tText("Scheduled: {{what}} {{when}}", { what, when: triggerText(tr.trigger) }), "success");
  batch = [];
  renderReview();
  failuresPoll.kick(); viewsPoll.kick(); timelinePoll.kick();
  setTimeout(refreshBreakpoints, 1500);
}

/* ── scheduled + active failures ───────────────────────────────────────── */

function renderSchedule(list) {
  const box = $("schedule-list");
  const n = (list || []).length;
  $("schedule-count").innerHTML = n ? `<span class="inj-chip">${esc(tText("{{n}} pending", { n }))}</span>` : "";
  if (!n) { box.innerHTML = `<div class="no-data" style="padding:var(--sp-2) var(--sp-4)">${t("Nothing scheduled")}</div>`; return; }
  box.innerHTML = list.map((e) => `<div class="item fail"><span class="fname">${esc(e.injects.map((i) => `${i.subsystem}/${i.failure}`).join(", "))}</span>
    <button type="button" class="ds-btn sm" data-act="cancel-schedule" data-id="${esc(e.id)}" aria-label="${esc(tText("Cancel scheduled inject {{id}}", { id: e.id }))}">${t("Cancel")}</button>
    <div class="fmeta"><span>${esc(e.id)}</span><span>${esc(triggerText(e.trigger))}</span>${e.due_ts ? `<span>${esc(V.fmtClockSec(e.due_ts))}</span>` : ""}${e.snapshot_before ? `<span>${t("snapshot")}</span>` : ""}</div></div>`).join("");
}
async function cancelSchedule(id) {
  const res = await sendCommand({ type: "schedule_cancel", schedule_id: id });
  if (res && res.status !== "ok") { showToast(tText("Cancel refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  viewsPoll.kick(); timelinePoll.kick();
}
let lastFailures = [];
function renderFailures(failures) {
  lastFailures = failures || [];
  const list = $("failures-list");
  const n = lastFailures.length;
  $("failures-count").innerHTML = n ? `<span class="inj-chip">${esc(tText("{{n}} injected", { n }))}</span>` : "";
  if (n) setEnabled($("btn-clear-all")); else setDisabled($("btn-clear-all"), tText("No failures are active"));
  if (list.querySelector(".is-armed")) return;
  if (!n) { list.innerHTML = `<div class="no-data" style="padding:var(--sp-2) var(--sp-4)">${t("No active failures")}</div>`; return; }
  list.innerHTML = lastFailures.map((f) => {
    const id = f.failure_id || f.id || `${f.subsystem}_${f.failure}`;
    const magPct = ((f.magnitude || 0) * 100).toFixed(0);
    const elapsed = f.elapsed_s ? formatDuration(f.elapsed_s) : "00:00";
    const what = `${(f.subsystem || "").toUpperCase()} / ${f.failure || f.type || ""}`;
    return `<div class="item fail" data-id="${esc(id)}"><span class="fname" title="${esc(what)}">${esc(what)}</span>
        <button type="button" class="ds-btn sm" data-act="clear-failure" data-id="${esc(id)}" aria-label="${esc(tText("Clear failure {{what}}", { what }))}">${t("Clear")}</button>
        <div class="fmeta"><span>${t("magnitude {{pct}} %", { pct: magPct })}</span><span>${elapsed}</span></div></div>`;
  }).join("");
}
async function clearFailure(id) {
  const res = await sendCommand({ type: "failure_clear", failure_id: id });
  if (res && res.status !== "ok") { showToast(tText("Clear refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  failuresPoll.kick();
}
async function clearAllFailures() {
  const res = await sendCommand({ type: "failure_clear_all" });
  if (res && res.status !== "ok") { showToast(tText("Clear-all refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  showToast(tText("All failures cleared"), "success");
  failuresPoll.kick();
}

/* ── phase, overrides, marks ───────────────────────────────────────────── */

async function setSpacecraftPhase() {
  const phase = parseInt($("phase-select").value, 10);
  if (!Number.isInteger(phase) || phase < 0 || phase > 6) { showToast(tText("Phase must be 0-6"), "error"); return; }
  const res = await sendCommand({ type: "set_phase", phase });
  if (res && res.status !== "ok") { showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  showToast(tText("Phase set: {{phase}} {{name}}", { phase, name: PHASE_NAMES[phase] }), "success");
}
async function startSeparation() {
  const res = await sendCommand({ type: "start_separation" });
  if (res && res.status !== "ok") { showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  showToast(tText("Separation sequence started"), "success");
}
async function toggleOverride() {
  const newState = !(state && state.override_passes);
  const res = await sendCommand({ type: "override_passes", enabled: newState });
  if (res && res.status !== "ok") { showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  statePoll.kick();
}
async function setBatterySoc() {
  const soc = parseFloat($("soc-override-input").value);
  if (!isFinite(soc) || soc < 0 || soc > 100) { showToast(tText("Battery SoC override must be 0-100 %"), "error"); return; }
  const res = await sendCommand({ type: "set_battery_soc", soc_pct: soc });
  if (res && res.status !== "ok") { showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  showToast(tText("Battery SoC set to {{soc}} %", { soc }), "success");
}
async function mark(kind, disposition) {
  const text = $("mark-text").value.trim();
  const res = await sendCommand({ type: "timeline_mark", kind, text, ...(disposition ? { disposition } : {}) });
  if (res && res.status !== "ok") { showToast(tText("Mark refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  $("mark-text").value = "";
  showToast(kind === "anomaly" && disposition === "restart"
    ? tText("Marked. To restart, load a snapshot from the Snapshots list.") : tText("Marked on the timeline"), "success");
  timelinePoll.kick();
}

/* ── time control ──────────────────────────────────────────────────────── */

async function setSpeed(speed) {
  const res = await sendCommand({ type: "set_speed", value: speed });
  if (res && res.status !== "ok") { showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  if (state) state.speed = speed;
  renderTimeControl();
  statePoll.kick();
}
async function toggleFreeze() {
  const next = !frozen;
  const res = await sendCommand({ type: next ? "freeze" : "resume" });
  if (res && res.status !== "ok") { showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error"); return; }
  frozen = next;
  if (state) state.speed = next ? 0 : Math.max(1, state.speed || 0);
  renderTimeControl();
  statePoll.kick();
}
function renderTimeControl() {
  const speed = state && state.speed != null ? Number(state.speed) : null;
  const was = frozen;
  frozen = speed === 0;
  if (was !== frozen && scenarios.length) renderScenarios();
  $("run-chip").innerHTML = speed === null ? renderChip({ kind: "nodata", label: tText("no data") })
    : frozen ? renderChip({ kind: "warn", label: tText("Frozen"), title: tText("Simulation time is stopped") })
      : renderChip({ kind: "active", label: tText("Running ×{{s}}", { s: speed }),
        title: speed > 1 ? tText("Accelerated: physics is sub-stepped; housekeeping, pacing and the planner see the same accelerated time") : "" });
  $$("#speed-group button[data-speed]").forEach((b) => b.setAttribute("aria-pressed", String(!frozen && parseFloat(b.dataset.speed) === speed)));
  const btn = $("freeze-btn");
  btn.textContent = frozen ? tText("Resume") : tText("Freeze");
  btn.classList.toggle("primary", frozen);
  btn.title = frozen ? tText("Resume the simulation at ×1") : tText("Stop simulation time for everyone");
}

/* ── session label (published to the ground in the state feed) ────────── */

let sessionLabelSeeded = false;
function publishedLabel() { return state && typeof state.session_label === "string" ? state.session_label : null; }
function renderSessionLabel() {
  const cur = publishedLabel();
  const el = $("session-label-now");
  if (!el) return;
  el.textContent = cur === null ? tText("Published label: no data from the simulator")
    : cur ? tText("Published: {{label}}", { label: cur }) : tText("Nothing published: the consoles leave it blank.");
  if (!sessionLabelSeeded && cur !== null) { sessionLabelSeeded = true; if (!$("session-label").value) $("session-label").value = cur; }
  updateSessionLabelBtn();
}
function updateSessionLabelBtn() {
  const btn = $("btn-session-label");
  const v = $("session-label").value.trim().replace(/\s+/g, " ");
  const cur = publishedLabel();
  if (cur !== null && v === cur) setDisabled(btn, v ? tText("Already published") : tText("Type a label first"));
  else setEnabled(btn);
  btn.textContent = !v && cur ? tText("Clear") : tText("Publish");
}
async function publishSessionLabel() {
  if ($("btn-session-label").getAttribute("aria-disabled") === "true") return;
  const label = $("session-label").value.trim().replace(/\s+/g, " ");
  const res = await sendCommand({ type: "set_session_label", label });
  if (!res || res.status !== "ok") { showToast(tText("Label not published: {{reason}}", { reason: (res && res.message) || tText("unknown") }), "error"); return; }
  showToast(label ? tText("Published to the consoles") : tText("Session label cleared"), "success");
  setTimeout(() => statePoll.kick(), 600);
}

/* ── snapshots (breakpoints) ───────────────────────────────────────────── */

async function saveBreakpoint(nameIn) {
  const name = (nameIn || $("breakpoint-name").value).trim();
  if (!name) return;
  if (!nameIn) { $("breakpoint-name").value = ""; updateBpSave(); }
  const res = await apiPost("/api/breakpoint/save", { name });
  if (res && res.status !== "saved") { showToast(tText("Snapshot save failed: {{reason}}", { reason: res.error || res.message || tText("unknown") }), "error"); return; }
  showToast(tText("Snapshot \"{{name}}\" saved", { name }), "success");
  setTimeout(refreshBreakpoints, 600);
}
async function refreshBreakpoints() {
  let data = null;
  try { data = await apiGet("/api/breakpoints"); } catch (e) { return; }
  if (!Array.isArray(data)) return;
  breakpoints = data.map((b) => ({ name: b.name, auto: !!b.auto, tick: b.tick != null ? b.tick : (b.tick_count != null ? b.tick_count : 0), time: b.sim_time || null,
    fault: b.fault || "", onDisk: !!b.on_disk, bytes: b.bytes, previous: !!b.previous_process, note: b.note || "" }));
  breakpoints.sort((a, b) => String(b.time || "").localeCompare(String(a.time || "")));
  renderBreakpoints();
}
function renderBreakpoints() {
  const list = $("breakpoints-list");
  if (list.querySelector(".is-armed")) return;
  if (!breakpoints.length) { list.innerHTML = `<div class="no-data" style="padding:0 var(--sp-4) var(--sp-3)">${t("No snapshots saved")}</div>`; return; }
  // Auto snapshots (taken just before each injected fault) are kept on disk
  // too, so they survive a restart: "restore" puts the team back before it.
  const autoLine = (bp) => [
    bp.onDisk ? tText("on disk{{size}}", { size: bp.bytes ? ` (${Math.max(1, Math.round(bp.bytes / 1024))} kB)` : "" }) : tText("in memory only"),
    bp.previous ? tText("from before the restart") : "", bp.note || ""].filter(Boolean).join(" · ");
  list.innerHTML = breakpoints.map((bp) => `<div class="item">
      <span class="fname">${esc(bp.auto && bp.fault ? tText("Before {{fault}}", { fault: bp.fault }) : bp.name)}</span>
      <button type="button" class="ds-btn critical sm" data-name="${esc(bp.name)}" aria-label="${esc(bp.auto ? tText("Restore snapshot {{name}}", { name: bp.name }) : tText("Load snapshot {{name}}", { name: bp.name }))}">${bp.auto ? t("Restore") : t("Load")}</button>
      <div class="fmeta">${bp.auto ? `<span class="inj-chip">${t("auto")}</span>` : ""}<span>${bp.time ? fmtUTC(bp.time, { date: true }) : ""}</span></div>
      ${bp.auto ? `<div class="fmeta dim">${esc(autoLine(bp))}</div>` : ""}</div>`).join("");
  list.querySelectorAll("button[data-name]").forEach((b) => armButton(b, { onExecute: () => loadBreakpoint(b.dataset.name) }));
}
function updateBpSave() {
  if ($("breakpoint-name").value.trim()) setEnabled($("btn-save-bp"));
  else setDisabled($("btn-save-bp"), tText("Enter a snapshot name first"));
}
async function loadBreakpoint(name) {
  const res = await apiPost("/api/breakpoint/load", { name });
  if (res && res.status !== "loaded") { showToast(tText("Snapshot load failed: {{reason}}", { reason: res.error || res.message || tText("unknown") }), "error"); return; }
  showToast(tText("Snapshot \"{{name}}\" loaded", { name }), "success");
  timelinePoll.kick();
}

/* ── focus pane ────────────────────────────────────────────────────────── */

function viewLabel(id) { const v = VIEWS.find((x) => x.id === id); return v ? tText(v.label) : id; }
function renderTabsBar() {
  const fs = focus.state();
  const tabs = VIEWS.filter((v) => v.id !== "|").map((v) => ({ id: v.id, label: tText(v.label) }));
  const html = renderTabs(tabs, fs.view, { label: tText("Focus views"), panel: "focus-body" });
  const host = $("focus-tabs");
  host.innerHTML = html;
  const list = host.querySelector('[role="tablist"]');
  // a hairline between the run views and Prep / Debrief
  const prep = host.querySelector('[data-tab="prep"]');
  if (prep) prep.insertAdjacentHTML("beforebegin", '<span class="sep" aria-hidden="true"></span>');
  if (list && !list.__wired) { list.__wired = true; mountTabs(list, (id) => goView(id, true)); }
  $("view-select").innerHTML = tabs.map((tb) => `<option value="${esc(tb.id)}"${tb.id === fs.view ? " selected" : ""}>${esc(tb.label)}</option>`).join("");
}
function renderFocusHead() {
  const fs = focus.state();
  $("focus-title").textContent = viewLabel(fs.view);
  const r = fs.reason;
  $("focus-reason").innerHTML = r
    ? `<span class="auto">${esc(tText("auto"))}</span> · ${esc(tText("because {{reason}}: {{subject}} at {{time}}", {
        reason: tText(r.reason || ""), subject: r.subject || "", time: V.fmtClockSec(r.ts) }))}`
    : esc(fs.pinned ? tText("pinned") : !fs.auto ? tText("auto-follow off") : tText("chosen by you"));
  const sg = fs.suggestion;
  $("focus-suggest").innerHTML = sg ? `${esc(tText("Suggested: {{view}} — {{reason}}", { view: viewLabel(sg.view), reason: tText(sg.reason || "") }))}
    <button type="button" class="ds-btn sm primary" id="btn-suggest-go">${t("Go")}</button>
    <button type="button" class="ds-btn sm ghost" id="btn-suggest-x" aria-label="${esc(tText("Dismiss the suggestion"))}">×</button>` : "";
  const back = $("btn-focus-back");
  if (fs.canBack) { setEnabled(back); back.title = tText("Back to {{view}}", { view: viewLabel(fs.backView) }); }
  else setDisabled(back, tText("No previous view"));
  $("btn-focus-pin").setAttribute("aria-pressed", String(fs.pinned));
  $("btn-focus-pin").textContent = fs.pinned ? tText("Pinned") : tText("Pin");
  $("focus-auto").checked = fs.auto;
}
function showView() {
  const fs = focus.state();
  $$(".view").forEach((v) => { v.hidden = v.id !== "view-" + fs.view; });
  $$("#focus-tabs [role=tab]").forEach((b) => { const s = b.dataset.tab === fs.view; b.setAttribute("aria-selected", String(s)); b.tabIndex = s ? 0 : -1; });
  if ($("view-select").value !== fs.view) $("view-select").value = fs.view;
  $$("#overview .tile[data-view]").forEach((b) => b.classList.toggle("is-focus", b.dataset.view === fs.view));
  renderFocusHead();
  renderActiveView();
  if (fs.view === "debrief" && debrief) debrief.refresh();
  if (fs.view === "raw" || fs.view === "obc") snapshotPoll.kick();
}
function goView(id, manual) {
  if (manual) focus.select(id, Date.now());
  else focus.select(id, Date.now());
  showView();
}
function applyFocusResult(res) {
  if (res && (res.action === "switch" || res.action === "accept")) {
    showView();
    addLog("info", "FOCUS", tText("Focus → {{view}} ({{reason}})", { view: viewLabel(res.view), reason: tText((focus.state().reason || {}).reason || "") }));
  } else if (res && (res.action === "suggest" || res.action === "queued")) {
    renderFocusHead();
  }
}

/* keep <details> open state and scroll across re-renders */
function swapHtml(el, html) {
  const open = [...el.querySelectorAll("details")].map((d) => d.open);
  el.innerHTML = html;
  [...el.querySelectorAll("details")].forEach((d, i) => { if (open[i] !== undefined) d.open = open[i]; });
}

function situationHtml() {
  const nowTs = simNowTs();
  const active = tlFaults.filter((f) => f.seg === tlSegment && f.cleared_ts == null);
  const cleared = tlFaults.filter((f) => f.seg === tlSegment && f.cleared_ts != null).slice(-4);
  const card = (f) => {
    const stage = [...V.STAGES].reverse().find((s) => f[s.k] != null);
    return `<button type="button" class="fcard${f.cleared_ts ? " cleared" : ""}" data-fault="${esc(f.fault_id)}">
      <span class="ft"><span>${esc(`${f.subsystem.toUpperCase()} / ${f.failure}`)}</span><span class="dim">T+${esc(V.fmtAge(nowTs - f.inserted_ts))}</span></span>
      <span class="st">${esc(tText(f.inject_class === "indication" ? "indication (sensor lie)" : "physical"))} · ${esc(tText((faultMenu && (faultMenu.elements.find((e) => e.id === f.element) || {}).label) || f.element))}</span>
      <span class="st">${esc(tText("Latest: {{stage}}", { stage: stage ? tText(stage.label) : "" }))}</span></button>`;
  };
  const div = views && views.divergence ? views.divergence.summary : null;
  const pend = tlPending.slice().sort((a, b) => (a.ts ?? 9e12) - (b.ts ?? 9e12)).slice(0, 8);
  const noScenario = !activeScenarioName;
  return `<div class="sit"><div>
      ${noScenario ? `<p class="lede">${t("No scenario is running. Choose one in Prep, or inject faults by hand in free run.")} <button type="button" class="ds-btn sm" data-goview="prep">${t("Open Prep")}</button></p>` : ""}
      <h3>${t("Active injects")}</h3>
      ${active.length ? `<div class="fault-cards">${active.map(card).join("")}</div>` : `<div class="no-data">${t("No inject is active.")}</div>`}
      ${cleared.length ? `<h3>${t("Recently cleared")}</h3><div class="fault-cards">${cleared.map(card).join("")}</div>` : ""}
      <h3>${t("Coming up")}</h3>
      ${pend.length ? `<ul class="plain">${pend.map((p) => `<li><span class="mono dim">${p.ts ? esc(V.fmtClockSec(p.ts)) : esc(tText("gate"))}</span> ${p.source === "scenario" ? esc(tText("scenario")) + ": " : ""}${esc(p.text)}${p.gate ? ` <span class="why">${esc(p.gate)}</span>` : ""}</li>`).join("")}</ul>`
        : `<div class="no-data">${t("Nothing scheduled by you or the scenario.")}</div>`}
    </div><div class="side">
      <h3>${t("Truth vs trainees")}</h3>
      ${div ? `<div class="kv"><span>${t("Injected indication faults")}</span><span class="cause cause-injected">${div.by_cause.injected}</span></div>
        <div class="kv"><span>${t("Spacecraft estimate or clock off")}</span><span class="cause cause-estimator">${div.by_cause.estimator}</span></div>
        <div class="kv"><span>${t("Ground does not have it yet")}</span><span class="cause cause-delay">${div.by_cause.delay}</span></div>
        <button type="button" class="ds-btn sm" data-goview="divergence" style="margin-top:var(--sp-2)">${t("Open the comparison")}</button>` : V.num(null)}
      <h3>${t("Team activity the simulator can see")}</h3>
      ${teamActivityHtml(nowTs)}
      <p class="note">${t("Alarm acknowledgements, procedure steps and voice loops happen on the ground and are not visible to the simulator.")}</p>
    </div></div>`;
}
function teamActivityHtml(nowTs) {
  const seg = tlItems.filter((i) => i.seg === tlSegment);
  const tcs = seg.filter((i) => i.kind === "tc_rx");
  const last10 = tcs.filter((i) => nowTs - i.ts <= 600).length;
  const rej = seg.filter((i) => i.lane === "tc" && (i.kind === "tc_rej" || i.kind === "tc_fail" || i.kind === "tc_link") && nowTs - i.ts <= 600).length;
  const lastTc = tcs.length ? tcs[tcs.length - 1] : null;
  const missed = seg.filter((i) => i.kind === "missed_cue").length;
  return `<div class="kv"><span>${t("Telecommands, last 10 min")}</span><span class="mono">${last10}</span></div>
    <div class="kv"><span>${t("Rejected, last 10 min")}</span><span class="mono">${rej}</span></div>
    <div class="kv"><span>${t("Last telecommand")}</span>${lastTc ? `<span class="mono">${esc(tText("{{age}} ago", { age: V.fmtAge(nowTs - lastTc.ts) }))}</span>` : `<span class="dim">${t("none")}</span>`}</div>
    <div class="kv"><span>${t("Alarms not acted on")}</span><span class="mono">${missed}</span></div>`;
}
function rowsFor(sub) { return views && views.divergence ? views.divergence.rows.filter((r) => r.subsystem === sub) : []; }

function renderActiveView() {
  const fs = focus.state();
  const nowTs = simNowTs();
  const el = $("view-" + fs.view);
  if (!el) return;
  switch (fs.view) {
    case "situation": swapHtml(el, situationHtml()); break;
    case "divergence": swapHtml(el, views ? V.renderDivergence(views.divergence) : V.num(null)); break;
    case "fault": {
      const f = tlFaults.find((x) => x.fault_id === selectedFault) || tlFaults.filter((x) => x.seg === tlSegment).slice(-1)[0];
      if (f && faultMenu) f.element_label = (faultMenu.elements.find((e) => e.id === f.element) || {}).label;
      const others = tlFaults.filter((x) => x.seg === tlSegment && (!f || x.fault_id !== f.fault_id));
      swapHtml(el, V.renderFault(f, nowTs) + (others.length ? `<h3>${t("Other injects in this run")}</h3><div class="fault-cards">${others.map((x) =>
        `<button type="button" class="fcard${x.cleared_ts ? " cleared" : ""}" data-fault="${esc(x.fault_id)}"><span class="ft">${esc(`${x.subsystem.toUpperCase()} / ${x.failure}`)}</span></button>`).join("")}</div>` : ""));
      break;
    }
    case "power": renderPowerSide(); break;
    case "thermal": swapHtml(el, views ? V.renderThermal(views.thermal) + V.pairTable(rowsFor("tcs")) : ""); break;
    case "attitude": swapHtml(el, views ? V.renderAttitude(views.attitude, attHist) + V.pairTable(rowsFor("aocs")) : ""); break;
    case "orbit": swapHtml(el, views ? V.renderOrbit(views.orbit, nowTs) : ""); break;
    case "obc": swapHtml($("obc-main"), views ? V.renderObc(views.obc, rowsFor("obdh")) : ""); break;
    case "storage": swapHtml(el, views ? V.renderStorage(views.storage) + V.pairTable(rowsFor("payload")) : ""); break;
    default: break;
  }
}

/* power flow: the shared powerflow.js fed with the simulator's own values */
function truthSource() {
  const p = (state && state.params) || {};
  const hexv = {};
  for (const [k, v] of Object.entries(p)) {
    const n = parseInt(k, 10);
    if (Number.isFinite(n)) hexv["0x" + n.toString(16).toUpperCase().padStart(4, "0")] = v;
  }
  return {
    state: state || {}, limits: {},
    get(hex) {
      const v = hexv[hex];
      return D.qty(Number.isFinite(Number(v)) && v !== null ? Number(v) : null, "", { verdict: v == null ? "nodata" : "fresh", src: `sim ${hex}` });
    },
  };
}
function renderPower() {
  if (!state || focus.state().view !== "power") return;
  if (!powerView) powerView = PF.mount($("powerflow"), { t: tText, variant: "full" });
  const src = truthSource();
  powerHist.push(simNowTs(), { gen: src.get("0x0107").v });
  try { powerView.update(D.derivePower(src, { history: powerHist })); } catch (e) { /* model mid-boot */ }
}
function renderPowerSide() {
  const pw = views && views.power;
  if (!pw || !pw.available) { $("power-side").innerHTML = ""; return; }
  const trips = Object.entries(pw.oc_trips || {}).filter(([, v]) => v).map(([k]) => k);
  $("power-side").innerHTML = `<h3 style="margin-top:0">${t("Model truth")}</h3>
    <div class="kv"><span>${t("State of charge")}</span>${V.num(pw.soc, 1, "%")}</div>
    <div class="kv"><span>${t("Bus voltage")}</span>${V.num(pw.bus_v, 2, "V")}</div>
    <div class="kv"><span>${t("Generated / consumed")}</span><span class="mono">${esc(`${(pw.p_gen ?? 0).toFixed(1)} / ${(pw.p_cons ?? 0).toFixed(1)} W`)}</span></div>
    <div class="kv"><span>${t("Battery current (+ charging)")}</span>${V.num(pw.bat_current, 2, "A")}</div>
    <div class="kv"><span>${t("Sun fraction")}</span>${V.num(pw.sun_fraction, 2, "")}</div>
    <div class="kv"><span>${t("Array output factor A / B")}</span><span class="mono">${esc((pw.sa_degradation || []).map((v) => v == null ? "?" : (v * 100).toFixed(0) + " %").join(" / "))}</span></div>
    <div class="kv"><span>${t("Load-shed stage")}</span><span class="mono">${esc(String(pw.shed_stage))}</span></div>
    <div class="kv"><span>${t("Overcurrent trips")}</span>${trips.length ? `<span class="mono">${esc(trips.join(", "))}</span>` : `<span class="dim">${t("none")}</span>`}</div>`;
  swapHtml($("power-pairs"), V.pairTable(rowsFor("eps")));
}

/* ── overview strip ────────────────────────────────────────────────────── */

function renderOverview() {
  if (!views || !views.overview) return;
  for (const tl of views.overview.tiles) {
    const a = (sparkHist[tl.id] = sparkHist[tl.id] || []);
    a.push(tl.value == null ? NaN : Number(tl.value));
    while (a.length > 120) a.shift();
  }
  $("overview").innerHTML = V.renderTiles(views.overview, sparkHist, focus.state().view);
}

/* ── timeline ──────────────────────────────────────────────────────────── */

function renderTimeline() {
  if (!timeline) return;
  timeline.update({ items: tlItems, pending: tlPending, nowTs: simNowTs(), windowS: tlWindowS,
                    futureFrac: 0.2, segment: tlSegment, selectedSeq: tlSelected });
}
function ingestTimeline(d) {
  if (!d || !Array.isArray(d.items)) return;
  const first = tlSeqAtLoad === null;
  if (first) tlSeqAtLoad = d.seq;
  for (const it of d.items) {
    tlItems.push(it);
    if (it.lane !== "link" || it.kind === "aos" || it.kind === "los") {
      if (it.kind !== "ev_down" || it.sev >= 3) {
        addLog(SEV_KIND[it.sev] || "info", it.lane.toUpperCase(), it.text, V.fmtClockSec(it.ts));
      }
    }
    if (!first && it.focus && it.seq > tlSeqAtLoad) {
      if (it.lane === "fault" && it.kind === "inject") selectedFault = it.ref;
      applyFocusResult(focus.offer({ view: it.focus.view, prio: it.focus.prio, reason: it.focus.reason,
        subject: it.text, ts: it.ts, seq: it.seq }, Date.now()));
    }
  }
  if (tlItems.length > 6000) tlItems = tlItems.slice(-6000);
  tlSeq = d.seq;
  tlPending = d.pending || [];
  tlFaults = d.faults || [];
  if (d.segment !== tlSegment) { tlSegment = d.segment; }
  renderTimeline();
}
function showTimelineDetail(seq) {
  tlSelected = seq;
  const it = tlItems.find((i) => i.seq === seq);
  $("tl-detail").textContent = it ? `${V.fmtClockSec(it.ts)} · ${tText((timelineLaneLabel(it.lane)))} · ${it.text}` : "";
  if (it && it.lane === "fault" && it.ref && tlFaults.some((f) => f.fault_id === it.ref)) { selectedFault = it.ref; goView("fault", true); }
  renderTimeline();
}
function timelineLaneLabel(id) {
  return ({ phase: "Phase & modes", fault: "Injects", alarm: "On-board alarms", tc: "Telecommands", proc: "Procedures",
    link: "Link & sun", instr: "Instructor", voice: "Voice loops" })[id] || id;
}

/* ── polling ───────────────────────────────────────────────────────────── */

const statePoll = poller(async () => {
  try {
    state = await apiGet("/api/state");
    lastStateOkMs = Date.now();
  } finally {
    renderAppBar();
    renderSessionLabel();
    renderPower();
  }
}, 1000);

const viewsPoll = poller(async () => {
  const v = await apiGet("/api/instructor/views");
  if (!v || v.pending || v.error) return;
  views = v;
  const a = views.attitude || {};
  attHist.point.push(a.point_err_true ?? NaN); attHist.know.push(a.knowledge_err ?? NaN);
  for (const k of ["point", "know"]) while (attHist[k].length > 120) attHist[k].shift();
  renderOverview();
  renderSchedule(views.schedule || []);
  if (debrief && views.divergence) debrief.setPairsMeta(views.divergence.rows);
  if (focus.state().view !== "debrief" && focus.state().view !== "prep" && focus.state().view !== "raw") renderActiveView();
}, 1000);

const timelinePoll = poller(async () => {
  const d = await apiGet(`/api/instructor/timeline?since=${tlSeq}`);
  if (d.segment !== tlSegment && tlSeq) {
    addLog("low", "SIM", tText("A snapshot was loaded: new timeline segment {{n}}", { n: d.segment }));
  }
  ingestTimeline(d);
}, 2000);

const snapshotPoll = poller(async () => {
  const v = focus.state().view;
  if (snapshot && v !== "raw" && v !== "obc" && !document.body.classList.contains("subpage")
      && Date.now() - (snapshotPoll.last || 0) < 10000) return;
  snapshotPoll.last = Date.now();
  snapshot = await apiGet("/api/instructor/snapshot");
  updateRawSnapshot();
  updateClockTruth();
  if (!snapshotTabsBuilt) { buildSnapshotTabs(); snapshotTabsBuilt = true; }
  updateActiveSnapshotTab();
  updateCompletenessCounter();
  performParameterSearch();
}, 2000);

const failuresPoll = poller(async () => {
  const data = await apiGet("/api/failures");
  renderFailures(Array.isArray(data) ? data : (data.failures || []));
  await fetchDebrief(false);
}, 5000);

/* VR headset link (smo-vr/1, docs/VR_INTERFACE_ICD.md). The return line is
 * optional, so a connected headset that never replies is NO_REPLY (neutral),
 * not a fault; DEGRADED / SILENT caution, ERROR alarm. */
function renderVrBadge(link) {
  const b = $("vr-badge");
  if (!b) return;
  if (!link || link.enabled === false) {
    b.innerHTML = renderChip({ kind: "off", label: tText("VR off"),
      title: tText("VR bridge not running (--no-vr, SMO_VR=0 or port in use)") });
    return;
  }
  const n = link.n_clients || 0;
  const overall = link.overall || "NO_CLIENTS";
  const rows = (link.clients || []).map((c) => `${c.team || c.peer} [${c.transport}] ${c.health}` +
    (c.status_word_hex ? ` ${c.status_word_hex}` : "") + (c.text ? ` — ${c.text}` : ""));
  const title = tText("VR bridge TCP:{{tcp}} WS:{{ws}}", { tcp: link.tcp_port, ws: link.ws_port }) + "\n" +
    (rows.length ? rows.join("\n") : tText("no headsets connected"));
  const kind = overall === "ERROR" ? "alarm" : (overall === "DEGRADED" || overall === "SILENT") ? "warn" : "neutral";
  b.innerHTML = renderChip({ kind, title, label: n ? `VR ${n} ${overall.replace("_", " ")}` : tText("VR: no headsets") });
}

function renderAppBar() {
  if (!state) { renderTimeControl(); return; }
  $("sim-time").textContent = state.sim_time ? fmtUTC(state.sim_time) : tText("no data");
  $("sim-date").textContent = state.sim_time ? String(state.sim_time).slice(0, 10) + " UTC" : "";
  renderTimeControl();
  renderVrBadge(state.vr_link);
  const ob = $("btn-override");
  ob.textContent = state.override_passes ? tText("Pass override on") : tText("Override passes");
  ob.setAttribute("aria-pressed", String(!!state.override_passes));
  ob.classList.toggle("primary", !!state.override_passes);
  if (state.spacecraft_phase != null && document.activeElement !== $("phase-select") && !$("btn-set-phase").classList.contains("is-armed")) {
    $("phase-select").value = String(state.spacecraft_phase);
  }
  $("phase-now").innerHTML = state.spacecraft_phase != null
    ? `<span class="ds-id">${esc(PHASE_NAMES[state.spacecraft_phase] || state.spacecraft_phase)}</span>` : "";
  if (Array.isArray(state.active_failures)) renderFailures(state.active_failures);
  updateScenarioButtons();
  if (activeScenarioName && selectedScenario != null) {
    const sc = scenarios[selectedScenario];
    const nowSimMs = simNowMs();
    if (sc && scenarioStartSimMs != null && nowSimMs != null) {
      const elapsedS = Math.max(0, (nowSimMs - scenarioStartSimMs) / 1000);
      const totalS = sc.duration_s || 1;
      $("progress-elapsed").textContent = formatDuration(elapsedS);
      $("progress-remaining").textContent = formatDuration(totalS);
      $("progress-fill").style.width = Math.min(100, (elapsedS / totalS) * 100) + "%";
    }
  }
  if (stateAgeS() !== null && stateAgeS() > 3) $("run-chip").innerHTML = renderChip({ kind: "stale", label: tText("no data"), title: tText("The simulator stopped answering") });
}

/* ── language ──────────────────────────────────────────────────────────── */

function relabel(changed) {
  const q = new URLSearchParams(location.search);
  const requestedSub = q.get("sub");
  const back = $("subpage-back");
  if (back) {
    const backQ = new URLSearchParams();
    if (q.get("ui")) backQ.set("ui", q.get("ui"));
    if (q.get("lang")) backQ.set("lang", q.get("lang"));
    back.href = "/" + (backQ.toString() ? "?" + backQ.toString() : "");
    back.textContent = tText("← Back to dashboard");
  }
  $("full-snapshot-title").textContent = requestedSub
    ? tText("Subsystem deep-dive: {{sub}}", { sub: requestedSub.toUpperCase() }) : tText("Full simulator state");
  renderTimeControl();
  const showing = $("raw-snapshot-container").style.display === "block";
  $("btn-toggle-raw").textContent = showing ? tText("Hide raw snapshot") : tText("Show raw snapshot");
  if (!snapshot) $("raw-snapshot-json").textContent = tText("Loading…");
  setConn(wsUp);
  renderTabsBar();
  renderFocusHead();
  if (scenarios.length) renderScenarios();
  if (selectedScenario != null && scenarios[selectedScenario]) $("scenario-briefing").textContent = scnBriefing(scenarios[selectedScenario]) || tText("No briefing available.");
  if (lastDebrief !== undefined) renderDebrief(lastDebrief);
  if (!changed) return;
  armAll();
  renderElements();
  updateFailureTypes();
  renderBreakpoints();
  renderFailures(lastFailures);
  renderSchedule(views ? views.schedule : []);
  if (snapshotTabsBuilt) populateSubsystemLauncher();
  if (powerView) { powerView.destroy(); powerView = null; }
  renderAppBar(); renderOverview(); renderActiveView(); renderTimeline(); renderPower();
  updateScenarioButtons(); updateBpSave(); updateCompletenessCounter();
  if (debrief) debrief.relabel();
  fetchDebrief(false);
}

/* ── two-step (arm -> execute) for everything that disrupts the class ──── */

const ARMED = [
  ["btn-clear-all", () => clearAllFailures()],
  ["btn-set-phase", () => setSpacecraftPhase()],
  ["btn-start-separation", () => startSeparation()],
  ["btn-set-soc", () => setBatterySoc()],
  ["btn-stop-scenario", () => stopScenario()],
];
function rearm(id, fn) {
  const old = $(id);
  const fresh = old.cloneNode(true);
  old.replaceWith(fresh);
  armButton(fresh, { seconds: 5, onExecute: fn });
}
function armInject() { rearm("btn-inject", () => injectFailure()); }
function armAll() {
  for (const [id, fn] of ARMED) rearm(id, fn);
  armInject();
}

/* ── init ──────────────────────────────────────────────────────────────── */

async function init() {
  await I18n.ready;
  mountLangToggle($("lang-toggle"));
  onLangChange(() => relabel(true));
  mountLogbook({ tool: "instructor", buttonHost: $("lb-slot"),
    getContext: () => {
      const sc = selectedScenario != null ? scenarios[selectedScenario] : null;
      return { ...(sc && sc.id ? { scenario: sc.id } : {}), ...(activeScenarioName ? { sim_status: frozen ? "stopped" : "running" } : {}) };
    } });
  onLangChange(() => { loadPrepWorksheets(); debriefWsKey = ""; loadDebriefWorksheets(); });
  loadDebriefWorksheets();
  const q = new URLSearchParams(location.search);
  const requestedSub = q.get("sub");
  if (requestedSub) {
    document.body.classList.add("subpage");
    focus.select("raw", Date.now());
    const cont = $("full-snapshot-container");
    const back = document.createElement("a");
    back.className = "subpage-back";
    back.id = "subpage-back";
    cont.parentNode.insertBefore(back, cont);
    const titleEl = document.querySelector("title");
    if (titleEl) titleEl.removeAttribute("data-i18n");
    document.title = "SMO — " + requestedSub.toUpperCase();
  }
  timeline = mountTimeline($("timeline"), { t: tText, onSelect: showTimelineDetail });
  debrief = createDebrief($("view-debrief"), { onToast: (m) => showToast(m, "success") });
  armAll();
  relabel();
  showView();

  // header
  $$("#speed-group button[data-speed]").forEach((btn) => btn.addEventListener("click", () => setSpeed(parseFloat(btn.dataset.speed))));
  $("freeze-btn").addEventListener("click", toggleFreeze);
  $("btn-quick-snap").addEventListener("click", () => saveBreakpoint(tText("snapshot {{t}}", { t: simClock() })));

  // focus pane
  $("view-select").addEventListener("change", (e) => goView(e.target.value, true));
  $("btn-focus-back").addEventListener("click", () => { focus.back(Date.now()); showView(); });
  $("btn-focus-pin").addEventListener("click", () => { focus.pin(!focus.state().pinned); renderFocusHead(); });
  $("focus-auto").addEventListener("change", (e) => { focus.setAuto(e.target.checked); renderFocusHead(); });
  setInterval(() => applyFocusResult(focus.tick(Date.now())), 1000);

  // scenarios + debrief
  $("refresh-scenarios").addEventListener("click", loadScenarios);
  $("btn-start-scenario").addEventListener("click", startScenario);
  $("btn-fetch-debrief").addEventListener("click", () => fetchDebrief(true));

  // fault menu + form
  $("fail-subsystem").addEventListener("change", updateFailureTypes);
  $("fail-type").addEventListener("change", updateFailureParams);
  $$("input[name=\"fail-onset\"]").forEach((r) => r.addEventListener("change", updateOnsetDurationVisibility));
  $("fail-trigger").addEventListener("change", () => {
    $("trigger-delay-group").hidden = $("fail-trigger").value !== "delay";
    $("trigger-tc-group").hidden = $("fail-trigger").value !== "tc";
    renderReview();
  });
  for (const id of ["fail-params", "fail-onset-dur", "fail-delay", "fail-tc", "fail-snapshot"]) {
    $(id).addEventListener("input", renderReview);
    $(id).addEventListener("change", renderReview);
  }
  updateOnsetDurationVisibility();
  $("btn-add-batch").addEventListener("click", addToBatch);
  $("btn-override").addEventListener("click", toggleOverride);
  $("btn-bookmark").addEventListener("click", () => mark("bookmark"));
  $("anomaly-disp").addEventListener("change", (e) => { if (e.target.value) { mark("anomaly", e.target.value); e.target.value = ""; } });

  // delegated clicks (no inline handlers, no globals)
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-el]");
    if (el && el.getAttribute("aria-disabled") !== "true") { selectedElement = el.dataset.el; renderElements(); updateFailureTypes(); return; }
    const tile = e.target.closest("#overview .tile[data-view]");
    if (tile) { goView(tile.dataset.view, true); return; }
    const gv = e.target.closest("[data-goview]");
    if (gv) { goView(gv.dataset.goview, true); return; }
    const fc = e.target.closest("[data-fault]");
    if (fc) { selectedFault = fc.dataset.fault; goView("fault", true); return; }
    if (e.target.id === "btn-suggest-go") { applyFocusResult(focus.accept(Date.now())); showView(); return; }
    if (e.target.id === "btn-suggest-x") { focus.dismiss(); renderFocusHead(); return; }
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    if (btn.dataset.act === "clear-failure") clearFailure(btn.dataset.id);
    if (btn.dataset.act === "cancel-schedule") cancelSchedule(btn.dataset.id);
    if (btn.dataset.act === "unbatch") { batch.splice(+btn.dataset.i, 1); renderReview(); }
  });

  // session label
  $("btn-session-label").addEventListener("click", publishSessionLabel);
  $("session-label").addEventListener("input", updateSessionLabelBtn);
  $("session-label").addEventListener("keydown", (e) => { if (e.key === "Enter") publishSessionLabel(); });

  // snapshots
  $("btn-save-bp").addEventListener("click", () => saveBreakpoint());
  $("breakpoint-name").addEventListener("input", updateBpSave);
  $("breakpoint-name").addEventListener("keydown", (e) => { if (e.key === "Enter") saveBreakpoint(); });
  updateBpSave();
  refreshBreakpoints();
  setInterval(refreshBreakpoints, 15000);

  // timeline panel
  $("clear-log").addEventListener("click", () => { $("event-log").innerHTML = ""; });
  $("btn-log-toggle").addEventListener("click", () => {
    const panel = $("timeline-panel");
    const collapsed = panel.classList.toggle("collapsed");
    $("btn-log-toggle").setAttribute("aria-expanded", String(!collapsed));
  });
  $$("#tl-window button[data-win]").forEach((b) => b.addEventListener("click", () => {
    tlWindowS = +b.dataset.win;
    $$("#tl-window button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    renderTimeline();
  }));
  const setTlMode = (list) => {
    $("timeline").hidden = list; $("event-log").hidden = !list;
    $("btn-tl-graph").setAttribute("aria-pressed", String(!list));
    $("btn-tl-list").setAttribute("aria-pressed", String(list));
    if (list) $("event-log").scrollTop = $("event-log").scrollHeight; else renderTimeline();
  };
  $("btn-tl-graph").addEventListener("click", () => setTlMode(false));
  $("btn-tl-list").addEventListener("click", () => setTlMode(true));
  setInterval(renderTimeline, 2000);

  // raw state: search + raw JSON
  $("param-search").addEventListener("input", performParameterSearch);
  $("btn-clear-search").addEventListener("click", () => { $("param-search").value = ""; $("param-search-results").style.display = "none"; });
  $("btn-toggle-raw").addEventListener("click", () => {
    const container = $("raw-snapshot-container");
    const showing = container.style.display === "block";
    container.style.display = showing ? "none" : "block";
    $("btn-toggle-raw").setAttribute("aria-expanded", String(!showing));
    $("btn-toggle-raw").textContent = showing ? tText("Show raw snapshot") : tText("Hide raw snapshot");
    if (!showing) updateRawSnapshot();
  });

  setConn(false);
  $("scenario-chip").innerHTML = renderChip({ kind: "neutral", label: tText("No scenario running") });
  updateScenarioButtons();
  renderFailures([]);
  loadScenarios();
  loadFailureCatalog();
  startWs();
  statePoll.start();
  viewsPoll.start();
  timelinePoll.start();
  snapshotPoll.start();
  failuresPoll.start();
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
