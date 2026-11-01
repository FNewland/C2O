/* ============================================================================
 * SMO DESIGN SYSTEM — i18n.js  (served at /static/shared/i18n.js)
 * ============================================================================
 * Browser-side EN/FR runtime for the MODERN consoles. No build step, no
 * dependency. Catalogs are i18next-v4-compatible JSON whose KEYS ARE THE
 * EXACT ENGLISH TEXT, so English needs no catalog and renders byte-identically
 * to the untranslated source (t() in English = the key, interpolated).
 *
 *   t(en, vars?)      HTML-context text: catalog text verbatim, {{var}} values
 *                     HTML-escaped ({{- var}} inserts a value raw).
 *   tText(en, vars?)  same lookup, nothing escaped: textContent, alert(),
 *                     confirm(), canvas fillText, setAttribute values.
 *   tHtml(en, vars?)  same as tText; use when a var is TRUSTED markup.
 *   tdb(key, enText)  YAML-overlay lookup ('tm:eps.bat_voltage:description');
 *                     returns enText in English or when absent. Raw text.
 *   vars.count  -> plural key `<en>_one|_many|_other` (Intl.PluralRules);
 *                  English other-form comes from vars.plural.
 *   vars.context -> key `<en>_<context>` (one English word, two French ones).
 *
 * Language: ?lang= > localStorage "c2o.lang" (the suite-wide setting; the
 * old "smo.lang" key is still read, and both are written) > <html data-default-lang>
 * (injected by the server from SMO_LANG / mission.yaml ui_lang) > "en".
 * Per browser, never per server: two operators may differ.
 *
 * Catalogs: /static/shared/i18n/<lang>.json (design system), the app catalog
 * /static/modern/i18n/<lang>.json (override with init({app})), and the YAML
 * overlay /static/shared/i18n/<lang>.db.json. Missing keys fall back to
 * English and are collected in I18n.missing (console.debug once each).
 *
 * State lives on globalThis.__smoI18n so a second copy of this module (e.g.
 * imported with a ?v= query) shares it. See docs/i18n/UI_I18N_GUIDE.md.
 * ============================================================================ */

export const LANGS = ["en", "fr"];
const LS_KEY = "c2o.lang";        // one language setting for every C2O app
const LS_OLD = ["smo.lang"];      // read for one release (R3 audit §i18n)
const SHARED = "/static/shared/i18n/";
const APP_DEFAULT = "/static/modern/i18n/";
const TIMEOUT_MS = 2500;   // a hung catalog fetch must never block a console
const G = globalThis;
const S = G.__smoI18n || (G.__smoI18n = {
  lang: null, opts: { app: APP_DEFAULT, storage: true }, cache: {},
  cat: {}, db: {}, loaded: false, ready: null, missing: new Set(),
  textOrig: new WeakMap(), attrOrig: new WeakMap(), plural: {},
});

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const escHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ESC[c]);

/** normLang("fr-CA") -> "fr"; unsupported/empty -> null. */
export function normLang(l) {
  const p = String(l ?? "").trim().toLowerCase().split(/[-_]/)[0];
  return LANGS.includes(p) ? p : null;
}

/** resolveLang({storage}) — the documented precedence, no side effects. */
export function resolveLang(opts = S.opts) {
  let q = null, ls = null, def = null;
  try { q = new URLSearchParams((G.location && G.location.search) || "").get("lang"); } catch (e) { /* no URL */ }
  if (opts.storage !== false) {
    try {
      if (G.localStorage) {
        for (const k of [LS_KEY, ...LS_OLD]) { ls = normLang(G.localStorage.getItem(k)); if (ls) break; }
      }
    } catch (e) { /* private mode */ }
  }
  try {
    const h = G.document && G.document.documentElement;
    def = h && h.getAttribute ? h.getAttribute("data-default-lang") : null;
  } catch (e) { /* no DOM */ }
  return normLang(q) || normLang(ls) || normLang(def) || "en";
}

export function getLang() { return S.lang || (S.lang = resolveLang(S.opts)); }

function fetchJson(url) {
  if (typeof G.fetch !== "function") return Promise.resolve({});
  const get = G.fetch(url, { cache: "no-cache" })
    .then((r) => (r && r.ok ? r.json() : {}))
    .then((j) => (j && typeof j === "object" && !Array.isArray(j) ? j : {}))
    .catch(() => ({}));
  const late = new Promise((res) => setTimeout(() => res({}), TIMEOUT_MS));
  return Promise.race([get, late]);
}

