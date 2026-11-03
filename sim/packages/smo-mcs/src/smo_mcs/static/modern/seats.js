/* ============================================================================
 * MCS console seats — the participant side (redesign WP10)
 * ============================================================================
 * Loaded BEFORE mcs.js. With seats on (SMO_SEATS=iap|local) it:
 *
 *   - registers this browser tab as one of the person's screens and keeps
 *     it alive with a heartbeat (20 s; idle after 3 min, reclaimable 5 min);
 *   - stamps every same-origin /api/ request with X-SMO-Screen, so the
 *     command log names the screen. The SERVER decides the position of
 *     every command from the desks the person holds; the header's position
 *     selector only switches among them;
 *   - puts a "Desk" button beside the position selector: the desk list
 *     (who holds what), Claim / Release / Request, incoming requests with
 *     Accept / Decline, this screen's name and view (my desk, a tile of my
 *     desks, the wall), and, for instructors, the seat board (/seats);
 *   - in laptop mode (SMO_SEATS=local) asks for a typed name, shown as
 *     "unverified" everywhere.
 *
 * mcs.js listens for the "c2o:seats" event (detail = {enforced, me, board,
 * view}) to restrict the position selector and apply the screen view.
 * Seats off: nothing is shown and nothing changes.
 * ============================================================================ */

import { tText, tdb, onLangChange } from "/static/shared/i18n.js";
import { esc } from "/static/shared/components.js";

const SS_CONN = "c2o.seat.conn";
const LS_NAME = "c2o.seat.name";
const HEARTBEAT_MS = 20000;

const SEAT = { mode: "off", enforced: false, me: null, board: null, positions: {}, error: "" };
let connId = "";
try { connId = sessionStorage.getItem(SS_CONN) || ""; } catch (e) { /* private mode */ }

/* ── every /api/ call carries this screen's id ─────────────────────────── */
const _fetch = window.fetch.bind(window);
window.fetch = function seatFetch(input, init) {
  try {
    const url = typeof input === "string" ? input : (input && input.url) || "";
    const u = new URL(url, location.href);
    if (connId && u.origin === location.origin && u.pathname.startsWith("/api/")) {
      init = Object.assign({}, init || {});
      const h = new Headers(init.headers || (typeof input !== "string" && input ? input.headers : undefined) || {});
      h.set("X-SMO-Screen", connId);
      init.headers = h;
    }
  } catch (e) { /* never block a request */ }
  return _fetch(input, init);
};

const $ = (id) => document.getElementById(id);
const posLabel = (id) => {
  const p = SEAT.positions[id] || {};
  return p.label ? tdb(`pos:${id}:label`, p.label) : id;
};
const stateWord = (s) => ({ vacant: tText("vacant"), staffed: tText("staffed"), idle: tText("idle"),
  reclaimable: tText("reclaimable") }[s] || s);

