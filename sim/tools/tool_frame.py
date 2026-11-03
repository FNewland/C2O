"""tool_frame.py: the one page frame shared by the sim/tools web pages.

Every tool (delayed TM, orbit tools, documentation, scenario generator, ADCS
viewer) is served on its own public host behind sign-in, so each page must
stand on its own and still read as one product. This module gives them the
same frame, built only on the shared design system (smo_common/ui, mounted at
/static/shared/ by ``smo_common.web.http.setup_tool_app``):

  * ``head(...)``    in <head>: theme chosen before first paint (no flash),
                     the shared stylesheet + language runtime (TOOL_HEAD) and
                     the frame's own rules (tokens only, no hex values).
  * ``bar(...)``     the title bar: "C2O" mark, tool name, a context line,
                     a status slot, the Dark | Light theme switch and the
                     EN | FR language switch.
  * ``SCRIPT``       at the end of <body>: wires the two switches and
                     exposes the shared components as ``window.DS`` for the
                     tools' classic inline scripts. When the bar was built
                     with ``logbook="<tool>"`` it also mounts the participant
                     logbook (smo_common/ui/logbook.js) in the bar; the page
                     supplies its context with ``window.c2oLogbookContext =
                     () => ({...})`` and reaches the panel as
                     ``window.C2O_LOGBOOK`` (the server mounts /api/logbook
                     with ``smo_common.logbook.register_logbook_routes``).

Theme rule (same key as the gallery): ``?theme=`` > localStorage
``c2o.theme`` > the page default (dark: the tools are operations pages).
Language rule: tool-page.js (``?lang=`` > ``c2o.lang`` > default).

Pages never print a server path or a localhost link: they are reached at
tm./orbit./docs./scenarios./adcs.c2o.live.
"""
from __future__ import annotations

import html as _html

#: Theme before first paint; also keeps ?theme= working for screenshots.
_THEME_BOOT = """<script>
(function(){var d=document.documentElement,t=null;
try{t=new URLSearchParams(location.search).get("theme")||localStorage.getItem("c2o.theme");}catch(e){}
if(t!=="light"&&t!=="dark")t=d.getAttribute("data-default-theme")||"dark";
d.setAttribute("data-theme",t);})();
</script>"""

FRAME_CSS = """
/* ── tool frame (sim/tools/tool_frame.py) ── tokens only ───────────── */
html{ scrollbar-gutter:stable; }
body{ min-height:100%; }
.tf-bar{ position:sticky; top:0; z-index:30; display:flex; align-items:center;
  gap:var(--sp-3); min-height:48px; padding:0 var(--sp-5); background:var(--bg);
  border-bottom:1px solid var(--line); }
.tf-mark{ font-family:var(--mono); font-size:var(--fs-label); font-weight:500;
  color:var(--tx2); letter-spacing:.06em; padding-right:var(--sp-3);
  border-right:1px solid var(--line-2); line-height:20px; }
.tf-name{ font-size:var(--fs-value); font-weight:600; color:var(--val);
  white-space:nowrap; letter-spacing:-.005em; }
.tf-meta{ font-size:var(--fs-label); color:var(--tx3); min-width:0; overflow:hidden;
  text-overflow:ellipsis; white-space:nowrap; }
.tf-meta code,.tf-meta .num{ font-family:var(--mono); color:var(--tx2); }
.tf-ctl{ margin-left:auto; display:flex; align-items:center; gap:var(--sp-3); flex:0 0 auto; }
.tf-status{ display:flex; align-items:center; gap:var(--sp-2); font-size:var(--fs-label);
  color:var(--tx2); white-space:nowrap; }
.tf-status:empty{ display:none; }
.tf-main{ padding:var(--sp-4) var(--sp-5) var(--sp-6); }
/* Section heading inside a page: sentence case, weight not caps. */
.tf-h{ font-size:var(--fs-body); font-weight:600; color:var(--tx); }
.tf-sub{ font-size:var(--fs-label); color:var(--tx3); font-weight:400; }
.tf-empty{ padding:var(--sp-5) var(--sp-4); color:var(--tx2); max-width:64ch; }
.tf-empty b{ color:var(--tx); font-weight:600; }
/* A plot frame: hairline, its own scale and units inside. */
.tf-plot{ display:block; width:100%; height:auto; overflow:visible; }
.tf-plot text{ font-family:var(--mono); font-size:12px; fill:var(--tx3); }
.tf-plot .ax{ stroke:var(--line-2); stroke-width:1; fill:none; }
.tf-plot .grid{ stroke:var(--line); stroke-width:1; fill:none; }
@media (max-width:720px){
  .tf-bar{ flex-wrap:wrap; padding:var(--sp-2) var(--sp-4); row-gap:var(--sp-1); }
  .tf-meta{ order:9; flex:1 0 100%; }
  .tf-ctl{ display:contents; }
  .tf-ctl>.ds-seg{ margin-left:auto; }
  .tf-status{ order:10; flex:1 0 100%; white-space:normal; }
  .tf-main{ padding:var(--sp-3) var(--sp-4) var(--sp-5); }
}
@media (max-width:420px){
  .tf-mark{ display:none; }
}
"""


