/* ============================================================================
 * C2O pictorial displays — derive.js  (source: shared/ui-viz/derive.js)
 * ============================================================================
 * The interpretation layer. Pure functions from a parameter snapshot to the
 * quantities an operator reasons about, each carried as a QUANTITY:
 *
 *     { v, units, verdict, ageS, src, ground }
 *
 *   v        number, or null when it cannot be computed
 *   units    display unit ("" for ratios and states)
 *   verdict  "fresh" | "degraded" | "stale" | "nodata" | "disabled" | "design"
 *            — the WORST verdict of every input that went into it, so a value
 *            computed from one stale parameter is itself stale
 *   ageS     age of the OLDEST input (sim seconds), null if unknown
 *   src      provenance: "TM 0x0101", "ground: Kepler from alt", ...
 *   ground   true when computed on the ground (never downlinked)
 *
 * No DOM, no clock, no fetch, no i18n, no imports: the MCS (vanilla JS),
 * the planner and SpaceCDF (React) all import this file unchanged, and the
 * Node unit tests (sim/tests/test_common/js/test_derive.mjs) run it as is.
 *
 * ── Conventions (printed on every attitude display) ──────────────────────
 * Every EOSAT-1 quaternion is SCALAR-LAST [x, y, z, w] and is the ECI->body
 * attitude of smo_common/attitude.py: quatToDcm(q) maps an ECI vector into
 * body axes, v_b = C(q) v_eci. Hamilton product, so C(a)·C(b) = C(b ⊗ a).
 *
 *   source  parameters                 meaning
 *   est     aocs.q_est_1..4 0x02A0-A3  MEKF estimate (what the FSW believes)
 *   att     aocs.att_q1..4  0x0200-03  the published attitude: the SAME
 *                                      estimate (models/aocs_basic.py sets
 *                                      s.q from the EKF); all zeros while
 *                                      no attitude source is valid
 *   ref     aocs.q_ref_x..w 0x02AB-AE  commanded reference
 *
 * There is no truth quaternion on an operator screen (truth is instructor
 * only). three.js uses the same (x, y, z, w) storage; for an ECI scene
 * `object.quaternion.set(x, y, z, w)` reproduces C(q)^T = body->ECI.
 * A scalar-FIRST source must go through fromScalarFirst() — the classic trap
 * (unit-tested: reading [w,x,y,z] as [x,y,z,w] turns a 10° error into ~170°).
 *
 * Body frame (ruling Q4): -Z nadir face (imager boresight, radiator), +Z
 * zenith (body cells, star tracker), +X ~ velocity, +Y = +orbit normal
 * (wing + SADA drive axis). Wing cell normal at shaft angle θ: (cosθ, 0, sinθ).
 * ============================================================================ */

/* ── 0. Quantities and verdicts ─────────────────────────────────────────── */

export const VERDICT_ORDER = ["design", "fresh", "degraded", "stale", "disabled", "nodata"];
const RANK = Object.fromEntries(VERDICT_ORDER.map((v, i) => [v, i]));

const fin = (x) => x !== null && x !== undefined && x !== "" && Number.isFinite(Number(x));
const num = (x) => (fin(x) ? Number(x) : null);

/** worst("fresh", "stale") -> "stale" (no-data dominates). */
export function worst(...verdicts) {
  let w = "design";
  for (const v of verdicts.flat()) {
    const r = RANK[v] ?? RANK.nodata;
    if (r > RANK[w]) w = VERDICT_ORDER[r];
  }
  return w;
}

/** Build a quantity. */
export function qty(v, units = "", meta = {}) {
  const ok = fin(v);
  return {
    v: ok ? Number(v) : null,
    units,
    verdict: ok ? (meta.verdict || "fresh") : "nodata",
    ageS: fin(meta.ageS) ? Number(meta.ageS) : null,
    src: meta.src || "",
    ground: !!meta.ground,
  };
}

/** Combine the provenance of several input quantities into one. */
export function from(inputs, v, units = "", extra = {}) {
  const ins = inputs.filter(Boolean);
  const ages = ins.map((q) => q.ageS).filter(fin);
  const anyMissing = ins.some((q) => q.v === null || q.v === undefined);
  return qty(anyMissing ? null : v, units, {
    verdict: worst(ins.map((q) => q.verdict)),
    ageS: ages.length ? Math.max(...ages) : null,
    src: extra.src || ins.map((q) => q.src).filter(Boolean).join(" + "),
    ground: extra.ground !== undefined ? extra.ground : true,
  });
}

/* Default freshness policy (configs/eosat1/mcs/staleness.yaml floors). The
 * MCS passes its own cadence-aware verdict function instead. */
const FLOOR_FRESH_S = 10, FLOOR_STALE_S = 20;
export function defaultVerdict(ageS) {
  if (!fin(ageS)) return "fresh";            // age not served: trust the value
  const a = Number(ageS);
  return a <= FLOOR_FRESH_S ? "fresh" : a <= FLOOR_STALE_S ? "degraded" : "stale";
}

/**
 * A SOURCE is what every derive function reads: src.get(hex) -> quantity
 * (raw engineering value from TM), plus src.state (the /api/state document,
 * for ground-propagated orbit fields) and src.limits ({hex: band}).
 *
 * sourceFromState(state, {verdict(hex, ageS), limits, units}) wraps the MCS
 * /api/state (params keyed "0x0101", params_age keyed by DECIMAL id).
 */
