/* ============================================================================
 * C2O DESIGN SYSTEM — logbook.js  (served at /static/shared/logbook.js)
 * ============================================================================
 * The participant logbook panel (docs/plan_2026-11/LOGBOOK_SPEC.md §5), one
 * copy for every tool. The tool's server mounts /api/logbook
 * (smo_common.logbook.register_logbook_routes, or SpaceCDF's FastAPI twin).
 *
 *   import { mountLogbook, logThis, renderLogThis } from "/static/shared/logbook.js";
 *   const lb = mountLogbook({
 *     tool: "mcs",                         // mcs | delayed_tm | orbit | radio | docs
 *                                          // | instructor | design | portal
 *     getContext: () => ({page, procedure, alarm_id, position, sim_ts, ...}),
 *     buttonHost: el | "#selector",        // where the header button goes
 *     bannerHost: el | "#selector",        // optional: the < 12 h expiry banner
 *   });
 *   lb.open() / lb.close() / lb.toggle()
 *   lb.endSession({reason})                // the download prompt dialog
 *   lb.refresh()
 *   logThis({alarm_id: 42}, {kind: "decision"})   // opens the panel, context prefilled
 *   renderLogThis({procedure: "NOM-001", step: 3}) // "Log this" button markup;
 *                                                  // clicks are delegated here
 *
 * The panel is docked and non-modal: it never blocks the page, and a "Log
 * this" button never blocks the action it sits beside. The text lives only
 * on the server (48 h after the last write); this module keeps at most an
 * unsent draft in sessionStorage.
 *
 * Every string goes through i18n.js (keys are the English text; the French
 * is in smo_common/ui/i18n/fr.json).
 * ============================================================================ */

import { t, tText, getLang, onLangChange } from "/static/shared/i18n.js";
import { esc, armButton } from "/static/shared/components.js";

const API = "/api/logbook";
const KINDS = ["decision", "thought", "observation", "reflection"];
const CTX_KEYS = ["page", "procedure", "step", "alarm_id", "param", "study_id", "position",
  "scenario", "report", "dump", "station", "pass", "doc", "command", "gonogo", "gate",
  "proposal", "anomaly", "sim_status", "phase"];
const HIDDEN_CTX = new Set(["sim_status", "phase"]);   // sent, not shown as chips
const POLL_MS = 60000;
const CTX_POLL_MS = 2500;
const WARN_H = 12;

const BOOK = `<svg aria-hidden="true" viewBox="0 0 14 14" width="14" height="14" fill="none" ` +
  `stroke="currentColor" stroke-width="1.3" stroke-linejoin="round">` +
  `<path d="M2 2.5h4a1.5 1.5 0 0 1 1 .4V12a1.6 1.6 0 0 0-1-.4H2z"/>` +
  `<path d="M12 2.5H8a1.5 1.5 0 0 0-1 .4V12a1.6 1.6 0 0 1 1-.4h4z"/></svg>`;

/* English is the i18n key; plain functions so the extractor sees literals. */
const kindLabel = (k) => ({
  decision: tText("Decision"), thought: tText("Thought"), observation: tText("Observation"),
  reflection: tText("Reflection"), worksheet: tText("Worksheet answer"),
}[k] || k);
const toolLabel = (k) => ({
  mcs: tText("Mission control"), delayed_tm: tText("Delayed TM"), orbit: tText("Orbit tools"),
  radio: tText("Radio view"), docs: tText("Documentation"), instructor: tText("Instructor"),
  design: tText("SpaceCDF"), portal: tText("Welcome page"),
}[k] || k);
const ctxLabel = (k) => ({
  page: tText("page"), procedure: tText("procedure"), step: tText("step"), alarm_id: tText("alarm"),
  param: tText("parameter"), study_id: tText("study"), position: tText("position"),
  scenario: tText("scenario"), report: tText("report"), dump: tText("dump"),
  station: tText("station"), pass: tText("pass"), doc: tText("document"),
  command: tText("command"), gonogo: "GO/NO-GO", gate: tText("gate"),
  proposal: tText("proposal"), anomaly: tText("anomaly"), sim_ts: tText("sim time"),
}[k] || k);

const S = {
  tool: null, getContext: () => ({}), mounted: false, open: false, tab: "write",
  data: null, sheets: [], sheetsKey: "", kind: "decision", override: {}, removed: new Set(),
  btn: null, panel: null, banner: null, dlg: null, lastFocus: null, ctxSig: "",
  timers: [], busy: false,
};

