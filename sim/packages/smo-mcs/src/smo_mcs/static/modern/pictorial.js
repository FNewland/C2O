/* ============================================================================
 * SMO MCS MODERN CONSOLE — pictorial.js
 * ============================================================================
 * Mounts the shared pictorial displays (/static/shared/viz/, source
 * shared/ui-viz/) on the console pages and feeds them interpreted values:
 *
 *   Overview   spacecraft synoptic (overview.js: subsystem blocks, antenna and
 *              wings stowed/deployed, panels sunlit/dark) + power-flow summary
 *   EPS        power flow, full (powerflow.js)
 *   AOCS       2D attitude instruments (attitude2d.js) and, when the module
 *              is present and WebGL works, the 3D view (attitude3d.js) in #att3d
 *
 * mcs.js loads this module with a dynamic import() and hands it a context of
 * accessors (state, limits, freshness verdicts, alarm summary, mode, clock,
 * navigation, translation). Nothing here re-derives contact, mode or age:
 * those come from mcs.js / state.js; the physics interpretation comes from
 * derive.js. If any module fails to load, the console keeps its schematics.
 * ============================================================================ */

const BASE = "/static/shared/viz/";
let D, PF, OV, A2, A3 = null;
let C = null;                      // context from mcs.js
const V = { hist: null, views: {}, sunlitGenW: null, att3d: null, att3dFailed: false, geometry: null };

/* subsystem id (overview.js) -> console page id */
export const SUB_PAGE = { eps: "eps", aocs: "aocs", obdh: "obd", tcs: "tcs", ttc: "ttc", payload: "pld", prop: "prp" };
const SUB_RANGE = { eps: [0x0100, 0x01FF], aocs: [0x0200, 0x02FF], obdh: [0x0300, 0x03FF],
  tcs: [0x0400, 0x04FF], ttc: [0x0500, 0x05FF], payload: [0x0600, 0x06FF], prop: [0x0B00, 0x0BFF] };
/* the parameters whose freshness says whether a subsystem block is current */
const SUB_KEY = { eps: ["0x0101", "0x0105"], aocs: ["0x020F", "0x02A0"], obdh: ["0x0302"],
  tcs: ["0x0406", "0x0407"], ttc: ["0x0502"], payload: ["0x0601", "0x0604"], prop: ["0x0B01"] };

export async function init(ctx) {
  C = ctx;
  [D, PF, OV, A2] = await Promise.all(["derive.js", "powerflow.js", "overview.js", "attitude2d.js"]
    .map((f) => import(BASE + f)));
  V.hist = D.createHistory(900);
  // The 3D view is V2's module: optional, behind a feature check.
  try {
    const m = await import(BASE + "attitude3d.js");
    if (m && typeof m.mount === "function") A3 = m;
  } catch (e) { A3 = null; }
  return true;
}

function src() {
  return D.sourceFromState(C.state(), {
    limits: C.limits(),
    verdict: (hex) => C.freshness(hex),
  });
}

/** Called on every state message, whatever the page: keeps the trend history. */
export function onState() {
  if (!D) return;
  const s = src();
  const now = C.nowS();
  const sample = D.historySample(s);
  const a = D.deriveAttitude(s);
  if (a.errDeg.v !== null && a.errDeg.verdict !== "stale") sample.err = a.errDeg.v;
  V.hist.push(now, sample);
  const st = C.state();
  const ecl = st.in_eclipse ?? st.eclipse;
  const gen = s.get("0x0107");
  if (ecl === false && gen.v !== null && gen.verdict === "fresh") V.sunlitGenW = gen.v;
}

function model() {
  const s = src();
  const m = D.deriveAll(s, { history: V.hist, sunlitGenW: V.sunlitGenW });
  m.src = s;
  return m;
}

const U = (q, units) => ({ ...q, units });

/** The power-flow "This orbit" ground estimate ({periodS, inWh, outWh,
 *  netWh}), for the EPS projections card (mcs.js); null before init. */
export function powerBalance() {
  if (!D) return null;
  try { return model().power.balance; } catch (e) { return null; }
}

