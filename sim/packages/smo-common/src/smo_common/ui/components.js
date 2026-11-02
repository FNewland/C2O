/* ============================================================================
 * SMO DESIGN SYSTEM — components.js
 * ============================================================================
 * The shared component vocabulary for the three modern consoles (MCS,
 * Planner, Instructor). Served by every server at
 * /static/shared/components.js; styled exclusively by design-system.css;
 * glyphs referenced from glyphs.svg.
 *
 * THIS IS A FROZEN CONTRACT (execution plan §3). Agents 2-4 build against
 * these exact names and signatures. Do not rename, remove, reorder or retype
 * an argument. Additive-only evolution (new optional args / new exports).
 *
 * DESIGN RULES (PRINCIPLES.md):
 *  - Pure render functions: every render*() takes plain data and RETURNS AN
 *    HTML STRING (or SVG string). No DOM reads, no fetch, no globals, no
 *    Date.now(). Callers own insertion and diffing. (The one read is the UI
 *    language: prose goes through i18n.js t(); English output is unchanged.
 *    Re-render on `smo:langchange` to switch.)
 *  - One idiom per concept (P5): there is exactly one stepper, one chip, one
 *    param triad, one AND table. Pages must not fork these.
 *  - Colour is never the only cue (P6): every state emitted here carries a
 *    glyph and/or text label alongside its status class.
 *  - Stale must never look like steady (P4), and never like never-received:
 *    a STALE value keeps its last number, dimmed + italic, with an age chip
 *    ("82.1 % · 59 s"); a value NEVER RECEIVED reads "no data" (never "—");
 *    a parameter whose HK structure is disabled reads "not enabled".
 *    Verdicts come from state.js freshness() (cadence-aware, four states).
 *
 * STATE VOCABULARY (brief §1.3, gallery.html): renderButton, renderValue,
 * renderAge, renderNoData, renderGauge, renderField, renderTabs,
 * renderDisclosure, renderBanner, renderLinkBanner, renderModeBanner (pure);
 * setDisabled, setEnabled, armButton, installReasonTips, mountTabs (impure,
 * DOM). Reason tooltips are installed automatically on import in a browser.
 *
 * DATA CONTRACT SUMMARY (which endpoint feeds which argument):
 *  - `def`    — one entry of MCS GET /api/param-catalog `parameters[]`:
 *               {id, hex, name, subsystem, units, description, in_hk,
 *                on_demand, hk_sids, hk_interval_s}.
 *  - `limits` — one band of MCS GET /api/limits `limits["0xHHHH"]`:
 *               {yellow_low, yellow_high, red_low, red_high, name,
 *                subsystem, units}; absent/null band = no ground limit
 *               (renders the explicit "no limit defined" affordance).
 *  - `value` / `values` — live numbers from WS `state` message `data.params`
 *               (keys "0xHHHH") with per-parameter ages in `data.params_age`
 *               (keys are DECIMAL id strings — quirk preserved from classic)
 *               and limit states in `data.param_limit_state` ("0xHHHH" ->
 *               "nominal"|"yellow_low"|"yellow_high"|"red_low"|"red_high";
 *               "unlimited" appears only from /api/limits `state`).
 *  - `alarm`  — one WS `alarm` message payload / one row of GET /api/alarms
 *               `alarms[]` (see renderAlarmRow).
 *  - `evt`    — one MCS event entry (WS `event` messages / event log rows).
 * ============================================================================ */

import { t, tText, getLang, setLang, onLangChange, LANGS } from "/static/shared/i18n.js";
import { freshness as freshness4 } from "/static/shared/state.js";

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

/** esc(s) — HTML-escape a string. Exported because pages composing their own
 *  markup around these components need the same escaping discipline. */
export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ESC[c]);
}

/** Path to the shared glyph sprite; change here only. */
export const GLYPHS = "/static/shared/glyphs.svg";

/** glyph(name, cls) — inline <svg><use> for a glyphs.svg symbol id
 *  (without the "g-" prefix): glyph("warn-up") -> #g-warn-up. */
export function glyph(name, cls = "") {
  return `<svg class="${esc(cls)}" aria-hidden="true" width="11" height="11">` +
         `<use href="${GLYPHS}#g-${esc(name)}"></use></svg>`;
}

/* ── FRESHNESS ─────────────────────────────────────────────────────────── */

/**
 * freshness(ageS) -> "fresh" | "degraded" | "stale"
 *
 * The display-wide freshness policy (P4), promoted from the classic charts:
 * fresh < 5 s, degraded 5-15 s, stale > 15 s. `null`/`undefined` (never
 * seen) is "stale".
 *
 * @param {number|null|undefined} ageS — SIM-seconds age as served
 *        (`data.params_age[id]`, `data.last_frame_age_s`,
 *        `data.subsystem_staleness[sub]`, `data.hk_sid_age_s[sid]`).
 *        Do not re-age client-side with Date.now().
 */
export function freshness(ageS) {
  if (ageS === null || ageS === undefined || !Number.isFinite(Number(ageS))) {
    return "stale";
  }
  const a = Number(ageS);
  if (a < 5) return "fresh";
  if (a <= 15) return "degraded";
  return "stale";
}

/* Map a limit-state string ("nominal"/"yellow_*"/"red_*"/"unlimited") to the
   design-system modifier class ("", "w", "a"). Internal + exported. */
export function limitClass(state) {
  if (!state) return "";
  if (state.startsWith("red")) return "a";
  if (state.startsWith("yellow")) return "w";
  return "";
}

/* ── 1. PARAMETER TRIAD (P3) ───────────────────────────────────────────── */

/**
 * renderParam(def, value, limits) -> html string
 *
 * The one way a scalar with limits is displayed: name + numeral + unit +
 * bar against limits. Parameters WITHOUT limits render a visible "no limit
 * defined" line instead of a bar (P3).
 *
 * Data states (brief §1.3):
 *   live      value bright, upright; out-of-limits adds colour + triangle +
 *             ISA code (H/HH/L/LL) and the w/a class
 *   degraded  live, plus an amber age chip
 *   stale     LAST VALUE KEPT, dim italic, dashed age chip ("82.1 % · 59 s");
 *             the needle stays at the last value, uncoloured
 *   no data   never received: the label "no data", no number, no needle
 *   off       HK structure not enabled (verdict "disabled"): "not enabled"
 *
 * @param {object} def    — /api/param-catalog entry (see header). Only
 *        `name`, `hex`, `units` are required; `description` becomes the
 *        title attribute; `hk_interval_s` makes the freshness verdict
 *        cadence-aware; `eng` is the engineering string of a discrete value.
 * @param {number|null|undefined} value — live value from WS state
 *        `data.params[def.hex]`. null/undefined => "no data".
 * @param {object|null} [limits] — /api/limits band for def.hex, optionally
 *        extended by the caller with:
 *          state {string}   — data.param_limit_state[def.hex] (else derived
 *                             from the band client-side),
 *          age_s {number}   — data.params_age[String(def.id)],
 *          verdict {string} — the caller's own verdict ("fresh"|"degraded"|
 *                             "stale"|"nodata"|"disabled"), wins over age_s,
 *          lo/hi {number}   — display range override for the bar.
 * @returns {string} `<div class="ds-param ...">...`
 *          Classes: "w"/"a" (= is-caution/is-alarm), "stale" (= is-stale),
 *          "is-nodata", "degraded".
 */
export function renderParam(def, value, limits) {
  const d = def || {};
  const L = limits || {};
  const hasVal = _finite(value);
  const band = _band(limits);
  const age = "age_s" in L ? L.age_s : undefined;
  const vs = valueState(value, age, { verdict: L.verdict, intervalS: d.hk_interval_s });
  const live = vs === "live" || vs === "degraded";
  const state = L.state || (band && hasVal ? _classify(Number(value), band) : "");
  const lc = live ? limitClass(state) : "";
  const cls = ["ds-param", lc, vs === "stale" ? "stale" : "",
    vs === "nodata" || vs === "off" ? "is-nodata" : "", vs === "degraded" ? "degraded" : ""]
    .filter(Boolean).join(" ");
  // `def.eng` — the engineering-value string for a DISCRETE parameter
  // ("COARSE_SUN (2)"). It is carried separately from `value` on purpose:
  // `value` stays numeric so limits, banding and the deviation bar keep
  // working, and only the rendered text changes. Passing the string as
  // `value` instead makes Number() NaN, which trips `hasVal` and renders the
  // parameter as "no data" — i.e. a mode chip that shows nothing.
  let vHtml;
  if (vs === "nodata") vHtml = renderNoData();
  else if (vs === "off") vHtml = renderNoData({ off: true });
  else {
    const txt = d.eng !== undefined && d.eng !== null ? esc(String(d.eng)) : _num(Number(value));
    const unit = d.units ? `<u>${esc(d.units)}</u>` : "";
    vHtml = (lc ? glyph(_limitGlyph(state)) : "") + txt + unit +
      (lc ? renderFlag(state, { glyph: false }) : "") +
      (vs === "stale" || vs === "degraded" ? renderAge(age, { degraded: vs === "degraded" }) : "");
  }
  const bar = band
    ? _devbar(hasVal && vs !== "off" ? Number(value) : null, limits, !live)
    : `<span class="nolimit">${t("no limit defined")}</span>`;
  return `<div class="${cls}" data-param="${esc(d.hex || "")}"` +
         (d.description ? ` title="${esc(d.description)}"` : "") + `>` +
         `<span class="nm">${esc(d.name || d.hex || "?")}` +
         `<small>${esc(d.hex || "")}</small></span>` +
         `<span class="vl">${vHtml}</span>` +
         bar +
         `</div>`;
}