export function sourceFromState(state, opts = {}) {
  const st = state || {};
  const p = st.params || {};
  const ages = st.params_age || {};
  const vfn = opts.verdict || ((hex, ageS) => defaultVerdict(ageS));
  return {
    state: st,
    limits: opts.limits || {},
    get(hex) {
      const raw = p[hex];
      const a = ages[String(parseInt(hex, 16))];
      if (!fin(raw)) return qty(null, "", { src: `TM ${hex}` });
      const verdict = vfn(hex, fin(a) ? Number(a) : null);
      return qty(Number(raw), "", {
        verdict: verdict === "nodata" ? "nodata" : verdict,
        ageS: a, src: `TM ${hex}`, ground: false,
      });
    },
  };
}

/** A design-time source (SpaceCDF): plain {hex: value}, verdict "design". */
export function sourceFromValues(values, opts = {}) {
  return {
    state: opts.state || {},
    limits: opts.limits || {},
    get(hex) {
      const v = (values || {})[hex];
      return qty(fin(v) ? Number(v) : null, "", { verdict: "design", src: `design ${hex}` });
    },
  };
}

/** Ground-propagated field of the state document as a quantity. */
function stateQty(src, key, units, label) {
  const v = (src.state || {})[key];
  return qty(fin(v) ? Number(v) : null, units, { verdict: fin(v) ? "fresh" : "nodata",
    src: label || `ground ${key}`, ground: true });
}

const withUnits = (q, units) => ({ ...q, units });

/* ── 1. Quaternion algebra (scalar-last, matches smo_common/attitude.py) ── */

export const QUAT_CONVENTION = "[x y z w], scalar last · ECI→body (v_b = C(q)·v_eci)";

export function quatNorm(q) {
  const n = Math.hypot(q[0], q[1], q[2], q[3]);
  return n > 0 ? q.map((c) => c / n) : [0, 0, 0, 1];
}
export function quatConj(q) { return [-q[0], -q[1], -q[2], q[3]]; }
/** Hamilton product a ⊗ b, scalar last (smo_common.attitude.quat_mult). */
export function quatMul(a, b) {
  const [ax, ay, az, aw] = a, [bx, by, bz, bw] = b;
  return [
    aw * bx + ax * bw + ay * bz - az * by,
    aw * by - ax * bz + ay * bw + az * bx,
    aw * bz + ax * by - ay * bx + az * bw,
    aw * bw - ax * bx - ay * by - az * bz,
  ];
}
/** DCM mapping ECI -> body (row-major 3×3), smo_common.attitude.quat_to_dcm. */
export function quatToDcm(q) {
  const [x, y, z, w] = q;
  return [
    [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)],
    [2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)],
    [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)],
  ];
}
export function matVec(C, v) {
  return [0, 1, 2].map((i) => C[i][0] * v[0] + C[i][1] * v[1] + C[i][2] * v[2]);
}
/** [w,x,y,z] (scalar first) -> [x,y,z,w]. */
export function fromScalarFirst(q) { return [q[1], q[2], q[3], q[0]]; }
/** [x,y,z,w] -> [w,x,y,z]. */
export function toScalarFirst(q) { return [q[3], q[0], q[1], q[2]]; }

/** Error quaternion taking a to b in a's body axes: conj(a) ⊗ b, w >= 0. */
export function quatError(a, b) {
  let e = quatMul(quatConj(a), b);
  if (e[3] < 0) e = e.map((c) => -c);       // shortest path: no 180° sign flips
  return e;
}
/** Rotation angle of a quaternion, degrees, atan2 form (stable near 0°). */
export function quatAngleDeg(q) {
  return (2 * Math.atan2(Math.hypot(q[0], q[1], q[2]), Math.abs(q[3])) * 180) / Math.PI;
}
/** Angle between two attitudes, degrees. */
export function attitudeAngleDeg(a, b) { return quatAngleDeg(quatError(a, b)); }

/** Gimbal-lock guard: Euler angles are flagged within this of ±90° pitch. */
export const GIMBAL_GUARD_DEG = 5;
/**
 * Roll/pitch/yaw (3-2-1, z-y-x) of rotation q, degrees. `singular` is true
 * within GIMBAL_GUARD_DEG of ±90° pitch, where roll and yaw are not separable
 * and the display must say so instead of showing two wild numbers.
 */
export function eulerZYX(q) {
  const [x, y, z, w] = quatNorm(q);
  const sinp = Math.max(-1, Math.min(1, 2 * (w * y - z * x)));
  const pitch = (Math.asin(sinp) * 180) / Math.PI;
  const roll = (Math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)) * 180) / Math.PI;
  const yaw = (Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)) * 180) / Math.PI;
  return { roll, pitch, yaw, singular: Math.abs(pitch) > 90 - GIMBAL_GUARD_DEG };
}
/** Quaternion of rotation by `deg` about unit `axis` (scalar last). */
export function quatFromAxisAngle(axis, deg) {
  const h = (deg * Math.PI) / 360, s = Math.sin(h);
  const n = Math.hypot(...axis) || 1;
  return [(axis[0] / n) * s, (axis[1] / n) * s, (axis[2] / n) * s, Math.cos(h)];
}