async function api(path, body) {
  const r = await fetch("/api/seats" + path, body === undefined ? { cache: "no-store" } : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  let j = null;
  try { j = await r.json(); } catch (e) { /* not JSON */ }
  if (!r.ok) {
    const e = new Error((j && (j.error || j.message)) || `HTTP ${r.status}`);
    e.status = r.status; e.code = j && j.code; throw e;
  }
  return j;
}

function emit() {
  const view = SEAT.me && SEAT.me.screen ? SEAT.me.screen.view : null;
  const detail = { enforced: SEAT.enforced, mode: SEAT.mode, me: SEAT.me, board: SEAT.board, view };
  window.__c2oSeats = detail;        // for a listener that registers later
  document.dispatchEvent(new CustomEvent("c2o:seats", { detail }));
}

function apply(j) {
  if (j.conn_id && j.conn_id !== connId) {
    connId = j.conn_id;
    try { sessionStorage.setItem(SS_CONN, connId); } catch (e) { /* */ }
  }
  if (j.me) SEAT.me = j.me;
  if (j.board) SEAT.board = j.board;
  SEAT.error = "";
  paint();
  emit();
}

/* ── header button and panel ──────────────────────────────────────────── */
const CSS = `
#seat-btn{position:relative}
#seat-btn .sd{width:8px;height:8px;border-radius:50%;background:var(--alarm);display:inline-block}
#seat-btn.has-desk .sd{background:var(--ok)}
#seat-btn.has-req{border-color:var(--warn);color:var(--warn)}
#seat-panel{position:fixed;top:52px;right:12px;z-index:45;width:min(380px,calc(100vw - 24px));max-height:calc(100vh - 70px);overflow:auto;
  background:var(--s1);border:1px solid var(--line-2);border-radius:var(--radius-lg);box-shadow:0 6px 24px rgba(0,0,0,.4);padding:var(--sp-3);display:flex;flex-direction:column;gap:var(--sp-2)}
#seat-panel[hidden]{display:none}
#seat-panel h2{font-size:var(--fs-body);margin:0;font-weight:var(--fw-semibold)}
#seat-panel .who{font-size:var(--fs-label);color:var(--tx2)}
#seat-panel .unv{color:var(--warn)}
#seat-panel .req{border:1px solid var(--warn);background:var(--warn-wash);border-radius:var(--radius);padding:var(--sp-2);font-size:var(--fs-label);display:flex;flex-wrap:wrap;gap:6px;align-items:center}
#seat-panel table{width:100%;border-collapse:collapse;font-size:var(--fs-label)}
#seat-panel td{padding:3px 4px;border-bottom:1px solid var(--line);vertical-align:middle}
#seat-panel td.a{text-align:right;white-space:nowrap}
#seat-panel .dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:4px}
#seat-panel .dot.vacant{background:var(--alarm)} #seat-panel .dot.staffed{background:var(--ok)}
#seat-panel .dot.idle{background:var(--warn)} #seat-panel .dot.reclaimable{border:1.5px solid var(--warn)}
#seat-panel .mine{color:var(--accent);font-weight:var(--fw-medium)}
#seat-panel .ds-btn{min-height:22px;padding:0 8px;font-size:var(--fs-label)}
#seat-panel .scr{display:grid;grid-template-columns:auto 1fr;gap:4px 8px;align-items:center;font-size:var(--fs-label)}
#seat-panel input,#seat-panel select{font:inherit;font-size:var(--fs-label);background:var(--s2);color:var(--tx);border:1px solid var(--line-2);border-radius:var(--radius-sm);padding:2px 4px;min-width:0}
#seat-panel .err{color:var(--alarm);font-size:var(--fs-label)}
#seat-name{position:fixed;inset:0;z-index:60;background:var(--overlay);display:flex;align-items:center;justify-content:center;padding:16px}
#seat-name[hidden]{display:none}
#seat-name form{background:var(--s1);border:1px solid var(--line-2);border-radius:var(--radius-lg);padding:var(--sp-4);width:min(360px,100%);display:flex;flex-direction:column;gap:var(--sp-2)}
#seat-name input{font:inherit;background:var(--s2);color:var(--tx);border:1px solid var(--line-2);border-radius:var(--radius);padding:6px}
#seat-banner{font-size:var(--fs-label)}
body.seat-wall #nav-rail [data-page="cmd"],body.seat-wall #nav-rail [data-page="diag"],body.seat-wall #nav-rail [data-page="proc"]{display:none}
`;

function ensureUi() {
  if ($("seat-btn")) return;
  const st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);
  const btn = document.createElement("button");
  btn.type = "button"; btn.id = "seat-btn"; btn.className = "ds-btn ghost";
  btn.setAttribute("aria-expanded", "false"); btn.setAttribute("aria-controls", "seat-panel");
  const host = $("pos-bar");
  if (host) host.appendChild(btn); else document.body.appendChild(btn);
  const panel = document.createElement("div");
  panel.id = "seat-panel"; panel.hidden = true; panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", tText("Console desks"));
  document.body.appendChild(panel);
  btn.addEventListener("click", () => togglePanel());
  panel.addEventListener("click", onPanelClick);
  panel.addEventListener("change", onPanelChange);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) togglePanel(false); });
}
function togglePanel(on) {
  const p = $("seat-panel"), b = $("seat-btn");
  if (!p) return;
  p.hidden = on === undefined ? !p.hidden : !on;
  b.setAttribute("aria-expanded", String(!p.hidden));
  if (!p.hidden) paint();
}

