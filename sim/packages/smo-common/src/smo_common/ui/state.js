/* ============================================================================
 * SMO DESIGN SYSTEM — state.js  (served at /static/shared/state.js)
 * ============================================================================
 * ONE place that turns a console state snapshot into the three answers every
 * panel shows: are we in contact, what mode is the spacecraft in, and how old
 * is this value. Before this module each panel derived them from a different
 * field (state.in_contact, the pass override, a stale frame-lock parameter),
 * so the header could say "LINK · IN CONTACT" while the overview said
 * "NO CONTACT" (UI audit R3 problem #10). Every panel that shows link, mode
 * or freshness calls these selectors; none re-derives them.
 *
 * Pure functions: no DOM, no fetch, no clock, no i18n. Labels returned here
 * are identifiers (EN, upper case) that callers translate for display.
 *
 *   linkState(state, opts?)  -> { contact, gs, source, locks, tm, ageS }
 *   modeState(state)         -> { mode, code, source, fdirLevel, contingency }
 *   freshness(ageS, opts?)   -> "fresh" | "degraded" | "stale" | "nodata"
 *   linkLimited(state, opts?) -> { limited, speed }
 *
 * `state` is the MCS /api/state (or WS state_update) snapshot. The planner
 * and instructor serve a subset of the same fields; missing fields degrade
 * to "unknown", never to a confident wrong answer.
 * ============================================================================ */

/** Spacecraft mode enum of obdh.mode (0x0300). */
export const SC_MODES = ["NOMINAL", "SAFE", "EMERGENCY", "SCIENCE"];

/** FDIR alert levels of fdir.level (0x0700). NOT a mode enum. */
export const FDIR_LEVELS = ["NOMINAL", "CAUTION", "WARNING", "CRITICAL"];

/* Default freshness policy (seconds of SIM time). Matches
 * configs/<mission>/mcs/staleness.yaml and the classic console. */
export const FRESHNESS_POLICY = {
  stale_factor: 1.5, fresh_factor: 0.9,
  floor_fresh_s: 10.0, floor_stale_s: 20.0,
  aperiodic_fresh_s: 300.0, aperiodic_stale_s: 900.0,
};

const finite = (v) => v !== null && v !== undefined && v !== "" && Number.isFinite(Number(v));

/**
 * freshness(ageS, {intervalS, policy}) — the four-state age verdict.
 *
 *  - "nodata"   never received (age null/undefined/NaN)
 *  - "fresh"    age <= max(floor_fresh_s, interval * fresh_factor)
 *  - "degraded" age <= max(floor_stale_s, interval * stale_factor)
 *  - "stale"    older than that: show the LAST value, dimmed, with its age
 *
 * `intervalS` is the HK cadence of the parameter (null => aperiodic, the
 * 300 s / 900 s pair). Ages are SIM seconds, as served; never re-age them
 * against the browser clock.
 */
export function freshness(ageS, opts = {}) {
  if (!finite(ageS)) return "nodata";
  const pol = Object.assign({}, FRESHNESS_POLICY, opts.policy || {});
  const iv = Number(opts.intervalS);
  let fresh, stale;
  if (finite(opts.intervalS) && iv > 0) {
    fresh = Math.max(pol.floor_fresh_s, iv * pol.fresh_factor);
    stale = Math.max(pol.floor_stale_s, iv * pol.stale_factor, fresh);
  } else {
    fresh = pol.aperiodic_fresh_s;
    stale = pol.aperiodic_stale_s;
  }
  const a = Number(ageS);
  if (a <= fresh) return "fresh";
  if (a <= stale) return "degraded";
  return "stale";
}

/**
 * linkState(state, {lockFresh}) — contact and telemetry-link verdict.
 *
 * contact is TRUE when the ground segment says a station is in contact
 * (state.sa.in_contact / state.in_contact), or when the frame-lock parameter
 * (ttc 0x0512) reads locked AND that reading is itself current. A last-known
 * "locked" from a previous pass is not contact; `lockFresh(hex)` lets the
 * caller apply its cadence-aware verdict (default: params_age <= 20 s).
 *
 * source: "ground" (station geometry/link state) | "TM frame lock" | "none".
 * tm: freshness of the newest frame (sa.last_frame_age_s), "nodata" if none.
 */
