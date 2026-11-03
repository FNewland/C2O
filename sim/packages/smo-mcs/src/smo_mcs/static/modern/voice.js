/* ============================================================================
 * C2O voice loops — keyset panel logic (WP-4 prototype). Page: voice.html.
 * ============================================================================
 * Model
 *   One LiveKit room per loop. POST /api/voice/token returns one token per
 *   loop this position may hear (access MON or TALK; a loop with access OFF,
 *   such as the Instructor/SIM loop for a student, is never sent). The key
 *   state is per loop:
 *     OFF   not connected
 *     MON   connected, subscribed, never publishing
 *     TALK  connected, a microphone track published MUTED; push-to-talk
 *           unmutes it. Talk on one loop at a time: choosing TALK elsewhere
 *           moves the previous TALK loop back to MON.
 *   The server enforces the rights (canPublish only on TALK loops); this
 *   page only mirrors them, with the reason on every disabled control.
 *
 * Position: until seat binding (WP10) it is the MCS header selection,
 *   localStorage "mcs.position" (same origin), followed live. Instructor
 *   roles (instructor, sim) are chosen here and need the instructor role.
 *
 * Audio never starts by itself: everything begins with the Join click (a
 *   user gesture), and the microphone is opened only when a loop is TALK.
 *   Echo cancellation, noise suppression and AGC are on.
 *
 * Connection state uses the seven UI states (docs/ui/C2O_UI_BRIEF.md §1.3):
 *   no data  "Not joined"            disabled  "Voice unavailable" + reason
 *   stale    "Connecting / Reconnecting" + age
 *   enabled  "Connected"             active    transmitting (the talk button)
 *   armed    Latch on (open microphone, amber outline)
 *   alarm    "Disconnected" + reason + Rejoin
 * ============================================================================ */
import { I18n, t, tText, tdb, getLang, onLangChange } from "/static/shared/i18n.js";
import { glyph, esc, setDisabled, setEnabled, mountLangToggle } from "/static/shared/components.js";

const LK = globalThis.LivekitClient;
const $ = (id) => document.getElementById(id);
const STATES = ["OFF", "MON", "TALK"];
const RANK = { OFF: 0, MON: 1, TALK: 2 };
const LS_PREFS = "c2o.voice.v1";
const LS_NAME = "c2o.voice.name";
const IN_FRAME = window.parent !== window;

const S = {
  cfg: null,            // /api/voice/config
  tok: null,            // last /api/voice/token answer
  position: null,
  joined: false,
  joining: false,
  loops: [],            // [{id,label,colour,access,state,volume,token,room,conn,since,speakers,tracks,mic}]
  talkId: null,         // the loop in TALK
  tx: false,            // microphone open
  holding: new Set(),   // what holds PTT down: "key", "pointer"
  latched: false,
  micError: null,
  refreshTimer: null,
  audioBlocked: false,
  lastError: null,
};

/* ── small helpers ────────────────────────────────────────────────────── */
function prefs() { try { return JSON.parse(localStorage.getItem(LS_PREFS) || "{}") || {}; } catch (e) { return {}; } }
function savePrefs() {
  try {
    const p = prefs(); const mine = p[S.position] = p[S.position] || {};
    for (const L of S.loops) mine[L.id] = { state: L.state, volume: L.volume };
    localStorage.setItem(LS_PREFS, JSON.stringify(p));
  } catch (e) { /* private mode: not remembered */ }
}
function loopLabel(L) { const l = L.label || {}; return (getLang() === "fr" && l.fr) ? l.fr : (l.en || L.id); }
function posLabel(id) {
  const l = ((S.cfg || {}).position_labels || {})[id] || {};
  if (getLang() === "fr") return l.fr || tdb(`pos:${id}:display_name`, l.en || id);
  return l.en || id;
}
function secsSince(ms) { return Math.max(0, Math.round((Date.now() - ms) / 1000)); }
function tell(msg) { if (IN_FRAME) try { window.parent.postMessage({ source: "c2o-voice", ...msg }, location.origin); } catch (e) { /* */ } }
function chip(kind, label, g, title) {
  return `<span class="ds-chip ${kind}"${title ? ` title="${esc(title)}"` : ""}>${g ? glyph(g) : ""}<span>${esc(label)}</span></span>`;
}

