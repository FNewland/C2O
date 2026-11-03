/* ============================================================================
 * C2O INSTRUCTOR — truth views (HTML/SVG strings from /api/instructor/views)
 * ============================================================================
 * Every view reads the simulator's TRUTH (model internals), grey at rest,
 * colour only for status, the inject colour (--shelf) only for what the
 * instructor did. Numbers sit in fixed places beside the pictures, never on
 * moving marks. INSTRUCTOR_CONSOLE_DESIGN.md §6 has the figure of each view.
 * ========================================================================== */

import { esc, renderChip, renderNoData, renderSparkline, renderStepper } from "/static/shared/components.js";
import { t, tText } from "/static/shared/i18n.js";

// i18n-keys (labels that arrive from the server and are translated here)
export const DYNAMIC_KEYS = [
  "Control input", "Controller", "Actuator", "Process", "Process input", "Disturbance",
  "Observer (sensor)", "Data path and products",
  "Commands cannot reach the spacecraft or arrive wrong", "On-board software, computer and control laws",
  "Wheels, torquers, heaters, switches, valves, drives", "The physical plant: arrays, battery, bus, tanks, zones",
  "Outside the spacecraft: ground station and RF path", "Upsets and unplanned heat: SEU, memory errors, heat leaks",
  "Sensors, estimates and clocks lie; the truth is unchanged", "Buses, transponders, mass memory and image products",
  "Energy balance", "Keep the spacecraft powered", "Pointing and momentum", "Image the target; keep arrays on the sun",
  "Thermal balance", "Keep units inside their temperature limits", "Command, data and autonomy",
  "Keep the spacecraft safe and commandable", "Communication with the ground", "Downlink data and accept commands",
  "Image acquisition", "Deliver usable images", "Orbit control", "Keep the orbit and avoid collisions",
  "Time knowledge", "Time-tag data and run schedules on time", "Command reception",
  "Accept commands from the ground", "Array pointing", "Focal-plane cooling",
];
// i18n-keys (split: the catalog scanner reads at most 2000 characters per table)
export const DYNAMIC_KEYS_2 = [
  "Pointing error", "Attitude knowledge error", "Body rate roll", "Body rate pitch", "Body rate yaw",
  "+X panel temperature", "−X panel temperature", "+Y panel temperature", "−Y panel temperature",
  "+Z panel temperature", "−Z panel (radiator) temperature", "OBC temperature", "Battery temperature",
  "FPA temperature", "Catalyst bed temperature", "Battery state of charge", "Bus voltage", "Power generated",
  "Spacecraft mode (sat.mode)", "OBC software mode (obdh.mode)", "On-board clock offset", "Payload store used",
  "Station in view", "ttc_tx power line on", "PA on", "Selected transponder alive", "S-band antenna deployed",
  "S-band radiating",
];
// i18n-keys
export const DYNAMIC_KEYS_3 = [
  "SoC", "Pointing (true)", "OBC", "Mode", "Margin", "Store", "Tank",
  "OBC / FDIR", "TT&C / link", "Payload / storage", "Propulsion", "eclipse", "downlink", "no downlink",
  "no telecommand delay data", "housekeeping SID disabled", "no downlink (out of contact or transmitter off)",
  "waiting for the next housekeeping packet", "not in any housekeeping structure",
  "waiting for the next housekeeping packet (every {{s}} s)", "housekeeping SID {{sids}} disabled",
  "not generated: power line {{line}} off", "OBC in the bootloader: only the beacon housekeeping is generated",
  "no telecommand for the ground to compare", "no truth for this quantity",
  "never received on the ground", "the ground has an older value",
];

const nd = () => renderNoData();
const fin = (v) => v !== null && v !== undefined && Number.isFinite(Number(v));
const fx = (v, d = 1) => (fin(v) ? Number(v).toFixed(d) : null);
const mono = (s, cls = "") => `<span class="mono ${cls}">${esc(s)}</span>`;

export function num(v, d, unit) {
  if (!fin(v)) return nd();
  return `<span class="ds-value">${esc(Number(v).toFixed(d))}${unit ? `<span class="u"> ${esc(unit)}</span>` : ""}</span>`;
}

export function fmtAge(s) {
  if (!fin(s)) return "";
  s = Math.abs(Number(s));
  if (s < 90) return `${Math.round(s)} s`;
  if (s < 5400) return `${Math.round(s / 60)} min`;
  if (s < 172800) return `${(s / 3600).toFixed(1)} h`;
  return `${Math.round(s / 86400)} d`;
}

export function fmtClockSec(ts) {
  if (!fin(ts)) return "--:--:--";
  return new Date(ts * 1000).toISOString().slice(11, 19);
}

/** A clock offset in its natural scale: days first, never a 9-digit second count. */
export function fmtOffset(s) {
  if (!fin(s)) return null;
  const a = Math.abs(s), sign = s < 0 ? "−" : "+";
  if (a >= 86400) return tText("{{sign}}{{d}} days (clock never set)", { sign, d: Math.round(a / 86400) });
  if (a >= 3600) return `${sign}${(a / 3600).toFixed(2)} h`;
  if (a >= 60) return `${sign}${(a / 60).toFixed(2)} min`;
  return `${sign}${a.toFixed(3)} s`;
}