export const QUAT_SOURCES = {
  est: { hex: ["0x02A0", "0x02A1", "0x02A2", "0x02A3"], order: "xyzw",
         label: "aocs.q_est (MEKF estimate)" },
  att: { hex: ["0x0200", "0x0201", "0x0202", "0x0203"], order: "xyzw",
         label: "aocs.att_q (published estimate)" },
  ref: { hex: ["0x02AB", "0x02AC", "0x02AD", "0x02AE"], order: "xyzw",
         label: "aocs.q_ref (commanded)" },
};

/**
 * readQuat(src, "est"|"att"|"ref") -> {q, valid, reason, verdict, ageS, src, label}
 * All-zero (the simulator's "no attitude solution" placeholder) and
 * non-unit quaternions are INVALID, never normalised into a confident lie.
 */
export function readQuat(src, which) {
  const def = QUAT_SOURCES[which];
  const comps = def.hex.map((h) => src.get(h));
  const verdict = worst(comps.map((c) => c.verdict));
  const ages = comps.map((c) => c.ageS).filter(fin);
  const base = { label: def.label, src: `TM ${def.hex[0]}–${def.hex[3].slice(-2)}`,
                 verdict, ageS: ages.length ? Math.max(...ages) : null,
                 convention: QUAT_CONVENTION, raw: comps.map((c) => c.v) };
  if (comps.some((c) => c.v === null)) return { ...base, q: null, valid: false, reason: "no data" };
  let q = comps.map((c) => c.v);
  if (def.order === "wxyz") q = fromScalarFirst(q);
  const n = Math.hypot(...q);
  if (n < 1e-6) return { ...base, q: null, valid: false, reason: "no attitude solution" };
  if (Math.abs(n - 1) > 0.01) return { ...base, q: null, valid: false, reason: "not a unit quaternion" };
  return { ...base, q: quatNorm(q), valid: true, reason: "" };
}

/* ── 2. Vectors and angles ──────────────────────────────────────────────── */

export const BODY = {
  boresight: [0, 0, -1],      // payload imager, -Z (nadir face)
  radiator: [0, 0, -1],       // radiator on -Z
  starTracker: [0, 0, 1],     // zenith star tracker, +Z
  bodyCells: [0, 0, 1],       // +Z body-mounted cells
};
/** Wing cell normal at SADA shaft angle `deg` (drive axis = body Y). */
export function wingNormal(deg) {
  const t = (deg * Math.PI) / 180;
  return [Math.cos(t), 0, Math.sin(t)];
}
export function unit(v) {
  const n = Math.hypot(...v);
  return n > 1e-9 ? v.map((c) => c / n) : null;
}
export function angleDeg(a, b) {
  const ua = unit(a), ub = unit(b);
  if (!ua || !ub) return null;
  const c = ua[0] * ub[0] + ua[1] * ub[1] + ua[2] * ub[2];
  const s = Math.hypot(ua[1] * ub[2] - ua[2] * ub[1], ua[2] * ub[0] - ua[0] * ub[2],
    ua[0] * ub[1] - ua[1] * ub[0]);
  return (Math.atan2(s, c) * 180) / Math.PI;
}
/**
 * Body-frame direction -> position on the "boresight view": azimuthal
 * equidistant about -Z. r = angle from boresight / 180 (0 centre, 1 rim
 * = straight up), az measured from +X towards +Y (x right, y up on screen).
 */
export function boresightView(v) {
  const u = unit(v);
  if (!u) return null;
  const off = angleDeg(u, BODY.boresight);
  const az = Math.atan2(u[1], u[0]);
  return { r: off / 180, az, x: (off / 180) * Math.cos(az), y: (off / 180) * Math.sin(az), offDeg: off };
}

function readVec(src, hexes) {
  const c = hexes.map((h) => src.get(h));
  const verdict = worst(c.map((q) => q.verdict));
  const ages = c.map((q) => q.ageS).filter(fin);
  if (c.some((q) => q.v === null)) return { v: null, verdict, ageS: null };
  const v = c.map((q) => q.v);
  return { v: unit(v), verdict, ageS: ages.length ? Math.max(...ages) : null,
           src: `TM ${hexes[0]}–${hexes[2].slice(-2)}` };
}

/* ── 3. Attitude ────────────────────────────────────────────────────────── */

export const POINTING_FRAMES = { 0: "INERTIAL", 1: "LVLH_NADIR", 2: "TARGET_TRACK", 3: "SUN" };

/**
 * deriveAttitude(src, ctx) -> the model for attitude2d / attitude3d.
 * ctx: { wheelMaxRpm (5500), wheelZeroBandRpm (200), errLimits {warn, alarm} }
 */
