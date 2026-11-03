/* ============================================================================
 * C2O DESIGN SYSTEM — dock.js  (served at /static/shared/dock.js)
 * ============================================================================
 * One right-hand dock for the side panels a page opens (MCS: the alarm
 * journal, the logbook, the voice loops). Without it each panel was its own
 * fixed overlay on the right edge and two open panels lay on top of each
 * other.
 *
 * The page opts in with an empty container beside its work area:
 *
 *   <div class="shell"> <nav …> <main class="work">…</main>
 *     <div id="c2o-dock"></div> </div>
 *
 * Wide screens: open panels stand side by side in the dock, in a fixed order
 * (alarms, logbook, voice from the work area outwards), and the work area
 * narrows (panels shrink towards their minimum first); nothing covers anything. The work area keeps at least MAIN_MIN
 * px: when one more panel would not fit, the panel opened longest ago
 * closes (voice only hides: its loops stay connected). Below 1000 px a panel
 * is a full-height overlay and only one is open at a time.
 * A page without #c2o-dock keeps its panel as an overlay (other tools have
 * one panel only).
 *
 *   import { dockPanel } from "/static/shared/dock.js";
 *   const d = dockPanel(el, { width: 440, min: 360, order: 2,
 *                             close: ({ evicted }) => myClose(evicted) });
 *   d.opened();  d.closed();      // call from the panel's own open / close
 * ============================================================================ */

const MAIN_MIN = 480;                       // px the work area always keeps
const NARROW = "(max-width: 999px)";        // the pages' phone/tablet breakpoint
const panels = new Map();                   // element -> record
let seq = 0;
let wired = false;

export function dockHost() { return document.getElementById("c2o-dock"); }
export const isNarrow = () => window.matchMedia(NARROW).matches;

/** Room for docked panels: the shell minus its other columns (the rail)
 *  minus the work area's floor. */
function room() {
  const h = dockHost();
  if (!h || !h.parentElement) return Infinity;
  let other = 0;
  for (const c of h.parentElement.children) {
    if (c === h || c.matches("main, .work")) continue;
    other += c.getBoundingClientRect().width;
  }
  return h.parentElement.clientWidth - other - MAIN_MIN;
}

function openOnes() {
  return [...panels.entries()].filter(([, r]) => r.open).sort((a, b) => a[1].t - b[1].t);
}

/** Close the oldest open panels until the newest fits (or, narrow: until it
 *  is the only one). `keep` is never closed. */
function fit(keep) {
  const open = openOnes();
  if (open.length < 2) return;
  if (isNarrow() || !dockHost()) {
    for (const [el, r] of open) if (el !== keep && r !== open[open.length - 1][1]) evict(el, r);
    return;
  }
  const avail = room();
  let need = open.reduce((s, [, r]) => s + r.min, 0);
  for (const [el, r] of open) {
    if (need <= avail) break;
    if (el === keep || r === open[open.length - 1][1]) continue;
    evict(el, r);
    need -= r.min;
  }
}

function evict(el, r) {
  r.open = false;
  el.classList.remove("is-dock-open");
  try { r.close({ evicted: true }); } catch (e) { /* a panel's close never breaks the dock */ }
}

function wire() {
  if (wired) return;
  wired = true;
  let t = null;
  window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => fit(null), 120); });
}

/**
 * dockPanel(el, {width, min, order, close}) -> {opened(), closed(), docked}
 * Moves `el` into #c2o-dock when the page has one. `close({evicted})` is
 * the panel's own close, called when the dock needs the room.
 */
export function dockPanel(el, o = {}) {
  const r = { width: o.width || 420, min: o.min || 340, order: o.order || 0,
    close: o.close || (() => {}), open: false, t: 0 };
  panels.set(el, r);
  const h = dockHost();
  if (h) {
    el.classList.add("c2o-docked");
    el.style.setProperty("--dock-w", `${r.width}px`);
    el.style.setProperty("--dock-min", `${r.min}px`);
    el.style.order = String(r.order);
    if (el.parentElement !== h) h.appendChild(el);
  }
  wire();
  return {
    docked: !!h,
    opened() {
      r.open = true;
      r.t = ++seq;
      el.classList.add("is-dock-open");
      fit(el);
    },
    closed() {
      r.open = false;
      el.classList.remove("is-dock-open");
    },
  };
}

export default { dockPanel, dockHost, isNarrow };
