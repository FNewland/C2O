/* ============================================================================
 * C2O pictorial displays — stack3d.js  (source: shared/ui-viz/stack3d.js)
 * ============================================================================
 * The CubeSat stack in 3D: the CDS envelope as a wireframe, one box per placed
 * unit coloured by subsystem (category tokens), the stowed or deployed
 * configuration (wings, antenna elements), an exploded view along the stack
 * axis, the optical keep-out cones, the centre of gravity with the CDS CoG box,
 * and the body axes with the frame convention printed.
 *
 * Input is a c2o.geometry/1 document (sim geometry.yaml schema) with the
 * stack-builder extension (`internal`, `mass_properties`, `frame`), which is
 * what SpaceCDF exports (GET /api/studies/{id}/stack/geometry) and what the
 * MCS can serve for the same spacecraft. Body frame (ruling Q4): +X ~ velocity,
 * +Y = orbit normal, +Z = zenith, -Z = nadir, origin at the envelope centre;
 * the scene shows +Z (zenith) up.
 *
 *   mount(el, { t, geometry, mode: "stowed"|"deployed", exploded: 0..1,
 *               cogBox_m: [hx, hy, hz], height, onSelect(id), onFallback,
 *               preserveDrawingBuffer })
 *     -> { update(geometry), setMode(m), setExploded(f), select(id), destroy() }
 *
 * Rules (as attitude3d.js): renders only on update / drag / resize, no loop;
 * WebGL missing -> "vz:webgl-unavailable" bubbles and opts.onFallback runs;
 * text alternative: role="img" + aria-label summary, and a "Values" table.
 * ============================================================================ */

import * as THREE from "./vendor/three/three.module.min.js";
import {
  injectBase, injectCss, translator, fmt, esc, segmented, valuesToggle, tokenValue, onThemeChange,
} from "./vizkit.js";

/** Strings built at run time (listed for the i18n scanners). */
// i18n-keys
export const DYNAMIC_KEYS = ["PC/104 board", "PC/104 module", "U module", "face panel", "deployable", "bracket",
  "structure", "distributed", "Payload", "Data handling", "AOCS", "Power", "Thermal", "TT&C", "Propulsion",
  "Structure", "Other"];
// i18n-keys
const SUBSYSTEM_LABEL = { payload: "Payload", obdh: "Data handling", obc: "Data handling", aocs: "AOCS", power: "Power",
  eps: "Power", thermal: "Thermal", ttc: "TT&C", comms: "TT&C", propulsion: "Propulsion", structure: "Structure",
  other: "Other" };
// i18n-keys
const MOUNT_LABEL = { pc104_board: "PC/104 board", pc104_module: "PC/104 module", u_module: "U module",
  face_panel: "face panel", deployable: "deployable", bracket: "bracket", structure: "structure",
  distributed: "distributed" };
/** Subsystem -> category token (same mapping as SpaceCDF theme/tokens.ts SUBSYSTEM). */
export const SUBSYSTEM_TOKEN = { payload: "--cat-1", obdh: "--cat-2", obc: "--cat-2", aocs: "--cat-3",
  power: "--cat-4", eps: "--cat-4", thermal: "--cat-5", ttc: "--cat-6", comms: "--cat-6", propulsion: "--cat-7",
  structure: "--cat-8", other: "--cat-8" };
const NORMAL = { px: [1, 0, 0], mx: [-1, 0, 0], py: [0, 1, 0], my: [0, -1, 0], pz: [0, 0, 1], mz: [0, 0, -1] };
const DEG = Math.PI / 180;

/* ── pure helpers (exported for tests) ─────────────────────────────────── */

/** Scene (three.js, y up) from body: x -> x, z (zenith) -> y, y -> -z. A proper rotation. */
export function sceneFromBody(v) { return [v[0], v[2], -v[1]]; }

/**
 * Where a box goes in the exploded view: column units spread along the stack
 * axis by slot and apart by column, face items out along their face normal.
 * f in [0, 1]; returns a body-frame offset in metres.
 */
export function explodeOffset(item, f, size) {
  if (!f) return [0, 0, 0];
  const [, sy, sz] = size;
  if (item.face && item.mount !== "u_module" && item.column == null && item.slot == null) {
    const n = NORMAL[item.face] || [0, 0, 0];
    return n.map((c) => c * 0.06 * f);
  }
  if (item.column != null) {
    const b = item.box_m;
    const zRel = b[2] / (sz / 2 || 1);                      // -1 nadir .. +1 zenith
    const side = Math.sign(b[1]) || 0;
    return [0, side * sy * 0.35 * f, zRel * sz * 0.45 * f];
  }
  return [0, 0, 0];
}