export function deriveAttitude(src, ctx = {}) {
  const est = readQuat(src, "est");
  const att = readQuat(src, "att");
  const ref = readQuat(src, "ref");
  const q = est.valid ? est : att;           // q_est first; att_q is the same estimate
  const frameQ = src.get("0x02AF");
  const frameCode = frameQ.v;
  const frame = frameCode === null ? null : (POINTING_FRAMES[Math.round(frameCode)] || `FRAME_${frameCode}`);
  const out = { q, ref, est, att, frame, frameCode, frameVerdict: frameQ.verdict };

  // pointing error: computed from the quaternions (atan2) AND the on-board value
  if (q.valid && ref.valid) {
    const e = quatError(ref.q, q.q);          // body relative to commanded, in commanded axes
    const eu = eulerZYX(e);
    const meta = { verdict: worst(q.verdict, ref.verdict), ageS: Math.max(q.ageS ?? 0, ref.ageS ?? 0),
                   src: "ground: 2·atan2(|δq_v|, δq_w), δq = q_ref⁻¹ ⊗ q_est", ground: true };
    out.errQuat = e;
    out.errDeg = qty(quatAngleDeg(e), "°", meta);
    out.roll = qty(eu.roll, "°", meta);
    out.pitch = qty(eu.pitch, "°", meta);
    out.yaw = qty(eu.yaw, "°", meta);
    out.singular = eu.singular;
  } else {
    const why = !q.valid ? q.reason : ref.reason;
    for (const k of ["errDeg", "roll", "pitch", "yaw"]) out[k] = { ...qty(null, "°"), reason: why };
    out.singular = false;
  }
  out.errTm = withUnits(src.get("0x02A8").v !== null ? src.get("0x02A8") : src.get("0x0217"), "°");
  const lim = ctx.errLimits || limitBand(src.limits, "0x0217") || {};
  out.errLimits = { warn: lim.warn ?? lim.yellow_high ?? null, alarm: lim.alarm ?? lim.red_high ?? null };

  // frame label: which frame the roll/pitch/yaw are expressed against
  out.frameLabel = frame === "LVLH_NADIR" ? "LVLH (nadir)" : frame === "INERTIAL" ? "inertial"
    : frame === "SUN" ? "sun-pointing" : frame === "TARGET_TRACK" ? "target track" : "unknown";

  // body rates (estimate, bias corrected); fall back to the legacy rates
  const rx = src.get("0x02A4").v !== null ? ["0x02A4", "0x02A5", "0x02A6"] : ["0x0204", "0x0205", "0x0206"];
  out.rates = rx.map((h) => withUnits(src.get(h), "°/s"));

  // sun and nadir in body axes
  const cssValid = src.get("0x0248");
  const sun = readVec(src, ["0x0245", "0x0246", "0x0247"]);
  const sunOk = sun.v && cssValid.v !== null && cssValid.v >= 1;
  out.sun = { v: sunOk ? sun.v : null, verdict: worst(sun.verdict, cssValid.verdict),
              ageS: sun.ageS, valid: !!sunOk,
              reason: cssValid.v === null ? "no data" : sunOk ? "" : "sun sensors not valid (eclipse or off)",
              src: "TM 0x0245–47 (CSS)" };
  const nadir = readVec(src, ["0x02B0", "0x02B1", "0x02B2"]);
  out.nadir = { v: nadir.v, verdict: nadir.verdict, ageS: nadir.ageS, valid: !!nadir.v,
                reason: nadir.v ? "" : "no data", src: "TM 0x02B0–B2" };

  const driveQ = src.get("0x0133");
  const angMeta = (vs) => ({ verdict: worst(vs), src: "ground: angle between body vectors", ground: true });
  const sv = out.sun.v, nv = out.nadir.v;
  out.angles = {
    sunBoresight: qty(sv ? angleDeg(sv, BODY.boresight) : null, "°", angMeta([out.sun.verdict])),
    sunRadiator: qty(sv ? angleDeg(sv, BODY.radiator) : null, "°", angMeta([out.sun.verdict])),
    sunStarTracker: qty(sv ? angleDeg(sv, BODY.starTracker) : null, "°", angMeta([out.sun.verdict])),
    sunArray: qty(sv && driveQ.v !== null ? angleDeg(sv, wingNormal(driveQ.v)) : null, "°",
      angMeta([out.sun.verdict, driveQ.verdict])),
    offNadir: qty(nv ? angleDeg(nv, BODY.boresight) : null, "°", angMeta([out.nadir.verdict])),
  };
  out.angles.sunReason = out.sun.reason;
  out.driveDeg = withUnits(driveQ, "°");

  // wheels against saturation and the zero-crossing band
  const maxRpm = ctx.wheelMaxRpm || 5500;
  const zb = ctx.wheelZeroBandRpm ?? 200;
  out.wheels = [0, 1, 2, 3].map((i) => {
    const sp = withUnits(src.get(hex(0x0207 + i)), "rpm");
    const en = src.get(hex(0x0254 + i));
    return { id: `RW${i + 1}`, speed: sp, maxRpm, zeroBandRpm: zb,
             enabled: en.v === null ? null : en.v >= 1,
             frac: sp.v === null ? null : sp.v / maxRpm,
             inZeroBand: sp.v !== null && Math.abs(sp.v) < zb };
  });
  // momentum envelope (most-loaded wheel) and its trend
  const env = src.get("0x02BA");
  out.momentum = {
    envPct: withUnits(env.v !== null ? env : src.get("0x0282"), "%"),
    h: withUnits(src.get("0x025B"), "N·m·s"),
  };
  out.mode = src.get("0x020F");
  return out;
}

/* ── 4. Orbit ───────────────────────────────────────────────────────────── */

export const MU_KM3_S2 = 398600.4418;
export const R_EARTH_KM = 6378.137;

