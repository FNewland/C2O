// Unit tests for the pure geometry of shared/ui-viz attitude3d.js,
// groundtrack.js and skyplot.js — hand-computed cases.
//   node test_geometry_views.mjs <ui-viz dir> '<reference JSON>'
// The reference JSON is computed by sim/tests/test_common/test_ui_viz_geometry.py
// with smo_common.attitude (the simulator's own frame maths), so the
// browser's LVLH/quaternion handling is checked against the simulator.
// Prints "ok N" and exits 0, or prints every failure and exits 1.
import { pathToFileURL } from "node:url";

const dir = process.argv[2];
const REF = JSON.parse(process.argv[3] || "{}");
const A3 = await import(pathToFileURL(`${dir}/attitude3d.js`).href);
const GT = await import(pathToFileURL(`${dir}/groundtrack.js`).href);
const SK = await import(pathToFileURL(`${dir}/skyplot.js`).href);
const fails = [];
let n = 0;
const near = (a, b, tol, msg) => { n++; if (!(Math.abs(a - b) <= tol)) fails.push(`${msg}: got ${a}, want ${b} ± ${tol}`); };
const eq = (a, b, msg) => { n++; if (a !== b) fails.push(`${msg}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`); };
const nearM = (A, B, tol, msg) => A.forEach((r, i) => r.forEach((c, j) => near(c, B[i][j], tol, `${msg}[${i}][${j}]`)));
const nearV = (a, b, tol, msg) => a.forEach((c, i) => near(c, b[i], tol, `${msg}[${i}]`));

/* ── attitude3d: conventions against smo_common.attitude ── */
if (REF.q) {
  nearM(A3.quatToDcm(REF.q), REF.C, 1e-12, "quatToDcm == smo_common.attitude.quat_to_dcm");
  nearM(A3.lvlhFromRV(REF.r, REF.v), REF.L, 1e-12, "lvlhFromRV == smo_common.attitude.lvlh_dcm");
  // the commanded nadir quaternion (aocs_basic.nominal_body_dcm) gives back L exactly
  nearM(A3.lvlhFromNadirRef(REF.qNominal), REF.L, 1e-9, "lvlhFromNadirRef(q_ref nadir) == L");
}

/* a nominal nadir attitude built from r, v: body +Z must be scene up
 * (zenith), body +X along velocity (scene +x), body +Y = orbit normal = scene -z */
if (REF.qNominal) {
  const geo = { star_trackers: [{ id: "st1", boresight: [0, 0, 1] }, { id: "st2", boresight: [0, Math.SQRT1_2, Math.SQRT1_2] }],
    star_tracker_sun_exclusion_deg: 15, star_tracker_earth_exclusion_deg: 25,
    array_drive: { normal_at_0deg: [1, 0, 0], normal_at_90deg: [0, 0, 1] }, payload: { boresight: [0, 0, -1] } };
  const m = { q: { q: REF.qNominal, valid: true }, ref: { q: REF.qNominal, valid: true },
    lvlh: { r: REF.r, v: REF.v }, nadir: { v: [0, 0, -1], valid: true }, sun: { v: [0, Math.SQRT1_2, Math.SQRT1_2 * 1.0001], valid: true },
    driveDeg: { v: 90 } };
  const sc = A3.attitudeScene(m, geo, "lvlh");
  eq(sc.ok, true, "nominal scene ok");
  eq(sc.frame, "lvlh", "frame lvlh");
  nearV(A3.mv(sc.Rbody, [0, 0, 1]), [0, 1, 0], 1e-9, "body +Z -> scene up (zenith)");
  nearV(A3.mv(sc.Rbody, [1, 0, 0]), [1, 0, 0], 1e-9, "body +X -> scene +x (velocity)");
  nearV(A3.mv(sc.Rbody, [0, 1, 0]), [0, 0, -1], 1e-9, "body +Y (orbit normal) -> scene -z");
  nearV(sc.nadir, [0, -1, 0], 1e-9, "nadir straight down in LVLH");
  nearV(sc.velocity, [1, 0, 0], 1e-3, "velocity to the right in LVLH");
  near(sc.errDeg, 0, 1e-6, "estimate == commanded -> 0 deg");
  near(sc.offNadirDeg, 0, 1e-9, "imager on nadir");
  // sun exactly on the ST2 boresight: blinded; ST1 at 45 deg: clear
  eq(sc.checks.find((c) => c.id === "st2").blinded, true, "ST2 blinded by the sun on its boresight");
  eq(sc.checks.find((c) => c.id === "st1").blinded, false, "ST1 clear at 45 deg");
  // drive angle 90: wing normal (0,0,1) per eps_basic._wing_normal
  nearV(sc.wingNormal, [0, 0, 1], 1e-12, "wing normal at 90 deg");
  // no orbit state and not commanding LVLH -> inertial, with the reason
  const sc2 = A3.attitudeScene({ ...m, lvlh: undefined, frame: "SUN" }, geo, "lvlh");
  eq(sc2.frame, "inertial", "LVLH unavailable falls back to inertial");
  eq(!!sc2.lvlhReason, true, "and says why");
  // commanding LVLH nadir: L recovered from q_ref, labelled as such
  const sc3 = A3.attitudeScene({ ...m, lvlh: undefined, frame: "LVLH_NADIR" }, geo, "lvlh");
  eq(sc3.frame, "lvlh", "LVLH from the commanded nadir reference");
  eq(sc3.lvlhSrc, "commanded nadir reference", "source printed");
  nearV(A3.mv(sc3.Rbody, [0, 0, 1]), [0, 1, 0], 1e-9, "same picture from q_ref");
  // all-zero placeholder quaternion is no data, never identity
  eq(A3.attitudeScene({ q: { q: [0, 0, 0, 0], valid: true } }, geo).ok, false, "zero quaternion is no attitude");
}
/* error angle: atan2 form, q/-q, and the scalar-first trap */
{
  const h = (10 * Math.PI) / 360;
  const q10 = [Math.sin(h), 0, 0, Math.cos(h)];
  near(A3.errAngleDeg([0, 0, 0, 1], q10), 10, 1e-9, "10 deg roll");
  near(A3.errAngleDeg(q10, q10.map((c) => -c)), 0, 1e-9, "q vs -q is 0 deg");
  const trap = [q10[3], q10[0], q10[1], q10[2]];         // [w,x,y,z] read as [x,y,z,w]
  n++; if (!(A3.errAngleDeg([0, 0, 0, 1], trap) > 150)) fails.push("scalar-first trap should look like ~170 deg");
  near(A3.angleDeg([1, 0, 0], [1, 1e-9, 0]), 5.7e-8, 1e-9, "angle near 0 keeps precision");
}

