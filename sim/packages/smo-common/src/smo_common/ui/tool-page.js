/* ============================================================================
 * SMO DESIGN SYSTEM — tool-page.js  (served at /static/shared/tool-page.js)
 * ============================================================================
 * Language bootstrap for the stand-alone tool pages in sim/tools (delayed-TM
 * viewer, orbit tools, doc viewer, scenario generator, ADCS viewer). Each
 * tool server mounts smo_common/ui at /static/shared/ and loads this module.
 *
 *   - Language follows the suite rule: ?lang= > localStorage "c2o.lang"
 *     (old "smo.lang" still read) > <html data-default-lang> > "en".
 *   - Catalog: /static/shared/i18n/tools/<lang>.json (one catalog for all
 *     five tools, English-text keys like every other SMO catalog), on top of
 *     the shared design-system catalog.
 *   - Static markup is translated with data-i18n* attributes (i18n.js
 *     applyDom). Inline (non-module) page scripts translate dynamic text via
 *     window.SMO_I18N.tText, and re-render on the "smo:i18nready" event,
 *     which fires once the catalog has loaded.
 *   - <body data-server-lang> marks a page whose CONTENT is chosen by the
 *     server from ?lang= (the doc viewer): when the stored language differs
 *     and the URL has no ?lang=, the page reloads once with ?lang= added.
 * ============================================================================ */
import I18n, { init, getLang } from "/static/shared/i18n.js";

// db:false: no tool page shows spacecraft-database prose, so the 266 KB YAML
// overlay (fr.db.json) is not fetched.
const ready = init({ app: "/static/shared/i18n/tools/", db: false });

const body = document.body;
if (body && body.hasAttribute("data-server-lang")) {
  const u = new URL(location.href);
  const served = body.getAttribute("data-server-lang") || "en";
  if (!u.searchParams.has("lang") && getLang() !== served) {
    u.searchParams.set("lang", getLang());
    location.replace(u);
  }
}

ready.then((lang) => {
  try { window.dispatchEvent(new CustomEvent("smo:i18nready", { detail: { lang } })); } catch (e) { /* no window */ }
});

export default I18n;
