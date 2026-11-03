// Unit tests for the instructor console's focus-pane state machine (focus.js)
// and the timeline helpers (timeline.js) — INSTRUCTOR_CONSOLE_DESIGN.md §5, §4.
//   node test_instructor_focus.mjs <static/modern dir>
// Prints "ok N" and exits 0, or prints every failure and exits 1.
// Run by sim/tests/test_simulator/test_instructor_console.py.
import { pathToFileURL } from "node:url";
import path from "node:path";

const dir = process.argv[2];
const F = await import(pathToFileURL(path.join(dir, "focus.js")).href);
const TL = await import(pathToFileURL(path.join(dir, "timeline.js")).href);
const fails = [];
let n = 0;
const eq = (a, b, msg) => { n++; if (JSON.stringify(a) !== JSON.stringify(b)) fails.push(`${msg}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`); };
const ok = (c, msg) => { n++; if (!c) fails.push(msg); };

const ev = (view, prio, reason = "r") => ({ view, prio, reason, subject: "s", ts: 0 });
const T0 = 1_000_000;

/* 1. auto-follow is the default; a focus-worthy event switches and says why */
{
  const f = F.createFocus("situation");
  eq(f.state().auto, true, "auto-follow on by default");
  const r = f.offer(ev("power", 3, "inject fired"), T0);
  eq(r.action, "switch", "first event switches");
  eq(f.state().view, "power", "view is power");
  eq(f.state().reason.reason, "inject fired", "the switch carries its cause");
  eq(f.state().canBack, true, "back is available after a switch");
}

/* 2. rate limit: inside the dwell events queue; best = highest prio, then newest */
{
  const f = F.createFocus("situation");
  f.offer(ev("power", 2), T0);
  eq(f.offer(ev("thermal", 1), T0 + 1000).action, "queued", "inside dwell -> queued");
  eq(f.offer(ev("orbit", 2), T0 + 2000).action, "queued", "equal prio queued");
  eq(f.state().view, "power", "pane did not churn");
  eq(f.state().queued.view, "orbit", "higher prio wins the queue");
  eq(f.tick(T0 + 5000).action, "waiting", "still dwelling");
  const r = f.tick(T0 + F.DEFAULTS.minDwellMs + 1);
  eq(r.action, "switch", "queued event applied after the dwell");
  eq(f.state().view, "orbit", "switched to the queued view");
}

/* 3. pre-emption: strictly higher priority after PREEMPT_AFTER */
{
  const f = F.createFocus("situation");
  f.offer(ev("orbit", 1), T0);
  eq(f.offer(ev("power", 3), T0 + 1000).action, "queued", "too early to pre-empt");
  eq(f.offer(ev("thermal", 3), T0 + F.DEFAULTS.preemptAfterMs + 10).action, "switch", "higher prio pre-empts after 5 s");
  eq(f.state().view, "thermal", "pre-empted view");
  eq(f.offer(ev("obc", 3), T0 + F.DEFAULTS.preemptAfterMs + 20).action, "queued", "equal prio does not pre-empt");
}

/* 4. stale queued events are dropped */
{
  const f = F.createFocus("situation");
  f.offer(ev("power", 2), T0);
  f.offer(ev("orbit", 1), T0 + 100);
  f.pin(true); f.pin(false);              // pin clears the queue
  eq(f.state().queued, null, "pin clears the queue");
  f.offer(ev("orbit", 1), T0 + 200);
  eq(f.tick(T0 + 200 + F.DEFAULTS.maxAgeMs + 1).action, "dropped", "too old -> dropped");
}

/* 5. pinned: events become a suggestion, accepted with one click */
{
  const f = F.createFocus("situation");
  f.pin(true);
  eq(f.offer(ev("power", 3, "inject fired"), T0).action, "suggest", "pinned -> suggest");
  eq(f.state().view, "situation", "pinned pane does not move");
  f.offer(ev("orbit", 1), T0 + 10);
  eq(f.state().suggestion.view, "power", "suggestion keeps the higher priority");
  eq(f.accept(T0 + 20).action, "accept", "accept the suggestion");
  eq(f.state().view, "power", "accepted view");
  eq(f.state().suggestion, null, "suggestion consumed");
}

