/* ============================================================================
 * C2O DESIGN SYSTEM — where.js  (served at /static/shared/where.js)
 * ============================================================================
 * "Where to find this" links on workbook questions (worksheet screen audit,
 * 2026-11-04). A question in the logbook's Workbook tab carries `where`: the
 * places that answer it (configs/eosat1/worksheets/worksheet_where.yaml,
 * localised by smo_common/logbook/worksheets.py). This module turns them into
 * links:
 *
 *   tool: mcs        #page=<id>&param=0xHHHH&focus=<id>&tab=<id>&bd=<id> on the
 *                    MCS (mcs.js applyNavHash). Inside the MCS the hash
 *                    changes in place; from another tool it opens or focuses
 *                    the MCS window (target "c2o-mcs").
 *   tool: planner | orbit | radio | delayed_tm   <tool>/<path>#<focus>
 *   tool: docs       /doc/<path>?lang=<lang>#<anchor> on the documentation viewer
 *   tool: ext        an https URL outside C2O: a new window, rel="noopener
 *                    noreferrer". Nothing but https is ever turned into a link
 *                    (the server already filters; this checks again).
 *
 * Tool addresses follow tools/portal.py: in the cloud every tool is
 * https://<key>.<domain>/ (ops, plan, tm, orbit, radio, docs); on a laptop it
 * is the same host on the tool's start.sh port.
 * ============================================================================ */

import { t, tText, getLang } from "/static/shared/i18n.js";
import { esc } from "/static/shared/components.js";

/** logbook tool id -> [portal key (cloud host label), local port] */
export const TOOL_ADDR = {
  mcs: ["ops", 9090], planner: ["plan", 9091], delayed_tm: ["tm", 8092],
  orbit: ["orbit", 8093], radio: ["radio", 8094], docs: ["docs", 8095],
};
const KEYS = new Set(Object.values(TOOL_ADDR).map(([k]) => k).concat(["sim", "design", "scenarios", "adcs", "www"]));
const ID = /^[A-Za-z][\w-]{0,63}$/;
const PARAM = /^0x[0-9A-Fa-f]{4}$/;
const SAFE_URL = /^https:\/\/[^\s"'<>\\]+$/i;

/** Base URL of a C2O tool as seen from this page, or "" when unknown. */
export function toolBase(tool, loc = window.location) {
  const a = TOOL_ADDR[tool];
  if (!a) return "";
  const host = String(loc.hostname || "");
  const labels = host.split(".");
  const isIp = /^[\d.]+$/.test(host) || host.includes(":");
  if (!isIp && labels.length >= 3 && KEYS.has(labels[0])) {
    return `${loc.protocol}//${a[0]}.${labels.slice(1).join(".")}`;
  }
  const h = host.includes(":") ? `[${host}]` : host;
  return `${loc.protocol}//${h || "localhost"}:${a[1]}`;
}

/** The MCS deep-link hash for a place, or "" when nothing valid is left. */
export function mcsHash(w) {
  const q = new URLSearchParams();
  if (w.page && ID.test(w.page)) q.set("page", w.page);
  if (w.tab && ID.test(w.tab)) q.set("tab", w.tab);
  if (w.param && PARAM.test(w.param)) q.set("param", w.param);
  if (w.focus && ID.test(w.focus)) q.set("focus", w.focus);
  if (w.bd && ID.test(w.bd)) q.set("bd", w.bd);
  const s = q.toString();
  return s ? `#${s}` : "";
}

/** {href, target, rel, same} for one place, or null when it cannot link. */
export function whereLink(w, hostTool, loc = window.location) {
  if (!w || !w.tool) return null;
  if (w.tool === "ext") {
    return SAFE_URL.test(String(w.url || "")) ? { href: w.url, target: "_blank", rel: "noopener noreferrer", ext: true } : null;
  }
  if (w.tool === "mcs") {
    const h = mcsHash(w);
    if (!h) return null;
    if (hostTool === "mcs") return { href: h, same: true };
    const base = toolBase("mcs", loc);
    return base ? { href: `${base}/${h}`, target: "c2o-mcs" } : null;
  }
  if (w.tool === "docs") {
    const path = String(w.path || "");
    if (!path || path.split("/").some((p) => p === ".." || p === "") || !/^[\w./-]+\.md$/.test(path)) return null;
    const anchor = w.anchor && /^[\w-]{1,120}$/.test(w.anchor) ? `#${w.anchor}` : "";
    const lang = getLang() === "fr" ? "?lang=fr" : "";
    const rel = `/doc/${path}${lang}${anchor}`;
    if (hostTool === "docs") return { href: rel, same: true };
    const base = toolBase("docs", loc);
    return base ? { href: base + rel, target: "c2o-docs" } : null;
  }
  const path = w.path && /^[\w-]{1,40}$/.test(w.path) ? `/${w.path}` : "/";
  const anchor = w.focus && ID.test(w.focus) ? `#${w.focus}` : "";
  if (hostTool === w.tool) return { href: `${path === "/" ? "" : path}${anchor}` || "#", same: true };
  const base = toolBase(w.tool, loc);
  return base ? { href: base + path + anchor, target: `c2o-${w.tool}` } : null;
}

/** The "Where to find this" line for a question (empty string if none). */
export function whereHtml(items, hostTool) {
  const links = (items || []).map((w) => {
    const l = whereLink(w, hostTool);
    if (!l) return "";
    const attrs = [`href="${esc(l.href)}"`, `class="wb-where-a${l.ext ? " ext" : ""}"`];
    if (l.target) attrs.push(`target="${esc(l.target)}"`);
    if (l.rel) attrs.push(`rel="${esc(l.rel)}"`);
    if (l.same) attrs.push(`data-where-same="1"`);
    const title = l.ext ? tText("Open reference, opens in a new window") : l.same ? tText("Go to this place on this screen")
      : tText("Opens the tool in its own window");
    return `<a ${attrs.join(" ")} title="${esc(title)}">${esc(w.label)}${l.ext
      ? `<span class="ds-sr"> ${t("(opens in a new window)")}</span><span aria-hidden="true"> ↗</span>` : ""}</a>`;
  }).filter(Boolean);
  if (!links.length) return "";
  return `<div class="wb-where"><span class="lbl">${t("Where to find this:")}</span> ${links.join('<span class="sep" aria-hidden="true"> · </span>')}</div>`;
}

/** Same-screen links: move there without reloading (a repeated click on the
 *  same MCS place still re-applies it). Call once per root element. */
export function bindWhere(root) {
  if (!root || root.__whereBound) return;
  root.__whereBound = true;
  root.addEventListener("click", (e) => {
    const a = e.target.closest ? e.target.closest("a[data-where-same]") : null;
    if (!a || !root.contains(a)) return;
    const href = a.getAttribute("href") || "";
    if (!href.startsWith("#")) return;          // a path on this tool: a normal navigation
    e.preventDefault();
    if (window.location.hash === href) window.dispatchEvent(new HashChangeEvent("hashchange"));
    else window.location.hash = href;
    const el = href.length > 1 && /^#[A-Za-z][\w-]*$/.test(href) ? document.getElementById(href.slice(1)) : null;
    if (el) el.scrollIntoView({ block: "center", behavior: "smooth" });
  });
}