/** Circular period from altitude, seconds (Kepler's third law). */
export function periodFromAltS(altKm) {
  const a = R_EARTH_KM + altKm;
  return 2 * Math.PI * Math.sqrt((a * a * a) / MU_KM3_S2);
}
/** Critical beta above which a circular orbit has no eclipse, degrees. */
export function betaCriticalDeg(altKm) {
  return (Math.asin(R_EARTH_KM / (R_EARTH_KM + altKm)) * 180) / Math.PI;
}
/** Cylindrical-shadow eclipse fraction of a circular orbit (0..~0.4). */
export function eclipseFraction(altKm, betaDeg = 0) {
  const R = R_EARTH_KM, h = altKm;
  const b = (Math.abs(betaDeg) * Math.PI) / 180;
  if (Math.abs(betaDeg) >= betaCriticalDeg(altKm)) return 0;
  const x = Math.sqrt(h * h + 2 * R * h) / ((R + h) * Math.cos(b));
  return x >= 1 ? 0 : Math.acos(x) / Math.PI;
}

/**
 * deriveOrbit(src) — position, period and the eclipse timeline. Present
 * eclipse state comes from the spacecraft when the server has it
 * (state.eclipse_source), the timeline from the ground propagator.
 */
export function deriveOrbit(src) {
  const alt = stateQty(src, "alt_km", "km", "ground propagator");
  const lat = stateQty(src, "lat", "°"), lon = stateQty(src, "lon", "°");
  const st = src.state || {};
  let inEcl = st.in_eclipse ?? st.eclipse;
  let eclSrc = st.eclipse_source || "ground";
  if (inEcl === undefined || inEcl === null) {
    const f = src.get("0x0108");
    inEcl = f.v === null ? null : f.v >= 1;
    eclSrc = "TM 0x0108";
  }
  const period = alt.v !== null ? periodFromAltS(alt.v) : null;
  const tIn = num(st.time_to_eclipse_entry_s), tOut = num(st.time_to_eclipse_exit_s);
  const beta = src.get("0x0216");
  // eclipse duration: from the propagator's own next entry/exit when both are
  // known (60 s resolution), else the cylindrical model at the served beta
  // (beta = 0, the worst case, when beta is not available)
  let eclS = null, eclHow = "";
  if (tIn !== null && tOut !== null && inEcl !== null) {
    if (!inEcl && tOut > tIn) { eclS = tOut - tIn; eclHow = "ground: next entry→exit"; }
    else if (inEcl && tIn > tOut && period) { eclS = period - (tIn - tOut); eclHow = "ground: period − next sunlit arc"; }
  }
  if (eclS === null && period && alt.v !== null) {
    eclS = period * eclipseFraction(alt.v, beta.v ?? 0);
    eclHow = beta.v === null ? "ground: cylindrical shadow, β = 0 assumed" : "ground: cylindrical shadow at β";
  }
  const g = { verdict: alt.verdict, ground: true };
  return {
    lat, lon, alt,
    periodS: qty(period, "s", { ...g, src: "ground: Kepler from altitude" }),
    inEclipse: inEcl === null ? null : !!inEcl, eclipseSource: eclSrc,
    toEntryS: qty(inEcl ? null : tIn, "s", { ...g, verdict: "fresh", src: "ground propagator" }),
    toExitS: qty(inEcl ? tOut : null, "s", { ...g, verdict: "fresh", src: "ground propagator" }),
    eclipseS: qty(eclS, "s", { ...g, src: eclHow }),
    betaDeg: withUnits(beta, "°"),
    betaCritDeg: alt.v !== null ? betaCriticalDeg(alt.v) : null,
  };
}

/* ── 5. Power ───────────────────────────────────────────────────────────── */

const hex = (n) => "0x" + n.toString(16).toUpperCase().padStart(4, "0");

/** EOSAT-1 power lines (eps.yaml order), grouped for the flow diagram. */
export const POWER_LINES = [
  { id: "obc", label: "OBC", group: "Platform", i: "0x0118", on: "0x0110" },
  { id: "ttc_rx", label: "TT&C RX", group: "Platform", i: "0x0119", on: "0x0111" },
  { id: "ttc_tx", label: "TT&C TX", group: "Comms", i: "0x011A", on: "0x0112" },
  { id: "payload", label: "Imager", group: "Payload", i: "0x011B", on: "0x0113" },
  { id: "fpa_cooler", label: "FPA cooler", group: "Payload", i: "0x011C", on: "0x0114" },
  { id: "htr_bat", label: "Battery heater", group: "Thermal", i: "0x011D", on: "0x0115" },
  { id: "htr_obc", label: "OBC heater", group: "Thermal", i: "0x011E", on: "0x0116" },
  { id: "aocs_wheels", label: "AOCS wheels", group: "AOCS", i: "0x011F", on: "0x0117" },
  { id: "prop", label: "Propulsion", group: "Propulsion", i: "0x014B", on: "0x014A" },
];
export const POWER_GROUPS = ["Platform", "Comms", "Payload", "Thermal", "AOCS", "Propulsion"];
/** Load group -> owning subsystem (for click-through). */
export const GROUP_SUBSYSTEM = { Platform: "obdh", Comms: "ttc", Payload: "payload", Thermal: "tcs",
  AOCS: "aocs", Propulsion: "prop" };