/* ── server calls ─────────────────────────────────────────────────────── */
async function getConfig() {
  const name = currentName();
  const r = await fetch("/api/voice/config" + (name ? `?name=${encodeURIComponent(name)}` : ""), { cache: "no-store" });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(j.error || String(r.status)), { code: j.code || r.status });
  return j;
}
async function getTokens(position) {
  const r = await fetch("/api/voice/token", {
    method: "POST", cache: "no-store", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ position, name: currentName() }),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(j.error || String(r.status)), { code: j.code || r.status });
  return j;
}
function currentName() { const el = $("name"); return el && !$("name-field").hidden ? el.value.trim() : ""; }

/* ── rendering: header ────────────────────────────────────────────────── */
function paintHeader() {
  const c = S.cfg;
  const sel = $("pos");
  if (c) {
    const ids = c.positions || [];
    sel.innerHTML = ids.map((p) => `<option value="${esc(p)}">${esc(posLabel(p))}</option>`).join("");
    if (S.position && ids.includes(S.position)) sel.value = S.position;
    const id = c.identity;
    if (id) {
      $("who").innerHTML = id.verified
        ? `${esc(tText("Signed in as"))} <b>${esc(id.name)}</b>${id.instructor ? ` · ${esc(tText("instructor"))}` : ""}`
        : `<b>${esc(id.name)}</b> <span class="unv">${esc(tText("(unverified)"))}</span>`;
    } else {
      $("who").textContent = "";
    }
  }
  paintConn();
}

function paintConn() {
  const el = $("conn");
  if (!S.cfg && !S.lastError) { el.innerHTML = chip("is-nodata", tText("Checking…")); return; }
  if (S.cfg && !S.cfg.available) {
    el.innerHTML = chip("off", tText("Voice unavailable"), "off", reasonText(S.cfg.reason)); return;
  }
  if (!S.joined) {
    el.innerHTML = S.lastError
      ? chip("alarm", tText("Disconnected"), "alarm-up", S.lastError)
      : chip("is-nodata", tText("Not joined"));
    tell({ conn: S.lastError ? "alarm" : "idle", tx: false });
    return;
  }
  const on = S.loops.filter((L) => L.state !== "OFF");
  const failed = on.filter((L) => L.conn === "failed");
  const slow = on.filter((L) => L.conn === "connecting" || L.conn === "reconnecting");
  if (failed.length) {
    el.innerHTML = chip("alarm", tText("Disconnected"), "alarm-up",
      failed.map((L) => loopLabel(L)).join(", ")) +
      ` <button type="button" class="ds-btn sm" id="rejoin">${esc(tText("Rejoin"))}</button>`;
    tell({ conn: "alarm", tx: S.tx });
  } else if (slow.length) {
    const since = Math.min(...slow.map((L) => L.since || Date.now()));
    const what = slow.some((L) => L.conn === "reconnecting") ? tText("Reconnecting") : tText("Connecting…");
    el.innerHTML = `${chip("stale", what, "stale")} <span class="ds-age">${secsSince(since)} s</span>`;
    tell({ conn: "stale", tx: S.tx });
  } else {
    el.innerHTML = `<span class="ds-chip ok">${glyph("ack")}<span>${esc(tText("Connected"))}</span></span>` +
      ` <span class="ds-meta">${esc(tText("{{n}} loops", { n: on.length }))}</span>`;
    tell({ conn: "ok", tx: S.tx, talk: S.talkId });
  }
}

function reasonText(code) {
  return {
    "not-configured": tText("No voice server is configured for this mission control."),
    "weak-secret": tText("The voice server key is misconfigured."),
    "no-library": tText("The voice token library is not installed on the server."),
    "bad-config": tText("The loop configuration is invalid; see the MCS log."),
  }[code] || tText("Voice is not available.");
}

