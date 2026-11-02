/* ============================================================================
 * SMO INSTRUCTOR — modern console page logic (design_2026-08 plan §2.4)
 * ============================================================================
 * ES module, no build step. Uses the frozen Agent-1 shared design system:
 * pure renderers + poller/wsClient from /static/shared/components.js, time
 * formatters from /static/shared/format.js.
 *
 * TRANSPORT RULES (deliberate deviations from the classic page):
 *  - Every instructor command goes ONCE via POST /api/command — the
 *    synchronous error surface; a 400/403 body carries the engine's REASON.
 *    The classic page sent each command twice (WS + POST), enqueuing it
 *    twice. Do not reintroduce that.
 *  - The WebSocket is INBOUND-ONLY: `event`, `state_update`,
 *    `failure_injected`, `failure_cleared`. This module never calls the WS
 *    client's send().
 *  - Event-log timestamps are SIM time (from the last /api/state poll), not
 *    the browser wall clock the classic page used.
 *
 * POLLING (classic cadences preserved): /api/state 1 s ·
 * /api/instructor/snapshot 2 s · /api/failures 5 s (debrief piggybacks the
 * 5 s cycle so a scenario auto-stop surfaces without a click).
 * ========================================================================== */

import {
  esc, renderChip, renderEventRow, poller, wsClient, mountLangToggle,
  renderValue, renderGauge, renderNoData, renderBanner, renderLinkBanner, renderModeBanner,
  glyph, setDisabled, setEnabled, armButton,
} from "/static/shared/components.js";
import { fmtUTC, fmtHex } from "/static/shared/format.js";
// One contact verdict for every console (R3 audit problem #10).
import { linkState } from "/static/shared/state.js";
// UI language (EN|FR) — see docs/i18n/UI_I18N_GUIDE.md. Import i18n.js
// WITHOUT a ?v= query (state is shared via globalThis either way).
import { I18n, t, tText, tdb, onLangChange } from "/static/shared/i18n.js";

/* ── constants ─────────────────────────────────────────────────────────── */

const MAX_LOG_ENTRIES = 200;

// Mode names follow the telemetry decoders (configs/eosat1/aocs/aocs_mode_codes.yaml,
// rulings Q5/Q6). OBC mode 2 is EMERGENCY; the bootloader is not an OBC mode —
// it is indicated by obdh.sw_image = 0.
const AOCS_MODES = { 0: "OFF", 1: "SAFE_BOOT", 2: "DETUMBLE", 3: "COARSE_SUN", 4: "NOMINAL",
                     5: "FINE_POINT", 6: "SLEW", 7: "DESAT", 8: "ECLIPSE", 9: "INERTIAL" };
const OBDH_MODES = { 0: "NOMINAL", 1: "SAFE", 2: "EMERGENCY" };
const TTC_MODES  = { 0: "NOMINAL", 1: "REDUNDANT", 2: "OFF" };
const PL_MODES   = { 0: "OFF", 1: "STANDBY", 2: "IMAGING", 3: "PLAYBACK" };
const LINK_STATUS = { 0: "DOWN", 1: "UP" };
// Authoritative sc_mode convention (engine SC_* constants):
const SC_MODES = { 0: "SAFE", 1: "NOMINAL", 2: "SCIENCE", 3: "EMERGENCY" };
const PHASE_NAMES = ["PRE_SEPARATION", "SEPARATION_TIMER", "INITIAL_POWER_ON",
                     "BOOTLOADER_OPS", "LEOP", "COMMISSIONING", "NOMINAL"];
// Scenario difficulty (YAML `difficulty:`): display label only, never compared.
// English text is the i18n key
const DIFFICULTY_LABELS = { ADVANCED: "ADVANCED", BASIC: "BASIC", BEGINNER: "BEGINNER",
                            INTERMEDIATE: "INTERMEDIATE" };

/* ── state ─────────────────────────────────────────────────────────────── */

let state = null;           // last /api/state
let snapshot = null;        // last /api/instructor/snapshot
let scenarios = [];
let selectedScenario = null;
let activeScenarioName = null;
let scenarioStartSimMs = null;   // scenario progress runs on SIM time
let debriefWasActive = false;
let frozen = false;          // engine truth: state.speed === 0
let lastStateOkMs = null;    // wall time of the last good /api/state poll
let failureCatalog = null;
let currentFailureSpec = null;
let breakpoints = [];

const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

/* ── helpers ───────────────────────────────────────────────────────────── */

/* Readouts go through the shared renderValue(): live / stale (last value,
 * dim italic, age chip) / "no data" — never a dash. The truth feed is
 * /api/state at 1 Hz; if it stops answering, every value turns stale with
 * the age of the last good poll. */
function stateAgeS() {
  return lastStateOkMs === null ? null : (Date.now() - lastStateOkMs) / 1000;
}
function rv(value, units, digits, limits, extra) {
  const age = stateAgeS();
  const verdict = age !== null && age > 3 ? "stale" : "fresh";
  return renderValue(value, Object.assign({ units, digits, limits, ageS: age, verdict }, extra || {}));
}
function pair(a, b, units, digits) {
  const age = stateAgeS();
  const verdict = age !== null && age > 3 ? "stale" : "fresh";
  if ((a == null || !isFinite(a)) && (b == null || !isFinite(b))) return renderNoData();
  const f = (v) => (v != null && isFinite(v) ? Number(v).toFixed(digits) : "?");
  return renderValue(0, { eng: `${f(a)} / ${f(b)}`, units, verdict, ageS: age });
}

function formatDuration(totalSec) {
  const m = Math.floor(totalSec / 60);
  const s = Math.floor(totalSec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/** Scenario difficulty for display; unknown values pass through untranslated. */
function difficultyLabel(d) {
  if (!d) return "?";
  const en = DIFFICULTY_LABELS[String(d).toUpperCase()];
  return en ? tText(en) : String(d);
}

function simNowMs() {
  if (!state || !state.sim_time) return null;
  const t = Date.parse(state.sim_time);
  return isNaN(t) ? null : t;
}

/** Current SIM-time-of-day string for log rows ("—" before the first poll). */
function simClock() {
  return state && state.sim_time ? fmtUTC(state.sim_time) : "--:--:--";
}

function showToast(msg, type) {
  const el = $("toast");
  el.innerHTML = renderBanner(type === "error" ? "alarm" : "ok", msg);
  el.classList.add("show");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.classList.remove("show"), type === "error" ? 6000 : 3000);
}

/* ── API (single command channel: POST /api/command) ───────────────────── */

async function apiGet(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`HTTP ${r.status} on ${path}`);
  return r.json();
}

async function apiPost(path, body) {
  try {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    // A 400/403 carries the REASON the server refused — return it either way.
    let payload = null;
    try { payload = await r.json(); } catch (e) { payload = null; }
    if (!r.ok) return payload || { status: "error", message: `HTTP ${r.status}` };
    return payload;
  } catch (e) {
    return { status: "error", message: String(e) };
  }
}

/** Send one instructor command, ONCE, over the documented HTTP path.
 *  Returns the response object; callers surface `message` on non-ok. */
function sendCommand(payload) {
  return apiPost("/api/command", payload);
}

/* ── event log (SIM-time stamps, 200-entry cap, severity-coloured) ─────── */