/** Linear least-squares slope of [{t, v}] (units per second), or null. */
export function slope(samples) {
  const s = (samples || []).filter((p) => fin(p.t) && fin(p.v));
  if (s.length < 3) return null;
  const n = s.length, mt = s.reduce((a, p) => a + p.t, 0) / n, mv = s.reduce((a, p) => a + p.v, 0) / n;
  let num2 = 0, den = 0;
  for (const p of s) { num2 += (p.t - mt) * (p.v - mv); den += (p.t - mt) ** 2; }
  if (den <= 0) return null;
  return num2 / den;
}
/** Seconds until a trend reaches `limit` from `now`, null if moving away/flat. */
export function timeToLimit(now, ratePerS, limit) {
  if (!fin(now) || !fin(ratePerS) || !fin(limit) || ratePerS === 0) return null;
  const t = (limit - now) / ratePerS;
  return t > 0 ? t : null;
}

/**
 * A tiny timestamped history for trend-based ETAs (time-to-full, time to
 * saturation, last sunlit generation). Stateful, kept by the host page.
 */
export function createHistory(maxAgeS = 900) {
  const S = {};
  return {
    push(t, values) {
      for (const [k, v] of Object.entries(values)) {
        if (!fin(v)) continue;
        const arr = S[k] || (S[k] = []);
        if (arr.length && arr[arr.length - 1].t === t) arr[arr.length - 1].v = Number(v);
        else arr.push({ t, v: Number(v) });
        while (arr.length && t - arr[0].t > maxAgeS) arr.shift();
      }
    },
    series(k, windowS) {
      const arr = S[k] || [];
      if (!windowS || !arr.length) return arr.slice();
      const t1 = arr[arr.length - 1].t;
      return arr.filter((p) => t1 - p.t <= windowS);
    },
    last(k) { const a = S[k] || []; return a.length ? a[a.length - 1] : null; },
  };
}

function limitBand(limits, hexId) {
  const b = (limits || {})[hexId];
  return b && typeof b === "object" ? b : null;
}

/**
 * derivePower(src, ctx) -> energy-flow model.
 * ctx: { batteryWh (100), history, sunlitGenW }
 * Battery current is POSITIVE WHEN CHARGING (models/eps_basic.py).
 * Array currents are referred to the bus: power = I × bus voltage.
 */