const STATE_CHIP = {
  caution: () => renderChip({ kind: "warn", label: tText("caution") }),
  alarm: () => renderChip({ kind: "alarm", label: tText("alarm") }),
  injected: () => `<span class="inj-chip">${esc(tText("injected"))}</span>`,
  nodata: () => renderChip({ kind: "nodata", label: tText("no data") }),
};

/* ── 1. overview strip (Level 1) ───────────────────────────────────────── */

export function renderTiles(ov, spark, focusView) {
  if (!ov || !ov.tiles) return "";
  const tiles = ov.tiles.map((tl) => {
    const st = tl.state || "ok";
    const v = tl.id === "obdh" ? `<span class="ds-value">${esc(tl.note || "")}</span>`
      : num(tl.value, tl.digits, tl.unit);
    const badges = [];
    if (tl.injected) badges.push(`<span class="inj-chip" title="${esc(tText("{{n}} injected fault(s) active", { n: tl.injected }))}">${esc(tText("inj {{n}}", { n: tl.injected }))}</span>`);
    const dlie = (tl.div_injected || 0) + (tl.div_estimator || 0);
    if (dlie) badges.push(`<span class="div-chip" title="${esc(tText("{{n}} value(s) where the spacecraft's own measurement is off the truth", { n: dlie }))}">≠ ${dlie}</span>`);
    const s = (spark && spark[tl.id]) || [];
    return `<button type="button" class="tile st-${esc(st)}${focusView === tl.view ? " is-focus" : ""}" data-view="${esc(tl.view)}"
        aria-label="${esc(tText("{{label}}: {{state}} — open the view", { label: tText(tl.label), state: tText(st) }))}">
      <span class="tl-h"><span class="nm">${esc(tText(tl.label))}</span>${st !== "ok" && st !== "injected" && STATE_CHIP[st] ? STATE_CHIP[st]() : ""}</span>
      <span class="tl-v"><span class="k">${esc(tText(tl.headline))}</span>${v}</span>
      <span class="tl-f">${renderSparkline(s, { w: 84, h: 16 })}<span class="bd">${badges.join("")}</span></span>
      ${tl.id !== "obdh" && tl.note ? `<span class="tl-n">${esc(tText(tl.note))}</span>` : ""}
    </button>`;
  }).join("");
  const o = ov.orbit || {};
  const ribbon = `<div class="tile ribbon" role="group" aria-label="${esc(tText("Orbit and contact"))}">
    <span class="tl-h"><span class="nm">${t("Orbit")}</span></span>
    <span class="rb">${o.contact ? renderChip({ kind: "active", label: tText("Downlink") + (o.station ? " · " + o.station : "") })
      : renderChip({ kind: "off", label: tText("No downlink") })}
      ${o.override ? `<span class="inj-chip">${t("pass override")}</span>` : ""}</span>
    <span class="rb">${renderChip({ kind: "neutral", label: o.in_eclipse ? tText("Eclipse") : tText("Sunlit") })}</span>
  </div>`;
  return tiles + ribbon;
}

/* ── 2. truth vs trainee (divergence) ──────────────────────────────────── */

const CAUSE_TEXT = {
  injected: "Injected indication fault",
  estimator: "Spacecraft estimate or clock off",
  delay: "Ground does not have it yet",
};
// i18n-keys
export const CAUSE_KEYS = ["Injected indication fault", "Spacecraft estimate or clock off",
  "Ground does not have it yet", "In agreement"];

function enumName(r, v) {
  if (v === null || v === undefined) return null;
  return (r.enum_names && r.enum_names[String(v)]) || String(v);
}

function cellVal(r, v) {
  if (r.kind === "enum") return v === null || v === undefined ? nd() : mono(enumName(r, v));
  if (r.unit === "s" && fin(v) && Math.abs(v) >= 3600) return `<span class="ds-value">${esc(fmtOffset(v))}</span>`;
  return num(v, r.digits, r.unit);
}

function gapHtml(r) {
  if (r.kind === "enum") return "";
  const parts = [];
  const eps = 0.5 * Math.pow(10, -(r.digits || 0));
  if (r.unit === "s" && fin(r.onboard_err) && Math.abs(r.onboard_err) >= 3600) return "";
  if (fin(r.onboard_err) && Math.abs(r.onboard_err) >= eps) parts.push(`${tText("on board")} ${r.onboard_err > 0 ? "+" : ""}${Number(r.onboard_err).toFixed(r.digits)}`);
  if (fin(r.ground_lag) && Math.abs(r.ground_lag) >= eps) parts.push(`${tText("ground")} ${r.ground_lag > 0 ? "+" : ""}${Number(r.ground_lag).toFixed(r.digits)}`);
  return parts.length ? `<span class="gap">${esc(parts.join(" · "))}</span>` : "";
}