/* ── rendering: keys ──────────────────────────────────────────────────── */
function keyHtml(L) {
  const lab = loopLabel(L);
  const seg = STATES.map((st) => {
    const allowed = RANK[st] <= RANK[L.access];
    const why = allowed ? "" : (L.access === "MON"
      ? tText("Your position may only monitor this loop")
      : tText("Not available to your position"));
    const name = { OFF: tText("Off"), MON: tText("Monitor"), TALK: tText("Talk") }[st];
    return `<button type="button" role="radio" data-set="${st}" aria-checked="${L.state === st}"` +
      ` title="${esc(why || name)}" aria-label="${esc(name)}"` +
      (allowed ? "" : ` aria-disabled="true" data-reason="${esc(why)}"`) + `>${st}</button>`;
  }).join("");
  return `<li class="key" id="key-${esc(L.id)}" data-loop="${esc(L.id)}" data-state="${L.state}"` +
    ` style="--loop:${L.colour === "neutral" ? "var(--tx3)" : `var(--${esc(L.colour)})`}">` +
    `<span class="sw" aria-hidden="true"></span>` +
    `<span class="nm"><b>${esc(lab)}</b><span class="id">${esc(L.id)}</span></span>` +
    `<span class="ds-seg" role="radiogroup" aria-label="${esc(lab)}">${seg}</span>` +
    `<span class="ln2"><span class="tk" aria-live="polite"></span>` +
    `<label class="vol"><span>${esc(tText("Vol"))}</span>` +
    `<input type="range" min="0" max="100" step="5" value="${Math.round(L.volume * 100)}"` +
    ` aria-label="${esc(tText("Volume, {{loop}}", { loop: lab }))}">` +
    `<output>${Math.round(L.volume * 100)}</output></label></span></li>`;
}

function paintKeys() {
  $("keys").innerHTML = S.loops.map(keyHtml).join("");
  S.loops.forEach(paintKey);
}

function paintKey(L) {
  const li = $(`key-${L.id}`);
  if (!li) return;
  li.dataset.state = L.state;
  li.querySelectorAll("[data-set]").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.set === L.state)));
  const vol = li.querySelector("input[type=range]");
  if (L.state === "OFF") setDisabled(vol, tText("Monitor the loop to hear it")); else setEnabled(vol);
  vol.disabled = L.state === "OFF";
  const tk = li.querySelector(".tk");
  const talkers = talkersOf(L);
  const audible = (L.speakers || []).some((p) => p && !p.isLocal);
  const mine = L.id === S.talkId && S.tx;
  li.classList.toggle("is-tx", mine);
  li.classList.toggle("is-heard", !mine && audible);     // LiveKit active speaker (audio level)
  li.dataset.talkers = String(talkers.length);
  li.classList.toggle("is-stale", L.conn === "reconnecting" || L.conn === "connecting");
  if (L.state === "OFF") {
    tk.innerHTML = "";
  } else if (L.conn === "failed") {
    tk.innerHTML = chip("alarm", tText("Lost"), "alarm-up", L.error || "");
  } else if (L.conn === "connecting") {
    tk.innerHTML = `<span>${esc(tText("connecting…"))}</span>`;
  } else if (L.conn === "reconnecting") {
    tk.innerHTML = `<span>${esc(tText("reconnecting, {{s}} s", { s: secsSince(L.since) }))}</span>`;
  } else if (L.state === "TALK" && S.micError) {
    tk.innerHTML = chip("alarm", tText("Microphone blocked"), "alarm-up", S.micError);
  } else if (talkers.length) {
    tk.innerHTML = talkers.slice(0, 3).map((p) => {
      const pos = (p.attributes || {}).position || "";
      const unv = (p.attributes || {}).verified === "0" ? ` ${tText("(unverified)")}` : "";
      const name = p.isLocal ? tText("you") : (p.name || p.identity || "");
      return `<i aria-hidden="true"></i><span class="pos">${esc(posLabel(pos))}</span>` +
        `<span>·</span><span class="who">${esc(name + unv)}</span>`;
    }).join(`<span>,</span>`);
  } else {
    const n = L.room ? L.room.remoteParticipants.size : 0;
    tk.innerHTML = `<span>${esc(tText("{{n}} on the loop", { n: n + 1 }))}</span>`;
  }
}