/* ── 2. DEVIATION BAR (P3) ─────────────────────────────────────────────── */

/**
 * renderDeviationBar(value, limits) -> html string
 *
 * Analogue position-in-range bar with the yellow/red boundaries drawn as
 * ticks. Tick labels are revealed on hover/focus — handled by CSS, nothing
 * to do here.
 *
 * @param {number|null} value — live value; null => needle omitted (stale).
 * @param {object|null} limits — /api/limits band {yellow_low, yellow_high,
 *        red_low, red_high} (any subset non-null), plus optional lo/hi
 *        display-range override and units. With no band at all, returns the
 *        "no limit defined" affordance so callers can use this standalone.
 * @returns {string} `<div class="ds-devbar ...">...`
 */
export function renderDeviationBar(value, limits) {
  return _devbar(value, limits, false);
}

function _devbar(value, limits, neutral) {
  const band = _band(limits);
  if (!band) return `<span class="nolimit">${t("no limit defined")}</span>`;
  const { yellow_low: yl, yellow_high: yh, red_low: rl, red_high: rh } = band;
  // Display range: explicit lo/hi, else pad the outermost defined bound.
  const bounds = [yl, yh, rl, rh].filter((v) => v !== null && v !== undefined);
  let lo = limits.lo, hi = limits.hi;
  if (lo === undefined || hi === undefined) {
    const mn = Math.min(...bounds, value ?? Infinity);
    const mx = Math.max(...bounds, value ?? -Infinity);
    const pad = (mx - mn || Math.abs(mx) || 1) * 0.15;
    if (lo === undefined) lo = mn - pad;
    if (hi === undefined) hi = mx + pad;
  }
  const pct = (v) => Math.max(0, Math.min(100, ((v - lo) / (hi - lo)) * 100));
  let segs = "";
  const seg = (a, b, c) =>
    `<span class="seg ${c}" style="left:${pct(a).toFixed(1)}%;width:${(pct(b) - pct(a)).toFixed(1)}%"></span>`;
  if (rl !== null && rl !== undefined) segs += seg(lo, rl, "r");
  if (yl !== null && yl !== undefined) segs += seg(rl ?? lo, yl, "y");
  if (yh !== null && yh !== undefined) segs += seg(yh, rh ?? hi, "y");
  if (rh !== null && rh !== undefined) segs += seg(rh, hi, "r");
  let ticks = "";
  const tick = (v, c) =>
    `<span class="tick ${c}" style="left:${pct(v).toFixed(1)}%"></span>` +
    `<span class="lab" style="left:${pct(v).toFixed(1)}%">${_num(v)}</span>`;
  for (const [v, c] of [[yl, "y"], [yh, "y"], [rl, "r"], [rh, "r"]]) {
    if (v !== null && v !== undefined) ticks += tick(v, c);
  }
  const hasVal = value !== null && value !== undefined && Number.isFinite(Number(value));
  const state = hasVal ? _classify(Number(value), band) : "";
  const needle = hasVal
    ? `<span class="nd" style="left:${pct(Number(value)).toFixed(1)}%"></span>` : "";
  return `<div class="ds-devbar ${neutral ? "" : limitClass(state)}" tabindex="0" role="img" ` +
         `aria-label="${esc(tText("value {{value}} of range {{lo}} to {{hi}}", {
           value: hasVal ? _num(Number(value)) : tText("unknown"), lo: _num(lo), hi: _num(hi) }))}">` +
         segs + ticks + needle + `</div>`;
}

/* ── 3. SPARKLINE ──────────────────────────────────────────────────────── */

/**
 * renderSparkline(series, opts) -> svg string
 *
 * Chrome-free inline-SVG trend (P5: "sparkline or trend panel, never a
 * third thing"). STOPS APPENDING WHEN STALE: the caller passes the series
 * it holds; when opts.stale is true the line simply ends and a short dashed
 * cut mark is drawn at the last sample — the line is never flat-extended
 * to "now" (P4).
 *
 * @param {number[]} series — newest-last numeric samples (caller-maintained
 *        ring buffer fed from WS state values; recommended cap ~120).
 *        Non-finite entries break the line (gap), which is how HK dropouts
 *        should look.
 * @param {{w?:number,h?:number,stale?:boolean,cls?:string,min?:number,max?:number}} [opts]
 *        w/h — pixel size (default 90x22); stale — freshness(age)==="stale";
 *        cls — extra class ("w"/"a" to colour by limit state);
 *        min/max — fixed y-range (else auto from data).
 * @returns {string} `<svg class="ds-spark ...">...`
 */
export function renderSparkline(series, opts = {}) {
  const { w = 90, h = 22, stale = false, cls = "", min, max } = opts;
  const data = Array.isArray(series) ? series : [];
  const fin = data.filter((v) => Number.isFinite(v));
  if (!fin.length) {
    return `<svg class="ds-spark ${esc(cls)}" width="${w}" height="${h}" aria-hidden="true"></svg>`;
  }
  const lo = min !== undefined ? min : Math.min(...fin);
  const hi = max !== undefined ? max : Math.max(...fin);
  const span = hi - lo || 1;
  const n = data.length;
  const x = (i) => (n === 1 ? w / 2 : (i / (n - 1)) * (w - 2) + 1);
  const y = (v) => h - 2 - ((v - lo) / span) * (h - 4);
  let d = "", pen = false, lastX = null, lastY = null;
  data.forEach((v, i) => {
    if (!Number.isFinite(v)) { pen = false; return; }
    lastX = x(i); lastY = y(v);
    d += `${pen ? "L" : "M"}${lastX.toFixed(1)} ${lastY.toFixed(1)}`;
    pen = true;
  });
  const cut = stale && lastX !== null
    ? `<line class="stale-cut" x1="${lastX.toFixed(1)}" y1="2" ` +
      `x2="${lastX.toFixed(1)}" y2="${h - 2}"></line>` : "";
  return `<svg class="ds-spark ${stale ? "stale " : ""}${esc(cls)}" width="${w}" ` +
         `height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true">` +
         `<path d="${d}"></path>${cut}</svg>`;
}

/* ── 4. AND TABLE (SCOS-2000) ──────────────────────────────────────────── */

/**
 * renderAndTable(params, values) -> html string
 *
 * SCOS-2000-style alphanumeric display: one row per parameter with name,
 * description, raw, engineering value, unit, and OOL flag column. Generated
 * from the catalog so it can never drift from the telemetry dictionary (P10).
 *
 * @param {object[]} params — /api/param-catalog entries (typically filtered
 *        to one subsystem: p.subsystem === "eps").
 * @param {object} values — the composite live view the page maintains:
 *        {
 *          params:      WS state data.params            ("0xHHHH" -> number),
 *          ages:        WS state data.params_age        (decimal-id-string -> s),
 *          limitState:  WS state data.param_limit_state ("0xHHHH" -> state),
 *          limits:      GET /api/limits `limits`        ("0xHHHH" -> band),
 *          raw:         optional ("0xHHHH" -> raw count) when the page has
 *                       decommutated raw values; omitted -> raw column shows
 *                       an em-dash.
 *        }
 * @returns {string} `<table class="ds-and">...`
 */