export function pairRow(r) {
  const cause = r.state === "diverged" ? r.cause : null;
  const age = r.ground_kind === "none" ? `<span class="age">${t("not observable on the ground")}</span>`
    : fin(r.ground_age_s) ? `<span class="age${r.late ? " late" : ""}">${esc(fmtAge(r.ground_age_s))}${r.ground_via === "playback" ? " · " + esc(tText("played back")) : ""}</span>` : "";
  const ground = r.ground_kind === "none" ? `<span class="dim">—</span>` : cellVal(r, r.ground);
  return `<tr class="pr${cause ? " c-" + cause : ""}" data-pair="${esc(r.id)}">
    <th scope="row"><span class="pl">${esc(tText(r.label))}</span>${r.param ? `<span class="pid">${esc(r.param)}</span>` : ""}</th>
    <td class="v truth">${cellVal(r, r.truth)}</td>
    <td class="v">${cellVal(r, r.onboard)}</td>
    <td class="v">${ground}${age}</td>
    <td class="c">${cause ? `<span class="cause cause-${cause}">${esc(tText(cause === "injected" ? "injected" : cause === "estimator" ? "estimate" : "delay"))}</span>` : ""}${gapHtml(r)}
      ${cause && r.reason ? `<span class="why">${esc(r.reason_t ? tText(r.reason_t.key, r.reason_t.vars) : tText(r.reason))}</span>` : ""}</td>
  </tr>`;
}

export function pairTable(rows, opts = {}) {
  if (!rows || !rows.length) return `<div class="no-data">${t("No compared values for this view.")}</div>`;
  return `<table class="pairs"><thead><tr><th scope="col">${t("Quantity")}</th>
    <th scope="col">${t("Truth")}</th><th scope="col">${t("Spacecraft")}</th>
    <th scope="col">${t("Ground (age)")}</th><th scope="col">${opts.causeHead || t("Gap and cause")}</th></tr></thead>
    <tbody>${rows.map(pairRow).join("")}</tbody></table>`;
}

export function renderDivergence(div) {
  if (!div || !div.rows) return `<div class="no-data">${t("Waiting for the first truth snapshot…")}</div>`;
  const groups = { injected: [], estimator: [], delay: [], ok: [] };
  for (const r of div.rows) groups[r.state === "diverged" && r.cause ? r.cause : "ok"].push(r);
  const s = div.summary || { by_cause: {} };
  const head = `<div class="div-sum">
    <span class="cause cause-injected">${esc(tText("injected"))} ${s.by_cause.injected || 0}</span>
    <span class="cause cause-estimator">${esc(tText("estimate"))} ${s.by_cause.estimator || 0}</span>
    <span class="cause cause-delay">${esc(tText("delay"))} ${s.by_cause.delay || 0}</span>
    <span class="note">${div.ground_last_rx == null ? t("The ground has received no housekeeping yet.")
      : t("Last housekeeping reached the ground {{age}} ago.", { age: fmtAge(div.ground_last_rx) })}</span></div>
    <p class="lede">${t("Truth is the simulator's state. Spacecraft is what the spacecraft measures or estimates. Ground is the last value in downlinked housekeeping — what the trainees can know.")}</p>`;
  const sec = (key, title, open) => groups[key].length
    ? `<details class="ds-disclosure grp grp-${key}"${open ? " open" : ""}><summary><span class="ti">${esc(tText(title))}</span><span class="r">${groups[key].length}</span></summary><div class="bd">${pairTable(groups[key])}</div></details>`
    : "";
  return head + sec("injected", CAUSE_TEXT.injected, true) + sec("estimator", CAUSE_TEXT.estimator, true)
    + sec("delay", CAUSE_TEXT.delay, groups.injected.length + groups.estimator.length === 0)
    + sec("ok", "In agreement", false);
}

/* ── 3. thermal network ────────────────────────────────────────────────── */

const TH_POS = {
  panel_pz: [390, 28], wing_my: [70, 80], panel_my: [210, 80], panel_py: [570, 80], wing_py: [710, 80],
  obc: [270, 138], battery: [510, 138], panel_mx: [70, 190], structure: [390, 190], panel_px: [710, 190],
  ttc: [250, 246], aocs: [540, 242], prop: [130, 290], payload: [540, 298],
  thruster: [70, 336], panel_mz: [390, 330], fpa: [710, 336],
};
// English text is the i18n key
const TH_NAME = {
  panel_pz: "+Z panel", panel_my: "−Y panel", wing_my: "−Y wing", panel_py: "+Y panel", wing_py: "+Y wing",
  panel_mx: "−X panel", obc: "OBC", structure: "Structure", battery: "Battery", panel_px: "+X panel",
  ttc: "TT&C", aocs: "AOCS", prop: "Propulsion", thruster: "Catalyst bed", panel_mz: "−Z radiator",
  payload: "Payload", fpa: "FPA",
};
const TH_LIM = { obc: [-20, -10, 50, 60], battery: [0, 5, 35, 40], thruster: [-5, 5, 120, 150] };

function thLevel(id, v) {
  const l = TH_LIM[id];
  if (!l || !fin(v)) return "";
  if (v < l[0] || v > l[3]) return "alarm";
  if (v < l[1] || v > l[2]) return "caution";
  return "";
}