function paintPtt() {
  const btn = $("ptt"), latch = $("latch");
  const L = S.loops.find((x) => x.id === S.talkId);
  let reason = "";
  if (!L) reason = tText("Set one loop to TALK first");
  else if (S.micError) reason = tText("Microphone blocked: allow it in the browser, then choose TALK again");
  else if (!L.mic) reason = tText("Opening the microphone…");
  else if (L.conn !== "connected") reason = tText("The talk loop is not connected");
  if (reason) {
    setDisabled(btn, reason); setDisabled(latch, reason);
    $("ptt-l").textContent = tText("Push to talk");
    $("ptt-s").textContent = reason;
  } else {
    setEnabled(btn); setEnabled(latch);
    $("ptt-l").textContent = S.tx ? tText("TALKING") : tText("Hold to talk");
    $("ptt-s").textContent = loopLabel(L);
  }
  btn.classList.toggle("is-active", !!S.tx);
  btn.classList.toggle("is-armed", S.latched);
  latch.setAttribute("aria-pressed", String(S.latched));
  latch.classList.toggle("is-armed", S.latched);
  $("ptt-note").textContent = S.latched
    ? tText("Latched: your microphone is open on {{loop}}. Press Latch again to close it.", { loop: L ? loopLabel(L) : "" })
    : tText("Hold Space or the button to talk. Release to stop.");
  if (L) paintKey(L);
}

function showBanner(kind, html) {
  const b = $("banner");
  if (!html) { b.hidden = true; b.innerHTML = ""; return; }
  b.hidden = false;
  b.innerHTML = `<div class="ds-banner ${kind}" role="status">${html}</div>`;
}

/* Who is keyed on a loop: a participant whose microphone is unmuted (it is
 * published muted and opened only by push-to-talk or latch), plus anyone the
 * server reports as speaking. Keyed is stable for the whole transmission,
 * where the audio-level "active speaker" flickers between words. */
function talkersOf(L) {
  const out = new Map();
  const room = L.room;
  if (room) {
    for (const p of room.remoteParticipants.values()) {
      const pub = p.getTrackPublication && p.getTrackPublication(LK.Track.Source.Microphone);
      if (pub && !pub.isMuted) out.set(p.identity, p);
    }
    if (L.id === S.talkId && S.tx) out.set(room.localParticipant.identity, room.localParticipant);
  }
  for (const p of L.speakers || []) if (p && !out.has(p.identity)) out.set(p.identity, p);
  return [...out.values()];
}

/* ── LiveKit: one room per loop ───────────────────────────────────────── */
function newRoom(L) {
  const room = new LK.Room({
    adaptiveStream: false, dynacast: false, disconnectOnPageLeave: true,
    audioCaptureDefaults: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
  });
  const E = LK.RoomEvent;
  room.on(E.TrackSubscribed, (track) => {
    if (track.kind !== "audio") return;
    const el = track.attach();
    $("sink").appendChild(el);
    try { track.setVolume(L.volume); } catch (e) { el.volume = L.volume; }
    L.tracks.add(track);
  });
  room.on(E.TrackUnsubscribed, (track) => {
    track.detach().forEach((el) => el.remove());
    L.tracks.delete(track);
  });
  room.on(E.ActiveSpeakersChanged, (speakers) => { L.speakers = speakers; paintKey(L); });
  room.on(E.ParticipantConnected, () => paintKey(L));
  for (const ev of [E.TrackMuted, E.TrackUnmuted, E.TrackPublished, E.TrackUnpublished]) room.on(ev, () => paintKey(L));
  room.on(E.ParticipantDisconnected, () => paintKey(L));
  room.on(E.Reconnecting, () => { L.conn = "reconnecting"; L.since = Date.now(); paintKey(L); paintConn(); paintPtt(); });
  room.on(E.Reconnected, () => { L.conn = "connected"; paintKey(L); paintConn(); paintPtt(); });
  room.on(E.Disconnected, (reason) => {
    if (L.room !== room) return;                       // we closed it on purpose
    L.conn = "failed"; L.error = describeDisconnect(reason); L.room = null; L.mic = null;
    if (S.talkId === L.id) setTx(false);
    paintKey(L); paintConn(); paintPtt();
  });
  room.on(E.AudioPlaybackStatusChanged, () => {
    S.audioBlocked = !room.canPlaybackAudio; paintAudioBanner();
  });
  return room;
}

