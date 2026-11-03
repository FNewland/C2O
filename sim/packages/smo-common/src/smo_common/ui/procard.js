/* ============================================================================
 * C2O DESIGN SYSTEM — procard.js  (served at /static/shared/procard.js)
 * ============================================================================
 * The procedure card as the working surface (Franz, 2026-11-03: "the
 * procedure cards should help the user to go to the workbook to mark steps
 * as done or not, capture values, and capture decisions; the procedure
 * cards become part of the logbook as they get filled in").
 *
 * The host renders the card (Markdown -> HTML) as it always did; this module
 * then works on that DOM:
 *
 *   const card = mountProcCard(box, {
 *     procedure: "COM-006",          // the card's id (procedure_index.yaml)
 *     lb,                            // mountLogbook() result (logbook.js)
 *     levels: { step: "H4", section: "H3" },   // ### and ## as rendered
 *     live: true,                    // live TM here (the MCS): capture works
 *   });
 *   card.destroy();
 *
 * - every "### Step N" section gets its controls at the end: Done / Failed /
 *   Skip (GO / NO-GO / Skip on a GO/NO-GO gate), the expected value of each
 *   Verify line beside its live value, "Capture values", a note/deviation
 *   field and "Record decision" (a logbook decision entry prefilled with the
 *   procedure, step, run and the captured values);
 * - every "[ ]" item of "## Prerequisites" becomes a checkbox;
 * - a bar at the top: run, progress, deviations, New run, Workbook.
 *
 * One source of truth: the controls write the SAME check records as the
 * logbook's Workbook tab (workbook.js tick/capture), so ticking in either
 * place updates both, and the MCS runner's automatic ticks show here too
 * (workbook.subscribe). The filled card is the run table of the logbook
 * export (smo_common/logbook/export.py), card decisions printed under it.
 *
 * Optimistic and never blocking; buttons are native (keyboard: Tab, Enter /
 * Space); the note saves on Enter (Shift+Enter for a new line) or on leaving
 * the field. Every string goes through i18n.js (keys are the English text).
 * ============================================================================ */

import { t, tText } from "/static/shared/i18n.js";
import { esc } from "/static/shared/components.js";
import { cardStepKeys, isPrereqHeading, prereqItem, isDeviation } from "/static/shared/checklist.js";

const LIVE_MS = 2000;
const LEVEL = (tag) => Number(String(tag || "").replace(/^H/i, "")) || 0;

const resultLabel = (r) => ({
  pass: tText("PASS"), fail: tText("FAIL"), skip: tText("SKIPPED"), go: "GO", nogo: "NO-GO",
  done: tText("done"), open: tText("open"),
}[r] || r);

/**
 * Wrap each step section of the rendered card in <section data-pc-step>
 * and find the Prerequisites checkbox items. The DOM keeps its look: the
 * nodes are only regrouped. Returns {steps: [{key, el, head}], prereqs:
 * [{key, el, text}]}.
 */
export function markCard(box, levels = {}) {
  const stepL = LEVEL(levels.step || "H4"), secL = LEVEL(levels.section || "H3");
  const doc = box.ownerDocument || document;
  const nodes = Array.from(box.childNodes);
  const heads = nodes.filter((n) => n.nodeType === 1 && LEVEL(n.tagName) === stepL && /^H\d$/i.test(n.tagName));
  const keys = cardStepKeys(heads.map((h) => h.textContent));
  const steps = [], prereqs = [];
  let cur = null, inPre = false, hi = 0;
  for (const n of nodes) {
    const isHead = n.nodeType === 1 && /^H\d$/i.test(n.tagName);
    const lv = isHead ? LEVEL(n.tagName) : 0;
    if (isHead && lv === stepL) {
      const key = keys[hi++];
      cur = doc.createElement("section");
      cur.className = "pc-step";
      cur.dataset.pcStep = key;
      box.insertBefore(cur, n);
      cur.appendChild(n);
      steps.push({ key, el: cur, head: n });
      inPre = false;
      continue;
    }
    if (isHead && lv < stepL) {
      cur = null;
      inPre = lv === secL && isPrereqHeading(n.textContent);
      continue;
    }
    if (cur) { cur.appendChild(n); continue; }
    if (inPre && n.nodeType === 1) {
      const lis = n.tagName === "LI" ? [n] : Array.from(n.querySelectorAll ? n.querySelectorAll("li") : []);
      for (const li of lis) {
        const text = prereqItem(li.textContent);
        if (text === null) continue;
        prereqs.push({ key: `p${prereqs.length + 1}`, el: li, text });
      }
    }
  }
  return { steps, prereqs };
}

