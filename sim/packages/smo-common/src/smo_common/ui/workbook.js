/* ============================================================================
 * C2O DESIGN SYSTEM — workbook.js  (served at /static/shared/workbook.js)
 * ============================================================================
 * The "Workbook" tab of the participant logbook (logbook.js): the course
 * workbook as the team member's working copy during operations (Franz,
 * 2026-11-02: "I want the teams to really use them as work books … make the
 * checklists part of the log books").
 *
 *  1. Live procedure checklist — the procedure open or running in the tool
 *     (context.procedure). Built by the server from the procedure CARD
 *     (GET /api/logbook/checklist), with the printed workbook row beside each
 *     step and the places where the two disagree. Each step is confirmed
 *     (GO / NO-GO where the card has a GO/NO-GO), failed or skipped, by the
 *     operator or by the MCS procedure runner (onRunner); the tick captures
 *     UTC, sim time, position and the observed value of every parameter the
 *     step checks. Fail, skip and NO-GO are deviations.
 *  2. Forms — anomaly ticket, handover, GO/NO-GO scorecard, pre-pass
 *     briefing, debrief and every other sheet, saved as one record per
 *     filled copy, prefilled from the console (host.prefill / host.info).
 *  3. The workbook index — every sheet the tool offers, in workbook order.
 *
 * Records: kind "worksheet" entries; a step tick carries `check`, a form
 * `form` (smo_common/logbook/store.py). Everything is optimistic and
 * asynchronous: a tick never waits for the server before the row updates,
 * and the tool's own action is never blocked.
 *
 * The procedure card is a second surface on the SAME records (procard.js,
 * 2026-11-03: "the procedure cards become part of the logbook as they get
 * filled in"): useCard(proc) loads the card's checklist here, tick() /
 * capture() write it, subscribe() tells the card when ticks change (its
 * own, this tab's, the runner's). Prerequisites (cl.prereqs) are ticked
 * like steps with check.part = "pre".
 * ============================================================================ */

import { t, tText, getLang } from "/static/shared/i18n.js";
import { esc } from "/static/shared/components.js";
import { evalCheck, parseInlineCheck, runnerResults, runIds, nextRunId, ticksFor, progress,
  isDeviation } from "/static/shared/checklist.js";

const LIVE_MS = 2500;
const FORM_ORDER = ["anomaly", "handover", "scorecard", "briefing", "debrief"];

const resultLabel = (r) => ({
  pass: tText("PASS"), fail: tText("FAIL"), skip: tText("SKIPPED"), go: "GO", nogo: "NO-GO",
  done: tText("done"), open: tText("open"),
}[r] || r);
const formLabel = (k) => ({
  anomaly: tText("Anomaly ticket"), handover: tText("Handover"), scorecard: tText("GO/NO-GO scorecard"),
  briefing: tText("Pre-pass briefing"), debrief: tText("Debrief"),
}[k] || k);
const newLabel = (k) => ({
  anomaly: tText("New anomaly ticket"), handover: tText("New handover form"),
}[k] || tText("New copy"));