function paint() {
  const b = $("seat-btn"), p = $("seat-panel");
  if (!b || !p) return;
  const me = SEAT.me || {};
  const mine = me.command_positions || [];
  const reqs = me.requests || [];
  b.classList.toggle("has-desk", mine.length > 0);
  b.classList.toggle("has-req", reqs.length > 0);
  const sv = me.screen && me.screen.view ? me.screen.view.kind : "";
  b.innerHTML = `<span class="sd" aria-hidden="true"></span> ` + esc(mine.length
    ? tText("Desk: {{list}}", { list: mine.map(posLabel).join(" + ") })
    : tText("No desk")) + (sv === "wall" ? ` · ${esc(tText("wall view"))}` : sv === "tile" ? ` · ${esc(tText("tile view"))}` : "") +
    (reqs.length ? ` · ${esc(tText("request"))}` : "");
  b.title = mine.length ? tText("Your desks: you command from these positions")
    : tText("You hold no desk: claim one to command");
  if (p.hidden) return;
  const board = SEAT.board || { positions: [] };
  const rows = (board.positions || []).map((c) => {
    const isMine = mine.includes(c.position);
    const holder = c.holder ? `${esc(c.holder.name)}${c.holder.verified ? "" : ` <span class="unv">${esc(tText("(unverified)"))}</span>`}` : `<i>${esc(tText("vacant"))}</i>`;
    let action = "";
    if (board.locked || c.locked) action = `<span class="who">${esc(tText("locked"))}</span>`;
    else if (isMine) action = `<button type="button" class="ds-btn" data-release="${esc(c.position)}">${esc(tText("Release"))}</button>`;
    else if (!c.holder || c.state === "reclaimable") action = `<button type="button" class="ds-btn" data-claim="${esc(c.position)}">${esc(tText("Claim"))}</button>`;
    else if ((me.outgoing || []).some((o) => o.position === c.position)) action = `<span class="who">${esc(tText("asked…"))}</span>`;
    else action = `<button type="button" class="ds-btn" data-request="${esc(c.position)}">${esc(tText("Request"))}</button>`;
    return `<tr><td><span class="dot ${esc(c.state)}" aria-hidden="true"></span><span class="${isMine ? "mine" : ""}">${esc(posLabel(c.position))}</span></td>
      <td>${holder}${c.holder ? `<div class="who">${esc(stateWord(c.state))}</div>` : ""}</td><td class="a">${action}</td></tr>`;
  }).join("");
  const reqHtml = reqs.map((r) => `<div class="req" role="alert">${esc(tText("{{name}} asks for your {{desk}} desk ({{s}} s)", { name: r.from, desk: posLabel(r.position), s: r.expires_in_s }))}
    <button type="button" class="ds-btn" data-accept="${esc(r.position)}">${esc(tText("Hand over"))}</button>
    <button type="button" class="ds-btn ghost" data-decline="${esc(r.position)}">${esc(tText("Keep it"))}</button></div>`).join("");
  const scr = me.screen;
  const view = scr ? scr.view || {} : {};
  const viewSel = scr ? `<div class="scr"><label for="seat-scr-label">${esc(tText("This screen"))}</label>
      <input id="seat-scr-label" maxlength="32" value="${esc(scr.label)}">
      <label for="seat-scr-view">${esc(tText("Shows"))}</label>
      <select id="seat-scr-view">
        <option value="position"${view.kind === "position" ? " selected" : ""}>${esc(tText("my active desk"))}</option>
        <option value="tile"${view.kind === "tile" ? " selected" : ""}>${esc(tText("a tile of all my desks"))}</option>
        <option value="wall"${view.kind === "wall" ? " selected" : ""}>${esc(tText("the wall (whole spacecraft, read-only)"))}</option>
      </select></div>` : "";
  p.innerHTML = `<h2>${esc(tText("Console desks"))}</h2>
    <div class="who">${me.name ? (me.verified ? esc(tText("Signed in as {{name}}", { name: me.name }))
      : `${esc(me.name)} <span class="unv">${esc(tText("(unverified)"))}</span>`) : ""}${me.instructor ? ` · ${esc(tText("instructor"))}` : ""}</div>
    ${SEAT.error ? `<div class="err" role="alert">${esc(SEAT.error)}</div>` : ""}
    ${reqHtml}
    <table><tbody>${rows}</tbody></table>
    <div class="who">${esc(tText("One holder per desk. A request goes to the holder, who has 60 s to answer. A desk idle for 5 min can be claimed."))}</div>
    ${viewSel}
    ${me.instructor ? `<a class="ds-btn" href="/seats" target="_blank" rel="noopener">${esc(tText("Open the seat board"))}</a>` : ""}`;
}

