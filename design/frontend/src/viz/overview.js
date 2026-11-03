/* ============================================================================
 * C2O pictorial displays — overview.js  (source: shared/ui-viz/overview.js)
 * ============================================================================
 * Spacecraft synoptic: the subsystem blocks placed on a plain outline of the
 * spacecraft as seen from ahead (velocity towards the viewer), +Z zenith up,
 * the imager boresight and antenna down towards the Earth, the two wings on
 * ±Y. Each block carries the worst state of its subsystem (shape + word +
 * colour), one or two interpreted values against their limits, and is a link
 * to the subsystem page. A mode ladder sits above the outline.
 *
 * Calm at rest: every block is grey with grey values; a block changes only
 * when its subsystem is in caution, alarm, stale or never received.
 *
 *   mount(el, { t, onNavigate(subsystemId) }) -> { update(model), destroy() }
 *
 *   model = {
 *     mode:      { label: "NOMINAL", contingency: false, src: "TM obdh.mode 0x0300" },
 *     aocsMode:  "NOMINAL",            eclipse: true|false|null,
 *     contact:   true|false,           gs: "Svalbard",
 *     deploy:    deriveDeployment() (derive.js): antenna stowed / deployed /
 *                jammed, each wing stowed or deployed and sunlit or dark,
 *                the six body faces, the on-board string-lit flags. Each
 *                item carries its verdict (fresh / stale / no data).
 *     subsystems: { eps|aocs|obdh|tcs|prop|payload|ttc: {
 *        state: "nominal"|"caution"|"alarm"|"stale"|"nodata",
 *        alarms: { a: 0, w: 0 },
 *        rows: [{ label, q: quantity, digits, limits: {red_low, yellow_low, yellow_high, red_high} }] } } }
 * ============================================================================ */
import { esc, fmt, fmtDur, withUnit, stateClass, s, mountFrame, valuesTable, readout,
  tDefault, uid, ensureStyle, fin } from "./common.js";