/* ── small utilities ─────────────────────────────────────────────────── */
const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
const hostOf = (h) => (typeof h === "string" ? document.querySelector(h) : h) || null;
const lsKey = () => `c2o.lb.draft.${S.tool}`;
function draftGet() { try { return sessionStorage.getItem(lsKey()) || ""; } catch (e) { return ""; } }
function draftSet(v) {
  try { if (v) sessionStorage.setItem(lsKey(), v); else sessionStorage.removeItem(lsKey()); } catch (e) { /* private mode */ }
}
function locale() { return getLang() === "fr" ? "fr-CA" : "en-CA"; }
function fmtTime(iso) {
  const d = iso ? new Date(iso) : null;
  if (!d || isNaN(d)) return "";
  return d.toLocaleTimeString(locale(), { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "UTC" });
}
function fmtDay(iso) {
  const d = iso ? new Date(iso) : null;
  if (!d || isNaN(d)) return "";
  return d.toLocaleDateString(locale(), { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" }) + " · UTC";
}
function fmtWhen(iso) {
  const d = iso ? new Date(iso) : null;
  if (!d || isNaN(d)) return "";
  return d.toLocaleString(locale(), { weekday: "short", day: "numeric", month: "short",
    hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "UTC", timeZoneName: "short" });
}
function announce(msg) {
  const r = S.panel && $(".lb-live", S.panel);
  if (!r) return;
  r.textContent = "";
  setTimeout(() => { r.textContent = msg; }, 30);
}

async function api(method, path, body) {
  const init = { method, credentials: "same-origin", headers: { Accept: "application/json" } };
  if (body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const r = await fetch(API + path, init);
  let j = null;
  try { j = await r.json(); } catch (e) { /* empty */ }
  if (!r.ok) throw new Error((j && j.error) || `HTTP ${r.status}`);
  return j;
}

/* ── context ─────────────────────────────────────────────────────────── */
function liveContext() {
  let c = {};
  try { c = S.getContext() || {}; } catch (e) { c = {}; }
  return c;
}
function draftContext() {
  const c = { ...liveContext(), ...S.override };
  const out = {};
  for (const [k, v] of Object.entries(c)) {
    if (v === null || v === undefined || v === "" || S.removed.has(k)) continue;
    if (k === "sim_ts" || CTX_KEYS.includes(k)) out[k] = v;
  }
  return out;
}
function worksheetContext() {
  const c = { ...liveContext(), ...S.override };
  const out = {};
  for (const k of ["page", "procedure", "scenario", "alarm_id", "anomaly", "study_id", "gate", "phase"]) {
    if (c[k] !== undefined && c[k] !== null && c[k] !== "") out[k] = c[k];
  }
  return out;
}

/* ── derived state ───────────────────────────────────────────────────── */
function entries() { return (S.data && S.data.entries) || []; }
function answersFor(wid, qid) {
  return entries().filter((e) => e.kind === "worksheet" && e.worksheet &&
    e.worksheet.id === wid && e.worksheet.q === qid);
}
function hoursLeft() {
  if (!S.data || !S.data.expires_at) return null;
  return (new Date(S.data.expires_at) - Date.now()) / 3600e3;
}

/* ── header button + banner ──────────────────────────────────────────── */
function renderButton() {
  if (!S.btn) return;
  const n = S.data ? S.data.count : null;
  const unsaved = S.data ? S.data.unsaved : 0;
  $(".lb-t", S.btn).textContent = tText("Logbook");
  const badge = $(".lb-n", S.btn);
  badge.textContent = n === null ? "·" : String(n);
  badge.classList.toggle("is-unsaved", unsaved > 0);
  const label = n === null ? tText("Logbook")
    : unsaved > 0 ? tText("Logbook, {{count}} entry, {{u}} not downloaded",
      { count: n, u: unsaved, plural: "Logbook, {{count}} entries, {{u}} not downloaded" })
    : tText("Logbook, {{count}} entry", { count: n, plural: "Logbook, {{count}} entries" });
  S.btn.setAttribute("aria-label", label);
  S.btn.title = label;
  S.btn.setAttribute("aria-expanded", String(S.open));
}

function renderBanner() {
  if (!S.banner) return;
  const h = hoursLeft();
  const show = S.data && S.data.unsaved > 0 && h !== null && h < WARN_H;
  S.banner.hidden = !show;
  if (!show) return;
  S.banner.innerHTML =
    `<svg aria-hidden="true" width="12" height="12"><use href="/static/shared/glyphs.svg#g-warn-up"></use></svg>` +
    `<span>${t("Your logbook has {{count}} entry not downloaded. The server deletes it on {{when}}.",
      { count: S.data.unsaved, when: fmtWhen(S.data.expires_at),
        plural: "Your logbook has {{count}} entries not downloaded. The server deletes it on {{when}}." })}</span>` +
    `<button type="button" class="ds-btn sm" data-lb="banner-open">${t("Download…")}</button>`;
}

/* ── panel skeleton ──────────────────────────────────────────────────── */
function buildPanel() {
  const p = S.panel;
  const kinds = KINDS.map((k) =>
    `<button type="button" role="radio" class="lb-kind" data-kind="${k}" aria-checked="${k === S.kind}" ` +
    `tabindex="${k === S.kind ? 0 : -1}">${esc(kindLabel(k))}</button>`).join("");
  p.innerHTML =
    `<div class="lb-hd"><h2 id="lb-h">${t("Logbook")}</h2><span class="lb-who"></span>` +
    `<button type="button" class="ds-btn ghost sm lb-x" data-lb="close" aria-label="${esc(tText("Close logbook"))}">✕</button></div>` +
    `<div class="lb-warn-slot"></div>` +
    `<div class="ds-tabs lb-tabs" role="tablist" aria-label="${esc(tText("Logbook sections"))}">` +
    `<button type="button" role="tab" class="ds-tab" id="lb-tab-write" data-tab="write" aria-controls="lb-pane-write">${t("Entries")} <span class="ds-chip lb-c-e">0</span></button>` +
    `<button type="button" role="tab" class="ds-tab" id="lb-tab-ws" data-tab="ws" aria-controls="lb-pane-ws">${t("Worksheets")} <span class="ds-chip lb-c-w">0</span></button>` +
    `</div>` +
    `<div class="lb-body">` +
    `<section class="lb-pane" id="lb-pane-write" role="tabpanel" aria-labelledby="lb-tab-write">` +
    `<form class="lb-new" autocomplete="off">` +
    `<div class="lb-kinds" role="radiogroup" aria-label="${esc(tText("Entry kind"))}">${kinds}</div>` +
    `<label class="ds-sr" for="lb-text">${t("New logbook entry")}</label>` +
    `<textarea id="lb-text" class="lb-ta" maxlength="8000" ` +
    `placeholder="${esc(tText("What did you decide, notice or think? Ctrl+Enter saves."))}"></textarea>` +
    `<div class="lb-ctx" aria-label="${esc(tText("Context saved with the entry"))}" role="group"></div>` +
    `<div class="lb-row"><span class="lb-hint lb-grow">${t("Context is captured automatically; remove what does not apply.")}</span>` +
    `<button type="submit" class="ds-btn primary" data-lb="save">${t("Save entry")}</button></div>` +
    `<div class="lb-err" role="alert"></div>` +
    `</form>` +
    `<ol class="lb-list" aria-label="${esc(tText("Your entries, newest first"))}"></ol>` +
    `</section>` +
    `<section class="lb-pane" id="lb-pane-ws" role="tabpanel" aria-labelledby="lb-tab-ws" hidden>` +
    `<p class="lb-wsintro">${t("Worksheets from the course workbook that apply here. Each answer is saved to your logbook.")}</p>` +
    `<div class="lb-wslist"></div></section>` +
    `</div>` +
    `<div class="lb-ft"><div class="priv"></div>` +
    `<div class="lb-row">` +
    `<a class="ds-btn sm" data-lb="dl-md" download>${t("Download Markdown")}</a>` +
    `<a class="ds-btn sm" data-lb="dl-html" download>${t("Download printable HTML")}</a>` +
    `<span class="lb-grow"></span>` +
    `<button type="button" class="ds-btn sm" data-lb="end">${t("End session…")}</button>` +
    `<button type="button" class="ds-btn sm critical" data-lb="wipe">${t("Delete now")}</button>` +
    `</div></div>` +
    `<div class="ds-sr lb-live" aria-live="polite"></div>`;
  $("#lb-text", p).value = draftGet();
  armButton($('[data-lb="wipe"]', p), { seconds: 5, onExecute: wipe });
  selectTab(S.tab, false);
  renderAll();
}

function selectTab(tab, focus) {
  S.tab = tab;
  for (const b of $$('[role="tab"]', S.panel)) {
    const on = b.dataset.tab === tab;
    b.setAttribute("aria-selected", String(on));
    b.tabIndex = on ? 0 : -1;
    if (on && focus) b.focus();
  }
  $("#lb-pane-write", S.panel).hidden = tab !== "write";
  $("#lb-pane-ws", S.panel).hidden = tab !== "ws";
  if (tab === "ws") loadSheets();
}

function renderAll() {
  renderButton();
  renderBanner();
  if (!S.panel || !S.panel.firstChild) return;
  renderWho();
  renderCtx();
  renderList();
  renderFooter();
  renderSheets();
}

function renderWho() {
  const w = $(".lb-who", S.panel);
  if (!S.data) { w.textContent = ""; return; }
  const p = S.data.person || {};
  w.textContent = p.local ? tText("this browser") : (p.id_label || "");
  w.title = p.local ? tText("No sign-in here: the logbook belongs to this browser.") : "";
  const slot = $(".lb-warn-slot", S.panel);
  const h = hoursLeft();
  slot.innerHTML = S.data.unsaved > 0 && h !== null && h < WARN_H
    ? `<div class="ds-banner is-caution lb-warn" role="status">` +
      `<svg aria-hidden="true" width="12" height="12"><use href="/static/shared/glyphs.svg#g-warn-up"></use></svg>` +
      `<span>${t("Not downloaded yet, and deleted from the server in {{h}} h.", { h: Math.max(0, Math.floor(h)) })}</span></div>`
    : "";
}

function renderCtx() {
  const box = $(".lb-ctx", S.panel);
  const ctx = draftContext();
  const sig = JSON.stringify(ctx);
  if (sig === S.ctxSig && box.childElementCount) return;
  S.ctxSig = sig;
  const chips = Object.entries(ctx).filter(([k]) => !HIDDEN_CTX.has(k)).map(([k, v]) =>
    `<span class="ds-chip">${esc(ctxLabel(k))} ${esc(String(v))}` +
    `<button type="button" data-rm="${esc(k)}" aria-label="${esc(tText("Remove {{what}} from this entry", { what: ctxLabel(k) }))}">✕</button></span>`).join("");
  box.innerHTML = chips
    ? `<span class="lbl">${t("Context")}</span>${chips}`
    : `<span class="lbl">${t("No context captured here.")}</span>`;
}

function renderList() {
  const ol = $(".lb-list", S.panel);
  const es = entries();
  $(".lb-c-e", S.panel).textContent = String(es.length);
  if (!S.data) { ol.innerHTML = `<li class="lb-empty">${t("Loading…")}</li>`; return; }
  if (!es.length) {
    ol.innerHTML = `<li class="lb-empty">${t("No entries yet. Log decisions as you make them; you can download everything at the end of the session.")}</li>`;
    return;
  }
  let day = "", html = "";
  for (const e of es) {
    const d = fmtDay(e.ts);
    if (d !== day) { day = d; html += `<li class="lb-day" aria-hidden="true">${esc(d)}</li>`; }
    const ctx = Object.entries(e.context || {}).filter(([k]) => !HIDDEN_CTX.has(k))
      .map(([k, v]) => `${ctxLabel(k)} ${v}`).join(" · ");
    const ws = e.kind === "worksheet" && e.worksheet
      ? `<div class="ws">${esc(e.worksheet.id)} · ${esc(e.worksheet.q_text || e.worksheet.q || "")}</div>` : "";
    const mark = e.worksheet && e.worksheet.checked === true ? "☑ " : e.worksheet && e.worksheet.checked === false ? "☐ " : "";
    html += `<li class="lb-e" data-id="${esc(e.id)}">` +
      `<div class="meta"><span class="tm">${esc(fmtTime(e.ts))}</span>` +
      `<span class="kd">${esc(kindLabel(e.kind))}</span>` +
      (e.tool !== S.tool ? `<span>${esc(toolLabel(e.tool))}</span>` : "") +
      (e.edited ? `<span>${t("edited")}</span>` : "") +
      `<span class="act"><button type="button" class="ds-btn ghost sm" data-edit="${esc(e.id)}">${t("Edit")}</button>` +
      `<button type="button" class="ds-btn ghost sm" data-del="${esc(e.id)}">${t("Delete")}</button></span></div>` +
      ws + `<div class="tx">${esc(mark)}${esc(e.text)}</div>` +
      (ctx || e.sim_ts ? `<div class="cx">${esc([ctx, e.sim_ts ? `${ctxLabel("sim_ts")} ${e.sim_ts}` : ""].filter(Boolean).join(" · "))}</div>` : "") +
      `</li>`;
  }
  ol.innerHTML = html;
  for (const b of $$("[data-del]", ol)) {
    armButton(b, { seconds: 4, onExecute: () => removeEntry(b.dataset.del) });
  }
}

function renderFooter() {
  const p = $(".priv", S.panel);
  const d = S.data;
  if (!d) { p.textContent = ""; }
  else if (d.expires_at) {
    p.innerHTML = t("<b>Private to you</b> · deleted from the server on {{- when}} ({{h}} h after your last entry)",
      { when: `<span class="num">${esc(fmtWhen(d.expires_at))}</span>`, h: Math.round(d.retention_h) });
  } else {
    p.innerHTML = t("<b>Private to you</b> · nothing is stored on the server yet. Entries are kept {{h}} h after your last one.",
      { h: Math.round(d.retention_h) });
  }
  const lang = getLang();
  $('[data-lb="dl-md"]', S.panel).href = `${API}/export?format=md&lang=${lang}`;
  $('[data-lb="dl-html"]', S.panel).href = `${API}/export?format=html&lang=${lang}`;
  const none = !d || !d.count;
  for (const a of $$('[data-lb^="dl-"]', S.panel)) {
    if (none) { a.setAttribute("aria-disabled", "true"); a.setAttribute("data-reason", tText("Nothing to download yet")); }
    else { a.removeAttribute("aria-disabled"); a.removeAttribute("data-reason"); }
  }
  const wipeBtn = $('[data-lb="wipe"]', S.panel);
  if (none) { wipeBtn.setAttribute("aria-disabled", "true"); wipeBtn.setAttribute("data-reason", tText("Nothing stored on the server")); }
  else { wipeBtn.removeAttribute("aria-disabled"); wipeBtn.removeAttribute("data-reason"); }
}

/* ── worksheets ──────────────────────────────────────────────────────── */
async function loadSheets(force) {
  const ctx = worksheetContext();
  const key = JSON.stringify([getLang(), ctx]);
  if (!force && key === S.sheetsKey) return;
  S.sheetsKey = key;
  try {
    const j = await api("GET", `/worksheets?tool=${encodeURIComponent(S.tool)}&lang=${getLang()}` +
      `&context=${encodeURIComponent(JSON.stringify(ctx))}`);
    if (S.sheetsKey !== key) return;
    S.sheets = j.worksheets || [];
  } catch (e) {
    S.sheets = [];
  }
  renderSheets(true);
}

function questionHtml(w, q) {
  const id = `lbq-${w.id}-${q.id}`.replace(/[^\w-]/g, "_");
  const prev = answersFor(w.id, q.id).slice().reverse();
  const answers = prev.map((a) => {
    const mark = a.worksheet.checked === true ? "☑ " : a.worksheet.checked === false ? "☐ " : "";
    return `<div class="qa"><span class="tm">${esc(fmtTime(a.ts))}</span> ${esc(mark)}${esc(a.text)}</div>`;
  }).join("");
  const short = q.kind !== "check" && q.text.length < 90 && !/[?？]\s*$/.test(q.text);
  const oneLine = short || q.kind === "check";
  // one-line rows keep the button short so the field keeps its width
  const btn = `<button type="button" class="ds-btn sm" data-answer aria-describedby="${id}-t">` +
    `${prev.length ? t("Add answer") : oneLine ? t("Save") : t("Save answer")}</button>`;
  // A confirm-each-step row is one line: tick, optional note, save. A
  // form field ("Pass / shift", "Image ID") is one line too; a reflection
  // question (ends in "?") gets room to write.
  const input = short
    ? `<div class="lb-row lb-chk"><label class="ds-sr" for="${id}">${t("Your answer")}</label>` +
      `<textarea id="${id}" class="lb-ta line" rows="1" maxlength="8000" placeholder="${esc(tText("Your answer"))}"></textarea>${btn}</div>`
    : q.kind === "check"
    ? `<div class="lb-row lb-chk"><label class="ds-check"><input type="checkbox" id="${id}-c" aria-describedby="${id}-t"> ${t("Done")}</label>` +
      `<label class="ds-sr" for="${id}">${t("Note")}</label>` +
      `<textarea id="${id}" class="lb-ta line" rows="1" maxlength="8000" placeholder="${esc(tText("Note or actual value (optional)"))}"></textarea>${btn}</div>`
    : `<label class="ds-sr" for="${id}">${t("Your answer")}</label>` +
      `<textarea id="${id}" class="lb-ta sm" maxlength="8000" placeholder="${esc(tText("Your answer"))}"></textarea>` +
      `<div class="lb-row"><span class="lb-grow"></span>${btn}</div>`;
  return `<div class="lb-q" data-w="${esc(w.id)}" data-q="${esc(q.id)}" data-kind="${esc(q.kind)}">` +
    `<div class="qt" id="${id}-t">${esc(q.text)}</div>` +
    (q.hint ? `<div class="qh">${q.kind === "check" ? t("Expected:") + " " : ""}${esc(q.hint)}</div>` : "") +
    answers + input + `</div>`;
}

function sheetHtml(w, open) {
  const total = w.questions.length;
  const done = w.questions.filter((q) => answersFor(w.id, q.id).length).length;
  let sec = "", body = "";
  for (const q of w.questions) {
    if (q.section && q.section !== sec) { sec = q.section; body += `<div class="qs">${esc(sec)}</div>`; }
    body += questionHtml(w, q);
  }
  return `<details class="ds-disclosure lb-ws" data-w="${esc(w.id)}"${open ? " open" : ""}>` +
    `<summary><span class="id">${esc(w.id)}</span> <span class="ti">${esc(w.title)}</span>` +
    `<span class="r">${t("{{done}} of {{total}} answered", { done, total })}</span></summary>` +
    `<div class="bd">${body}</div></details>`;
}

function renderSheets(fresh) {
  if (!S.panel || !S.panel.firstChild) return;
  const specific = S.sheets.filter((w) => w.match && w.match !== "general");
  $(".lb-c-w", S.panel).textContent = String(specific.length || S.sheets.length);
  const box = $(".lb-wslist", S.panel);
  if (!fresh && box.childElementCount) {
    // keep open state and typed answers: refresh only answer counts/lists
    for (const d of $$("details.lb-ws", box)) {
      const w = S.sheets.find((x) => x.id === d.dataset.w);
      if (!w) continue;
      const done = w.questions.filter((q) => answersFor(w.id, q.id).length).length;
      $("summary .r", d).textContent = tText("{{done}} of {{total}} answered", { done, total: w.questions.length });
    }
    return;
  }
  if (!S.sheets.length) {
    box.innerHTML = `<p class="lb-empty">${t("No worksheet applies here. Open a procedure, or use the entries tab for free notes.")}</p>`;
    return;
  }
  const openIds = new Set($$("details.lb-ws[open]", box).map((d) => d.dataset.w));
  let html = "";
  specific.forEach((w, i) => { html += sheetHtml(w, openIds.has(w.id) || (!openIds.size && i === 0)); });
  const general = S.sheets.filter((w) => !w.match || w.match === "general");
  if (general.length) {
    if (specific.length) html += `<div class="lb-sep">${t("Also for this tool")}</div>`;
    general.forEach((w, i) => { html += sheetHtml(w, openIds.has(w.id) || (!specific.length && !openIds.size && i === 0)); });
  }
  box.innerHTML = html;
}

async function saveAnswer(qel) {
  const ta = $("textarea", qel);
  const cb = $('input[type="checkbox"]', qel);
  let text = ta.value.trim();
  const checked = cb ? cb.checked : undefined;
  if (!text && cb) text = checked ? tText("Done") : tText("Not done");
  if (!text) { ta.focus(); return; }
  const w = S.sheets.find((x) => x.id === qel.dataset.w) ||
    (S.dlgSheets || []).find((x) => x.id === qel.dataset.w);
  const q = w && w.questions.find((x) => x.id === qel.dataset.q);
  const body = {
    kind: "worksheet", text, tool: S.tool, lang: getLang(), context: draftContext(),
    worksheet: { id: qel.dataset.w, q: qel.dataset.q, ...(w ? { title: w.title } : {}),
      ...(q ? { q_text: q.text } : {}), ...(cb ? { checked } : {}) },
  };
  if (body.context.sim_ts) { body.sim_ts = String(body.context.sim_ts); delete body.context.sim_ts; }
  try {
    await api("POST", "/entries", body);
    ta.value = ""; if (cb) cb.checked = false;
    announce(tText("Answer saved to your logbook"));
    await refresh();
    // re-render just this worksheet so its answers show; keep it open
    const d = qel.closest("details.lb-ws");
    if (d && w) {
      const tmp = document.createElement("div");
      tmp.innerHTML = sheetHtml(w, true);
      const fresh = tmp.firstChild;
      d.replaceWith(fresh);
      const same = $(`.lb-q[data-q="${CSS.escape(qel.dataset.q)}"] [data-answer]`, fresh);
      if (same) same.focus();
    }
  } catch (e) {
    announce(tText("Not saved: {{why}}", { why: e.message }));
  }
}

/* ── actions ─────────────────────────────────────────────────────────── */
async function saveEntry() {
  const ta = $("#lb-text", S.panel);
  const err = $(".lb-err", S.panel);
  const text = ta.value.trim();
  if (!text) { err.textContent = tText("Write something first."); ta.focus(); return; }
  err.textContent = "";
  const ctx = draftContext();
  const body = { kind: S.kind, text, tool: S.tool, lang: getLang(), context: ctx };
  if (ctx.sim_ts) { body.sim_ts = String(ctx.sim_ts); delete ctx.sim_ts; }
  const btn = $('[data-lb="save"]', S.panel);
  btn.setAttribute("aria-disabled", "true");
  btn.setAttribute("data-reason", tText("Saving…"));
  try {
    await api("POST", "/entries", body);
    ta.value = ""; draftSet("");
    S.override = {}; S.removed.clear(); S.ctxSig = "";
    announce(tText("Entry saved"));
    await refresh();
  } catch (e) {
    err.textContent = tText("Not saved: {{why}}", { why: e.message });
  } finally {
    btn.removeAttribute("aria-disabled"); btn.removeAttribute("data-reason");
  }
}

function editEntry(id) {
  const li = $(`.lb-e[data-id="${CSS.escape(id)}"]`, S.panel);
  const e = entries().find((x) => x.id === id);
  if (!li || !e) return;
  const tx = $(".tx", li);
  tx.innerHTML = `<label class="ds-sr" for="lb-ed-${esc(id)}">${t("Edit entry")}</label>` +
    `<textarea class="lb-ta sm" id="lb-ed-${esc(id)}" maxlength="8000">${esc(e.text)}</textarea>` +
    `<div class="lb-row"><span class="lb-grow"></span>` +
    `<button type="button" class="ds-btn sm ghost" data-ed-cancel>${t("Cancel")}</button>` +
    `<button type="button" class="ds-btn sm primary" data-ed-save="${esc(id)}">${t("Save")}</button></div>`;
  const ta = $("textarea", tx);
  ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length);
  ta.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) { ev.preventDefault(); commitEdit(id, ta.value); }
    if (ev.key === "Escape") { ev.preventDefault(); ev.stopPropagation(); renderList(); focusEntry(id, "edit"); }
  });
}
function focusEntry(id, which) {
  const b = $(`[data-${which}="${CSS.escape(id)}"]`, S.panel);
  if (b) b.focus();
}
async function commitEdit(id, text) {
  if (!text.trim()) return;
  try {
    await api("PATCH", `/entries/${encodeURIComponent(id)}`, { text });
    announce(tText("Entry updated"));
    await refresh();
    focusEntry(id, "edit");
  } catch (e) { announce(tText("Not saved: {{why}}", { why: e.message })); }
}
async function removeEntry(id) {
  try {
    await api("DELETE", `/entries/${encodeURIComponent(id)}`);
    announce(tText("Entry deleted"));
    await refresh();
    $("#lb-text", S.panel).focus();
  } catch (e) { announce(tText("Not deleted: {{why}}", { why: e.message })); }
}
async function wipe() {
  try {
    await api("DELETE", "");
    announce(tText("Your logbook was deleted from the server"));
    await refresh();
  } catch (e) { announce(tText("Not deleted: {{why}}", { why: e.message })); }
}