function describeDisconnect(reason) {
  const R = LK.DisconnectReason || {};
  if (reason === R.DUPLICATE_IDENTITY) return tText("You joined this loop from another window");
  if (reason === R.PARTICIPANT_REMOVED) return tText("Removed from the loop");
  if (reason === R.ROOM_DELETED) return tText("The loop was closed on the server");
  if (reason === R.JOIN_FAILURE) return tText("Could not reach the voice server");
  return tText("Connection to the voice server lost");
}

function paintAudioBanner() {
  if (S.audioBlocked) {
    showBanner("stale", `${esc(tText("The browser blocked audio playback."))} ` +
      `<button type="button" class="ds-btn sm" id="audio-on">${esc(tText("Enable audio"))}</button>`);
  } else showBanner(null);
}

async function connectLoop(L) {
  if (L.room || !S.tok) return;
  const room = newRoom(L);
  L.room = room; L.conn = "connecting"; L.since = Date.now(); L.error = null;
  paintKey(L); paintConn();
  try {
    await room.connect(S.tok.url, L.token, { autoSubscribe: true });
    if (L.room !== room) { room.disconnect(); return; }
    L.conn = "connected";
    try { await room.startAudio(); } catch (e) { /* AudioPlaybackStatusChanged reports it */ }
    S.audioBlocked = !room.canPlaybackAudio; paintAudioBanner();
    if (L.state === "TALK") await openMic(L);
  } catch (e) {
    if (L.room === room) { L.room = null; L.conn = "failed"; L.error = tText("Could not reach the voice server"); }
    try { console.warn("voice: connect failed", L.id, e); } catch (e2) { /* */ }
  }
  paintKey(L); paintConn(); paintPtt();
}

async function disconnectLoop(L) {
  const room = L.room;
  L.room = null; L.conn = "off"; L.speakers = []; L.mic = null;
  if (S.talkId === L.id) setTx(false);
  for (const tr of L.tracks) tr.detach().forEach((el) => el.remove());
  L.tracks.clear();
  if (room) { try { await room.disconnect(); } catch (e) { /* already gone */ } }
  paintKey(L); paintConn(); paintPtt();
}

async function openMic(L) {
  if (!L.room || L.mic) return;
  try {
    const track = await LK.createLocalAudioTrack({
      echoCancellation: true, noiseSuppression: true, autoGainControl: true,
    });
    await track.mute();                                  // closed until push-to-talk
    if (!L.room || L.state !== "TALK") { track.stop(); return; }
    await L.room.localParticipant.publishTrack(track, { source: LK.Track.Source.Microphone, dtx: true, red: true });
    L.mic = track; S.micError = null;
  } catch (e) {
    S.micError = (e && e.name === "NotAllowedError")
      ? tText("Microphone permission denied") : tText("No microphone available");
    try { console.warn("voice: microphone", e); } catch (e2) { /* */ }
  }
  paintKey(L); paintPtt();
}

async function closeMic(L) {
  const tr = L.mic; L.mic = null;
  if (!tr) return;
  if (S.talkId === L.id) setTx(false);
  try { if (L.room) await L.room.localParticipant.unpublishTrack(tr, true); } catch (e) { /* */ }
  try { tr.stop(); } catch (e) { /* */ }
}