export function renderAndTable(params, values) {
  const v = values || {};
  const rows = (params || []).map((p) => {
    const hex = p.hex || (Number.isFinite(p.id) ? "0x" + p.id.toString(16).toUpperCase().padStart(4, "0") : "");
    const val = v.params ? v.params[hex] : undefined;
    const age = v.ages ? v.ages[String(p.id)] : undefined;
    // `v.verdicts` — the caller's cadence-aware four-state verdict, which also
    // knows about DISABLED HK structures. Without it we fall back to the flat
    // threshold, which cannot distinguish "the link is down" from "nobody
    // enabled this SID", and so shows the last known value as though it were
    // arriving. See configs/eosat1/mcs/staleness.yaml.
    const fr = v.verdicts ? v.verdicts[hex] : undefined;
    const hasVal = val !== null && val !== undefined && Number.isFinite(Number(val));
    const vs = valueState(val, age, { verdict: fr, intervalS: p.hk_interval_s });
    const disabled = vs === "off";
    const stale = vs === "stale";
    const nodata = vs === "nodata";
    const live = vs === "live" || vs === "degraded";
    const state = (v.limitState && v.limitState[hex]) || "";
    const lc = live ? limitClass(state) : "";
    const band = v.limits ? v.limits[hex] : null;
    const st = v.states ? v.states[hex] : null;
    const code = hasVal ? Math.round(Number(val)) : null;
    // Stale keeps the LAST value (dim italic, the Age column says how old);
    // never-received says "no data"; a disabled HK structure says "not
    // enabled" and shows no number at all.
    const engHtml = disabled ? renderNoData({ off: true, label: tText("NOT ENABLED") })
      : nodata || !hasVal ? renderNoData()
      : esc(st && st[String(code)] !== undefined ? `${st[String(code)]} (${code})` : _num(Number(val)));
    // RAW follows the same gate as ENG. Showing the last received count beside
    // an ENG cell reading "NOT ENABLED" is a mixed message: the operator sees a
    // number in a value column and reads it as current. The value is not lost —
    // it is still in the ground cache, and the Age column says how old it is —
    // but a display column is not the place to assert it.
    const raw = disabled || nodata || !hasVal ? ""
      : (v.raw && v.raw[hex] !== undefined ? String(v.raw[hex]) : _num(Number(val)));
    const ool = !band ? `<span class="ds-meta">${t("no limit")}</span>`
      : !live ? ""
      : lc ? glyph(_limitGlyph(state)) + _isaCode(state)
      : "";
    const rowCls = [lc, stale ? "stale" : "", nodata ? "is-nodata" : "", disabled ? "disabled" : ""]
      .filter(Boolean).join(" ");
    return `<tr class="${rowCls}" data-param="${esc(hex)}">` +
           `<td class="id">${esc(hex)}</td>` +
           `<td>${esc(p.name || "")}` +
           (p.description ? `<br><small>${esc(p.description)}</small>` : "") + `</td>` +
           `<td class="raw">${esc(raw)}</td>` +
           `<td class="eng">${engHtml}</td>` +
           `<td>${esc(p.units || "")}</td>` +
           `<td class="ool">${ool}</td>` +
           `<td class="ds-age${vs === "degraded" ? " degraded" : ""}">${hasVal ? _age(age) : ""}</td>` +
           `</tr>`;
  }).join("");
  return `<table class="ds-and"><thead><tr>` +
         `<th>ID</th><th>${t("Parameter")}</th><th>${t("Raw")}</th><th>${t("Eng")}</th>` +
         `<th>${t("Unit")}</th><th>OOL</th><th>${t("Age")}</th>` +
         `</tr></thead><tbody>${rows}</tbody></table>`;
}

/* ── 5. STATE CHIP (P6 glyph vocabulary) ───────────────────────────────── */

/**
 * renderChip(state) -> html string
 *
 * The one binary/enumerated-state idiom: glyph + text label + colour class.
 * Glyph vocabulary (PRINCIPLES P6): warning = hollow amber up/down triangle;
 * alarm = filled red triangle; stale = dashed outline + italic; commanded =
 * accent dashed diamond; off = hollow ring; ok = check; active = accent fill
 * + filled square; nominal = plain grey, no glyph.
 *
 * @param {{kind:string, label:string, dir?:"up"|"down", title?:string}} state
 *        kind — "ok"|"warn"|"alarm"|"stale"|"cmd"|"off"|"neutral"|
 *               "active" (accent fill: running/tracking)|"nodata"|"shelved".
 *        glyph — override the glyph (a glyphs.svg id without "g-").
 *        label — the text (ALWAYS present: colour is never the only cue).
 *        dir — for warn/alarm: which side of the band ("up" high, "down"
 *              low; derived from limit state suffix _high/_low).
 *        title — tooltip.
 * @returns {string} `<span class="ds-chip ...">...`
 */
export function renderChip(state) {
  const s = state || {};
  const kind = s.kind || "neutral";
  const dir = s.dir === "down" ? "down" : "up";
  const g = s.glyph || {
    warn: `warn-${dir}`, alarm: `alarm-${dir}`, ok: "ack", shelved: "shelved",
    stale: "stale", cmd: "commanded", off: "off", active: "run",
  }[kind];
  const cls = { neutral: "", ok: "ok", active: "is-active", nodata: "is-nodata" }[kind] ?? kind;
  return `<span class="ds-chip ${cls}"` +
         (s.title ? ` title="${esc(s.title)}"` : "") + `>` +
         (g ? glyph(g) : "") +
         `<span>${esc(s.label ?? "—")}</span></span>`;
}

/* ── 6. STEPPER (P5: one component for all chains) ─────────────────────── */

/**
 * renderStepper(states, activeIdx) -> html string
 *
 * Progression through discrete stages: AOCS mode chain, TTC lock chain
 * (carrier -> bit -> frame), load-shed ladder, TC verification
 * (accept -> start -> complete), procedure steps. ONE component for all.
 *
 * @param {(string|{label:string, fail?:boolean, detail?:string})[]} states
 *        Ordered stage labels. An object form marks a failed stage
 *        (fail:true) and can carry a small detail line.
 * @param {number} activeIdx — index of the CURRENT stage; stages before it
 *        render as done, after it as pending. Pass -1 for "none reached".
 * @returns {string} `<div class="ds-stepper" role="list">...`
 */
export function renderStepper(states, activeIdx) {
  const items = (states || []).map((st, i) => {
    const o = typeof st === "string" ? { label: st } : (st || { label: "?" });
    const cls = o.fail ? "fail" : i < activeIdx ? "done" : i === activeIdx ? "active" : "";
    return `<span class="ds-step ${cls}" role="listitem"` +
           (i === activeIdx ? ` aria-current="step"` : "") + `>` +
           `<span class="pip"></span><span>${esc(o.label)}` +
           (o.detail ? `<br><small>${esc(o.detail)}</small>` : "") +
           `</span></span>`;
  }).join("");
  return `<div class="ds-stepper" role="list">${items}</div>`;
}

/* ── 7. ALARM ROW (P7) ─────────────────────────────────────────────────── */

/**
 * renderAlarmRow(alarm) -> html string
 *
 * One row of the single alarm authority. Blank-tolerant: rationalisation /
 * procedure / priority may be absent and the row still renders.
 *
 * @param {object} alarm — WS `alarm` message payload / GET /api/alarms row:
 *        {id, timestamp (sim epoch s), time_base, subsystem, severity,
 *         message?, param_id?, value?, status?, limit?, acknowledged,
 *         procedure? {id?, name?, path?}, db_id?}.
 *        Optional extensions the renderer honours when present:
 *        priority (1-4, ISA-18.2; derived by the page when absent),
 *        rationalisation {cause?, consequence?, response?}, shelved (bool),
 *        rtn (bool, returned-to-normal), utc (pre-formatted time string —
 *        pages format timestamps with fmtUTC + the sim clock; this renderer
 *        does NOT read clocks).
 * @param {object} [opts] — {role?: ARIA role for the row, e.g. "listitem"
 *        inside a role="list" container}. No role by default: a row
 *        without cells is an axe critical (was role="row" until 2026-11).
 * @returns {string} `<div class="ds-alarm-row ...">...`
 */
export function renderAlarmRow(alarm, opts) {
  const a = alarm || {};
  const role = opts && opts.role ? ` role="${esc(opts.role)}"` : "";
  const pri = [1, 2, 3, 4].includes(a.priority) ? a.priority
    : (Number(a.severity) >= 3 ? 2 : Number(a.severity) === 2 ? 3 : 4);
  const cls = [
    "ds-alarm-row", `p${pri}`,
    a.acknowledged ? "acked" : "unacked",
    a.shelved ? "shelved" : "", a.rtn ? "rtn" : "",
  ].filter(Boolean).join(" ");
  const rat = a.rationalisation || {};
  const ratHtml = (rat.cause || rat.consequence || rat.response)
    ? `<small>${[rat.cause, rat.consequence, rat.response]
        .filter(Boolean).map(esc).join(" · ")}</small>` : "";
  const proc = a.procedure
    ? `<button class="ds-btn" data-act="procedure" ` +
      `data-proc="${esc(a.procedure.path || a.procedure.id || "")}">` +
      `${esc(a.procedure.name || a.procedure.id || tText("PROCEDURE"))}</button>` : "";
  const ack = a.acknowledged ? "" :
    `<button class="ds-btn" data-act="ack" data-id="${esc(a.id)}">${t("ACK")}</button>`;
  const msg = a.message ||
    (a.param_id !== undefined
      ? tText("{{status}} on {{param}}", { status: a.status || tText("limit"),
        param: `0x${Number(a.param_id).toString(16).toUpperCase().padStart(4, "0")}` })
      : "");
  return `<div class="${cls}" data-id="${esc(a.id)}"${role}>` +
         `<span class="t num">${esc(a.utc || "")}</span>` +
         `<span class="pri">${pri <= 2 ? glyph("alarm-up") : pri === 3 ? glyph("warn-up") : ""}P${pri}</span>` +
         `<span class="msg">${esc(a.subsystem ? a.subsystem.toUpperCase() + " — " : "")}` +
         `${esc(msg)}${a.value !== undefined ? ` <span class="num">(${_num(Number(a.value))})</span>` : ""}` +
         `${ratHtml}</span>` +
         `<span class="act">${ack}${proc}</span>` +
         `</div>`;
}

/* ── 8. EVENT ROW (P5) ─────────────────────────────────────────────────── */