export async function refresh() {
  try {
    S.data = await api("GET", "");
  } catch (e) {
    if (!S.data) S.data = null;
  }
  renderAll();
  return S.data;
}

/* ── open / close ────────────────────────────────────────────────────── */
function open(opts = {}) {
  if (!S.panel) return;
  if (!S.panel.firstChild) buildPanel();
  if (!S.open) S.lastFocus = document.activeElement;
  S.open = true;
  S.panel.classList.add("open");
  S.panel.removeAttribute("inert");
  if (opts.tab) selectTab(opts.tab, false);
  renderButton();
  renderCtx();
  refresh();
  loadSheets();           // also gives the Worksheets tab its count
  const ta = $("#lb-text", S.panel);
  if (opts.focus !== false) setTimeout(() => (S.tab === "write" ? ta : $("#lb-tab-ws", S.panel)).focus(), 20);
}
function close() {
  if (!S.panel || !S.open) return;
  S.open = false;
  S.panel.classList.remove("open");
  S.panel.setAttribute("inert", "");
  renderButton();
  const back = S.lastFocus && document.contains(S.lastFocus) ? S.lastFocus : S.btn;
  if (back && back.focus) back.focus();
}

/** logThis(context, {kind, text}) — open the panel with the context
 *  prefilled. Never blocks: call it after (or beside) the real action. */
