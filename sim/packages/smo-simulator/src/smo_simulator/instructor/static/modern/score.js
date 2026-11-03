/* ============================================================================
 * C2O INSTRUCTOR — scenario score (the debrief's "what the team did")
 * ============================================================================
 * The score comes from the commands the team sent (scenario_scoring.py): every
 * expected response is listed with its status and the evidence that met it —
 * which command, when, what the spacecraft said — or "not seen". Responses
 * the simulator cannot see are listed for the instructor to judge and are not
 * scored. Keep it explainable: nothing here is a number without its source.
 * ========================================================================== */

import { esc, renderChip } from "/static/shared/components.js";
import { t, tText, tdb } from "/static/shared/i18n.js";

// i18n-keys (statuses, categories and notes that arrive from the simulator)
export const DYNAMIC_KEYS = [
  "done", "late", "wrong", "missed", "observed", "not reached",
  "detect", "isolate", "recover", "verify", "command", "action", "monitor", "plan",
  "sent", "accepted", "completed", "rejected", "failed", "not uplinked",
  "not visible to the simulator: judge it in the debrief", "its reference event never happened",
  "sent, but {{state}} never followed", "sent before {{after}} was done", "prerequisite {{after}} not seen",
  "rejected by the spacecraft", "failed on board", "not uplinked (no command link)",
  "rejected by the spacecraft ({{error}})", "failed on board ({{error}})",
  "not uplinked (no command link) ({{error}})", "declaration error: {{error}}",
];
// i18n-keys
export const DYNAMIC_KEYS_2 = [
  "{{id}}: {{evidence}}", "first relevant command {{name}}", "instructor mark",
  "first recovery {{id}}: {{evidence}}", "last recovery {{id}}: {{evidence}}",
  "MTTD (detect)", "MTTI (isolate)", "MTTR (recover)",
];

const fin = (v) => v !== null && v !== undefined && Number.isFinite(Number(v));
const CHIP = { done: "ok", late: "warn", wrong: "alarm", missed: "alarm", observed: "neutral", not_reached: "nodata" };

/** T+mm:ss from scenario start. */
export function tPlus(s) {
  if (!fin(s)) return "—";
  const v = Math.max(0, Math.round(Number(s)));
  const h = Math.floor(v / 3600), m = Math.floor((v % 3600) / 60), x = v % 60;
  return `T+${h ? `${h}:` : ""}${String(m).padStart(h ? 2 : 1, "0")}:${String(x).padStart(2, "0")}`;
}
/** A duration in seconds, minutes when long. */
export function dur(s) {
  if (!fin(s)) return "—";
  const v = Math.abs(Number(s));
  if (v < 120) return `${Math.round(v)} s`;
  return `${Math.floor(v / 60)} min ${String(Math.round(v % 60)).padStart(2, "0")} s`;
}
function noteText(n) {
  if (!n) return "";
  if (typeof n === "string") return n;
  return n.key ? tText(n.key, n.vars || {}) : "";
}
const statusLabel = (st) => tText(st === "not_reached" ? "not reached" : st);
const fateLabel = (f) => tText(f === "not_uplinked" ? "not uplinked" : f);
function respText(d, r) { return d.id ? tdb(`scnresp:${d.id}.${r.i}:description`, r.description) : r.description; }
function harmText(d, h) { return d.id && h.reason ? tdb(`scnharm:${d.id}.${h.i}:reason`, h.reason) : h.reason; }

function evidenceHtml(r) {
  if (!r.evidence || !r.evidence.length) {
    if (r.status === "observed" || r.status === "not_reached") return "";
    return `<span class="ev none">${t("not seen")}</span>`;
  }
  return r.evidence.map((e) => e.kind === "tc"
    ? `<span class="ev"><span class="mono">${esc(e.name)}${e.args ? `(${esc(e.args)})` : ""}</span> ${esc(tPlus(e.t))} · ${esc(fateLabel(e.fate))}</span>`
    : `<span class="ev"><span class="mono">${esc(e.text)}</span> ${esc(tText("from {{t}}", { t: tPlus(e.t) }))}</span>`).join("");
}