export function renderThermal(th) {
  if (!th || !th.available) return `<div class="no-data">${t("No thermal network in this simulator.")}</div>`;
  const nodes = Object.fromEntries((th.nodes || []).map((n) => [n.id, n]));
  const heat = Object.fromEntries((th.heaters || []).map((h) => [h.node, h]));
  const out = [];
  out.push(`<defs><marker id="th-arr" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L8 4L0 8Z" class="th-arrh"/></marker></defs>`);
  for (const l of th.links || []) {
    const a = TH_POS[l.a], b = TH_POS[l.b];
    if (!a || !b) continue;
    const w = Number(l.w) || 0;
    const [p, q] = w >= 0 ? [a, b] : [b, a];
    const sw = Math.min(7, 0.8 + Math.abs(w) * 1.2);
    const mx = (p[0] + q[0]) / 2, my = (p[1] + q[1]) / 2;
    const tip = `${tText(TH_NAME[l.a] || l.a)} ↔ ${tText(TH_NAME[l.b] || l.b)}: ${Math.abs(w).toFixed(2)} W ${l.kind === "rad" ? tText("radiated") : tText("conducted")}`;
    out.push(`<g class="th-link ${l.kind}${Math.abs(w) < 0.05 ? " is-zero" : ""}"><line x1="${p[0]}" y1="${p[1]}" x2="${q[0]}" y2="${q[1]}" stroke-width="${sw.toFixed(2)}"/>` +
      (Math.abs(w) >= 0.05 ? `<line class="th-dir" x1="${(p[0] + mx) / 2}" y1="${(p[1] + my) / 2}" x2="${mx}" y2="${my}" marker-end="url(#th-arr)"/>` : "") +
      `<title>${esc(tip)}</title></g>`);
  }
  for (const [id, pos] of Object.entries(TH_POS)) {
    const n = nodes[id];
    if (!n) continue;
    const lv = thLevel(id, n.t);
    const h = heat[id];
    const [x, y] = pos;
    const lbl = tText(TH_NAME[id] || id);
    out.push(`<g class="th-node${lv ? " is-" + lv : ""}" transform="translate(${x - 58} ${y - 16})">
      <rect width="116" height="32" rx="2"/>
      <text class="nm" x="6" y="13">${esc(lbl)}</text>
      <text class="val" x="110" y="27" text-anchor="end">${fin(n.t) ? Number(n.t).toFixed(1) + " °C" : "—"}</text>
      ${n.published ? `<text class="pub" x="6" y="27">${esc(n.published)}</text>` : ""}
      ${h ? `<text class="htr${h.on ? " on" : ""}${h.failed || h.stuck_on || h.open_circuit ? " bad" : ""}" x="110" y="13" text-anchor="end">${esc(h.failed ? tText("HTR failed") : h.stuck_on ? tText("HTR stuck on") : h.open_circuit ? tText("HTR open") : h.on ? tText("HTR on") : tText("HTR off"))}</text>` : ""}
      <title>${esc(`${lbl}: ${fin(n.t) ? Number(n.t).toFixed(2) + " °C" : tText("no data")}`)}</title>
    </g>`);
    if (fin(n.sensor_offset) && Math.abs(n.sensor_offset) > 0.001) {
      out.push(`<g class="th-lie" transform="translate(${x - 58} ${y + 18})"><rect width="76" height="18" rx="2"/>
        <text x="38" y="13" text-anchor="middle">TM ${n.sensor_offset > 0 ? "+" : ""}${Number(n.sensor_offset).toFixed(1)} K</text>
        <title>${esc(tText("Injected sensor offset: telemetry reads this much off the truth"))}</title></g>`);
    }
  }
  const heaters = (th.heaters || []).map((h) => `<li>${esc(tText(TH_NAME[h.node] || h.node))}: ${h.on ? t("on") : t("off")}${fin(h.duty_pct) ? ` · ${esc(tText("duty {{d}} %", { d: Number(h.duty_pct).toFixed(0) }))}` : ""}${h.failed ? " · " + t("failed") : ""}${h.stuck_on ? " · " + t("stuck on") : ""}${h.open_circuit ? " · " + t("open circuit") : ""}</li>`).join("");
  return `<div class="viewgrid">
    <figure class="fig"><svg class="th-svg" viewBox="0 0 780 372" role="img" aria-label="${esc(tText("Thermal network truth: node temperatures and heat flows"))}">${out.join("")}</svg>
      <figcaption>${t("Node temperatures are the simulator's truth. Line width is the heat flowing (W), the arrow its direction. A lilac tag is an injected sensor offset.")}</figcaption></figure>
    <div class="side"><h3>${t("Heaters")}</h3><ul class="plain">${heaters}</ul>
      <div class="kv"><span>${t("Heater power")}</span>${num(th.heater_power_w, 1, "W")}</div>
      <div class="kv"><span>${t("FPA cooler")}</span>${th.cooler && th.cooler.failed ? renderChip({ kind: "alarm", label: tText("failed") }) : th.cooler && th.cooler.on ? renderChip({ kind: "neutral", label: tText("on") }) : renderChip({ kind: "off", label: tText("off") })}</div>
    </div></div>`;
}

/* ── 4. attitude: truth body, estimate ghost ───────────────────────────── */

/** One scale for the three tapes, so equal lengths mean equal angles. */
export function tapeScale(values) {
  const m = Math.max(0, ...values.filter(fin).map((v) => Math.abs(v)));
  return [0.05, 0.2, 1, 5, 20, 90, 180].find((s) => s >= m * 1.15) || 180;
}