/* ── key state changes ────────────────────────────────────────────────── */
async function setState(L, st) {
  if (!STATES.includes(st) || RANK[st] > RANK[L.access] || st === L.state) return;
  const prev = L.state;
  if (st === "TALK" && S.talkId && S.talkId !== L.id) {       // talk on one loop at a time
    const old = S.loops.find((x) => x.id === S.talkId);
    if (old) { old.state = "MON"; await closeMic(old); paintKey(old); }
  }
  L.state = st;
  if (st === "TALK") { S.talkId = L.id; S.micError = null; }
  else if (S.talkId === L.id) { S.talkId = null; S.latched = false; await closeMic(L); }
  savePrefs();
  paintKey(L); paintPtt();
  if (!S.joined) return;
  if (st === "OFF") return disconnectLoop(L);
  if (prev === "OFF") return connectLoop(L);
  if (st === "TALK") return openMic(L);
}

/* ── push-to-talk ─────────────────────────────────────────────────────── */
async function setTx(on) {
  const L = S.loops.find((x) => x.id === S.talkId);
  const want = !!on && !!L && !!L.mic && L.conn === "connected";
  if (want === S.tx) return;
  S.tx = want;
  if (!want) S.latched = S.latched && !!L && !!L.mic;
  try { if (L && L.mic) { if (want) await L.mic.unmute(); else await L.mic.mute(); } } catch (e) { /* */ }
  paintPtt(); paintConn();
}
function pttDown(src) {
  if ($("ptt").getAttribute("aria-disabled") === "true") return;
  S.holding.add(src); setTx(true);
}
function pttUp(src) {
  S.holding.delete(src);
  if (!S.holding.size && !S.latched) setTx(false);
}
function toggleLatch() {
  if ($("latch").getAttribute("aria-disabled") === "true") return;
  S.latched = !S.latched;
  setTx(S.latched || S.holding.size > 0);
  paintPtt();
}
function isTyping(el) {
  if (!el) return false;
  const tag = (el.tagName || "").toLowerCase();
  return tag === "textarea" || tag === "select" || el.isContentEditable ||
    (tag === "input" && !["range", "checkbox", "radio", "button"].includes((el.type || "").toLowerCase()));
}

/* ── join / leave / position ──────────────────────────────────────────── */
function buildLoops(tok) {
  const saved = (prefs()[tok.position] || {});
  const old = new Map(S.loops.map((L) => [L.id, L]));
  S.loops = tok.loops.map((x) => {
    const was = old.get(x.id);
    const keep = saved[x.id] || {};
    let state = was ? was.state : (keep.state || x.start);
    if (!STATES.includes(state) || RANK[state] > RANK[x.access]) state = x.start;
    return {
      id: x.id, label: x.label, colour: x.colour, access: x.access, token: x.token,
      state, volume: was ? was.volume : (typeof keep.volume === "number" ? keep.volume : 0.8),
      room: null, conn: "off", since: 0, speakers: [], tracks: new Set(), mic: null, error: null,
    };
  });
  const talk = S.loops.filter((L) => L.state === "TALK");
  talk.slice(1).forEach((L) => { L.state = "MON"; });
  S.talkId = talk.length ? talk[0].id : null;
}

function scheduleRefresh() {
  clearTimeout(S.refreshTimer);
  if (!S.tok) return;
  S.refreshTimer = setTimeout(async () => {
    try {
      const tok = await getTokens(S.position);
      S.tok = tok;
      const by = new Map(tok.loops.map((x) => [x.id, x.token]));
      S.loops.forEach((L) => { if (by.has(L.id)) L.token = by.get(L.id); });
    } catch (e) {
      try { console.warn("voice: token refresh failed", e); } catch (e2) { /* */ }
    }
    scheduleRefresh();
  }, Math.max(30, S.tok.refresh_in_s || 450) * 1000);
}