export function logThis(context = {}, opts = {}) {
  if (!S.mounted) return;
  S.override = { ...(context || {}) };
  S.removed.clear();
  S.ctxSig = "";
  if (opts.kind && KINDS.includes(opts.kind)) S.kind = opts.kind;
  open({ tab: "write", focus: false });
  for (const b of $$(".lb-kind", S.panel)) {
    const on = b.dataset.kind === S.kind;
    b.setAttribute("aria-checked", String(on)); b.tabIndex = on ? 0 : -1;
  }
  renderCtx();
  const ta = $("#lb-text", S.panel);
  if (opts.text && !ta.value) ta.value = opts.text;
  setTimeout(() => ta.focus(), 20);
}

/** renderLogThis(context, {label, kind}) -> button markup. Clicks are
 *  handled here (delegated), so tools only place the markup. */
export function renderLogThis(context = {}, opts = {}) {
  // data-i18n* keep static page templates translatable by applyDom().
  const label = opts.label
    ? `<span>${esc(opts.label)}</span>`
    : `<span data-i18n="Log this">${esc(tText("Log this"))}</span>`;
  const tip = tText("Note this decision in your logbook");
  return `<button type="button" class="ds-btn ghost sm lb-this${opts.iconOnly ? " icon" : ""}" ` +
    `data-lb-ctx="${esc(JSON.stringify(context))}"` +
    (opts.kind ? ` data-lb-kind="${esc(opts.kind)}"` : "") +
    ` title="${esc(tip)}" data-i18n-title="Note this decision in your logbook"` +
    (opts.iconOnly ? ` aria-label="${esc(tText("Log this"))}" data-i18n-aria-label="Log this">${BOOK}`
      : `>${BOOK}${label}`) + `</button>`;
}