/** One-line text summary for screen readers. */
export function summary(geo, t) {
  if (!geo || !Array.isArray(geo.internal)) return t("No stack layout yet");
  const units = new Set(geo.internal.filter((b) => !b.distributed)
    .map((b) => String(b.id).split("#")[0].split("@")[0]));
  const mp = geo.mass_properties || {};
  const c = (mp.cog_m || []).map((x) => fmt(x * 1000, 1));
  return t("{{n}} units, {{m}} kg, centre of gravity {{x}}, {{y}}, {{z}} mm from the envelope centre.",
    { n: units.size, m: fmt(mp.mass_kg, 2), x: c[0] ?? "?", y: c[1] ?? "?", z: c[2] ?? "?" });
}

function webglAvailable() {
  try {
    const c = globalThis.document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch (e) { return false; }
}

const CSS = `
.vz-s3 .vz-stage{ position:relative; border:1px solid var(--vz-line); border-radius:var(--radius,3px);
  background:var(--vz-bg); overflow:hidden; touch-action:none; cursor:grab; }
.vz-s3 .vz-stage:active{ cursor:grabbing; }
.vz-s3 .vz-stage canvas{ display:block; width:100%; height:100%; }
.vz-s3 .vz-lbls{ position:absolute; inset:0; pointer-events:none; }
.vz-s3 .vz-lbl{ position:absolute; transform:translate(-50%,-50%); font-size:var(--fs-label,12px); white-space:nowrap;
  color:var(--vz-tx2); text-shadow:0 0 3px var(--vz-bg),0 0 3px var(--vz-bg); }
.vz-s3 .vz-lbl.ax{ font-family:var(--vz-mono); color:var(--vz-tx3); }
.vz-s3 .vz-lbl.sel{ color:var(--vz-val); font-weight:600; }
.vz-s3 .vz-conv{ position:absolute; left:10px; bottom:6px; right:10px; font:400 var(--fs-label,12px)/1.3 var(--vz-mono);
  color:var(--vz-tx3); pointer-events:none; }
.vz-s3 .vz-hint{ position:absolute; left:10px; top:8px; font-size:var(--fs-label,12px); color:var(--vz-tx3); pointer-events:none; }
.vz-s3 .vz-empty{ position:absolute; inset:0; display:grid; place-items:center; text-align:center; padding:24px; color:var(--vz-tx2); }
.vz-s3 .vz-empty[hidden]{ display:none; }
.vz-s3 .vz-range{ display:inline-flex; align-items:center; gap:6px; font-size:var(--fs-label,12px); color:var(--vz-tx2); }
.vz-s3 .vz-range input{ width:120px; accent-color:var(--vz-accent); }
.vz-s3 .vz-legend{ display:flex; gap:4px 14px; flex-wrap:wrap; padding-top:6px; font-size:var(--fs-label,12px); color:var(--vz-tx3); }
.vz-s3 .vz-legend i{ display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:4px; vertical-align:-1px; }
.vz-s3 .vz-fallback{ padding:16px; border:1px dashed var(--vz-line2); border-radius:var(--radius,3px); color:var(--vz-tx2); }
`;

export function mount(el, opts = {}) {
  injectBase();
  injectCss("vz-s3-css", CSS);
  const t = translator(opts);
  const d = globalThis.document;
  let geo = opts.geometry || null;
  let mode = opts.mode === "deployed" ? "deployed" : "stowed";
  let exploded = Math.max(0, Math.min(1, Number(opts.exploded) || 0));
  let selected = null;
  let destroyed = false;

  const root = d.createElement("div");
  root.className = "vz vz-s3";
  el.appendChild(root);

  const bar = d.createElement("div");
  bar.className = "vz-bar";
  const seg = segmented(t("Configuration"), [
    { value: "stowed", label: t("Stowed") }, { value: "deployed", label: t("Deployed") }], mode,
  (v) => { mode = v; seg.set(v); build(); });
  const range = d.createElement("label");
  range.className = "vz-range";
  const rin = d.createElement("input");
  rin.type = "range"; rin.min = "0"; rin.max = "100"; rin.step = "5"; rin.value = String(Math.round(exploded * 100));
  rin.setAttribute("aria-label", t("Exploded view"));
  range.append(d.createTextNode(t("Exploded view")), rin);
  rin.addEventListener("input", () => { exploded = Number(rin.value) / 100; build(); });
  const sp = d.createElement("span"); sp.className = "vz-sp";
  const reset = d.createElement("button");
  reset.type = "button"; reset.className = "vz-btn"; reset.textContent = t("Reset view");
  const tabHost = d.createElement("div");
  const vt = valuesToggle(t, tabHost, `vz-s3-tab-${Math.random().toString(36).slice(2, 8)}`);
  bar.append(seg.el, range, sp, reset, vt.btn);
  root.appendChild(bar);

  if (!webglAvailable()) return fallback(t("WebGL is not available in this browser"));

  const stage = d.createElement("div");
  stage.className = "vz-stage";
  stage.setAttribute("role", "img");
  stage.tabIndex = 0;
  stage.style.height = `${opts.height || 420}px`;
  const lbls = d.createElement("div"); lbls.className = "vz-lbls"; lbls.setAttribute("aria-hidden", "true");
  const conv = d.createElement("div"); conv.className = "vz-conv";
  const hint = d.createElement("div"); hint.className = "vz-hint";
  hint.textContent = t("Drag to orbit, wheel or +/− to zoom, arrow keys to rotate.");
  const empty = d.createElement("div"); empty.className = "vz-empty"; empty.hidden = true;
  const legend = d.createElement("div"); legend.className = "vz-legend";
  root.append(stage, legend, tabHost);

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: !!opts.preserveDrawingBuffer });
  } catch (e) {
    stage.remove(); legend.remove();
    return fallback(t("WebGL could not start"));
  }
  renderer.setPixelRatio(Math.min(2, globalThis.devicePixelRatio || 1));
  renderer.domElement.setAttribute("aria-hidden", "true");
  stage.append(renderer.domElement, lbls, hint, conv, empty);
  renderer.domElement.addEventListener("webglcontextlost", (e) => { e.preventDefault(); signalFallback(t("the WebGL context was lost")); });

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 50);
  const CAM0 = { az: 38, el: 22, dist: 1.3 };
  const cam = { ...CAM0 };
  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  const key = new THREE.DirectionalLight(0xffffff, 1.2);
  key.position.set(1, 2, 1.5);
  scene.add(key);
  const body = new THREE.Group();                 // body frame -> scene (zenith up)
  body.matrixAutoUpdate = false;
  body.matrix.set(1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1);
  scene.add(body);

  let disposables = [];
  const track = (o) => { disposables.push(o); return o; };
  const pickables = [];                           // meshes with userData.id
  let labelsAt = [];                              // [{text, pos (body), cls}]

  const col = (name, fb = "--vz-tx3") => new THREE.Color(tokenValue(root, name) || tokenValue(root, fb) || "gray");

  function clearScene() {
    while (body.children.length) body.remove(body.children[0]);
    disposables.forEach((o) => o.dispose && o.dispose());
    disposables = [];
    pickables.length = 0;
    labelsAt = [];
  }

  function box(c, s, colour, opacity = 1, edgeColour = null, id = null) {
    const g = track(new THREE.BoxGeometry(Math.max(s[0], 0.0008), Math.max(s[1], 0.0008), Math.max(s[2], 0.0008)));
    const grp = new THREE.Group();
    if (colour) {
      const m = track(new THREE.MeshLambertMaterial({ color: colour, transparent: opacity < 1, opacity,
        depthWrite: opacity >= 1 }));
      const mesh = new THREE.Mesh(g, m);
      if (id) { mesh.userData.id = id; pickables.push(mesh); }
      grp.add(mesh);
    }
    if (edgeColour) {
      grp.add(new THREE.LineSegments(track(new THREE.EdgesGeometry(g)), track(new THREE.LineBasicMaterial({ color: edgeColour }))));
    }
    grp.position.set(c[0], c[1], c[2]);
    body.add(grp);
    return grp;
  }

  function line(pts, colour, dashed = false) {
    const g = track(new THREE.BufferGeometry().setFromPoints(pts.map((p) => new THREE.Vector3(...p))));
    const m = track(dashed ? new THREE.LineDashedMaterial({ color: colour, dashSize: 0.008, gapSize: 0.006 })
      : new THREE.LineBasicMaterial({ color: colour }));
    const l = new THREE.Line(g, m);
    if (dashed) l.computeLineDistances();
    body.add(l);
    return l;
  }

  function cone(apex, dir, halfDeg, len, colour) {
    const r = len * Math.tan(halfDeg * DEG);
    const g = track(new THREE.ConeGeometry(r, len, 28, 1, true));
    g.translate(0, -len / 2, 0);
    g.rotateX(Math.PI);                            // apex at the origin, opening along +y
    const m = track(new THREE.MeshBasicMaterial({ color: colour, transparent: true, opacity: 0.07, depthWrite: false,
      side: THREE.DoubleSide }));
    const mesh = new THREE.Mesh(g, m);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(...dir).normalize());
    mesh.position.set(...apex);
    body.add(mesh);
  }

  function build() {
    if (destroyed) return;
    clearScene();
    const has = geo && geo.bus && Array.isArray(geo.bus.size_m);
    empty.hidden = !!has;
    empty.textContent = t("No stack layout yet");
    if (!has) { describe(); render(); return; }
    const size = geo.bus.size_m;
    const [sx, sy, sz] = size;
    const C = { line: col("--vz-line2"), tx3: col("--vz-tx3"), val: col("--vz-val"), accent: col("--vz-accent"),
      fill: col("--vz-fill"), warn: col("--vz-warn") };
    // envelope
    box([0, 0, 0], size, C.fill, 0.06, C.line);
    // units
    const deployed = mode === "deployed";
    const used = new Set();
    for (const b of geo.internal || []) {
      if (b.distributed || b.mount === "structure" || b.mount === "distributed") continue;
      if (deployed && b.mount === "deployable") continue;   // drawn unfolded below
      const off = explodeOffset(b, exploded, size);
      const c = [b.box_m[0] + off[0], b.box_m[1] + off[1], b.box_m[2] + off[2]];
      const tok = SUBSYSTEM_TOKEN[b.subsystem] || "--cat-8";
      used.add(b.subsystem || "other");
      const base = String(b.id).split("#")[0];
      const sel = selected && (selected === base || selected === b.id || selected === String(base).split("@")[0]);
      box(c, b.box_m.slice(3), col(tok), 0.92, sel ? C.accent : C.line, base);
      if (sel) labelsAt.push({ text: b.name || base, pos: [c[0], c[1], c[2] + b.box_m[5] / 2 + 0.01], cls: "sel" });
    }
    // deployed geometry: wings (simulator law at drive angle 0) and antenna elements
    if (deployed) {
      for (const w of geo.wings || []) {
        const out = NORMAL[w.face] || w.mount_axis;
        const [len, wid] = w.panel_size_m;
        for (let k = 0; k < (w.panels || 1); k++) {
          const dist = (w.face === "py" || w.face === "my" ? sy : sx) / 2 + 0.03 + len * (k + 0.5);
          const c = out.map((v) => v * dist);
          const s = out.map((v) => (v ? len : 0));
          if (Math.abs(out[0]) > 0.5) { s[1] = 0.004; s[2] = wid; } else { s[0] = 0.004; s[2] = wid; }
          box(c, s, col("--cat-4"), 0.85, C.line, `wing:${w.id}`);
        }
        const root0 = out.map((v) => v * ((w.face === "py" || w.face === "my" ? sy : sx) / 2));
        line([root0, out.map((v, i) => root0[i] + v * 0.03)], C.line);
      }
      for (const a of geo.antennas || []) {
        if (a.kind !== "dipole") continue;
        const p0 = a.position_m, L = a.length_m || 0.17;
        line([p0, p0.map((v, i) => v + a.boresight[i] * L)], C.val);
      }
    }
    // keep-out cones: star trackers and the imager
    for (const s of geo.star_trackers || []) cone(s.position_m, s.boresight, (s.fov_deg || 12) / 2, 0.22, C.tx3);
    if (geo.payload) cone(geo.payload.position_m, geo.payload.boresight, (geo.payload.fov_deg || 10) / 2, 0.2, C.tx3);
    // centre of gravity + CDS box
    const mp = geo.mass_properties;
    if (mp && Array.isArray(mp.cog_m)) {
      const g = mp.cog_m, r = 0.012;
      for (let i = 0; i < 3; i++) {
        const a = [...g], b = [...g];
        a[i] -= r; b[i] += r;
        line([a, b], C.val);
      }
      const m = new THREE.Mesh(track(new THREE.OctahedronGeometry(0.006)), track(new THREE.MeshBasicMaterial({ color: C.val })));
      m.position.set(...g);
      body.add(m);
      labelsAt.push({ text: t("CoG"), pos: [g[0], g[1], g[2] + 0.02], cls: "sel" });
      if (Array.isArray(opts.cogBox_m)) {
        const h = opts.cogBox_m;
        const cb = box([0, 0, 0], [2 * h[0], 2 * h[1], 2 * h[2]], null, 1, C.warn);
        cb.children.forEach((c) => { if (c.material) { c.material.transparent = true; c.material.opacity = 0.7; } });
      }
    }
    // body axes from the envelope corner
    const o = [-sx / 2 - 0.02, -sy / 2 - 0.02, -sz / 2 - 0.02];
    const L = 0.07;
    [[1, 0, 0, "+X"], [0, 1, 0, "+Y"], [0, 0, 1, "+Z"]].forEach(([x, y, z, n]) => {
      const tip = [o[0] + x * L, o[1] + y * L, o[2] + z * L];
      line([o, tip], C.tx3);
      labelsAt.push({ text: n, pos: tip.map((v, i) => v + [x, y, z][i] * 0.018), cls: "ax" });
    });
    labelsAt.push({ text: t("+Z zenith"), pos: [0, 0, sz / 2 + 0.03], cls: "ax" });
    labelsAt.push({ text: t("nadir"), pos: [0, 0, -sz / 2 - 0.03], cls: "ax" });
    conv.textContent = t("Body frame: +X velocity, +Y orbit normal, +Z zenith (−Z nadir); origin at the envelope centre");
    // legend
    legend.innerHTML = [...used].sort().map((k) =>
      `<span><i style="background:var(${SUBSYSTEM_TOKEN[k] || "--cat-8"})"></i>${esc(t(SUBSYSTEM_LABEL[k] || "Other"))}</span>`).join("");
    describe();
    render();
  }

  function describe() {
    stage.setAttribute("aria-label", `${t("Stack in 3D")}. ${summary(geo, t)}`);
    if (!vt.isOpen()) return;
    const rows = (geo?.internal || []).filter((b) => !b.distributed).map((b) => {
      const where = b.column != null ? t("column {{c}}, slot {{s}}", { c: b.column + 1, s: (b.slot ?? 0) + 1 })
        : b.face ? t("face {{f}}", { f: b.face }) : "—";
      return `<tr><th scope="row" style="font-weight:400;text-align:left">${esc(b.name || b.id)}</th>` +
        `<td class="s">${esc(t(MOUNT_LABEL[b.mount] || b.mount || ""))}</td><td class="s">${esc(where)}</td>` +
        `<td class="n">${esc(fmt(b.mass_kg, 3))}</td>` +
        `<td class="n">${esc(b.box_m.slice(0, 3).map((x) => fmt(x * 1000, 0)).join(", "))}</td></tr>`;
    }).join("");
    tabHost.innerHTML = `<table class="vz-tab"><caption>${esc(t("Stack layout values"))}</caption><thead><tr>` +
      `<th scope="col">${esc(t("Unit"))}</th><th scope="col">${esc(t("Mount"))}</th><th scope="col">${esc(t("Where"))}</th>` +
      `<th scope="col">${esc(t("Mass (kg)"))}</th><th scope="col">${esc(t("Centre (mm)"))}</th></tr></thead><tbody>${rows}</tbody></table>`;
  }
  vt.btn.addEventListener("click", () => describe());

  /* labels */
  const labelEls = [];
  function placeLabels() {
    while (labelEls.length < labelsAt.length) { const e = d.createElement("span"); lbls.appendChild(e); labelEls.push(e); }
    const w = stage.clientWidth, h = stage.clientHeight;
    labelEls.forEach((e, i) => {
      const L = labelsAt[i];
      if (!L) { e.style.display = "none"; return; }
      const p = new THREE.Vector3(...sceneFromBody(L.pos)).project(camera);
      const x = (p.x + 1) / 2 * w, y = (1 - p.y) / 2 * h;
      if (p.z > 1 || x < 4 || x > w - 4 || y < 4 || y > h - 4) { e.style.display = "none"; return; }
      e.className = `vz-lbl ${L.cls || ""}`;
      e.textContent = L.text;
      e.style.display = "";
      e.style.left = `${x.toFixed(0)}px`;
      e.style.top = `${y.toFixed(0)}px`;
    });
  }

  /* camera */
  function placeCamera() {
    const a = cam.az * DEG, e = cam.el * DEG;
    const span = geo?.bus?.size_m ? Math.max(...geo.bus.size_m) : 0.35;
    const dist = cam.dist * span * 2.2 * Math.max(1, 1.3 / (camera.aspect || 1.3)) * (1 + exploded * 0.6);
    camera.position.set(dist * Math.cos(e) * Math.sin(a), dist * Math.sin(e), dist * Math.cos(e) * Math.cos(a));
    camera.lookAt(0, 0, 0);
  }
  function size() {
    const w = stage.clientWidth || 600, h = stage.clientHeight || 420;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  function render() {
    if (destroyed) return;
    placeCamera();
    renderer.setClearColor(0x000000, 0);
    renderer.render(scene, camera);
    placeLabels();
  }
  let drag = null, moved = false;
  const onDown = (e) => { drag = { x: e.clientX, y: e.clientY, az: cam.az, el: cam.el }; moved = false; stage.setPointerCapture?.(e.pointerId); };
  const onMove = (e) => {
    if (!drag) return;
    if (Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) > 3) moved = true;
    cam.az = drag.az - (e.clientX - drag.x) * 0.4;
    cam.el = Math.max(-85, Math.min(85, drag.el + (e.clientY - drag.y) * 0.3));
    render();
  };
  const onUp = (e) => {
    if (drag && !moved) pick(e);
    drag = null;
  };
  const onWheel = (e) => { e.preventDefault(); cam.dist = Math.max(0.5, Math.min(4, cam.dist * (e.deltaY > 0 ? 1.08 : 0.93))); render(); };
  const onKey = (e) => {
    if (e.key === "+" || e.key === "=") { cam.dist = Math.max(0.5, cam.dist * 0.9); render(); e.preventDefault(); return; }
    if (e.key === "-") { cam.dist = Math.min(4, cam.dist * 1.1); render(); e.preventDefault(); return; }
    const k = { ArrowLeft: [-10, 0], ArrowRight: [10, 0], ArrowUp: [0, 8], ArrowDown: [0, -8] }[e.key];
    if (!k) return;
    e.preventDefault();
    cam.az += k[0]; cam.el = Math.max(-85, Math.min(85, cam.el + k[1]));
    render();
  };
  const ray = new THREE.Raycaster();
  function pick(e) {
    const r = stage.getBoundingClientRect();
    const v = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(v, camera);
    const hit = ray.intersectObjects(pickables, false)[0];
    const id = hit ? hit.object.userData.id : null;
    selected = id;
    build();
    if (typeof opts.onSelect === "function") opts.onSelect(id);
  }
  stage.addEventListener("pointerdown", onDown);
  stage.addEventListener("pointermove", onMove);
  stage.addEventListener("pointerup", onUp);
  stage.addEventListener("pointercancel", () => { drag = null; });
  stage.addEventListener("wheel", onWheel, { passive: false });
  stage.addEventListener("keydown", onKey);
  reset.addEventListener("click", () => { Object.assign(cam, CAM0); render(); });
  let ro = null;
  try { ro = new ResizeObserver(() => { size(); render(); }); ro.observe(stage); } catch (e) { /* static size */ }
  const offTheme = onThemeChange(() => build());
  size();
  build();

  function signalFallback(reason) {
    try { el.dispatchEvent(new CustomEvent("vz:webgl-unavailable", { bubbles: true, detail: { reason } })); } catch (e) { /* */ }
    if (typeof opts.onFallback === "function") opts.onFallback(reason);
  }
  function fallback(reason) {
    const fb = d.createElement("div");
    fb.className = "vz-fallback";
    fb.textContent = t("3D view unavailable: {{reason}}. The elevation and face map show the same layout.", { reason });
    root.appendChild(fb);
    signalFallback(reason);
    return { update() {}, setMode() {}, setExploded() {}, select() {}, fallback: true,
      destroy() { destroyed = true; root.remove(); } };
  }

  return {
    update(g) { geo = g || null; build(); },
    setMode(m) { mode = m === "deployed" ? "deployed" : "stowed"; seg.set(mode); build(); },
    setExploded(f) { exploded = Math.max(0, Math.min(1, Number(f) || 0)); rin.value = String(Math.round(exploded * 100)); build(); },
    select(id) { selected = id || null; build(); },
    destroy() {
      destroyed = true;
      try { ro && ro.disconnect(); } catch (e) { /* */ }
      offTheme();
      clearScene();
      renderer.dispose();
      root.remove();
    },
  };
}
