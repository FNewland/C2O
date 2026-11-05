// Drawn pointer, click ripple and highlight ring for headless screen captures.
// Injected into every page of a capture (Playwright add_init_script). The
// capture runner calls window.__c2oCursor.move/click/ring; nothing here
// intercepts input, so the page behaves exactly as for a user.
(() => {
  if (window.__c2oCursor) return;
  const KEY = "c2o.video.cursor";
  const css = `
    #c2o-vcur{position:fixed;left:0;top:0;width:26px;height:26px;z-index:2147483647;pointer-events:none;
      transform:translate(-3px,-2px);filter:drop-shadow(0 1px 2px rgba(0,0,0,.45));will-change:left,top}
    .c2o-vrip{position:fixed;z-index:2147483646;pointer-events:none;width:44px;height:44px;margin:-22px 0 0 -22px;
      border-radius:50%;border:3px solid #ffb000;opacity:.95;animation:c2oRip .55s ease-out forwards}
    @keyframes c2oRip{from{transform:scale(.35);opacity:.95}to{transform:scale(1.25);opacity:0}}
    .c2o-vring{position:fixed;z-index:2147483645;pointer-events:none;border:3px solid #ffb000;border-radius:8px;
      box-shadow:0 0 0 4000px rgba(0,0,0,.18),0 0 18px 2px rgba(255,176,0,.65);transition:opacity .35s;opacity:0}
  `;
  const svg = `<svg viewBox="0 0 24 24" width="26" height="26" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 2 L3 19 L7.6 14.9 L10.6 21.4 L13.4 20.1 L10.5 13.8 L16.6 13.6 Z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>`;
  let x = 0, y = 0, el = null;
  try { const s = JSON.parse(sessionStorage.getItem(KEY) || "null"); if (s) { x = s[0]; y = s[1]; } } catch (e) {}
  function ensure() {
    if (el && document.body && document.body.contains(el)) return el;
    if (!document.body) return null;
    if (!document.getElementById("c2o-vstyle")) {
      const st = document.createElement("style"); st.id = "c2o-vstyle"; st.textContent = css;
      (document.head || document.documentElement).appendChild(st);
    }
    el = document.createElement("div"); el.id = "c2o-vcur"; el.innerHTML = svg;
    el.style.left = x + "px"; el.style.top = y + "px";
    document.body.appendChild(el);
    return el;
  }
  const ease = (t) => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  window.__c2oCursor = {
    pos() { return [x, y]; },
    move(tx, ty, ms) {
      const c = ensure(); if (!c) return;
      const sx = x, sy = y, t0 = performance.now(), d = Math.max(1, ms || 600);
      return new Promise((res) => {
        function f(now) {
          const k = Math.min(1, (now - t0) / d), e = ease(k);
          x = sx + (tx - sx) * e; y = sy + (ty - sy) * e;
          c.style.left = x + "px"; c.style.top = y + "px";
          if (k < 1) requestAnimationFrame(f); else { try { sessionStorage.setItem(KEY, JSON.stringify([x, y])); } catch (e) {} res(); }
        }
        requestAnimationFrame(f);
      });
    },
    click() {
      ensure();
      const r = document.createElement("div"); r.className = "c2o-vrip";
      r.style.left = x + "px"; r.style.top = y + "px";
      document.body.appendChild(r); setTimeout(() => r.remove(), 700);
    },
    ring(left, top, w, h, secs) {
      ensure();
      const r = document.createElement("div"); r.className = "c2o-vring";
      Object.assign(r.style, { left: (left - 6) + "px", top: (top - 6) + "px", width: (w + 12) + "px", height: (h + 12) + "px" });
      document.body.appendChild(r);
      requestAnimationFrame(() => { r.style.opacity = "1"; });
      setTimeout(() => { r.style.opacity = "0"; setTimeout(() => r.remove(), 400); }, Math.max(400, (secs || 2.5) * 1000));
    },
    hide() { if (el) el.style.display = "none"; },
    show() { const c = ensure(); if (c) c.style.display = ""; },
  };
  const boot = () => ensure();
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