/* ── worst state per subsystem: alarms, then limit states, then freshness ── */
function subState(sub, s) {
  const summ = C.alarmSummary();
  const c = (summ.bySub || {})[sub] || { a: 0, w: 0 };
  if (c.a) return { state: "alarm", alarms: c };
  if (c.w) return { state: "caution", alarms: c };
  const [lo, hi] = SUB_RANGE[sub];
  let lim = "";
  for (const [hex, st] of Object.entries(C.state().param_limit_state || {})) {
    const n = parseInt(hex, 16);
    if (n < lo || n > hi || !st) continue;
    if (String(st).startsWith("red")) { lim = "alarm"; break; }
    if (String(st).startsWith("yellow")) lim = "caution";
  }
  if (lim) return { state: lim, alarms: c };
  const keys = SUB_KEY[sub].map((h) => s.get(h));
  if (keys.every((q) => q.verdict === "nodata")) return { state: "nodata", alarms: c };
  if (keys.some((q) => q.verdict === "stale" || q.verdict === "disabled")) return { state: "stale", alarms: c };
  return { state: "nominal", alarms: c };
}

function overviewModel(m) {
  const s = m.src, t = C.t, L = C.limits();
  const lim = (hex) => L[hex] || null;
  const ls = (hex) => {
    const st = (C.state().param_limit_state || {})[hex];
    return !st ? "" : String(st).startsWith("red") ? "alarm" : String(st).startsWith("yellow") ? "caution" : "";
  };
  const row = (label, q, digits, hex, limits) => ({ label, q, digits, limits: limits || (hex ? lim(hex) : null), limitState: hex ? ls(hex) : "" });
  const a = m.attitude, p = m.power;
  const aocsModeName = C.engValue("0x020F", s.get("0x020F").v);
  const errLim = { red_low: 0, yellow_low: 0, yellow_high: a.errLimits.warn, red_high: a.errLimits.alarm };
  const sto = m.storage;
  const net = p.balance.netWh;
  const subs = {
    eps: { ...subState("eps", s), rows: [
      row(t("Battery SoC"), U(s.get("0x0101"), "%"), 1, "0x0101"),
      row(t("Bus voltage"), U(s.get("0x0105"), "V"), 2, "0x0105")],
      mode: net.v !== null ? t("orbit energy balance {{n}} (ground estimate)", { n: `${net.v > 0 ? "+" : ""}${net.v.toFixed(0)} Wh` }) : "" },
    aocs: { ...subState("aocs", s), rows: [
      row(t("error"), a.errDeg.v !== null ? a.errDeg : U(s.get("0x0217"), "°"), 3, null, errLim),
      row(t("momentum"), U(a.momentum.envPct, "%"), 0, "0x02BA")],
      mode: aocsModeName ? t("mode {{m}}", { m: String(aocsModeName).replace(/\s*\(\d+\)$/, "") }) : "" },
    obdh: { ...subState("obdh", s), rows: [
      row(t("CPU"), U(s.get("0x0302"), "%"), 0, "0x0302"), row(t("TM buffer"), U(s.get("0x0312"), "%"), 0, "0x0312")] },
    tcs: { ...subState("tcs", s), rows: [
      row(t("battery"), U(s.get("0x0407"), "°C"), 1, "0x0407"), row(t("OBC"), U(s.get("0x0406"), "°C"), 1, "0x0406")] },
    prop: { ...subState("prop", s), rows: [
      row(t("tank"), U(s.get("0x0B01"), "bar"), 1, "0x0B01"), row(t("ΔV left"), U(s.get("0x0B0C"), "m/s"), 1, "0x0B0C")] },
    payload: { ...subState("payload", s), rows: [
      row(t("FPA temperature"), U(s.get("0x0601"), "°C"), 1, "0x0601"),
      row(t("Storage"), U(sto.fill, "%"), 0, "0x0604", lim("0x0604") || { yellow_low: 0, red_low: 0, yellow_high: 80, red_high: 95 })],
      mode: sto.timeToFullS.v !== null ? t("storage full in {{d}} at the present rate", { d: fmtDur(sto.timeToFullS.v) }) : "" },
    ttc: { ...subState("ttc", s), rows: [
      row(t("margin"), { ...U(s.get("0x0503"), "dB"), ground: true }, 1, "0x0503"),
      row(t("TM rate"), (() => { const q = s.get("0x0506"); return { ...q, v: q.v === null ? null : q.v / 1000, units: "kbps" }; })(), 0, "0x0506")] },
  };
  const vis = C.visibleSubsystems();
  if (vis) for (const k of Object.keys(subs)) if (!vis.includes(k)) subs[k].hidden = true;
  const mi = C.scModeInfo();
  const link = C.linkState();
  return {
    mode: { label: mi.label === "—" ? null : mi.label, src: mi.src },
    aocsMode: aocsModeName ? String(aocsModeName).replace(/\s*\(\d+\)$/, "") : null,
    eclipse: m.orbit.inEclipse, contact: link.contact, gs: link.gs, subsystems: subs,
    // antenna / wings stowed or deployed, panels sunlit or dark: TM only
    // (derive.js deriveDeployment documents the parameters)
    deploy: m.deploy,
  };
}

