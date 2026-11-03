/* ============================================================================
 * C2O DESIGN SYSTEM — seatboard.js  (served at /static/shared/seatboard.js)
 * ============================================================================
 * The SMO console seat board (redesign WP10), one copy for the MCS page
 * /seats and the instructor console's "Crew" view (where /api/seats* is
 * answered by the GSG on the ground, never over the space link).
 *
 *   import { mountSeatBoard, positionLabel } from "/static/shared/seatboard.js";
 *   const sb = mountSeatBoard(host, { base: "/api/seats", positions,  // {id: {label}}
 *                                     onToast: (msg, kind) => … });
 *   sb.refresh(); sb.destroy();
 *
 * Layout (redesign s5 "Seat board mock"): one column per console position,
 * plus Bench (connected, no desk) and Wall. A participant card lists that
 * person's screens. Drag a card onto a column to assign the desk (from the
 * Bench it adds a desk; from a desk it moves); drag a screen chip onto a
 * desk to show that desk on the screen, onto Wall for the wall view; the
 * chip's "tile" button tiles all the person's desks. Every drag has a
 * keyboard twin (the card's "Assign to" menu, the chip's view menu).
 * A vacant desk shows a red dot AND the word "vacant" (never colour alone).
 * Rotate roles (two-step), Lock board, Vacate a person ("sick member"),
 * per-desk lock and pair (read-only shadow or second commander).
 * Every action is checked again on the server (SMO_INSTRUCTORS).
 * ============================================================================ */

import { t, tText, tdb, onLangChange } from "/static/shared/i18n.js";
import { esc, armButton } from "/static/shared/components.js";

const POLL_MS = 3000;

const CSS = `
.sb{display:flex;flex-direction:column;gap:var(--sp-3);min-width:0}
.sb-bar{display:flex;flex-wrap:wrap;align-items:center;gap:var(--sp-2)}
.sb-bar h2{font-size:var(--fs-value);margin:0 var(--sp-2) 0 0;font-weight:var(--fw-semibold)}
.sb-bar .grow{flex:1}
.sb-note{font-size:var(--fs-label);color:var(--tx3)}
.sb-cols{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:var(--sp-2);padding-bottom:var(--sp-2)}
.sb-col{background:var(--s1);border:1px solid var(--line);border-radius:var(--radius);display:flex;flex-direction:column;min-height:220px}
.sb-col.is-drop{outline:2px dashed var(--accent);outline-offset:-2px}
.sb-col.bench,.sb-col.wall{background:var(--bg)}
.sb-col.locked{background-image:var(--hatch)}
.sb-head{padding:var(--sp-2);border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:3px}
.sb-head .nm{font-weight:var(--fw-semibold);font-size:var(--fs-body);display:flex;align-items:center;gap:6px}
.sb-head .st{font-size:var(--fs-label);color:var(--tx3);display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.sb-dot{width:9px;height:9px;border-radius:50%;flex:0 0 auto;display:inline-block}
.sb-dot.vacant{background:var(--alarm)}
.sb-dot.staffed{background:var(--ok)}
.sb-dot.idle{background:var(--warn)}
.sb-dot.reclaimable{background:transparent;border:1.5px solid var(--warn)}
.sb-head .ctl{display:flex;gap:4px;flex-wrap:wrap;align-items:center}
.sb-head select{max-width:100%;font:inherit;font-size:var(--fs-label);background:var(--s2);color:var(--tx);border:1px solid var(--line-2);border-radius:var(--radius-sm);padding:1px 2px}
.sb-body{padding:var(--sp-2);display:flex;flex-direction:column;gap:var(--sp-2);flex:1}
.sb-empty{font-size:var(--fs-label);color:var(--tx-off);font-style:italic}
.sb-card{background:var(--s2);border:1px solid var(--line-2);border-radius:var(--radius);padding:6px;cursor:grab;display:flex;flex-direction:column;gap:4px}
.sb-card[aria-grabbed="true"]{opacity:.5}
.sb-card .who{display:flex;align-items:center;gap:6px;font-size:var(--fs-body);color:var(--val);min-width:0}
.sb-card .who b{font-weight:var(--fw-medium);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sb-card .tag{font-size:10px;color:var(--tx3);border:1px solid var(--line-2);border-radius:var(--radius-sm);padding:0 3px}
.sb-card .tag.unv{color:var(--warn);border-color:var(--warn)}
.sb-card .tag.role{color:var(--shelf);border-color:var(--shelf)}
.sb-card .pres{font-size:var(--fs-label);color:var(--tx3)}
.sb-card .row{display:flex;gap:4px;flex-wrap:wrap;align-items:center}
.sb-card select{font:inherit;font-size:var(--fs-label);background:var(--s1);color:var(--tx);border:1px solid var(--line-2);border-radius:var(--radius-sm);padding:1px 2px;max-width:100%}
.sb-scr{display:grid;grid-template-columns:1fr auto;align-items:baseline;gap:0 4px;width:100%;font-size:var(--fs-label);border:1px dashed var(--tx3);border-radius:var(--radius-sm);padding:2px 4px;background:var(--s1);cursor:grab;color:var(--tx2);min-width:0}
.sb-scr .l{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sb-scr .v{grid-column:1 / -1;color:var(--accent);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sb-card .scrs{display:flex;flex-direction:column;gap:3px}
.sb-scr button{font:inherit;font-size:10px;background:none;border:0;color:var(--tx3);cursor:pointer;padding:0 2px}
.sb-scr button:hover{color:var(--accent)}
.sb-ev{font-size:var(--fs-label);color:var(--tx2);max-height:180px;overflow:auto;border-top:1px solid var(--line);padding-top:var(--sp-2)}
.sb-ev div{padding:1px 0;font-family:var(--mono)}
.sb-err{color:var(--alarm);font-size:var(--fs-label)}
.sb-mini{font:inherit;font-size:var(--fs-label);min-height:20px;padding:0 6px}
`;