function addLog(severity, source, message) {
  const log = $("event-log");
  const holder = document.createElement("div");
  holder.innerHTML = renderEventRow({
    severity, source, text: message, utc: simClock(),
  });
  log.appendChild(holder.firstElementChild);
  while (log.children.length > MAX_LOG_ENTRIES) log.removeChild(log.firstChild);
  log.scrollTop = log.scrollHeight;
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
  // Return value deliberately unused: no instructor command is ever sent on
  // the WS — POST /api/command is the single outbound channel.
  wsClient(`${proto}//${location.host}/ws`, {
    _open: () => { setConn(true); addLog("info", "SYSTEM", tText("WebSocket connected")); },
    _close: () => setConn(false),
    event: (msg) => {
      addLog(msg.severity || "info", msg.source || msg.subsystem || "SIM",
             msg.message || JSON.stringify(msg));
    },
    state_update: (msg) => { if (msg.state) state = msg.state; },
    failure_injected: (msg) =>
      addLog("high", "FAIL", tText("Injected: {{what}}", { what: `${msg.subsystem}/${msg.failure}` })),
    failure_cleared: (msg) =>
      addLog("info", "FAIL", tText("Cleared: {{id}}", { id: msg.failure_id })),
  });
}

/* ── snapshot browser (full god-mode state; ?sub= deep-dive) ───────────── */

let snapshotTabs = [];
let snapshotActiveTab = null;
let snapshotTabsBuilt = false;

/** Normalise a snapshot.parameters key to "0xHHHH". The endpoint serialises
 *  integer param ids as decimal strings ("257"); accept both forms. */
function paramHexId(key) {
  if (/^0x/i.test(key)) return key;
  const n = parseInt(key, 10);
  return Number.isFinite(n) ? fmtHex(n, 4) : key;
}

const SUB_REGIONS = {
  "01": "EPS·raw", "02": "AOCS·raw", "03": "TCS·raw", "04": "OBDH·raw",
  "05": "TTC·raw", "06": "PAYLOAD·raw", "07": "FDIR·raw", "08": "ORBIT·raw",
  "0B": "PROP·raw",
};

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

  // 1. One tab per subsystem model from snapshot.subsystems
  if (snapshot.subsystems && typeof snapshot.subsystems === "object") {
    for (const sub of Object.keys(snapshot.subsystems).sort()) {
      const st = snapshot.subsystems[sub];
      if (st == null || typeof st !== "object") continue;
      const fields = Object.keys(st).sort().map((k) => ({
        key: k,
        getter: () => (snapshot.subsystems[sub] ? snapshot.subsystems[sub][k] : undefined),
      }));
      snapshotTabs.push({ id: "sub:" + sub, label: sub.toUpperCase(), fields, cells: new Map() });
    }
  }

  // 2. Raw parameter dict grouped by hex high byte (subsystem region);
  //    unknown regions fall back to a "0xNNxx" group so EVERY parameter in
  //    the snapshot has a rendering home (completeness guarantee).
  if (snapshot.parameters && typeof snapshot.parameters === "object") {
    const groups = {};
    for (const rawId of Object.keys(snapshot.parameters)) {
      const hex = paramHexId(rawId);
      const m = hex.match(/^0x([0-9A-Fa-f]{2})/);
      const region = m ? (SUB_REGIONS[m[1].toUpperCase()] || ("0x" + m[1].toUpperCase() + "xx"))
                       : "OTHER·raw";
      (groups[region] = groups[region] || []).push(rawId);
    }
    for (const region of Object.keys(groups).sort()) {
      const fields = groups[region]
        .sort((a, b) => paramHexId(a).localeCompare(paramHexId(b)))
        .map((rawId) => ({
          key: paramHexId(rawId),
          getter: () => (snapshot.parameters ? snapshot.parameters[rawId] : undefined),
        }));
      snapshotTabs.push({ id: "raw:" + region, label: region, fields, cells: new Map() });
    }
  }

  for (const tab of snapshotTabs) {
    const btn = document.createElement("button");
    btn.className = "snap-tab";
    btn.dataset.tabId = tab.id;
    btn.innerHTML = `${esc(tab.label)}<span class="count">${tab.fields.length}</span>`;
    btn.addEventListener("click", () => {
      snapshotActiveTab = tab.id;
      renderActiveSnapshotTab();
    });
    tabsRoot.appendChild(btn);
  }

  // Honour ?sub=<id> in subpage mode (accepts "sub:eps", "eps" or "raw:…").
  const requested = new URLSearchParams(location.search).get("sub");
  if (requested) {
    const want = snapshotTabs.find((t) => t.id === requested
      || t.id === "sub:" + requested || t.id === "raw:" + requested);
    snapshotActiveTab = want ? want.id
      : (snapshotTabs.length ? snapshotTabs[0].id : null);
  } else if (snapshotTabs.length) {
    snapshotActiveTab = snapshotTabs[0].id;
  }
  populateSubsystemLauncher();
  renderActiveSnapshotTab();
}

/** Deep-dive launcher: one link per snapshot tab. ?sub= COMPOSES with ?ui= —
 *  the current ui override (if any) is propagated so a deep-dive opened from
 *  /?ui=modern stays modern. ?lang= is carried the same way (i18n S4). */
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
  $$("#full-snapshot-tabs .snap-tab").forEach((b) =>
    b.classList.toggle("active", b.dataset.tabId === snapshotActiveTab));

  const tab = snapshotTabs.find((t) => t.id === snapshotActiveTab);
  if (!tab) return;
  tab.cells = new Map();
  const frag = document.createDocumentFragment();
  for (const f of tab.fields) {
    const row = document.createElement("div");
    row.className = "param-cell";
    const k = document.createElement("span");
    k.className = "pkey";
    k.textContent = f.key;
    const v = document.createElement("span");
    v.className = "pval";
    v.textContent = formatParamValue(f.getter());
    row.appendChild(k);
    row.appendChild(v);
    frag.appendChild(row);
    tab.cells.set(f.key, v);
  }
  body.appendChild(frag);
}

function updateActiveSnapshotTab() {
  // In-place text update of the visible tab only — no innerHTML rebuild.
  const tab = snapshotTabs.find((t) => t.id === snapshotActiveTab);
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
  for (const t of snapshotTabs) {
    total += t.fields.length;
    for (const f of t.fields) {
      const v = f.getter();
      if (v !== undefined && v !== null) populated++;
    }
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

/* ── parameter search (name or hex id, across params + subsystem state) ── */

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
        for (const [key, val] of Object.entries(subState)) {
          all.push({ id: `${subName}.${key}`, name: `${subName}.${key}`, value: val });
        }
      }
    }
  }

  const isHexQuery = query.startsWith("0x");
  const matches = all.filter((p) => {
    if (isHexQuery) return p.id.toLowerCase().includes(query);
    return p.name.toLowerCase().includes(query)
        || String(p.value).toLowerCase().includes(query);
  }).slice(0, 10);

  results.innerHTML = matches.length
    ? matches.map((m) =>
        `<div class="hit"><span class="k">${esc(m.id)}</span>` +
        `<span>${esc(formatParamValue(m.value))}</span></div>`).join("")
    : `<div class="no-data">${t("No parameters found")}</div>`;
  results.style.display = "block";
}

