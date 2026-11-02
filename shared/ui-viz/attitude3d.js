/* ============================================================================
 * C2O pictorial displays — attitude3d.js  (source: shared/ui-viz/attitude3d.js)
 * ============================================================================
 * A deliberately plain 3D picture of the spacecraft's SITUATION: the body
 * built procedurally from the geometry description (geometry.yaml, served at
 * GET /api/geometry; SpaceCDF writes the same shape), shown in LVLH by
 * default (nadir down, velocity to the right, camera fixed in the frame —
 * never auto-following the body), with sun / nadir / velocity arrows, a
 * translucent ghost of the COMMANDED attitude, star-tracker FOV cones with
 * the sun and Earth-limb exclusion check, the solar-array drive angle and
 * eclipse shading. Low-poly, flat-shaded, token colours, no textures.
 *
 * Rules it follows (research report, design rules table):
 *   - numbers never ride on the moving model: every value is in the fixed
 *     readout strip beside the view (Buchner 2025);
 *   - the frame and the quaternion convention are always printed;
 *   - renders only when update() brings new data, the camera is dragged or
 *     the element is resized: no animation loop;
 *   - WebGL missing or lost -> the "vz:webgl-unavailable" event bubbles from
 *     the host element (and opts.onFallback runs) so the page shows the 2D
 *     attitude instruments instead;
 *   - text alternative: role="img" + an aria-label summary kept current, and
 *     a "Values" table.
 *
 *   mount(el, { geometry, t, frame: "lvlh"|"inertial", height, onFallback })
 *     -> { update(model), setGeometry(geo), setFrame(f), destroy() }
 *
 * MODEL. update() takes the attitude model of derive.js deriveAttitude()
 * unchanged, plus three optional fields:
 *   q     {q:[x,y,z,w], valid, verdict, ageS, reason}  estimate, ECI->body
 *   ref   {q:[x,y,z,w], valid}                          commanded, ECI->body
 *   sun   {v:[x,y,z] body, valid, reason}   nadir {v:[x,y,z] body, valid}
 *   driveDeg {v}   errDeg {v, verdict}   errLimits {warn, alarm}   frame
 *   lvlh  {q:[x,y,z,w] ECI->LVLH} | {r:[km], v:[km/s]} ECI   (optional)
 *   illum {sunFraction 0..1, verdict}                        (optional)
 *   wingStatus  bitmask of eps.wing_status 0x0144            (optional)
 * Quaternions are smo_common.attitude's: scalar LAST, ECI -> body
 * (v_b = C(q) v_eci). Without `lvlh`, LVLH is recovered from the commanded
 * quaternion when the spacecraft is commanding LVLH nadir pointing (q_ref
 * then IS the nadir frame), and said so; otherwise the view offers inertial
 * only and gives the reason on the disabled LVLH button.
 * ============================================================================ */

import * as THREE from "./vendor/three/three.module.min.js";
import {
  injectBase, injectCss, translator, fmt, fin, esc, valueHtml, flagHtml, tableHtml,
  segmented, valuesToggle, tokenValue, onThemeChange,
} from "./vizkit.js";

/* ── pure geometry (exported for the unit tests) ───────────────────────── */

/** ECI->body DCM of a scalar-last quaternion (smo_common.attitude.quat_to_dcm). */
export function quatToDcm(q) {
  const [x, y, z, w] = q;
  return [
    [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)],
    [2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)],
    [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)],
  ];
}
export const mul = (A, B) => A.map((r) => [0, 1, 2].map((j) => r[0] * B[0][j] + r[1] * B[1][j] + r[2] * B[2][j]));
export const tr = (A) => [0, 1, 2].map((i) => [A[0][i], A[1][i], A[2][i]]);
export const mv = (A, v) => [0, 1, 2].map((i) => A[i][0] * v[0] + A[i][1] * v[1] + A[i][2] * v[2]);
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (v) => Math.hypot(v[0], v[1], v[2]);
const unit = (v) => { const n = norm(v); return n > 1e-9 ? v.map((c) => c / n) : null; };
/** Angle between two vectors, degrees (atan2 form: exact near 0 and 180). */
export function angleDeg(a, b) {
  const ua = unit(a), ub = unit(b);
  if (!ua || !ub) return null;
  return (Math.atan2(norm(cross(ua, ub)), dot(ua, ub)) * 180) / Math.PI;
}

/** ECI->LVLH DCM from ECI r, v (smo_common.attitude.lvlh_dcm): z nadir,
 *  y = -orbit normal, x completes (~ velocity). */
export function lvlhFromRV(r, v) {
  const z = unit(r.map((c) => -c));
  const y = unit(cross(r, v).map((c) => -c));
  if (!z || !y) return null;
  return [unit(cross(y, z)), y, z];
}
/** Nominal body-from-LVLH (aocs_basic.BODY_FROM_LVLH): -Z nadir, +Y orbit normal. */
export const BODY_FROM_LVLH = [[1, 0, 0], [0, -1, 0], [0, 0, -1]];
/** ECI->LVLH from the commanded quaternion WHILE the commanded frame is LVLH
 *  nadir: C_ref = B . L, so L = B^T . C_ref (B is its own transpose). */
export function lvlhFromNadirRef(qRef) { return mul(BODY_FROM_LVLH, quatToDcm(qRef)); }

/* Scene axes (three.js, y up). LVLH: scene x = velocity (LVLH x), scene y =
 * zenith (-LVLH z), scene z = LVLH y (-orbit normal) — a proper rotation, so
 * the camera on +z looks at the -Y (sun) side with velocity to the right.
 * Inertial: scene x = ECI X, scene y = ECI Z (north up), scene z = -ECI Y. */