/** A position's display name in the interface language. */
export function positionLabel(id, positions) {
  if (id === "bench") return tText("Bench");
  if (id === "wall") return tText("Wall");
  const p = (positions || {})[id] || {};
  return p.label ? tdb(`pos:${id}:label`, p.label) : id;
}

const presenceText = (p) => ({ active: tText("active"), idle: tText("idle (no heartbeat 3 min)"),
  away: tText("away: desk reclaimable") }[p] || "");
const stateText = (s) => ({ vacant: tText("vacant"), staffed: tText("staffed"), idle: tText("idle"),
  reclaimable: tText("reclaimable") }[s] || s);
const viewText = (v, positions) => {
  if (!v) return "";
  if (v.kind === "wall") return tText("wall");
  if (v.kind === "tile") return tText("tile: {{list}}", { list: (v.positions || []).map((p) => positionLabel(p, positions)).join(" + ") });
  return positionLabel((v.positions || [])[0] || "", positions);
};
const actionText = (a) => ({
  claim: tText("claimed"), release: tText("released"), request: tText("asked for"),
  handover: tText("took over (handover)"), request_declined: tText("request declined"),
  request_expired: tText("request expired"), reclaim: tText("reclaimed"), assign: tText("assigned"),
  vacate: tText("vacated"), lock: tText("locked"), unlock: tText("unlocked"), rotate: tText("rotated roles"),
  pair: tText("paired"), unpair: tText("unpaired"), pair_mode: tText("pair setting"),
  view: tText("screen view"), idle: tText("went idle"), away: tText("away"), active: tText("back"),
}[a] || a);

