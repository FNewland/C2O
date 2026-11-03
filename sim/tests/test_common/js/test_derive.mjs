// Unit tests for shared/ui-viz/derive.js — hand-computed cases.
//   node sim/tests/test_common/js/test_derive.mjs <path-to-derive.js>
// Prints "ok N" and exits 0, or prints every failure and exits 1.
// Run by sim/tests/test_common/test_ui_viz.py (which also cross-checks the
// quaternion algebra against smo_common/attitude.py).
import { pathToFileURL } from "node:url";

const D = await import(pathToFileURL(process.argv[2]).href);
const fails = [];
let n = 0;
const near = (a, b, tol, msg) => {
  n++;
  if (!(Math.abs(a - b) <= tol)) fails.push(`${msg}: got ${a}, want ${b} ± ${tol}`);
};
const eq = (a, b, msg) => { n++; if (a !== b) fails.push(`${msg}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`); };

/* a source from plain values (fresh, age 1 s) */
function src(params, state = {}, limits = {}) {
  const ages = Object.fromEntries(Object.keys(params).map((h) => [String(parseInt(h, 16)), 1]));
  return D.sourceFromState({ params, params_age: ages, ...state }, { limits });
}
const qp = (hexes, q) => Object.fromEntries(hexes.map((h, i) => [h, q[i]]));

/* 1. quaternion basics */
const r10 = D.quatFromAxisAngle([1, 0, 0], 10);
near(D.quatAngleDeg(r10), 10, 1e-9, "axis-angle 10° round trip");
near(D.attitudeAngleDeg([0, 0, 0, 1], r10), 10, 1e-9, "angle identity→10° roll");
// sign flip: q and -q are the same attitude (no 180°/360° jumps)
near(D.attitudeAngleDeg(r10, r10.map((c) => -c)), 0, 1e-9, "q vs -q is 0°");
// tiny angles keep precision with the atan2 form
const tiny = D.quatFromAxisAngle([0, 1, 0], 1e-4);
near(D.quatAngleDeg(tiny), 1e-4, 1e-10, "1e-4° error resolved (atan2)");
// DCM: +90° about Z (body relative to ECI). C maps ECI→body: ECI +X is body -Y.
const z90 = D.quatFromAxisAngle([0, 0, 1], 90);
const v = D.matVec(D.quatToDcm(z90), [1, 0, 0]);
near(v[0], 0, 1e-12, "C(z90)·x̂ x"); near(v[1], -1, 1e-12, "C(z90)·x̂ y"); near(v[2], 0, 1e-12, "C(z90)·x̂ z");
// composition rule C(a)·C(b) = C(b ⊗ a)
{
  const a = D.quatFromAxisAngle([1, 2, 3], 37), b = D.quatFromAxisAngle([-2, 0.5, 1], 71);
  const Ca = D.quatToDcm(a), Cb = D.quatToDcm(b), Cba = D.quatToDcm(D.quatMul(b, a));
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
    const s = Ca[i][0] * Cb[0][j] + Ca[i][1] * Cb[1][j] + Ca[i][2] * Cb[2][j];
    near(s, Cba[i][j], 1e-12, `C(a)C(b)=C(b⊗a) [${i}][${j}]`);
  }
}

/* 2. the scalar-first / scalar-last trap */
{
  const qLast = r10;                               // [x y z w] for a 10° roll
  const qFirst = D.toScalarFirst(qLast);           // [w x y z]
  near(D.attitudeAngleDeg([0, 0, 0, 1], D.fromScalarFirst(qFirst)), 10, 1e-9, "scalar-first converted: 10°");
  // read naively as if it were scalar-last: w=0 → a ~180° "error"
  const naive = D.attitudeAngleDeg([0, 0, 0, 1], D.quatNorm(qFirst));
  n++; if (!(naive > 150)) fails.push(`scalar-first misread should be wildly wrong, got ${naive}`);
  // The angle between two quaternions is order-invariant when BOTH are
  // misread the same way; the bug bites when two sources disagree (an
  // estimate scalar-last, a reference scalar-first): 25° becomes nonsense.
  const a = D.quatFromAxisAngle([1, 1, 0], 50), b = D.quatMul(a, D.quatFromAxisAngle([0, 0, 1], 25));
  near(D.attitudeAngleDeg(D.toScalarFirst(a), D.toScalarFirst(b)), 25, 1e-9, "same misread on both: still 25°");
  near(D.attitudeAngleDeg(a, D.fromScalarFirst(D.toScalarFirst(b))), 25, 1e-9, "mixed sources, converted: 25°");
  const wrong = D.attitudeAngleDeg(a, D.toScalarFirst(b));
  n++; if (!(Math.abs(wrong - 25) > 5)) fails.push(`mixed sources misread should differ from 25°, got ${wrong}`);
}