/* ── groundtrack ── */
{
  // coverage: lambda = acos(R/(R+h) cos e) - e, 513 km, 5 deg mask
  const R = 6378.137, h = 513, e = (5 * Math.PI) / 180;
  near(GT.coverageAngleDeg(513, 5), ((Math.acos((R / (R + h)) * Math.cos(e)) - e) * 180) / Math.PI, 1e-12, "coverage angle");
  near(GT.coverageAngleDeg(513, 5), 17.77, 0.01, "coverage 17.77 deg (~1980 km): acos(0.9221) - 5");
  // March equinox 2026-03-20 12:00 UTC: sub-solar point near (0, ~0 lon)
  const ss = GT.subsolarPoint(Date.UTC(2026, 2, 20, 12, 0, 0));
  near(ss.lat, 0, 0.5, "equinox sub-solar latitude");
  near(ss.lon, 0, 3, "noon UTC sub-solar longitude (equation of time < 3 deg)");
  // June solstice: declination +23.4
  near(GT.subsolarPoint(Date.UTC(2026, 5, 21, 12)).lat, 23.43, 0.1, "June solstice declination");
  // track interpolation across the antimeridian goes the short way
  const tr = GT.normTrack([{ t: 0, lat: 0, lon: 179, in_eclipse: false }, { t: 1000, lat: 2, lon: -179, in_eclipse: true }]);
  const p = GT.interpTrack(tr, 500);
  near(Math.abs(p.lon), 180, 1e-9, "antimeridian midpoint at 180");
  near(p.lat, 1, 1e-9, "midpoint latitude");
  const tx = GT.eclipseTransitions(tr);
  eq(tx.length, 1, "one transition"); eq(tx[0].kind, "entry", "eclipse entry");
  // small circle radius is constant
  const sc = GT.smallCircle(78.2, 15.4, 20, 36);
  n++; if (!sc.every(([lo, la]) => Number.isFinite(lo) && la >= -90 && la <= 90)) fails.push("small circle points valid");
}

/* ── skyplot ── */
{
  const st = { name: "X", lat: 45, lon: 10, alt_km: 0, min_elevation_deg: 5 };
  const over = SK.lookAngles(st, [{ t: 0, lat: 45, lon: 10, alt_km: 500 }])[0];
  near(over.el, 90, 0.2, "overhead -> el 90");
  near(over.range, 500, 1, "overhead range = altitude");
  const north = SK.lookAngles(st, [{ t: 0, lat: 50, lon: 10, alt_km: 500 }])[0];
  near(north.az, 0, 0.5, "due north -> az 0");
  const east = SK.lookAngles(st, [{ t: 0, lat: 45, lon: 15, alt_km: 500 }])[0];
  n++; if (!(east.az > 80 && east.az < 100)) fails.push(`due east -> az ~90, got ${east.az}`);
  // AOS/LOS interpolated to the mask crossing, max elevation and its time
  const ps = SK.passesFromSamples([{ t: 0, az: 10, el: 0 }, { t: 60, az: 20, el: 10 }, { t: 120, az: 90, el: 40 },
    { t: 180, az: 160, el: 10 }, { t: 240, az: 170, el: 0 }], 5);
  eq(ps.length, 1, "one pass");
  near(ps[0].aos, 30, 1e-9, "AOS at the 5 deg crossing");
  near(ps[0].los, 210, 1e-9, "LOS at the 5 deg crossing");
  near(ps[0].maxEl, 40, 1e-9, "max elevation"); near(ps[0].tMax, 120, 1e-9, "time of max");
  // polar projection: north up, east right, zenith centre
  const [cx, cy] = SK.polar(0, 90, 300);
  near(cx, 150, 1e-9, "zenith x"); near(cy, 150, 1e-9, "zenith y");
  const [ex] = SK.polar(90, 0, 300); n++; if (!(ex > 270)) fails.push("east to the right");
  const [, ny] = SK.polar(0, 0, 300); n++; if (!(ny < 30)) fails.push("north up");
}

if (fails.length) { console.log(fails.join("\n")); process.exit(1); }
console.log(`ok ${n}`);