const CSS = `
.vz-ov .o-bus{fill:var(--vz-s1);stroke:var(--vz-tx3);stroke-width:1.25}
.vz-ov .o-wing{fill:var(--vz-s2);stroke:var(--vz-tx3);stroke-width:1}
.vz-ov .o-wing.is-dark{fill:var(--vz-bg)}
.vz-ov .o-cell{stroke:var(--vz-line2);stroke-width:1}
.vz-ov .o-yoke{stroke:var(--vz-tx3);stroke-width:2}
.vz-ov .o-earth{fill:var(--vz-s2);stroke:var(--vz-line2)}
.vz-ov .o-axis{stroke:var(--vz-tx3);stroke-width:1;fill:none}
.vz-ov .o-axhead{fill:var(--vz-tx3)}
.vz-ov .o-bore{stroke:var(--vz-tx3);stroke-width:1;stroke-dasharray:4 4;fill:none}
.vz-ov .o-dev{fill:var(--vz-s2);stroke:var(--vz-tx3);stroke-width:1}
.vz-ov .o-blk{cursor:pointer}
.vz-ov .o-blk rect.o-bx{fill:var(--vz-bg);stroke:var(--vz-line2);stroke-width:1}
.vz-ov .o-blk:hover rect.o-bx,.vz-ov .o-blk:focus-visible rect.o-bx{stroke:var(--vz-accent);stroke-width:1.5}
.vz-ov .o-blk:focus-visible{outline:none}
.vz-ov .o-blk.is-caution rect.o-bx{stroke:var(--vz-warn);stroke-width:1.5;fill:var(--vz-warn-wash)}
.vz-ov .o-blk.is-alarm rect.o-bx{stroke:var(--vz-alarm);stroke-width:2;fill:var(--vz-alarm-wash)}
.vz-ov .o-blk.is-stale rect.o-bx,.vz-ov .o-blk.is-nodata rect.o-bx{stroke:var(--vz-stale);stroke-dasharray:4 3}
.vz-ov .o-st{font-size:12px;font-weight:600;fill:var(--vz-tx3)}
.vz-ov .is-caution .o-st{fill:var(--vz-warn)} .vz-ov .is-alarm .o-st{fill:var(--vz-alarm)}
.vz-ov .gl-caution{fill:none;stroke:var(--vz-warn);stroke-width:1.5}
.vz-ov .gl-alarm{fill:var(--vz-alarm)}
.vz-ov .gl-stale{fill:none;stroke:var(--vz-stale);stroke-width:1.25;stroke-dasharray:2 2}
.vz-ov .o-mode rect{fill:var(--vz-bg);stroke:var(--vz-line2)}
.vz-ov .o-mode text{font-size:12px;fill:var(--vz-tx3)}
.vz-ov .o-mode.is-on rect{fill:var(--vz-accent);stroke:var(--vz-accent)}
.vz-ov .o-mode.is-on text{fill:var(--on-accent,var(--on-fill));font-weight:600}
.vz-ov .o-mode.is-on.is-alarm rect{fill:var(--vz-alarm-wash);stroke:var(--vz-alarm);stroke-width:2}
.vz-ov .o-mode.is-on.is-alarm text{fill:var(--vz-alarm)}
.vz-ov .o-link{stroke:var(--vz-line2);stroke-width:1}
.vz-ov .o-list{list-style:none;margin:0;padding:0;display:grid;gap:var(--sp-2)}
.vz-ov .o-modes{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:var(--sp-2);font-size:var(--fs-label);color:var(--vz-tx3);align-items:center}
.vz-ov .o-modes span{border:1px solid var(--vz-line2);border-radius:var(--radius-sm);padding:0 6px;line-height:20px}
.vz-ov .o-modes span.is-on{background:var(--vz-accent);border-color:var(--vz-accent);color:var(--on-accent,var(--on-fill));font-weight:600}
.vz-ov .o-modes span.o-mlab{border:0;padding-left:0}
.vz-ov .o-tile{display:block;width:100%;text-align:left;font:inherit;color:inherit;background:var(--vz-bg);
  border:1px solid var(--vz-line2);border-radius:var(--radius);padding:var(--sp-2) var(--sp-3);cursor:pointer}
.vz-ov .o-tile:hover{border-color:var(--vz-accent)}
.vz-ov .o-tile.is-caution{border-color:var(--vz-warn);background:var(--vz-warn-wash)}
.vz-ov .o-tile.is-alarm{border-color:var(--vz-alarm);border-width:2px;background:var(--vz-alarm-wash)}
.vz-ov .o-tile.is-stale,.vz-ov .o-tile.is-nodata{border-style:dashed;border-color:var(--vz-stale)}
.vz-ov .o-th{display:flex;justify-content:space-between;gap:var(--sp-2);font-weight:600;color:var(--vz-tx)}
.vz-ov .o-th em{font-style:normal;font-size:var(--fs-label);color:var(--vz-tx3)}
.vz-ov .is-caution .o-th em{color:var(--vz-warn)} .vz-ov .is-alarm .o-th em{color:var(--vz-alarm)}
.vz-ov .o-tr{display:flex;justify-content:space-between;gap:var(--sp-2);font-size:var(--fs-label);color:var(--vz-tx2);margin-top:2px}
.vz-ov .o-tr .vz-v{font-size:var(--fs-body)}
.vz-ov .o-wing.is-lit{fill:var(--vz-s3)}
.vz-ov .o-wing.is-nodata,.vz-ov .o-wing.is-unk{fill:none;stroke:var(--vz-stale);stroke-dasharray:4 3}
.vz-ov .o-wing.is-stale{stroke:var(--vz-stale);stroke-dasharray:4 3}
.vz-ov .o-stow{fill:var(--vz-s2);stroke:var(--vz-tx3);stroke-width:1}
.vz-ov .o-stow.is-stale,.vz-ov .o-ant.is-stale{stroke-dasharray:4 3;stroke:var(--vz-stale)}
.vz-ov .o-ghost{fill:none;stroke:var(--vz-line);stroke-width:1;stroke-dasharray:1 5}
.vz-ov .o-ant{fill:var(--vz-s2);stroke:var(--vz-tx3);stroke-width:1.25}
.vz-ov .o-ant.is-nodata{fill:none;stroke:var(--vz-stale);stroke-dasharray:4 3}
.vz-ov .o-ant.is-caution{stroke:var(--vz-warn);stroke-width:1.75}
.vz-ov .o-sun{fill:none;stroke:var(--vz-tx2);stroke-width:1.25}
.vz-ov .o-sun-c{fill:var(--vz-tx2)}
.vz-ov .t-lab.is-stale{font-style:italic}
.vz-ov .t-lab.is-caution{fill:var(--vz-warn);font-weight:600}
.vz-ov .o-sa{display:grid;grid-template-columns:auto minmax(0,1fr);gap:var(--sp-1) var(--sp-3);align-items:start;
  margin-top:var(--sp-2);padding-top:var(--sp-2);border-top:1px solid var(--vz-line);font-size:var(--fs-label);color:var(--vz-tx3)}
.vz-ov .o-sa .k{color:var(--vz-tx3);line-height:22px}
.vz-ov .o-faces{display:flex;flex-wrap:wrap;gap:4px;list-style:none;margin:0;padding:0}
.vz-ov .o-face{display:inline-flex;align-items:center;gap:4px;min-width:84px;line-height:20px;padding:0 6px;
  border:1px solid var(--vz-line2);border-radius:var(--radius-sm);color:var(--vz-tx2);background:var(--vz-bg)}
.vz-ov .o-face b{font-family:var(--vz-mono);font-weight:500;color:var(--vz-tx)}
.vz-ov .o-face.is-lit{background:var(--vz-s3);color:var(--vz-tx)}
.vz-ov .o-face.is-stale{border-style:dashed;border-color:var(--vz-stale);font-style:italic}
.vz-ov .o-face.is-nodata{border-style:dashed;border-color:var(--vz-stale)}
.vz-ov .o-face svg{flex:0 0 auto}
.vz-ov .o-legend{display:flex;flex-wrap:wrap;gap:var(--sp-1) var(--sp-3);list-style:none;margin:0;padding:0;line-height:22px}
.vz-ov .o-legend li{display:inline-flex;align-items:center;gap:6px}
.vz-ov .o-sw{display:inline-block;width:18px;height:10px;border:1px solid var(--vz-tx3);border-radius:1px;background:var(--vz-bg)}
.vz-ov .o-sw.is-lit{background:var(--vz-s3)}
.vz-ov .o-sw.is-stale{border-style:dashed;border-color:var(--vz-stale)}
.vz-ov .o-sw.is-nodata{border-style:dashed;border-color:var(--vz-stale);background:transparent}
.vz-ov .o-sw.is-stow{width:6px;height:14px;background:var(--vz-s2)}
.vz-ov .o-vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.vz-ov .o-blk.is-hidden{cursor:default}
.vz-ov .o-blk.is-hidden rect.o-bx{fill:none;stroke:var(--vz-line);stroke-dasharray:2 3}
`;