/**
 * renderEventRow(evt) -> html string
 *
 * List-of-things-that-happened idiom: time · severity glyph · source · text.
 *
 * @param {object} evt — event entry (MCS WS `event` payloads / S5 decodes /
 *        instructor log lines): {severity (1-4 numeric or
 *        "info"|"low"|"medium"|"high"|"critical"), name?, subsystem?,
 *        description?|text?, utc? (pre-formatted by the page — this renderer
 *        reads no clock), instructor? (bool: M9 INSTRUCTOR badge, sim only)}.
 * @param {object} [opts] — {role?: ARIA role for the row, e.g. "listitem"}.
 * @returns {string} `<div class="ds-event-row ...">...`
 */
export function renderEventRow(evt, opts) {
  const e = evt || {};
  const sevNum = typeof e.severity === "number" ? e.severity
    : { critical: 4, high: 3, medium: 2, low: 1, info: 1 }[String(e.severity).toLowerCase()] ?? 1;
  const cls = sevNum >= 3 ? "alarm" : sevNum === 2 ? "warn" : "info";
  const sevTxt = sevNum >= 4 ? "CRIT" : sevNum === 3 ? "HIGH" : sevNum === 2 ? "MED" : "INFO";
  const badge = e.instructor
    ? ` <span class="ds-badge" title="${esc(tText("injected by instructor (training)"))}">${t("INSTRUCTOR")}</span>` : "";
  // No role="row": a row without cells and outside a table is an axe
  // critical (R3 audit A6). Event rows sit inside a role="log" live region
  // (instructor) or a plain list; pass opts.role = "listitem" when the
  // container is role="list".
  const role = opts && opts.role ? ` role="${esc(opts.role)}"` : "";
  return `<div class="ds-event-row ${cls}"${role}>` +
         `<span class="t num">${esc(e.utc || "")}</span>` +
         `<span class="sev">${sevTxt}</span>` +
         `<span class="src">${esc((e.subsystem || e.source || "").toUpperCase())}</span>` +
         `<span>${esc(e.name || "")}${e.name && (e.description || e.text) ? " — " : ""}` +
         `${esc(e.description || e.text || "")}${badge}</span>` +
         `</div>`;
}

/* ── 9. SCHEMATIC BINDING ──────────────────────────────────────────────── */

/**
 * bindSchematic(svgRoot, state) -> void
 *
 * The ONE deliberately impure export (it must walk a live SVG DOM).
 * Idempotent: call it on every state update.
 *
 * Walks the schematic for:
 *  - [data-param="0xHHHH"] nodes: sets the node's status class from
 *    state.param_limit_state / staleness, and writes the value into a child
 *    <text class="vl"> (formatted, with units from data-units attr if set).
 *  - [data-nav="pageid"] nodes: adds click + Enter/Space handlers that
 *    dispatch a bubbling CustomEvent "ds-nav" with detail {page} on the
 *    node — pages listen once at the document level and route
 *    (schematic-as-navigation, plan §2.1). Adds tabindex/role/cursor.
 *
 * @param {SVGElement|Element} svgRoot — the inlined schematic root
 *        (e.g. the <svg> from modern/schematics.svg for the shown page).
 * @param {object} state — the WS `state` message `data` object (needs
 *        .params, .params_age, .param_limit_state; tolerates absence).
 */
function hasFiniteNumber(v) {
  return v !== null && v !== undefined && Number.isFinite(Number(v));
}
export function bindSchematic(svgRoot, state) {
  if (!svgRoot) return;
  const st = state || {};
  const params = st.params || {};
  const limitState = st.param_limit_state || {};
  const ages = st.params_age || {};
  svgRoot.querySelectorAll("[data-param]").forEach((node) => {
    const hex = node.getAttribute("data-param");
    const val = params[hex];
    const id = parseInt(hex, 16);
    const age = ages[String(id)];
    // Same four-state verdict as the tables when the caller supplies one
    // (state.param_verdicts): a schematic that prints the last known number
    // for a SID nobody enabled is the most confident possible way to be wrong.
    const fr = (st.param_verdicts && st.param_verdicts[hex])
      || freshness4(age !== undefined ? age : (val !== undefined ? 0 : null));
    const disabled = fr === "disabled";
    const stale = fr === "stale" || fr === "nodata" || disabled || val === undefined || val === null;
    const lc = stale ? "" : limitClass(limitState[hex] || "");
    node.classList.remove("warn", "alarm", "stale");
    if (stale) node.classList.add("stale");
    else if (lc === "a") node.classList.add("alarm");
    else if (lc === "w") node.classList.add("warn");
    const vl = node.querySelector(".vl");
    if (vl) {
      const units = node.getAttribute("data-units") || "";
      // Discrete parameters read as their state name. The AOCS CORE box on the
      // L2 schematic is `data-param="0x020F"` — it showed a bare "3" where the
      // operator needs "COARSE_SUN". States come from the parameter catalogue
      // via state.param_states; a unit suffix on a state name is meaningless.
      const stt = st.param_states && st.param_states[hex];
      const code = hasFiniteNumber(val) ? Math.round(Number(val)) : null;
      if (disabled) vl.textContent = tText("NOT ENABLED");
      else if (!hasFiniteNumber(val)) vl.textContent = tText("no data");
      // stale: the LAST value stays, the node's .stale class dims it (dashed
      // outline, italic) — a blank box hides what the spacecraft last said.
      else if (stt && code !== null && stt[String(code)] !== undefined) {
        vl.textContent = `${stt[String(code)]} (${code})`;
      } else vl.textContent = _num(Number(val)) + (units ? " " + units : "");
    }
  });
  svgRoot.querySelectorAll("[data-nav]").forEach((node) => {
    if (node.__dsNavBound) return;
    node.__dsNavBound = true;
    node.setAttribute("tabindex", "0");
    node.setAttribute("role", "link");
    const go = () => node.dispatchEvent(new CustomEvent("ds-nav", {
      bubbles: true, detail: { page: node.getAttribute("data-nav") },
    }));
    node.addEventListener("click", go);
    node.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); go(); }
    });
  });
}

/* ── 9b. LANGUAGE TOGGLE (EN | FR) — additive 2026-10 (i18n S0) ─────────── */

const LANG_NAMES = { en: "English", fr: "Français" };

/**
 * renderLangToggle(current, langs) -> html string
 *
 * Compact segmented pill "EN | FR" for a console top bar. Pure. The pressed
 * segment (aria-pressed="true") is the current language; colour is not the
 * only cue (pressed = raised fill + underline). Codes are identifiers and
 * are never translated; each button carries its language's own name
 * (`lang` + aria-label) so screen readers pronounce it correctly.
 *
 * @param {string} [current] — "en"|"fr" (default: i18n.js getLang()).
 * @param {string[]} [langs] — default i18n.js LANGS.
 * @returns {string} `<div class="ds-lang" role="group">...`
 */
export function renderLangToggle(current, langs) {
  const cur = current || getLang();
  return `<div class="ds-lang" role="group" aria-label="${esc(tText("Language"))}">` +
    (langs || LANGS).map((l) =>
      `<button type="button" data-lang="${esc(l)}" lang="${esc(l)}" ` +
      `aria-pressed="${l === cur}" aria-label="${esc(LANG_NAMES[l] || l)}" ` +
      `title="${esc(LANG_NAMES[l] || l)}">${esc(l.toUpperCase())}</button>`).join("") +
    `</div>`;
}

/**
 * mountLangToggle(host) -> host
 *
 * The second deliberately impure export: renders the toggle into `host`,
 * wires click (and Left/Right arrow keys between the segments) to
 * i18n.js setLang(), and re-renders on every `smo:langchange` so two
 * toggles on one page stay in step. Tab/Enter/Space are native <button>.
 *
 * @param {Element|null} host — e.g. <span id="lang-toggle"> in the top bar.
 */
export function mountLangToggle(host) {
  if (!host || host.__dsLangBound) return host;
  host.__dsLangBound = true;
  const draw = () => {
    const had = host.contains(document.activeElement);
    host.innerHTML = renderLangToggle(getLang());
    if (had) { const b = host.querySelector('[aria-pressed="true"]'); if (b) b.focus(); }
  };
  host.addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-lang]");
    if (b && b.getAttribute("aria-pressed") !== "true") setLang(b.getAttribute("data-lang"));
  });
  host.addEventListener("keydown", (ev) => {
    if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
    const bs = Array.from(host.querySelectorAll("[data-lang]"));
    const i = bs.indexOf(document.activeElement);
    if (i < 0) return;
    ev.preventDefault();
    bs[(i + (ev.key === "ArrowRight" ? 1 : bs.length - 1)) % bs.length].focus();
  });
  onLangChange(draw);
  draw();
  return host;
}