def head(*, default_theme: str = "dark", extra_css: str = "") -> str:
    """Markup for <head>: theme boot, shared DS + language runtime, frame CSS."""
    from smo_common.web.http import TOOL_HEAD
    return (_THEME_BOOT.replace('"dark";', f'"{default_theme}";', 1) + "\n"
            + TOOL_HEAD + f"<style>{FRAME_CSS}{extra_css}</style>\n")


def bar(name_html: str, *, meta_html: str = "", status_id: str = "tf-status",
        logbook: str | None = None) -> str:
    """The title bar. ``name_html`` is trusted markup (usually a data-i18n span).
    ``logbook``: the tool id for the participant logbook button (None: none)."""
    lb = (f'<span id="tf-logbook" data-logbook-tool="{_html.escape(logbook)}"></span>'
          if logbook else "")
    return (
        '<header class="tf-bar">'
        '<span class="tf-mark" aria-hidden="true">C2O</span>'
        f'<h1 class="tf-name">{name_html}</h1>'
        f'<span class="tf-meta" id="tf-meta">{meta_html}</span>'
        '<div class="tf-ctl">'
        f'<span class="tf-status" id="{_html.escape(status_id)}" role="status" aria-live="polite"></span>'
        + lb +
        '<div class="ds-seg" role="group" id="tf-theme" aria-label="Theme" data-i18n-aria-label>'
        '<button type="button" data-theme-set="dark" aria-pressed="true" data-i18n>Dark</button>'
        '<button type="button" data-theme-set="light" aria-pressed="false" data-i18n>Light</button>'
        '</div>'
        '<span id="tf-lang"></span>'
        '</div></header>'
    )


#: End of <body>. Module: runs after the page's own markup is parsed.
SCRIPT = """<script type="module">
import * as DS from "/static/shared/components.js";
window.DS = DS;
const root = document.documentElement;
function paintTheme() {
  const th = root.getAttribute("data-theme") || "dark";
  document.querySelectorAll("#tf-theme [data-theme-set]").forEach((b) =>
    b.setAttribute("aria-pressed", String(b.dataset.themeSet === th)));
}
const seg = document.getElementById("tf-theme");
if (seg) seg.addEventListener("click", (ev) => {
  const b = ev.target.closest("[data-theme-set]");
  if (!b || b.getAttribute("aria-pressed") === "true") return;
  root.setAttribute("data-theme", b.dataset.themeSet);
  try { localStorage.setItem("c2o.theme", b.dataset.themeSet); } catch (e) { /* private mode */ }
  try {   // keep an explicit ?theme= in step, as setLang does for ?lang=
    const u = new URL(location.href);
    if (u.searchParams.has("theme")) { u.searchParams.set("theme", b.dataset.themeSet); history.replaceState(history.state, "", u); }
  } catch (e) { /* no URL */ }
  paintTheme();
  window.dispatchEvent(new CustomEvent("c2o:themechange", { detail: { theme: b.dataset.themeSet } }));
});
paintTheme();
DS.mountLangToggle(document.getElementById("tf-lang"));
const lbSlot = document.getElementById("tf-logbook");
if (lbSlot) {
  const LB = await import("/static/shared/logbook.js");
  window.C2O_LOGBOOK = LB.mountLogbook({
    tool: lbSlot.dataset.logbookTool,
    getContext: () => (typeof window.c2oLogbookContext === "function" ? window.c2oLogbookContext() : {}),
    buttonHost: lbSlot,
  });
  window.C2O_LOGBOOK_MODULE = LB;
}
window.dispatchEvent(new CustomEvent("c2o:frameready"));
</script>"""


def css_var_js() -> str:
    """A tiny helper for canvas/SVG code that needs a token value at draw
    time (Chart.js cannot read CSS variables): ``tok("--tx3")``."""
    return ('const tok = (n) => getComputedStyle(document.documentElement)'
            '.getPropertyValue(n).trim();')