export function derivePower(src, ctx = {}) {
  const busV = withUnits(src.get("0x0105"), "V");
  const P = (iHex) => {
    const i = src.get(iHex);
    return from([i, busV], i.v !== null && busV.v !== null ? Math.max(0, i.v * busV.v) : null, "W",
      { src: `${iHex} × bus V`, ground: true });
  };
  const ia = src.get("0x0103"), ib = src.get("0x0104");
  const wpy = src.get("0x0146"), wmy = src.get("0x0147");
  const sub = (a, b) => (a.v !== null && b.v !== null ? Math.max(0, a.v - b.v) : null);
  const mk = (ins, i, label) => from([...ins, busV], i !== null && busV.v !== null ? i * busV.v : null, "W",
    { src: label, ground: true });
  const sources = [
    { id: "wing_py", label: "+Y wing", w: mk([wpy], wpy.v, "0x0146 × bus V") },
    { id: "wing_my", label: "−Y wing", w: mk([wmy], wmy.v, "0x0147 × bus V") },
    { id: "body_a", label: "Body +X +Y +Z", w: mk([ia, wpy], sub(ia, wpy), "(0x0103 − 0x0146) × bus V") },
    { id: "body_b", label: "Body −X −Y −Z", w: mk([ib, wmy], sub(ib, wmy), "(0x0104 − 0x0147) × bus V") },
  ];
  const gen = withUnits(src.get("0x0107"), "W");
  const cons = withUnits(src.get("0x0106"), "W");
  const margin = withUnits(src.get("0x0135"), "W");
  const loads = POWER_LINES.map((l) => {
    const on = src.get(l.on);
    return { ...l, on: on.v === null ? null : on.v >= 1, onVerdict: on.verdict, w: P(l.i) };
  });
  const groups = POWER_GROUPS.map((g) => {
    const ls = loads.filter((l) => l.group === g);
    const known = ls.filter((l) => l.w.v !== null);
    return { id: g, label: g, subsystem: GROUP_SUBSYSTEM[g], lines: ls,
             w: from(ls.map((l) => l.w), known.length === ls.length ? known.reduce((a, l) => a + l.w.v, 0) : null,
                     "W", { src: "Σ line current × bus V", ground: true }) };
  });

  const batI = withUnits(src.get("0x0109"), "A");
  const batV = withUnits(src.get("0x0100"), "V");
  const batW = from([batI, batV], batI.v !== null && batV.v !== null ? batI.v * batV.v : null, "W",
    { src: "0x0109 × 0x0100 (+ = charging)", ground: true });
  const soc = withUnits(src.get("0x0101"), "%");
  const dod = withUnits(src.get("0x0120"), "%");
  const capQ = src.get("0x010A");
  const capWh = capQ.v !== null && capQ.v > 0 ? capQ.v : (ctx.batteryWh || 100);
  const socBand = limitBand(src.limits, "0x0101") || {};
  const dodBand = limitBand(src.limits, "0x0120") || {};
  const socMin = fin(socBand.yellow_low) ? Number(socBand.yellow_low) : 25;
  const socFloor = fin(socBand.red_low) ? Number(socBand.red_low) : 15;
  const dodMax = fin(dodBand.yellow_high) ? Number(dodBand.yellow_high) : 100 - socMin;
  const dir = batI.v === null ? null : batI.v > 0.05 ? "charge" : batI.v < -0.05 ? "discharge" : "idle";

  const orbit = deriveOrbit(src);
  const T = orbit.periodS.v, Tecl = orbit.eclipseS.v;
  const hist = ctx.history;
  // generation while sunlit: now if sunlit, else the last sunlit value seen
  let sunGen = null, sunGenHow = "";
  if (orbit.inEclipse === false && gen.v !== null) { sunGen = gen.v; sunGenHow = "now"; }
  else if (fin(ctx.sunlitGenW)) { sunGen = Number(ctx.sunlitGenW); sunGenHow = "last sunlit arc"; }
  const g = (v, u, how, ins) => from(ins, v, u, { src: how, ground: true });
  const balance = { periodS: T, eclipseS: Tecl, sunGenHow };
  if (T && Tecl !== null && sunGen !== null && cons.v !== null) {
    const ein = (sunGen * (T - Tecl)) / 3600, eout = (cons.v * T) / 3600;
    balance.inWh = g(ein, "Wh", "ground: sunlit generation × sunlit time", [gen, orbit.eclipseS]);
    balance.outWh = g(eout, "Wh", "ground: consumption × period", [cons]);
    balance.netWh = g(ein - eout, "Wh", "ground: in − out (before charge efficiency)", [gen, cons]);
  } else {
    for (const k of ["inWh", "outWh", "netWh"]) balance[k] = qty(null, "Wh", { ground: true });
  }
  // predicted SoC / DoD at the next eclipse exit (simple energy integration)
  let socExit = null;
  if (soc.v !== null && cons.v !== null && Tecl !== null) {
    if (orbit.inEclipse && orbit.toExitS.v !== null) {
      socExit = soc.v - ((cons.v - (gen.v || 0)) * orbit.toExitS.v) / 3600 / capWh * 100;
    } else if (orbit.inEclipse === false && orbit.toEntryS.v !== null && gen.v !== null) {
      const socEntry = Math.min(100, soc.v + (Math.max(0, gen.v - cons.v) * orbit.toEntryS.v) / 3600 / capWh * 100);
      socExit = socEntry - (cons.v * Tecl) / 3600 / capWh * 100;
    }
  }
  const pred = { socAtExit: g(socExit, "%", "ground: energy integration to next eclipse exit", [soc, cons]),
                 dodAtExit: g(socExit === null ? null : 100 - socExit, "%", "ground: 100 − predicted SoC", [soc, cons]) };
  // time to the minimum SoC at the present battery power
  let tMin = null;
  if (soc.v !== null && batW.v !== null && batW.v < -0.5 && soc.v > socMin) {
    tMin = ((soc.v - socMin) / 100) * capWh * 3600 / -batW.v;
  }
  pred.timeToMinSocS = g(tMin, "s", `ground: (SoC − ${socMin} %) × capacity ÷ discharge power`, [soc, batW]);
  pred.minReachedBeforeExit = tMin !== null && orbit.inEclipse && orbit.toExitS.v !== null
    ? tMin < orbit.toExitS.v : null;

  // power margin (TM) and its sign
  return {
    busV, gen, cons, margin, sources, loads, groups,
    battery: { i: batI, v: batV, w: batW, soc, dod, dir, capWh,
               temp: withUnits(src.get("0x0102"), "°C"),
               socMin, socFloor, dodMax, capSrc: capQ.v !== null ? "TM 0x010A" : "config eps.yaml (100 Wh)" },
    shedStage: src.get("0x0134"),
    orbit, balance, pred,
  };
}

/* ── 6. Data storage and link ───────────────────────────────────────────── */

/** Payload storage fill and time to full from its trend (ctx.history). */
export function deriveStorage(src, ctx = {}) {
  const fill = withUnits(src.get("0x0604"), "%");
  const rate = ctx.history ? slope(ctx.history.series("0x0604", 600)) : null;
  const ttf = fill.v !== null && rate !== null && rate > 1e-4 ? (100 - fill.v) / rate : null;
  return { fill, ratePctPerMin: rate === null ? null : rate * 60,
           timeToFullS: qty(ttf, "s", { verdict: fill.verdict, src: "ground: linear trend, last 10 min", ground: true }) };
}

/** Downlink margin (ground link budget) and Eb/N0 (ground receiver). */
export function deriveLink(src) {
  const margin = { ...withUnits(src.get("0x0503"), "dB"), ground: true };
  const ebn0 = { ...withUnits(src.get("0x0519"), "dB"), ground: true };
  return { margin, ebn0, ok: margin.v === null ? null : margin.v >= 0 };
}

/** Momentum trend: seconds until the envelope reaches 100 %. */
export function momentumEta(att, history) {
  const env = att.momentum.envPct;
  if (!history || env.v === null) return qty(null, "s", { ground: true });
  const r = slope(history.series("momentum_env", 600));
  return qty(timeToLimit(env.v, r, 100), "s", { verdict: env.verdict,
    src: "ground: linear trend, last 10 min", ground: true });
}

/* ── 7. Everything at once ──────────────────────────────────────────────── */