/* ── 9c. STATE VOCABULARY (brief §1.3) — additive 2026-11 ─────────────────
 * One function per state concept, shared by every console. The gallery
 * (/static/shared/gallery.html) shows each in every state, dark and light.
 *
 *   valueState(value, ageS, opts)   -> "live"|"degraded"|"stale"|"nodata"|"off"
 *   renderValue(value, opts)        -> a readout in its data state
 *   renderAge(ageS, opts)           -> the dashed age chip ("59 s")
 *   renderNoData(opts)              -> "no data" / "not enabled" tag
 *   renderFlag(limitState, opts)    -> triangle + ISA code (H/HH/L/LL)
 *   renderGauge(value, limits, opts)-> compact bar against limits + value
 *   renderButton(opts)              -> enabled|disabled|armed|active button
 *   renderField(opts)               -> labelled input/select/checkbox
 *   renderTabs(tabs, activeId, opts)-> tablist (wire with mountTabs)
 *   renderDisclosure(summary, body, opts) -> <details> that opens downward
 *   renderBanner(kind, text, opts)  -> full-width state strip
 *   renderLinkBanner(link, opts)    -> from state.js linkState()/linkLimited()
 *   renderModeBanner(mode)          -> from state.js modeState()
 * Impure (DOM): setDisabled, setEnabled, armButton, installReasonTips,
 * mountTabs. installReasonTips(document) runs on import in a browser.
 * ------------------------------------------------------------------------- */

let _seq = 0;
const _uid = (p) => `${p}-${(++_seq).toString(36)}`;
const _finite = (v) => v !== null && v !== undefined && v !== "" && Number.isFinite(Number(v));

function _limitGlyph(state) {
  const s = String(state || "");
  const dir = s.endsWith("low") ? "down" : "up";
  return (s.startsWith("red") ? "alarm-" : "warn-") + dir;
}

/* ISA-18.2 limit codes: identifiers, never translated. */
function _isaCode(state) {
  return { red_high: "HH", yellow_high: "H", yellow_low: "L", red_low: "LL" }[state] || "";
}

function _limitText(state) {
  return {
    red_high: tText("above the alarm limit"), yellow_high: tText("above the caution limit"),
    yellow_low: tText("below the caution limit"), red_low: tText("below the alarm limit"),
  }[state] || "";
}

/**
 * valueState(value, ageS, opts) -> "live"|"degraded"|"stale"|"nodata"|"off"
 *
 * The one data-state verdict for a displayed value. `opts.verdict` (the
 * caller's own four-state verdict, e.g. from the MCS staleness policy, or
 * "disabled" for an HK structure that is not enabled) wins; otherwise the
 * age is classified by state.js freshness() with `opts.intervalS`. A value
 * with no age at all is taken as live (the caller vouches for it); no value
 * is "nodata" whatever the age says.
 */
export function valueState(value, ageS, opts = {}) {
  const vd = opts.verdict;
  if (vd === "disabled" || vd === "off") return "off";
  if (!_finite(value) && (opts.eng === undefined || opts.eng === null)) return "nodata";
  if (vd === "stale") return "stale";
  if (vd === "degraded") return "degraded";
  if (vd === "fresh" || vd === "live") return "live";
  if (ageS === undefined || ageS === null) return "live";
  const f = freshness4(ageS, { intervalS: opts.intervalS, policy: opts.policy });
  return f === "fresh" || f === "nodata" ? "live" : f;
}

/**
 * renderAge(ageS, {degraded}) -> html string
 * The age chip that follows a stale (dashed grey) or degraded (amber) value.
 * Screen readers hear "stale value, age 59 s".
 */
export function renderAge(ageS, opts = {}) {
  const txt = _age(ageS);
  return `<span class="ds-age${opts.degraded ? " degraded" : ""}" ` +
         `title="${esc(tText("last value received {{age}} ago", { age: txt }))}">` +
         `<span class="ds-sr">${opts.degraded ? t("late value, age") : t("stale value, age")} </span>${esc(txt)}</span>`;
}

/**
 * renderNoData({off, label}) -> html string
 * "no data": never received (never an em-dash). off:true -> "not enabled"
 * with the hollow-ring glyph (the HK structure that carries it is disabled).
 */
export function renderNoData(opts = {}) {
  const label = opts.label || (opts.off ? tText("not enabled") : tText("no data"));
  return `<span class="ds-nodata${opts.off ? " off" : ""}"` +
         (opts.off ? ` title="${esc(tText("HK SID carrying this parameter is disabled"))}"` : "") + `>` +
         (opts.off ? glyph("off") : "") + `${esc(label)}</span>`;
}

/**
 * renderFlag(limitState, {glyph}) -> html string
 * Out-of-limits marker: triangle (hollow caution, filled alarm, pointing to
 * the side of the band) + ISA code + a spoken explanation. "" when nominal.
 */
export function renderFlag(limitState, opts = {}) {
  const lc = limitClass(limitState);
  if (!lc) return "";
  const cls = lc === "a" ? "is-alarm" : "is-caution";
  return `<span class="ds-flag ${cls}" title="${esc(_limitText(limitState))}">` +
         (opts.glyph === false ? "" : glyph(_limitGlyph(limitState))) +
         `${_isaCode(limitState)}<span class="ds-sr"> ${esc(_limitText(limitState))}</span></span>`;
}

/**
 * renderValue(value, opts) -> html string
 *
 * A single readout in its data state, as ONE element (`.ds-readout`, or the
 * `.ds-nodata` tag): live (bright mono), caution/alarm
 * (colour + triangle + ISA code), degraded (amber age chip), stale (last
 * value, dim italic, dashed age chip), no data, not enabled.
 *
 * @param {number|null|undefined} value
 * @param {{units?:string, digits?:number, eng?:string, ageS?:number,
 *          verdict?:string, intervalS?:number, limitState?:string,
 *          limits?:object, cls?:string}} [opts]
 *        limitState — "nominal"|"yellow_low"|... (else classified from
 *        opts.limits when given); eng — discrete state text to show instead
 *        of the number.
 */
export function renderValue(value, opts = {}) {
  const vs = valueState(value, opts.ageS, opts);
  if (vs === "nodata") return renderNoData();
  if (vs === "off") return renderNoData({ off: true });
  const band = _band(opts.limits);
  const state = opts.limitState || (band && _finite(value) ? _classify(Number(value), band) : "");
  const live = vs === "live" || vs === "degraded";
  const lc = live ? limitClass(state) : "";
  const cls = ["ds-value", lc === "a" ? "is-alarm" : lc === "w" ? "is-caution" : "",
    vs === "stale" ? "is-stale" : "", opts.cls || ""].filter(Boolean).join(" ");
  const txt = opts.eng !== undefined && opts.eng !== null ? esc(String(opts.eng))
    : _fmtDigits(Number(value), opts.digits);
  return `<span class="ds-readout"><span class="${cls}">${lc ? glyph(_limitGlyph(state)) : ""}${txt}` +
         (opts.units ? `<span class="u">${esc(opts.units)}</span>` : "") + `</span>` +
         (lc ? renderFlag(state, { glyph: false }) : "") +
         (vs === "stale" || vs === "degraded" ? renderAge(opts.ageS, { degraded: vs === "degraded" }) : "") +
         `</span>`;
}

function _fmtDigits(v, digits) {
  if (!Number.isFinite(v)) return "—";
  return Number.isInteger(digits) ? v.toFixed(digits) : _num(v);
}

/**
 * renderGauge(value, limits, opts) -> html string
 *
 * The compact flight-deck readout: label, a scale with the caution/alarm
 * ranges drawn as bands under it, a neutral fill up to the value (status
 * colour only when out of limits), and the exact value beside it.
 *
 * @param {number|null} value
 * @param {object|null} limits — {yellow_low, yellow_high, red_low, red_high}
 *        (any subset) plus optional lo/hi scale range.
 * @param {{label?:string, units?:string, digits?:number, lo?:number,
 *          hi?:number, ageS?:number, verdict?:string, intervalS?:number,
 *          reason?:string}} [opts] — reason: the gauge is disabled (e.g.
 *          "Payload off"), shown on hover and focus.
 */
