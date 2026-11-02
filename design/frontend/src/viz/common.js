/* ============================================================================
 * C2O pictorial displays — common.js  (source: shared/ui-viz/common.js)
 * ============================================================================
 * Small helpers shared by every view module: the stylesheet (token aliases
 * that resolve in BOTH the SMO consoles and SpaceCDF), SVG building, number
 * formatting with units, the verdict -> CSS class map, the text alternative
 * ("Values" table toggle) and a default translator.
 *
 * No imports. Views take `opts.t(en, vars)` for i18n: the consoles pass the
 * shared tText, SpaceCDF its i18next t; the default only interpolates.
 * ============================================================================ */

/** Default translator: English, {{var}} interpolation. */
export function tDefault(s, v) {
  return String(s).replace(/\{\{\s*([\w.]+)\s*\}\}/g, (m, k) => (v && v[k] !== undefined ? String(v[k]) : m));
}

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ESC[c]);

export const fin = (x) => x !== null && x !== undefined && Number.isFinite(Number(x));

/** fmt(12.345, 1) -> "12.3" with a true minus sign; null -> "". */
export function fmt(v, digits = 1) {
  if (!fin(v)) return "";
  const s = Number(v).toFixed(digits);
  return s.startsWith("-") && Number(s) !== 0 ? "−" + s.slice(1) : s.replace(/^-/, "");
}
/** Signed: +12.3 / −4.0. */
export function fmtSigned(v, digits = 1) {
  if (!fin(v)) return "";
  return (Number(v) > 0 ? "+" : "") + fmt(v, digits);
}
/** Duration in seconds -> "42 min" / "1 h 05 min" / "35 s". */
export function fmtDur(s) {
  if (!fin(s)) return "";
  const x = Math.max(0, Math.round(Number(s)));
  if (x < 90) return `${x} s`;
  const m = Math.round(x / 60);
  if (m < 90) return `${m} min`;
  return `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")} min`;
}
/** Value + unit with a thin space; units "%"/"°" attach directly. */
export function withUnit(text, units) {
  if (!text) return text;
  if (!units) return text;
  return units === "°" || units === "%" ? `${text}${units === "%" ? " %" : "°"}` : `${text} ${units}`;
}

/** Verdict -> modifier class shared with the design system's state names. */
export function stateClass(verdict) {
  return verdict === "stale" ? "is-stale" : verdict === "nodata" ? "is-nodata"
    : verdict === "disabled" ? "is-nodata" : verdict === "degraded" ? "is-degraded" : "";
}

/** Short age text for a stale value ("59 s", "4 min"). */
export function ageText(ageS) { return fin(ageS) ? fmtDur(ageS) : ""; }

/**
 * One readout as HTML: value + unit in its data state.
 *   fresh/degraded/design  value
 *   stale                  value, dimmed italic + " · 59 s"
 *   nodata                 the words "no data"
 */
export function readout(q, digits, t0, opts = {}) {
  const t = t0 || tDefault;
  if (!q || q.v === null || q.v === undefined || q.verdict === "nodata") {
    return `<span class="vz-v is-nodata">${esc(t(opts.reason || "no data"))}</span>`;
  }
  const txt = withUnit((opts.signed ? fmtSigned : fmt)(q.v, digits), opts.units ?? q.units);
  const cls = stateClass(q.verdict);
  const age = q.verdict === "stale" && fin(q.ageS) ? `<span class="vz-age"> · ${esc(ageText(q.ageS))}</span>` : "";
  const g = q.ground && opts.showGround ? `<span class="vz-gnd">${esc(t("ground"))}</span>` : "";
  return `<span class="vz-v ${cls}${opts.cls ? " " + opts.cls : ""}">${esc(txt)}${age}</span>${g}`;
}

/** SVG element string. */
export function s(tag, attrs = {}, inner = "") {
  const a = Object.entries(attrs).filter(([, v]) => v !== null && v !== undefined && v !== false)
    .map(([k, v]) => ` ${k}="${esc(v)}"`).join("");
  return `<${tag}${a}>${inner}</${tag}>`;
}