async function join() {
  if (S.joining) return;
  const btn = $("join-btn");
  if (btn.getAttribute("aria-disabled") === "true") return;
  if (!$("name-field").hidden && !currentName()) {
    $("name").setAttribute("aria-invalid", "true"); $("name").focus(); return;
  }
  // Unlock audio inside the click itself (autoplay policy).
  try { const ac = new (window.AudioContext || window.webkitAudioContext)(); ac.resume().finally(() => ac.close()); } catch (e) { /* */ }
  S.joining = true; S.lastError = null; btn.setAttribute("aria-busy", "true");
  try {
    if (currentName()) try { localStorage.setItem(LS_NAME, currentName()); } catch (e) { /* */ }
    S.cfg = await getConfig();               // identity with the typed name
    const tok = await getTokens(S.position);
    S.tok = tok; S.joined = true;
    buildLoops(tok);
    $("join").hidden = true; $("keys").hidden = false; $("pttbar").hidden = false;
    paintHeader(); paintKeys(); paintPtt();
    scheduleRefresh();
    await Promise.all(S.loops.filter((L) => L.state !== "OFF").map(connectLoop));
  } catch (e) {
    S.lastError = e.message || String(e);
    showBanner("alarm", esc(tText("Could not join: {{why}}", { why: S.lastError })));
  } finally {
    S.joining = false; btn.removeAttribute("aria-busy"); paintConn();
  }
}

async function leave() {
  clearTimeout(S.refreshTimer);
  S.latched = false; S.holding.clear(); await setTx(false);
  await Promise.all(S.loops.map((L) => disconnectLoop(L)));
  S.joined = false; S.tok = null;
  $("join").hidden = false; $("keys").hidden = true; $("pttbar").hidden = true;
  showBanner(null); paintConn();
}

async function switchPosition(pos) {
  if (!pos || pos === S.position) return;
  S.position = pos;
  if ($("pos").value !== pos) $("pos").value = pos;
  if (!S.joined) return;
  await leave();
  S.loops = [];
  await join();
}