/* ── end of session dialog ───────────────────────────────────────────── */
export async function endSession(opts = {}) {
  if (!S.mounted) return;
  await refresh();
  let debrief = [];
  try {
    const ctx = { ...worksheetContext(), phase: "debrief" };
    const j = await api("GET", `/worksheets?tool=${encodeURIComponent(S.tool)}&lang=${getLang()}` +
      `&context=${encodeURIComponent(JSON.stringify(ctx))}`);
    debrief = (j.worksheets || []).filter((w) => w.questions.some((q) => !answersFor(w.id, q.id).length));
    // the reflection sheet first (WB-5.5-DB), then scorecards
    debrief.sort((a, b) => Number(!/-DB$/.test(a.id)) - Number(!/-DB$/.test(b.id)));
  } catch (e) { /* no worksheets: the dialog still offers the download */ }
  S.dlgSheets = debrief;
  const d = S.data || { count: 0 };
  const lang = getLang();
  const head = opts.reason === "stopped"
    ? t("The scenario has stopped")
    : opts.reason === "gate" ? t("Gate passed") : t("End of session");
  const w = debrief[0];
  const deb = w
    ? `<div class="sec"><div class="lbl">${t("Debrief worksheet, not answered yet")}</div>` +
      sheetHtml(w, true) + `</div>` : "";
  const when = d.expires_at
    ? t("The server deletes it on {{- when}}.", { when: `<b class="num">${esc(fmtWhen(d.expires_at))}</b>` })
    : t("Nothing is stored on the server.");
  S.dlg.innerHTML =
    `<div class="lb-dlg" role="dialog" aria-modal="true" aria-labelledby="lb-dlg-h">` +
    `<h2><span id="lb-dlg-h">${head}</span>` +
    `<button type="button" class="ds-btn ghost sm lb-x" data-lb="dlg-close" aria-label="${esc(tText("Close"))}">✕</button></h2>` +
    `<div class="sec"><div><span class="big">${d.count}</span> ${t("entry in your logbook", { count: d.count, plural: "entries in your logbook" })}` +
    (d.unsaved ? ` · ${t("{{n}} not downloaded", { n: d.unsaved })}` : "") + `</div>` +
    `<div class="lb-hint">${t("Download your logbook before you leave. Hand in the file if it is to be graded.")} ${when}</div>` +
    `<div class="lb-row">` +
    `<a class="ds-btn primary" data-lb="dl-md" href="${API}/export?format=md&lang=${lang}" download>${t("Download Markdown")}</a>` +
    `<a class="ds-btn" data-lb="dl-html" href="${API}/export?format=html&lang=${lang}" download>${t("Download printable HTML")}</a>` +
    `</div></div>` + deb +
    `<div class="sec"><div class="lb-row"><span class="lb-grow"></span>` +
    `<button type="button" class="ds-btn" data-lb="dlg-close">${t("Close")}</button></div></div></div>`;
  S.dlg.hidden = false;
  S.dlgFocus = document.activeElement;
  setTimeout(() => { const f = $("[data-lb^='dl-'], button", S.dlg); if (f) f.focus(); }, 20);
}
function closeDialog() {
  if (!S.dlg || S.dlg.hidden) return;
  S.dlg.hidden = true;
  S.dlg.innerHTML = "";
  if (S.dlgFocus && document.contains(S.dlgFocus)) S.dlgFocus.focus();
}