/** prefers-reduced-motion, evaluated at render time. */
export function reducedMotion() {
  try { return !!(globalThis.matchMedia && globalThis.matchMedia("(prefers-reduced-motion: reduce)").matches); }
  catch (e) { return false; }
}

let _uid = 0;
export function uid(prefix = "vz") { _uid += 1; return `${prefix}-${_uid}`; }

/**
 * Values table (the text alternative). rows: [[label, valueHtml, source], ...]
 */
export function valuesTable(rows, t0, caption) {
  const t = t0 || tDefault;
  return `<table class="vz-table">${caption ? `<caption>${esc(caption)}</caption>` : ""}
    <thead><tr><th scope="col">${esc(t("Quantity"))}</th><th scope="col" class="n">${esc(t("Value"))}</th>
    <th scope="col">${esc(t("Source"))}</th></tr></thead><tbody>` +
    rows.map(([k, v, src]) => `<tr><th scope="row">${esc(k)}</th><td class="n">${v}</td>` +
      `<td class="src">${esc(src || "")}</td></tr>`).join("") + `</tbody></table>`;
}

/**
 * Frame for a view: a header row (title, frame/convention chips, "Values"
 * toggle) over the picture and a hidden values table. Returns the parts.
 */
export function mountFrame(el, { title, t: t0, cls = "", toggle = true }) {
  ensureStyle();
  const t = t0 || tDefault;
  const id = uid("vzv");
  el.classList.add("c2o-viz");
  if (cls) cls.split(" ").forEach((c) => c && el.classList.add(c));
  el.innerHTML = `
    <div class="vz-head">${title ? `<span class="vz-title">${esc(title)}</span>` : ""}<span class="vz-chips"></span>
      ${toggle ? `<button type="button" class="vz-toggle" aria-pressed="false" aria-controls="${id}">${esc(t("Values"))}</button>` : ""}</div>
    <div class="vz-pic"></div>
    <div class="vz-values" id="${id}" hidden></div>`;
  const parts = {
    head: el.querySelector(".vz-head"), chips: el.querySelector(".vz-chips"),
    pic: el.querySelector(".vz-pic"), values: el.querySelector(".vz-values"),
    btn: el.querySelector(".vz-toggle"),
  };
  if (parts.btn) {
    parts.btn.addEventListener("click", () => {
      const on = parts.btn.getAttribute("aria-pressed") !== "true";
      parts.btn.setAttribute("aria-pressed", on ? "true" : "false");
      parts.values.hidden = !on;
    });
  }
  return parts;
}

/* ── Stylesheet ──────────────────────────────────────────────────────────
 * Token aliases: the console names (--bg --s1 --tx ...) first, SpaceCDF's
 * semantic names (--surface-0 --text ...) as the fallback. No literal
 * colour anywhere (sim/tests/test_common/test_ui_viz.py checks).
 */
