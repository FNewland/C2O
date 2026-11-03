/* ============================================================================
 * C2O DESIGN SYSTEM — checklist.js  (served at /static/shared/checklist.js)
 * ============================================================================
 * Pure helpers for the live procedure checklists of the ops workbook
 * (logbook "Workbook" tab, workbook.js). No DOM, no fetch, no i18n: the
 * node tests import this file directly.
 *
 *   evalCheck(check, raw)            -> true | false | null (cannot judge)
 *   parseInlineCheck(text)           -> {param, pid, op, value} | null
 *   runnerResults(map, stepResults)  -> {stepKey: "pass"|"fail"|"skip"}
 *   runIds(entries, sheetId)         -> ["1", "2", …] runs seen, oldest first
 *   nextRunId(entries, sheetId)      -> "3"
 *   ticksFor(entries, sheetId, run)  -> {stepKey: entry}
 *   progress(steps, ticks)           -> {done, total, deviations}
 *   isDeviation(result)              -> fail / skip / NO-GO
 *   cardStepKeys(headings)           -> ["s0", "s1", "h1", …] for the card's
 *                                       ### headings (checklist.py parse_card)
 *   isPrereqHeading(text)            -> a "## Prerequisites" / "## Prérequis"
 *   prereqItem(text)                 -> the item text of "[ ] …", else null
 * ============================================================================ */

export const RESULTS = ["pass", "fail", "skip", "go", "nogo", "done", "open"];
const DEVIATION = new Set(["fail", "skip", "nogo"]);
// procedure_runner.py StepResult
const R_PENDING = 0, R_RUNNING = 1, R_PASSED = 2, R_FAILED = 3, R_SKIPPED = 4, R_TIMEOUT = 5;

export function isDeviation(result) { return DEVIATION.has(result); }

