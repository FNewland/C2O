/* ============================================================================
 * C2O INSTRUCTOR — debrief view (PEARLS, the timeline replayed)
 * ============================================================================
 * Simulation plus debriefing beats simulation alone; video adds nothing
 * measurable (Cheng et al. 2014). So the debrief replays the SAME semantic
 * timeline the instructor watched live, seekable, in the four PEARLS phases
 * (Eppich & Cheng 2015): Reactions, Description (the shared picture: the
 * timeline with a cursor), Analysis (the fault swimlane gaps, with prompts
 * keyed to the largest gap) and Summary (plus / delta, export).
 * Notes stay in this browser only (localStorage) and in the export file.
 * INSTRUCTOR_CONSOLE_DESIGN.md §8.
 * ========================================================================== */

import { esc } from "/static/shared/components.js";
import { t, tText } from "/static/shared/i18n.js";
import { mountTimeline } from "/static/modern/timeline.js";
import { fmtAge, fmtClockSec, renderChain, STAGES } from "/static/modern/views.js";

export const PHASES = [
  { id: "reactions", label: "Reactions", hint: "How did that feel?" },
  { id: "description", label: "Description", hint: "What happened, in order" },
  { id: "analysis", label: "Analysis", hint: "Why the gaps" },
  { id: "summary", label: "Summary", hint: "Plus / delta, take-aways" },
];
// i18n-keys
export const DYNAMIC_KEYS = ["Reactions", "How did that feel?", "Description", "What happened, in order",
  "Analysis", "Why the gaps", "Summary", "Plus / delta, take-aways"];

const fin = (v) => v !== null && v !== undefined && Number.isFinite(Number(v));

/** Prompts for the Analysis phase, keyed to a fault's largest gap. */
export function gapPrompts(f) {
  const L = f.latency || {};
  const out = [];
  const what = `${f.subsystem.toUpperCase()} / ${f.failure}`;
  if (!fin(L.to_symptom_s)) {
    out.push(tText("{{what}} produced no on-board alarm. What other indication could have shown it? Which display would you have had to look at?", { what }));
  } else if (!fin(f.ground_ts)) {
    out.push(tText("The first alarm for {{what}} never reached the ground in this run. When could the team have seen it (next pass, a dump)?", { what }));
  }
  if (fin(L.to_ground_s) && L.to_ground_s > 120) {
    out.push(tText("The alarm waited {{gap}} on board before it reached the ground. What did the team know about the spacecraft during that time?", { gap: fmtAge(L.to_ground_s) }));
  }
  if (fin(L.to_response_s)) {
    out.push(tText("{{gap}} passed between the alarm reaching the ground and the first telecommand. What were you looking at? What told you what to do?", { gap: fmtAge(L.to_response_s) }));
  } else if (fin(f.ground_ts)) {
    out.push(tText("No telecommand followed the alarm. Was that a decision (monitor first) or a miss?"));
  }
  if (f.inject_class === "indication") {
    out.push(tText("This was a lying sensor: the spacecraft was fine but a reading was wrong. Which cross-check could have shown that?"));
  }
  return out;
}

export function biggestGap(f) {
  const L = f.latency || {};
  const cand = [["to_symptom_s", "Inserted → symptom"], ["to_ground_s", "Symptom → ground"],
    ["to_response_s", "Ground → first telecommand"]].filter(([k]) => fin(L[k]));
  if (!cand.length) return null;
  return cand.reduce((a, b) => (L[b[0]] > L[a[0]] ? b : a));
}

function store(key, val) {
  try {
    if (val === undefined) return localStorage.getItem(key) || "";
    localStorage.setItem(key, val);
  } catch (e) { /* private window: notes stay in the textarea only */ }
  return "";
}