export function mountSeatBoard(host, opts = {}) {
  const base = opts.base || "/api/seats";
  const positions = opts.positions || {};
  const toast = opts.onToast || (() => {});
  if (!document.getElementById("sb-css")) {
    const st = document.createElement("style"); st.id = "sb-css"; st.textContent = CSS;
    document.head.appendChild(st);
  }
  host.classList.add("sb");
  let data = null, err = null, timer = null, dragging = null, alive = true;

  async function api(path, body) {
    const r = await fetch(base + path, body === undefined ? { cache: "no-store" } : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    let j = null;
    try { j = await r.json(); } catch (e) { /* not JSON */ }
    if (!r.ok) {
      const e = new Error((j && (j.error || j.message)) || `HTTP ${r.status}`);
      e.status = r.status; e.code = j && j.code; throw e;
    }
    return j;
  }
  async function act(path, body, okMsg) {
    try {
      await api(path, body);
      if (okMsg) toast(okMsg, "success");
    } catch (e) {
      toast(tText("Refused: {{why}}", { why: e.message }), "error");
    }
    await refresh();
  }
  async function refresh() {
    try { data = await api("/board"); err = null; }
    catch (e) {
      err = e.status === 403 ? tText("The seat board is for instructors.")
        : e.status === 502 ? tText("The MCS on the ground is not reachable.")
          : e.status === 404 ? tText("No seat board on this server.") : e.message;
    }
    if (alive) render();
  }

  function card(p, from, role) {
    const people = data.people || [];
    const me = people.find((x) => x.id === p.id) || p;
    // A person's screens are listed once, on their first card (first desk
    // in board order, or the bench).
    const first = (me.positions || [])[0] || (me.paired || [])[0] || "bench";
    const screens = (from === first || (from === "" && !(me.positions || []).length &&
      first === (me.paired || [])[0])) ? (me.screens || []) : [];
    const opts2 = [`<option value="">${esc(tText("Assign to…"))}</option>`]
      .concat((data.positions || []).map((c) =>
        `<option value="${esc(c.position)}">${esc(positionLabel(c.position, positions))}</option>`))
      .join("");
    const scr = screens.map((s) =>
      `<span class="sb-scr" draggable="true" data-conn="${esc(s.conn_id)}" data-person="${esc(me.id)}" ` +
      `title="${esc(tText("Drag onto a desk or the Wall to set what this screen shows"))}">` +
      `<span class="l">${esc(s.label)}</span>` +
      `<button type="button" data-tile="${esc(s.conn_id)}" title="${esc(tText("Tile all of this person's desks on this screen"))}">${esc(tText("tile"))}</button>` +
      `<span class="v" title="${esc(viewText(s.view, positions))}">${esc(viewText(s.view, positions))}</span></span>`).join("");
    return `<div class="sb-card" draggable="true" data-person="${esc(me.id)}" data-from="${esc(from)}">
      <div class="who"><b>${esc(me.name)}</b>${me.verified ? "" : `<span class="tag unv">${esc(tText("unverified"))}</span>`}` +
      `${me.instructor ? `<span class="tag">${esc(tText("instructor"))}</span>` : ""}` +
      `${role ? `<span class="tag role">${esc(role === "second" ? tText("second commander") : tText("shadow"))}</span>` : ""}</div>
      <div class="pres">${esc(presenceText(me.presence))}</div>
      ${scr ? `<div class="scrs">${scr}</div>` : (me.screens || []).length && !screens.length
        ? `<div class="pres">${esc(tText("screens: see the first desk"))}</div>` : ""}
      <div class="row"><select data-assign="${esc(me.id)}" data-from="${esc(from)}" aria-label="${esc(tText("Assign {{name}} to a desk", { name: me.name }))}">${opts2}</select>
      ${(me.positions || []).length || (me.paired || []).length ? `<button type="button" class="ds-btn sb-mini" data-bench="${esc(me.id)}" title="${esc(tText("Take every desk from this person (sick member)"))}">${esc(tText("Vacate"))}</button>` : ""}</div>
    </div>`;
  }

  function render() {
    if (!data) {
      host.innerHTML = `<div class="sb-err" role="alert">${esc(err || tText("Loading…"))}</div>`;
      return;
    }
    const people = data.people || [];
    const cols = data.positions || [];
    const bench = people.filter((p) => p.bench);
    const wallScreens = people.flatMap((p) => (p.screens || []).filter((s) => s.view && s.view.kind === "wall")
      .map((s) => ({ p, s })));
    const modeNote = !data.enforced ? tText("Seats are off on this MCS (SMO_SEATS=off): positions are chosen freely and every command is logged unverified.")
      : data.mode === "local" ? tText("Laptop mode: names are typed, not verified.")
        : tText("Identities verified by IAP.");
    const colHtml = cols.map((c) => {
      const holder = c.holder ? card(c.holder, c.position, null) : "";
      const pairs = (c.pairs || []).map((x) => card(x, "", x.role)).join("");
      const req = c.request ? `<div class="sb-note">${esc(tText("{{name}} asked for this desk", { name: c.request.from.name }))}</div>` : "";
      return `<section class="sb-col${c.locked ? " locked" : ""}" data-drop="${esc(c.position)}" aria-label="${esc(positionLabel(c.position, positions))}">
        <div class="sb-head"><div class="nm"><span class="sb-dot ${esc(c.state)}" aria-hidden="true"></span>${esc(positionLabel(c.position, positions))}</div>
          <div class="st">${esc(stateText(c.state))}${c.locked ? ` · ${esc(tText("locked"))}` : ""}</div>
          <div class="ctl">
            <select data-pair="${esc(c.position)}" aria-label="${esc(tText("Pair on {{desk}}", { desk: positionLabel(c.position, positions) }))}" title="${esc(tText("Allow a second person at this desk"))}">
              <option value="">${esc(tText("one holder"))}</option>
              <option value="shadow"${c.pair_mode === "shadow" ? " selected" : ""}>${esc(tText("+ shadow (read-only)"))}</option>
              <option value="second"${c.pair_mode === "second" ? " selected" : ""}>${esc(tText("+ second commander"))}</option></select>
            <button type="button" class="ds-btn sb-mini" data-lockpos="${esc(c.position)}" aria-pressed="${!!c.locked}">${esc(c.locked ? tText("Unlock") : tText("Lock"))}</button>
            ${c.holder ? `<button type="button" class="ds-btn sb-mini" data-vacate="${esc(c.position)}">${esc(tText("Vacate"))}</button>` : ""}
          </div></div>
        <div class="sb-body">${holder || `<div class="sb-empty">${esc(tText("vacant — drag a participant here"))}</div>`}${pairs}${req}</div>
      </section>`;
    }).join("");
    const benchHtml = `<section class="sb-col bench" data-drop="bench" aria-label="${esc(tText("Bench"))}">
      <div class="sb-head"><div class="nm">${esc(tText("Bench"))}</div><div class="st">${esc(tText("connected, no desk"))}</div></div>
      <div class="sb-body">${bench.map((p) => card(p, "bench", null)).join("") || `<div class="sb-empty">${esc(tText("nobody waiting"))}</div>`}</div></section>`;
    const wallHtml = `<section class="sb-col wall" data-drop="wall" aria-label="${esc(tText("Wall"))}">
      <div class="sb-head"><div class="nm">${esc(tText("Wall"))}</div><div class="st">${esc(tText("screens showing the wall view"))}</div></div>
      <div class="sb-body">${wallScreens.map(({ p, s }) => `<span class="sb-scr" draggable="true" data-conn="${esc(s.conn_id)}" data-person="${esc(p.id)}">${esc(p.name)} · ${esc(s.label)}</span>`).join("")
        || `<div class="sb-empty">${esc(tText("drop a screen here"))}</div>`}</div></section>`;
    const ev = (data.events || []).slice().reverse().slice(0, 40).map((e) => {
      const who = e.person_id ? (people.find((p) => p.id === e.person_id) || {}).name || "" : "";
      return `<div>#${e.seq} ${esc(actionText(e.action))} ${esc(e.position ? positionLabel(e.position, positions) : "")} ${esc(who)}</div>`;
    }).join("");
    host.innerHTML = `
      <div class="sb-bar"><h2>${esc(tText("Console seats"))}</h2>
        <span class="sb-note">${esc(modeNote)}</span><span class="grow"></span>
        <button type="button" class="ds-btn" id="sb-rotate">${esc(tText("Rotate roles"))}</button>
        <button type="button" class="ds-btn" id="sb-lock" aria-pressed="${!!data.locked}">${esc(data.locked ? tText("Unlock board") : tText("Lock board"))}</button>
        <a class="ds-btn ghost" href="${esc(base)}/events?format=csv" download>${esc(tText("Export seat log"))}</a></div>
      ${err ? `<div class="sb-err" role="alert">${esc(err)}</div>` : ""}
      <div class="sb-cols">${benchHtml}${colHtml}${wallHtml}</div>
      <details class="sb-ev"><summary>${esc(tText("Seat log"))}</summary>${ev || esc(tText("nothing yet"))}</details>`;
    const rot = host.querySelector("#sb-rotate");
    if (rot && data.enforced) armButton(rot, { onExecute: () => act("/rotate", {}, tText("Roles rotated")) });
    if (!data.enforced) host.querySelectorAll("button,select").forEach((b) => { b.disabled = true; });
  }

  // ── events (delegated) ─────────────────────────────────────────────────
  host.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b || !data) return;
    if (b.id === "sb-lock") act("/lock", { on: !data.locked });
    else if (b.dataset.lockpos) act("/lock", { on: b.getAttribute("aria-pressed") !== "true", position: b.dataset.lockpos });
    else if (b.dataset.vacate) act("/vacate", { position: b.dataset.vacate });
    else if (b.dataset.bench) act("/bench", { person: b.dataset.bench });
    else if (b.dataset.tile) act("/screen", { conn_id: b.dataset.tile, view: { kind: "tile", positions: [] } });
  });
  host.addEventListener("change", (e) => {
    const s = e.target;
    if (s.dataset.assign !== undefined && s.value) {
      const to = s.value, from = s.dataset.from;
      act("/assign", { position: to, person: s.dataset.assign }).then(() =>
        (from && from !== "bench" && from !== to) ? act("/vacate", { position: from }) : null);
    } else if (s.dataset.pair !== undefined) {
      act("/pair", { position: s.dataset.pair, mode: s.value || null });
    }
  });
  host.addEventListener("dragstart", (e) => {
    const scr = e.target.closest && e.target.closest(".sb-scr");
    const c = e.target.closest && e.target.closest(".sb-card");
    if (scr) dragging = { kind: "screen", conn: scr.dataset.conn };
    else if (c) { dragging = { kind: "person", person: c.dataset.person, from: c.dataset.from }; c.setAttribute("aria-grabbed", "true"); }
    else return;
    e.dataTransfer.effectAllowed = "move";
    try { e.dataTransfer.setData("text/plain", JSON.stringify(dragging)); } catch (x) { /* */ }
    e.stopPropagation();
  });
  host.addEventListener("dragend", () => {
    host.querySelectorAll(".is-drop").forEach((x) => x.classList.remove("is-drop"));
    host.querySelectorAll("[aria-grabbed]").forEach((x) => x.removeAttribute("aria-grabbed"));
  });
  host.addEventListener("dragover", (e) => {
    const col = e.target.closest && e.target.closest("[data-drop]");
    if (!col || !dragging) return;
    e.preventDefault();
    host.querySelectorAll(".is-drop").forEach((x) => { if (x !== col) x.classList.remove("is-drop"); });
    col.classList.add("is-drop");
  });
  host.addEventListener("drop", (e) => {
    const col = e.target.closest && e.target.closest("[data-drop]");
    const d = dragging; dragging = null;
    if (!col || !d) return;
    e.preventDefault();
    col.classList.remove("is-drop");
    const to = col.dataset.drop;
    if (d.kind === "screen") {
      if (to === "wall") act("/screen", { conn_id: d.conn, view: { kind: "wall", positions: [] } });
      else if (to !== "bench") act("/screen", { conn_id: d.conn, view: { kind: "position", positions: [to] } });
      return;
    }
    if (to === "bench") { if (d.from && d.from !== "bench") act("/vacate", { position: d.from }); return; }
    if (to === "wall" || to === d.from) return;
    act("/assign", { position: to, person: d.person }).then(() =>
      (d.from && d.from !== "bench") ? act("/vacate", { position: d.from }) : null);
  });

  const offLang = onLangChange(() => render());
  refresh();
  timer = setInterval(() => { if (!host.querySelector(":focus") && !dragging) refresh(); }, POLL_MS);
  return {
    refresh,
    destroy() { alive = false; clearInterval(timer); if (typeof offLang === "function") offLang(); host.innerHTML = ""; },
  };
}