function load(lang) {
  if (lang === "en") return Promise.resolve({ cat: {}, db: {} });   // identity
  const withDb = S.opts.db !== false;
  const key = lang + "|" + S.opts.app + "|" + withDb;
  if (!S.cache[key]) {
    S.cache[key] = Promise.all([
      fetchJson(`${SHARED}${lang}.json`),
      S.opts.app ? fetchJson(`${S.opts.app}${lang}.json`) : {},
      withDb ? fetchJson(`${SHARED}${lang}.db.json`) : {},   // db:false = no YAML overlay
    ]).then(([shared, app, db]) => ({ cat: { ...shared, ...app }, db }));
  }
  return S.cache[key];
}

function adopt(lang, c) {
  if (S.lang !== lang) return;          // a newer setLang() won the race
  S.cat = c.cat; S.db = c.db; S.loaded = true;
}

function setHtmlLang(l) {
  try { if (G.document && G.document.documentElement) G.document.documentElement.lang = l; } catch (e) { /* stub */ }
}

/** init({app, storage, db}) — (re)start loading. app: app catalog base URL
 *  (default "/static/modern/i18n/"); db:false skips the 266 KB YAML overlay
 *  (pages with no spacecraft-database text); storage:false ignores localStorage
 *  (wall display: ?lang= / server default only). Returns I18n.ready. */
export function init(opts = {}) {
  S.opts = { ...S.opts, ...opts };
  const lang = S.lang = resolveLang(S.opts);
  if (lang !== "en") setHtmlLang(lang);
  S.ready = load(lang).then((c) => {
    adopt(lang, c);
    if (lang !== "en") applyDom();
    return S.lang;
  });
  return S.ready;
}

function pluralCat(lang, n) {
  try {
    const pr = S.plural[lang] || (S.plural[lang] = new Intl.PluralRules(lang));
    return pr.select(n);
  } catch (e) { return n === 1 ? "one" : "other"; }
}

function lookup(k) {
  const v = Object.prototype.hasOwnProperty.call(S.cat, k) ? S.cat[k] : undefined;
  return typeof v === "string" && v !== "" ? v : undefined;   // null / "" = untranslated
}

function noteMissing(key) {
  if (!S.loaded || S.missing.has(key)) return;
  S.missing.add(key);
  try { console.debug(`[i18n] missing ${S.lang}: ${JSON.stringify(key)}`); } catch (e) { /* no console */ }
}

function interp(s, v, escape) {
  return s.replace(/\{\{(-?)\s*([\w.]+)\s*\}\}/g, (m, raw, name) => {
    if (!Object.prototype.hasOwnProperty.call(v, name) || v[name] === null || v[name] === undefined) return m;
    return escape && !raw ? escHtml(v[name]) : String(v[name]);
  });
}

function translate(en, vars, escape) {
  const key = String(en ?? "");
  const v = vars || {};
  const lang = getLang();
  const hasCount = typeof v.count === "number" && Number.isFinite(v.count);
  let s;
  if (lang !== "en") {
    const bases = v.context ? [`${key}_${v.context}`, key] : [key];
    for (const b of bases) {
      if (hasCount) s = lookup(`${b}_${pluralCat(lang, v.count)}`) ?? lookup(`${b}_other`);
      if (s === undefined) s = lookup(b);
      if (s !== undefined) break;
    }
    if (s === undefined) noteMissing(bases[0]);
  }
  if (s === undefined) {
    s = key;
    if (hasCount && v.plural !== undefined && pluralCat("en", v.count) !== "one") s = String(v.plural);
  }
  return interp(s, v, escape);
}

export const t = (en, vars) => translate(en, vars, true);
export const tText = (en, vars) => translate(en, vars, false);
export const tHtml = tText;

/** tdb(key, enText) — YAML-overlay text by stable id ("kind:id:field"). */
export function tdb(key, enText) {
  if (getLang() === "en") return enText;
  const e = S.db[key];
  const v = typeof e === "string" ? e : (e && typeof e === "object" ? (e[getLang()] ?? e.text) : undefined);
  if (typeof v === "string" && v !== "") return v;
  noteMissing("db:" + key);
  return enText;
}

/* ── DOM: data-i18n / data-i18n-{title,placeholder,aria-label,html} ────── */
const ATTRS = ["title", "placeholder", "aria-label"];
const SEL = "[data-i18n],[data-i18n-html]," + ATTRS.map((a) => `[data-i18n-${a}]`).join(",");
const collapse = (s) => String(s).replace(/\s+/g, " ").trim();