export const VIZ_CSS = `
.c2o-viz{
  --vz-bg:var(--bg,var(--surface-0)); --vz-s1:var(--s1,var(--surface-1)); --vz-s2:var(--s2,var(--surface-2));
  --vz-s3:var(--s3,var(--surface-3)); --vz-line:var(--line); --vz-line2:var(--line-2,var(--line-strong));
  --vz-val:var(--val,var(--text-value)); --vz-tx:var(--tx,var(--text)); --vz-tx2:var(--tx2,var(--text-2));
  --vz-tx3:var(--tx3,var(--text-3)); --vz-off:var(--tx-off,var(--text-disabled));
  --vz-accent:var(--accent,var(--interactive)); --vz-accent-wash:var(--accent-wash,var(--interactive-wash));
  --vz-ok:var(--ok,var(--status-ok)); --vz-warn:var(--warn,var(--status-caution));
  --vz-warn-wash:var(--warn-wash,var(--status-caution-wash)); --vz-alarm:var(--alarm,var(--status-alarm));
  --vz-alarm-wash:var(--alarm-wash,var(--status-alarm-wash)); --vz-stale:var(--stale,var(--status-stale));
  --vz-fill:var(--fill,var(--graphic-fill)); --vz-sans:var(--sans,var(--font-sans)); --vz-mono:var(--mono,var(--font-mono));
  font-family:var(--vz-sans); font-size:var(--fs-body); color:var(--vz-tx); min-width:0;
}
.c2o-viz .vz-head{display:flex;align-items:center;gap:var(--sp-2) var(--sp-3);flex-wrap:wrap;min-height:28px;margin-bottom:var(--sp-2)}
.c2o-viz .vz-title{font-size:var(--fs-body);font-weight:600;color:var(--vz-val)}
.c2o-viz .vz-chips{display:flex;gap:var(--sp-2);flex-wrap:wrap;align-items:center;flex:1;min-width:0}
.c2o-viz .vz-chip{display:inline-flex;align-items:center;gap:4px;border:1px solid var(--vz-line2);border-radius:var(--radius-sm);
  padding:0 6px;font-size:var(--fs-label);line-height:20px;color:var(--vz-tx2);white-space:nowrap}
.c2o-viz .vz-chip b{font-family:var(--vz-mono);font-weight:500;color:var(--vz-val)}
.c2o-viz .vz-chip.is-ecl{border-color:var(--vz-tx3);color:var(--vz-tx)}
.c2o-viz .vz-toggle{margin-left:auto;font:inherit;font-size:var(--fs-label);color:var(--vz-tx2);background:transparent;
  border:1px solid var(--vz-line2);border-radius:var(--radius);min-height:24px;padding:0 var(--sp-2);cursor:pointer}
.c2o-viz .vz-toggle:hover{color:var(--vz-tx);background:var(--vz-s2)}
.c2o-viz .vz-toggle[aria-pressed="true"]{color:var(--vz-val);border-color:var(--vz-accent);box-shadow:inset 0 -2px 0 var(--vz-accent)}
.c2o-viz button:focus-visible,.c2o-viz [tabindex]:focus-visible{outline:2px solid var(--vz-accent);outline-offset:1px}
.c2o-viz .vz-pic{position:relative;min-width:0}
.c2o-viz .vz-stage{overflow-x:auto;overflow-y:hidden}
.c2o-viz svg{display:block;font-family:var(--vz-sans)}
.c2o-viz .vz-v{font-family:var(--vz-mono);font-variant-numeric:tabular-nums;font-weight:500;color:var(--vz-val);white-space:nowrap}
.c2o-viz .vz-v.is-stale{color:var(--vz-tx3);font-style:italic;font-weight:400}
.c2o-viz .vz-v.is-nodata{font-family:var(--vz-sans);font-weight:400;color:var(--vz-tx2);font-size:var(--fs-label)}
.c2o-viz .vz-age{font-style:normal;font-size:var(--fs-label)}
.c2o-viz .vz-gnd{margin-left:6px;font-size:var(--fs-label);color:var(--vz-tx3);border:1px dashed var(--vz-line2);border-radius:var(--radius-sm);padding:0 4px}
.c2o-viz .vz-note{font-size:var(--fs-label);color:var(--vz-tx3);line-height:var(--lh-text)}
.c2o-viz .vz-values{margin-top:var(--sp-3);overflow-x:auto}
.c2o-viz table.vz-table{width:100%;border-collapse:collapse;font-size:var(--fs-body)}
.c2o-viz .vz-table caption{text-align:left;font-size:var(--fs-label);color:var(--vz-tx3);padding-bottom:4px}
.c2o-viz .vz-table th,.c2o-viz .vz-table td{padding:4px var(--sp-2);border-bottom:1px solid var(--vz-line);text-align:left;vertical-align:baseline}
.c2o-viz .vz-table thead th{font-size:var(--fs-label);font-weight:500;color:var(--vz-tx3);border-bottom-color:var(--vz-line2)}
.c2o-viz .vz-table tbody th{font-weight:400;color:var(--vz-tx2)}
.c2o-viz .vz-table .n{text-align:right}
.c2o-viz .vz-table .src{font-family:var(--vz-mono);font-size:var(--fs-label);color:var(--vz-tx3)}

/* SVG vocabulary (grey at rest; colour only for status or selection) */
.c2o-viz .t-lab{font-size:12px;fill:var(--vz-tx3)}
.c2o-viz .t-name{font-size:13px;font-weight:600;fill:var(--vz-tx)}
.c2o-viz .t-val{font-family:var(--vz-mono);font-variant-numeric:tabular-nums;font-size:13px;font-weight:500;fill:var(--vz-val)}
.c2o-viz .t-big{font-family:var(--vz-mono);font-variant-numeric:tabular-nums;font-size:15px;font-weight:500;fill:var(--vz-val)}
.c2o-viz .t-val.is-stale,.c2o-viz .t-big.is-stale{fill:var(--vz-tx3);font-style:italic;font-weight:400}
.c2o-viz .t-val.is-nodata,.c2o-viz .t-big.is-nodata{font-family:var(--vz-sans);font-size:12px;font-weight:400;fill:var(--vz-tx2)}
.c2o-viz .t-off{font-size:12px;fill:var(--vz-off)}
.c2o-viz .g-box{fill:var(--vz-s1);stroke:var(--vz-line2);stroke-width:1}
.c2o-viz .g-box2{fill:var(--vz-s2);stroke:var(--vz-line2);stroke-width:1}
.c2o-viz .g-rule{stroke:var(--vz-line);stroke-width:1;fill:none}
.c2o-viz .g-rule2{stroke:var(--vz-line2);stroke-width:1;fill:none}
.c2o-viz .g-track{fill:var(--vz-s3)}
.c2o-viz .g-fill{fill:var(--vz-fill)}
.c2o-viz .g-ptr{fill:var(--vz-val)}
.c2o-viz .g-ink{stroke:var(--vz-tx2);fill:none;stroke-width:1.25}
.c2o-viz .g-band-w{fill:var(--vz-warn-wash)}
.c2o-viz .g-band-a{fill:var(--vz-alarm-wash)}
.c2o-viz .g-lim-w{stroke:var(--vz-warn);stroke-width:1.5}
.c2o-viz .g-lim-a{stroke:var(--vz-alarm);stroke-width:1.5}
.c2o-viz .g-accent{stroke:var(--vz-accent);fill:none;stroke-width:1.5}
.c2o-viz .is-caution .g-ptr,.c2o-viz .g-ptr.is-caution{fill:var(--vz-warn)}
.c2o-viz .is-alarm .g-ptr,.c2o-viz .g-ptr.is-alarm{fill:var(--vz-alarm)}
.c2o-viz .g-ptr.is-stale{fill:var(--vz-stale)}
.c2o-viz .g-hatch{fill:var(--vz-tx3);opacity:.35}
`;

export function ensureStyle(id = "c2o-viz-style", css = VIZ_CSS) {
  const d = globalThis.document;
  if (!d || !d.head || d.getElementById(id)) return;
  const st = d.createElement("style");
  st.id = id;
  st.textContent = css;
  d.head.appendChild(st);
}

/** Small inline glyphs (shape carries the state, never colour alone). */
export function stateGlyph(state, x, y, size = 11) {
  const h = size, w = size;
  if (state === "alarm") return `<path d="M${x} ${y - h / 2} L${x + w / 2} ${y + h / 2} L${x - w / 2} ${y + h / 2} Z" class="gl-alarm"/>`;
  if (state === "caution") return `<path d="M${x} ${y - h / 2} L${x + w / 2} ${y + h / 2} L${x - w / 2} ${y + h / 2} Z" class="gl-caution"/>`;
  if (state === "stale" || state === "nodata") return `<circle cx="${x}" cy="${y}" r="${h / 2 - 0.5}" class="gl-stale"/>`;
  return "";
}