function tape(label, truthV, estV, full) {
  const W = 280, H = 30, x = (v) => 10 + ((v + full) / (2 * full)) * (W - 20);
  const ticks = [-full, -full / 2, 0, full / 2, full].map((v) =>
    `<line class="tp-t" x1="${x(v)}" x2="${x(v)}" y1="11" y2="${v === 0 ? 25 : 19}"/>`).join("");
  return `<div class="tape"><span class="k">${esc(label)}</span>
    <svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" aria-hidden="true">
      <line class="tp-ax" x1="10" x2="${W - 10}" y1="15" y2="15"/>${ticks}
      ${fin(estV) ? `<circle class="tp-est" cx="${x(estV)}" cy="15" r="5.5"/>` : ""}
      ${fin(truthV) ? `<path class="tp-true" d="M${x(truthV)} 9L${x(truthV) + 5} 18L${x(truthV) - 5} 18Z"/>` : ""}
      <text class="tp-s" x="${W - 10}" y="29" text-anchor="end">±${full}°</text></svg>
    <span class="vv">${fin(truthV) ? mono(Number(truthV).toFixed(3) + "°") : nd()}<span class="dim"> / ${fin(estV) ? esc(Number(estV).toFixed(3) + "°") : "—"}</span></span></div>`;
}

const ST_NAMES = { 0: "OFF", 1: "BOOTING", 2: "TRACKING", 3: "BLIND", 4: "FAILED" };

export function renderAttitude(a, hist) {
  if (!a || !a.available) return `<div class="no-data">${t("No AOCS model in this simulator.")}</div>`;
  const rt = a.rpy_true || [], re = a.rpy_est || [];
  const rates = ["roll", "pitch", "yaw"].map((ax, i) => `<tr><th scope="row">${esc(tText(ax))}</th>
    <td>${num(a.rates_true && a.rates_true[i], 4, "°/s")}</td><td>${num(a.rates_est && a.rates_est[i], 4, "°/s")}</td></tr>`).join("");
  const wheels = (a.wheels || []).map((w) => {
    const frac = fin(w.rpm) ? Math.min(1, Math.abs(w.rpm) / 5500) : 0;
    return `<div class="wh"><span class="k">${esc(w.id)}</span><span class="bar"><span style="width:${(frac * 100).toFixed(0)}%"></span></span>${num(w.rpm, 0, "rpm")}<span>${w.enabled === false ? renderChip({ kind: "off", label: tText("disabled") }) : ""}</span></div>`;
  }).join("");
  const inj = (a.gyro_bias_injected || []).some((v) => fin(v) && Math.abs(v) > 0);
  return `<div class="viewgrid">
    <section class="fig"><h3>${t("Roll, pitch, yaw against the commanded attitude")}</h3>
      <div class="legend"><span class="lg-true"></span>${t("truth")}<span class="lg-est"></span>${t("on-board estimate")}</div>
      ${(() => { const sc = tapeScale([...rt, ...re]); return tape(tText("Roll"), rt[0], re[0], sc) + tape(tText("Pitch"), rt[1], re[1], sc) + tape(tText("Yaw"), rt[2], re[2], sc); })()}
      <div class="sparks"><div><span class="k">${t("Pointing error, truth")}</span>${renderSparkline((hist && hist.point) || [], { w: 180, h: 28, min: 0 })}${num(a.point_err_true, 3, "°")}</div>
        <div><span class="k">${t("Knowledge error (estimate vs truth)")}</span>${renderSparkline((hist && hist.know) || [], { w: 180, h: 28, min: 0 })}${num(a.knowledge_err, 3, "°")}</div></div>
    </section>
    <div class="side">
      <div class="kv"><span>${t("AOCS mode")}</span>${mono(a.mode_name)}</div>
      ${a.mode_change_reason ? `<div class="kv"><span>${t("Last mode change")}</span><span class="why">${esc(a.mode_change_reason)}</span></div>` : ""}
      <div class="kv"><span>${t("Pointing error (estimate)")}</span>${num(a.point_err_est, 3, "°")}</div>
      <div class="kv"><span>${t("Knowledge 3σ (on board)")}</span>${num(a.knowledge_3sig_arcsec, 0, "″")}</div>
      <div class="kv"><span>${t("Estimate source")}</span>${a.est_source ? mono(a.est_source) : nd()}</div>
      <div class="kv"><span>${t("Star trackers")}</span>${mono((a.st_status || []).map((s) => ST_NAMES[s] || s).join(" / "))}</div>
      <div class="kv"><span>${t("Sun sensors / magnetometer")}</span>${mono((a.css_valid ? "OK" : "INVALID") + " / " + (a.mag_valid ? "OK" : "INVALID"))}</div>
      ${inj ? `<div class="kv"><span>${t("Injected gyro bias")}</span><span class="inj-chip">${esc((a.gyro_bias_injected || []).map((v) => Number(v).toFixed(3)).join(" / "))} °/s</span></div>` : ""}
      <table class="mini"><thead><tr><th></th><th scope="col">${t("truth")}</th><th scope="col">${t("estimate")}</th></tr></thead><tbody>${rates}</tbody></table>
      <h3>${t("Reaction wheels")}</h3>${wheels}
    </div></div>`;
}

/* ── 5. orbit, visibility and link ─────────────────────────────────────── */