export function createWorkbook(host) {
  const W = {
    pane: null, proc: "", manualProc: "", cl: null, clKey: "", clErr: "", run: "", sheets: [],
    sheetsKey: "", open: new Set(), editing: {}, queue: new Map(), ids: new Map(),
    runnerSeen: new Set(), runnerKey: "", lastRunner: null, liveTimer: null, mmOpen: false, prefillCtx: {},
    pending: new Map(), subs: new Set(),
  };
  /* Tell the card surfaces (procard.js) that ticks or the checklist changed. */
  function notify() { for (const fn of W.subs) { try { fn(); } catch (e) { /* a card problem stays there */ } } }
  const $ = (sel, root) => (root || W.pane).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || W.pane).querySelectorAll(sel));
  const entries = () => host.entries() || [];
  const ctx = () => { try { return host.context() || {}; } catch (e) { return {}; } };

  /* ── data ─────────────────────────────────────────────────────────── */
  async function loadSheets(force) {
    const c = ctx();
    const wctx = {};
    for (const k of ["page", "procedure", "scenario", "alarm_id", "anomaly", "phase"]) {
      if (c[k] !== undefined && c[k] !== null && c[k] !== "") wctx[k] = c[k];
    }
    delete wctx.phase;
    const key = JSON.stringify([getLang(), wctx]);
    if (!force && key === W.sheetsKey) return false;
    W.sheetsKey = key;
    try {
      const j = await host.api("GET", `/worksheets?all=1&tool=${encodeURIComponent(host.tool)}` +
        `&lang=${getLang()}&context=${encodeURIComponent(JSON.stringify(wctx))}`);
      if (W.sheetsKey !== key) return false;
      W.sheets = j.worksheets || [];
    } catch (e) { W.sheets = []; }
    return true;
  }
  function currentProc() { return W.manualProc || String(ctx().procedure || ""); }
  async function loadChecklist(force) {
    const proc = currentProc();
    const key = `${proc}|${getLang()}`;
    if (!force && key === W.clKey) return false;
    W.clKey = key; W.clErr = ""; W.runnerKey = ""; W.runnerSeen.clear();
    if (!proc) { W.cl = null; return true; }
    try {
      const j = await host.api("GET", `/checklist?procedure=${encodeURIComponent(proc)}&lang=${getLang()}`);
      if (W.clKey !== key) return false;
      W.cl = j;
      const runs = runIds(entries(), j.sheet_id);
      W.run = runs.length ? runs[runs.length - 1] : "1";
      // A runner status that arrived during the fetch chose the run before
      // this line reset it, and a short card can finish before the fetch
      // returns (the console then stops polling): forget that choice and
      // re-apply the runner's last status, or the view stays on the
      // previous run while the ticks go to the new one.
      W.runnerKey = ""; W.runnerSeen.clear();
      const last = W.lastRunner;
      if (last && String(last.procedure_id || last.procedure_ref || "") === proc) {
        setTimeout(() => { if (W.cl === j) onRunner(last); }, 0);
      }
    } catch (e) {
      W.cl = null;
      W.clErr = proc;
    }
    notify();
    return true;
  }
  const sheet = (id) => W.sheets.find((w) => w.id === id);
  function formEntries(wid) {
    return entries().filter((e) => e.kind === "worksheet" && e.worksheet && e.worksheet.id === wid && e.form)
      .sort((a, b) => String(b.updated_ts || b.ts).localeCompare(String(a.updated_ts || a.ts)));
  }
  function answers(wid, qid) {
    return entries().filter((e) => e.kind === "worksheet" && e.worksheet && e.worksheet.id === wid &&
      e.worksheet.q === qid && !e.form && !e.check);
  }

  /* ── readings ─────────────────────────────────────────────────────── */
  function reading(param, pid) {
    try { return host.readParam ? host.readParam(param, pid) : null; } catch (e) { return null; }
  }
  function readingHtml(c, r) {
    if (!c.param && !c.pid) return "";
    if (!r || r.nodata) return `<span class="lv nd">${t("no data")}</span>`;
    const ok = evalCheck(c, r.raw);
    const mark = ok === true ? `<span class="okm" aria-label="${esc(tText("meets the check"))}">✓</span>`
      : ok === false ? `<span class="bad" aria-label="${esc(tText("does not meet the check"))}">✗</span>` : "";
    return `<span class="lv${r.stale ? " st" : ""}${ok === false ? " off" : ""}">` +
      `${esc(r.text)}${r.units ? " " + esc(r.units) : ""}${r.stale ? ` <i>${t("stale")}</i>` : ""} ${mark}</span>`;
  }
  function expectText(c) {
    if (!c.param) return c.text;
    if (c.op === "in" && c.set) return `${c.param} ∈ {${c.set.join(", ")}}`;
    if (c.op === "in") return `${c.param} ∈ [${c.lo}, ${c.hi}]`;
    if (c.op) return `${c.param} ${c.op === "==" ? "=" : c.op} ${c.value}`;
    return c.param;
  }

  /* ── checklist ────────────────────────────────────────────────────── */
  /** Ticks of the current run, with the optimistic ones not yet saved. */
  function ticks() {
    if (!W.cl) return {};
    const out = ticksFor(entries(), W.cl.sheet_id, W.run);
    for (const [k, fake] of W.pending) {
      const [sheet, run, key] = k.split("|");
      if (sheet === W.cl.sheet_id && run === W.run) out[key] = fake;
    }
    return out;
  }
  /** A card step or a Prerequisites item by key: {item, i, pre}. */
  function itemOf(key) {
    if (!W.cl) return null;
    const i = W.cl.steps.findIndex((x) => x.key === key);
    if (i >= 0) return { item: W.cl.steps[i], i, pre: false };
    const j = (W.cl.prereqs || []).findIndex((x) => x.key === key);
    return j >= 0 ? { item: W.cl.prereqs[j], i: j, pre: true } : null;
  }
  function stepState(tick) {
    if (!tick) return "open";
    return tick.check.result || (tick.worksheet && tick.worksheet.checked ? "done" : "open");
  }
  function mismatchText(m) {
    switch (m.kind) {
      case "count": return tText("The printed sheet has {{a}} steps; the card has {{b}}.", { a: m.n_sheet, b: m.n_card });
      case "row_unmatched": return tText("Printed row {{row}} is not on the card: {{text}}", { row: m.row, text: String(m.text || "").replace(/^\d+[a-z]?\.\s+/, "") });
      case "order": return tText("Printed row {{row}} is card step {{step}}, in a different order.", { row: m.row, step: m.step });
      case "command": return tText("Printed row {{row}} sends {{names}}; the card does not.", { row: m.row, names: (m.names || []).join(", ") });
      case "parameter": return tText("Printed row {{row}} checks {{names}}; the card does not.", { row: m.row, names: (m.names || []).join(", ") });
      case "step_unprinted": return tText("Card step {{step}} ({{title}}) is not on the printed sheet.", { step: m.step, title: m.title || "" });
      case "no_steps": return tText("The printed sheet is a status table, not a step list.");
      default: return m.detail || "";
    }
  }
  function stepHtml(s, i, tick) {
    const st = stepState(tick);
    const c = tick ? tick.check : null;
    const go = !!s.gonogo;
    const btn = (r, label, cls = "") => `<button type="button" id="wb-b-${esc(s.key)}-${r}" class="ds-btn sm${cls}" data-wb="tick" data-r="${r}"` +
      ` aria-pressed="${st === r}" aria-describedby="wb-st-${esc(s.key)}">${label}</button>`;
    const acts = go
      ? btn("go", "GO") + btn("nogo", "NO-GO") + btn("skip", t("Skip"))
      : btn("pass", t("Done"), " primary") + btn("fail", t("Failed")) + btn("skip", t("Skip"));
    const vals = (c && c.values) || [];
    const checks = (s.checks || []).map((ck, ci) => {
      const v = vals.find((x) => x.param && x.param === ck.param);
      const right = tick && st !== "open"
        ? (v ? `<span class="lv cap${v.ok === false ? " off" : ""}">${esc(v.value || "")}${v.units ? " " + esc(v.units) : ""}` +
            `${v.ok === true ? ' <span class="okm">✓</span>' : v.ok === false ? ' <span class="bad">✗</span>' : ""}</span>` : "")
        : `<span class="lvh" data-ci="${ci}">${readingHtml(ck, reading(ck.param, ck.pid))}</span>`;
      return `<li><span class="ex">${esc(ck.text)}</span>${right}</li>`;
    }).join("");
    const tcs = (s.tcs || []).length
      ? `<div class="tc"><span class="lbl">TC</span> ${s.tcs.map((x) => `<code>${esc(x)}</code>`).join(" ")}</div>` : "";
    const refs = (s.ref || []).map((r) => r.text).join(" · ");
    const when = tick && st !== "open"
      ? `<span class="tm">${esc(host.fmtTime(tick.updated_ts || tick.ts, true))}` +
        `${c.sim_ts ? ` · ${t("sim")} ${esc(String(c.sim_ts).replace(/^.*T/, "").replace(/Z$/, ""))}` : ""}` +
        `${c.position ? ` · ${esc(c.position)}` : ""}${c.source === "runner" ? ` · ${t("runner")}` : ""}</span>` : "";
    const label = s.n ? tText("Step {{n}}", { n: s.n }) : s.title;
    return `<li class="wb-st" data-key="${esc(s.key)}" data-i="${i}" data-state="${st}">` +
      `<div class="hd"><span class="n">${esc(s.n || "·")}</span>` +
      `<span class="ti" id="wb-st-${esc(s.key)}"><span class="ds-sr">${esc(label)}: </span>${esc(s.title)}</span>` +
      `<span class="res${isDeviation(st) ? " dev" : ""}">${st === "open" ? "" : esc(resultLabel(st))}</span></div>` +
      tcs + (checks ? `<ul class="ck">${checks}</ul>` : "") +
      (s.gonogo ? `<div class="go"><span class="lbl">GO/NO-GO</span> ${esc(s.gonogo)}</div>` : "") +
      (!checks && !s.gonogo && (s.actions || []).length ? `<div class="go">${esc(s.actions[0])}</div>` : "") +
      (refs ? `<div class="pr" title="${esc(refs)}"><span class="lbl">${t("Printed")}</span> ${esc(refs)}</div>` : "") +
      `<div class="act">${acts}${when}</div>` +
      `<div class="nt"><label class="ds-sr" for="wb-nt-${esc(s.key)}">${t("Note or deviation for {{step}}", { step: label })}</label>` +
      // a box that wraps: a runner note ("Runner: one S3.27 request…") or
      // a long deviation note must be readable, not cut at the field edge
      `<textarea id="wb-nt-${esc(s.key)}" class="ds-input wb-note" maxlength="2000" ` +
      `rows="${Math.min(4, Math.max(1, Math.ceil(String((c && c.note) || "").length / 56)))}" ` +
      `placeholder="${esc(tText("Note or deviation (Enter saves)"))}">${esc((c && c.note) || "")}</textarea></div></li>`;
  }
  function prereqHtml(tk) {
    const ps = (W.cl && W.cl.prereqs) || [];
    if (!ps.length) return "";
    const done = ps.filter((p) => tk[p.key] && stepState(tk[p.key]) !== "open").length;
    return `<div class="wb-pres"><div class="lbl">${t("Prerequisites")} · ${t("{{done}} of {{total}}", { done, total: ps.length })}</div>` +
      `<ul>${ps.map((p) => {
        const tick = tk[p.key];
        const on = !!tick && stepState(tick) !== "open";
        const ck = (p.checks || [])[0];
        const live = ck && !on ? ` <span class="lvh" data-pre="${esc(p.key)}">${readingHtml(ck, reading(ck.param, ck.pid))}</span>` : "";
        const v = on && tick.check.values && tick.check.values[0];
        const cap = v ? ` <span class="lv cap${v.ok === false ? " off" : ""}">${esc(v.value || "")}${v.units ? " " + esc(v.units) : ""}</span>` : "";
        return `<li class="wb-pre" data-key="${esc(p.key)}" data-state="${on ? "done" : "open"}">` +
          `<label class="ds-check"><input type="checkbox" data-wb="pre"${on ? " checked" : ""}> ` +
          `<span><span class="n">${esc(p.n)}</span> ${esc(p.text)}</span></label>${live}${cap}</li>`;
      }).join("")}</ul></div>`;
  }
  function checklistHtml() {
    const proc = currentProc();
    if (!proc) return "";
    if (!W.cl) {
      return W.clErr ? `<div class="wb-cl-empty">${t("No checklist for {{proc}}: this card has no steps.", { proc: W.clErr })}</div>` : "";
    }
    const cl = W.cl;
    const tk = ticks();
    const pr = progress(cl.steps, tk);
    const runs = runIds(entries(), cl.sheet_id);
    if (!runs.includes(W.run)) runs.push(W.run);
    const runSel = `<label class="ds-sr" for="wb-run">${t("Run")}</label><select id="wb-run" class="ds-select sm">` +
      runs.map((r) => `<option value="${esc(r)}"${r === W.run ? " selected" : ""}>${esc(tText("Run {{n}}", { n: r }))}</option>`).join("") +
      `</select><button type="button" class="ds-btn ghost sm" data-wb="new-run">${t("New run")}</button>`;
    const mm = cl.mismatches || [];
    const mmHtml = mm.length
      ? `<details class="wb-mm"${W.mmOpen ? " open" : ""}><summary>` +
        `<svg aria-hidden="true" width="12" height="12"><use href="/static/shared/glyphs.svg#g-warn-up"></use></svg> ` +
        `${t("The printed sheet differs from the card ({{n}})", { n: mm.length })}</summary>` +
        `<p>${t("The checklist follows the card, which is what is executed. The printed rows are shown as a reference.")}</p>` +
        `<ul>${mm.map((m) => `<li>${esc(mismatchText(m))}</li>`).join("")}</ul></details>` : "";
    const extra = (cl.extra || []).length
      ? `<div class="wb-extra"><div class="lbl">${t("Also on the printed sheet")}</div>` +
        formHtml({ id: cl.sheet_id, title: cl.sheet_title, questions: cl.extra }, extraEntry(), { extra: true }) + `</div>` : "";
    return `<section class="wb-cl" aria-labelledby="wb-cl-h">` +
      `<div class="wb-clh"><h3 id="wb-cl-h"><span class="id">${esc(cl.procedure)}</span> ${esc(cl.name || cl.title)}</h3>` +
      (W.manualProc ? `<button type="button" class="ds-btn ghost sm" data-wb="close-cl" aria-label="${esc(tText("Close this checklist"))}">✕</button>` : "") +
      `</div>` +
      `<div class="wb-meta"><span class="pg" role="status">${t("{{done}} of {{total}} steps", { done: pr.done, total: pr.total })}` +
      `${pr.deviations ? ` · <b class="dev">${t("{{count}} deviation", { count: pr.deviations, plural: "{{count}} deviations" })}</b>` : ""}</span>` +
      `<span class="rn">${runSel}</span></div>` +
      `<div class="wb-src">${t("From the procedure card")}${cl.runnable ? " · " + t("the runner ticks steps as it completes them") : ""}` +
      `${cl.sheet_title ? ` · ${t("printed sheet")} <span class="id">${esc(cl.sheet_id)}</span>` : ""}</div>` +
      mmHtml + prereqHtml(tk) +
      `<ol class="wb-steps" aria-label="${esc(tText("Checklist steps"))}">${cl.steps.map((s, i) => stepHtml(s, i, tk[s.key])).join("")}</ol>` +
      extra +
      `<div class="wb-sheet-dl">${sheetDownloads(cl.sheet_id)}</div>` +
      `</section>`;
  }
  function extraEntry() {
    if (!W.cl) return null;
    return formEntries(W.cl.sheet_id).find((e) => (e.form.instance || "") === `run-${W.run}`) || null;
  }
  function sheetDownloads(wid) {
    const q = host.exportQuery();
    return `<a class="ds-btn ghost sm" data-wb="dl" href="${host.API}/export?format=md&sheet=${encodeURIComponent(wid)}&${q}" download>${t("This sheet (.md)")}</a>` +
      `<a class="ds-btn ghost sm" data-wb="dl" href="${host.API}/export?format=html&sheet=${encodeURIComponent(wid)}&${q}" download>${t("This sheet (printable)")}</a>` +
      `<button type="button" class="ds-btn ghost sm" data-wb="copy-sheet" data-w="${esc(wid)}">${t("Copy as Markdown")}</button>`;
  }

  function captureValues(s) {
    const out = [];
    for (const ck of s.checks || []) {
      if (!ck.param && !ck.pid) continue;
      const r = reading(ck.param, ck.pid);
      const v = { param: ck.param || ck.pid, expect: expectText(ck) };
      if (ck.pid) v.pid = ck.pid;
      if (r && !r.nodata) {
        v.value = r.text; if (r.units) v.units = r.units;
        const ok = evalCheck(ck, r.raw);
        if (ok !== null) v.ok = ok;
        if (r.stale) v.stale = true;
      } else if (!host.hasReadings || host.hasReadings()) v.value = tText("no data");
      // a tool without live TM (documentation viewer) records the expectation only
      out.push(v);
    }
    return out;
  }
  function tickText(s, result, values, note, pre) {
    const head = pre
      ? `${tText("Prerequisite {{n}}", { n: s.n })} · ${s.text} — ${resultLabel(result)}`
      : `${s.n ? tText("Step {{n}}", { n: s.n }) + " · " : ""}${s.title} — ${resultLabel(result)}`;
    const vals = values.filter((v) => v.value).map((v) => `${v.param} = ${v.value}${v.units ? " " + v.units : ""}` +
      `${v.ok === false ? " ✗" : ""} (${tText("expected")} ${v.expect})`);
    return [head, ...vals, note ? `${tText("Note")}: ${note}` : ""].filter(Boolean).join("\n");
  }

  /** Record a step result. Optimistic: the row changes now; the write is
   *  queued per step so ticks and notes never race each other.
   *  result: pass | fail | skip | go | nogo | done | open, or
   *    "note"    keep the result and the captured values, save the note;
   *    "capture" keep the result, record the live values now (procard.js).
   *  opts: {note, source, runnerRun, runnerNote}. */
  function tick(key, result, opts = {}) {
    if (!W.cl) return Promise.resolve();
    const cl = W.cl, run = W.run;
    const it = itemOf(key);
    if (!it) return Promise.resolve();
    const s = it.item, i = it.i, pre = it.pre;
    const prev = ticks()[key];
    const c = ctx();
    const noteEl = W.pane && $(`.wb-st[data-key="${CSS.escape(key)}"] .wb-note`);
    const note = (opts.note !== undefined ? opts.note : (noteEl ? noteEl.value.trim() : (prev && prev.check.note) || ""))
      || opts.runnerNote || "";      // where the activity did the step differently (runner_step_map.yaml)
    const keepRes = result === "note" || result === "capture";
    const res = keepRes ? (prev ? stepState(prev) : "open") : result;
    const prevVals = (prev && prev.check.values) || [];
    // Values: "capture" records them now; "note" keeps them; a result keeps
    // values captured on an OPEN step (the operator captured, then decided);
    // otherwise a result captures them at the tick, as before.
    const values = result === "capture" ? captureValues(s)
      : result === "note" ? prevVals
      : res === "open" ? (prev && stepState(prev) === "open" ? prevVals : [])
      : (prev && stepState(prev) === "open" && prevVals.length ? prevVals : captureValues(s));
    const simTs = c.sim_ts ? String(c.sim_ts) : "";
    const label = pre ? s.n : (s.n || "");
    const check = {
      procedure: cl.procedure, step: label, key, order: i, title: pre ? s.text.slice(0, 300) : s.title, run,
      result: res, source: opts.source || "operator", position: c.position || "",
      sim_ts: result === "note" && prev ? (prev.check.sim_ts || simTs) : simTs, note, values,
      ...(pre ? { part: "pre" } : {}),
      ...(!pre && s.gonogo ? { gonogo: s.gonogo.slice(0, 280) } : {}),
      ...(opts.runnerRun || W.runnerKey ? { runner_run: opts.runnerRun || W.runnerKey } : {}),
    };
    const text = tickText(s, res, values, note, pre);
    const idKey = `${cl.sheet_id}|${run}|${key}`;
    const id = W.ids.get(idKey) || (prev && prev.id && !prev.pending ? prev.id : "");
    const checked = res !== "open" && !isDeviation(res);
    // optimistic: this tab's row and every card surface change now
    W.pending.set(idKey, { id: id || "", pending: true, ts: new Date().toISOString(),
      updated_ts: new Date().toISOString(), check, worksheet: { id: cl.sheet_id, q: key, instance: run, checked } });
    const rowEl = W.pane && $(`.wb-st[data-key="${CSS.escape(key)}"], .wb-pre[data-key="${CSS.escape(key)}"]`);
    if (rowEl) {
      rowEl.dataset.state = res;
      const r = $(".res", rowEl);
      if (r) { r.textContent = res === "open" ? "" : resultLabel(res); r.classList.toggle("dev", isDeviation(res)); }
      for (const b of $$('[data-wb="tick"]', rowEl)) b.setAttribute("aria-pressed", String(b.dataset.r === res));
      const cb = $('input[type="checkbox"]', rowEl);
      if (cb) cb.checked = res !== "open";
    }
    notify();
    const job = async () => {
      const known = W.ids.get(idKey) || id;
      try {
        let saved = null;
        if (known) {
          saved = await host.api("PATCH", `/entries/${encodeURIComponent(known)}`, { text, checked, check });
        } else {
          const qText = pre ? `${tText("Prerequisite {{n}}", { n: s.n })} — ${s.text}`
            : `${s.n ? tText("Step {{n}}", { n: s.n }) + " — " : ""}${s.title}`;
          const body = {
            kind: "worksheet", tool: host.tool, lang: getLang(), text,
            context: { ...host.cleanContext(c), procedure: cl.procedure, step: label || key },
            worksheet: { id: cl.sheet_id, q: key, title: cl.sheet_title || `${cl.procedure} ${cl.name || cl.title}`,
              q_text: qText.slice(0, 1000), checked, instance: run },
            check,
          };
          if (simTs) body.sim_ts = simTs;
          const e = await host.api("POST", "/entries", body);
          if (e && e.id) W.ids.set(idKey, e.id);
          saved = e;
        }
        // until the logbook's next read has it, the saved record stands in
        const p = W.pending.get(idKey);
        if (p && p.check === check) {
          W.pending.set(idKey, saved && saved.check ? { ...saved, saved: true } : { ...p, saved: true });
        }
        if (opts.source !== "runner") {
          const who = pre ? s.n : (s.n || s.title);
          host.announce(result === "capture" ? tText("Values captured for {{n}}", { n: who })
            : res === "open" ? tText("Step {{n}} cleared", { n: who })
            : tText("Step {{n}}: {{r}}", { n: who, r: resultLabel(res) }));
        }
      } catch (e) {
        W.pending.delete(idKey);
        notify();
        host.announce(tText("Not saved: {{why}}", { why: e.message }));
        throw e;
      }
    };
    const chain = (W.queue.get(key) || Promise.resolve()).then(job);
    W.queue.set(key, chain.catch(() => {}));
    chain.then(() => host.refreshSoon(), () => {});
    return chain.catch(() => {});
  }

  /** The MCS runner's status (procedure_runner.status()). Ticks the card
   *  steps whose runner steps are all final. Cheap when nothing changed. */
  function onRunner(st) {
    if (!st) return;
    const proc = String(st.procedure_id || st.procedure_ref || "");
    if (!proc) return;
    W.lastRunner = st;
    if (!W.cl || W.cl.procedure !== proc) {
      // the panel may be closed: fetch the checklist, then apply this status
      if (currentProc() === proc && W.clKey !== `${proc}|${getLang()}`) {
        loadChecklist(false).then(() => { if (W.cl && W.cl.procedure === proc) onRunner(st); });
      }
      return;
    }
    if (!Array.isArray(W.cl.runner_map)) return;
    // One runner load = one checklist run (loaded_at identifies the load):
    // its ticks carry it, so a page reload finds the run again, and a new
    // load starts a new run once the current one already has ticks.
    const rk = st.loaded_at !== undefined && st.loaded_at !== null ? String(st.loaded_at) : "";
    if (rk && rk !== W.runnerKey) {
      const mine = entries().find((e) => e.check && e.worksheet && e.worksheet.id === W.cl.sheet_id &&
        e.check.runner_run === rk);
      const prevRun = W.run;
      if (mine) W.run = String(mine.worksheet.instance || mine.check.run || W.run);
      else if (Object.keys(ticks()).length) W.run = nextRunId(entries(), W.cl.sheet_id);
      W.runnerKey = rk;
      W.runnerSeen.clear();
      if (W.run !== prevRun) render();
    }
    const res = runnerResults(W.cl.runner_map, st.step_results || [],
      W.cl.steps.filter((s) => s.gonogo).map((s) => s.key));
    const tk = ticks();
    for (const [key, r] of Object.entries(res)) {
      const seen = `${W.run}|${key}`;
      if (W.runnerSeen.has(seen)) continue;
      W.runnerSeen.add(seen);
      if (tk[key] && stepState(tk[key]) !== "open") continue;   // the operator's tick stands
      tick(key, r, { source: "runner", runnerRun: rk, runnerNote: (W.cl.runner_notes || {})[key] || "" });
    }
  }

  /* ── forms ────────────────────────────────────────────────────────── */
  function prefillFor(w, q) {
    if (!q.prefill || !host.prefill) return "";
    try { return host.prefill(q.prefill, { ...ctx(), ...W.prefillCtx }, w) || ""; } catch (e) { return ""; }
  }
  function formHtml(w, entry, opts = {}) {
    const fields = entry && entry.form ? entry.form.fields || [] : [];
    const fieldOf = (qid) => fields.find((f) => f.q === qid);
    let info = entry && entry.form ? entry.form.info || [] : [];
    if (!entry && host.info && w.form) {
      try { info = host.info(w.form, { ...ctx(), ...W.prefillCtx }, w) || []; } catch (e) { info = []; }
    }
    const fid = (q) => `wbf-${w.id}-${q.id}${opts.extra ? "-x" : ""}`.replace(/[^\w-]/g, "_");
    let sec = "";
    // step rows belong to the live checklist in the MCS; elsewhere the
    // printed sheet is worked row by row, so they stay in the form
    const body = (w.questions || []).filter((q) => opts.extra || !q.step || host.tool !== "mcs").map((q) => {
      const f = fieldOf(q.id);
      const pre = !entry ? prefillFor(w, q) : "";
      const val = f ? (f.value || "") : pre;
      const isPre = f ? !!f.prefilled : !!pre;
      const prev = answers(w.id, q.id).map((a) => `<div class="qa"><span class="tm">${esc(host.fmtTime(a.ts))}</span> ${esc(a.text)}</div>`).join("");
      let h = "";
      if (q.section && q.section !== sec && !(w.instances && /—/.test(q.section))) {
        sec = q.section; h += `<div class="qs">${esc(sec)}</div>`;
      }
      const preChip = isPre ? `<span class="pre" title="${esc(tText("Filled in from the console; check and edit it"))}">${t("from console")}</span>` : "";
      if (q.kind === "check") {
        const ic = parseInlineCheck(q.text);
        const r = ic ? reading(ic.param, ic.pid) : null;
        const live = ic ? `<div class="qh">${t("Console")}: ${readingHtml(ic, r)}</div>` : "";
        return h + `<div class="lb-q wb-q" data-q="${esc(q.id)}" data-kind="check">` +
          `<label class="ds-check wb-chk"><input type="checkbox" id="${fid(q)}-c"${f && f.checked ? " checked" : ""}> <span>${esc(q.text)}</span></label>` +
          (q.hint ? `<div class="qh">${t("Expected:")} ${esc(q.hint)}</div>` : "") + live + prev +
          `<label class="ds-sr" for="${fid(q)}">${t("Note")}</label>` +
          `<input id="${fid(q)}" class="ds-input wb-in" maxlength="4000" value="${esc(val)}" placeholder="${esc(tText("Note or actual value (optional)"))}">${preChip}</div>`;
      }
      // a long (or long prefilled) answer gets a box that wraps: a one-line
      // field hid most of a prefilled pass or alarm line
      const long = /[?？]\s*$/.test(q.text) || q.text.length > 90 || String(val || "").length > 44 ||
        /actions|hypothes|reason|why|conflict|ordre|notes?\b/i.test(q.text);
      const input = long
        ? `<textarea id="${fid(q)}" class="lb-ta sm wb-in" maxlength="4000">${esc(val)}</textarea>`
        : `<input id="${fid(q)}" class="ds-input wb-in" maxlength="4000" value="${esc(val)}">`;
      return h + `<div class="lb-q wb-q" data-q="${esc(q.id)}" data-kind="text">` +
        `<label class="qt" for="${fid(q)}">${esc(q.text)}</label>` +
        (q.hint ? `<div class="qh">${esc(q.hint)}</div>` : "") + prev + input + preChip + `</div>`;
    }).join("");
    const infoHtml = info.length ? `<ul class="wb-info">${info.map((i) =>
      `<li><span class="k">${esc(i.label)}</span> <span class="v">${esc(i.value)}</span></li>`).join("")}</ul>` : "";
    const inst = entry ? (entry.form.instance || "") : "";
    return `<div class="wb-form" data-w="${esc(w.id)}" data-e="${esc(entry ? entry.id : "")}"` +
      ` data-inst="${esc(inst)}"${opts.extra ? ' data-extra="1"' : ""}>` + infoHtml + body +
      `<div class="lb-row"><button type="button" class="ds-btn primary sm" data-wb="form-save">` +
      `${entry ? t("Save changes") : t("Save sheet")}</button>` +
      (!opts.extra ? `<button type="button" class="ds-btn ghost sm" data-wb="form-close">${t("Close")}</button>` : "") +
      `<span class="wb-st-msg" role="status"></span></div></div>`;
  }
  function formStatus(w) {
    const n = formEntries(w.id).length;
    if (n) return w.instances ? tText("{{n}} filed", { n }) : tText("saved {{t}}", { t: host.fmtTime(formEntries(w.id)[0].updated_ts || formEntries(w.id)[0].ts) });
    const a = entries().filter((e) => e.kind === "worksheet" && e.worksheet && e.worksheet.id === w.id).length;
    return a ? tText("{{count}} answer", { count: a, plural: "{{count}} answers" }) : tText("not started");
  }
  function sheetBlockHtml(w) {
    // only the MCS has live checklists (see the "ix" handler)
    const isList = host.tool === "mcs" && (w.questions || []).some((q) => q.step) && (w.applies.procedures || []).length;
    const filed = formEntries(w.id);
    const ed = W.editing[w.id];
    let inner;
    if (isList) {
      inner = `<p class="lb-hint">${t("A confirm-each-step sheet: work it as the live checklist of its procedure card.")}</p>` +
        `<div class="lb-row">${(w.applies.procedures || []).map((p) =>
          `<button type="button" class="ds-btn sm" data-wb="open-cl" data-proc="${esc(p)}">${t("Open the {{proc}} checklist", { proc: p })}</button>`).join("")}</div>`;
    } else {
      const list = filed.length ? `<ul class="wb-filed">${filed.map((e) =>
        `<li><span class="tm">${esc(host.fmtTime(e.updated_ts || e.ts))}</span> ` +
        `<span class="v">${esc(e.form.instance || (e.text || "").split("\n")[0].slice(0, 80))}</span>` +
        `<button type="button" class="ds-btn ghost sm" data-wb="form-edit" data-e="${esc(e.id)}">${t("Edit")}</button></li>`).join("")}</ul>` : "";
      let form = "";
      if (ed === "new" || (ed === undefined && !filed.length && W.open.has(w.id))) form = formHtml(w, null);
      else if (ed) {
        const e = filed.find((x) => x.id === ed);
        form = e ? formHtml(w, e) : "";
      }
      const newBtn = (w.instances || !filed.length) && ed !== "new" && !(ed === undefined && !filed.length && W.open.has(w.id))
        ? `<button type="button" class="ds-btn sm" data-wb="form-new">${esc(w.instances ? newLabel(w.form) : tText("Fill in"))}</button>` : "";
      inner = list + form + (newBtn ? `<div class="lb-row">${newBtn}</div>` : "") + `<div class="wb-sheet-dl">${sheetDownloads(w.id)}</div>`;
    }
    return `<details class="ds-disclosure lb-ws wb-sheet" data-w="${esc(w.id)}"${W.open.has(w.id) ? " open" : ""}>` +
      `<summary><span class="id">${esc(w.id)}</span> <span class="ti">${esc(w.title)}</span>` +
      `<span class="r">${esc(isList ? "" : formStatus(w))}</span></summary><div class="bd">${inner}</div></details>`;
  }
  function quickHtml() {
    const kinds = [];
    for (const k of FORM_ORDER) {
      const cands = W.sheets.filter((w) => w.form === k);
      if (!cands.length) continue;
      const best = cands.find((w) => w.match && w.match !== "general") || cands.find((w) => w.match) || cands[0];
      kinds.push([k, best]);
    }
    if (!kinds.length) return "";
    return `<div class="wb-quick" role="group" aria-label="${esc(tText("Workbook forms"))}">` +
      kinds.map(([k, w]) => `<button type="button" class="ds-btn sm" data-wb="quick" data-w="${esc(w.id)}" ` +
        `title="${esc(w.id + " — " + w.title)}">${esc(formLabel(k))}</button>`).join("") + `</div>`;
  }
  function hereSheets() {
    const clSheet = W.cl ? W.cl.sheet_id : "";
    return W.sheets.filter((w) => w.id !== clSheet &&
      ((w.match && w.match !== "general") || W.open.has(w.id) || W.editing[w.id] !== undefined));
  }
  function indexHtml() {
    if (!W.sheets.length) return "";
    const rows = W.sheets.map((w) => `<li><button type="button" class="wb-ix" data-wb="ix" data-w="${esc(w.id)}">` +
      `<span class="id">${esc(w.id)}</span> <span class="ti">${esc(w.title)}</span></button></li>`).join("");
    return `<details class="wb-index"><summary>${t("All workbook sheets ({{n}})", { n: W.sheets.length })}</summary>` +
      `<ol>${rows}</ol></details>`;
  }

  /* ── render ───────────────────────────────────────────────────────── */
  function snapshotInputs() {
    // typed but unsaved values survive a re-render
    const snap = {};
    if (!W.pane) return snap;
    for (const el of $$("input.wb-in, textarea.wb-in, input[type=checkbox], .wb-note")) {
      // only what the person changed: a saved value re-renders from the record
      if (!el.id) continue;
      if (el.type === "checkbox" ? el.checked !== el.defaultChecked : el.value !== el.defaultValue) {
        snap[el.id] = el.type === "checkbox" ? el.checked : el.value;
      }
    }
    const a = document.activeElement;
    snap.__focus = a && W.pane.contains(a) ? a.id || "" : "";
    snap.__sel = a && typeof a.selectionStart === "number" ? [a.selectionStart, a.selectionEnd] : null;
    const sc = W.pane.closest(".lb-body");
    snap.__top = sc ? sc.scrollTop : 0;
    return snap;
  }
  function restoreInputs(snap) {
    for (const [id, v] of Object.entries(snap)) {
      if (id.startsWith("__")) continue;
      const el = document.getElementById(id);
      if (!el || !W.pane.contains(el)) continue;
      if (el.type === "checkbox") el.checked = v; else el.value = v;
    }
    const sc = W.pane.closest(".lb-body");
    if (sc) sc.scrollTop = snap.__top || 0;
    if (snap.__focus) {
      const f = document.getElementById(snap.__focus);
      if (f) {
        f.focus({ preventScroll: true });
        if (snap.__sel && typeof f.setSelectionRange === "function") {
          try { f.setSelectionRange(snap.__sel[0], snap.__sel[1]); } catch (e) { /* not a text field */ }
        }
      }
    }
  }
  function render() {
    if (!W.pane) return;
    const snap = snapshotInputs();
    const here = hereSheets();
    W.pane.innerHTML =
      checklistHtml() +
      quickHtml() +
      (here.length ? `<div class="wb-here"><div class="lb-sep">${t("Sheets for this context")}</div>${here.map(sheetBlockHtml).join("")}</div>` : "") +
      (!currentProc() && !here.length
        ? `<p class="lb-empty">${host.tool === "mcs"
          ? t("Open or start a procedure to get its checklist here, or pick a sheet below. Everything you fill in is saved to your logbook.")
          : t("Pick a sheet below. Everything you fill in is saved to your logbook.")}</p>` : "") +
      indexHtml();
    restoreInputs(snap);
    host.onCount(here.length + (W.cl ? 1 : 0));
  }
  /** Data changed (refresh): update in place when the structure is the same. */
  function onData() {
    // the logbook re-read its entries: saved ticks are in them now
    for (const [k, p] of W.pending) if (p.saved) W.pending.delete(k);
    notify();
    if (!W.pane || !W.pane.firstChild || (W.pane.closest && W.pane.closest("[hidden]"))) return;
    render();
  }
  async function sync(force) {
    const a = await loadSheets(force);
    const b = await loadChecklist(force);
    if (a || b || force) render();
  }
  function liveTick() {
    if (!W.pane || W.pane.hidden || !W.cl) return;
    for (const span of $$(".lvh[data-pre]")) {
      const p = (W.cl.prereqs || []).find((x) => x.key === span.dataset.pre);
      const ck = p && (p.checks || [])[0];
      if (ck) span.innerHTML = readingHtml(ck, reading(ck.param, ck.pid));
    }
    for (const li of $$(".wb-st")) {
      if (li.dataset.state !== "open") continue;
      const s = W.cl.steps[Number(li.dataset.i)];
      if (!s) continue;
      for (const span of $$(".lvh", li)) {
        const ck = s.checks[Number(span.dataset.ci)];
        if (ck) span.innerHTML = readingHtml(ck, reading(ck.param, ck.pid));
      }
    }
  }

  async function saveForm(el) {
    const wid = el.dataset.w;
    const extra = el.dataset.extra === "1";
    const w = extra && W.cl ? { id: W.cl.sheet_id, title: W.cl.sheet_title, questions: W.cl.extra } : sheet(wid);
    if (!w) return false;
    const fields = [];
    const lines = [];
    for (const qel of $$(".wb-q", el)) {
      const q = (w.questions || []).find((x) => x.id === qel.dataset.q);
      const inp = $(".wb-in", qel);
      const cb = $('input[type="checkbox"]', qel);
      const v = inp ? inp.value.trim() : "";
      const f = { q: qel.dataset.q };
      if (v) f.value = v;
      if (cb) f.checked = cb.checked;
      if ($(".pre", qel) && v) f.prefilled = true;
      if (f.value !== undefined || f.checked) {
        fields.push(f);
        lines.push(`${q ? q.text : f.q}: ${cb ? (cb.checked ? "☑ " : "☐ ") : ""}${v}`.trim());
      }
    }
    const msg = $(".wb-st-msg", el);
    if (!fields.length) { msg.textContent = tText("Nothing filled in yet."); return false; }
    const info = Array.from(el.querySelectorAll(".wb-info li")).map((li) =>
      ({ label: $(".k", li).textContent, value: $(".v", li).textContent }));
    let inst = el.dataset.inst || "";
    if (!inst && extra) inst = `run-${W.run}`;          // language-neutral: matched back by extraEntry
    if (!inst && w.instances) {
      const idq = (w.questions || []).find((q) => q.prefill === "ticket_id");
      const ff = idq && fields.find((x) => x.q === idq.id);
      inst = (ff && ff.value) || (w.form === "handover" ? (ctx().position || "") : "") ||
        `${w.id.replace(/^WB-/, "")}-${formEntries(w.id).length + 1}`;
    }
    const form = { fields, ...(info.length ? { info } : {}), ...(inst ? { instance: inst } : {}) };
    const text = [`${w.id} ${w.title || ""}${inst ? ` — ${inst}` : ""}`.trim(), ...lines].join("\n").slice(0, 7900);
    const btn = $('[data-wb="form-save"]', el);
    btn.setAttribute("aria-disabled", "true");
    try {
      if (el.dataset.e) {
        await host.api("PATCH", `/entries/${encodeURIComponent(el.dataset.e)}`, { text, form });
      } else {
        const c = ctx();
        const body = { kind: "worksheet", tool: host.tool, lang: getLang(), text, context: host.cleanContext(c),
          worksheet: { id: w.id, q: "form", title: w.title, q_text: inst || w.title, ...(inst ? { instance: inst } : {}) },
          form };
        if (c.sim_ts) body.sim_ts = String(c.sim_ts);
        await host.api("POST", "/entries", body);
      }
      host.announce(tText("{{id}} saved to your logbook", { id: w.id }));
      if (!extra) { delete W.editing[w.id]; }
      W.prefillCtx = {};
      await host.refresh();
      render();
      const d = W.pane.querySelector(`details.wb-sheet[data-w="${CSS.escape(w.id)}"] summary`);
      if (d && !extra && W.pane.contains(el) === false && W.pane.offsetParent !== null) d.focus();
      return true;
    } catch (e) {
      msg.textContent = tText("Not saved: {{why}}", { why: e.message });
      return false;
    } finally { btn.removeAttribute("aria-disabled"); }
  }

  /** Open a sheet's form now (an alarm's "Ticket" button, the quick row). */
  function openForm(idOrKind, prefillCtx = {}) {
    const w = sheet(idOrKind) || (() => {
      const cands = W.sheets.filter((x) => x.form === idOrKind);
      return cands.find((x) => x.match && x.match !== "general") || cands[0];
    })();
    if (!w) return false;
    W.prefillCtx = prefillCtx || {};
    W.open.add(w.id);
    W.editing[w.id] = "new";
    if (!w.instances && formEntries(w.id).length) W.editing[w.id] = formEntries(w.id)[0].id;
    render();
    const d = W.pane.querySelector(`details.wb-sheet[data-w="${CSS.escape(w.id)}"]`);
    if (d) {
      d.scrollIntoView({ block: "start" });
      const f = d.querySelector(".wb-in, input[type=checkbox]");
      if (f) setTimeout(() => f.focus(), 20);
    }
    return true;
  }
  function openChecklist(proc) {
    W.manualProc = proc || "";
    W.clKey = "";
    sync(false).then(() => {
      const h = W.pane && $("#wb-cl-h"); if (h) { h.tabIndex = -1; h.focus(); }
    });
  }

  /* ── events ───────────────────────────────────────────────────────── */
  function wire(pane) {
    pane.addEventListener("click", (ev) => {
      const el = ev.target.closest("[data-wb]");
      if (!el || !pane.contains(el)) return;
      if (el.getAttribute("aria-disabled") === "true") { ev.preventDefault(); return; }
      const a = el.dataset.wb;
      const li = el.closest(".wb-st");
      if (a === "tick" && li) {
        const cur = li.dataset.state;
        tick(li.dataset.key, cur === el.dataset.r ? "open" : el.dataset.r);
      } else if (a === "new-run" && W.cl) {
        newRun();
      } else if (a === "close-cl") { W.manualProc = ""; W.clKey = ""; sync(false); }
      else if (a === "open-cl") openChecklist(el.dataset.proc);
      else if (a === "quick" || a === "ix") {
        const w = sheet(el.dataset.w);
        // a confirm-each-step sheet is the live checklist where the tool runs
        // procedures (the MCS serves /api/logbook/checklist); elsewhere (radio,
        // orbit tools) it opens as the printed sheet, row by row
        if (host.tool === "mcs" && w && (w.questions || []).some((q) => q.step) && (w.applies.procedures || []).length) {
          openChecklist(w.applies.procedures[0]);
        } else if (a === "quick") openForm(el.dataset.w);
        else { W.open.add(el.dataset.w); render(); const d = pane.querySelector(`details.wb-sheet[data-w="${CSS.escape(el.dataset.w)}"] summary`); if (d) { d.scrollIntoView({ block: "start" }); d.focus(); } }
      } else if (a === "form-new") {
        const d = el.closest("details.wb-sheet"); W.editing[d.dataset.w] = "new"; W.open.add(d.dataset.w); render();
        const f = pane.querySelector(`details.wb-sheet[data-w="${CSS.escape(d.dataset.w)}"] .wb-in`); if (f) f.focus();
      } else if (a === "form-edit") {
        const d = el.closest("details.wb-sheet"); W.editing[d.dataset.w] = el.dataset.e; render();
        const f = pane.querySelector(`details.wb-sheet[data-w="${CSS.escape(d.dataset.w)}"] .wb-in`); if (f) f.focus();
      } else if (a === "form-close") {
        const d = el.closest("details.wb-sheet"); delete W.editing[d.dataset.w]; W.prefillCtx = {}; render();
        const s = pane.querySelector(`details.wb-sheet[data-w="${CSS.escape(d.dataset.w)}"] summary`); if (s) s.focus();
      } else if (a === "form-save") saveForm(el.closest(".wb-form"));
      else if (a === "copy-sheet") host.copyMarkdown(el.dataset.w);
      else if (a === "dl") host.afterDownload();
    });
    pane.addEventListener("toggle", (ev) => {
      const d = ev.target;
      if (d.matches && d.matches("details.wb-sheet")) {
        if (d.open) W.open.add(d.dataset.w); else W.open.delete(d.dataset.w);
      } else if (d.matches && d.matches("details.wb-mm")) W.mmOpen = d.open;
    }, true);
    pane.addEventListener("change", (ev) => {
      if (ev.target.id === "wb-run") { W.run = ev.target.value; W.runnerSeen.clear(); render(); notify(); }
      const pre = ev.target.dataset && ev.target.dataset.wb === "pre" && ev.target.closest(".wb-pre");
      if (pre) tick(pre.dataset.key, ev.target.checked ? "done" : "open");
    });
    pane.addEventListener("keydown", (ev) => {
      const t = ev.target;
      if (t.classList && t.classList.contains("wb-note") && ev.key === "Enter" && !ev.shiftKey) {
        ev.preventDefault();
        const li = t.closest(".wb-st");
        tick(li.dataset.key, "note", { note: t.value.trim() });
      }
      if (t.closest && t.closest(".wb-form") && ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) {
        ev.preventDefault(); saveForm(t.closest(".wb-form"));
      }
    });
    pane.addEventListener("focusout", (ev) => {
      const t = ev.target;
      if (!(t.classList && t.classList.contains("wb-note"))) return;
      const li = t.closest(".wb-st");
      const prev = W.cl && ticksFor(entries(), W.cl.sheet_id, W.run)[li.dataset.key];
      if (t.value.trim() !== ((prev && prev.check.note) || "") && (prev || t.value.trim())) {
        tick(li.dataset.key, "note", { note: t.value.trim() });
      }
    });
  }

  function newRun() {
    if (!W.cl) return;
    W.run = nextRunId(entries(), W.cl.sheet_id); W.runnerSeen.clear(); render(); notify();
    host.announce(tText("Run {{n}} started", { n: W.run }));
  }

  /* ── the procedure card as a working surface (procard.js) ─────────── */
  /** Load *proc*'s checklist here (the Workbook tab follows it). */
  async function useCard(proc) {
    proc = String(proc || "");
    if (!proc) return null;
    if (currentProc() !== proc) W.manualProc = String(ctx().procedure || "") === proc ? "" : proc;
    else if (W.manualProc && String(ctx().procedure || "") === proc) W.manualProc = "";
    await loadChecklist(false);
    if (W.pane && W.pane.firstChild && !(W.pane.closest && W.pane.closest("[hidden]"))) render();
    return W.cl && W.cl.procedure === proc ? W.cl : null;
  }
  function cardState() {
    if (!W.cl) return null;
    const tk = ticks();
    const runs = runIds(entries(), W.cl.sheet_id);
    if (!runs.includes(W.run)) runs.push(W.run);
    const pre = (W.cl.prereqs || []).filter((p) => tk[p.key] && stepState(tk[p.key]) !== "open").length;
    return { cl: W.cl, run: W.run, runs, ticks: tk, progress: progress(W.cl.steps, tk),
      prereqs: { done: pre, total: (W.cl.prereqs || []).length }, stepState, readingHtml, expectText };
  }
  function setRun(r) { if (!W.cl) return; W.run = String(r); W.runnerSeen.clear(); render(); notify(); }

  return {
    mount(pane) {
      W.pane = pane; wire(pane);
      W.liveTimer = setInterval(liveTick, LIVE_MS);
    },
    sync, render, onData, onRunner, openForm, openChecklist, tick, newRun, setRun, useCard, cardState,
    capture: (key) => tick(key, "capture"),
    reading,
    subscribe(fn) { W.subs.add(fn); return () => W.subs.delete(fn); },
    get checklist() { return W.cl; },
    get run() { return W.run; },
    get procedure() { return currentProc(); },
    debriefSheets() {
      return W.sheets.filter((w) => w.form === "debrief" || w.phase === "debrief")
        .filter((w) => !formEntries(w.id).length && !entries().some((e) => e.worksheet && e.worksheet.id === w.id));
    },
    formHtml, saveForm, reset() { W.sheetsKey = ""; W.clKey = ""; },
  };
}

export default { createWorkbook };