/* ── scenarios & session ───────────────────────────────────────────────── */

async function loadScenarios() {
  let data = null;
  try { data = await apiGet("/api/scenarios"); } catch (e) { data = null; }
  scenarios = data ? (Array.isArray(data) ? data : (data.scenarios || [])) : [];
  renderScenarios();
}

/* Display text only: sc.name stays the command/compare key (start_scenario).
 * The overlay is keyed by the YAML file stem the API returns as sc.id. */
function scnName(sc) { return sc.id ? tdb(`scn:${sc.id}:name`, sc.name) : sc.name; }
function scnLabel(name) { const sc = scenarios.find((x) => x.name === name); return sc ? scnName(sc) : name; }
function scnBriefing(sc) { return sc.id && sc.briefing ? tdb(`scn:${sc.id}:briefing`, sc.briefing) : sc.briefing; }

/** Run state of the scenario: "running" | "paused" (sim frozen) | null. */
function scenarioRunState() {
  if (!activeScenarioName) return null;
  return frozen ? "paused" : "running";
}
function runChip(st) {
  return st === "running" ? renderChip({ kind: "active", label: tText("Running") })
    : st === "paused" ? renderChip({ kind: "stale", label: tText("Paused") }) : "";
}

function renderScenarios() {
  const list = $("scenario-list");
  if (!scenarios.length) {
    list.innerHTML = `<div class="no-data" style="padding:var(--sp-3) var(--sp-4)">${t("No scenarios available")}</div>`;
    return;
  }
  const had = list.contains(document.activeElement) ? document.activeElement.dataset.index : null;
  list.innerHTML = scenarios.map((sc, i) => `
    <button type="button" class="scn" data-index="${i}" aria-pressed="${selectedScenario === i}">
      <span>${esc(scnName(sc))}</span>
      ${activeScenarioName === sc.name ? runChip(scenarioRunState()) : ""}
      <span class="sd"><span>${esc(difficultyLabel(sc.difficulty))}</span>
        <span>${formatDuration(sc.duration_s || 0)}</span></span>
    </button>`).join("");
  list.querySelectorAll(".scn").forEach((el) =>
    el.addEventListener("click", () => selectScenario(parseInt(el.dataset.index, 10))));
  if (had !== null && had !== undefined) {
    const b = list.querySelector(`[data-index="${had}"]`);
    if (b) b.focus();
  }
}

/** Start / Stop: enabled, disabled with a reason, never ambiguous. */
function updateScenarioButtons() {
  const sc = selectedScenario != null ? scenarios[selectedScenario] : null;
  const start = $("btn-start-scenario"), stop = $("btn-stop-scenario");
  if (!sc) setDisabled(start, tText("Select a scenario first"));
  else if (activeScenarioName === sc.name) setDisabled(start, tText("This scenario is already running"));
  else if (activeScenarioName) {
    setDisabled(start, tText("Stop \"{{name}}\" first", { name: scnLabel(activeScenarioName) }));
  } else setEnabled(start);
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
}