export function renderOrbit(o, nowTs) {
  if (!o) return "";
  // The downlink gates are a SET, not a sequence: every one must hold.
  const chain = `<ul class="gates">${(o.chain || []).map((c) => `<li class="${c.ok ? "ok" : "blocked"}">` +
    renderChip(c.ok ? { kind: "ok", label: tText(c.label) } : { kind: "alarm", label: tText(c.label), glyph: "off" }) +
    (c.note ? ` <span class="inj-chip">${esc(tText(c.note))}</span>` : "") + `</li>`).join("")}</ul>`;
  let why;
  if (o.downlink && o.override && !o.geometric_contact) why = tText("The operators have a link only because of the pass override: no station is in view.");
  else if (o.downlink) why = tText("Downlink up through {{gs}}.", { gs: o.station || tText("a station") });
  else if (o.beacon_only) why = tText("Bootloader: only the UHF beacon is on the air.");
  else {
    const first = (o.chain || []).find((c) => !c.ok);
    why = first ? tText("No downlink: {{gate}} is not met.", { gate: tText(first.label) }) : tText("No downlink.");
  }
  const H = 4 * 3600, W = 520, x = (ts) => 8 + ((ts - nowTs) / H) * (W - 16);
  const rows = {};
  for (const c of o.contacts || []) (rows[c.station] = rows[c.station] || []).push(c);
  const names = Object.keys(rows);
  const bars = names.map((n, i) => {
    const y = 18 + i * 18;
    const segs = rows[n].map((c) => {
      const a = Date.parse(c.aos) / 1000, b = Date.parse(c.los) / 1000;
      const xa = Math.max(8, x(a)), xb = Math.min(W - 8, x(b));
      return xb > xa ? `<rect class="ps" x="${xa.toFixed(1)}" y="${y}" width="${(xb - xa).toFixed(1)}" height="10"><title>${esc(`${n} ${c.aos.slice(11, 19)}–${c.los.slice(11, 19)} · ${tText("max el {{e}}°", { e: c.max_el })}`)}</title></rect>` : "";
    }).join("");
    return `<text class="pn" x="${W + 6}" y="${y + 9}">${esc(n)}</text>${segs}`;
  }).join("");
  const hours = [0, 1, 2, 3, 4].map((h) => `<line class="tp-t" x1="${x(nowTs + h * 3600)}" x2="${x(nowTs + h * 3600)}" y1="10" y2="${22 + names.length * 18}"/><text class="tp-s" x="${x(nowTs + h * 3600)}" y="8" text-anchor="middle">+${h} h</text>`).join("");
  const nextEcl = o.in_eclipse ? tText("eclipse exit in {{t}}", { t: fmtAge(o.time_to_eclipse_exit_s) }) : tText("eclipse entry in {{t}}", { t: fmtAge(o.time_to_eclipse_entry_s) });
  return `<div class="viewgrid">
    <section class="fig"><h3>${t("Why the operators have, or do not have, a link")}</h3>
      <p class="lede">${esc(why)}</p>${chain}
      <h3>${t("Contacts in the next 4 hours (truth geometry)")}</h3>
      ${names.length ? `<svg class="passes" viewBox="0 0 ${W + 90} ${28 + names.length * 18}" role="img" aria-label="${esc(tText("Contact windows"))}">${hours}${bars}</svg>` : `<div class="no-data">${t("No contact in the next 4 hours.")}</div>`}
    </section>
    <div class="side">
      <div class="kv"><span>${t("Station in view")}</span>${o.geometric_contact ? mono(o.station) : `<span class="dim">${t("none")}</span>`}</div>
      <div class="kv"><span>${t("Elevation")}</span>${o.geometric_contact ? num(o.elevation_deg, 1, "°") : `<span class="dim">${t("no geometry")}</span>`}</div>
      <div class="kv"><span>${t("Range")}</span>${o.geometric_contact ? num(o.range_km, 0, "km") : `<span class="dim">${t("no geometry")}</span>`}</div>
      <div class="kv"><span>${t("Pass override")}</span>${o.override ? `<span class="inj-chip">${t("ON")}</span>` : mono(tText("off"))}</div>
      <div class="kv"><span>${t("Downlink / uplink")}</span>${mono((o.downlink ? "UP" : "DOWN") + " / " + (o.uplink ? "UP" : "DOWN"))}</div>
      <div class="kv"><span>${t("Link margin")}</span>${o.margin_db == null ? `<span class="dim">${t("no link")}</span>` : num(o.margin_db, 1, "dB")}</div>
      <div class="kv"><span>${t("TM rate")}</span>${o.tm_rate_bps ? mono(`${o.tm_rate_bps} bps · ${o.tm_tier || ""}`) : nd()}</div>
      <div class="kv"><span>${t("Sun")}</span>${mono(o.in_eclipse ? tText("eclipse") : tText("sunlit"))}<span class="dim"> · ${esc(nextEcl)}</span></div>
      <div class="kv"><span>${t("Position")}</span>${mono(`${fx(o.lat, 2)}°, ${fx(o.lon, 2)}° · ${fx(o.alt_km, 0)} km`)}</div>
      <div class="kv"><span>${t("Last HK on the ground")}</span>${o.ground_last_rx_s == null ? `<span class="dim">${t("never")}</span>` : mono(tText("{{age}} ago", { age: fmtAge(o.ground_last_rx_s) }))}</div>
    </div></div>`;
}

