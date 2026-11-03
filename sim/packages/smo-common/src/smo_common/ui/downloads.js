/* ============================================================================
 * SMO DESIGN SYSTEM — downloads.js  (served at /static/shared/downloads.js)
 * ============================================================================
 * The course-PDF list (textbooks, workbooks, references, guides), one
 * renderer for every page that offers them:
 *
 *   docs viewer   /downloads           GET /api/downloads (student list)
 *   MCS           MAN page card        GET /api/downloads (student list)
 *   instructor    left column panel    GET /api/downloads (every entry)
 *
 * The server decides the audience (smo_common/downloads.py); this module only
 * draws what it is given. One row per document; its language versions sit in
 * the row (EN / FR, size, Open in a tab, Download). A language filter hides
 * the versions — and the documents — not in that language.
 *
 *   mountDownloads(host, { api = "/api/downloads", compact = false })
 *
 * Titles come from the manifest in both languages; the chrome strings go
 * through i18n.js t() (smo-common catalog). Re-renders on smo:langchange and
 * once the page's catalog has loaded (smo:i18nready / I18n.ready).
 * ========================================================================== */

import { t, tText, getLang, onLangChange } from "/static/shared/i18n.js";

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ESC[c]);

const CSS = `
.dl-bar{ display:flex; align-items:center; gap:var(--sp-3); flex-wrap:wrap; margin:0 0 var(--sp-3); }
.dl-bar .dl-n{ font-size:var(--fs-label); color:var(--tx3); }
.dl-cat{ font-size:var(--fs-label); font-weight:600; color:var(--tx3); margin:var(--sp-4) 0 0;
  padding-bottom:var(--sp-1); border-bottom:1px solid var(--line-2); }
.dl-cat:first-of-type{ margin-top:0; }
.dl-list{ list-style:none; margin:0; padding:0; }
.dl-row{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:var(--sp-1) var(--sp-4);
  align-items:center; padding:var(--sp-2) 0; border-bottom:1px solid var(--line); }
.dl-t{ font-size:var(--fs-body); color:var(--tx); line-height:1.35; min-width:0; }
.dl-t .ds-chip{ margin-left:var(--sp-2); vertical-align:1px; font-size:var(--fs-label); }
.dl-v{ display:flex; flex-direction:column; gap:2px; align-items:stretch; }
.dl-f{ display:grid; grid-template-columns:2.4em 5.5em max-content max-content; justify-content:end;
  align-items:center; gap:var(--sp-2); }
.dl-f .lg{ font-family:var(--mono); font-size:var(--fs-label); color:var(--tx2); }
.dl-f .sz{ font-family:var(--mono); font-variant-numeric:tabular-nums; font-size:var(--fs-label);
  color:var(--tx3); text-align:right; }
.dl-f a{ font-size:var(--fs-label); color:var(--accent); text-decoration:none; white-space:nowrap; }
.dl-f a:hover{ text-decoration:underline; }
.dl-f a:focus-visible{ outline:2px solid var(--accent); outline-offset:2px; }
.dl-empty{ font-size:var(--fs-body); color:var(--tx2); padding:var(--sp-2) 0; }
.dl.compact .dl-row{ grid-template-columns:minmax(0,1fr); }
.dl.compact .dl-f{ justify-content:start; }
@media (max-width:640px){ .dl-row{ grid-template-columns:minmax(0,1fr); } .dl-f{ justify-content:start; } }
`;

function injectCss() {
  if (typeof document === "undefined" || document.getElementById("c2o-dl-css")) return;
  const s = document.createElement("style");
  s.id = "c2o-dl-css";
  s.textContent = CSS;
  document.head.appendChild(s);
}

const ORDER = ["textbook", "workbook", "reference", "guide"];
function catLabel(c) {
  if (c === "textbook") return t("Textbooks");
  if (c === "workbook") return t("Workbooks and worksheets");
  if (c === "reference") return t("References");
  if (c === "guide") return t("Guides");
  return esc(c);
}

/** fmtSize(bytes) — "12.4 MB" / "63 kB" (French: Mo / ko, decimal point kept). */
export function fmtSize(b) {
  const n = Number(b) || 0;
  if (n >= 1e6) return t("{{n}} MB", { n: (n / 1e6).toFixed(1) });
  return t("{{n}} kB", { n: String(Math.max(1, Math.round(n / 1e3))) });
}

/** Group the flat listing into documents: a pair (EN + FR) is one row. */
export function groupDocs(docs) {
  const byId = new Map(docs.map((d) => [d.id, d]));
  const seen = new Set();
  const out = [];
  for (const d of docs) {
    if (seen.has(d.id)) continue;
    const versions = [d];
    seen.add(d.id);
    const p = d.pair && byId.get(d.pair);
    if (p && !seen.has(p.id)) { versions.push(p); seen.add(p.id); }
    versions.sort((a, b) => (a.lang === "en" ? -1 : 1) - (b.lang === "en" ? -1 : 1));
    out.push({ ...d, versions });
  }
  return out;
}