export function renderGauge(value, limits, opts = {}) {
  const band = _band(limits) || {};
  const vs = opts.reason ? "off" : valueState(value, opts.ageS, opts);
  const has = _finite(value) && vs !== "nodata" && vs !== "off";
  const v = has ? Number(value) : null;
  const L = limits || {};
  const bounds = [band.yellow_low, band.yellow_high, band.red_low, band.red_high].filter(_finite);
  let lo = opts.lo ?? L.lo, hi = opts.hi ?? L.hi;
  if (lo === undefined || hi === undefined) {
    const mn = Math.min(...bounds, v ?? Infinity), mx = Math.max(...bounds, v ?? -Infinity);
    const span = Number.isFinite(mx - mn) ? (mx - mn || Math.abs(mx) || 1) : 1;
    if (lo === undefined) lo = Number.isFinite(mn) ? mn - span * 0.15 : 0;
    if (hi === undefined) hi = Number.isFinite(mx) ? mx + span * 0.15 : 1;
  }
  const pct = (x) => Math.max(0, Math.min(100, ((x - lo) / (hi - lo || 1)) * 100)).toFixed(1);
  let marks = "";
  const bandSeg = (a, b, c) => `<span class="band ${c}" style="left:${pct(a)}%;width:${(pct(b) - pct(a)).toFixed(1)}%"></span>`;
  if (_finite(band.red_low)) marks += bandSeg(lo, band.red_low, "r");
  if (_finite(band.yellow_low)) marks += bandSeg(_finite(band.red_low) ? band.red_low : lo, band.yellow_low, "y");
  if (_finite(band.yellow_high)) marks += bandSeg(band.yellow_high, _finite(band.red_high) ? band.red_high : hi, "y");
  if (_finite(band.red_high)) marks += bandSeg(band.red_high, hi, "r");
  const state = has ? (_band(limits) ? _classify(v, band) : "") : "";
  const live = vs === "live" || vs === "degraded";
  const lc = live ? limitClass(state) : "";
  const cls = ["ds-gauge", lc === "a" ? "is-alarm" : lc === "w" ? "is-caution" : "",
    vs === "stale" ? "is-stale" : "", vs === "nodata" ? "is-nodata" : "",
    vs === "off" ? "is-disabled" : ""].filter(Boolean).join(" ");
  const fill = has ? `<span class="fill" style="width:${pct(v)}%"></span>` : "";
  const label = opts.label || "";
  const aria = has ? tText("value {{value}} of range {{lo}} to {{hi}}", { value: _num(v), lo: _num(lo), hi: _num(hi) })
    : tText("no data");
  const val = opts.reason ? renderNoData({ label: tText("off") })
    : renderValue(value, { units: opts.units, digits: opts.digits, ageS: opts.ageS,
                           verdict: opts.verdict, intervalS: opts.intervalS, limitState: state });
  const why = opts.reason ? _uid("ds-why") : "";
  return `<div class="${cls}${label ? "" : " nolabel"}"` +
         (opts.reason ? ` data-reason="${esc(opts.reason)}" tabindex="0" aria-describedby="${why}"` : "") + `>` +
         (label ? `<span class="nm">${esc(label)}</span>` : "") +
         `<span class="tr" role="img" aria-label="${esc(label ? label + ": " + aria : aria)}">${fill}${marks}</span>` +
         val +
         (opts.reason ? `<span id="${why}" class="ds-sr">${esc(opts.reason)}</span>` : "") +
         `</div>`;
}

/**
 * renderButton(opts) -> html string
 *
 * @param {{label:string, kind?:"default"|"primary"|"critical"|"ghost",
 *          state?:"enabled"|"disabled"|"armed"|"active", reason?:string,
 *          id?:string, act?:string, size?:"sm", toggle?:boolean,
 *          seconds?:number, attrs?:string}} o
 *   state "disabled" needs `reason` (shown on hover AND focus, read by
 *   screen readers through aria-describedby). The button stays focusable
 *   (aria-disabled, not the disabled attribute) and clicks are swallowed.
 *   state "armed" renders the armed look statically (armButton() animates
 *   it live); state "active" fills with the accent: say what is running in
 *   the label ("Running", "Tracking"). toggle:true adds aria-pressed.
 *   `attrs` is trusted extra attribute markup.
 */
export function renderButton(o = {}) {
  const st = o.state || "enabled";
  const kind = o.kind && o.kind !== "default" ? o.kind : "";
  const cls = ["ds-btn", kind, o.size === "sm" ? "sm" : "",
    st === "active" ? "is-active" : "", st === "armed" ? "is-armed" : ""].filter(Boolean).join(" ");
  const why = st === "disabled" ? (o.id ? `${o.id}-why` : _uid("ds-why")) : "";
  const label = esc(o.label ?? "");
  const inner = st === "armed"
    ? `${t("Confirm: {{action}}", { action: o.label ?? "" })} <span class="ds-arm-t">${o.seconds ?? 5} s</span>` +
      `<span class="ds-arm-bar"></span>`
    : (st === "active" ? `<span class="ds-run" aria-hidden="true"></span>` : "") + label;
  return `<button type="button" class="${cls}"` +
         (o.id ? ` id="${esc(o.id)}"` : "") +
         (o.act ? ` data-act="${esc(o.act)}"` : "") +
         (o.toggle ? ` aria-pressed="${st === "active"}"` : "") +
         (st === "disabled" ? ` aria-disabled="true" data-reason="${esc(o.reason || "")}" aria-describedby="${why}"` : "") +
         (o.attrs ? " " + o.attrs : "") + `>${inner}</button>` +
         (st === "disabled" ? `<span id="${why}" class="ds-sr" hidden>${esc(o.reason || "")}</span>` : "");
}

/**
 * renderField(opts) -> html string
 *
 * @param {{label:string, id?:string, type?:"number"|"text"|"select"|"checkbox",
 *          value?:any, options?:(string|{value,label})[], units?:string,
 *          hint?:string, error?:string, placeholder?:string,
 *          state?:"enabled"|"disabled"|"invalid", reason?:string,
 *          name?:string, checked?:boolean}} o
 *   disabled: aria-disabled + readonly (still focusable, reason on hover and
 *   focus); invalid: alarm border, aria-invalid, and the error text with a
 *   triangle under the field ("Enter a value between 0 and 100").
 */
export function renderField(o = {}) {
  const id = o.id || _uid("ds-f");
  const st = o.state || (o.error ? "invalid" : "enabled");
  const dis = st === "disabled";
  const inv = st === "invalid";
  const desc = [o.hint ? `${id}-hint` : "", inv && o.error ? `${id}-err` : "", dis ? `${id}-why` : ""]
    .filter(Boolean).join(" ");
  const common = ` id="${esc(id)}"` + (o.name ? ` name="${esc(o.name)}"` : "") +
    (desc ? ` aria-describedby="${desc}"` : "") +
    (dis ? ` aria-disabled="true" data-reason="${esc(o.reason || "")}"` : "") +
    (inv ? ` aria-invalid="true"` : "");
  const extra = (o.hint ? `<span class="hint" id="${id}-hint">${esc(o.hint)}</span>` : "") +
    (inv && o.error ? `<span class="err" id="${id}-err">${glyph("alarm-up")}${esc(o.error)}</span>` : "") +
    (dis ? `<span class="ds-sr" id="${id}-why" hidden>${esc(o.reason || "")}</span>` : "");
  const wcls = ["ds-field", dis ? "is-disabled" : "", inv ? "is-invalid" : ""].filter(Boolean).join(" ");
  if (o.type === "checkbox") {
    return `<div class="${wcls}"><label class="ds-check${dis ? " is-disabled" : ""}">` +
           `<input type="checkbox"${common}${o.checked ? " checked" : ""}${dis ? ` onclick="return false"` : ""}>` +
           `${esc(o.label || "")}</label>${extra}</div>`;
  }
  let control;
  if (o.type === "select") {
    const opts = (o.options || []).map((x) => {
      const v = typeof x === "object" ? x.value : x, l = typeof x === "object" ? x.label : x;
      return `<option value="${esc(v)}"${String(v) === String(o.value ?? "") ? " selected" : ""}>${esc(l)}</option>`;
    }).join("");
    control = `<select class="ds-select"${common}>${opts}</select>`;
  } else {
    const isNum = o.type !== "text";
    control = `<span class="ds-input-wrap"><input class="ds-input${isNum ? "" : " text"}" ` +
      `type="text"${isNum ? ` inputmode="decimal"` : ""}${common}` +
      ` value="${esc(o.value ?? "")}"` + (o.placeholder ? ` placeholder="${esc(o.placeholder)}"` : "") +
      (dis ? " readonly" : "") + `>` + (o.units ? `<span class="u">${esc(o.units)}</span>` : "") + `</span>`;
  }
  return `<div class="${wcls}"><label for="${esc(id)}">${esc(o.label || "")}</label>${control}${extra}</div>`;
}

/**
 * renderTabs(tabs, activeId, {label}) -> html string
 * @param {{id:string, label:string, count?:number|string, countKind?:string,
 *          reason?:string}[]} tabs — reason => the tab is disabled.
 * Wire keyboard (arrows, Home/End) and selection with mountTabs().
 */
export function renderTabs(tabs, activeId, opts = {}) {
  return `<div class="ds-tabs" role="tablist"` +
    (opts.label ? ` aria-label="${esc(opts.label)}"` : "") + `>` +
    (tabs || []).map((tb) => {
      const sel = tb.id === activeId;
      return `<button type="button" role="tab" class="ds-tab" id="tab-${esc(tb.id)}" data-tab="${esc(tb.id)}" ` +
        `aria-selected="${sel}" tabindex="${sel ? 0 : -1}"` +
        (opts.panel ? ` aria-controls="${esc(opts.panel)}"` : "") +
        (tb.reason ? ` aria-disabled="true" data-reason="${esc(tb.reason)}"` : "") + `>` +
        esc(tb.label) +
        (tb.count !== undefined && tb.count !== null
          ? ` ${renderChip({ kind: tb.countKind || "neutral", label: String(tb.count) })}` : "") +
        `</button>`;
    }).join("") + `</div>`;
}

/**
 * renderDisclosure(summary, bodyHtml, {open, meta}) -> html string
 * Progressive disclosure: a native <details> that opens DOWNWARD below its
 * summary, so nothing above it moves. `bodyHtml` is trusted markup.
 */
export function renderDisclosure(summary, bodyHtml, opts = {}) {
  return `<details class="ds-disclosure"${opts.open ? " open" : ""}>` +
         `<summary>${esc(summary)}` +
         (opts.meta ? `<span class="r">${esc(opts.meta)}</span>` : "") +
         `</summary><div class="bd">${bodyHtml || ""}</div></details>`;
}