/* ── events ──────────────────────────────────────────────────────────── */
function wire() {
  const p = S.panel;
  p.addEventListener("click", (ev) => {
    const el = ev.target.closest("button, a");
    if (!el || !p.contains(el)) return;
    const a = el.dataset.lb;
    if (a === "close") close();
    else if (a === "end") endSession({ reason: "user" });
    else if (a && a.startsWith("dl-")) afterDownload();
    else if (el.dataset.kind) setKind(el.dataset.kind, true);
    else if (el.dataset.rm) { S.removed.add(el.dataset.rm); S.ctxSig = ""; renderCtx(); $("#lb-text", p).focus(); }
    else if (el.dataset.edit) editEntry(el.dataset.edit);
    else if (el.hasAttribute("data-ed-cancel")) { const id = el.closest(".lb-e").dataset.id; renderList(); focusEntry(id, "edit"); }
    else if (el.dataset.edSave) commitEdit(el.dataset.edSave, $("textarea", el.closest(".lb-e")).value);
    else if (el.hasAttribute("data-answer")) saveAnswer(el.closest(".lb-q"));
    else if (el.getAttribute("role") === "tab") selectTab(el.dataset.tab, true);
  });
  p.addEventListener("submit", (ev) => { ev.preventDefault(); saveEntry(); });
  p.addEventListener("input", (ev) => { if (ev.target.id === "lb-text") draftSet(ev.target.value); });
  p.addEventListener("keydown", (ev) => {
    // The panel's keys are its own: a page's single-key shortcuts and its
    // Esc handler must not fire while the person writes here.
    if (ev.key !== "F6" && ev.key !== "Tab") ev.stopPropagation();
    if (ev.target.id === "lb-text" && ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) {
      ev.preventDefault(); saveEntry(); return;
    }
    if (ev.target.closest && ev.target.closest(".lb-q") && ev.target.tagName === "TEXTAREA" &&
        ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) {
      ev.preventDefault(); saveAnswer(ev.target.closest(".lb-q")); return;
    }
    const rg = ev.target.closest && ev.target.closest('[role="radiogroup"], [role="tablist"]');
    if (rg && ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(ev.key)) {
      const items = $$(rg.getAttribute("role") === "tablist" ? '[role="tab"]' : '[role="radio"]', rg);
      let i = items.indexOf(ev.target);
      if (i < 0) return;
      ev.preventDefault();
      i = ev.key === "Home" ? 0 : ev.key === "End" ? items.length - 1
        : (i + (ev.key === "ArrowLeft" || ev.key === "ArrowUp" ? -1 : 1) + items.length) % items.length;
      const it = items[i];
      if (it.dataset.kind) setKind(it.dataset.kind, true);
      else selectTab(it.dataset.tab, true);
      return;
    }
    if (ev.key === "Escape" && !ev.defaultPrevented) {
      if (ev.target.closest && ev.target.closest(".is-armed")) return;   // armButton disarms
      ev.preventDefault(); close();
    }
  });
  S.dlg.addEventListener("click", (ev) => {
    if (ev.target === S.dlg) { closeDialog(); return; }
    const el = ev.target.closest("button, a");
    if (!el) return;
    if (el.dataset.lb === "dlg-close") closeDialog();
    else if (el.dataset.lb && el.dataset.lb.startsWith("dl-")) afterDownload();
    else if (el.hasAttribute("data-answer")) saveAnswer(el.closest(".lb-q"));
  });
  S.dlg.addEventListener("keydown", (ev) => {
    if (ev.key !== "Tab") ev.stopPropagation();
    if (ev.key === "Escape") { ev.preventDefault(); closeDialog(); return; }
    if (ev.key !== "Tab") return;
    const f = $$("button, a[href], textarea, input", S.dlg).filter((x) => !x.hidden && x.offsetParent !== null);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (ev.shiftKey && document.activeElement === first) { ev.preventDefault(); last.focus(); }
    else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
  });
  document.addEventListener("click", (ev) => {
    const b = ev.target.closest && ev.target.closest(".lb-this[data-lb-ctx]");
    if (b) {
      let ctx = {};
      try { ctx = JSON.parse(b.dataset.lbCtx || "{}"); } catch (e) { ctx = {}; }
      logThis(ctx, { kind: b.dataset.lbKind });
      return;
    }
    const bo = ev.target.closest && ev.target.closest('[data-lb="banner-open"]');
    if (bo) endSession({ reason: "expiry" });
  });
  S.btn && S.btn.addEventListener("click", () => (S.open ? close() : open()));
  window.addEventListener("beforeunload", (ev) => {
    if (S.data && S.data.unsaved > 0) { ev.preventDefault(); ev.returnValue = ""; }
  });
  onLangChange(() => {
    if (S.panel.firstChild) { S.ctxSig = ""; buildPanel(); S.sheetsKey = ""; if (S.tab === "ws") loadSheets(); }
    renderButton(); renderBanner();
  });
  S.timers.push(setInterval(() => { if (!document.hidden) refresh(); }, POLL_MS));
  S.timers.push(setInterval(() => {
    if (!S.open) return;
    renderCtx();
    if (S.tab === "ws") loadSheets();
  }, CTX_POLL_MS));
}

