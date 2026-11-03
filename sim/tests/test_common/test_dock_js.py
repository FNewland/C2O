"""The shared right dock (smo_common/ui/dock.js): side panels stand side by
side beside the work area and never overlap; when they do not fit, the one
opened longest ago closes. Run under node with a minimal DOM stub, plus the
contract of the pages that use it (MCS alarms, logbook, voice loops)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
UI = REPO / "packages" / "smo-common" / "src" / "smo_common" / "ui"
MODERN = REPO / "packages" / "smo-mcs" / "src" / "smo_mcs" / "static" / "modern"
NODE = shutil.which("node") or shutil.which("nodejs")
needs_node = pytest.mark.skipif(not NODE, reason="node not installed")

STUB = r"""
class El {
  constructor(id, w = 0) { this.id = id; this.w = w; this.children = []; this.parentElement = null;
    this.style = { setProperty() {} }; this._cls = new Set(); this.isMain = false;
    this.classList = { add: (c) => this._cls.add(c), remove: (c) => this._cls.delete(c),
      contains: (c) => this._cls.has(c) }; }
  appendChild(c) { c.parentElement = this; this.children.push(c); return c; }
  matches() { return this.isMain; }
  getBoundingClientRect() { return { width: this.w }; }
  get clientWidth() { return this.w; }
}
const shell = new El("shell", 0);
const rail = new El("rail", 64), main = new El("main", 0), host = new El("c2o-dock", 0);
main.isMain = true;
shell.appendChild(rail); shell.appendChild(main); shell.appendChild(host);
let narrow = false;
globalThis.window = { matchMedia: () => ({ matches: narrow }), addEventListener() {} };
globalThis.document = { getElementById: (id) => (id === "c2o-dock" ? host : null) };
"""


def run(snippet: str, tmp_path: Path):
    (tmp_path / "dock.mjs").write_text((UI / "dock.js").read_text(encoding="utf-8"))
    (tmp_path / "run.mjs").write_text(
        STUB + 'const D = await import("./dock.mjs");\n'
        f"const out = (() => {{ {snippet} }})();\nconsole.log(JSON.stringify(out));\n")
    p = subprocess.run([NODE, str(tmp_path / "run.mjs")], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


PANELS = """
  const closed = [];
  const mk = (name, width, min, order) => {
    const el = new El(name);
    const d = D.dockPanel(el, { width, min, order, close: (o) => closed.push([name, !!o.evicted]) });
    return { el, d };
  };
  const al = mk("alarms", 540, 360, 1), lb = mk("logbook", 440, 360, 2), vo = mk("voice", 400, 340, 3);
  const open = () => [al, lb, vo].filter((p) => p.el.classList.contains("is-dock-open")).map((p) => p.el.id);
"""


@needs_node
@pytest.mark.parametrize("width, both_fit", [(1440, True), (1280, True), (1100, False)])
def test_two_panels_side_by_side_when_they_fit(tmp_path, width, both_fit):
    out = run(PANELS + f"""
      shell.w = {width};
      al.d.opened(); lb.d.opened();
      return {{ open: open(), closed, docked: al.d.docked && host.children.length === 3 }};
    """, tmp_path)
    assert out["docked"]
    if both_fit:
        assert out["open"] == ["alarms", "logbook"] and out["closed"] == []
    else:
        assert out["open"] == ["logbook"] and out["closed"] == [["alarms", True]]


@needs_node
def test_the_panel_opened_longest_ago_makes_room(tmp_path):
    out = run(PANELS + """
      shell.w = 1440;
      al.d.opened(); lb.d.opened(); vo.d.opened();        // three do not fit at 1440
      const a = open();
      al.d.opened();                                        // alarms again: logbook is now oldest
      return { a, b: open(), closed };
    """, tmp_path)
    assert out["a"] == ["logbook", "voice"]
    assert out["b"] == ["alarms", "voice"]
    assert out["closed"] == [["alarms", True], ["logbook", True]]


@needs_node
def test_narrow_screens_show_one_panel_at_a_time(tmp_path):
    out = run(PANELS + """
      shell.w = 390; narrow = true;
      lb.d.opened(); al.d.opened();
      const a = open();
      al.d.closed();
      return { a, b: open() };
    """, tmp_path)
    assert out["a"] == ["alarms"] and out["b"] == []


def test_pages_put_their_side_panels_in_the_dock():
    html = (MODERN / "index.html").read_text(encoding="utf-8")
    dock_at = html.index('<div id="c2o-dock">')
    assert html.index('<main class="work"') < dock_at < html.index('<aside id="alarm-drawer"')
    mcs = (MODERN / "mcs.js").read_text(encoding="utf-8")
    assert "alarmDock = dockPanel(d, {" in mcs
    voice = (MODERN / "voice-dock.js").read_text(encoding="utf-8")
    assert "slot = dockPanel(dock, {" in voice
    # the iframe is placed after the panel moved: moving a loaded frame reloads it
    assert voice.index("slot = dockPanel(dock") < voice.index("dock.appendChild(frame)")
    lb = (UI / "logbook.js").read_text(encoding="utf-8")
    assert "S.dock = dockPanel(S.panel, {" in lb and "if (!S.dock.docked) document.body.appendChild(S.panel);" in lb
    css = (UI / "design-system.css").read_text(encoding="utf-8")
    assert "#c2o-dock > .c2o-docked" in css
    # the page grids follow the work area, not the viewport
    assert "container-name:work" in html and "@container work" in html