export const SCENE_FROM = {
  lvlh: [[1, 0, 0], [0, 0, -1], [0, 1, 0]],
  inertial: [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
};

function quatOk(o) {
  if (!o || !Array.isArray(o.q) || o.q.length !== 4 || o.valid === false) return false;
  const n = Math.hypot(...o.q);
  return Number.isFinite(n) && Math.abs(n - 1) < 0.01;
}
function vecOk(o) { return o && Array.isArray(o.v) && o.v.length === 3 && o.v.every(fin) && norm(o.v) > 1e-6; }

/** Where ECI->LVLH comes from, or why it is unknown. */
export function resolveLvlh(model) {
  const l = model && model.lvlh;
  if (l && Array.isArray(l.q) && quatOk({ q: l.q })) return { L: quatToDcm(l.q), src: "orbit state" };
  if (l && Array.isArray(l.r) && Array.isArray(l.v)) {
    const L = lvlhFromRV(l.r, l.v);
    if (L) return { L, src: "orbit state" };
  }
  if (model && model.frame === "LVLH_NADIR" && quatOk(model.ref)) {
    return { L: lvlhFromNadirRef(model.ref.q), src: "commanded nadir reference" };
  }
  return { L: null, src: "", reason: "LVLH needs the orbit state, or the spacecraft commanding nadir pointing" };
}

/**
 * attitudeScene(model, geo, frame) — everything the picture and the strip
 * show, in scene axes. Pure; no three.js.
 */
export function attitudeScene(model, geo, frame = "lvlh") {
  const out = { ok: false, frame, reason: "", checks: [] };
  if (!model || !quatOk(model.q)) {
    out.reason = (model && model.q && model.q.reason) || "no attitude solution";
    return out;
  }
  const Ceb = quatToDcm(model.q.q);                  // ECI -> body
  const lv = resolveLvlh(model);
  out.lvlhSrc = lv.src;
  out.lvlhReason = lv.reason || "";
  let use = frame;
  if (use === "lvlh" && !lv.L) use = "inertial";
  out.frame = use;
  const Cfe = use === "lvlh" ? lv.L : [[1, 0, 0], [0, 1, 0], [0, 0, 1]];   // ECI -> frame
  const M = SCENE_FROM[use];
  const Rb = mul(M, mul(Cfe, tr(Ceb)));               // scene <- body
  out.Rbody = Rb;
  out.ok = true;
  if (quatOk(model.ref)) out.Rghost = mul(M, mul(Cfe, tr(quatToDcm(model.ref.q))));
  // directions in scene axes
  const sunB = vecOk(model.sun) && model.sun.valid !== false ? unit(model.sun.v) : null;
  out.sunBody = sunB;
  out.sun = sunB ? mv(Rb, sunB) : null;
  let nadirB = vecOk(model.nadir) && model.nadir.valid !== false ? unit(model.nadir.v) : null;
  if (lv.L) {
    const nE = mv(tr(lv.L), [0, 0, 1]);                // nadir in ECI
    const nB = mv(Ceb, nE);
    if (!nadirB) nadirB = nB;
    out.nadir = mv(M, mv(Cfe, nE));
    out.velocity = mv(M, mv(Cfe, mv(tr(lv.L), [1, 0, 0])));
  } else {
    out.nadir = nadirB ? mv(Rb, nadirB) : null;
    out.velocity = null;
  }
  out.nadirBody = nadirB;
  // star trackers: sun inside the exclusion cone blinds the unit (as the
  // simulator models it); the Earth-limb check is a display constraint
  const altKm = model.altKm || 513;
  const earthRadDeg = (Math.asin(6378.137 / (6378.137 + altKm)) * 180) / Math.PI;
  for (const st of (geo && geo.star_trackers) || []) {
    const sunDeg = sunB ? angleDeg(st.boresight, sunB) : null;
    const limbDeg = nadirB ? angleDeg(st.boresight, nadirB) - earthRadDeg : null;
    out.checks.push({
      id: st.id, sunDeg, limbDeg,
      blinded: sunDeg !== null && sunDeg < geo.star_tracker_sun_exclusion_deg,
      earth: limbDeg !== null && limbDeg < geo.star_tracker_earth_exclusion_deg,
    });
  }
  const drive = model.driveDeg && fin(model.driveDeg.v) ? Number(model.driveDeg.v) : null;
  out.driveDeg = drive;
  const ad = geo && geo.array_drive;
  if (ad && drive !== null) {
    const a = (drive * Math.PI) / 180;
    out.wingNormal = ad.normal_at_0deg.map((c, i) => Math.cos(a) * c + Math.sin(a) * ad.normal_at_90deg[i]);
    out.sunArrayDeg = sunB ? angleDeg(out.wingNormal, sunB) : null;
  }
  const pb = (geo && geo.payload && geo.payload.boresight) || [0, 0, -1];
  out.offNadirDeg = nadirB ? angleDeg(pb, nadirB) : null;
  if (out.Rghost) out.errDeg = errAngleDeg(model.ref.q, model.q.q);
  return out;
}
/** Angle between two scalar-last attitudes: 2 atan2(|dq_v|, |dq_w|). */
export function errAngleDeg(a, b) {
  const [ax, ay, az, aw] = a, [bx, by, bz, bw] = b;
  // conj(a) (x) b
  const x = aw * bx - ax * bw - ay * bz + az * by;
  const y = aw * by + ax * bz - ay * bw - az * bx;
  const z = aw * bz - ax * by + ay * bx - az * bw;
  const w = aw * bw + ax * bx + ay * by + az * bz;
  return (2 * Math.atan2(Math.hypot(x, y, z), Math.abs(w)) * 180) / Math.PI;
}

/* Reasons and sources passed to t() as variables.
// i18n-keys (English text is the i18n key)
 */
export const I18N_KEYS = [
  "no attitude solution", "orbit state", "commanded nadir reference",
  "LVLH needs the orbit state, or the spacecraft commanding nadir pointing",
  "LVLH needs the orbit state", "no commanded attitude", "sun sensors not valid (eclipse or off)",
  "WebGL is not available in this browser", "WebGL could not start", "the WebGL context was lost",
  "no data", "not a unit quaternion",
];
void I18N_KEYS;

/* ── view ──────────────────────────────────────────────────────────────── */

const CSS = `
.vz-a3{ display:grid; grid-template-columns:minmax(0,1fr) 248px; gap:0 var(--sp-4,16px); }
.vz-a3 > .vz-bar{ grid-column:1 / -1; }
.vz-a3 .vz-stage{ position:relative; min-height:240px; border:1px solid var(--vz-line); border-radius:var(--radius,3px);
  background:var(--vz-bg); overflow:hidden; touch-action:none; cursor:grab; }
.vz-a3 .vz-stage:active{ cursor:grabbing; }
.vz-a3 .vz-stage canvas{ display:block; width:100%; height:100%; }
.vz-a3 .vz-stage.is-stale{ border-style:dashed; border-color:var(--vz-stale); }
.vz-a3 .vz-stage.is-stale canvas{ opacity:.55; }
.vz-a3 .vz-hud{ position:absolute; left:10px; top:8px; right:10px; display:flex; gap:8px; align-items:baseline;
  pointer-events:none; font-size:var(--fs-label,12px); color:var(--vz-tx2); flex-wrap:wrap; }
.vz-a3 .vz-hud b{ font-weight:600; color:var(--vz-val); }
.vz-a3 .vz-hud .vz-age{ pointer-events:auto; }
.vz-a3 .vz-conv{ position:absolute; left:10px; bottom:6px; font:400 var(--fs-label,12px)/1.3 var(--vz-mono);
  color:var(--vz-tx3); pointer-events:none; }
.vz-a3 .vz-lbls{ position:absolute; inset:0; pointer-events:none; }
.vz-a3 .vz-lbl{ position:absolute; transform:translate(-50%,-50%); font-size:var(--fs-label,12px); white-space:nowrap;
  color:var(--vz-tx2); text-shadow:0 0 3px var(--vz-bg),0 0 3px var(--vz-bg); }
.vz-a3 .vz-lbl.lft{ transform:translate(0,-50%); }
.vz-a3 .vz-lbl.ax{ font-family:var(--vz-mono); color:var(--vz-tx3); }
.vz-a3 .vz-lbl.cmd{ color:var(--vz-accent); }
.vz-a3 .vz-empty{ position:absolute; inset:0; display:grid; place-items:center; text-align:center; padding:24px;
  color:var(--vz-tx2); }
.vz-a3 .vz-empty[hidden]{ display:none; }
.vz-a3 .vz-strip{ display:flex; flex-direction:column; border-top:1px solid var(--vz-line); }
.vz-a3 .vz-row{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:2px 8px; align-items:baseline;
  padding:6px 0; border-bottom:1px solid var(--vz-line); }
.vz-a3 .vz-row > .k{ font-size:var(--fs-label,12px); color:var(--vz-tx3); }
.vz-a3 .vz-row > .v{ text-align:right; }
.vz-a3 .vz-row > .d{ grid-column:1 / -1; font-size:var(--fs-label,12px); color:var(--vz-tx3); }
.vz-a3 .vz-row .vz-flag{ justify-self:end; }
.vz-a3 .vz-raw{ font:400 var(--fs-label,12px)/1.4 var(--vz-mono); color:var(--vz-tx2); white-space:nowrap; }
.vz-a3 .vz-legend{ grid-column:1; display:flex; gap:4px 16px; flex-wrap:wrap; padding-top:6px;
  font-size:var(--fs-label,12px); color:var(--vz-tx3); }
.vz-a3 .vz-legend svg{ width:22px; height:10px; vertical-align:-1px; margin-right:4px; overflow:visible; }
.vz-a3 .vz-legend line{ stroke-width:1.5; }
.vz-a3 .vz-tabhost{ grid-column:1 / -1; }
.vz-a3 .vz-fallback{ grid-column:1 / -1; padding:16px; border:1px dashed var(--vz-line2); border-radius:var(--radius,3px);
  color:var(--vz-tx2); }
@media (max-width: 720px){
  .vz-a3{ grid-template-columns:minmax(0,1fr); }
  .vz-a3 .vz-strip{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:16px; margin-top:8px; }
  .vz-a3 .vz-strip .vz-row:last-child{ grid-column:1 / -1; }
}
`;

const DEG = Math.PI / 180;
/** The commanded-attitude ghost is drawn only beyond this error (deg). */
export const GHOST_MIN_DEG = 1;

function m3ToQuat(R) {
  const m = new THREE.Matrix4().set(
    R[0][0], R[0][1], R[0][2], 0, R[1][0], R[1][1], R[1][2], 0, R[2][0], R[2][1], R[2][2], 0, 0, 0, 0, 1);
  return new THREE.Quaternion().setFromRotationMatrix(m);
}
const V = (a) => new THREE.Vector3(a[0], a[1], a[2]);

function webglAvailable() {
  try {
    const c = globalThis.document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch (e) { return false; }
}

export function mount(el, opts = {}) {
  injectBase();
  injectCss("vz-a3-css", CSS);
  const t = translator(opts);
  const d = globalThis.document;
  let geo = opts.geometry || null;
  let frame = opts.frame === "inertial" ? "inertial" : "lvlh";
  let model = null, sc = null;
  let destroyed = false;

  const root = d.createElement("div");
  root.className = "vz vz-a3";
  el.appendChild(root);

  /* header bar: frame toggle, reset, values */
  const bar = d.createElement("div");
  bar.className = "vz-bar";
  const seg = segmented(t("Reference frame"), [
    { value: "lvlh", label: t("LVLH") }, { value: "inertial", label: t("Inertial") }], frame,
  (v) => { frame = v; draw(); });
  const cap = d.createElement("span");
  cap.className = "vz-cap";
  const sp = d.createElement("span");
  sp.className = "vz-sp";
  const reset = d.createElement("button");
  reset.type = "button";
  reset.className = "vz-btn";
  reset.textContent = t("Reset view");
  const tabHost = d.createElement("div");
  tabHost.className = "vz-tabhost";
  const vt = valuesToggle(t, tabHost, `vz-a3-tab-${Math.random().toString(36).slice(2, 8)}`);
  vt.btn.addEventListener("click", () => draw());
  bar.append(seg.el, cap, sp, reset, vt.btn);
  root.appendChild(bar);

  if (!webglAvailable()) return fallback("WebGL is not available in this browser");

  /* stage */
  const stage = d.createElement("div");
  stage.className = "vz-stage";
  stage.setAttribute("role", "img");
  stage.tabIndex = 0;
  const hud = d.createElement("div");
  hud.className = "vz-hud";
  const conv = d.createElement("div");
  conv.className = "vz-conv";
  const lbls = d.createElement("div");
  lbls.className = "vz-lbls";
  lbls.setAttribute("aria-hidden", "true");
  const empty = d.createElement("div");
  empty.className = "vz-empty";
  empty.hidden = true;
  const strip = d.createElement("div");
  strip.className = "vz-strip";
  strip.setAttribute("aria-live", "off");
  const legend = d.createElement("div");
  legend.className = "vz-legend";
  root.append(stage, strip, legend, tabHost);

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: !!opts.preserveDrawingBuffer });
  } catch (e) {
    stage.remove(); strip.remove(); legend.remove();
    return fallback("WebGL could not start");
  }
  renderer.setPixelRatio(Math.min(2, globalThis.devicePixelRatio || 1));
  stage.append(renderer.domElement, lbls, hud, conv, empty);
  renderer.domElement.setAttribute("aria-hidden", "true");
  renderer.domElement.addEventListener("webglcontextlost", (e) => {
    e.preventDefault();
    signalFallback("the WebGL context was lost");
  });

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, 1, 0.05, 200);
  const CAM0 = { az: 34, el: 14, dist: 2.7 };
  const cam = { ...CAM0 };
  const ambient = new THREE.AmbientLight(0xffffff, 0.55);
  const sunLight = new THREE.DirectionalLight(0xffffff, 1.6);
  scene.add(ambient, sunLight, sunLight.target);

  const world = new THREE.Group();          // frame-fixed things
  const body = new THREE.Group();           // spacecraft (estimate)
  const ghost = new THREE.Group();          // commanded attitude
  const earth = new THREE.Group();
  scene.add(world, earth, body, ghost);

  const mats = {};
  const disposables = [];
  const track = (o) => { disposables.push(o); return o; };
  function colours() {
    const c = (n) => new THREE.Color(tokenValue(root, n) || tokenValue(root, "--tx3") || "gray");
    return {
      bg: c("--vz-bg"), bus: c("--vz-fill"), cell: c("--vz-line2"), edge: c("--vz-line2"), tx2: c("--vz-tx2"),
      tx3: c("--vz-tx3"), val: c("--vz-val"), accent: c("--vz-accent"), warn: c("--vz-warn"), alarm: c("--vz-alarm"),
      earth: c("--vz-s2"), earthLine: c("--vz-line2"),
    };
  }
  let C = colours();

  /* materials (recoloured on theme change) */
  function makeMats() {
    mats.bus = track(new THREE.MeshLambertMaterial({ color: C.bus }));
    mats.cell = track(new THREE.MeshLambertMaterial({ color: C.cell, side: THREE.DoubleSide }));
    mats.dark = track(new THREE.MeshLambertMaterial({ color: C.cell }));
    mats.edge = track(new THREE.LineBasicMaterial({ color: C.edge }));
    mats.ghostEdge = track(new THREE.LineBasicMaterial({ color: C.accent, transparent: true, opacity: 0.95 }));
    mats.ghostFace = track(new THREE.MeshBasicMaterial({ color: C.accent, transparent: true, opacity: 0.07,
      depthWrite: false, side: THREE.DoubleSide }));
    mats.arrow = track(new THREE.LineBasicMaterial({ color: C.tx2 }));
    mats.sun = track(new THREE.LineBasicMaterial({ color: C.val }));
    mats.sunDisc = track(new THREE.MeshBasicMaterial({ color: C.val }));
    mats.dash = track(new THREE.LineDashedMaterial({ color: C.tx2, dashSize: 0.06, gapSize: 0.05 }));
    mats.axis = track(new THREE.LineBasicMaterial({ color: C.tx3 }));
    mats.cone = track(new THREE.MeshBasicMaterial({ color: C.tx3, transparent: true, opacity: 0.12,
      depthWrite: false, side: THREE.DoubleSide }));
    mats.coneEdge = track(new THREE.LineBasicMaterial({ color: C.tx3, transparent: true, opacity: 0.6 }));
    mats.fov = track(new THREE.LineDashedMaterial({ color: C.tx3, dashSize: 0.04, gapSize: 0.04, transparent: true, opacity: 0.7 }));
    mats.earth = track(new THREE.MeshLambertMaterial({ color: C.earth }));
    mats.earthLine = track(new THREE.LineBasicMaterial({ color: C.earthLine }));
    mats.arrowHead = track(new THREE.MeshBasicMaterial({ color: C.tx2 }));
  }
  function recolour() {
    C = colours();
    const set = (k, c) => mats[k] && mats[k].color.copy(c);
    set("bus", C.bus); set("cell", C.cell); set("dark", C.cell); set("edge", C.edge);
    set("ghostEdge", C.accent); set("ghostFace", C.accent); set("arrow", C.tx2); set("sun", C.val);
    set("sunDisc", C.val); set("dash", C.tx2); set("axis", C.tx3); set("fov", C.tx3);
    set("earth", C.earth); set("earthLine", C.earthLine); set("arrowHead", C.tx2);
    draw();
  }
  makeMats();

  /* ── procedural spacecraft ── */
  const stParts = [];          // [{id, cone, edge}]
  let wingPivots = [];         // [{group, face, bit}]
  const ghostWings = [];
  function boxWithEdges(size, mat, edgeMat) {
    const g = track(new THREE.BoxGeometry(size[0], size[1], size[2]));
    const grp = new THREE.Group();
    if (mat) grp.add(new THREE.Mesh(g, mat));
    grp.add(new THREE.LineSegments(track(new THREE.EdgesGeometry(g)), edgeMat));
    return grp;
  }
  /* body axes in scene: geometry is built in BODY axes directly (the
   * body group carries the scene<-body rotation). */
  function buildSpacecraft(target, isGhost) {
    while (target.children.length) target.remove(target.children[0]);
    if (!geo) return;
    const [sx, sy, sz] = geo.bus.size_m;
    const face = isGhost ? mats.ghostFace : mats.bus;
    const edge = isGhost ? mats.ghostEdge : mats.edge;
    target.add(boxWithEdges([sx, sy, sz], face, edge));
    const half = { px: [sx / 2, 0, 0], mx: [-sx / 2, 0, 0], py: [0, sy / 2, 0], my: [0, -sy / 2, 0], pz: [0, 0, sz / 2], mz: [0, 0, -sz / 2] };
    if (!isGhost) {
      // body-mounted cells: thin dark plates on the faces that carry cells
      for (const p of geo.body_panels || []) {
        if (!(p.cell_area_m2 > 0)) continue;
        const n = p.normal;
        const dims = [sx, sy, sz].map((s, i) => (n[i] !== 0 ? 0.004 : s * 0.82));
        const m = new THREE.Mesh(track(new THREE.BoxGeometry(...dims)), mats.cell);
        m.position.set(...half[p.face].map((c, i) => c + n[i] * 0.002));
        target.add(m);
      }
      // imager aperture + FOV (dashed edges)
      if (geo.payload) {
        const ap = new THREE.Mesh(track(new THREE.CylinderGeometry(0.035, 0.035, 0.02, 20)), mats.dark);
        const pb = V(geo.payload.boresight);
        ap.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), pb);
        ap.position.copy(V(geo.payload.position_m)).addScaledVector(pb, 0.008);
        target.add(ap);
        const L = 0.55, rr = L * Math.tan((geo.payload.fov_deg / 2) * DEG);
        const o = V(geo.payload.position_m);
        const side = new THREE.Vector3(0, 1, 0).cross(pb).normalize();
        if (side.lengthSq() < 0.5) side.set(1, 0, 0);
        const pts = [o, o.clone().addScaledVector(pb, L).addScaledVector(side, rr),
          o, o.clone().addScaledVector(pb, L).addScaledVector(side, -rr)];
        const fl = new THREE.LineSegments(track(new THREE.BufferGeometry().setFromPoints(pts)), mats.fov);
        fl.computeLineDistances();
        target.add(fl);
      }
      // star trackers: small barrels + FOV cones
      stParts.length = 0;
      for (const st of geo.star_trackers || []) {
        const b = V(st.boresight);
        const barrel = new THREE.Mesh(track(new THREE.CylinderGeometry(0.022, 0.022, 0.05, 16)), mats.dark);
        barrel.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b);
        barrel.position.copy(V(st.position_m)).addScaledVector(b, 0.02);
        target.add(barrel);
        const L = 0.5, r = L * Math.tan((st.fov_deg / 2) * DEG);
        const cg = track(new THREE.ConeGeometry(r, L, 24, 1, true));
        cg.translate(0, -L / 2, 0);
        cg.rotateX(Math.PI);                  // apex at origin, opening along +y
        const cmat = mats.cone.clone(); track(cmat);
        const emat = mats.coneEdge.clone(); track(emat);
        const cone = new THREE.Mesh(cg, cmat);
        const ring = new THREE.LineLoop(track(new THREE.BufferGeometry().setFromPoints(
          Array.from({ length: 32 }, (_, k) => new THREE.Vector3(r * Math.cos(k / 32 * 2 * Math.PI), L, r * Math.sin(k / 32 * 2 * Math.PI))))), emat);
        const cg2 = new THREE.Group();
        cg2.add(cone, ring);
        cg2.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b);
        cg2.position.copy(V(st.position_m)).addScaledVector(b, 0.045);
        target.add(cg2);
        stParts.push({ id: st.id, cmat, emat });
      }
      // antennas
      for (const a of geo.antennas || []) {
        const bs = V(a.boresight);
        if (a.kind === "patch") {
          const m = new THREE.Mesh(track(new THREE.BoxGeometry(0.05, 0.05, 0.006)), mats.dark);
          m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), bs);
          m.position.copy(V(a.position_m)).addScaledVector(bs, 0.003);
          target.add(m);
        } else {
          const p0 = V(a.position_m), p1 = p0.clone().addScaledVector(bs, a.length_m || 0.17);
          target.add(new THREE.Line(track(new THREE.BufferGeometry().setFromPoints([p0, p1])), mats.edge));
        }
      }
      // thrusters: nozzle cone opening opposite the thrust axis
      for (const th of geo.thrusters || []) {
        const ax = V(th.thrust_axis);
        const g = track(new THREE.ConeGeometry(0.02, 0.04, 12, 1, true));
        const m = new THREE.Mesh(g, mats.dark);
        m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), ax);
        m.position.copy(V(th.position_m)).addScaledVector(ax, -0.02);
        target.add(m);
      }
    }
    // wings: pivot on the mounting face, rotated about the drive axis
    const pivots = [];
    for (const w of geo.wings || []) {
      const out = V(w.mount_axis);
      const pivot = new THREE.Group();
      pivot.position.set(...half[w.face]);
      const [len, wid] = w.panel_size_m;
      const span = len * w.panels;
      const wingGrp = new THREE.Group();
      for (let k = 0; k < w.panels; k++) {
        const pg = boxWithEdges([0.006, len - 0.006, wid], isGhost ? mats.ghostFace : mats.cell, edge);
        pg.position.set(0, (0.03 + len * k + len / 2) * Math.sign(out.y || 1), 0);
        wingGrp.add(pg);
      }
      // yoke
      const yk = [V([0, 0, 0]), V([0, 0.03 * Math.sign(out.y || 1), 0])];
      wingGrp.add(new THREE.Line(track(new THREE.BufferGeometry().setFromPoints(yk)), edge));
      pivot.add(wingGrp);
      // stowed: folded flat against the face (drawn as one plate on the face)
      const stowed = boxWithEdges([0.006 + 0.004, 0.004, wid], isGhost ? mats.ghostFace : mats.cell, edge);
      stowed.scale.set(sx / 0.01, 1, 1);
      stowed.visible = false;
      pivot.add(stowed);
      target.add(pivot);
      pivots.push({ pivot, deployed: wingGrp, stowed, bit: w.deployed_bit, span });
    }
    if (isGhost) { ghostWings.length = 0; ghostWings.push(...pivots); } else wingPivots = pivots;
  }

  /* frame-fixed arrows */
  const arrows = {};
  function arrowLine(mat, dashed) {
    const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3(1, 0, 0)]);
    track(g);
    const l = new THREE.Line(g, dashed ? mats.dash : mat);
    const head = new THREE.Mesh(track(new THREE.ConeGeometry(0.018, 0.06, 12)), dashed ? mats.arrowHead : new THREE.MeshBasicMaterial({ color: mat.color }));
    const grp = new THREE.Group();
    grp.add(l, head);
    world.add(grp);
    return { grp, line: l, head };
  }
  function setArrow(a, dir, len, from = 0.0) {
    if (!dir) { a.grp.visible = false; return; }
    const u = V(dir).normalize();
    const p0 = u.clone().multiplyScalar(from), p1 = u.clone().multiplyScalar(len);
    a.line.geometry.setFromPoints([p0, p1]);
    a.line.computeLineDistances();
    a.head.position.copy(p1);
    a.head.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), u);
    a.grp.visible = true;
  }
  arrows.sun = arrowLine(mats.sun, false);
  arrows.sun.head.visible = false;      // the sun disc is the marker
  arrows.sun.head.material = mats.sunDisc;
  arrows.nadir = arrowLine(mats.arrow, true);
  arrows.vel = arrowLine(mats.arrow, false);
  const sunDisc = new THREE.Mesh(track(new THREE.SphereGeometry(0.04, 16, 12)), mats.sunDisc);
  world.add(sunDisc);

  /* body axis ticks (+X +Y +Z) */
  const axisLines = new THREE.LineSegments(track(new THREE.BufferGeometry()), mats.axis);
  body.add(axisLines);

  /* Earth: low-poly sphere below along nadir */
  const R_E = 7.5, ALT = 1.35;
  const earthMesh = new THREE.Mesh(track(new THREE.SphereGeometry(R_E, 72, 48)), mats.earth);
  earth.add(earthMesh);
  // the horizon as the spacecraft sees it: the tangent circle, cos(th) = R / (R + h)
  const cosH = R_E / (R_E + ALT), rH = R_E * Math.sqrt(1 - cosH * cosH);
  const limb = new THREE.LineLoop(track(new THREE.BufferGeometry().setFromPoints(
    Array.from({ length: 128 }, (_, k) => new THREE.Vector3(rH * Math.cos(k / 128 * 2 * Math.PI), R_E * cosH, rH * Math.sin(k / 128 * 2 * Math.PI))))), mats.earthLine);
  earth.add(limb);

  function rebuild() {
    buildSpacecraft(body, false);
    buildSpacecraft(ghost, true);
    body.add(axisLines);
    if (geo) {
      const [sx, sy, sz] = geo.bus.size_m;
      const tip = (i, s) => { const a = [0, 0, 0]; a[i] = s; return a; };
      const ext = [sx / 2 + 0.16, sy / 2 + 0.16, sz / 2 + 0.16];
      axisLines.geometry.setFromPoints([0, 1, 2].flatMap((i) => [V(tip(i, [sx, sy, sz][i] / 2)), V(tip(i, ext[i]))]));
    }
  }

  /* ── labels (HTML, projected) ── */
  const labelEls = new Map();
  function label(key, text, cls = "") {
    let e = labelEls.get(key);
    if (!e) { e = d.createElement("span"); e.className = "vz-lbl " + cls; lbls.appendChild(e); labelEls.set(key, e); }
    if (e.textContent !== text) e.textContent = text;
    return e;
  }
  function placeLabel(key, text, pos3, cls, dx = 0) {
    const e = label(key, text, cls);
    if (!pos3) { e.style.display = "none"; return; }
    const p = pos3.clone().project(camera);
    if (p.z > 1) { e.style.display = "none"; return; }
    const w = stage.clientWidth, h = stage.clientHeight;
    const x = (p.x + 1) / 2 * w, y = (1 - p.y) / 2 * h;
    if (x < 8 || x > w - 8 || y < 24 || y > h - 18) { e.style.display = "none"; return; }
    e.style.display = "";
    e.style.left = `${(x + dx).toFixed(0)}px`;
    e.style.top = `${y.toFixed(0)}px`;
  }

  /* ── camera ── */
  function placeCamera() {
    const a = cam.az * DEG, e = cam.el * DEG;
    // narrow stages: back off so the arrows stay in the horizontal field
    const dist = cam.dist * Math.max(1, 1.7 / (camera.aspect || 1.7));
    camera.position.set(dist * Math.cos(e) * Math.sin(a), dist * Math.sin(e), dist * Math.cos(e) * Math.cos(a));
    camera.lookAt(0, -0.12, 0);
  }
  let drag = null;
  const onDown = (e) => { drag = { x: e.clientX, y: e.clientY, az: cam.az, el: cam.el }; stage.setPointerCapture?.(e.pointerId); };
  const onMove = (e) => {
    if (!drag) return;
    cam.az = drag.az - (e.clientX - drag.x) * 0.4;
    cam.el = Math.max(-80, Math.min(80, drag.el + (e.clientY - drag.y) * 0.3));
    render();
  };
  const onUp = () => { drag = null; };
  const onWheel = (e) => { e.preventDefault(); cam.dist = Math.max(2.2, Math.min(9, cam.dist * (e.deltaY > 0 ? 1.08 : 0.93))); render(); };
  const onKey = (e) => {
    const k = { ArrowLeft: [-10, 0], ArrowRight: [10, 0], ArrowUp: [0, 8], ArrowDown: [0, -8] }[e.key];
    if (!k) return;
    e.preventDefault();
    cam.az += k[0]; cam.el = Math.max(-80, Math.min(80, cam.el + k[1]));
    render();
  };
  stage.addEventListener("pointerdown", onDown);
  stage.addEventListener("pointermove", onMove);
  stage.addEventListener("pointerup", onUp);
  stage.addEventListener("pointercancel", onUp);
  stage.addEventListener("wheel", onWheel, { passive: false });
  stage.addEventListener("keydown", onKey);
  reset.addEventListener("click", () => { Object.assign(cam, CAM0); render(); });

  /* ── size ── */
  function size() {
    const w = Math.max(200, stage.clientWidth);
    const h = opts.height || Math.round(Math.max(260, Math.min(440, w * 0.5)));
    stage.style.height = `${h}px`;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  let ro = null;
  try { ro = new ResizeObserver(() => { size(); render(); }); ro.observe(stage); } catch (e) { /* static size */ }
  const offTheme = onThemeChange(() => recolour());

  /* ── render (only on demand) ── */
  function render() {
    if (destroyed) return;
    placeCamera();
    renderer.setClearColor(C.bg, 1);
    renderer.render(scene, camera);
    // labels: frame arrows and body axes
    const L = (k) => (sc && sc[k] ? V(sc[k]).normalize() : null);
    placeLabel("sun", t("Sun"), L("sun") && L("sun").multiplyScalar(0.92), "lft", 12);
    placeLabel("nadir", t("Nadir"), L("nadir") && L("nadir").multiplyScalar(0.98).add(new THREE.Vector3(0.14, 0, 0)));
    placeLabel("vel", t("Velocity"), L("velocity") && L("velocity").multiplyScalar(1.0));
    if (geo && sc && sc.ok) {
      const ext = geo.bus.size_m.map((s) => s / 2 + 0.22);
      ["+X", "+Y", "+Z"].forEach((n, i) => {
        const p = [0, 0, 0]; p[i] = ext[i];
        placeLabel("ax" + i, n, V(p).applyQuaternion(body.quaternion), "ax");
      });
      if (ghost.visible) {
        const g = V([0, 0, geo.bus.size_m[2] / 2 + 0.12]).applyQuaternion(ghost.quaternion);
        placeLabel("cmd", t("Commanded"), g, "cmd");
      } else placeLabel("cmd", "", null);
    } else {
      ["ax0", "ax1", "ax2", "cmd"].forEach((k) => placeLabel(k, "", null));
    }
  }

  /* ── update ── */
  function relabel() {
    seg.el.setAttribute("aria-label", t("Reference frame"));
    seg.el.querySelector('[data-value="lvlh"]').textContent = t("LVLH");
    seg.el.querySelector('[data-value="inertial"]').textContent = t("Inertial");
    reset.textContent = t("Reset view");
    vt.btn.textContent = t("Values");
  }
  function draw() {
    if (destroyed) return;
    relabel();
    sc = attitudeScene(model, geo, frame);
    const lvAvail = !!(model && resolveLvlh(model).L);
    seg.set(sc.frame === "lvlh" || !model ? frame : "inertial",
      lvAvail || !model ? {} : { lvlh: t(sc.lvlhReason || "LVLH needs the orbit state") });
    const verdict = model && model.q ? model.q.verdict : "nodata";
    stage.classList.toggle("is-stale", verdict === "stale");

    // no data
    empty.hidden = sc.ok || !geo;
    if (!geo) { empty.hidden = false; empty.textContent = t("Spacecraft geometry not loaded"); }
    else if (!sc.ok) empty.textContent = sc.reason === "no attitude solution" ? t("No attitude solution")
      : t("No attitude solution — {{reason}}", { reason: t(sc.reason) });
    body.visible = !!(sc.ok && geo);
    // the commanded ghost appears only when it is visibly apart: an outline
    // permanently hugging the body would be colour at rest
    ghost.visible = !!(sc.ok && geo && sc.Rghost && sc.errDeg >= GHOST_MIN_DEG);
    if (sc.ok) {
      body.quaternion.copy(m3ToQuat(sc.Rbody));
      if (sc.Rghost) ghost.quaternion.copy(m3ToQuat(sc.Rghost));
    }
    // wings: deployment + drive angle
    const bits = model && fin(model.wingStatus) ? Number(model.wingStatus) : null;
    const ad = geo && geo.array_drive;
    for (const set of [wingPivots, ghostWings]) {
      for (const w of set) {
        const dep = bits === null ? true : !!(bits & (1 << w.bit));
        w.deployed.visible = dep;
        w.stowed.visible = !dep;
        if (ad && sc.driveDeg !== null) {
          // rotate the cell normal from +X(0 deg) toward normal_at_90deg
          const n0 = V(ad.normal_at_0deg), n9 = V(ad.normal_at_90deg);
          const axis = new THREE.Vector3().crossVectors(n0, n9).normalize();
          w.pivot.quaternion.setFromAxisAngle(axis, sc.driveDeg * DEG);
        }
      }
    }
    // star tracker cones: status colour only when a check fails
    for (const p of stParts) {
      const ck = sc.checks.find((c) => c.id === p.id);
      const col = ck && ck.blinded ? C.alarm : ck && ck.earth ? C.warn : C.tx3;
      p.cmat.color.copy(col); p.emat.color.copy(col);
      p.cmat.opacity = ck && (ck.blinded || ck.earth) ? 0.28 : 0.08;
      p.emat.opacity = ck && (ck.blinded || ck.earth) ? 1 : 0.45;
    }
    // frame-fixed arrows; Earth along nadir
    setArrow(arrows.sun, sc.ok ? sc.sun : null, 0.85, 0.0);
    sunDisc.visible = !!(sc.ok && sc.sun);
    if (sc.sun) sunDisc.position.copy(V(sc.sun).normalize().multiplyScalar(0.92));
    setArrow(arrows.nadir, sc.ok ? sc.nadir : null, 0.95, 0.3);
    setArrow(arrows.vel, sc.ok ? sc.velocity : null, 0.85, 0.3);
    earth.visible = !!(sc.ok && sc.nadir);
    if (sc.nadir) {
      const n = V(sc.nadir).normalize();
      earth.position.copy(n.clone().multiplyScalar(R_E + ALT));
      limb.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), n.clone().negate());
    }
    // illumination: sunlight scaled by the illuminated fraction of the disc
    const f = model && model.illum && fin(model.illum.sunFraction) ? Number(model.illum.sunFraction)
      : (sc.sun ? 1 : 0);
    sunLight.intensity = 1.5 * f;
    ambient.intensity = 0.95;
    if (sc.sun) sunLight.position.copy(V(sc.sun).normalize().multiplyScalar(10));
    else sunLight.intensity = 0;

    renderHud(f);
    renderStrip(f);
    size();
    render();
  }

  function frameText() {
    if (!sc || !sc.ok) return frame === "lvlh" ? t("LVLH") : t("Inertial (ECI)");
    return sc.frame === "lvlh" ? t("LVLH · nadir down, velocity right") : t("Inertial (ECI) · +Z north up");
  }
  function illumText(f) {
    if (!(model && model.illum && fin(model.illum.sunFraction))) return sc && sc.sun ? t("Sunlit") : t("Sun not measured");
    return f >= 0.999 ? t("Sunlit") : f <= 0.001 ? t("Eclipse") : t("Penumbra {{pct}} %", { pct: fmt(f * 100, 0) });
  }
  function renderHud(f) {
    const age = model && model.q && model.q.verdict === "stale" ? valueHtml(null, { text: "", verdict: "stale", ageS: model.q.ageS, t }) : "";
    hud.innerHTML = `<b>${esc(frameText())}</b>` +
      (sc && sc.ok && sc.frame === "lvlh" && sc.lvlhSrc ? `<span>${esc(t("from {{src}}", { src: t(sc.lvlhSrc) }))}</span>` : "") +
      `<span>· ${esc(illumText(f))}</span>${age}`;
    conv.textContent = t("q = [x y z w], scalar last · ECI→body");
    stage.setAttribute("aria-label", summary(f));
  }
  function stState(ck) {
    if (!ck || ck.sunDeg === null) return { level: "", text: t("sun not measured") };
    if (ck.blinded) return { level: "alarm", text: t("Sun in exclusion") };
    if (ck.earth) return { level: "caution", text: t("Earth limb near") };
    return { level: "", text: t("Clear") };
  }
  function summary(f) {
    if (!geo) return t("Spacecraft attitude view: geometry not loaded.");
    if (!sc || !sc.ok) return t("Spacecraft attitude view: no attitude solution.");
    const parts = [t("Spacecraft attitude in {{frame}}.", { frame: frameText() })];
    if (fin(sc.errDeg)) parts.push(t("Pointing error {{v}} degrees from the commanded attitude.", { v: fmt(sc.errDeg, 2) }));
    if (fin(sc.sunArrayDeg)) parts.push(t("Sun {{v}} degrees from the array normal.", { v: fmt(sc.sunArrayDeg, 0) }));
    for (const ck of sc.checks) parts.push(`${ck.id.toUpperCase()}: ${stState(ck).text}.`);
    parts.push(illumText(f) + ".");
    return parts.join(" ");
  }
  function errLevel(v) {
    const L = (model && model.errLimits) || {};
    if (!fin(v)) return "";
    if (fin(L.alarm) && v >= L.alarm) return "alarm";
    if (fin(L.warn) && v >= L.warn) return "caution";
    return "";
  }
  function renderStrip(f) {
    const v = model && model.q ? model.q.verdict : "nodata";
    const ageS = model && model.q ? model.q.ageS : null;
    const ok = sc && sc.ok;
    const row = (k, html, dsc) => `<div class="vz-row"><span class="k">${esc(k)}</span><span class="v">${html}</span>` +
      (dsc ? `<span class="d">${dsc}</span>` : "") + `</div>`;
    const val = (x, digits, units, extra = {}) => valueHtml(ok ? x : null, { digits, units, verdict: ok ? v : "nodata", ageS, t, ...extra });
    const sunWhy = model && model.sun && model.sun.reason ? model.sun.reason : "sun not measured";
    const rows = [];
    rows.push(row(t("Pointing error"), val(sc && sc.errDeg, 2, "°", { level: errLevel(sc && sc.errDeg),
      reason: ok && !sc.Rghost ? "no commanded attitude" : undefined }), esc(t("estimate vs commanded"))));
    rows.push(row(t("Imager off nadir"), val(sc && sc.offNadirDeg, 1, "°")));
    rows.push(row(t("Sun to array normal"), val(sc && sc.sunArrayDeg, 0, "°"),
      ok && !(sc && sc.sunBody) ? esc(t(sunWhy)) : ""));
    rows.push(row(t("Array drive angle"), valueHtml(sc ? sc.driveDeg : null, { digits: 1, units: "°",
      verdict: model && model.driveDeg ? model.driveDeg.verdict : "nodata", ageS: model && model.driveDeg ? model.driveDeg.ageS : null, t })));
    rows.push(row(t("Illumination"), `<span class="vz-v" style="font-size:var(--fs-body,13px)">${esc(illumText(f))}</span>`));
    for (const ck of (sc && sc.checks) || []) {
      const s = stState(ck);
      const det = ck.sunDeg === null ? "" : esc(t("sun {{s}}° (limit {{l}}°)", { s: fmt(ck.sunDeg, 0), l: fmt(geo.star_tracker_sun_exclusion_deg, 0) })) +
        (ck.limbDeg === null ? "" : " · " + esc(t("limb {{e}}°", { e: fmt(ck.limbDeg, 0) })));
      rows.push(row(t("Star tracker {{n}}", { n: ck.id.replace(/\D/g, "") || ck.id }), ok ? flagHtml(s.level, s.text) : valueHtml(null, { t }), ok ? det : ""));
    }
    const q = ok ? model.q.q : null;
    rows.push(row(t("q estimate"), q ? "" : valueHtml(null, { t }), q ? `<span class="vz-raw">${q.map((c) => (c >= 0 ? " " : "") + fmt(c, 4)).join(" ")}</span>` : ""));
    strip.innerHTML = rows.join("");
    // legend (static meaning of line styles)
    legend.innerHTML =
      `<span><svg viewBox="0 0 22 10" aria-hidden="true"><line x1="1" y1="5" x2="21" y2="5" stroke="var(--vz-val)"/><circle cx="20" cy="5" r="3" fill="var(--vz-val)"/></svg>${esc(t("Sun"))}</span>` +
      `<span><svg viewBox="0 0 22 10" aria-hidden="true"><line x1="1" y1="5" x2="21" y2="5" stroke="var(--vz-tx2)" stroke-dasharray="3 2"/></svg>${esc(t("Nadir"))}</span>` +
      `<span><svg viewBox="0 0 22 10" aria-hidden="true"><line x1="1" y1="5" x2="21" y2="5" stroke="var(--vz-tx2)"/></svg>${esc(t("Velocity"))}</span>` +
      `<span><svg viewBox="0 0 22 10" aria-hidden="true"><rect x="2" y="1" width="18" height="8" fill="none" stroke="var(--vz-accent)"/></svg>${esc(t("Commanded attitude (drawn when over 1° away)"))}</span>` +
      `<span><svg viewBox="0 0 22 10" aria-hidden="true"><path d="M1 5L21 1V9Z" fill="var(--vz-tx3)" fill-opacity=".35" stroke="var(--vz-tx3)"/></svg>${esc(t("Star tracker field of view"))}</span>`;
    // values table
    if (vt.isOpen()) {
      const r = (label, html, src) => ({ label, html, src });
      tabHost.innerHTML = tableHtml(t("Attitude geometry values"), [
        r(t("Reference frame"), esc(frameText()), sc && sc.frame === "lvlh" && sc.lvlhSrc ? t("LVLH from {{src}}", { src: t(sc.lvlhSrc) }) : ""),
        r(t("Pointing error"), val(sc && sc.errDeg, 3, "°"), t("ground: 2·atan2(|δq_v|, |δq_w|)")),
        r(t("Imager off nadir"), val(sc && sc.offNadirDeg, 2, "°"), "TM 0x02B0–B2"),
        r(t("Sun to array normal"), val(sc && sc.sunArrayDeg, 1, "°"), "TM 0x0245–47, 0x0133"),
        r(t("Array drive angle"), valueHtml(sc ? sc.driveDeg : null, { digits: 1, units: "°", t }), "TM 0x0133"),
        ...((sc && sc.checks) || []).map((ck) => r(t("Star tracker {{n}} sun angle", { n: ck.id.replace(/\D/g, "") }),
          val(ck.sunDeg, 1, "°"), t("exclusion {{l}}°", { l: fmt(geo.star_tracker_sun_exclusion_deg, 0) }))),
        ...((sc && sc.checks) || []).map((ck) => r(t("Star tracker {{n}} Earth-limb clearance", { n: ck.id.replace(/\D/g, "") }),
          val(ck.limbDeg, 1, "°"), t("display limit {{l}}°", { l: fmt(geo.star_tracker_earth_exclusion_deg, 0) }))),
        r(t("q estimate [x y z w]"), q ? esc(q.map((c) => fmt(c, 5)).join("  ")) : valueHtml(null, { t }), "TM 0x02A0–A3"),
        r(t("q commanded [x y z w]"), ok && model.ref && model.ref.q ? esc(model.ref.q.map((c) => fmt(c, 5)).join("  ")) : valueHtml(null, { t }), "TM 0x02AB–AE"),
      ], t);
    }
  }

  /* ── fallback ── */
  function signalFallback(reason) {
    try { el.dispatchEvent(new CustomEvent("vz:webgl-unavailable", { bubbles: true, detail: { reason } })); } catch (e) { /* no DOM events */ }
    if (typeof opts.onFallback === "function") opts.onFallback(reason);
  }
  function fallback(reason) {
    const fb = d.createElement("div");
    fb.className = "vz-fallback";
    fb.setAttribute("role", "note");
    fb.textContent = t("3D view unavailable: {{reason}}. The 2D attitude instruments show the same attitude.", { reason: t(reason) });
    seg.el.hidden = true; reset.hidden = true; vt.btn.hidden = true;
    root.appendChild(fb);
    queueMicrotask(() => signalFallback(reason));
    return {
      update() {}, setGeometry() {}, setFrame() {}, fallback: true,
      destroy() { destroyed = true; root.remove(); },
    };
  }

  rebuild();
  size();
  draw();

  return {
    update(m) { model = m || null; draw(); },
    setGeometry(g) { geo = g || null; rebuild(); draw(); },
    setFrame(f) { frame = f === "inertial" ? "inertial" : "lvlh"; draw(); },
    render,
    destroy() {
      destroyed = true;
      offTheme();
      if (ro) ro.disconnect();
      for (const o of disposables) { try { o.dispose(); } catch (e) { /* already gone */ } }
      renderer.dispose();
      root.remove();
    },
  };
}

/** Fetch helper for hosts: the geometry served by the MCS (or null). */
export async function fetchGeometry(url = "/api/geometry") {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    const j = await r.json();
    return j.geometry || null;
  } catch (e) { return null; }
}