function setKind(k, focus) {
  S.kind = k;
  for (const b of $$(".lb-kind", S.panel)) {
    const on = b.dataset.kind === k;
    b.setAttribute("aria-checked", String(on));
    b.tabIndex = on ? 0 : -1;
    if (on && focus) b.focus();
  }
}

function afterDownload() {
  // The download is a plain link (no navigation, no unload): re-read the
  // marker the server recorded once the response has gone out.
  setTimeout(refresh, 800);
  setTimeout(refresh, 2500);
}

/* ── mount ───────────────────────────────────────────────────────────── */
/**
 * mountLogbook({tool, getContext, buttonHost, bannerHost, buttonClass})
 * -> {open, close, toggle, refresh, endSession, logThis, setContext}
 * Call once per page. buttonHost receives the header button (appended);
 * without one the button is not drawn (open the panel from code).
 */
export function mountLogbook(o = {}) {
  if (S.mounted) return S.apiObj;
  S.tool = o.tool || "mcs";
  S.getContext = typeof o.getContext === "function" ? o.getContext : () => ({});
  if (!document.querySelector('link[data-lb-css]')) {
    const l = document.createElement("link");
    l.rel = "stylesheet"; l.href = "/static/shared/logbook.css"; l.setAttribute("data-lb-css", "");
    document.head.appendChild(l);
  }
  const bh = hostOf(o.buttonHost);
  if (bh) {
    S.btn = document.createElement("button");
    S.btn.type = "button";
    S.btn.className = o.buttonClass || "ds-btn ghost lb-btn";
    S.btn.setAttribute("aria-controls", "c2o-logbook");
    S.btn.setAttribute("aria-expanded", "false");
    S.btn.innerHTML = `${BOOK}<span class="lb-t"></span><span class="lb-n" aria-hidden="true">·</span>`;
    bh.appendChild(S.btn);
  }
  // The < 12 h banner: inside bannerHost when given (a header that stacks
  // its own banners), else right below the header holding the button.
  const banh = hostOf(o.bannerHost);
  const head = !banh && S.btn ? S.btn.closest("header") : null;
  if (banh || head) {
    S.banner = document.createElement("div");
    S.banner.className = "ds-banner is-caution lb-banner";
    S.banner.setAttribute("role", "status");
    S.banner.hidden = true;
    if (banh) banh.appendChild(S.banner);
    else head.insertAdjacentElement("afterend", S.banner);
  }
  S.panel = document.createElement("aside");
  S.panel.id = "c2o-logbook";
  S.panel.setAttribute("aria-labelledby", "lb-h");
  S.panel.setAttribute("inert", "");
  document.body.appendChild(S.panel);
  S.dlg = document.createElement("div");
  S.dlg.className = "lb-ov";
  S.dlg.hidden = true;
  document.body.appendChild(S.dlg);
  S.mounted = true;
  wire();
  renderButton();
  refresh();
  S.apiObj = {
    open, close, toggle: () => (S.open ? close() : open()), refresh, endSession, logThis,
    get isOpen() { return S.open; },
    get state() { return S.data; },
  };
  return S.apiObj;
}

export default { mountLogbook, logThis, renderLogThis, endSession, refresh };