function fmtDur(sec) {
  const x = Math.round(sec);
  if (x < 90) return `${x} s`;
  const mi = Math.round(x / 60);
  return mi < 90 ? `${mi} min` : `${Math.floor(mi / 60)} h ${String(mi % 60).padStart(2, "0")} min`;
}

function ensure(key, hostId, mod, opts) {
  const host = document.getElementById(hostId);
  if (!host) return null;
  const cur = V.views[key];
  if (cur && cur.host === host && host.isConnected) return cur.view;
  const view = mod.mount(host, { t: C.t, onNavigate: (sub) => C.showPage(SUB_PAGE[sub] || sub), ...opts });
  V.views[key] = { host, view };
  return view;
}

/** Render the views of the current page. Returns true when it drew. */
export function render(page) {
  if (!D) return false;
  const m = model();
  if (page === "ovr") {
    const ov = ensure("ov", "ovr-schematic", OV, { blockId: (sub) => `ovr-node-${SUB_PAGE[sub]}` });
    if (ov) ov.update(overviewModel(m));
    const pf = ensure("pfs", "ovr-power", PF, { variant: "summary" });
    if (pf) pf.update(m.power);
    return true;
  }
  if (page === "eps") {
    const pf = ensure("pff", "eps-flow", PF, { variant: "full", animate: true });
    if (pf) pf.update(m.power);
    return true;
  }
  if (page === "aocs") {
    const a = m.attitude;
    a.errHistory = V.hist.series("err", 600);
    a.limits = C.limits();
    const mode = C.engValue("0x020F", m.src.get("0x020F").v);
    a.aocsMode = mode ? String(mode).replace(/\s*\(\d+\)$/, "") : null;
    const a2 = ensure("a2", "aocs-att2d", A2, {});
    if (a2) a2.update(a);
    render3d(a, m);
    return true;
  }
  return false;
}

function render3d(a, m) {
  const host = document.getElementById("att3d");
  if (!host) return;
  if (!A3 || V.att3dFailed) { host.hidden = true; return; }
  if (!V.att3d || V.att3d.host !== host || !host.isConnected) {
    host.hidden = false;
    host.addEventListener("vz:webgl-unavailable", () => { V.att3dFailed = true; host.hidden = true; }, { once: true });
    try {
      const view = A3.mount(host, { t: C.t, onFallback: () => { V.att3dFailed = true; host.hidden = true; } });
      V.att3d = { host, view };
      if (typeof A3.fetchGeometry === "function" && typeof view.setGeometry === "function") {
        A3.fetchGeometry().then((g) => { if (g) view.setGeometry(g); }).catch(() => {});
      }
    } catch (e) { V.att3dFailed = true; host.hidden = true; return; }
  }
  const st = C.state();
  a.illum = { sunFraction: st.sun_fraction, verdict: "fresh" };
  a.wingStatus = m.src.get("0x0144").v;
  // Ground-propagated orbit (MCS /api/state orbit_ground, TEME ~ ECI): gives
  // the 3D view a true LVLH frame whatever the spacecraft is pointing at.
  const og = st.orbit_ground;
  a.lvlh = (og && Array.isArray(og.r_eci_km) && Array.isArray(og.v_eci_kms))
    ? { r: og.r_eci_km, v: og.v_eci_kms } : undefined;
  try { V.att3d.view.update(a); } catch (e) { /* the 2D instruments stay */ }
}

/** Language switch: rebuild every mounted view so static text re-translates. */
export function relabel() {
  for (const k of Object.keys(V.views)) {
    try { V.views[k].view.destroy(); } catch (e) { /* gone */ }
    delete V.views[k];
  }
  if (V.att3d) { try { V.att3d.view.destroy(); } catch (e) { /* gone */ } V.att3d = null; }
}