const BANNER = {
  ok: ["ok", "ack"], caution: ["is-caution", "warn-up"], alarm: ["is-alarm", "alarm-up"],
  stale: ["is-stale", "stale"], nodata: ["is-nodata", "off"], info: ["info", "commanded"],
  neutral: ["", ""],
};

/**
 * renderBanner(kind, text, {meta, metaHtml, html, role, glyph}) -> html string
 * meta: a string or an array of strings (each its own right-aligned item).
 * kind: "ok"|"caution"|"alarm"|"stale"|"nodata"|"info"|"neutral".
 * `text` is escaped; pass `html` (trusted) instead for markup. Glyph +
 * colour + text, so it reads in greyscale.
 */
export function renderBanner(kind, text, opts = {}) {
  const [cls, g0] = BANNER[kind] || BANNER.neutral;
  const g = opts.glyph ?? g0;
  return `<div class="ds-banner ${cls}"${opts.role ? ` role="${esc(opts.role)}"` : ""}>` +
         (g ? glyph(g) : "") + `<span>${opts.html ?? esc(text ?? "")}</span>` +
         (opts.metaHtml || (opts.meta && opts.meta.length)
           ? `<span class="r">${opts.metaHtml ?? [].concat(opts.meta).filter(Boolean)
               .map((m) => `<span>${esc(m)}</span>`).join("")}</span>` : "") +
         `</div>`;
}

/**
 * renderLinkBanner(link, {limited}) -> html string
 * @param {object} link — state.js linkState(state).
 * @param {{limited?:{limited:boolean, speed:number}, frameIntervalS?:number}} [opts]
 *        frameIntervalS — expected TM frame cadence in contact (default 1 s);
 *        limited — state.js
 *        linkLimited(state): at sim speed > 1 the console is link-limited,
 *        values are held, not lost — one caution banner says so.
 */
export function renderLinkBanner(link, opts = {}) {
  const ls = link || {};
  const gs = ls.gs ? ` <span class="k">${esc(ls.gs)}</span>` : "";
  const age = _finite(ls.ageS) ? renderAge(ls.ageS) : "";
  if (opts.limited && opts.limited.limited) {
    return renderBanner("caution", "", { html: t("Link-limited at ×{{speed}}: values are held, not lost",
      { speed: opts.limited.speed }), metaHtml: age });
  }
  // Frames arrive every second or so in contact: judge their age on that
  // cadence (state.js floors: 10 s fresh, 20 s stale), not the aperiodic one.
  const tmStale = ls.tm === "stale" ||
    (_finite(ls.ageS) && freshness4(ls.ageS, { intervalS: opts.frameIntervalS ?? 1 }) === "stale");
  if (ls.contact && tmStale) {
    return renderBanner("stale", "", { html: t("In contact") + gs + " " + t("telemetry stale"), metaHtml: age });
  }
  if (ls.contact) {
    return renderBanner("ok", "", { glyph: "lock", html: t("In contact") + gs,
      meta: ls.source ? tText("source: {{src}}", { src: ls.source }) : "" });
  }
  return renderBanner("nodata", t("No contact"), { metaHtml: age ? tText("last frame") + " " + age : "" });
}

/**
 * renderModeBanner(mode) -> html string
 * @param {object} mode — state.js modeState(state). SAFE -> caution,
 *        EMERGENCY -> alarm, FDIR level >= 2 -> at least caution, unknown ->
 *        "no data". Mode names are identifiers (never translated).
 */
export function renderModeBanner(mode) {
  const ms = mode || {};
  const lbl = t("Spacecraft mode");
  if (!ms.mode) return renderBanner("nodata", "", { html: `${lbl} ${renderNoData()}` });
  const kind = ms.mode === "EMERGENCY" ? "alarm" : ms.contingency ? "caution" : "neutral";
  const fdir = _finite(ms.fdirLevel) && ms.fdirLevel > 0
    ? tText("FDIR level {{n}}", { n: ms.fdirLevel }) : "";
  return renderBanner(kind, "", { html: `${lbl} <span class="k">${esc(ms.mode)}</span>`,
    meta: [fdir, ms.source || ""] });
}

/* ── impure helpers (DOM) ─────────────────────────────────────────────── */

/**
 * setDisabled(el, reason) / setEnabled(el)
 * Disable a control WITH its reason: aria-disabled (stays focusable, so the
 * reason is reachable from the keyboard), data-reason (tooltip on hover and
 * focus), aria-describedby -> a hidden span holding the reason. Activation
 * is swallowed by installReasonTips()'s guard. setEnabled undoes all of it.
 */
export function setDisabled(el, reason) {
  if (!el) return el;
  el.setAttribute("aria-disabled", "true");
  el.setAttribute("data-reason", reason || "");
  if (el.disabled) el.disabled = false;
  if (typeof document !== "undefined" && document.createElement) {
    const id = (el.id || _uid("ds-el")) + "-why";
    let sp = document.getElementById ? document.getElementById(id) : null;
    if (!sp) {
      sp = document.createElement("span");
      sp.id = id; sp.className = "ds-sr"; sp.hidden = true;
      if (el.insertAdjacentElement) el.insertAdjacentElement("afterend", sp);
    }
    sp.textContent = reason || "";
    const d = (el.getAttribute("aria-describedby") || "").split(/\s+/).filter((x) => x && x !== id);
    el.setAttribute("aria-describedby", [...d, id].join(" "));
  }
  return el;
}

export function setEnabled(el) {
  if (!el) return el;
  el.removeAttribute("aria-disabled");
  el.removeAttribute("data-reason");
  const d = (el.getAttribute("aria-describedby") || "").split(/\s+/).filter((x) => x && !x.endsWith("-why"));
  if (d.length) el.setAttribute("aria-describedby", d.join(" "));
  else el.removeAttribute("aria-describedby");
  return el;
}

function _announce(msg) {
  if (typeof document === "undefined" || !document.body) return;
  let r = document.getElementById("ds-live");
  if (!r) {
    r = document.createElement("div");
    r.id = "ds-live"; r.className = "ds-sr";
    r.setAttribute("aria-live", "polite");
    document.body.appendChild(r);
  }
  r.textContent = "";
  setTimeout(() => { r.textContent = msg; }, 30);
}

/**
 * armButton(el, {seconds, onExecute, onDisarm}) -> {disarm(), armed()}
 *
 * The two-step for critical commands (P9). First activation ARMS the button
 * for `seconds` (default 5): amber border, label "Confirm: <label>", a
 * countdown and a draining bar. A second activation inside the window calls
 * onExecute(event); Esc, the timeout, or the button becoming disabled
 * disarms. Screen readers are told what to do. Works on any <button>.
 */
export function armButton(el, opts = {}) {
  if (!el || el.__dsArm) return el && el.__dsArm;
  const secs = opts.seconds ?? 5;
  const orig = el.innerHTML;
  const origText = (el.textContent || "").trim();
  let timer = null, tick = null, until = 0;
  const armed = () => el.classList.contains("is-armed");
  function disarm(silent) {
    clearTimeout(timer); clearInterval(tick); timer = tick = null;
    if (!armed()) return;
    el.classList.remove("is-armed");
    el.innerHTML = orig;
    if (!silent) { _announce(tText("Disarmed")); if (opts.onDisarm) opts.onDisarm(); }
  }
  function arm() {
    until = Date.now() + secs * 1000;
    el.classList.add("is-armed");
    el.innerHTML = `${t("Confirm: {{action}}", { action: origText })} ` +
      `<span class="ds-arm-t">${secs} s</span><span class="ds-arm-bar"></span>`;
    const bar = el.querySelector(".ds-arm-bar"), cnt = el.querySelector(".ds-arm-t");
    if (bar) {
      bar.style.transform = "scaleX(1)";
      bar.getBoundingClientRect();
      bar.style.transition = `transform ${secs}s linear`;
      bar.style.transform = "scaleX(0)";
    }
    tick = setInterval(() => {
      const left = Math.max(0, Math.ceil((until - Date.now()) / 1000));
      if (cnt) cnt.textContent = `${left} s`;
      if (el.getAttribute("aria-disabled") === "true") disarm();
    }, 200);
    timer = setTimeout(() => disarm(), secs * 1000);
    _announce(tText("Armed. Press again within {{s}} s to execute, or Esc to cancel.", { s: secs }));
  }
  el.addEventListener("click", (ev) => {
    if (el.getAttribute("aria-disabled") === "true") return;
    if (armed()) { disarm(true); if (opts.onExecute) opts.onExecute(ev); }
    else arm();
  });
  el.addEventListener("keydown", (ev) => { if (ev.key === "Escape" && armed()) { ev.preventDefault(); disarm(); } });
  el.__dsArm = { disarm: () => disarm(), armed };
  return el.__dsArm;
}

/**
 * installReasonTips(root) — once per document (done on import in a browser).
 * Shows the data-reason of any element on hover and on keyboard focus in a
 * fixed-position tooltip (never clipped by a scroll panel), hides on Esc,
 * scroll and leave; and swallows click/Enter/Space/typing on anything
 * aria-disabled="true" so a disabled control can stay focusable.
 */
