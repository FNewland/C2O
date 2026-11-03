/* ============================================================================
 * MCS header "Voice" button: opens the voice loops (/voice) as a panel docked
 * to the right of the console, or as a pop-out window from inside the panel.
 * Self-contained (no change to mcs.js): it adds itself to #voice-btn.
 *
 * The panel is a same-origin iframe, so it shares the console's sign-in and
 * reads the position chosen in this header (localStorage "mcs.position").
 * Hiding the dock keeps the loops connected (the frame stays loaded); Leave
 * inside the panel disconnects. The button mirrors the panel's state from
 * its postMessage: connected (check), reconnecting (dashed), lost (filled
 * triangle), microphone open (accent fill).
 * ============================================================================ */
import { tText, onLangChange } from "/static/shared/i18n.js";
import { glyph } from "/static/shared/components.js";

const btn = document.getElementById("voice-btn");
let dock = null, frame = null, state = { conn: "idle", tx: false };

const CSS = `
#voice-dock{flex:0 0 400px;display:flex;flex-direction:column;min-height:0;border-left:1px solid var(--line-2);background:var(--bg)}
#voice-dock[hidden]{display:none}
#voice-dock iframe{flex:1;border:0;width:100%;min-height:0;background:var(--bg)}
#voice-dock.is-overlay{position:fixed;right:0;bottom:0;top:0;width:min(400px,100vw);z-index:40}
#voice-btn .vb{display:inline-flex;width:11px;height:11px}
#voice-btn .vb svg{width:11px;height:11px}
#voice-btn.is-ok .vb{color:var(--ok)}
#voice-btn.is-stale{font-style:italic}
#voice-btn.is-alarm{border-color:var(--alarm);color:var(--alarm)}
#voice-btn.is-tx{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
@media (max-width:999px){#voice-dock{position:fixed;right:0;bottom:0;top:0;width:min(400px,100vw);z-index:40}}
`;

function ensureDock() {
  if (dock) return dock;
  const st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);
  dock = document.createElement("aside");
  dock.id = "voice-dock";
  dock.setAttribute("aria-label", tText("Voice loops"));
  frame = document.createElement("iframe");
  frame.src = "/voice";
  frame.title = tText("Voice loops");
  frame.allow = "microphone; autoplay";
  dock.appendChild(frame);
  const shell = document.querySelector(".shell");
  if (shell) shell.appendChild(dock); else { dock.classList.add("is-overlay"); document.body.appendChild(dock); }
  return dock;
}

function paint() {
  if (!btn) return;
  const open = !!dock && !dock.hidden;
  btn.setAttribute("aria-expanded", String(open));
  btn.classList.toggle("is-ok", state.conn === "ok" && !state.tx);
  btn.classList.toggle("is-stale", state.conn === "stale");
  btn.classList.toggle("is-alarm", state.conn === "alarm");
  btn.classList.toggle("is-tx", !!state.tx);
  const g = state.tx ? "run" : ({ ok: "ack", stale: "stale", alarm: "alarm-up" }[state.conn] || "");
  const label = state.tx ? tText("Voice: talking") : tText("Voice");
  btn.innerHTML = (g ? `<span class="vb" aria-hidden="true">${glyph(g)}</span>` : "") + `<span>${label}</span>`;
  btn.title = open ? tText("Hide the voice loops (they stay connected)") : tText("Show the voice loops");
}

if (btn) {
  btn.setAttribute("aria-controls", "voice-dock");
  btn.addEventListener("click", () => {
    if (!dock) ensureDock();             // first click: create it, shown
    else dock.hidden = !dock.hidden;
    paint();
    if (!dock.hidden) try { frame.focus(); } catch (e) { /* */ }
  });
  window.addEventListener("message", (e) => {
    if (e.origin !== location.origin || !e.data || e.data.source !== "c2o-voice") return;
    if (e.data.action === "popped-out") {
      if (dock) dock.hidden = true;
      state = { conn: "idle", tx: false };
    } else {
      state = { conn: e.data.conn || "idle", tx: !!e.data.tx };
    }
    paint();
  });
  onLangChange(paint);
  paint();
}