/* ── wiring ───────────────────────────────────────────────────────────── */
function wire() {
  $("join-btn").addEventListener("click", join);
  $("leave").addEventListener("click", leave);
  $("pos").addEventListener("change", (e) => switchPosition(e.target.value));
  $("popout").addEventListener("click", async () => {
    const w = window.open("/voice", "c2o-voice", "popup,width=460,height=780");
    if (w && IN_FRAME) { await leave(); tell({ action: "popped-out" }); }
  });
  $("keys").addEventListener("click", (e) => {
    const b = e.target.closest("[data-set]");
    if (!b || b.getAttribute("aria-disabled") === "true") return;
    const L = S.loops.find((x) => x.id === b.closest(".key").dataset.loop);
    if (L) setState(L, b.dataset.set);
  });
  $("keys").addEventListener("keydown", (e) => {     // arrows move within a key's radio group
    const b = e.target.closest("[data-set]");
    if (!b || (e.key !== "ArrowLeft" && e.key !== "ArrowRight")) return;
    e.preventDefault();
    const bs = Array.from(b.parentElement.querySelectorAll("[data-set]"));
    bs[(bs.indexOf(b) + (e.key === "ArrowRight" ? 1 : bs.length - 1)) % bs.length].focus();
  });
  $("keys").addEventListener("input", (e) => {
    if (e.target.type !== "range") return;
    const L = S.loops.find((x) => x.id === e.target.closest(".key").dataset.loop);
    if (!L) return;
    L.volume = Number(e.target.value) / 100;
    e.target.nextElementSibling.textContent = e.target.value;
    for (const tr of L.tracks) { try { tr.setVolume(L.volume); } catch (err) { /* */ } }
    savePrefs();
  });
  document.addEventListener("click", (e) => {
    if (e.target.closest("#rejoin")) { leave().then(join); }
    if (e.target.closest("#audio-on")) {
      S.loops.forEach((L) => L.room && L.room.startAudio().catch(() => {}));
      S.audioBlocked = false; paintAudioBanner();
    }
  });
  const ptt = $("ptt");
  ptt.addEventListener("pointerdown", (e) => { e.preventDefault(); try { ptt.setPointerCapture(e.pointerId); } catch (err) { /* */ } pttDown("pointer"); });
  for (const ev of ["pointerup", "pointercancel", "lostpointercapture"]) ptt.addEventListener(ev, () => pttUp("pointer"));
  ptt.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); if (!e.repeat) pttDown("enter"); } });
  ptt.addEventListener("keyup", (e) => { if (e.key === "Enter") pttUp("enter"); });
  $("latch").addEventListener("click", toggleLatch);
  // Space = push-to-talk anywhere in the panel except while typing. Captured
  // first, so a focused button is never "clicked" by it.
  document.addEventListener("keydown", (e) => {
    if (e.code !== "Space" || !S.joined || isTyping(e.target)) return;
    e.preventDefault(); e.stopPropagation();
    if (!e.repeat) pttDown("key");
  }, true);
  document.addEventListener("keyup", (e) => {
    if (e.code !== "Space" || isTyping(e.target)) return;
    e.preventDefault(); e.stopPropagation(); pttUp("key");
  }, true);
  // Never leave a microphone open by accident: losing focus releases a held
  // (not latched) talk; leaving the page closes everything.
  window.addEventListener("blur", () => { S.holding.clear(); if (!S.latched) setTx(false); });
  window.addEventListener("pagehide", () => { S.loops.forEach((L) => L.room && L.room.disconnect()); });
  // Follow the MCS position selection (same origin) unless an instructor
  // role was picked here.
  window.addEventListener("storage", (e) => {
    if (e.key !== "mcs.position" || !e.newValue) return;
    if ((S.cfg.role_positions || []).includes(S.position)) return;
    if ((S.cfg.positions || []).includes(e.newValue)) switchPosition(e.newValue);
  });
  window.addEventListener("message", (e) => {
    if (e.origin !== location.origin || !e.data || e.data.source !== "c2o-voice-host") return;
    if (e.data.action === "leave") leave();
  });
  setInterval(() => { if (S.joined) { paintConn(); S.loops.filter((L) => L.conn === "reconnecting").forEach(paintKey); } }, 1000);
  onLangChange(() => { paintHeader(); if (S.joined) { paintKeys(); paintPtt(); } });
}

async function boot() {
  try { if (localStorage.getItem("mcs.theme") === "light") document.documentElement.setAttribute("data-theme", "light"); } catch (e) { /* */ }
  await I18n.ready;
  if (IN_FRAME) {
    // Docked in the MCS: the console's language toggle rules (one setting,
    // localStorage "c2o.lang"); no second toggle in a 400 px panel.
    $("lang-toggle").hidden = true;
    window.addEventListener("storage", (e) => { if (e.key === "c2o.lang" && e.newValue) I18n.setLang(e.newValue); });
  } else {
    mountLangToggle($("lang-toggle"));
  }
  wire();
  if (!LK) {
    S.cfg = { available: false, reason: "no-client" };
    setDisabled($("join-btn"), tText("The voice client library did not load"));
    paintConn(); return;
  }
  try { $("name").value = localStorage.getItem(LS_NAME) || ""; } catch (e) { /* */ }
  try {
    S.cfg = await getConfig();
  } catch (e) {
    S.cfg = { available: false, reason: e.code === "sign-in" ? "sign-in" : "bad-config", positions: [] };
  }
  $("name-field").hidden = !S.cfg.needs_name && !(S.cfg.identity && !S.cfg.identity.verified);
  let pos = null;
  try { pos = new URLSearchParams(location.search).get("position") || localStorage.getItem("mcs.position"); } catch (e) { /* */ }
  const ids = S.cfg.positions || [];
  S.position = ids.includes(pos) ? pos : (ids.includes("flight_director") ? "flight_director" : ids[0]);
  paintHeader();
  // No auto-join: audio and the microphone start only from the Join click
  // in this document (a click in the MCS page does not activate a child frame).
  if (!S.cfg.available) setDisabled($("join-btn"), reasonText(S.cfg.reason));
}

boot();