export function createDebrief(host, { onToast } = {}) {
  let data = null, history = [], phase = "description", cursorTs = null, tl = null, keyed = "";
  const els = {
    pearls: host.querySelector("#pearls"), body: host.querySelector("#pearls-body"),
    tl: host.querySelector("#debrief-tl"), cursor: host.querySelector("#debrief-cursor"),
  };

  function noteKey(k) { return `c2o.instructor.debrief.${data ? data.segment : 0}.${k}`; }

  function renderPhases() {
    els.pearls.innerHTML = PHASES.map((p) => `<button type="button" data-ph="${p.id}" aria-pressed="${p.id === phase}">` +
      `<b>${esc(tText(p.label))}</b>${esc(tText(p.hint))}</button>`).join("");
  }

  function keyEvents() {
    const items = (data && data.items) || [];
    return items.filter((i) => (i.lane === "fault" && (i.kind === "inject" || i.kind === "clear" || i.kind === "diverge"))
      || (i.lane === "phase" && i.sev >= 2) || (i.lane === "alarm" && i.kind === "ev_down" && i.sev >= 3)
      || (i.lane === "alarm" && i.kind === "missed_cue") || (i.lane === "instr" && (i.kind === "bookmark" || i.kind === "anomaly"))
      || (i.lane === "tc" && (i.kind === "tc_rej" || i.kind === "tc_fail")));
  }

  function renderBody() {
    if (!data) { els.body.innerHTML = `<div class="no-data">${t("Loading the run…")}</div>`; return; }
    const faults = data.faults || [];
    let html = "";
    if (phase === "reactions") {
      html = `<ol class="prompts"><li>${t("How did that feel? (Let everyone speak before any analysis.)")}</li>
        <li>${t("What was the hardest moment?")}</li><li>${t("Is there anything you want to make sure we talk about?")}</li></ol>
        <div class="ds-field" style="margin-top:var(--sp-3)"><label for="db-react">${t("Notes (this browser only)")}</label>
        <textarea class="ds-input" id="db-react">${esc(store(noteKey("react")))}</textarea></div>`;
    } else if (phase === "description") {
      const evs = keyEvents();
      html = `<p class="lede">${t("Build one shared picture of what happened. Click an event (or the timeline) to put the cursor there; the panel below shows what was true and what the ground knew at that moment.")}</p>
        ${evs.length ? `<ol class="prompts">${evs.map((i) => `<li><button type="button" class="ds-btn ghost sm" data-ts="${i.ts}">${esc(fmtClockSec(i.ts))}</button> ${esc(i.text)}</li>`).join("")}</ol>`
        : `<div class="no-data">${t("No key events in this run segment.")}</div>`}`;
    } else if (phase === "analysis") {
      const rows = faults.map((f) => {
        const L = f.latency || {};
        const big = biggestGap(f);
        const cell = (k) => `<td class="${big && big[0] === k ? "big" : ""}">${fin(L[k]) ? esc(fmtAge(L[k])) : "—"}</td>`;
        return `<tr><td>${esc(`${f.subsystem.toUpperCase()} / ${f.failure}`)}</td>${cell("to_symptom_s")}${cell("to_ground_s")}${cell("to_response_s")}<td>${fin(L.to_clear_s) ? esc(fmtAge(L.to_clear_s)) : "—"}</td></tr>`;
      }).join("");
      const prompts = faults.map((f) => `<h3>${esc(`${f.subsystem.toUpperCase()} / ${f.failure}`)}</h3>${renderChain(f)}
        <ol class="prompts">${gapPrompts(f).map((p) => `<li>${esc(p)}</li>`).join("")}</ol>`).join("");
      html = faults.length ? `<table class="lat-table"><thead><tr><th scope="col">${t("Fault")}</th>
        <th scope="col">${t("to symptom")}</th><th scope="col">${t("to ground")}</th><th scope="col">${t("to first TC")}</th><th scope="col">${t("to clear")}</th></tr></thead>
        <tbody>${rows}</tbody></table><p class="note">${t("The largest gap of each fault is highlighted. Inserted → symptom is the spacecraft; symptom → ground is the link; ground → first telecommand is the team.")}</p>${prompts}`
        : `<div class="no-data">${t("No inject in this run segment, so there is no gap to analyse.")}</div>`;
    } else {
      html = `<div class="viewgrid"><div class="ds-field"><label for="db-plus">${t("Plus: what went well")}</label>
        <textarea class="ds-input" id="db-plus">${esc(store(noteKey("plus")))}</textarea></div>
        <div class="ds-field"><label for="db-delta">${t("Delta: what to change next time")}</label>
        <textarea class="ds-input" id="db-delta">${esc(store(noteKey("delta")))}</textarea></div></div>
        <p class="note">${t("Notes stay in this browser and in the export. Participants answer their debrief questions in their own logbook; you never see those answers.")}</p>
        <div class="scn-actions"><button type="button" class="ds-btn primary" id="db-export-md">${t("Export debrief (Markdown)")}</button>
        <button type="button" class="ds-btn" id="db-export-json">${t("Export data (JSON)")}</button></div>`;
    }
    els.body.innerHTML = html;
  }

  function nearestSample(ts) {
    let best = null;
    for (const h of history) if (!best || Math.abs(h.ts - ts) < Math.abs(best.ts - ts)) best = h;
    return best;
  }

  function renderCursor(pairsMeta) {
    if (cursorTs == null) { els.cursor.innerHTML = `<p class="note">${t("Click the replay to place the cursor.")}</p>`; return; }
    const h = nearestSample(cursorTs);
    const near = ((data && data.items) || []).filter((i) => Math.abs(i.ts - cursorTs) <= 60 && i.lane !== "link")
      .slice(0, 8).map((i) => `<li><span class="mono dim">${esc(fmtClockSec(i.ts))}</span> ${esc(i.text)}</li>`).join("");
    let rows = "";
    if (h) {
      const lab = Object.fromEntries((pairsMeta || []).map((r) => [r.id, r]));
      rows = Object.entries(h.pairs).filter(([, v]) => v[3]).map(([id, v]) => {
        const m = lab[id] || { label: id, digits: 2, unit: "" };
        const f = (x) => (x === null || x === undefined ? "—" : typeof x === "number" ? x.toFixed(m.digits ?? 2) : String(x));
        return `<tr class="c-${v[3]}"><th scope="row">${esc(tText(m.label))}</th><td>${esc(f(v[0]))}</td><td>${esc(f(v[1]))}</td><td>${esc(f(v[2]))}</td><td><span class="cause cause-${v[3]}">${esc(tText(v[3] === "estimator" ? "estimate" : v[3]))}</span></td></tr>`;
      }).join("");
    }
    els.cursor.innerHTML = `<h3>${t("At {{time}}", { time: fmtClockSec(cursorTs) })}${h ? ` <span class="dim">(${esc(tText("nearest sample {{t}}", { t: fmtClockSec(h.ts) }))})</span>` : ""}</h3>
      <div class="viewgrid"><div>${rows ? `<table class="pairs"><thead><tr><th scope="col">${t("Quantity")}</th><th scope="col">${t("Truth")}</th><th scope="col">${t("Spacecraft")}</th><th scope="col">${t("Ground")}</th><th scope="col">${t("Cause")}</th></tr></thead><tbody>${rows}</tbody></table>`
        : `<div class="no-data">${t("Truth and ground agreed at this moment.")}</div>`}</div>
      <ul class="plain">${near || `<li class="dim">${t("Nothing on the timeline within a minute.")}</li>`}</ul></div>`;
  }

  function renderReplay() {
    if (!data) return;
    if (!tl) tl = mountTimeline(els.tl, { t: tText, onCursor: (ts) => { cursorTs = ts; draw(); }, onSelect: (seq) => {
      const it = (data.items || []).find((i) => i.seq === seq); if (it) { cursorTs = it.ts; draw(); } } });
    const items = data.items || [];
    const t0 = items.length ? items[0].ts : Date.now() / 1000;
    const nowTs = data.now ? Date.parse(data.now) / 1000 : t0;
    const span = Math.max(600, nowTs - t0);
    tl.update({ items, pending: [], nowTs, windowS: span * 1.02, futureFrac: 0.01, segment: data.segment, cursorTs });
  }

  let pairsMeta = [];
  function draw() { renderPhases(); renderBody(); renderReplay(); renderCursor(pairsMeta); }

  host.addEventListener("click", (ev) => {
    const ph = ev.target.closest("[data-ph]");
    if (ph) { phase = ph.dataset.ph; draw(); return; }
    const ts = ev.target.closest("[data-ts]");
    if (ts) { cursorTs = Number(ts.dataset.ts); renderReplay(); renderCursor(pairsMeta); return; }
    if (ev.target.id === "db-export-md") exportMd();
    if (ev.target.id === "db-export-json") exportJson();
  });
  host.addEventListener("input", (ev) => {
    const map = { "db-react": "react", "db-plus": "plus", "db-delta": "delta" };
    if (map[ev.target.id]) store(noteKey(map[ev.target.id]), ev.target.value);
  });

  function download(name, type, text) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type }));
    a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
  function exportJson() {
    download(`debrief-${(data && data.now || "run").slice(0, 19).replace(/[:T]/g, "-")}.json`, "application/json",
      JSON.stringify({ ...data, history, notes: { reactions: store(noteKey("react")), plus: store(noteKey("plus")), delta: store(noteKey("delta")) } }, null, 2));
    if (onToast) onToast(tText("Debrief data exported"));
  }
  function exportMd() {
    const L = [];
    L.push(`# ${tText("Debrief")} — ${(data && data.scenario && data.scenario.name) || tText("free run")}`, "");
    L.push(`${tText("Exported")}: ${data ? data.now : ""}`, "");
    L.push(`## ${tText("Faults and gaps")}`, "");
    L.push(`| ${tText("Fault")} | ${tText("to symptom")} | ${tText("to ground")} | ${tText("to first TC")} | ${tText("to clear")} |`, "|---|---|---|---|---|");
    for (const f of (data && data.faults) || []) {
      const l = f.latency || {};
      const c = (k) => (fin(l[k]) ? fmtAge(l[k]) : "—");
      L.push(`| ${f.subsystem.toUpperCase()} / ${f.failure} | ${c("to_symptom_s")} | ${c("to_ground_s")} | ${c("to_response_s")} | ${c("to_clear_s")} |`);
    }
    L.push("", `## ${tText("Key events")}`, "");
    for (const i of keyEvents()) L.push(`- ${fmtClockSec(i.ts)} — ${i.text}`);
    L.push("", `## ${tText("Plus")}`, "", store(noteKey("plus")) || "—", "", `## ${tText("Delta")}`, "", store(noteKey("delta")) || "—", "");
    download(`debrief-${(data && data.now || "run").slice(0, 19).replace(/[:T]/g, "-")}.md`, "text/markdown", L.join("\n"));
    if (onToast) onToast(tText("Debrief exported"));
  }

  return {
    async refresh() {
      try {
        const [d, h] = await Promise.all([fetch("/api/instructor/debrief").then((r) => r.json()),
          fetch("/api/instructor/history").then((r) => r.json())]);
        data = d; history = (h && h.samples) || [];
        const k = `${data.segment}:${(data.items || []).length}`;
        if (k !== keyed || !els.body.innerHTML) {
          keyed = k;
          const typing = document.activeElement && document.activeElement.tagName === "TEXTAREA"
            && host.contains(document.activeElement);
          if (typing) { renderReplay(); renderCursor(pairsMeta); } else draw();
        }
      } catch (e) {
        els.body.innerHTML = `<div class="no-data">${t("The debrief data could not be loaded.")}</div>`;
      }
    },
    setPairsMeta(rows) { pairsMeta = rows || []; },
    relabel() { draw(); },
  };
}

export { STAGES };