/** deriveAll(src, ctx) — the full model the MCS hands its views. */
/* ── 9. Deployables and illumination (overview) ──────────────────────────
 * Only what the spacecraft downlinks; no simulator truth, no ground model.
 *   antenna  ttc.antenna_deployment_sensor 0x0536 (SID 6: 0 unknown,
 *            1 stowed, 2 deployed, 3 partial/jammed), else the commanded
 *            flag ttc.antenna_deployed 0x0520 (SID 6) when the sensor says
 *            nothing.
 *   wings    eps.wing_status 0x0144 (SID 1: bit0 +Y, bit1 −Y deployed);
 *            lit from the wing-only currents 0x0146 / 0x0147 (SID 8): a
 *            wing delivering more than LIT_CURRENT_A is in the sun.
 *   faces    the six body-face currents 0x012B–0x0130 (SID 1). The ±Y face
 *            currents include the deployed wing; the wing current is taken
 *            off when it is downlinked, otherwise the face says so.
 *   eclipse  eps.eclipse_flag 0x0108 (SID 1): in eclipse nothing is lit,
 *            even when no current is downlinked.
 *   strings  eps.sa_string_lit 0x014E (SID 8): the on-board judgement
 *            (bit0 string A, bit1 string B) that gates the yield monitors.
 * Current is a proxy for sunlight: a dead string reads dark in the sun,
 * which is why the on-board string flag is shown beside it. */
export const LIT_CURRENT_A = 0.05;
export const FACE_HEX = [["+X", "0x012B"], ["−X", "0x012C"], ["+Y", "0x012D"],
  ["−Y", "0x012E"], ["+Z", "0x012F"], ["−Z", "0x0130"]];

const pick = (q, extra = {}) => ({ verdict: q.verdict, ageS: q.ageS, src: q.src, ...extra });
const usable = (q) => q.v !== null && q.verdict !== "nodata";

export function deriveDeployment(src) {
  const ecl = src.get("0x0108");
  const eclipse = { v: usable(ecl) ? ecl.v >= 0.5 : null, ...pick(ecl) };
  const darkByEclipse = eclipse.v === true && ecl.verdict !== "stale";

  // antenna: the deployment sensor first, the commanded flag as fallback
  const sen = src.get("0x0536"), flag = src.get("0x0520");
  let antenna;
  if (usable(sen) && sen.v !== 0) {
    antenna = pick(sen, { state: ({ 1: "stowed", 2: "deployed", 3: "jammed" })[Math.round(sen.v)] || "unknown" });
  } else if (usable(flag)) {
    antenna = pick(flag, { state: flag.v >= 0.5 ? "deployed" : "stowed" });
  } else if (usable(sen)) {
    antenna = pick(sen, { state: "unknown" });
  } else {
    antenna = pick(sen, { state: null, verdict: "nodata" });
  }

  const ws = src.get("0x0144");
  const illum = (q) => {
    // a downlinked current decides, unless it is stale and a fresh eclipse
    // flag says nothing can be lit
    if (usable(q) && !(q.verdict === "stale" && darkByEclipse)) {
      return pick(q, { state: q.v > LIT_CURRENT_A ? "sunlit" : "dark", i: { ...q, units: "A" } });
    }
    if (darkByEclipse) return pick(ecl, { state: "dark", eclipse: true, i: null });
    return { state: null, verdict: "nodata", ageS: null, src: q.src, i: null };
  };
  const wing = (bit, curHex) => {
    const deployed = usable(ws) ? ((Math.round(ws.v) >> bit) & 1) === 1 : null;
    const cur = src.get(curHex);
    return {
      deployed, ...pick(ws, usable(ws) ? {} : { verdict: "nodata" }),
      // a stowed wing is folded against the bus: not part of the lit array
      illum: deployed === false ? { state: "stowed", verdict: ws.verdict, ageS: ws.ageS, src: ws.src, i: null }
        : illum(cur),
    };
  };
  const wings = { py: wing(0, "0x0146"), my: wing(1, "0x0147") };

  const faces = FACE_HEX.map(([face, hex]) => {
    let q = src.get(hex);
    let withWing = false;
    const side = face === "+Y" ? "py" : face === "−Y" ? "my" : null;
    if (side && usable(q) && wings[side].deployed !== false) {
      const w = src.get(side === "py" ? "0x0146" : "0x0147");
      if (usable(w)) q = from([q, w], Math.max(0, q.v - w.v), "A", { src: `${q.src} − ${w.src}`, ground: false });
      else withWing = wings[side].deployed === true;
    }
    return { face, withWing, ...illum(q) };
  });

  const sl = src.get("0x014E");
  const strings = usable(sl)
    ? pick(sl, { a: (Math.round(sl.v) & 1) === 1, b: (Math.round(sl.v) & 2) === 2 })
    : { a: null, b: null, verdict: "nodata", ageS: null, src: sl.src };

  return { eclipse, antenna, wings, faces, strings };
}

export function deriveAll(src, ctx = {}) {
  const attitude = deriveAttitude(src, ctx);
  attitude.momentum.etaS = momentumEta(attitude, ctx.history);
  return {
    attitude,
    power: derivePower(src, ctx),
    orbit: deriveOrbit(src),
    storage: deriveStorage(src, ctx),
    link: deriveLink(src),
    deploy: deriveDeployment(src),
  };
}

/** Values the host should push into its history each update. */
export function historySample(src) {
  const env = src.get("0x02BA").v ?? src.get("0x0282").v;
  return { "0x0604": src.get("0x0604").v, momentum_env: env, gen: src.get("0x0107").v };
}