async function startScenario() {
  if (selectedScenario == null) return;
  const sc = scenarios[selectedScenario];
  if (!sc) return;
  const res = await sendCommand({ type: "start_scenario", scenario: sc.name });
  if (res && res.status !== "ok") {
    showToast(tText("Scenario start refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  activeScenarioName = sc.name;
  scenarioStartSimMs = simNowMs();
  updateScenarioButtons();
  addLog("info", "SCENARIO", tText("Started: {{name}}", { name: scnName(sc) }));
  showToast(tText("Scenario \"{{name}}\" started", { name: scnName(sc) }), "success");
  renderScenarios();
}

async function stopScenario() {
  if (!activeScenarioName) return;
  const name = activeScenarioName;
  const res = await sendCommand({ type: "stop_scenario" });
  if (res && res.status !== "ok") {
    showToast(tText("Stop refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  addLog("info", "SCENARIO", tText("Stopped: {{name}}", { name: scnLabel(name) }));
  activeScenarioName = null;
  scenarioStartSimMs = null;
  updateScenarioButtons();
  renderScenarios();
  // The engine builds the debrief on stop; give it a tick then show it.
  setTimeout(() => fetchDebrief(true), 1200);
}

/* ── DEBRIEF (new — wires the previously-unreferenced endpoint) ────────── */

let lastDebrief;              // undefined: static markup still shown
function renderDebrief(d) {
  lastDebrief = d;
  const body = $("debrief-body");
  if (!d) {
    body.innerHTML = `<div class="no-data">${t("No debrief yet. It appears when a scenario ends (stopped, or its duration elapsed).")}</div>`;
    return;
  }
  const nd = renderNoData();
  const secs = (v) => (v == null ? nd : `${Number(v).toFixed(1)} s`);
  const responses = (d.responses || []).map((r) =>
    `<div class="prow"><span class="pl">${esc(r.category || "?")}` +
    `${r.description ? ": " + esc(r.description) : ""}</span>` +
    `<span class="pv ds-mono">${r.time_s != null ? Number(r.time_s).toFixed(1) + " s" : nd}</span></div>`
  ).join("");
  body.innerHTML = `
    <table>
      <tr><td>${t("Scenario")}</td><td>${d.name ? esc(d.name) : nd}</td></tr>
      <tr><td>${t("Duration")}</td><td>${secs(d.duration_s)}</td></tr>
      <tr><td>${t("Score")}</td><td>${d.score_pct != null ? Number(d.score_pct).toFixed(0) + " %" : nd}</td></tr>
      <tr><td>${t("MTTD (detect)")}</td><td>${secs(d.mttd_s)}</td></tr>
      <tr><td>${t("MTTI (isolate)")}</td><td>${secs(d.mtti_s)}</td></tr>
      <tr><td>${t("MTTR (recover)")}</td><td>${secs(d.mttr_s)}</td></tr>
    </table>
    ${responses ? `<div class="note" style="margin-top:6px;">${t("Operator responses")}</div>${responses}`
                : `<div class="note" style="margin-top:6px;">${t("No operator responses recorded.")}</div>`}`;
}

/** Poll GET /api/scenario/debrief. Also the authority for the header
 *  scenario chip; announces a debrief when a scenario ends (incl. auto-stop
 *  on duration_s, which the page cannot see any other way). */
async function fetchDebrief(announce) {
  let d = null;
  try { d = await apiGet("/api/scenario/debrief"); } catch (e) { return; }
  const chip = $("scenario-chip");
  if (d.active && d.current) {
    chip.innerHTML = renderChip({ kind: frozen ? "stale" : "active",
      label: (frozen ? tText("Paused: {{name}}", { name: scnLabel(d.current) })
        : tText("Running: {{name}}", { name: scnLabel(d.current) })),
      title: tText("A training scenario is running") });
    if (activeScenarioName !== d.current) {
      activeScenarioName = d.current;   // page reload during a run
      updateScenarioButtons();
      renderScenarios();
    }
  } else {
    chip.innerHTML = renderChip({ kind: "neutral", label: tText("No scenario running") });
    if (debriefWasActive && !d.active) {
      // active -> finished transition (auto-stop or STOP elsewhere)
      announce = true;
      if (activeScenarioName) {
        addLog("info", "SCENARIO", tText("Ended: {{name}}", { name: scnLabel(activeScenarioName) }));
        activeScenarioName = null;
        scenarioStartSimMs = null;
        updateScenarioButtons();
        renderScenarios();
      }
    }
  }
  debriefWasActive = !!d.active;
  if (d.debrief) {
    renderDebrief(d.debrief);
    if (announce) showToast(tText("Scenario debrief available"), "success");
  } else if (announce) {
    renderDebrief(null);
  }
}

/* ── failure injection (form generated from /api/failure-catalog) ──────── */

async function loadFailureCatalog() {
  let data = null;
  try { data = await apiGet("/api/failure-catalog"); } catch (e) { data = null; }
  if (!data || !Array.isArray(data.subsystems)) {
    addLog("high", "FAIL", tText("Failure catalogue unavailable — injection form disabled"));
    $("fail-subsystem").innerHTML = `<option value="">${t("(catalogue unavailable)")}</option>`;
    setDisabled($("btn-inject"), tText("The failure catalogue did not load"));
    return;
  }
  failureCatalog = data;
  $("fail-subsystem").innerHTML = data.subsystems
    .map((s) => `<option value="${esc(s.name)}">${esc(s.label || s.name.toUpperCase())}</option>`)
    .join("");
  updateFailureTypes();
}

function currentSubsystemEntry() {
  if (!failureCatalog) return null;
  const name = $("fail-subsystem").value;
  return failureCatalog.subsystems.find((s) => s.name === name) || null;
}

function updateFailureTypes() {
  const entry = currentSubsystemEntry();
  const failures = entry ? entry.failures : [];
  $("fail-type").innerHTML = failures
    .map((f) => `<option value="${esc(f.name)}">${esc(f.label || f.name)}</option>`)
    .join("");
  updateFailureParams();
}

/** One typed control per ParamSpec: bool→checkbox, enum→select (multi →
 *  multi-select), int/float→number with min/max/step and the engineering
 *  unit; the permitted range is always shown. */
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
    const checked = p.default ? " checked" : "";
    return `<div class="ds-field">
      <label class="ds-check"><input type="checkbox" id="${id}"
        data-param="${esc(p.name)}" data-ptype="bool"${checked}> ${esc(p.label || p.name)}</label>${hint}
    </div>`;
  }
  if (p.type === "enum") {
    const values = p.values || [];
    const labels = p.value_labels || values.map(String);
    const defaults = Array.isArray(p.default) ? p.default.map(String)
      : (p.default === null || p.default === undefined ? [] : [String(p.default)]);
    const opts = values.map((v, i) => {
      const sel = defaults.includes(String(v)) ? " selected" : "";
      return `<option value="${esc(String(v))}"${sel}>${esc(String(labels[i]))}</option>`;
    }).join("");
    const multi = p.multi ? ` multiple size="4" class="ds-select"` : ` class="ds-select"`;
    return `<div class="ds-field">${label}
      <select id="${id}" data-param="${esc(p.name)}" data-ptype="enum"
        data-multi="${p.multi ? "1" : ""}"${multi}>${opts}</select>${hint}
    </div>`;
  }
  const isNum = (p.type === "int" || p.type === "float");
  const step = p.type === "int" ? 1 : (p.step || "any");
  const attrs = [
    isNum ? `type="number"` : `type="text"`,
    isNum ? `step="${step}"` : "",
    (isNum && p.min !== undefined && p.min !== null) ? `min="${p.min}"` : "",
    (isNum && p.max !== undefined && p.max !== null) ? `max="${p.max}"` : "",
    (p.default !== null && p.default !== undefined) ? `value="${esc(String(p.default))}"` : "",
  ].filter(Boolean).join(" ");
  return `<div class="ds-field">${label}
    <input class="ds-input" id="${id}" data-param="${esc(p.name)}"
      data-ptype="${esc(p.type)}" ${attrs}>${hint}
  </div>`;
}

function updateFailureParams() {
  const entry = currentSubsystemEntry();
  const name = $("fail-type").value;
  const spec = entry ? entry.failures.find((f) => f.name === name) : null;
  currentFailureSpec = spec;
  setInjectError("");
  $("fail-effect").textContent = spec ? (spec.effect || "") : "";
  if (!spec) {
    $("fail-params").innerHTML = "";
    setDisabled($("btn-inject"), tText("Choose a failure type first"));
    return;
  }
  setEnabled($("btn-inject"));

  const html = [];
  // Magnitude only when the failure uses one — with ITS unit and range.
  if (spec.magnitude) html.push(renderParamControl(spec.magnitude, "fail-mag"));
  (spec.params || []).forEach((p) => html.push(renderParamControl(p, "fail-p")));
  if (!spec.reversible && spec.notes) {
    html.push(`<div class="fail-effect irrev">${t("Not fully reversible: {{notes}}", { notes: spec.notes })}</div>`);
  }
  $("fail-params").innerHTML = html.join("");
}

/** The server-rejection error box: shows the engine's refusal REASON. */
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
  if (raw === "") {
    if (p.required) return { ok: false, reason: tText("{{where}} is required", { where }) };
    return { ok: true, skip: true };
  }
  if (p.type === "int" || p.type === "float") {
    const num = Number(raw);
    if (!Number.isFinite(num)) return { ok: false, reason: tText("{{where}} must be a number (got \"{{raw}}\")", { where, raw }) };
    if (p.type === "int" && !Number.isInteger(num)) {
      return { ok: false, reason: tText("{{where}} must be a whole number (got {{num}})", { where, num }) };
    }
    const u = p.unit ? ` ${p.unit}` : "";
    if (p.min !== undefined && p.min !== null && num < p.min) {
      return { ok: false, reason: tText("{{where}} must be >= {{min}}{{u}} (got {{num}}{{u}})", { where, min: p.min, u, num }) };
    }
    if (p.max !== undefined && p.max !== null && num > p.max) {
      return { ok: false, reason: tText("{{where}} must be <= {{max}}{{u}} (got {{num}}{{u}})", { where, max: p.max, u, num }) };
    }
    return { ok: true, value: num };
  }
  return { ok: true, value: raw };
}

function updateOnsetDurationVisibility() {
  const onset = document.querySelector("input[name=\"fail-onset\"]:checked").value;
  // Duration applies to every non-step onset (gradual ramp / intermittent).
  $("onset-duration-group").style.display = (onset === "step") ? "none" : "block";
}

async function injectFailure() {
  const spec = currentFailureSpec;
  if (!spec) { setInjectError(tText("No failure selected (catalogue not loaded).")); return; }
  let subsystem = $("fail-subsystem").value;
  if (subsystem === "adcs") subsystem = "aocs";   // legacy alias
  const onset = document.querySelector("input[name=\"fail-onset\"]:checked").value;
  const onset_duration_s = parseInt($("fail-onset-dur").value, 10) || 30;

  const payload = { type: "failure_inject", subsystem, failure: spec.name,
                    onset, onset_duration_s };
  if (spec.magnitude) {
    const r = readParamControl(spec.magnitude, "fail-mag");
    if (!r.ok) { setInjectError(r.reason); return; }
    if (!r.skip) payload.magnitude = r.value;
  }
  for (const p of (spec.params || [])) {
    const r = readParamControl(p, "fail-p");
    if (!r.ok) { setInjectError(r.reason); return; }
    if (!r.skip) payload[p.name] = r.value;
  }
  setInjectError("");

  const res = await sendCommand(payload);
  if (res && res.status !== "ok") {
    setInjectError(tText("Rejected: {{reason}}", { reason: res.message || tText("unknown reason") }));
    showToast(tText("Injection rejected — see the reason above"), "error");
    return;
  }
  const describe = Object.keys(payload)
    .filter((k) => !["type", "subsystem", "failure", "onset", "onset_duration_s"].includes(k))
    .map((k) => `${k}=${JSON.stringify(payload[k])}`).join(" ");
  addLog("high", "INJECT", `${subsystem}/${spec.name} ${describe} onset=${onset}`);
  showToast(tText("Failure injected: {{what}}", { what: `${subsystem}/${spec.name}` }), "success");
  failuresPoll.kick();   // don't wait up to 5 s for the next cycle
}

/* ── active failures ───────────────────────────────────────────────────── */

let lastFailures = [];
function renderFailures(failures) {
  lastFailures = failures || [];
  const list = $("failures-list");
  const n = lastFailures.length;
  $("failures-count").innerHTML = n ? renderChip({ kind: "alarm", label: tText("{{n}} injected", { n }) }) : "";
  if (n) setEnabled($("btn-clear-all"));
  else setDisabled($("btn-clear-all"), tText("No failures are active"));
  // Mark the truth card of every subsystem carrying an injected failure.
  const failed = new Set(lastFailures.map((f) => f.subsystem === "adcs" ? "aocs" : f.subsystem));
  ["eps", "aocs", "tcs", "obdh", "ttc", "payload"].forEach((sub) => {
    const card = $("card-" + sub);
    if (!card) return;
    card.classList.toggle("is-alarm", failed.has(sub));
    const r = card.querySelector(".ds-panel-h .r");
    if (r) r.dataset.failed = failed.has(sub) ? "1" : "";
  });
  if (!n) {
    list.innerHTML = `<div class="no-data" style="padding:var(--sp-2) var(--sp-4)">${t("No active failures")}</div>`;
    return;
  }
  list.innerHTML = lastFailures.map((f) => {
    const id = f.failure_id || f.id || `${f.subsystem}_${f.failure}`;
    const magPct = ((f.magnitude || 0) * 100).toFixed(0);
    const elapsed = f.elapsed_s ? formatDuration(f.elapsed_s) : "00:00";
    const what = `${(f.subsystem || "").toUpperCase()} / ${f.failure || f.type || ""}`;
    return `
      <div class="item fail" data-id="${esc(id)}">
        <span class="fname" title="${esc(what)}">${esc(what)}</span>
        <button type="button" class="ds-btn sm" data-act="clear-failure" data-id="${esc(id)}"
          aria-label="${esc(tText("Clear failure {{what}}", { what }))}">${t("Clear")}</button>
        <div class="fmeta"><span>${t("magnitude {{pct}} %", { pct: magPct })}</span><span>${elapsed}</span></div>
      </div>`;
  }).join("");
}

async function clearFailure(id) {
  const res = await sendCommand({ type: "failure_clear", failure_id: id });
  if (res && res.status !== "ok") {
    showToast(tText("Clear refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  addLog("info", "FAIL", tText("Clearing failure: {{id}}", { id }));
  failuresPoll.kick();
}

async function clearAllFailures() {
  const res = await sendCommand({ type: "failure_clear_all" });
  if (res && res.status !== "ok") {
    showToast(tText("Clear-all refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  addLog("info", "FAIL", tText("Clearing all failures"));
  showToast(tText("All failures cleared"), "success");
  failuresPoll.kick();
}

/* ── mission phase & separation ────────────────────────────────────────── */

async function setSpacecraftPhase() {
  const phase = parseInt($("phase-select").value, 10);
  if (!Number.isInteger(phase) || phase < 0 || phase > 6) {
    showToast(tText("Phase must be 0-6"), "error");
    return;
  }
  const res = await sendCommand({ type: "set_phase", phase });
  if (res && res.status !== "ok") {
    showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  addLog("high", "PHASE", `set_phase ${phase} (${PHASE_NAMES[phase]})`);
  showToast(tText("Phase set: {{phase}} {{name}}", { phase, name: PHASE_NAMES[phase] }), "success");
}

async function startSeparation() {
  const res = await sendCommand({ type: "start_separation" });
  if (res && res.status !== "ok") {
    showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  addLog("high", "PHASE", "start_separation");
  showToast(tText("Separation sequence started"), "success");
}

/* ── overrides ─────────────────────────────────────────────────────────── */

async function toggleOverride() {
  // Desired state from the TRUE engine state, not the button class.
  const newState = !(state && state.override_passes);
  const res = await sendCommand({ type: "override_passes", enabled: newState });
  if (res && res.status !== "ok") {
    showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  addLog(newState ? "low" : "info", "OVERRIDE",
         newState ? tText("Pass override enabled") : tText("Pass override disabled"));
  statePoll.kick();
}

async function setBatterySoc() {
  const soc = parseFloat($("soc-override-input").value);
  if (!isFinite(soc) || soc < 0 || soc > 100) {
    showToast(tText("Battery SoC override must be 0-100 %"), "error");
    return;
  }
  const res = await sendCommand({ type: "set_battery_soc", soc_pct: soc });
  if (res && res.status !== "ok") {
    showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  addLog("low", "OVERRIDE", tText("Battery SoC override -> {{soc}} %", { soc }));
  showToast(tText("Battery SoC set to {{soc}} %", { soc }), "success");
}

/* ── speed group (one stepper: 0.5/1/2/5/10x + FREEZE) ─────────────────── */

async function setSpeed(speed) {
  const res = await sendCommand({ type: "set_speed", value: speed });
  if (res && res.status !== "ok") {
    showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  if (state) state.speed = speed;
  renderTimeControl();
  statePoll.kick();
}

async function toggleFreeze() {
  const next = !frozen;
  const res = await sendCommand({ type: next ? "freeze" : "resume" });
  if (res && res.status !== "ok") {
    showToast(tText("Refused: {{reason}}", { reason: res.message || tText("unknown") }), "error");
    return;
  }
  frozen = next;
  if (state) state.speed = next ? 0 : Math.max(1, state.speed || 0);
  renderTimeControl();
  addLog(frozen ? "low" : "info", "SIM",
         frozen ? tText("Simulation frozen") : tText("Simulation resumed"));
  statePoll.kick();
}

/** Time control states: Running ×N (accent) or Frozen (caution), the
 *  selected speed pressed, and Freeze / Resume saying what it will do. */
function renderTimeControl() {
  const speed = state && state.speed != null ? Number(state.speed) : null;
  const was = frozen;
  frozen = speed === 0;
  if (was !== frozen && scenarios.length) renderScenarios();
  $("run-chip").innerHTML = speed === null ? renderChip({ kind: "nodata", label: tText("no data") })
    : frozen ? renderChip({ kind: "warn", label: tText("Frozen"), title: tText("Simulation time is stopped") })
      : renderChip({ kind: "active", label: tText("Running ×{{s}}", { s: speed }) });
  $$("#speed-group button[data-speed]").forEach((b) =>
    b.setAttribute("aria-pressed", String(!frozen && parseFloat(b.dataset.speed) === speed)));
  const btn = $("freeze-btn");
  btn.textContent = frozen ? tText("Resume") : tText("Freeze");
  btn.classList.toggle("primary", frozen);
  btn.title = frozen ? tText("Resume the simulation at ×1") : tText("Stop simulation time for everyone");
}

/* ── breakpoints ───────────────────────────────────────────────────────── */

async function saveBreakpoint() {
  const name = $("breakpoint-name").value.trim();
  if (!name) return;
  $("breakpoint-name").value = "";
  updateBpSave();
  const res = await apiPost("/api/breakpoint/save", { name });
  if (res && res.status !== "saved") {
    showToast(tText("Breakpoint save failed: {{reason}}", { reason: res.error || res.message || tText("unknown") }), "error");
    return;
  }
  addLog("info", "BRKPT", tText("Saved: \"{{name}}\"", { name }));
  showToast(tText("Breakpoint \"{{name}}\" saved", { name }), "success");
  setTimeout(refreshBreakpoints, 1200);
}

async function refreshBreakpoints() {
  let data = null;
  try { data = await apiGet("/api/breakpoints"); } catch (e) { return; }
  if (!Array.isArray(data)) return;
  breakpoints = data.map((b) => ({
    name: b.name,
    tick: b.tick != null ? b.tick : (b.tick_count != null ? b.tick_count : 0),
    time: b.sim_time || null,
  }));
  renderBreakpoints();
}

function renderBreakpoints() {
  const list = $("breakpoints-list");
  if (list.querySelector(".is-armed")) return;   // never rebuild under a pending two-step
  if (!breakpoints.length) {
    list.innerHTML = `<div class="no-data" style="padding:0 var(--sp-4) var(--sp-3)">${t("No breakpoints saved")}</div>`;
    return;
  }
  list.innerHTML = breakpoints.map((bp) => `
    <div class="item">
      <span class="fname">${esc(bp.name)}</span>
      <button type="button" class="ds-btn critical sm" data-name="${esc(bp.name)}"
        aria-label="${esc(tText("Load breakpoint {{name}}", { name: bp.name }))}">${t("Load")}</button>
      <div class="fmeta"><span>${t("tick {{n}}", { n: bp.tick })}</span>
        <span>${bp.time ? fmtUTC(bp.time, { date: true }) : ""}</span></div>
    </div>`).join("");
  list.querySelectorAll("button[data-name]").forEach((b) =>
    armButton(b, { onExecute: () => loadBreakpoint(b.dataset.name) }));
}

function updateBpSave() {
  if ($("breakpoint-name").value.trim()) setEnabled($("btn-save-bp"));
  else setDisabled($("btn-save-bp"), tText("Enter a breakpoint name first"));
}

async function loadBreakpoint(name) {
  const res = await apiPost("/api/breakpoint/load", { name });
  if (res && res.status !== "loaded") {
    showToast(tText("Breakpoint load failed: {{reason}}", { reason: res.error || res.message || tText("unknown") }), "error");
    return;
  }
  addLog("info", "BRKPT", tText("Loaded: \"{{name}}\"", { name }));
  showToast(tText("Breakpoint \"{{name}}\" loaded", { name }), "success");
}

/* ── truth dashboard render (1 Hz, from /api/state) ────────────────────── */
/* Instructor-side limits, the same thresholds the page always used; the
 * shared renderers turn them into caution/alarm with glyph + ISA code. */
const LIM = {
  soc: { red_low: 30, yellow_low: 70, lo: 0, hi: 100 },
  pct: { yellow_high: 60, red_high: 80, lo: 0, hi: 100 },
  batT: { yellow_low: 5, red_high: 40 },
  obcT: { yellow_low: -10, red_high: 50 },
  fpaT: { yellow_low: -50, red_high: -10 },
  att: { yellow_high: 0.5, red_high: 1 },
  margin: { red_low: 3, yellow_low: 6 },
};

function gauge(id, label, v, lim, units) {
  const age = stateAgeS();
  $(id).innerHTML = renderGauge(v, lim, { label, units, digits: 1, ageS: age,
    verdict: age !== null && age > 3 ? "stale" : "fresh" });
}

function setPv(id, html) {
  const el = $(id);
  if (el) el.innerHTML = html;
}

function onOff(id, on) {
  $(id).innerHTML = on == null ? renderNoData()
    : renderChip(on ? { kind: "neutral", label: tText("On") } : { kind: "off", label: tText("Off") });
}

function modeLabel(id, text) {
  const el = $(id);
  if (!el) return;
  const failed = el.dataset.failed === "1";
  el.innerHTML = (failed ? renderChip({ kind: "alarm", label: tText("failure injected") }) + " " : "")
    + (text ? `<span class="ds-id">${esc(text)}</span>` : "");
}

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
  const rows = (link.clients || []).map((c) =>
    `${c.team || c.peer} [${c.transport}] ${c.health}` +
    (c.status_word_hex ? ` ${c.status_word_hex}` : "") +
    (c.text ? ` — ${c.text}` : ""));
  const title = tText("VR bridge TCP:{{tcp}} WS:{{ws}}", { tcp: link.tcp_port, ws: link.ws_port }) + "\n" +
    (rows.length ? rows.join("\n") : tText("no headsets connected"));
  const kind = overall === "ERROR" ? "alarm" : (overall === "DEGRADED" || overall === "SILENT") ? "warn" : "neutral";
  b.innerHTML = renderChip({ kind, title,
    label: n ? `VR ${n} ${overall.replace("_", " ")}` : tText("VR: no headsets") });
}

function renderBanners() {
  // One contact verdict for every console (R3 audit problem #10); the
  // instructor feed is truth, so the station comes straight from the sim.
  const link = linkState(state);
  if (link.contact && !link.gs) link.gs = state.ground_station_name || "";
  if (link.contact && state.override_passes) link.source = tText("pass override");
  $("link-banner").innerHTML = renderLinkBanner(link);
  // Spacecraft mode from simulation truth (sc_mode), labelled as such.
  const mode = SC_MODES[state.sc_mode] || null;
  $("mode-banner").innerHTML = renderModeBanner({ mode, source: tText("simulation truth"),
    contingency: mode === "SAFE" || mode === "EMERGENCY",
    fdirLevel: state.fdir && Number.isFinite(state.fdir.level) ? state.fdir.level : null });
}

function renderDashboard() {
  if (!state) return;

  // header: SIM TIME primary clock + time control + SC mode chip
  $("sim-time").textContent = state.sim_time ? fmtUTC(state.sim_time) : "--:--:--";
  $("sim-date").textContent = state.sim_time ? String(state.sim_time).slice(0, 10) + " UTC" : "";
  renderTimeControl();
  const mode = SC_MODES[state.sc_mode] || null;
  $("sc-mode-badge").innerHTML = "";
  renderBanners();
  renderVrBadge(state.vr_link);

  // EPS
  const eps = state.eps || {};
  gauge("eps-soc-g", tText("Battery SoC"), eps.soc_pct, LIM.soc, "%");
  setPv("eps-bus-v", rv(eps.bus_voltage_V, "V", 1));
  setPv("eps-bat-v", rv(eps.bat_voltage_V, "V", 1));
  setPv("eps-bat-temp", rv(eps.bat_temp_C, "°C", 1, LIM.batT));
  setPv("eps-pgen", rv(eps.power_gen_W, "W", 1));
  setPv("eps-pcons", rv(eps.power_cons_W, "W", 1));
  setPv("eps-sa", pair(eps.sa_a_A, eps.sa_b_A, "A", 2));
  modeLabel("eps-mode", "");

  // AOCS
  const aocs = state.aocs || {};
  modeLabel("aocs-mode", AOCS_MODES[aocs.mode] || "");
  setPv("aocs-atterr", rv(aocs.att_error_deg, "°", 3, LIM.att));
  setPv("aocs-rr", rv(aocs.rate_roll, "°/s", 4));
  setPv("aocs-rp", rv(aocs.rate_pitch, "°/s", 4));
  setPv("aocs-ry", rv(aocs.rate_yaw, "°/s", 4));
  setPv("aocs-rw12", pair(aocs.rw1_rpm, aocs.rw2_rpm, "rpm", 0));
  setPv("aocs-rw34", pair(aocs.rw3_rpm, aocs.rw4_rpm, "rpm", 0));

  // TCS
  const tcs = state.tcs || {};
  modeLabel("tcs-mode", "");
  setPv("tcs-obc", rv(tcs.temp_obc_C, "°C", 1, LIM.obcT));
  setPv("tcs-bat", rv(tcs.temp_bat_C, "°C", 1, LIM.batT));
  setPv("tcs-fpa", rv(tcs.temp_fpa_C, "°C", 1, LIM.fpaT));
  onOff("tcs-htr-bat", tcs.htr_bat == null ? null : !!tcs.htr_bat);
  onOff("tcs-htr-obc", tcs.htr_obc == null ? null : !!tcs.htr_obc);
  onOff("tcs-cooler", tcs.cooler_fpa == null ? null : !!tcs.cooler_fpa);

  // OBDH
  const obdh = state.obdh || {};
  modeLabel("obdh-mode", OBDH_MODES[obdh.mode] || "");
  gauge("obdh-cpu-g", tText("CPU load"), obdh.cpu_load_pct, LIM.pct, "%");
  gauge("obdh-mem-g", tText("Memory"), obdh.mem_used_pct, LIM.pct, "%");
  setPv("obdh-reboots", rv(obdh.reboot_count, "", 0, { yellow_high: 0.5 }));

  // TT&C
  const ttc = state.ttc || {};
  modeLabel("ttc-mode", TTC_MODES[ttc.mode] || "");
  $("ttc-link").innerHTML = ttc.link_status == null ? renderNoData()
    : renderChip(ttc.link_status === 1 ? { kind: "ok", label: tText("Up") }
      : { kind: "off", label: tText("Down") });
  setPv("ttc-rssi", rv(ttc.rssi_dBm, "dBm", 1));
  setPv("ttc-margin", ttc.link_status === 1 ? rv(ttc.link_margin_dB, "dB", 1, LIM.margin)
    : rv(ttc.link_margin_dB, "dB", 1));
  setPv("ttc-range", rv(ttc.range_km, "km", 1));
  setPv("ttc-elev", rv(ttc.elevation_deg, "°", 1));

  // Payload
  const pl = state.payload || {};
  modeLabel("payload-mode", PL_MODES[pl.mode] || "");
  setPv("pl-fpa", pl.mode ? rv(pl.fpa_temp_C, "°C", 1, LIM.fpaT) : rv(pl.fpa_temp_C, "°C", 1));
  gauge("pl-store-g", tText("Storage"), pl.store_used_pct, LIM.pct, "%");
  setPv("pl-images", rv(pl.image_count, "", 0));

  // Orbit bar
  setPv("orb-lat", rv(state.lat, "°", 4));
  setPv("orb-lon", rv(state.lon, "°", 4));
  setPv("orb-alt", rv(state.alt_km, "km", 2));
  $("orb-eclipse").innerHTML = state.in_eclipse == null ? "" : renderChip(state.in_eclipse
    ? { kind: "neutral", label: tText("In eclipse") } : { kind: "neutral", label: tText("Sunlit") });
  $("orb-contact").innerHTML = "";

  // The pass override — the single copy; its state is engine truth.
  const ob = $("btn-override");
  ob.textContent = state.override_passes ? tText("Pass override on") : tText("Override passes");
  ob.setAttribute("aria-pressed", String(!!state.override_passes));

  // phase select mirrors engine truth when the user is not mid-change
  if (state.spacecraft_phase != null && document.activeElement !== $("phase-select")
      && !$("btn-set-phase").classList.contains("is-armed")) {
    $("phase-select").value = String(state.spacecraft_phase);
  }
  $("phase-now").innerHTML = state.spacecraft_phase != null
    ? `<span class="ds-id" title="${esc(tText("now {{n}} {{name}}", { n: state.spacecraft_phase,
      name: PHASE_NAMES[state.spacecraft_phase] || "" }))}">${esc(PHASE_NAMES[state.spacecraft_phase] || state.spacecraft_phase)}</span>` : "";

  // Active failures + card highlight
  if (Array.isArray(state.active_failures)) renderFailures(state.active_failures);

  // Scenario progress in SIM time (freezes with the sim; speed changes do
  // not rescale already-elapsed time).
  updateScenarioButtons();
  if (activeScenarioName && selectedScenario != null) {
    const sc = scenarios[selectedScenario];
    const nowSimMs = simNowMs();
    if (sc && scenarioStartSimMs != null && nowSimMs != null) {
      const elapsedS = Math.max(0, (nowSimMs - scenarioStartSimMs) / 1000);
      const totalS = sc.duration_s || 1;
      const pct = Math.min(100, (elapsedS / totalS) * 100);
      $("progress-elapsed").textContent = formatDuration(elapsedS);
      $("progress-remaining").textContent = formatDuration(totalS);
      $("progress-fill").style.width = pct + "%";
    }
  }
}

/* ── clock truth card (instructor only — never downlinked) ─────────────── */

const CUC_EPOCH_MS = Date.UTC(2000, 0, 1, 12, 0, 0);   // mission time_epoch

function formatClockAge(sec) {
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return h > 0 ? `${h}h ${String(m).padStart(2, "0")}m`
               : `${m}m ${String(s % 60).padStart(2, "0")}s`;
}

const UINT32_MAX = 4294967295;   // "never synced" sentinel when it leaks through

function updateClockTruth() {
  const c = (snapshot && snapshot.clock_truth) || null;
  const nd = renderNoData();
  if (!c) {
    ["clock-sim-utc", "clock-obc-utc", "clock-since-sync", "clock-drift", "clock-offset"]
      .forEach((id) => setPv(id, nd));
    $("clock-ref").innerHTML = "";
    $("clock-offset-note").textContent = "";
    return;
  }
  $("clock-ref").innerHTML = c.time_ref_name ? `<span class="ds-id">${esc(c.time_ref_name)}</span>` : "";
  const mono = (txt) => `<span class="ds-value" style="font-size:var(--fs-body)">${esc(txt)}</span>`;
  setPv("clock-sim-utc", c.sim_time ? mono(fmtUTC(c.sim_time, { date: true })) : nd);
  setPv("clock-obc-utc", c.obc_time_s != null
    ? mono(fmtUTC(new Date(CUC_EPOCH_MS + c.obc_time_s * 1000), { date: true })) : nd);
  setPv("clock-since-sync", c.time_since_sync_s == null || c.time_since_sync_s >= UINT32_MAX
    ? renderNoData({ label: tText("never synced") }) : mono(formatClockAge(c.time_since_sync_s)));
  setPv("clock-drift", c.drift_ppm == null ? nd : renderValue(c.drift_ppm, { units: "ppm", digits: 2 }));
  if (c.offset_s == null) {
    setPv("clock-offset", nd);
    $("clock-offset-note").textContent = "";
  } else {
    // 1 s: an operator starts to care. 5 s: the FDIR jump guard.
    setPv("clock-offset", renderValue(c.offset_s, { units: "s", digits: 3,
      limits: { yellow_low: -1, yellow_high: 1, red_low: -5, red_high: 5 } }));
    const a = Math.abs(c.offset_s);
    $("clock-offset-note").textContent = a >= 86400
      ? tText("about {{d}} days: the OBC clock has not been set since boot", { d: Math.round(a / 86400) }) : "";
  }
}

/* ── polling (shared poller helper; classic cadences) ──────────────────── */

const statePoll = poller(async () => {
  try {
    state = await apiGet("/api/state");
    lastStateOkMs = Date.now();
  } finally {
    renderDashboard();     // a failed poll turns the readouts stale, visibly
  }
}, 1000);

const snapshotPoll = poller(async () => {
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

/* ── language: JS-owned labels (static markup is re-keyed by I18n) ────── */

/** Write every label the JS owns (button states, subpage chrome) in the
 *  current language, then rebuild the JS-built regions that are not
 *  re-rendered on each poll. Called once at init and on smo:langchange. */
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
    ? tText("Subsystem deep-dive: {{sub}}", { sub: requestedSub.toUpperCase() })
    : tText("Full simulator state");
  renderTimeControl();
  const showing = $("raw-snapshot-container").style.display === "block";
  $("btn-toggle-raw").textContent = showing ? tText("Hide raw snapshot") : tText("Show raw snapshot");
  if (!snapshot) $("raw-snapshot-json").textContent = tText("Loading…");
  setConn(wsUp);
  if (scenarios.length) renderScenarios();
  if (selectedScenario != null && scenarios[selectedScenario]) {
    $("scenario-briefing").textContent =
      scnBriefing(scenarios[selectedScenario]) || tText("No briefing available.");
  }
  if (lastDebrief !== undefined) renderDebrief(lastDebrief);
  if (!changed) return;
  armAll();     // re-bind the two-steps with the translated labels
  // the irreversibility notice only — re-rendering the generated failure
  // form would throw away values the instructor has typed
  const irrev = document.querySelector("#fail-params .fail-effect");
  if (irrev && currentFailureSpec) {
    irrev.textContent = tText("Not fully reversible: {{notes}}", { notes: currentFailureSpec.notes });
  }
  renderBreakpoints();
  renderFailures(lastFailures);
  if (snapshotTabsBuilt) populateSubsystemLauncher();
  if (state) renderDashboard();
  updateScenarioButtons(); updateBpSave();
  updateCompletenessCounter();
  fetchDebrief(false);   // scenario chip
}

/* ── two-step (arm -> execute) for everything that disrupts the class ──── */
/* armButton() keeps the label it was bound with, so after a language change
 * each button is cloned (dropping the old binding) and armed again. The
 * disabled state (aria-disabled + reason) travels with the clone. */
const ARMED = [
  ["btn-inject", () => injectFailure()],
  ["btn-clear-all", () => clearAllFailures()],
  ["btn-set-phase", () => setSpacecraftPhase()],
  ["btn-start-separation", () => startSeparation()],
  ["btn-set-soc", () => setBatterySoc()],
  ["btn-stop-scenario", () => stopScenario()],
];
function armAll() {
  for (const [id, fn] of ARMED) {
    const old = $(id);
    const fresh = old.cloneNode(true);
    old.replaceWith(fresh);
    armButton(fresh, { seconds: 5, onExecute: fn });
  }
}

/* ── init ──────────────────────────────────────────────────────────────── */

async function init() {
  await I18n.ready;            // English: immediate; else bounded catalog load
  mountLangToggle($("lang-toggle"));
  onLangChange(() => relabel(true));
  // ?sub= subpage deep-dive mode (preserved exactly, composing with ?ui=
  // and ?lang=): hide the dashboard chrome, render only the requested
  // snapshot tab full-width with a back link.
  const q = new URLSearchParams(location.search);
  const requestedSub = q.get("sub");
  if (requestedSub) {
    document.body.classList.add("subpage");
    const cont = $("full-snapshot-container");
    const back = document.createElement("a");
    back.className = "subpage-back";
    back.id = "subpage-back";
    cont.parentNode.insertBefore(back, cont);
    // the JS owns the title from here on: stop the DOM pass re-keying it
    const titleEl = document.querySelector("title");
    if (titleEl) titleEl.removeAttribute("data-i18n");
    document.title = "SMO — " + requestedSub.toUpperCase();
  }
  armAll();
  relabel();

  // header controls
  $$("#speed-group button[data-speed]").forEach((btn) =>
    btn.addEventListener("click", () => setSpeed(parseFloat(btn.dataset.speed))));
  $("freeze-btn").addEventListener("click", toggleFreeze);

  // scenarios + debrief
  $("refresh-scenarios").addEventListener("click", loadScenarios);
  $("btn-start-scenario").addEventListener("click", startScenario);
  $("btn-fetch-debrief").addEventListener("click", () => fetchDebrief(true));

  // interventions (the armed ones are wired by armAll)
  $("fail-subsystem").addEventListener("change", updateFailureTypes);
  $("fail-type").addEventListener("change", updateFailureParams);
  $$("input[name=\"fail-onset\"]").forEach((r) =>
    r.addEventListener("change", updateOnsetDurationVisibility));
  updateOnsetDurationVisibility();
  $("btn-override").addEventListener("click", toggleOverride);

  // per-row actions (event delegation — no inline handlers, no globals)
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    if (btn.dataset.act === "clear-failure") clearFailure(btn.dataset.id);
  });

  // breakpoints
  $("btn-save-bp").addEventListener("click", saveBreakpoint);
  $("breakpoint-name").addEventListener("input", updateBpSave);
  $("breakpoint-name").addEventListener("keydown", (e) => {
    if (e.key === "Enter") saveBreakpoint();
  });
  updateBpSave();
  refreshBreakpoints();

  // log panel: collapse + clear
  $("clear-log").addEventListener("click", () => { $("event-log").innerHTML = ""; });
  $("btn-log-toggle").addEventListener("click", () => {
    const panel = $("log-panel");
    const collapsed = panel.classList.toggle("collapsed");
    $("btn-log-toggle").setAttribute("aria-expanded", String(!collapsed));
  });

  // parameter search + raw snapshot
  $("param-search").addEventListener("input", performParameterSearch);
  $("btn-clear-search").addEventListener("click", () => {
    $("param-search").value = "";
    $("param-search-results").style.display = "none";
  });
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
  snapshotPoll.start();
  failuresPoll.start();
  addLog("info", "SYSTEM", tText("Instructor console (modern) initialised"));
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