export function installReasonTips(root) {
  const doc = root || (typeof document !== "undefined" ? document : null);
  if (!doc || typeof doc.addEventListener !== "function" || doc.__dsTips) return;
  doc.__dsTips = true;
  let tip = null, cur = null;
  const ensure = () => {
    if (tip || !doc.body) return tip;
    tip = doc.createElement("div");
    tip.className = "ds-tip"; tip.hidden = true;
    tip.setAttribute("aria-hidden", "true");   // the reason is read via aria-describedby
    doc.body.appendChild(tip);
    return tip;
  };
  const show = (el) => {
    const why = el.getAttribute("data-reason");
    if (!why || !ensure()) return;
    cur = el;
    tip.textContent = why;
    tip.hidden = false;
    const r = el.getBoundingClientRect();
    const w = tip.offsetWidth, h = tip.offsetHeight;
    const vw = doc.documentElement.clientWidth, vh = doc.documentElement.clientHeight;
    let top = r.bottom + 6;
    if (top + h > vh - 4) top = r.top - h - 6;
    tip.style.top = `${Math.max(4, top)}px`;
    tip.style.left = `${Math.max(4, Math.min(r.left, vw - w - 4))}px`;
  };
  const hide = () => { cur = null; if (tip) tip.hidden = true; };
  doc.addEventListener("mouseover", (ev) => {
    const el = ev.target.closest && ev.target.closest("[data-reason]");
    if (el && el !== cur) show(el); else if (!el && cur && doc.activeElement !== cur) hide();
  });
  doc.addEventListener("focusin", (ev) => {
    const el = ev.target.closest && ev.target.closest("[data-reason]");
    if (el) show(el); else hide();
  });
  doc.addEventListener("focusout", hide);
  doc.addEventListener("scroll", hide, true);
  const blocked = (ev) => ev.target.closest && ev.target.closest('[aria-disabled="true"]');
  for (const type of ["click", "mousedown"]) {
    doc.addEventListener(type, (ev) => {
      if (blocked(ev)) { ev.preventDefault(); ev.stopImmediatePropagation(); }
    }, true);
  }
  doc.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") hide();
    if (blocked(ev) && !["Tab", "Shift", "Escape"].includes(ev.key)) {
      ev.preventDefault(); ev.stopImmediatePropagation();
    }
  }, true);
}

/**
 * mountTabs(host, onSelect) -> host
 * Wires a renderTabs() tablist: click and Left/Right/Home/End move the
 * selection (skipping disabled tabs, whose reason still shows on focus) and
 * call onSelect(id).
 */
export function mountTabs(host, onSelect) {
  if (!host || host.__dsTabs) return host;
  host.__dsTabs = true;
  const tabs = () => Array.from(host.querySelectorAll('[role="tab"]'));
  const select = (b) => {
    if (!b || b.getAttribute("aria-disabled") === "true") return;
    tabs().forEach((x) => { x.setAttribute("aria-selected", String(x === b)); x.tabIndex = x === b ? 0 : -1; });
    b.focus();
    if (onSelect) onSelect(b.getAttribute("data-tab"));
  };
  host.addEventListener("click", (ev) => select(ev.target.closest('[role="tab"]')));
  host.addEventListener("keydown", (ev) => {
    const all = tabs().filter((x) => x.getAttribute("aria-disabled") !== "true");
    const i = all.indexOf(document.activeElement);
    if (i < 0) return;
    const k = ev.key;
    const n = k === "ArrowRight" ? all[(i + 1) % all.length] : k === "ArrowLeft" ? all[(i - 1 + all.length) % all.length]
      : k === "Home" ? all[0] : k === "End" ? all[all.length - 1] : null;
    if (n) { ev.preventDefault(); select(n); }
  });
  return host;
}
if (typeof window !== "undefined" && typeof document !== "undefined" &&
    typeof document.addEventListener === "function") {
  try { installReasonTips(document); } catch (e) { /* non-browser DOM stub */ }
}

/* ── 10. TRANSPORT HELPERS ─────────────────────────────────────────────── */

/**
 * poller(fn, ms) -> {start(), stop(), kick()}
 *
 * Shared REST polling loop with backoff, so the three pages do not each
 * reinvent it. Calls `fn()` (async) every `ms`; on rejection, backs off
 * exponentially (x2 per consecutive failure, capped at 8x ms) and recovers
 * to the base cadence on the next success. Never overlaps calls.
 *
 * @param {() => Promise<any>} fn — the poll body (fetch + render).
 * @param {number} ms — base cadence in milliseconds.
 * @returns {{start:Function, stop:Function, kick:Function}} kick() runs one
 *          immediate cycle (e.g. after a user action) without disturbing
 *          the schedule.
 */
export function poller(fn, ms) {
  let timer = null, running = false, fails = 0, inFlight = false;
  async function cycle() {
    if (inFlight) return;
    inFlight = true;
    try { await fn(); fails = 0; }
    catch (e) { fails = Math.min(fails + 1, 3); }
    finally { inFlight = false; }
    if (running) {
      timer = setTimeout(cycle, ms * Math.pow(2, fails));  // 1x,2x,4x,8x
    }
  }
  return {
    start() { if (!running) { running = true; cycle(); } },
    stop() { running = false; if (timer) { clearTimeout(timer); timer = null; } },
    kick() { if (running) { if (timer) clearTimeout(timer); cycle(); } },
  };
}

/**
 * wsClient(url, handlers) -> {close(), send(obj), readyState()}
 *
 * Shared WebSocket wrapper with the house 3-second reconnect (preserved 1:1
 * from the classic consoles). Messages are JSON; each parsed message `m` is
 * dispatched to `handlers[m.type](m)` — every message type is a first-class
 * handler, no default swallowing (unknown types go to `handlers._unknown`
 * if provided).
 *
 * @param {string} url — e.g. `ws://host/ws?position=eps_tcs` (MCS; the
 *        `position` query param is part of the server contract) or the
 *        instructor `/ws`.
 * @param {object} handlers — {state, alarm, event, ... : (msg) => void}
 *        plus optional lifecycle callbacks:
 *        _open(), _close() (fired on close AND on failed connect — drive
 *        the WS dot from these), _unknown(msg).
 * @returns {{close:Function, send:Function, readyState:Function}}
 *        close() disables reconnection and closes; send(obj) JSON-serialises
 *        (silently dropped when not open — callers check readyState() when
 *        it matters); readyState() -> WebSocket.readyState or -1.
 */
export function wsClient(url, handlers) {
  const h = handlers || {};
  let ws = null, closed = false, timer = null;
  function connect() {
    if (closed) return;
    try { ws = new WebSocket(url); }
    catch (e) { retry(); return; }
    ws.onopen = () => { if (h._open) h._open(); };
    ws.onmessage = (ev) => {
      let m;
      try { m = JSON.parse(ev.data); } catch (e) { return; }
      const fn = h[m.type];
      if (fn) fn(m);
      else if (h._unknown) h._unknown(m);
    };
    ws.onclose = () => { if (h._close) h._close(); retry(); };
    ws.onerror = () => { try { ws.close(); } catch (e) { /* noop */ } };
  }
  function retry() {
    if (closed || timer) return;
    timer = setTimeout(() => { timer = null; connect(); }, 3000);  // house rule
  }
  connect();
  return {
    close() { closed = true; if (timer) clearTimeout(timer); if (ws) try { ws.close(); } catch (e) { /* noop */ } },
    send(obj) { if (ws && ws.readyState === 1) ws.send(JSON.stringify(obj)); },
    readyState() { return ws ? ws.readyState : -1; },
  };
}

/* ── internals ─────────────────────────────────────────────────────────── */

function _band(limits) {
  if (!limits) return null;
  const { yellow_low, yellow_high, red_low, red_high } = limits;
  if ([yellow_low, yellow_high, red_low, red_high]
      .every((v) => v === null || v === undefined)) return null;
  return { yellow_low, yellow_high, red_low, red_high };
}

function _classify(value, band) {
  if (band.red_low !== null && band.red_low !== undefined && value < band.red_low) return "red_low";
  if (band.red_high !== null && band.red_high !== undefined && value > band.red_high) return "red_high";
  if (band.yellow_low !== null && band.yellow_low !== undefined && value < band.yellow_low) return "yellow_low";
  if (band.yellow_high !== null && band.yellow_high !== undefined && value > band.yellow_high) return "yellow_high";
  return "nominal";
}

function _num(v) {
  if (!Number.isFinite(v)) return "—";
  const a = Math.abs(v);
  if (a !== 0 && (a < 0.01 || a >= 1e6)) return v.toExponential(2);
  if (Number.isInteger(v) && a < 1e6) return String(v);
  return v.toFixed(a < 10 ? 2 : a < 100 ? 1 : 0);
}

function _age(ageS) {
  if (ageS === null || ageS === undefined || !Number.isFinite(Number(ageS))) return "—";
  const a = Math.max(0, Number(ageS));
  if (a < 10) return `${a.toFixed(1)} s`;
  if (a < 100) return `${Math.round(a)} s`;
  if (a < 3600) return `${Math.floor(a / 60)} m ${String(Math.round(a % 60)).padStart(2, "0")} s`;
  return `${Math.floor(a / 3600)} h`;
}