/* Block placement in the 900 × 420 drawing (inside the bus outline). */
const BUS = { x: 188, y: 84, w: 524, h: 300 };
const BLOCKS = {
  aocs:    { x: 200, y: 96,  w: 162, h: 88, name: "AOCS" },
  obdh:    { x: 370, y: 96,  w: 162, h: 88, name: "OBDH" },
  tcs:     { x: 540, y: 96,  w: 160, h: 88, name: "TCS" },
  eps:     { x: 200, y: 192, w: 332, h: 88, name: "EPS" },
  prop:    { x: 540, y: 192, w: 160, h: 88, name: "PROP" },
  payload: { x: 200, y: 288, w: 332, h: 84, name: "PAYLOAD" },
  ttc:     { x: 540, y: 288, w: 160, h: 84, name: "TT&C" },
};
const MODES = ["EMERGENCY", "SAFE", "NOMINAL", "SCIENCE"];

/** Position of a value on a limit bar [0..1] with the band edges. */
function band(lim, v) {
  if (!lim) return null;
  const rl = lim.red_low, rh = lim.red_high, yl = lim.yellow_low, yh = lim.yellow_high;
  const lo0 = Number.isFinite(rl) ? rl : yl, hi0 = Number.isFinite(rh) ? rh : yh;
  if (!Number.isFinite(lo0) || !Number.isFinite(hi0) || hi0 <= lo0) return null;
  const pad = (hi0 - lo0) * 0.12;
  const lo = lo0 - pad, hi = hi0 + pad;
  const f = (x) => (Number.isFinite(x) ? Math.max(0, Math.min(1, (x - lo) / (hi - lo))) : null);
  return { f, v: Number.isFinite(v) ? f(v) : null, rl: f(rl), rh: f(rh), yl: f(yl), yh: f(yh) };
}

