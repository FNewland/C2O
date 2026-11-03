/* ============================================================================
 * C2O INSTRUCTOR — focus-pane state machine (pure, no DOM)
 * ============================================================================
 * The overview strip and the timeline never move; ONE focus pane follows the
 * simulation (INSTRUCTOR_CONSOLE_DESIGN.md §5). The rules, from the research
 * report ("Switch the focus pane, never the overview"):
 *
 *   1. Auto-follow is the default; the instructor can turn it off.
 *   2. The pane switches only on events the server marks as focus-worthy
 *      (inject fired, phase / spacecraft-mode change, scenario end, FDIR
 *      recovery, an alarm not acted on, a new truth-vs-telemetry divergence,
 *      AOS / LOS, eclipse entry), each with a priority 1..3.
 *   3. Every switch carries its cause ("Power — because EPS-07 fired at …").
 *   4. Rate limit: after a switch the pane dwells MIN_DWELL; events in the
 *      meantime are queued (best = highest priority, then newest) and applied
 *      when the dwell ends, unless they are older than MAX_AGE by then. A
 *      strictly higher-priority event may pre-empt after PREEMPT_AFTER.
 *   5. Pinned (or auto-follow off): events only become a SUGGESTION the
 *      instructor can accept with one click.
 *   6. A manual view change or Back gives the instructor a grace period
 *      (USER_GRACE) during which events are suggestions too.
 *   7. Back restores the previous view (stack of MAX_BACK).
 *
 * Unit-tested in node: sim/tests/test_simulator/js/focus_test.mjs.
 * ========================================================================== */

export const DEFAULTS = Object.freeze({
  minDwellMs: 15000,
  preemptAfterMs: 5000,
  userGraceMs: 45000,
  maxAgeMs: 90000,
  maxBack: 10,
});

/** Which of two offered events wins: higher priority, then newer. */
export function better(a, b) {
  if (!a) return b;
  if (!b) return a;
  if ((b.prio || 0) !== (a.prio || 0)) return (b.prio || 0) > (a.prio || 0) ? b : a;
  return (b.atMs || 0) >= (a.atMs || 0) ? b : a;
}

export function createFocus(initialView = "situation", opts = {}) {
  const o = { ...DEFAULTS, ...opts };
  const s = {
    view: initialView,
    reason: null,           // {text-free} the event that brought us here, or null (manual / initial)
    prio: 0,
    since: 0,
    lastAutoMs: -Infinity,
    pinned: false,
    auto: true,
    graceUntil: -Infinity,
    queued: null,
    suggestion: null,
    back: [],
    switches: 0,
  };

  function pushBack() {
    s.back.push({ view: s.view, reason: s.reason, prio: s.prio });
    if (s.back.length > o.maxBack) s.back.shift();
  }

  function switchTo(ev, nowMs) {
    if (ev.view !== s.view) pushBack();
    s.view = ev.view;
    s.reason = ev;
    s.prio = ev.prio || 0;
    s.since = nowMs;
    s.lastAutoMs = nowMs;
    s.queued = null;
    if (s.suggestion && s.suggestion.view === ev.view) s.suggestion = null;
    s.switches += 1;
    return { action: "switch", view: ev.view, event: ev };
  }

  function suggest(ev) {
    s.suggestion = better(s.suggestion, ev);
    return { action: "suggest", view: ev.view, event: s.suggestion };
  }

  return {
    options: o,

    /** Offer a focus-worthy event {view, prio, reason, subject, ts, seq}. */
    offer(ev, nowMs) {
      if (!ev || !ev.view) return { action: "ignored", why: "no view" };
      ev = { ...ev, atMs: nowMs };
      if (ev.view === s.view) {
        // Already showing it: keep the newest cause visible, no switch.
        if ((ev.prio || 0) >= s.prio) { s.reason = ev; s.prio = ev.prio || 0; }
        return { action: "same", view: ev.view };
      }
      if (s.pinned || !s.auto || nowMs < s.graceUntil) return suggest(ev);
      const sinceLast = nowMs - s.lastAutoMs;
      if (sinceLast < o.minDwellMs) {
        if ((ev.prio || 0) > s.prio && sinceLast >= o.preemptAfterMs) return switchTo(ev, nowMs);
        s.queued = better(s.queued, ev);
        return { action: "queued", view: s.queued.view, event: s.queued };
      }
      return switchTo(ev, nowMs);
    },

    /** Call regularly (e.g. 1 Hz): applies a queued event once the dwell ends. */
    tick(nowMs) {
      if (!s.queued) return { action: "idle" };
      if (nowMs - s.queued.atMs > o.maxAgeMs) { s.queued = null; return { action: "dropped" }; }
      if (s.pinned || !s.auto || nowMs < s.graceUntil) {
        const q = s.queued; s.queued = null; return suggest(q);
      }
      if (nowMs - s.lastAutoMs >= o.minDwellMs) return switchTo(s.queued, nowMs);
      return { action: "waiting" };
    },

    /** The instructor picked a view: switch now, start the grace period. */
    select(view, nowMs) {
      if (view !== s.view) pushBack();
      s.view = view;
      s.reason = null;
      s.prio = 0;
      s.since = nowMs;
      s.graceUntil = nowMs + o.userGraceMs;
      if (s.suggestion && s.suggestion.view === view) s.suggestion = null;
      return { action: "manual", view };
    },

    /** One-click back to the previous view. */
    back(nowMs) {
      const prev = s.back.pop();
      if (!prev) return { action: "none" };
      s.view = prev.view;
      s.reason = prev.reason;
      s.prio = prev.prio || 0;
      s.since = nowMs;
      s.graceUntil = nowMs + o.userGraceMs;
      return { action: "back", view: prev.view };
    },

    /** Accept the pending suggestion (a manual action). */
    accept(nowMs) {
      const sg = s.suggestion;
      if (!sg) return { action: "none" };
      s.suggestion = null;
      if (sg.view !== s.view) pushBack();
      s.view = sg.view;
      s.reason = sg;
      s.prio = sg.prio || 0;
      s.since = nowMs;
      s.graceUntil = nowMs + o.userGraceMs;
      return { action: "accept", view: sg.view };
    },

    dismiss() { s.suggestion = null; },
    pin(on = true) { s.pinned = !!on; if (s.pinned) s.queued = null; },
    setAuto(on) { s.auto = !!on; if (!s.auto) s.queued = null; },

    state() {
      return {
        view: s.view, reason: s.reason, prio: s.prio, since: s.since,
        pinned: s.pinned, auto: s.auto, graceUntil: s.graceUntil,
        queued: s.queued, suggestion: s.suggestion,
        canBack: s.back.length > 0, backView: s.back.length ? s.back[s.back.length - 1].view : null,
        switches: s.switches,
      };
    },
  };
}