/* ── 6. OBC modes and FDIR ─────────────────────────────────────────────── */

const PHASES = ["PRE_SEPARATION", "SEPARATION_TIMER", "INITIAL_POWER_ON", "BOOTLOADER_OPS", "LEOP", "COMMISSIONING", "NOMINAL"];
const SC_MODES = { 0: "SAFE", 1: "NOMINAL", 2: "SCIENCE", 3: "EMERGENCY" };
const OBDH = { 0: "NOMINAL", 1: "SAFE", 2: "EMERGENCY" };

export function renderObc(o, modeRows) {
  if (!o) return "";
  const phase = renderStepper(PHASES.map((p) => ({ label: p })), o.phase);
  const tr = (o.transitions || []).slice().reverse().map((i) => `<li><span class="mono dim">${esc(fmtClockSec(i.ts))}</span> ${esc(i.text)}${i.trigger ? ` <span class="why">${esc(tText("trigger: {{t}}", { t: i.trigger }))}</span>` : ""}</li>`).join("");
  const fd = o.fdir || {};
  const rec = (fd.recovery || []).map((r) => `<li>${mono(r.fault_id)} · ${esc(r.group || "")} L${esc(r.level)} · ${esc(r.state || "")}${r.procedure ? " · " + mono(r.procedure) : ""} (${esc(r.attempts)}/${esc(r.max_attempts)})</li>`).join("");
  const procs = (fd.procedures || []).map((p) => `<li>${mono(p.proc_id)} · ${esc(tText("step {{a}}/{{b}}", { a: p.completed_steps, b: p.total_steps }))} · ${esc(p.state)}</li>`).join("");
  return `<div class="viewgrid">
    <section class="fig"><h3>${t("Mission phase")}</h3>${phase}
      <h3>${t("Modes: truth and what the ground has")}</h3>
      ${pairTable(modeRows || [], { causeHead: t("Cause") })}
      <p class="note">${t("sat.mode is the derived spacecraft mode: SAFE until the spacecraft is commissioned (phase NOMINAL) or while an FDIR safe contingency is latched. obdh.mode is the OBC application's own mode. They are different quantities; both are correct.")}</p>
      <h3>${t("Last transitions and what triggered them")}</h3>
      ${tr ? `<ul class="plain trans">${tr}</ul>` : `<div class="no-data">${t("No transition yet in this run.")}</div>`}
    </section>
    <div class="side">
      <div class="kv"><span>${t("Spacecraft mode")}</span>${mono(SC_MODES[o.sc_mode] || o.sc_mode)}</div>
      <div class="kv"><span>${t("OBC")}</span>${mono((OBDH[o.obdh_mode] || o.obdh_mode) + " · " + (o.sw_image ? tText("application") : tText("bootloader")))}</div>
      <div class="kv"><span>${t("CPU / memory")}</span>${mono(`${fx(o.cpu, 0) ?? "?"} % / ${fx(o.mem, 0) ?? "?"} %`)}</div>
      <div class="kv"><span>${t("Reboots")}</span>${mono(String(o.reboots ?? "?"))}</div>
      <div class="kv"><span>${t("CAN bus")}</span>${mono(o.active_bus === 1 ? "B" : "A")}</div>
      <h3>${t("FDIR")}</h3>
      <div class="kv"><span>${t("Level / load shed")}</span>${mono(`${fd.level ?? 0} / ${fd.load_shed_stage ?? 0}`)}</div>
      <div class="kv"><span>${t("Triggered rules")}</span>${(fd.triggered || []).length ? mono((fd.triggered || []).join(", ")) : `<span class="dim">${t("none")}</span>`}</div>
      ${rec ? `<h3>${t("Recoveries")}</h3><ul class="plain">${rec}</ul>` : ""}
      ${procs ? `<h3>${t("On-board procedures")}</h3><ul class="plain">${procs}</ul>` : ""}
    </div></div>`;
}

/* ── 7. storage ────────────────────────────────────────────────────────── */