function fileLine(v) {
  const href = esc(v.url);
  const lg = String(v.lang || "").toUpperCase();
  const name = esc(v.filename || "");
  return `<div class="dl-f" lang="${esc(v.lang)}">
    <span class="lg" title="${esc(v.lang === "fr" ? "Français" : "English")}">${esc(lg)}</span>
    <span class="sz">${fmtSize(v.size)}</span>
    <a href="${href}?inline=1" target="_blank" rel="noopener" hreflang="${esc(v.lang)}"
       aria-label="${esc(tText("Open {{name}} in a new tab", { name: v.filename || "" }))}">${t("Open")}</a>
    <a href="${href}" download="${name}" hreflang="${esc(v.lang)}"
       aria-label="${esc(tText("Download {{name}}", { name: v.filename || "" }))}">${t("Download")}</a>
  </div>`;
}

/** renderDownloads(docs, filter) — pure: HTML for the list body. */
export function renderDownloads(docs, filter = "all", lang = getLang()) {
  const groups = groupDocs(docs || []);
  const rows = { textbook: [], workbook: [], reference: [], guide: [] };
  let shown = 0;
  for (const g of groups) {
    const vs = g.versions.filter((v) => filter === "all" || v.lang === filter);
    if (!vs.length) continue;
    shown++;
    const title = (g.title && (g.title[lang] || g.title.en)) || g.id;
    const chips = (g.licence ? `<span class="ds-chip">${esc(g.licence)}</span>` : "") +
      (g.audience === "instructor"
        ? `<span class="ds-chip">${t("Instructor only")}</span>` : "");
    (rows[g.category] || (rows[g.category] = [])).push(
      `<li class="dl-row" data-dl="${esc(g.id)}"><div class="dl-t">${esc(title)}${chips}</div>` +
      `<div class="dl-v">${vs.map(fileLine).join("")}</div></li>`);
  }
  const cats = [...ORDER, ...Object.keys(rows).filter((c) => !ORDER.includes(c))];
  const body = cats.filter((c) => rows[c] && rows[c].length).map((c) =>
    `<h3 class="dl-cat">${catLabel(c)}</h3><ul class="dl-list">${rows[c].join("")}</ul>`).join("");
  return { html: body || `<p class="dl-empty">${t("No document in this language.")}</p>`, shown };
}

/** mountDownloads(host, opts) — fetch the listing and keep the list drawn. */
export function mountDownloads(host, opts = {}) {
  if (!host) return null;
  injectCss();
  const api = opts.api || "/api/downloads";
  const st = { docs: null, error: false, filter: "all" };
  host.classList.add("dl");
  if (opts.compact) host.classList.add("compact");

  function draw() {
    if (st.error) { host.innerHTML = `<p class="dl-empty">${t("Course PDFs are unavailable on this server.")}</p>`; return; }
    if (!st.docs) { host.innerHTML = `<p class="dl-empty">${t("Loading course PDFs…")}</p>`; return; }
    if (!st.docs.length) { host.innerHTML = `<p class="dl-empty">${t("No course PDFs on this server.")}</p>`; return; }
    const langs = [...new Set(st.docs.map((d) => d.lang))];
    const { html, shown } = renderDownloads(st.docs, st.filter);
    const seg = langs.length > 1
      ? `<div class="ds-seg" role="group" aria-label="${esc(tText("Language of the PDF"))}">
          <button type="button" data-dl-lang="all" aria-pressed="${st.filter === "all"}">${t("All languages")}</button>
          <button type="button" data-dl-lang="en" aria-pressed="${st.filter === "en"}" lang="en">English</button>
          <button type="button" data-dl-lang="fr" aria-pressed="${st.filter === "fr"}" lang="fr">Français</button>
        </div>` : "";
    host.innerHTML = `<div class="dl-bar">${seg}<span class="dl-n">${t("{{count}} document", { count: shown, plural: "{{count}} documents" })}</span></div>${html}`;
  }

  host.addEventListener("click", (e) => {
    const b = e.target.closest && e.target.closest("[data-dl-lang]");
    if (!b) return;
    st.filter = b.dataset.dlLang;
    draw();
    const again = host.querySelector(`[data-dl-lang="${st.filter}"]`);
    if (again) again.focus();
  });

  async function load() {
    try {
      const r = await fetch(api, { cache: "no-cache" });
      if (!r.ok) throw new Error(String(r.status));
      const j = await r.json();
      st.docs = Array.isArray(j.documents) ? j.documents : [];
      st.error = false;
    } catch (e) { st.error = true; }
    draw();
  }

  draw();
  load();
  onLangChange(draw);
  try { window.addEventListener("smo:i18nready", draw); } catch (e) { /* no window */ }
  const S = globalThis.__smoI18n;
  if (S && S.ready && S.ready.then) S.ready.then(draw, () => {});
  return { reload: load, redraw: draw };
}
