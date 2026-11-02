/* ============================================================================
 * C2O pictorial displays — vizkit.js  (source: shared/ui-viz/vizkit.js)
 * ============================================================================
 * The small kit the geometry views (attitude3d, groundtrack, skyplot) share:
 * token-scoped CSS, the i18n hook, engineering number formatting, SVG
 * element helpers, the four data states and the "values" table that is each
 * picture's text alternative. Framework-free, no imports, no fetch: the SMO
 * consoles (vanilla JS) and SpaceCDF (React) load it unchanged.
 *
 * TOKENS. The consoles name tokens --s1/--tx2/--warn…, SpaceCDF names the
 * same values --surface-1/--text-secondary/--status-caution…
 * (shared/ui-tokens). Every view styles itself from the --vz-* aliases
 * below, which resolve to whichever set the host page defines. No hex.
 *
 * I18N. Every view takes opts.t(en, vars) -> string (the console's tText,
 * SpaceCDF's own). Keys are the exact English text, so English needs no
 * catalog; without opts.t the English is interpolated as is.
 * ============================================================================ */

const VARS = {
  bg: "var(--bg, var(--surface-0))",
  s1: "var(--s1, var(--surface-1))",
  s2: "var(--s2, var(--surface-2))",
  s3: "var(--s3, var(--surface-3))",
  line: "var(--line)",
  line2: "var(--line-2, var(--line-strong))",
  val: "var(--val, var(--text-value))",
  tx: "var(--tx, var(--text-primary))",
  tx2: "var(--tx2, var(--text-secondary))",
  tx3: "var(--tx3, var(--text-3))",
  off: "var(--tx-off, var(--text-disabled))",
  accent: "var(--accent, var(--interactive))",
  ok: "var(--ok, var(--status-ok))",
  warn: "var(--warn, var(--status-caution))",
  alarm: "var(--alarm, var(--status-alarm))",
  stale: "var(--stale, var(--status-stale))",
  fill: "var(--fill, var(--graphic-fill))",
  overlay: "var(--overlay)",
  mono: "var(--mono, var(--font-mono))",
  sans: "var(--sans, var(--font-sans))",
};