/* 3. attitude model from telemetry: roll/pitch/yaw relative to commanded */
const EST = ["0x02A0", "0x02A1", "0x02A2", "0x02A3"], REF = ["0x02AB", "0x02AC", "0x02AD", "0x02AE"];
{
  const ref = D.quatFromAxisAngle([0.3, -1, 0.2], 140);       // arbitrary commanded attitude
  const est = D.quatMul(ref, D.quatFromAxisAngle([0, 1, 0], 3)); // 3° about body Y
  const a = D.deriveAttitude(src({ ...qp(EST, est), ...qp(REF, ref), "0x02AF": 1 }));
  near(a.errDeg.v, 3, 1e-9, "pointing error 3°");
  near(a.pitch.v, 3, 1e-9, "pitch 3°"); near(a.roll.v, 0, 1e-9, "roll 0°"); near(a.yaw.v, 0, 1e-9, "yaw 0°");
  eq(a.frameLabel, "LVLH (nadir)", "frame label");
  eq(a.singular, false, "not singular");
  // roll 4° then yaw: z-y-x composition e = yaw ⊗ pitch ⊗ roll
  const e = D.quatMul(D.quatFromAxisAngle([0, 0, 1], -7), D.quatMul(D.quatFromAxisAngle([0, 1, 0], 2), D.quatFromAxisAngle([1, 0, 0], 4)));
  const b = D.deriveAttitude(src({ ...qp(EST, D.quatMul(ref, e)), ...qp(REF, ref), "0x02AF": 0 }));
  near(b.roll.v, 4, 1e-9, "zyx roll"); near(b.pitch.v, 2, 1e-9, "zyx pitch"); near(b.yaw.v, -7, 1e-9, "zyx yaw");
  eq(b.frameLabel, "inertial", "inertial label");
  // gimbal guard
  const g = D.deriveAttitude(src({ ...qp(EST, D.quatFromAxisAngle([0, 1, 0], 87)), ...qp(REF, [0, 0, 0, 1]) }));
  eq(g.singular, true, "pitch 87° flagged near gimbal lock");
  // all-zero quaternion = no attitude solution, never "identity"
  const z = D.deriveAttitude(src({ ...qp(EST, [0, 0, 0, 0]), "0x0200": 0, "0x0201": 0, "0x0202": 0, "0x0203": 0, ...qp(REF, ref) }));
  eq(z.errDeg.v, null, "zero quaternion gives no error angle");
  eq(z.errDeg.reason, "no attitude solution", "zero quaternion reason");
  // a stale input makes the derived value stale
  const st = D.sourceFromState({ params: { ...qp(EST, est), ...qp(REF, ref) },
    params_age: { [String(0x02A0)]: 120 } });
  eq(D.deriveAttitude(st).errDeg.verdict, "stale", "stale input → stale derived value");
}

/* 4. vectors */
{
  const a = D.deriveAttitude(src({ "0x0245": 0, "0x0246": 0, "0x0247": -1, "0x0248": 1,
    "0x02B0": 0, "0x02B1": Math.sin(Math.PI / 18), "0x02B2": -Math.cos(Math.PI / 18), "0x0133": 90 }));
  near(a.angles.sunBoresight.v, 0, 1e-9, "sun on boresight");
  near(a.angles.offNadir.v, 10, 1e-9, "off-nadir 10°");
  near(a.angles.sunArray.v, 180, 1e-9, "wing at 90° faces +Z: sun on -Z is behind it");
  const c = D.deriveAttitude(src({ "0x0245": 1, "0x0246": 0, "0x0247": 0, "0x0248": 0 }));
  eq(c.sun.valid, false, "CSS invalid flag hides the sun vector");
  const bv = D.boresightView([0, 0, 1]);
  near(bv.r, 1, 1e-12, "zenith sits on the rim of the boresight view");
  const w = D.wingNormal(0);
  near(w[0], 1, 1e-12, "wing normal at 0° = +X");
}