export function renderStorage(s) {
  if (!s) return "";
  const bars = (s.stores || []).map((st) => {
    const f = fin(st.fill_pct) ? Number(st.fill_pct) : 0;
    const lvl = f >= 95 ? " is-alarm" : f >= 80 ? " is-caution" : "";
    return `<div class="store${lvl}"><span class="k">${esc(st.name)}</span><span class="bar"><span style="width:${Math.min(100, f).toFixed(0)}%"></span></span>
      <span class="mono">${esc(f.toFixed(1))} %</span><span class="dim">${esc(`${st.count}/${st.capacity}`)}${st.enabled ? "" : " · " + esc(tText("disabled"))}${st.overflow ? " · " + esc(tText("overflow")) : ""}</span></div>`;
  }).join("");
  const p = s.payload || {};
  return `<div class="viewgrid">
    <section class="fig"><h3>${t("On-board packet stores (S15)")}</h3>${bars || `<div class="no-data">${t("No packet stores.")}</div>`}
      <h3>${t("Payload mass memory")}</h3>
      <div class="store"><span class="k">${t("Image store")}</span><span class="bar"><span style="width:${Math.min(100, Number(p.store_used_pct) || 0).toFixed(0)}%"></span></span>${num(p.store_used_pct, 1, "%")}<span class="dim">${esc(tText("{{n}} images", { n: p.image_count ?? 0 }))}${(p.bad_segments || []).length ? " · " + esc(tText("bad segments {{s}}", { s: p.bad_segments.join(", ") })) : ""}</span></div>
    </section>
    <div class="side">
      <div class="kv"><span>${t("Dump in progress")}</span>${s.dump_pending_packets ? mono(tText("{{n}} packets queued", { n: s.dump_pending_packets })) : `<span class="dim">${t("no")}</span>`}</div>
      <div class="kv"><span>${t("Real-time backlog")}</span>${mono(String(s.rt_backlog ?? 0))}</div>
      <div class="kv"><span>${t("TM packets dropped")}</span>${mono(String(s.tm_queue_drops ?? 0))}</div>
      <div class="kv"><span>${t("HK packets on the ground")}</span>${mono(`${s.ground ? s.ground.packets : 0} (${s.ground ? s.ground.playback_packets : 0} ${tText("played back")})`)}</div>
    </div></div>`;
}

/* ── 8. fault: causal chain + swimlane ─────────────────────────────────── */

export const STAGES = [
  { k: "inserted_ts", label: "Inserted" },
  { k: "symptom_ts", label: "First on-board symptom" },
  { k: "ground_ts", label: "Alarm reached the ground" },
  { k: "response_ts", label: "First telecommand after it" },
  { k: "cleared_ts", label: "Cleared" },
];
// i18n-keys
export const STAGE_KEYS = ["Inserted", "First on-board symptom", "Alarm reached the ground",
  "First telecommand after it", "Cleared"];

export function renderFaultLane(f, nowTs) {
  const t0 = f.inserted_ts;
  const tEnd = Math.max(nowTs, ...STAGES.map((s) => f[s.k] || 0));
  const span = Math.max(60, tEnd - t0);
  const W = 520, x = (ts) => 10 + ((ts - t0) / span) * (W - 20);
  const marks = STAGES.map((s, i) => {
    const ts = f[s.k];
    if (!fin(ts)) return "";
    return `<g class="sl-m sl-${i}"><line x1="${x(ts)}" x2="${x(ts)}" y1="8" y2="34"/><circle cx="${x(ts)}" cy="21" r="5"/><title>${esc(tText(s.label) + " · T+" + fmtAge(ts - t0))}</title></g>`;
  }).join("");
  const gaps = [];
  for (let i = 1; i < STAGES.length; i++) {
    const a = f[STAGES[i - 1].k], b = f[STAGES[i].k];
    if (fin(a) && fin(b) && b > a) gaps.push(`<text class="sl-gap" x="${(x(a) + x(b)) / 2}" y="46" text-anchor="middle">${esc(fmtAge(b - a))}</text>`);
  }
  const rows = STAGES.map((s) => `<li class="${fin(f[s.k]) ? "done" : ""}"><span class="k">${esc(tText(s.label))}</span>${fin(f[s.k]) ? mono(`${fmtClockSec(f[s.k])} · T+${fmtAge(f[s.k] - t0)}`) : `<span class="dim">${t("not yet")}</span>`}</li>`).join("");
  return `<svg class="swim" viewBox="0 0 ${W} 52" role="img" aria-label="${esc(tText("Fault swimlane"))}"><line class="sl-ax" x1="10" x2="${W - 10}" y1="21" y2="21"/>
    <line class="sl-now" x1="${x(nowTs)}" x2="${x(nowTs)}" y1="4" y2="38"/>${marks}${gaps.join("")}</svg><ol class="stages">${rows}</ol>`;
}

export function renderChain(f) {
  return `<div class="chain" role="list">
    <div class="ch-box ch-comp" role="listitem"><span class="k">${t("Component")}</span><b>${esc(f.subsystem.toUpperCase())} · ${esc(f.failure)}</b>
      <span class="dim">${esc(tText(f.element_label || f.element))} · ${esc(f.inject_class === "indication" ? tText("indication (sensor lie)") : tText("physical"))}</span></div>
    <span class="ch-arr" aria-hidden="true">→</span>
    <div class="ch-box" role="listitem"><span class="k">${t("Degrades")}</span><b>${esc(tText(f.function))}</b></div>
    <span class="ch-arr" aria-hidden="true">→</span>
    <div class="ch-box" role="listitem"><span class="k">${t("Mission objective at risk")}</span><b>${esc(tText(f.objective))}</b></div>
  </div>`;
}

export function renderFault(f, nowTs) {
  if (!f) return `<div class="no-data">${t("No inject in this run yet. Injects appear here with their causal chain and swimlane.")}</div>`;
  return `<section class="fig fault"><h3>${esc(`${f.subsystem.toUpperCase()} / ${f.failure}`)} ${f.cleared_ts ? renderChip({ kind: "off", label: tText("cleared") }) : `<span class="inj-chip">${t("active")}</span>`}</h3>
    ${renderChain(f)}<h3>${t("Swimlane: the gaps are the team's performance measures")}</h3>${renderFaultLane(f, nowTs)}</section>`;
}