/** CSS custom properties every view root (.vz) defines. */
const BASE_CSS = `
.vz{ ${Object.entries(VARS).map(([k, v]) => `--vz-${k}:${v};`).join(" ")}
  font-family:var(--vz-sans); font-size:var(--fs-body, 13px); color:var(--vz-tx); min-width:0; }
.vz *{ box-sizing:border-box; }
.vz .vz-sr{ position:absolute !important; width:1px; height:1px; overflow:hidden;
  clip:rect(0 0 0 0); clip-path:inset(50%); white-space:nowrap; }
.vz .vz-bar{ display:flex; align-items:center; gap:var(--sp-3, 12px); flex-wrap:wrap;
  min-height:32px; padding:0 0 var(--sp-2, 8px); }
.vz .vz-bar .vz-sp{ flex:1 1 auto; }
.vz .vz-cap{ font-size:var(--fs-label, 12px); color:var(--vz-tx3); }
.vz .vz-seg{ display:inline-flex; border:1px solid var(--vz-line2); border-radius:var(--radius, 3px); overflow:hidden; }
.vz .vz-seg button,.vz .vz-btn{ font:500 var(--fs-label, 12px)/1 var(--vz-sans); min-height:26px; padding:0 10px;
  background:transparent; color:var(--vz-tx2); border:0; cursor:pointer; }
.vz .vz-btn{ border:1px solid var(--vz-line2); border-radius:var(--radius, 3px); }
.vz .vz-seg button+button{ border-left:1px solid var(--vz-line2); }
.vz .vz-seg button:hover,.vz .vz-btn:hover{ background:var(--vz-s2); color:var(--vz-tx); }
.vz .vz-seg button[aria-pressed="true"],.vz .vz-btn[aria-expanded="true"]{ background:var(--vz-s3); color:var(--vz-val);
  box-shadow:inset 0 -2px 0 var(--vz-accent); }
.vz .vz-seg button:focus-visible,.vz .vz-btn:focus-visible,.vz [tabindex]:focus-visible{
  outline:2px solid var(--vz-accent); outline-offset:-2px; }
.vz .vz-seg button[aria-disabled="true"]{ color:var(--vz-off); cursor:not-allowed; background:transparent; }
.vz .vz-v{ font-family:var(--vz-mono); font-variant-numeric:tabular-nums; font-weight:500;
  font-size:var(--fs-value, 15px); line-height:1.2; color:var(--vz-val); white-space:nowrap; }
.vz .vz-v .u{ font-weight:400; font-size:var(--fs-label, 12px); color:var(--vz-tx3); margin-left:3px; }
.vz .vz-v svg{ width:11px; height:11px; margin-right:4px; vertical-align:-1px; }
.vz .vz-v.is-stale{ color:var(--vz-tx3); font-style:italic; font-weight:400; }
.vz .vz-v.is-caution{ color:var(--vz-warn); }
.vz .vz-v.is-alarm{ color:var(--vz-alarm); }
.vz .vz-age{ font:400 var(--fs-label, 12px)/16px var(--vz-mono); color:var(--vz-tx3); padding:0 4px;
  border:1px dashed var(--vz-stale); border-radius:var(--radius-sm, 2px); margin-left:6px; white-space:nowrap; }
.vz .vz-nodata{ display:inline-flex; font:400 var(--fs-label, 12px)/18px var(--vz-sans); color:var(--vz-tx2);
  background:var(--vz-s3); border-radius:var(--radius-sm, 2px); padding:0 6px; white-space:nowrap; font-style:normal; }
.vz .vz-flag{ display:inline-flex; align-items:center; gap:4px; font:500 var(--fs-label, 12px)/1 var(--vz-sans);
  white-space:nowrap; }
.vz .vz-flag svg{ width:10px; height:10px; flex:none; }
.vz .vz-flag.is-caution{ color:var(--vz-warn); }
.vz .vz-flag.is-alarm{ color:var(--vz-alarm); }
.vz .vz-flag.is-ok{ color:var(--vz-tx2); }
.vz table.vz-tab{ width:100%; border-collapse:collapse; margin-top:var(--sp-2, 8px); }
.vz .vz-tab caption{ text-align:left; font-size:var(--fs-label, 12px); color:var(--vz-tx3); padding:0 0 4px; }
.vz .vz-tab th{ font-size:var(--fs-label, 12px); font-weight:500; color:var(--vz-tx3); text-align:left;
  padding:5px 8px; border-bottom:1px solid var(--vz-line2); }
.vz .vz-tab td{ padding:4px 8px; border-bottom:1px solid var(--vz-line); vertical-align:baseline; }
.vz .vz-tab td.n{ text-align:right; font-family:var(--vz-mono); font-variant-numeric:tabular-nums; color:var(--vz-val); }
.vz .vz-tab td.s{ font-size:var(--fs-label, 12px); color:var(--vz-tx3); }
.vz svg text{ font-family:var(--vz-sans); }
`;

/** Inject `css` once per document under `id` (idempotent; no-op off-DOM). */
export function injectCss(id, css) {
  const d = globalThis.document;
  if (!d || d.getElementById(id)) return;
  const s = d.createElement("style");
  s.id = id;
  s.textContent = css;
  (d.head || d.documentElement).appendChild(s);
}
export function injectBase() { injectCss("vz-base-css", BASE_CSS); }