/** The score panel: number, mean times with their source, every response. */
export function renderScore(d, { nd = "—", scenarioName = "" } = {}) {
  if (!d) return `<div class="no-data">${t("No debrief yet. It appears when a scenario ends (stopped, or its duration elapsed).")}</div>`;
  const scored = fin(d.score_pct);
  const resp = d.responses || [];
  const nScored = resp.filter((r) => r.scored).length;
  const head = `<div class="score-head">
      <div class="score-big${scored ? "" : " none"}">${scored ? `${Number(d.score_pct).toFixed(0)} %` : esc(tText("Not scored"))}</div>
      <div class="score-sub">
        <div class="name">${esc(scenarioName || d.name || "")}</div>
        <div>${scored ? esc(tText("{{earned}} of {{possible}} points from {{n}} checked responses", { earned: Number(d.earned).toFixed(1), possible: Number(d.possible).toFixed(0), n: nScored }))
          : esc(tText("Nothing in this scenario is visible to the simulator: judge the responses below."))}
          ${fin(d.penalty) && d.penalty > 0 ? ` · <span class="pen">${esc(tText("−{{p}} points for harmful commands", { p: Number(d.penalty).toFixed(0) }))}</span>` : ""}</div>
        <div class="dim">${esc(tText("Ran {{d}}; times are counted from the first fault ({{t}}).", { d: dur(d.duration_s), t: tPlus(d.ref_s) }))}</div>
      </div></div>`;
  const m = d.metrics || {};
  const mrow = (k, label) => {
    const x = m[k];
    return `<tr><th scope="row">${t(label)}</th><td class="mono">${x && fin(x.s) ? esc(dur(x.s)) : nd}</td>
      <td>${x ? `${x.inferred ? `<span class="cls-chip">${t("inferred")}</span> ` : ""}${esc(noteText(x.source))}` : `<span class="dim">${t("no evidence")}</span>`}</td></tr>`;
  };
  const metrics = `<table class="score-metrics"><tbody>${mrow("mttd", "MTTD (detect)")}${mrow("mtti", "MTTI (isolate)")}${mrow("mttr", "MTTR (recover)")}</tbody></table>`;
  const rows = resp.map((r) => `<li class="resp st-${esc(r.status)}">
      <div class="r1">${renderChip({ kind: CHIP[r.status] || "neutral", label: statusLabel(r.status) })}
        <span class="cat">${esc(tText(r.category))}</span>
        <span class="desc">${esc(respText(d, r))}</span>
        ${fin(r.time_s) ? `<span class="when mono" title="${esc(tText("after the fault"))}">+${esc(dur(r.time_s))}</span>` : ""}</div>
      <div class="r2">${evidenceHtml(r)}
        ${r.scored && fin(r.target_s) ? `<span class="dim">${esc(tText("target {{s}}", { s: dur(r.target_s) }))}</span>` : ""}
        ${r.checks && r.checks.length ? `<span class="dim">${esc(tText("checks {{what}}", { what: r.checks.join(" | ") }))}</span>` : ""}
        ${noteText(r.note) ? `<span class="note-t">${esc(noteText(r.note))}</span>` : ""}</div></li>`).join("");
  const harm = (d.harmful || []);
  const harmHtml = harm.length ? `<h4>${t("Harmful commands")}</h4><ul class="harm">${harm.map((h) => `<li>
      ${renderChip({ kind: h.applied ? "alarm" : "ok", label: h.applied ? tText("sent: −{{p}}", { p: Number(h.penalty).toFixed(0) }) : tText("not sent") })}
      <span class="mono">${esc((h.checks || []).join(" | "))}</span> <span class="desc">${esc(harmText(d, h))}</span>
      ${(h.evidence || []).map((e) => `<span class="ev">${esc(tPlus(e.t))}</span>`).join("")}</li>`).join("")}</ul>` : "";
  const cmds = d.commands || [];
  const cmdHtml = `<details class="ds-disclosure cmds"><summary>${esc(tText("Commands sent during the scenario ({{n}})", { n: cmds.length }))}</summary>
      ${cmds.length ? `<table class="lat-table"><thead><tr><th scope="col">${t("Command")}</th><th scope="col">${t("Time")}</th><th scope="col">${t("Spacecraft")}</th></tr></thead><tbody>
      ${cmds.map((c) => `<tr><td class="mono">${esc(c.name)}${c.args ? `(${esc(c.args)})` : ""}</td><td>${esc(tPlus(c.t))}</td><td>${esc(fateLabel(c.fate))}${c.error ? ` <span class="dim">${esc(c.error)}</span>` : ""}</td></tr>`).join("")}</tbody></table>`
        : `<div class="no-data">${t("The team sent no telecommand during the scenario.")}</div>`}</details>`;
  const marks = (d.marks || []).length ? `<h4>${t("Instructor marks")}</h4><ul class="plain">${d.marks.map((k) => `<li><span class="mono dim">${esc(tPlus(k.t))}</span> ${esc(tText(k.category))}${k.description ? ": " + esc(k.description) : ""}</li>`).join("")}</ul>` : "";
  const how = `<p class="note">${t("How it is scored: each expected response with a command or state to check is done (100 %), late after its target (50 %), wrong when the command was rejected, failed, came before its prerequisite or did not produce the state (0), or missed (0). Responses the simulator cannot see are listed but not scored. Each harmful command entry costs its penalty once.")}</p>`;
  return head + metrics + `<h4>${t("Expected responses")}</h4><ol class="resp-list">${rows}</ol>` + harmHtml + marks + cmdHtml + how;
}