export function linkState(state, opts = {}) {
  const st = state || {};
  const sa = st.sa || {};
  const p = st.params || {};
  const ages = st.params_age || {};
  const lockFresh = opts.lockFresh || ((hex) => {
    const a = ages[String(parseInt(hex, 16))];
    return finite(a) && Number(a) <= FRESHNESS_POLICY.floor_stale_s;
  });
  const lockOf = (hex) => finite(p[hex]) && Number(p[hex]) >= 1 && lockFresh(hex);
  const locks = { carrier: lockOf("0x0510"), bit: lockOf("0x0511"), frame: lockOf("0x0512") };
  const ground = sa.in_contact !== undefined && sa.in_contact !== null
    ? !!sa.in_contact : !!st.in_contact;
  const contact = ground || locks.frame;
  const gs = (contact && (sa.ground_station_name || st.active_gs_name ||
    sa.gs_in_contact || (st.ttc || {}).active_gs_name || (st.ttc || {}).ground_station)) || "";
  const ageS = finite(sa.last_frame_age_s) ? Number(sa.last_frame_age_s) : null;
  return {
    contact,
    gs: String(gs || ""),
    source: ground ? "ground" : locks.frame ? "TM frame lock" : "none",
    locks,
    tm: freshness(ageS, { policy: opts.policy }),
    ageS,
  };
}

/**
 * modeState(state) — spacecraft mode with provenance (M5–M8).
 *
 * obdh.mode (0x0300) is PRIMARY; the decoded obdh block is the fallback;
 * the simulator's own sc_mode is used ONLY when opts.trainingTruth is set
 * (instructor/training time source) and is labelled "SIM (training)".
 * fdir.level (0x0700) is a SECONDARY escalation: it never becomes the mode.
 * contingency is true for SAFE/EMERGENCY, or for FDIR level >= 2.
 */
export function modeState(state, opts = {}) {
  const st = state || {};
  const p = st.params || {};
  let code = null, source = null;
  if (finite(p["0x0300"])) { code = Number(p["0x0300"]); source = "TM obdh.mode 0x0300"; }
  else if (finite((st.obdh || {}).mode)) { code = Number(st.obdh.mode); source = "TM obdh.mode"; }
  let mode = code !== null ? (SC_MODES[code] ?? `MODE_${code}`) : null;
  if (mode === null && opts.trainingTruth && st.sc_mode) {
    mode = String(st.sc_mode).toUpperCase();
    source = "SIM (training)";
  }
  const fdirLevel = finite(p["0x0700"]) ? Number(p["0x0700"]) : null;
  const contingency = mode === "SAFE" || mode === "EMERGENCY" ||
    (fdirLevel !== null && fdirLevel >= 2);
  return { mode, code, source, fdirLevel, contingency };
}

/**
 * linkLimited(state, {thresholdS}) — the training-speed caveat.
 *
 * At sim speed > 1 the downlink still runs at its real bit rate, so ages in
 * SIM seconds grow `speed` times faster than the telemetry can arrive. When
 * the newest frame is older than the threshold while the sim runs fast, the
 * console is link-limited: values are held, not lost. Panels show one banner
 * instead of turning every value stale without explanation.
 */
export function linkLimited(state, opts = {}) {
  const st = state || {};
  const sa = st.sa || {};
  const speed = finite(sa.speed) ? Number(sa.speed) : finite(st.speed) ? Number(st.speed) : 1;
  const thr = finite(opts.thresholdS) ? Number(opts.thresholdS) : FRESHNESS_POLICY.floor_stale_s;
  const age = finite(sa.last_frame_age_s) ? Number(sa.last_frame_age_s) : null;
  const contact = linkState(st, opts).contact;
  return { limited: speed > 1 && contact && age !== null && age > thr, speed };
}