/* 5. orbit (EOSAT-1, 500 km) — report: 94.6 min period, ~36 min eclipse, β* ≈ 68° */
near(D.periodFromAltS(500) / 60, 94.62, 0.01, "period at 500 km");
near(D.betaCriticalDeg(500), 68.03, 0.02, "critical beta at 500 km");
near(D.eclipseFraction(500, 0) * D.periodFromAltS(500) / 60, 35.76, 0.05, "eclipse minutes at β=0");
eq(D.eclipseFraction(500, 70), 0, "no eclipse above β*");
{
  const o = D.deriveOrbit(src({}, { alt_km: 500, in_eclipse: false, time_to_eclipse_entry_s: 600, time_to_eclipse_exit_s: 2760 }));
  near(o.eclipseS.v, 2160, 1e-9, "eclipse duration from next entry→exit");
  near(o.toEntryS.v, 600, 1e-9, "time to entry");
  eq(o.toExitS.v, null, "no exit countdown while sunlit");
}

/* 6. power: hand-computed flow and predictions */
{
  const p = D.derivePower(src({
    "0x0105": 28, "0x0103": 2.0, "0x0104": 1.5, "0x0146": 1.5, "0x0147": 1.0, "0x0107": 98,
    "0x0106": 40, "0x0135": 58, "0x0109": 2.0, "0x0100": 29, "0x0101": 80, "0x0120": 20,
    "0x0118": 0.2, "0x0110": 1, "0x011B": 0.5, "0x0113": 1,
  }, { alt_km: 500, in_eclipse: false, time_to_eclipse_entry_s: 1200, time_to_eclipse_exit_s: 3360 },
  { "0x0101": { yellow_low: 25, red_low: 15 } }), { batteryWh: 100 });
  near(p.sources[0].w.v, 42, 1e-9, "+Y wing 1.5 A × 28 V");
  near(p.sources[2].w.v, 14, 1e-9, "body A (2.0 − 1.5) A × 28 V");
  near(p.loads[0].w.v, 5.6, 1e-9, "OBC line 0.2 A × 28 V");
  near(p.battery.w.v, 58, 1e-9, "battery +2 A × 29 V charging");
  eq(p.battery.dir, "charge", "battery direction");
  // orbit balance: T = 5677 s, eclipse 2160 s → in = 98 × 3517/3600, out = 40 × 5677/3600
  const T = D.periodFromAltS(500);
  near(p.balance.inWh.v, 98 * (T - 2160) / 3600, 1e-6, "energy in this orbit");
  near(p.balance.outWh.v, 40 * T / 3600, 1e-6, "energy out this orbit");
  // SoC at exit: 80 + 58 × 1200 / 3600 → 99.33 %, then − 40 × 2160 / 3600 = 24 → 75.33 %
  near(p.pred.socAtExit.v, 80 + 58 * 1200 / 3600 / 100 * 100 - 40 * 2160 / 3600, 1e-6, "predicted SoC at eclipse exit");
  eq(p.pred.timeToMinSocS.v, null, "no time-to-min while charging");
  // discharging in eclipse: 60 % SoC, −1.5 A × 27 V = −40.5 W, min 25 %: (35 % × 100 Wh) / 40.5 W
  const q = D.derivePower(src({ "0x0101": 60, "0x0109": -1.5, "0x0100": 27, "0x0106": 40.5, "0x0107": 0, "0x0105": 28 },
    { alt_km: 500, in_eclipse: true, time_to_eclipse_entry_s: 5000, time_to_eclipse_exit_s: 900 },
    { "0x0101": { yellow_low: 25 } }));
  near(q.pred.timeToMinSocS.v, 0.35 * 100 * 3600 / 40.5, 1e-6, "time to min SoC");
  eq(q.pred.minReachedBeforeExit, false, "min SoC not reached before exit");
  near(q.pred.socAtExit.v, 60 - 40.5 * 900 / 3600, 1e-6, "SoC at exit while in eclipse");
}

/* 7. trends */
{
  const h = D.createHistory(900);
  for (let t = 0; t <= 300; t += 30) h.push(t, { "0x0604": 40 + t / 60 });   // +1 %/min
  const s = D.deriveStorage(src({ "0x0604": 45 }), { history: h });
  near(s.ratePctPerMin, 1, 1e-9, "storage fill rate");
  near(s.timeToFullS.v, 55 * 60, 1e-6, "storage time to full");
  eq(D.timeToLimit(50, -1, 100), null, "moving away from the limit: no ETA");
  eq(D.worst("fresh", "degraded", "stale"), "stale", "worst verdict");
  eq(D.worst("fresh", "nodata"), "nodata", "no data dominates");
}