/** The same, as Markdown for the debrief export. */
export function scoreMarkdown(d) {
  if (!d) return [];
  const L = [];
  L.push(`## ${tText("Scenario score")}`, "");
  L.push(fin(d.score_pct) ? `**${Number(d.score_pct).toFixed(0)} %** (${tText("{{earned}} of {{possible}} points from {{n}} checked responses",
    { earned: Number(d.earned).toFixed(1), possible: Number(d.possible).toFixed(0), n: (d.responses || []).filter((r) => r.scored).length })}`
    + (d.penalty > 0 ? `; ${tText("−{{p}} points for harmful commands", { p: Number(d.penalty).toFixed(0) })}` : "") + ")"
    : tText("Not scored"), "");
  for (const [k, label] of [["mttd", "MTTD (detect)"], ["mtti", "MTTI (isolate)"], ["mttr", "MTTR (recover)"]]) {
    const x = (d.metrics || {})[k];
    L.push(`- ${tText(label)}: ${x && fin(x.s) ? dur(x.s) + (x.inferred ? ` (${tText("inferred")})` : "") + ` — ${noteText(x.source)}` : tText("no evidence")}`);
  }
  L.push("", `| ${tText("Status")} | ${tText("Response")} | ${tText("Evidence")} |`, "|---|---|---|");
  for (const r of d.responses || []) {
    const ev = (r.evidence || []).map((e) => e.kind === "tc" ? `${e.name}${e.args ? `(${e.args})` : ""} ${tPlus(e.t)} (${fateLabel(e.fate)})` : `${e.text} ${tPlus(e.t)}`).join("; ")
      || (r.status === "observed" ? "" : tText("not seen"));
    L.push(`| ${statusLabel(r.status)} | ${tText(r.category)}: ${respText(d, r).replace(/\|/g, "/")} | ${ev}${noteText(r.note) ? ` — ${noteText(r.note)}` : ""} |`);
  }
  if ((d.harmful || []).some((h) => h.applied)) {
    L.push("", `### ${tText("Harmful commands")}`, "");
    for (const h of d.harmful) if (h.applied) L.push(`- ${(h.checks || []).join(" | ")}: ${harmText(d, h)} (−${Number(h.penalty).toFixed(0)})`);
  }
  L.push("");
  return L;
}