export function mount(el, opts = {}) {
  const t = opts.t || tDefault;
  ensureStyle("c2o-viz-ov", CSS);
  const parts = mountFrame(el, { title: opts.title ?? "", t, cls: "vz-ov" });
  const tid = uid("ovt"), did = uid("ovd");
  let last = null;

  const stateWord = (st, al) => {
    if (st === "alarm") return t("ALARM") + (al && al.a ? ` ${al.a}` : "");
    if (st === "caution") return t("CAUTION") + (al && al.w ? ` ${al.w}` : "");
    if (st === "stale") return t("STALE");
    if (st === "nodata") return t("NO DATA");
    return "";
  };

  function blockSvg(id, b, sub) {
    const st = (sub && sub.state) || "nodata";
    const cls = st === "nominal" ? "" : `is-${st}`;
    const word = stateWord(st, sub && sub.alarms);
    const rows = (sub && sub.rows) || [];
    const name = b.name;              // subsystem identifiers are not translated
    const lab = [name + ":", st === "nominal" ? t("nominal") : word]
      .concat(rows.map((r) => `${r.label} ${tvText(r.q, r.digits)}`)).join(" ");
    if (sub && sub.hidden) {
      // not this position's subsystem: the outline stays, the block is inert
      return `<g class="o-blk is-hidden" aria-hidden="true"><rect class="o-bx" x="${b.x}" y="${b.y}" width="${b.w}" height="${b.h}" rx="3"/>` +
        s("text", { x: b.x + 10, y: b.y + 19, class: "t-off" }, esc(name)) + "</g>";
    }
    const bid = opts.blockId ? ` id="${esc(opts.blockId(id))}"` : "";
    let g = `<g class="o-blk ${cls}"${bid} data-sub="${esc(id)}" tabindex="0" role="link" aria-label="${esc(lab)}">`;
    g += `<rect class="o-bx" x="${b.x}" y="${b.y}" width="${b.w}" height="${b.h}" rx="3"/>`;
    g += s("text", { x: b.x + 10, y: b.y + 19, class: "t-name" }, esc(name));
    if (word) {
      const gx = b.x + b.w - 10;
      const glyphCls = st === "alarm" ? "gl-alarm" : st === "caution" ? "gl-caution" : "gl-stale";
      const tw = word.length * 7.2;
      g += st === "alarm" || st === "caution"
        ? `<path class="${glyphCls}" d="M${gx - tw - 14} ${b.y + 9} l6 10 h-12 z"/>`
        : `<circle class="${glyphCls}" cx="${gx - tw - 14}" cy="${b.y + 14}" r="5"/>`;
      g += s("text", { x: gx, y: b.y + 19, class: "o-st", "text-anchor": "end" }, esc(word));
    }
    // value rows: label, value, limit bar
    const wide = b.w > 200;
    rows.slice(0, wide ? 2 : 2).forEach((r, i) => {
      const y = b.y + 42 + i * 20;
      const colW = b.w - 20;
      g += s("text", { x: b.x + 10, y, class: "t-lab" }, esc(r.label));   // host translates row labels
      const v = tv(r.q, r.digits);
      const valX = wide ? b.x + 176 : b.x + b.w - 10;
      g += s("text", { x: valX, y, class: `t-val ${v.cls}`, "text-anchor": "end" }, esc(v.txt));
      if (wide) {
        const bd = band(r.limits, r.q && r.q.v);
        const bx = b.x + 188, bw = colW - 178;
        if (bd && bw > 40) {
          const X = (f) => bx + f * bw;
          g += `<rect class="g-track" x="${bx}" y="${y - 7}" width="${bw}" height="6" rx="1"/>`;
          if (bd.rl !== null && bd.yl !== null) g += `<rect class="g-band-w" x="${X(bd.rl)}" y="${y - 7}" width="${Math.max(0, X(bd.yl) - X(bd.rl))}" height="6"/>`;
          if (bd.yh !== null && bd.rh !== null) g += `<rect class="g-band-w" x="${X(bd.yh)}" y="${y - 7}" width="${Math.max(0, X(bd.rh) - X(bd.yh))}" height="6"/>`;
          if (bd.rl !== null) g += `<rect class="g-band-a" x="${bx}" y="${y - 7}" width="${Math.max(0, X(bd.rl) - bx)}" height="6"/>`;
          if (bd.rh !== null) g += `<rect class="g-band-a" x="${X(bd.rh)}" y="${y - 7}" width="${Math.max(0, bx + bw - X(bd.rh))}" height="6"/>`;
          if (bd.v !== null) {
            const pc = r.q.verdict === "stale" ? "is-stale" : r.limitState === "alarm" ? "is-alarm" : r.limitState === "caution" ? "is-caution" : "";
            g += `<rect class="g-ptr ${pc}" x="${X(bd.v) - 1.5}" y="${y - 10}" width="3" height="12"/>`;
          }
        }
      }
    });
    if (sub && sub.mode) g += s("text", { x: b.x + 10, y: b.y + b.h - 8, class: "t-lab" }, esc(sub.mode));
    g += "</g>";
    return g;
  }

  function tv(q, digits) {
    if (!q || q.v === null || q.v === undefined || q.verdict === "nodata") return { cls: "is-nodata", txt: t("no data") };
    if (q.text) return { cls: stateClass(q.verdict), txt: q.text };
    return { cls: stateClass(q.verdict), txt: withUnit(fmt(q.v, digits ?? 1), q.units) };
  }
  function tvText(q, digits) { return tv(q, digits).txt; }

  /* ── deployables + illumination (m.deploy, derive.js deriveDeployment) ── */
  const SUN = (cx, cy) => `<g aria-hidden="true"><circle class="o-sun-c" cx="${cx}" cy="${cy}" r="3"/>` +
    [0, 45, 90, 135, 180, 225, 270, 315].map((a) => {
      const r = (a * Math.PI) / 180, c = Math.cos(r), sn = Math.sin(r);
      return `<line class="o-sun" x1="${cx + 5 * c}" y1="${cy + 5 * sn}" x2="${cx + 8 * c}" y2="${cy + 8 * sn}"/>`;
    }).join("") + "</g>";
  const SUN_HTML = '<svg aria-hidden="true" width="14" height="14" viewBox="-8 -8 16 16">' +
    '<circle class="o-sun-c" r="3"/>' + [0, 45, 90, 135, 180, 225, 270, 315].map((a) => {
      const r = (a * Math.PI) / 180, c = Math.cos(r), sn = Math.sin(r);
      return `<line class="o-sun" x1="${(5 * c).toFixed(2)}" y1="${(5 * sn).toFixed(2)}" x2="${(7.5 * c).toFixed(2)}" y2="${(7.5 * sn).toFixed(2)}"/>`;
    }).join("") + "</svg>";

  /** One-line words for an illumination item (sunlit / dark / no data). */
  function illumWords(il) {
    if (!il || !il.state) return t("no data");
    if (il.state === "stowed") return t("stowed");
    const amp = il.i && il.i.v !== null ? " " + withUnit(fmt(il.i.v, 2), "A") : "";
    if (il.state === "sunlit") return t("sunlit") + amp;
    return il.eclipse ? t("dark (eclipse)") : t("dark") + amp;
  }
  function ageSuffix(q) { return q && q.verdict === "stale" && fin(q.ageS) ? " · " + fmtDur(q.ageS) : ""; }

  function wingWords(w) {
    if (!w || w.deployed === null) return t("no data");
    if (w.deployed === false) return t("stowed") + ageSuffix(w);
    return t("deployed") + " · " + illumWords(w.illum) + ageSuffix(w.illum && w.illum.state ? w.illum : w);
  }
  function antennaWords(a) {
    const st = a && a.state;
    const w = st === "deployed" ? t("antenna deployed") : st === "stowed" ? t("antenna stowed")
      : st === "jammed" ? t("antenna partly deployed (jammed)") : st === "unknown" ? t("antenna: state unknown")
      : t("antenna: no data");
    return w + ageSuffix(a);
  }

  /** A wing on ±Y: deployed (beside the bus, cells shown) or stowed (folded
   *  flat against the bus wall), filled by its illumination. */
  function wingSvg(side, w, legacyDark) {
    const left = side === "my";
    const x = left ? 16 : 736, y = 196, ww = 148, hh = 80;
    const cx = x + ww / 2;
    let g = "";
    const deployed = w ? w.deployed : null;
    const il = w ? w.illum : null;
    const stale = (w && w.verdict === "stale") || (il && il.verdict === "stale");
    if (deployed === false) {
      // folded: a narrow stack against the bus wall, the deployed outline ghosted
      const sx = left ? BUS.x - 18 : BUS.x + BUS.w + 4;
      g += `<rect class="o-ghost" x="${x}" y="${y}" width="${ww}" height="${hh}" rx="1"/>`;
      g += `<rect class="o-stow${stale ? " is-stale" : ""}" x="${sx}" y="${y - 30}" width="14" height="${hh + 60}" rx="1"/>`;
    } else {
      const cls = deployed === null && (!il || !il.state) ? "is-nodata"
        : !il || !il.state ? "is-unk" : il.state === "sunlit" ? "is-lit" : il.state === "dark" ? "is-dark" : "";
      const dark = cls === "is-dark" || (cls === "" && legacyDark);
      g += `<line class="o-yoke" x1="${left ? 164 : BUS.x + BUS.w}" y1="236" x2="${left ? BUS.x : 736}" y2="236"/>`;
      g += `<rect class="o-wing ${cls}${dark && cls !== "is-dark" ? " is-dark" : ""}${stale ? " is-stale" : ""}" x="${x}" y="${y}" width="${ww}" height="${hh}" rx="1"/>`;
      for (let i = 1; i < 4; i++) g += `<line class="o-cell" x1="${x + (ww * i) / 4}" y1="${y}" x2="${x + (ww * i) / 4}" y2="${y + hh}"/>`;
      g += `<line class="o-cell" x1="${x}" y1="${y + hh / 2}" x2="${x + ww}" y2="${y + hh / 2}"/>`;
      if (il && il.state === "sunlit") g += SUN(left ? x + 12 : x + ww - 12, y + 12);
    }
    g += s("text", { x: cx, y: 188, class: "t-lab", "text-anchor": "middle" }, esc(left ? t("−Y wing") : t("+Y wing")));
    const words = w ? wingWords(w) : "";
    if (words) {
      g += s("text", { x: cx, y: 296, class: `t-lab${stale ? " is-stale" : ""}`, "text-anchor": "middle" }, esc(words));
    }
    return g;
  }

  /** The S-band patch on −Z: flush when stowed, on its hinge arm when
   *  deployed, askew with a caution mark when the sensor reads jammed. */
  function antennaSvg(a, contact) {
    const x = 620, y0 = BUS.y + BUS.h;
    const st = a ? a.state : null;
    const stale = a && a.verdict === "stale";
    const sc = stale ? " is-stale" : "";
    let g = "";
    if (st === "deployed") {
      g += `<path class="o-ant${sc}" d="M${x} ${y0} v22" fill="none"/>` +
        `<rect class="o-ant${sc}" x="${x - 14}" y="${y0 + 22}" width="28" height="6" rx="1"/>`;
    } else if (st === "stowed") {
      g += `<rect class="o-ant${sc}" x="${x - 14}" y="${y0}" width="28" height="5" rx="1"/>` +
        `<path class="o-ghost" d="M${x} ${y0 + 5} v17 m-14 0 h28 v6 h-28 z"/>`;
    } else if (st === "jammed") {
      g += `<path class="o-ant is-caution${sc}" d="M${x} ${y0} l14 12" fill="none"/>` +
        `<rect class="o-ant is-caution${sc}" x="${x + 6}" y="${y0 + 10}" width="26" height="6" rx="1" transform="rotate(40 ${x + 19} ${y0 + 13})"/>` +
        `<path class="gl-caution" d="M${x - 22} ${y0 + 4} l6 10 h-12 z"/>`;
    } else {
      g += `<path class="o-ant is-nodata" d="M${x} ${y0} v22 m-14 0 h28 v6 h-28 z"/>`;
    }
    const cls = st === "jammed" ? "t-lab is-caution" : `t-lab${stale ? " is-stale" : ""}`;
    g += s("text", { x: x + 22, y: y0 + 20, class: cls }, esc(antennaWords(a)) +
      (contact ? " · " + esc(t("in contact")) : ""));
    return g;
  }

  /** Under the drawing: the six body faces, the on-board string judgement
   *  and the legend. HTML, so it wraps and reads in French too. */
  function solarHtml(d) {
    if (!d) return "";
    const face = (f) => {
      const cls = !f.state ? "is-nodata" : f.state === "sunlit" ? "is-lit" : "";
      const st = f.verdict === "stale" ? " is-stale" : "";
      const words = !f.state ? t("no data") : f.state === "sunlit"
        ? (f.i && f.i.v !== null ? withUnit(fmt(f.i.v, 2), "A") : t("sunlit"))
        : f.eclipse ? t("dark (eclipse)") : t("dark");
      const tip = `${t("face {{f}}", { f: f.face })}: ${illumWords(f)}${f.withWing ? " · " + t("includes the wing") : ""}` +
        `${ageSuffix(f)}${f.src ? " · " + f.src : ""}`;
      return `<li class="o-face ${cls}${st}" title="${esc(tip)}">${f.state === "sunlit" ? SUN_HTML : ""}` +
        `<b>${esc(f.face)}</b> <span>${esc(words)}${f.withWing ? "*" : ""}</span>` +
        (f.state === "sunlit" ? `<span class="o-vh"> ${esc(t("sunlit"))}</span>` : "") + "</li>";
    };
    const str = d.strings || {};
    const sw = (on) => (on === null || on === undefined ? t("no data") : on ? t("lit") : t("not lit"));
    const strWords = str.a === null || str.a === undefined
      ? t("on-board string check: no data")
      : t("on-board string check: string A {{a}} · string B {{b}}", { a: sw(str.a), b: sw(str.b) }) + ageSuffix(str);
    const anyWith = (d.faces || []).some((f) => f.withWing);
    return `<div class="o-sa">` +
      `<span class="k">${esc(t("Body faces"))}</span>` +
      `<div><ul class="o-faces" aria-label="${esc(t("Body-face illumination, from the panel currents"))}">${(d.faces || []).map(face).join("")}</ul>` +
      `<div class="${str.verdict === "stale" ? "vz-v is-stale" : ""}" style="margin-top:4px">${esc(strWords)}</div>` +
      (anyWith ? `<div>${esc(t("* includes the deployed wing: its own current is not downlinked (enable HK SID 8)"))}</div>` : "") +
      `</div>` +
      `<span class="k">${esc(t("Key"))}</span><ul class="o-legend">` +
      `<li><i class="o-sw is-lit"></i>${SUN_HTML}${esc(t("sunlit: delivering current"))}</li>` +
      `<li><i class="o-sw"></i>${esc(t("dark: no current, or eclipse"))}</li>` +
      `<li><i class="o-sw is-stow"></i>${esc(t("stowed"))}</li>` +
      `<li><i class="o-sw is-stale"></i>${esc(t("stale: last value, dimmed"))}</li>` +
      `<li><i class="o-sw is-nodata"></i>${esc(t("no data: not downlinked"))}</li></ul>` +
      `</div>`;
  }

  function draw(m) {
    const W = 900, H = 476;
    let g = "";
    // The spacecraft mode as ONE read-only value: a row of four segments read
    // as a mode-command control (review §2.2 OVR).
    const mode = (m.mode && m.mode.label) || null;
    g += s("text", { x: 16, y: 24, class: "t-lab" }, esc(t("Spacecraft mode")));
    if (!mode) g += s("text", { x: 132, y: 24, class: "t-val is-nodata" }, esc(t("mode not downlinked")));
    else {
      const alarm = mode === "SAFE" || mode === "EMERGENCY";
      const w = 22 + mode.length * 7.4;
      g += `<g class="o-mode is-on ${alarm ? "is-alarm" : ""}"><rect x="132" y="8" width="${w}" height="24" rx="2"/>` +
        s("text", { x: 132 + w / 2, y: 24, "text-anchor": "middle" }, esc(mode)) + "</g>";
    }
    // Earth below, nadir
    g += `<path class="o-earth" d="M0 ${H} L0 ${H - 16} Q${W / 2} ${H - 52} ${W} ${H - 16} L${W} ${H} Z"/>`;
    g += s("text", { x: W - 16, y: H - 6, class: "t-lab", "text-anchor": "end" }, esc(t("Earth: nadir is down (−Z)")));
    // axes key, top right: seen from ahead, +Y to the right, +X out of the screen
    g += `<g transform="translate(800 70)"><path class="o-axis" d="M0 34 V4 M0 34 H30"/>` +
      `<path class="o-axhead" d="M0 0 l-4 7 h8 z M34 34 l-7 -4 v8 z"/>` +
      s("text", { x: 6, y: 10, class: "t-lab" }, "+Z") + s("text", { x: 40, y: 38, class: "t-lab" }, "+Y") +
      `<circle class="o-axis" cx="0" cy="34" r="4"/><circle class="o-axhead" cx="0" cy="34" r="1.5"/>` +
      s("text", { x: 76, y: 58, class: "t-lab", "text-anchor": "end" }, esc(t("+X: velocity, towards you"))) + "</g>";
    // wings: seen from ahead, +Y is to the right (axes key); stowed or
    // deployed from eps.wing_status, sunlit or dark from the wing currents
    const dark = m.eclipse === true;
    const dep = m.deploy || null;
    g += wingSvg("my", dep ? dep.wings.my : null, dark) + wingSvg("py", dep ? dep.wings.py : null, dark);
    if (!dep && dark) g += s("text", { x: 90, y: 296, class: "t-lab", "text-anchor": "middle" }, esc(t("in eclipse")));
    // bus outline
    g += `<rect class="o-bus" x="${BUS.x}" y="${BUS.y}" width="${BUS.w}" height="${BUS.h}" rx="4"/>`;
    // zenith star tracker (+Z) above AOCS, imager + antenna on −Z
    g += `<path class="o-dev" d="M262 ${BUS.y} l6 -18 h22 l6 18 z"/>`;
    g += s("text", { x: 304, y: BUS.y - 6, class: "t-lab" }, esc(t("star tracker")));
    g += `<rect class="o-dev" x="354" y="${BUS.y + BUS.h}" width="24" height="12" rx="1"/>`;
    g += `<path class="o-bore" d="M366 ${BUS.y + BUS.h + 12} V${H - 40}"/>`;
    g += s("text", { x: 386, y: BUS.y + BUS.h + 26, class: "t-lab" }, esc(t("imager boresight")));
    if (dep) g += antennaSvg(dep.antenna, m.contact);
    else {
      g += `<path class="o-dev" d="M620 ${BUS.y + BUS.h} v14 m-8 0 h16"/>`;
      g += s("text", { x: 640, y: BUS.y + BUS.h + 20, class: "t-lab" }, esc(t("antenna")) +
        (m.contact ? " · " + esc(t("in contact")) : ""));
    }
    // blocks
    const subs = m.subsystems || {};
    for (const [id, b] of Object.entries(BLOCKS)) g += blockSvg(id, b, subs[id]);
    return { W, H, g };
  }

  function chips(m) {
    // Sunlit/eclipse and contact are on the page header strip already
    // (review §2.2 OVR: the same facts twice); the AOCS mode only when known.
    const out = [];
    if (m.aocsMode && m.aocsMode !== "—") out.push(`<span class="vz-chip">${esc(t("AOCS"))} <b>${esc(m.aocsMode)}</b></span>`);
    return out.join("");
  }

  function summaryText(m) {
    const subs = m.subsystems || {};
    const bad = Object.entries(subs).filter(([, v]) => v && v.state !== "nominal")
      .map(([k, v]) => `${BLOCKS[k] ? BLOCKS[k].name : k} ${stateWord(v.state, v.alarms).toLowerCase()}`);
    const d = m.deploy;
    const dep = d ? " " + [antennaWords(d.antenna), `${t("−Y wing")} ${wingWords(d.wings.my)}`,
      `${t("+Y wing")} ${wingWords(d.wings.py)}`].join("; ") + "." : "";
    return t("Mode {{m}}.", { m: (m.mode && m.mode.label) || t("not downlinked") }) + " " +
      (bad.length ? t("Not nominal: {{list}}.", { list: bad.join(", ") }) : t("All subsystems nominal.")) + dep;
  }

  function values(m) {
    const rows = [];
    for (const [id, b] of Object.entries(BLOCKS)) {
      const sub = (m.subsystems || {})[id];
      if (!sub) continue;
      rows.push([b.name, esc(sub.state === "nominal" ? t("nominal") : stateWord(sub.state, sub.alarms)), ""]);
      for (const r of sub.rows || []) rows.push([`${b.name} · ${r.label}`, r.q && r.q.text ? esc(r.q.text) : readout(r.q, r.digits ?? 1, t), r.q && r.q.src]);
    }
    const d = m.deploy;
    if (d) {
      rows.push([t("antenna"), esc(antennaWords(d.antenna)), d.antenna && d.antenna.src]);
      rows.push([t("−Y wing"), esc(wingWords(d.wings.my)), [d.wings.my.src, d.wings.my.illum && d.wings.my.illum.src].filter(Boolean).join(" · ")]);
      rows.push([t("+Y wing"), esc(wingWords(d.wings.py)), [d.wings.py.src, d.wings.py.illum && d.wings.py.illum.src].filter(Boolean).join(" · ")]);
      for (const f of d.faces || []) rows.push([t("face {{f}}", { f: f.face }), esc(illumWords(f) + ageSuffix(f)), f.src]);
      const str = d.strings || {};
      rows.push([t("on-board string check"), esc(str.a === null || str.a === undefined ? t("no data")
        : `A ${str.a ? t("lit") : t("not lit")} · B ${str.b ? t("lit") : t("not lit")}`), str.src]);
    }
    return valuesTable(rows, t, t("Spacecraft overview values"));
  }

  /* Narrow hosts (monitor view): the same blocks as a stacked list, no
   * outline; a 900-unit drawing would only scroll sideways there. */
  function compact(m) {
    const mode = (m.mode && m.mode.label) || null;
    let h = `<div class="o-modes"><span class="o-mlab">${esc(t("Spacecraft mode"))}</span>` +
      MODES.map((md) => `<span class="${md === mode ? "is-on" : ""}">${esc(md)}</span>`).join("") +
      (mode ? "" : `<em class="vz-v is-nodata">${esc(t("mode not downlinked"))}</em>`) + "</div><ul class=\"o-list\">";
    for (const [id, b] of Object.entries(BLOCKS)) {
      const sub = (m.subsystems || {})[id];
      if (!sub || sub.hidden) continue;
      const st = sub.state || "nodata";
      const word = st === "nominal" ? "" : stateWord(st, sub.alarms);
      const bid = opts.blockId ? ` id="${esc(opts.blockId(id))}"` : "";
      h += `<li><button type="button" class="o-tile ${st === "nominal" ? "" : "is-" + st}"${bid} data-sub="${esc(id)}">` +
        `<span class="o-th">${esc(b.name)}<em>${word ? (st === "alarm" || st === "caution" ? "▲ " : "○ ") + esc(word) : ""}</em></span>` +
        (sub.rows || []).map((r) => {
          const v = tv(r.q, r.digits);
          return `<span class="o-tr"><span>${esc(r.label)}</span><span class="vz-v ${v.cls}">${esc(v.txt)}</span></span>`;
        }).join("") + (sub.mode ? `<span class="o-tr"><span>${esc(sub.mode)}</span></span>` : "") + "</button></li>";
    }
    const d = m.deploy;
    if (d) {
      h += `<li class="o-tile" role="group" aria-label="${esc(t("Deployables and illumination"))}" style="cursor:default">` +
        `<span class="o-th">${esc(t("Deployables"))}</span>` +
        [[t("antenna"), antennaWords(d.antenna)], [t("−Y wing"), wingWords(d.wings.my)], [t("+Y wing"), wingWords(d.wings.py)]]
          .map(([k, v]) => `<span class="o-tr"><span>${esc(k)}</span><span>${esc(v)}</span></span>`).join("") + "</li>";
    }
    return h + "</ul>" + solarHtml(d);
  }

  function update(m) {
    last = m;
    if (!m) return;
    if ((el.clientWidth || 1000) < 640) {
      parts.chips.innerHTML = chips(m);
      const focused = el.ownerDocument && el.ownerDocument.activeElement;
      const fs = focused && focused.getAttribute && el.contains(focused) ? focused.getAttribute("data-sub") : null;
      parts.pic.innerHTML = compact(m);
      if (fs) { const n = parts.pic.querySelector(`[data-sub="${fs}"]`); if (n && n.focus) n.focus({ preventScroll: true }); }
      if (!parts.values.hidden) parts.values.innerHTML = values(m);
      return;
    }
    const r = draw(m);
    parts.chips.innerHTML = chips(m);
    const focused = el.ownerDocument && el.ownerDocument.activeElement;
    const focusSub = focused && focused.getAttribute && el.contains(focused) ? focused.getAttribute("data-sub") : null;
    parts.pic.innerHTML = `<div class="vz-stage" tabindex="-1">` +
      `<svg viewBox="0 0 ${r.W} ${r.H}" role="group" aria-labelledby="${tid} ${did}" ` +
      `style="width:100%;min-width:${Math.round(r.W * 0.93)}px;max-width:${Math.round(r.W * 1.3)}px">` +
      `<title id="${tid}">${esc(t("Spacecraft overview"))}</title><desc id="${did}">${esc(summaryText(m))}</desc>${r.g}</svg></div>` +
      solarHtml(m.deploy);
    if (focusSub) { const n = parts.pic.querySelector(`[data-sub="${focusSub}"]`); if (n && n.focus) n.focus({ preventScroll: true }); }
    if (!parts.values.hidden) parts.values.innerHTML = values(m);
  }
  if (parts.btn) parts.btn.addEventListener("click", () => { if (!parts.values.hidden && last) parts.values.innerHTML = values(last); });
  const go = (e) => {
    const n = e.target.closest && e.target.closest("[data-sub]");
    if (n && opts.onNavigate) { opts.onNavigate(n.getAttribute("data-sub")); return true; }
    return false;
  };
  const onClick = (e) => go(e);
  const onKey = (e) => {
    if (e.target && e.target.tagName === "BUTTON") return;      // buttons click themselves
    if ((e.key === "Enter" || e.key === " ") && go(e)) e.preventDefault();
  };
  let ro = null;
  try {
    let w0 = 0;
    ro = new ResizeObserver(() => { const w = el.clientWidth; if ((w < 640) !== (w0 < 640) && last) update(last); w0 = w; });
    ro.observe(el);
  } catch (e) { ro = null; }
  el.addEventListener("click", onClick);
  el.addEventListener("keydown", onKey);
  return {
    update,
    destroy() { if (ro) ro.disconnect(); el.removeEventListener("click", onClick); el.removeEventListener("keydown", onKey); el.innerHTML = ""; },
  };
}