/* 8. deployables and illumination (overview): TM only */
{
  // nothing downlinked: every item says no data, nothing is invented
  const none = D.deriveDeployment(src({}));
  eq(none.antenna.state, null, "antenna: no TM, no state");
  eq(none.antenna.verdict, "nodata", "antenna: no data verdict");
  eq(none.wings.py.deployed, null, "wing: no TM, deployment unknown");
  eq(none.wings.py.illum.state, null, "wing: no TM, illumination unknown");
  eq(none.faces.length, 6, "six body faces");
  eq(none.faces.every((f) => f.state === null), true, "faces: no data");
  eq(none.strings.a, null, "strings: no data");

  // LEOP: wings stowed, antenna stowed (sensor), sunlit body faces
  const leop = D.deriveDeployment(src({ "0x0144": 0, "0x0536": 1, "0x0520": 0, "0x0108": 0,
    "0x012B": 0.8, "0x012C": 0, "0x012D": 0.3, "0x012E": 0, "0x012F": 0.01, "0x0130": 0, "0x014E": 1 }));
  eq(leop.antenna.state, "stowed", "antenna stowed from the sensor");
  eq(leop.wings.py.deployed, false, "+Y wing stowed");
  eq(leop.wings.py.illum.state, "stowed", "stowed wing is not part of the lit array");
  eq(leop.faces[0].state, "sunlit", "+X face lit at 0.8 A");
  eq(leop.faces[1].state, "dark", "−X face dark at 0 A");
  eq(leop.faces[2].withWing, false, "+Y face: wing stowed, current is the body's");
  eq(leop.faces[4].state, "dark", "+Z face at 0.01 A is below the lit threshold");
  eq(leop.strings.a, true, "string A lit (bit0)"); eq(leop.strings.b, false, "string B not lit");

  // deployed: the sensor wins over the commanded flag; wing currents decide;
  // the ±Y faces lose the wing's own current
  const dep = D.deriveDeployment(src({ "0x0144": 3, "0x0536": 2, "0x0520": 1, "0x0108": 0,
    "0x0146": 3.2, "0x0147": 0.0, "0x012D": 3.5, "0x012E": 0.02, "0x014E": 3 }));
  eq(dep.antenna.state, "deployed", "antenna deployed");
  eq(dep.wings.py.deployed && dep.wings.my.deployed, true, "both wings deployed (bits 0 and 1)");
  eq(dep.wings.py.illum.state, "sunlit", "+Y wing sunlit at 3.2 A");
  near(dep.wings.py.illum.i.v, 3.2, 1e-9, "+Y wing current carried");
  eq(dep.wings.my.illum.state, "dark", "−Y wing dark at 0 A");
  near(dep.faces[2].i.v, 0.3, 1e-9, "+Y body face = face current − wing current");
  eq(dep.faces[2].withWing, false, "wing current downlinked: taken off the face");

  // jammed sensor; sensor 0 (unknown) falls back to the commanded flag
  eq(D.deriveDeployment(src({ "0x0536": 3, "0x0520": 0 })).antenna.state, "jammed", "sensor 3 = jammed");
  eq(D.deriveDeployment(src({ "0x0536": 0, "0x0520": 1 })).antenna.state, "deployed", "sensor unknown: commanded flag");
  eq(D.deriveDeployment(src({ "0x0536": 0 })).antenna.state, "unknown", "sensor unknown, no flag");

  // eclipse with no wing current downlinked (SID 8 off): dark, from the flag;
  // deployed, no wing current, sunlit: the ±Y face says it includes the wing
  const ecl = D.deriveDeployment(src({ "0x0144": 3, "0x0108": 1, "0x012D": 0 }));
  eq(ecl.wings.py.illum.state, "dark", "eclipse: wing dark without its current");
  eq(ecl.wings.py.illum.eclipse, true, "dark because of the eclipse flag");
  eq(ecl.faces[0].state, "dark", "eclipse: a face with no current is dark");
  const sun = D.deriveDeployment(src({ "0x0144": 3, "0x0108": 0, "0x012D": 3.4 }));
  eq(sun.wings.py.illum.state, null, "sunlit orbit, no wing current: unknown");
  eq(sun.faces[2].withWing, true, "+Y face includes the wing");

  // stale TM keeps its last state, marked stale
  const st = D.sourceFromState({ params: { "0x0144": 1, "0x0146": 2.0 }, params_age: { [String(0x0144)]: 1, [String(0x0146)]: 300 } }, {});
  const sd = D.deriveDeployment(st);
  eq(sd.wings.py.illum.state, "sunlit", "stale wing current keeps its state");
  eq(sd.wings.py.illum.verdict, "stale", "…marked stale");
}

if (fails.length) { console.log(fails.join("\n")); process.exit(1); }
console.log(`ok ${n}`);