function toNum(v) {
  if (v === null || v === undefined || v === "" || typeof v === "boolean") return null;
  const s = String(v).replace("−", "-").replace(",", ".");
  const m = /[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?/i.exec(s);
  if (!m) return null;
  const n = Number(m[0]);
  return Number.isFinite(n) ? n : null;
}

/** Judge a reading against a parsed card check ({op, value, num, lo, hi,
 *  set}). Returns null when the check states nothing comparable (prose, a
 *  comparison with another parameter) or there is no reading. */
export function evalCheck(check, raw) {
  if (!check || !check.op || raw === null || raw === undefined || raw === "") return null;
  if (check.ref_param) return null;
  const n = toNum(raw);
  if (check.op === "in") {
    if (Array.isArray(check.set)) {
      if (n !== null) return check.set.some((s) => toNum(s) !== null && Math.abs(toNum(s) - n) < 1e-9);
      return check.set.map(String).includes(String(raw));
    }
    if (typeof check.lo === "number" && typeof check.hi === "number") {
      return n === null ? null : n >= check.lo && n <= check.hi;
    }
    return null;
  }
  let want = typeof check.num === "number" ? check.num : toNum(check.value);
  if (want === null) {
    if (check.op === "==" || check.op === "!=") {
      const eq = String(raw).trim().toUpperCase() === String(check.value || "").trim().toUpperCase();
      return check.op === "==" ? eq : !eq;
    }
    return null;
  }
  if (n === null) return null;
  const eps = Math.max(1e-9, Math.abs(want) * 1e-6);
  switch (check.op) {
    case "==": return Math.abs(n - want) <= Math.max(eps, 0.01);
    case "!=": return Math.abs(n - want) > Math.max(eps, 0.01);
    case "<": return n < want;
    case ">": return n > want;
    case "<=": return n <= want + eps;
    case ">=": return n >= want - eps;
    default: return null;
  }
}

/** A criterion written inline on a printed sheet, e.g. "OBC application SW
 *  running (obdh.sw_image 0x0311 = 1)" -> {param, pid, op:"==", value:"1"}. */
export function parseInlineCheck(text) {
  const s = String(text || "");
  const m = /([a-z][a-z0-9_]+(?:\.[a-z0-9_]+)+)\s*\(?\s*(0x[0-9A-Fa-f]{4})?\s*\)?\s*(==|=|!=|<=|>=|≤|≥|<|>)\s*([-+]?\d+(?:\.\d+)?)/.exec(s);
  if (m) {
    const op = { "=": "==", "≤": "<=", "≥": ">=" }[m[3]] || m[3];
    return { param: m[1], pid: m[2] || "", op, value: m[4], num: Number(m[4]) };
  }
  const p = /([a-z][a-z0-9_]+(?:\.[a-z0-9_]+)+)\s*\(?\s*(0x[0-9A-Fa-f]{4})/.exec(s);
  return p ? { param: p[1], pid: p[2] } : null;
}

/** Card-step results from the MCS runner. ``map[i]`` is the checklist step
 *  key of runner step i (checklist.py runner_map). A failure or timeout
 *  fails its card step at once (the runner stops there); otherwise a card
 *  step is reported once ALL its runner steps are final: any skip -> skip,
 *  else pass ("go" for a step that is a GO/NO-GO gate, when ``gates`` lists
 *  it). Steps never reached are not reported. */
export function runnerResults(map, stepResults, gates) {
  const out = {};
  if (!Array.isArray(map) || !Array.isArray(stepResults)) return out;
  const by = {};
  stepResults.forEach((r, i) => {
    const key = map[i];
    if (!key) return;
    (by[key] = by[key] || []).push(Number(r && r.result !== undefined ? r.result : r));
  });
  const gate = new Set(gates || []);
  for (const [key, rs] of Object.entries(by)) {
    if (rs.some((r) => r === R_FAILED || r === R_TIMEOUT)) { out[key] = gate.has(key) ? "nogo" : "fail"; continue; }
    if (rs.some((r) => r === R_PENDING || r === R_RUNNING)) continue;
    out[key] = rs.some((r) => r === R_SKIPPED) ? "skip" : gate.has(key) ? "go" : "pass";
  }
  return out;
}

function checkEntries(entries, sheetId) {
  return (entries || []).filter((e) => e && e.check && e.worksheet && e.worksheet.id === sheetId);
}
function runOf(e) { return String((e.worksheet && e.worksheet.instance) || (e.check && e.check.run) || "1"); }

export function runIds(entries, sheetId) {
  const seen = [];
  for (const e of checkEntries(entries, sheetId).slice().sort((a, b) => String(a.ts).localeCompare(String(b.ts)))) {
    const r = runOf(e);
    if (!seen.includes(r)) seen.push(r);
  }
  return seen;
}

export function nextRunId(entries, sheetId) {
  const nums = runIds(entries, sheetId).map((r) => parseInt(r, 10)).filter(Number.isFinite);
  return String(nums.length ? Math.max(...nums) + 1 : 1);
}

/** Latest tick per step key for one run. */
export function ticksFor(entries, sheetId, run) {
  const out = {};
  for (const e of checkEntries(entries, sheetId)) {
    if (runOf(e) !== String(run)) continue;
    const k = e.check.key || (e.worksheet && e.worksheet.q);
    if (!k) continue;
    const prev = out[k];
    if (!prev || String(e.updated_ts || e.ts) > String(prev.updated_ts || prev.ts)) out[k] = e;
  }
  return out;
}

export function progress(steps, ticks) {
  let done = 0, deviations = 0;
  for (const s of steps || []) {
    const e = ticks[s.key];
    if (!e) continue;
    const r = e.check.result || (e.worksheet && e.worksheet.checked ? "done" : "open");
    if (r !== "open") done += 1;
    if (DEVIATION.has(r)) deviations += 1;
  }
  return { done, total: (steps || []).length, deviations };
}

/* ── card structure (mirrors smo_common/logbook/checklist.py) ─────────── */
const STEP_HEAD = /^(?:Step|[ÉE]tape)\s+([0-9]+[A-Za-z]?)(?![0-9A-Za-z])/;
const ANCHOR = /\s*\{#[A-Za-z0-9_][\w.:-]*(?:\s[^}]*)?\}\s*$/;

/** Checklist keys of a card's ### headings, in document order: "s<N>" for
 *  "Step N — …" / "Étape N — …", "h<i>" for the i-th other ### heading
 *  (parse_card numbers every one of them, kept or not). */
export function cardStepKeys(headings) {
  let h = 0;
  return (headings || []).map((raw) => {
    const text = String(raw || "").replace(ANCHOR, "").trim();
    const m = STEP_HEAD.exec(text);
    if (m) return `s${m[1].toLowerCase()}`;
    h += 1;
    return `h${h}`;
  });
}

/** "## Prerequisites" (EN) / "## Prérequis" (FR) / "Conditions préalables". */
export function isPrereqHeading(text) {
  return /^(?:Prerequisites|Pr[ée]requis|Conditions\s+pr[ée]alables)\b/i.test(String(text || "").trim());
}

/** "[ ] OBC in NOMINAL mode" -> "OBC in NOMINAL mode"; anything else -> null. */
export function prereqItem(text) {
  const m = /^\s*\[[ xX]\]\s+([\s\S]*\S)\s*$/.exec(String(text || ""));
  return m ? m[1] : null;
}

export default { cardStepKeys, isPrereqHeading, prereqItem, evalCheck, parseInlineCheck, runnerResults, runIds, nextRunId, ticksFor, progress, isDeviation };