// Translation of `key` for the DOM; `orig` (the remembered English) when
// English is active or the catalog has no entry, so a missing key never
// replaces what the page said with a bare key.
function trDom(key, orig, ctx) {
  if (getLang() === "en") return orig;
  const k = collapse(key);
  const tr = tText(k, ctx ? { context: ctx } : undefined);
  return tr === k ? orig : tr;
}

/** applyDom(root=document) — translate marked static markup in place. The
 *  English original is remembered, so switching back to EN restores it
 *  exactly. Mark LEAF text only; JS-rewritten text must use t() instead. */
export function applyDom(root) {
  const r = root || G.document;
  if (!r || typeof r.querySelectorAll !== "function") return;
  const els = Array.from(r.querySelectorAll(SEL));
  if (r.matches && r.matches(SEL)) els.unshift(r);
  for (const el of els) {
    const ctx = el.getAttribute("data-i18n-context") || "";
    const orig = S.attrOrig.get(el) || {};
    if (el.hasAttribute("data-i18n-html")) {
      if (orig.html === undefined) orig.html = el.innerHTML;
      const k = el.getAttribute("data-i18n-html") || collapse(orig.html);
      el.innerHTML = trDom(k, orig.html, ctx);
    } else if (el.hasAttribute("data-i18n")) {
      const explicit = el.getAttribute("data-i18n");
      if (explicit) {
        if (orig.text === undefined) orig.text = el.textContent;
        el.textContent = trDom(explicit, orig.text, ctx);
      } else {
        for (const n of Array.from(el.childNodes || [])) {
          if (n.nodeType !== 3 || !n.nodeValue.trim()) continue;
          if (!S.textOrig.has(n)) S.textOrig.set(n, n.nodeValue);
          const en = S.textOrig.get(n);
          const lead = en.match(/^\s*/)[0], trail = en.match(/\s*$/)[0];
          const tr = trDom(en, en, ctx);
          n.nodeValue = tr === en ? en : lead + tr + trail;
        }
      }
    }
    for (const a of ATTRS) {
      if (!el.hasAttribute(`data-i18n-${a}`)) continue;
      if (orig[a] === undefined) orig[a] = el.getAttribute(a) || "";
      const k = el.getAttribute(`data-i18n-${a}`) || orig[a];
      el.setAttribute(a, trDom(k, orig[a], ctx));
    }
    S.attrOrig.set(el, orig);
  }
}

/** setLang(l) — persist, update <html lang>, re-apply DOM, then dispatch
 *  `smo:langchange` (detail {lang}) on window for dynamic re-renders. */
export async function setLang(l) {
  const n = normLang(l);
  if (!n) return getLang();
  if (S.opts.storage !== false) {
    try {
      if (G.localStorage) for (const k of [LS_KEY, ...LS_OLD]) G.localStorage.setItem(k, n);
    } catch (e) { /* private mode */ }
  }
  try {   // keep an explicit ?lang= in step, so a reload shows the same thing
    const u = new URL(G.location.href);
    if (u.searchParams.has("lang")) { u.searchParams.set("lang", n); G.history.replaceState(G.history.state, "", u); }
  } catch (e) { /* no URL/history */ }
  if (n !== S.lang) S.loaded = false;   // renders during the catalog fetch must not log "missing"
  S.lang = n;
  setHtmlLang(n);
  adopt(n, await load(n));
  if (S.lang !== n) return S.lang;
  applyDom();
  try { G.dispatchEvent(new CustomEvent("smo:langchange", { detail: { lang: n } })); } catch (e) { /* no window */ }
  return n;
}

/** onLangChange(fn) — fn(lang) after every setLang(); returns unsubscribe. */
export function onLangChange(fn) {
  const h = (e) => fn((e && e.detail && e.detail.lang) || getLang());
  try { G.addEventListener("smo:langchange", h); } catch (e) { /* no window */ }
  return () => { try { G.removeEventListener("smo:langchange", h); } catch (e) { /* noop */ } };
}

export const I18n = {
  LANGS, t, tText, tHtml, tdb, init, setLang, getLang, resolveLang, normLang,
  applyDom, onLangChange, missing: S.missing,
  get lang() { return getLang(); },
  get ready() { return S.ready || init(); },
};
G.SMO_I18N = I18n;   // for classic (non-module) inline scripts, e.g. rfsim sim.html
export default I18n;