/* ── i18n ── */
function interp(s, vars) {
  return vars ? String(s).replace(/\{\{-?\s*(\w+)\s*\}\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : String(s);
}
/** The translator a view uses: opts.t, else English interpolation. */
export function translator(opts = {}) {
  return typeof opts.t === "function" ? (en, vars) => opts.t(en, vars) : (en, vars) => interp(en, vars);
}

/* ── numbers ── */
const fin = (x) => x !== null && x !== undefined && x !== "" && Number.isFinite(Number(x));
export { fin };
/** Engineering number: "." decimals in every language (owner ruling R5). */
export function fmt(x, digits) {
  if (!fin(x)) return "";
  return digits === undefined ? String(Number(x)) : Number(x).toFixed(digits);
}
/** "59 s", "4 min 10 s", "2 h 05 min". */
export function fmtAge(s) {
  if (!fin(s)) return "";
  const a = Math.max(0, Math.round(Number(s)));
  if (a < 60) return `${a} s`;
  if (a < 3600) return `${Math.floor(a / 60)} min ${String(a % 60).padStart(2, "0")} s`;
  return `${Math.floor(a / 3600)} h ${String(Math.floor((a % 3600) / 60)).padStart(2, "0")} min`;
}
/** Countdown "mm:ss" or "h:mm:ss". */
export function fmtClock(s) {
  if (!fin(s)) return "";
  const a = Math.max(0, Math.round(Number(s)));
  const p = (n) => String(n).padStart(2, "0");
  const h = Math.floor(a / 3600), m = Math.floor((a % 3600) / 60);
  return h ? `${h}:${p(m)}:${p(a % 60)}` : `${p(m)}:${p(a % 60)}`;
}
export function fmtUtc(ms, seconds = false) {
  if (!fin(ms)) return "";
  const d = new Date(Number(ms));
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getUTCHours())}:${p(d.getUTCMinutes())}${seconds ? ":" + p(d.getUTCSeconds()) : ""}`;
}

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ESC[c]);

/* ── data states ── */
/** Map a derive.js verdict to the display state. */
export function stateOf(verdict) {
  if (verdict === "nodata" || verdict === "disabled") return "nodata";
  if (verdict === "stale") return "stale";
  return "live";               // fresh | degraded | design | undefined
}
const TRI = (filled) => `<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M5 1L9.3 9H.7Z" ${filled
  ? 'fill="currentColor"' : 'fill="none" stroke="currentColor" stroke-width="1.4"'}/></svg>`;
/**
 * A value in its data state, HTML. v: number|null; o: {units, digits,
 * verdict, ageS, level: "caution"|"alarm", t, text (replaces the number)}.
 */
export function valueHtml(v, o = {}) {
  const t = o.t || ((s, x) => interp(s, x));
  const st = stateOf(o.verdict);
  if ((!fin(v) && o.text === undefined) || st === "nodata") {
    return `<span class="vz-nodata">${esc(o.reason ? t(o.reason) : t("no data"))}</span>`;
  }
  const lvl = st === "live" ? o.level : "";
  const cls = ["vz-v", st === "stale" ? "is-stale" : "", lvl === "alarm" ? "is-alarm" : lvl === "caution" ? "is-caution" : ""]
    .filter(Boolean).join(" ");
  const txt = o.text !== undefined ? esc(o.text) : esc(fmt(v, o.digits));
  return `<span class="${cls}">${lvl ? TRI(lvl === "alarm") + " " : ""}${txt}${o.units ? `<span class="u">${esc(o.units)}</span>` : ""}</span>` +
    (st === "stale" ? `<span class="vz-age" title="${esc(t("last value received {{age}} ago", { age: fmtAge(o.ageS) }))}">` +
      `<span class="vz-sr">${esc(t("stale value, age"))} </span>${esc(fmtAge(o.ageS))}</span>` : "");
}
/** A verdict flag: shape + text, colour only when not nominal. */
export function flagHtml(level, text) {
  const cls = level === "alarm" ? "is-alarm" : level === "caution" ? "is-caution" : "is-ok";
  const glyph = level === "alarm" ? TRI(true) : level === "caution" ? TRI(false)
    : `<svg viewBox="0 0 10 10" aria-hidden="true"><circle cx="5" cy="5" r="3.2" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>`;
  return `<span class="vz-flag ${cls}">${glyph}${esc(text)}</span>`;
}

/**
 * The text alternative: a values table. rows = [{label, html, src}].
 */
export function tableHtml(caption, rows, t) {
  return `<table class="vz-tab"><caption>${esc(caption)}</caption><thead><tr>` +
    `<th scope="col">${esc(t("Quantity"))}</th><th scope="col">${esc(t("Value"))}</th>` +
    `<th scope="col">${esc(t("Source"))}</th></tr></thead><tbody>` +
    rows.map((r) => `<tr><th scope="row" style="font-weight:400;color:inherit;border-bottom:1px solid var(--vz-line)">${esc(r.label)}</th>` +
      `<td class="n">${r.html}</td><td class="s">${esc(r.src || "")}</td></tr>`).join("") +
    `</tbody></table>`;
}

/* ── SVG ── */
export const SVGNS = "http://www.w3.org/2000/svg";
export function svgEl(tag, attrs = {}, text) {
  const n = globalThis.document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) n.setAttribute(k, v);
  if (text !== undefined) n.textContent = text;
  return n;
}
/** Remove every child. */
export function clear(node) { while (node && node.firstChild) node.removeChild(node.firstChild); }

/* ── environment ── */
export function reducedMotion() {
  try { return globalThis.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { return false; }
}
/** Resolved value of a --vz-* (or any) custom property on `el`. */
export function tokenValue(el, name) {
  try { return globalThis.getComputedStyle(el).getPropertyValue(name).trim(); } catch (e) { return ""; }
}
/**
 * Call `cb` when the page theme changes (data-theme / data-greyscale on
 * <html>, or the OS colour scheme). Returns an unsubscribe function.
 */
export function onThemeChange(cb) {
  const d = globalThis.document;
  const offs = [];
  try {
    const mo = new MutationObserver(cb);
    mo.observe(d.documentElement, { attributes: true, attributeFilter: ["data-theme", "data-greyscale", "class"] });
    offs.push(() => mo.disconnect());
  } catch (e) { /* no DOM */ }
  try {
    const mq = globalThis.matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", cb);
    offs.push(() => mq.removeEventListener("change", cb));
  } catch (e) { /* no matchMedia */ }
  return () => offs.forEach((f) => f());
}

/** A two-or-more option segmented control; returns {el, set(value)}. */
export function segmented(label, options, value, onChange) {
  const d = globalThis.document;
  const g = d.createElement("div");
  g.className = "vz-seg";
  g.setAttribute("role", "group");
  g.setAttribute("aria-label", label);
  const btns = options.map((o) => {
    const b = d.createElement("button");
    b.type = "button";
    b.dataset.value = o.value;
    b.textContent = o.label;
    if (o.title) b.title = o.title;
    b.addEventListener("click", () => {
      if (b.getAttribute("aria-disabled") === "true" || b.getAttribute("aria-pressed") === "true") return;
      onChange(o.value);
    });
    g.appendChild(b);
    return b;
  });
  const set = (v, disabled = {}) => btns.forEach((b) => {
    b.setAttribute("aria-pressed", String(b.dataset.value === v));
    const why = disabled[b.dataset.value];
    if (why) { b.setAttribute("aria-disabled", "true"); b.title = why; }
    else { b.removeAttribute("aria-disabled"); b.removeAttribute("title"); }
  });
  set(value);
  return { el: g, set };
}

/** "Values" disclosure button bound to a host element; returns {btn, render(html)}. */
export function valuesToggle(t, host, id) {
  const d = globalThis.document;
  const btn = d.createElement("button");
  btn.type = "button";
  btn.className = "vz-btn";
  btn.textContent = t("Values");
  btn.setAttribute("aria-expanded", "false");
  btn.setAttribute("aria-controls", id);
  host.id = id;
  host.hidden = true;
  btn.addEventListener("click", () => {
    const open = btn.getAttribute("aria-expanded") !== "true";
    btn.setAttribute("aria-expanded", String(open));
    host.hidden = !open;
  });
  return { btn, isOpen: () => btn.getAttribute("aria-expanded") === "true" };
}