function hms(iso) {
  const d = iso ? new Date(iso) : null;
  return d && !isNaN(d) ? d.toISOString().slice(11, 19) + " UTC" : "";
}
function simHms(s) {
  const m = /T(\d\d:\d\d:\d\d)/.exec(String(s || ""));
  return m ? m[1] : "";
}

export function mountProcCard(box, opts = {}) {
  const lb = opts.lb, wb = lb && lb.workbook;
  const proc = String(opts.procedure || "");
  const live = opts.live !== false;
  if (!box || !wb || !proc) return { destroy() {}, refresh() {} };
  const marks = markCard(box, opts.levels);
  const C = { cl: null, built: false, dead: false, timer: null, sig: {}, bar: null, uid: Math.random().toString(36).slice(2, 7) };
  const id = (k, what) => `pc-${C.uid}-${k}-${what}`;

  box.classList.add("pc-card");
  const bar = (box.ownerDocument || document).createElement("div");
  bar.className = "pc-bar";
  bar.setAttribute("role", "group");
  bar.setAttribute("aria-label", tText("Working copy of this card"));
  bar.innerHTML = `<span class="pc-bar-t">${t("Loading the checklist…")}</span>`;
  box.insertBefore(bar, box.firstChild);
  C.bar = bar;

  const state = () => wb.cardState();
  const stepOf = (key) => (C.cl ? C.cl.steps.find((s) => s.key === key) : null);
  const preOf = (key) => (C.cl ? (C.cl.prereqs || []).find((p) => p.key === key) : null);

  /* ── building (once per checklist) ─────────────────────────────────── */
  function liveCell(ck) {
    if (!live) return "";
    const st = state();
    return st ? st.readingHtml(ck, wb.reading(ck.param, ck.pid)) : "";
  }
  function ctlHtml(s) {
    const go = !!s.gonogo;
    const btn = (r, label, cls = "") => `<button type="button" class="ds-btn sm${cls}" data-pc="tick" data-r="${r}" ` +
      `aria-pressed="false" aria-describedby="${id(s.key, "res")}">${label}</button>`;
    const acts = go
      ? btn("go", "GO") + btn("nogo", "NO-GO") + btn("skip", t("Skip"))
      : btn("pass", t("Done"), " primary") + btn("fail", t("Failed")) + btn("skip", t("Skip"));
    const checks = (s.checks || []).filter((c) => c.param || c.pid);
    const label = s.n ? tText("Step {{n}}", { n: s.n }) : s.title;
    const vals = checks.length
      ? `<table class="pc-vals"><caption class="ds-sr">${t("Expected and observed values, {{step}}", { step: label })}</caption>` +
        `<thead><tr><th scope="col">${t("Expected")}</th>${live ? `<th scope="col">${t("Live")}</th>` : ""}` +
        `<th scope="col">${t("Captured")}</th></tr></thead><tbody>` +
        checks.map((c, ci) => `<tr><td class="ex"><code>${esc(state().expectText(c))}</code></td>` +
          (live ? `<td class="pc-live" data-ci="${ci}">${liveCell(c)}</td>` : "") +
          `<td class="pc-cap" data-ci="${ci}"></td></tr>`).join("") +
        `</tbody></table>` : "";
    return `<div class="pc-ctl" data-key="${esc(s.key)}">` +
      `<div class="pc-hd"><span class="pc-lbl">${t("Your working copy")}</span>` +
      `<span class="pc-res" id="${id(s.key, "res")}" role="status"></span><span class="pc-tm"></span></div>` +
      (go ? `<div class="pc-go"><span class="pc-lbl">GO/NO-GO</span> ${esc(s.gonogo)}</div>` : "") +
      vals +
      `<div class="pc-acts" role="group" aria-label="${esc(tText("Record {{step}}", { step: label }))}">${acts}` +
      // capture needs live TM: the MCS has it, the documentation viewer not
      (checks.length && live ? `<button type="button" class="ds-btn sm ghost" data-pc="capture">${t("Capture values")}</button>` : "") +
      `<button type="button" class="ds-btn sm ghost" data-pc="decision">${t("Record decision")}</button></div>` +
      `<div class="pc-nt"><label class="ds-sr" for="${id(s.key, "nt")}">${t("Note or deviation for {{step}}", { step: label })}</label>` +
      `<textarea id="${id(s.key, "nt")}" class="ds-input wb-note pc-note" rows="1" maxlength="2000" ` +
      `placeholder="${esc(tText("Note or deviation (Enter saves)"))}"></textarea></div></div>`;
  }
  function build() {
    const cl = C.cl;
    for (const m of marks.steps) {
      const s = stepOf(m.key);
      if (!s || m.el.querySelector(".pc-ctl")) continue;
      m.el.insertAdjacentHTML("beforeend", ctlHtml(s));
      m.head.insertAdjacentHTML("beforeend", ` <span class="pc-chip" aria-hidden="true"></span>`);
    }
    for (const m of marks.prereqs) {
      const p = preOf(m.key);
      if (!p || m.el.querySelector(".pc-pre")) continue;
      // the "[ ]" of the printed card becomes the real checkbox
      const lead = m.el.firstChild;
      if (lead && lead.nodeType === 3) lead.nodeValue = lead.nodeValue.replace(/^\s*\[[ xX]\]\s*/, "");
      m.el.classList.add("pc-pre-li");
      m.el.dataset.key = m.key;
      const ck = (p.checks || [])[0];
      m.el.insertAdjacentHTML("afterbegin", `<input type="checkbox" class="pc-pre" id="${id(m.key, "cb")}" ` +
        `aria-label="${esc(tText("Prerequisite {{n}} met", { n: p.n }))}"> `);
      if (ck && live) m.el.insertAdjacentHTML("beforeend", ` <span class="pc-prelive">${liveCell(ck)}</span>`);
    }
    C.built = !!cl;
  }

  /* ── updating in place (never steals focus or typed text) ──────────── */
  function capHtml(v) {
    if (!v) return "";
    return `<span class="lv cap${v.ok === false ? " off" : ""}${v.stale ? " st" : ""}">${esc(v.value || "")}` +
      `${v.units ? " " + esc(v.units) : ""}${v.ok === true ? ' <span class="okm">✓</span>' : v.ok === false ? ' <span class="bad">✗</span>' : ""}</span>`;
  }
  function update() {
    if (C.dead) return;
    const st = state();
    if (!st || !C.cl || st.cl !== C.cl) return;
    renderBar(st);
    for (const m of marks.steps) {
      const s = stepOf(m.key);
      const ctl = s && m.el.querySelector(".pc-ctl");
      if (!ctl) continue;
      const tick = st.ticks[m.key];
      const res = tick ? st.stepState(tick) : "open";
      const c = tick ? tick.check : null;
      const sig = JSON.stringify([st.run, res, c && c.values, c && c.note, tick && (tick.updated_ts || tick.ts), c && c.source]);
      if (C.sig[m.key] === sig) continue;
      C.sig[m.key] = sig;
      m.el.dataset.state = res;
      const dev = isDeviation(res);
      const r = ctl.querySelector(".pc-res");
      r.textContent = res === "open" ? tText("not done yet") : resultLabel(res);
      r.classList.toggle("dev", dev);
      r.classList.toggle("ok", res !== "open" && !dev);
      const chip = m.head.querySelector(".pc-chip");
      if (chip) {
        chip.textContent = res === "open" ? "" : resultLabel(res);
        chip.className = `pc-chip${dev ? " dev" : res === "open" ? "" : " ok"}`;
      }
      ctl.querySelector(".pc-tm").textContent = tick && res !== "open"
        ? [hms(tick.updated_ts || tick.ts), c.sim_ts ? `${tText("sim")} ${simHms(c.sim_ts)}` : "", c.position || "",
          c.source === "runner" ? tText("runner") : ""].filter(Boolean).join(" · ")
        : (tick && (c.values || []).length ? tText("values captured {{t}}", { t: hms(tick.updated_ts || tick.ts) }) : "");
      for (const b of ctl.querySelectorAll('[data-pc="tick"]')) b.setAttribute("aria-pressed", String(b.dataset.r === res));
      const vals = (c && c.values) || [];
      const checks = (s.checks || []).filter((x) => x.param || x.pid);
      ctl.querySelectorAll(".pc-cap").forEach((td) => {
        const ck = checks[Number(td.dataset.ci)];
        td.innerHTML = capHtml(ck && vals.find((v) => v.param === (ck.param || ck.pid)));
      });
      const nt = ctl.querySelector(".pc-note");
      const doc = nt.ownerDocument;
      if (doc.activeElement !== nt && nt.value === nt.defaultValue) {
        nt.value = nt.defaultValue = (c && c.note) || "";
        nt.rows = Math.min(4, Math.max(1, Math.ceil(nt.value.length / 70)));
      }
    }
    for (const m of marks.prereqs) {
      const cb = m.el.querySelector(".pc-pre");
      if (!cb) continue;
      const tick = st.ticks[m.key];
      const on = !!tick && st.stepState(tick) !== "open";
      cb.checked = on;
      m.el.dataset.state = on ? "done" : "open";
    }
    liveTick();
  }
  function renderBar(st) {
    const pr = st.progress;
    const runSel = `<label class="ds-sr" for="${id("bar", "run")}">${t("Run")}</label>` +
      `<select id="${id("bar", "run")}" class="ds-select sm" data-pc="run">` +
      st.runs.map((r) => `<option value="${esc(r)}"${r === st.run ? " selected" : ""}>${esc(tText("Run {{n}}", { n: r }))}</option>`).join("") +
      `</select>`;
    const sig = JSON.stringify([st.run, st.runs, pr, st.prereqs]);
    if (C.barSig === sig) return;
    const focused = bar.contains(bar.ownerDocument.activeElement) ? bar.ownerDocument.activeElement.dataset.pc : "";
    C.barSig = sig;
    bar.innerHTML = `<span class="pc-bar-t"><b>${t("Working copy")}</b> · ${t("each step you record is saved to your logbook")}` +
      (live ? "" : ` · ${t("values are captured in the MCS")}`) + `</span>` +
      `<span class="pc-bar-p" role="status">${t("{{done}} of {{total}} steps", { done: pr.done, total: pr.total })}` +
      (st.prereqs.total ? ` · ${t("prerequisites {{done}} of {{total}}", st.prereqs)}` : "") +
      (pr.deviations ? ` · <b class="dev">${t("{{count}} deviation", { count: pr.deviations, plural: "{{count}} deviations" })}</b>` : "") +
      `</span><span class="pc-bar-r">${runSel}` +
      `<button type="button" class="ds-btn ghost sm" data-pc="new-run">${t("New run")}</button>` +
      `<button type="button" class="ds-btn ghost sm" data-pc="workbook">${t("Open in the Workbook")}</button></span>`;
    if (focused) { const f = bar.querySelector(`[data-pc="${focused}"]`); if (f) f.focus(); }
  }
  function liveTick() {
    if (C.dead || !live) return;
    const st = state();
    if (!st || !C.cl) return;
    for (const m of marks.steps) {
      if (m.el.dataset.state && m.el.dataset.state !== "open") continue;
      const s = stepOf(m.key);
      if (!s) continue;
      const checks = (s.checks || []).filter((x) => x.param || x.pid);
      m.el.querySelectorAll(".pc-live").forEach((td) => {
        const ck = checks[Number(td.dataset.ci)];
        if (ck) td.innerHTML = liveCell(ck);
      });
      const cap = m.el.querySelector('[data-pc="capture"]');
      if (cap) {
        const any = checks.some((ck) => { const r = wb.reading(ck.param, ck.pid); return r && !r.nodata; });
        if (any) { cap.removeAttribute("aria-disabled"); cap.removeAttribute("data-reason"); }
        else {
          cap.setAttribute("aria-disabled", "true");
          cap.setAttribute("data-reason", tText("No telemetry received yet for these parameters"));
        }
      }
    }
    for (const m of marks.prereqs) {
      const span = m.el.querySelector(".pc-prelive");
      const p = preOf(m.key);
      const ck = p && (p.checks || [])[0];
      if (span && ck && m.el.dataset.state !== "done") span.innerHTML = liveCell(ck);
    }
  }

  /* ── actions ───────────────────────────────────────────────────────── */
  function decisionText(s, key) {
    const st = state();
    const tick = st && st.ticks[key];
    const vals = ((tick && tick.check.values) || []).filter((v) => v.value);
    const head = `${proc} · ${s.n ? tText("Step {{n}}", { n: s.n }) : s.title} — ${s.title}`;
    const lines = [head];
    if (s.gonogo) lines.push(`GO/NO-GO: ${s.gonogo.split("\n")[0]}`);
    for (const v of vals) lines.push(`${v.param} = ${v.value}${v.units ? " " + v.units : ""}${v.ok === false ? " ✗" : ""} (${tText("expected")} ${v.expect})`);
    if (!vals.length) {
      for (const ck of (s.checks || []).filter((x) => x.param || x.pid)) {
        const r = live ? wb.reading(ck.param, ck.pid) : null;
        if (r && !r.nodata) lines.push(`${ck.param} = ${r.text}${r.units ? " " + r.units : ""}${r.stale ? " (" + tText("stale") + ")" : ""} (${tText("expected")} ${st.expectText(ck)})`);
      }
    }
    lines.push(tText("Decision:") + " ");
    return lines.join("\n");
  }
  function onClick(ev) {
    const el = ev.target.closest && ev.target.closest("[data-pc]");
    if (!el || !box.contains(el)) return;
    if (el.getAttribute("aria-disabled") === "true") { ev.preventDefault(); return; }
    const a = el.dataset.pc;
    const sec = el.closest(".pc-step");
    const key = sec ? sec.dataset.pcStep : "";
    if (a === "tick" && key) {
      const cur = sec.dataset.state || "open";
      const note = sec.querySelector(".pc-note");
      wb.tick(key, cur === el.dataset.r ? "open" : el.dataset.r, { note: note ? note.value.trim() : undefined });
    } else if (a === "capture" && key) {
      const note = sec.querySelector(".pc-note");
      wb.tick(key, "capture", { note: note ? note.value.trim() : undefined });
    } else if (a === "decision" && key) {
      const s = stepOf(key);
      if (s) lb.logThis({ procedure: proc, step: s.n || key, run: state() ? state().run : "" },
        { kind: "decision", text: decisionText(s, key) });
    } else if (a === "new-run") wb.newRun();
    else if (a === "workbook") lb.openChecklist(proc);
  }
  function onChange(ev) {
    const el = ev.target;
    if (el.dataset && el.dataset.pc === "run") { wb.setRun(el.value); return; }
    if (el.classList && el.classList.contains("pc-pre")) {
      const li = el.closest(".pc-pre-li");
      if (li) wb.tick(li.dataset.key, el.checked ? "done" : "open");
    }
  }
  function saveNote(nt) {
    const sec = nt.closest(".pc-step");
    if (!sec) return;
    const v = nt.value.trim();
    const st = state();
    const tick = st && st.ticks[sec.dataset.pcStep];
    if (v === ((tick && tick.check.note) || "") || (!tick && !v)) return;
    nt.defaultValue = nt.value;
    wb.tick(sec.dataset.pcStep, "note", { note: v });
  }
  function onKey(ev) {
    const el = ev.target;
    if (el.classList && el.classList.contains("pc-note") && ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      saveNote(el);
    }
    // keys typed here are the card's, not the console's single-key shortcuts
    if (el.closest && el.closest(".pc-ctl, .pc-bar") && el.tagName === "TEXTAREA" && ev.key !== "Tab" && ev.key !== "F6") {
      ev.stopPropagation();
    }
  }
  function onInput(ev) {
    const el = ev.target;
    if (el.classList && el.classList.contains("pc-note")) {
      el.rows = Math.min(6, Math.max(1, Math.ceil(el.value.length / 70) + (el.value.match(/\n/g) || []).length));
    }
  }
  function onFocusOut(ev) {
    const el = ev.target;
    if (el.classList && el.classList.contains("pc-note")) saveNote(el);
  }
  box.addEventListener("click", onClick);
  box.addEventListener("change", onChange);
  box.addEventListener("keydown", onKey);
  box.addEventListener("focusout", onFocusOut);
  box.addEventListener("input", onInput);

  const unsub = wb.subscribe(() => {
    const st = state();
    // the same card reloaded (another language, a new fetch): adopt it
    if (st && st.cl && st.cl.procedure === proc && st.cl !== C.cl) { C.cl = st.cl; C.sig = {}; C.barSig = ""; build(); }
    if (st && st.cl === C.cl) update();
  });
  wb.useCard(proc).then((cl) => {
    if (C.dead) return;
    if (!cl) {
      bar.innerHTML = `<span class="pc-bar-t">${t("No checklist for {{proc}}: this card is read only.", { proc })}</span>`;
      return;
    }
    C.cl = cl;
    build();
    update();
  }).catch(() => {
    if (!C.dead) bar.innerHTML = `<span class="pc-bar-t">${t("The checklist could not be loaded; the card is read only.")}</span>`;
  });
  C.timer = setInterval(liveTick, LIVE_MS);

  return {
    refresh: update,
    get procedure() { return proc; },
    destroy() {
      C.dead = true;
      clearInterval(C.timer);
      unsub();
      box.removeEventListener("click", onClick);
      box.removeEventListener("change", onChange);
      box.removeEventListener("keydown", onKey);
      box.removeEventListener("focusout", onFocusOut);
      box.removeEventListener("input", onInput);
    },
  };
}

export default { mountProcCard, markCard };