/* 6. auto-follow off behaves like pinned */
{
  const f = F.createFocus("situation");
  f.setAuto(false);
  eq(f.offer(ev("power", 3), T0).action, "suggest", "auto off -> suggest");
  f.dismiss();
  eq(f.state().suggestion, null, "dismiss clears");
}

/* 7. manual choice starts a grace period; Back restores the previous view */
{
  const f = F.createFocus("situation");
  f.select("thermal", T0);
  eq(f.offer(ev("power", 3), T0 + 1000).action, "suggest", "inside user grace -> suggest");
  eq(f.offer(ev("power", 3), T0 + F.DEFAULTS.userGraceMs + 1).action, "switch", "after grace -> switch");
  eq(f.back(T0 + F.DEFAULTS.userGraceMs + 2).action, "back", "back");
  eq(f.state().view, "thermal", "back restores the previous view");
  eq(f.back(T0 + F.DEFAULTS.userGraceMs + 3).view, "situation", "back again");
  eq(f.back(T0 + F.DEFAULTS.userGraceMs + 4).action, "none", "empty stack");
}

/* 8. same view: no switch, cause refreshed */
{
  const f = F.createFocus("power");
  eq(f.offer(ev("power", 2, "eclipse entry"), T0).action, "same", "same view");
  eq(f.state().reason.reason, "eclipse entry", "cause refreshed");
  eq(f.state().switches, 0, "no switch counted");
}

/* 9. back stack is bounded */
{
  const f = F.createFocus("v0", { maxBack: 3 });
  for (let i = 1; i <= 6; i++) f.select("v" + i, T0 + i);
  let k = 0; while (f.back(T0 + 100).action === "back") k++;
  eq(k, 3, "back stack keeps MAX_BACK");
}

/* 10. timeline helpers */
{
  const items = [
    { ts: 100, kind: "aos" }, { ts: 200, kind: "los" }, { ts: 300, kind: "aos" },
    { ts: 150, kind: "ecl_in" }, { ts: 250, kind: "ecl_out" }, { ts: 350, kind: "ecl_in" },
  ];
  const sp = TL.spans(items, 400);
  eq(sp.contact, [[100, 200], [300, 400]], "contact spans (open span runs to now)");
  eq(sp.eclipse, [[150, 250], [350, 400]], "eclipse spans");
  eq(TL.spans([{ ts: 50, kind: "los" }], 60).contact, [[null, 50]], "LOS without AOS starts at the window edge");
  eq(TL.windowRange(1000, 100, 0.2), [920, 1020], "window: 80 % past, 20 % future");
  eq(TL.windowRange(1000, 100, 0.9), [960, 1060], "future fraction capped at 60 %");
  eq(TL.markOf({ lane: "fault", kind: "inject", sev: 3 }).cls, "m-inject", "injects use the inject colour");
  eq(TL.markOf({ lane: "alarm", kind: "event", sev: 3 }).cls, "m-alarm", "alarms use the alarm colour");
  eq(TL.markOf({ lane: "alarm", kind: "event", sev: 1 }).cls, "m-info", "info events stay grey");
  eq(TL.markOf({ lane: "tc", kind: "tc_rej", sev: 2 }).shape, "x", "rejected TC is a cross");
  ok(TL.LANES.length === 9 && TL.LANES[8].id === "voice" && TL.LANES[7].id === "crew",
     "nine lanes: consoles (ground staffing) then voice last");
  // ground-side items (anonymous MCS activity, WP10)
  eq(TL.markOf({ lane: "alarm", kind: "g_ack" }).cls, "m-ground", "a ground acknowledgement is a team mark");
  eq(TL.markOf({ lane: "proc", kind: "g_step", result: "FAILED" }).shape, "x", "a failed ground step is a cross");
  eq(TL.markOf({ lane: "crew", kind: "seat", state: "vacant" }).cls, "m-alarm", "a vacated desk is red");
  const ts = TL.talkSpans([{ lane: "voice", kind: "talk", ts: 10, ts_end: 14, position: "ttc", loop: "fd" }],
    [{ position: "aocs", loop: "fd", since: 20 }], 30);
  eq(ts.map((x) => [x[0], x[1]]), [[10, 14], [20, 30]], "talk spans: closed and still open");
}

if (fails.length) { console.log(fails.join("\n")); process.exit(1); }
console.log(`ok ${n}`);