async function guarded(fn) {
  try { apply(await fn()); }
  catch (e) { SEAT.error = e.message; paint(); }
}
function onPanelClick(e) {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.claim) guarded(() => api("/claim", { position: b.dataset.claim }));
  else if (b.dataset.release) guarded(() => api("/release", { position: b.dataset.release }));
  else if (b.dataset.request) guarded(() => api("/request", { position: b.dataset.request }));
  else if (b.dataset.accept) guarded(() => api("/answer", { position: b.dataset.accept, accept: true }));
  else if (b.dataset.decline) guarded(() => api("/answer", { position: b.dataset.decline, accept: false }));
}
function onPanelChange(e) {
  if (e.target.id === "seat-scr-label") {
    guarded(async () => { await api("/screen", { conn_id: connId, label: e.target.value }); return beat(); });
  } else if (e.target.id === "seat-scr-view") {
    const kind = e.target.value;
    const act = currentPosition();
    guarded(async () => {
      await api("/screen", { conn_id: connId, view: { kind, positions: kind === "position" ? [act] : [] } });
      return beat();
    });
  }
}

function currentPosition() {
  const sel = $("pos-select");
  if (sel && sel.value) return sel.value;
  try { return localStorage.getItem("mcs.position") || ""; } catch (e) { return ""; }
}

/* ── name (laptop mode) ───────────────────────────────────────────────── */
function askName() {
  return new Promise((resolve) => {
    let box = $("seat-name");
    if (!box) {
      box = document.createElement("div");
      box.id = "seat-name";
      box.innerHTML = `<form><b>${esc(tText("Who is at this console?"))}</b>
        <span class="who" style="font-size:var(--fs-label);color:var(--tx3)">${esc(tText("Type your name. Without sign-in it is shown as unverified."))}</span>
        <input id="seat-name-in" maxlength="40" autocomplete="name" required aria-label="${esc(tText("Your name"))}">
        <button class="ds-btn primary" type="submit">${esc(tText("Continue"))}</button></form>`;
      document.body.appendChild(box);
    }
    box.hidden = false;
    const inp = $("seat-name-in");
    try { inp.value = localStorage.getItem(LS_NAME) || ""; } catch (e) { /* */ }
    inp.focus();
    box.querySelector("form").onsubmit = (ev) => {
      ev.preventDefault();
      const v = inp.value.trim();
      if (!v) return;
      try { localStorage.setItem(LS_NAME, v); } catch (e) { /* */ }
      box.hidden = true;
      resolve(v);
    };
  });
}

/* ── lifecycle ────────────────────────────────────────────────────────── */
async function connect() {
  let name = "";
  try { name = localStorage.getItem(LS_NAME) || ""; } catch (e) { /* */ }
  for (let i = 0; i < 3; i++) {
    const j = await api("/connect", { conn_id: connId, name: SEAT.mode === "local" ? name : "" });
    if (j.me && j.me.needs_name) { name = await askName(); continue; }
    apply(j);
    return;
  }
}
async function beat() {
  if (!connId) return { };
  try {
    return await api("/heartbeat", { conn_id: connId, position: currentPosition() });
  } catch (e) {
    if (e.status === 404) { connId = ""; await connect(); return {}; }
    throw e;
  }
}

async function boot() {
  let j;
  try {
    const r = await _fetch("/api/positions"); SEAT.positions = (await r.json()).positions || {};
  } catch (e) { /* offline */ }
  try { j = await api(""); } catch (e) { return; }      // no seat service: nothing to do
  SEAT.mode = j.mode; SEAT.enforced = !!j.enforced; SEAT.board = j.board;
  if (!SEAT.enforced) { emit(); return; }
  ensureUi();
  try { await connect(); }
  catch (e) {
    SEAT.error = e.status === 401 ? tText("Sign-in could not be verified: reload the page.") : e.message;
    paint(); emit();
  }
  setInterval(() => guarded(beat), HEARTBEAT_MS);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) guarded(beat); });
  // the header selector changed: tell the server at once (active desk)
  document.addEventListener("change", (e) => { if (e.target && e.target.id === "pos-select") guarded(beat); });
  // a refused WS/HTTP action may mean the desk moved: refresh
  document.addEventListener("c2o:seats-refresh", () => guarded(beat));
  onLangChange(() => paint());
}

export const seats = { state: SEAT, refresh: () => guarded(beat) };
boot();
