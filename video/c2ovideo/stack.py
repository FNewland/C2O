"""Run the tools on capture ports, with throw-away state.

``spacecdf``: the SpaceCDF server on :18800 serving the built frontend, with a
fresh database and logbook folder under ``video/out/_stack/``.
``sim``: simulator, MCS, planner, orbit tools and docs viewer on their usual
ports from ``sim/`` (a seeded, repeatable run; pass overrides on).
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from .storyboard import REPO, ROOT

STATE = ROOT / "out" / "_stack"
DESIGN = REPO / "design"
SIM = REPO / "sim"


def _free(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def _wait(url: str, secs: float = 60) -> bool:
    t = time.time()
    while time.time() - t < secs:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def _py(venv: Path) -> str:
    p = venv / ".venv" / "bin" / "python"
    return str(p) if p.exists() else sys.executable


def _spawn(name: str, cmd: list[str], env: dict, cwd: Path) -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    log = open(STATE / f"{name}.log", "w")
    p = subprocess.Popen(cmd, env=env, cwd=str(cwd), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    return p.pid


def up_spacecdf() -> dict:
    port = int(os.environ.get("C2O_VIDEO_SPACECDF_PORT", 18800))
    if not _free(port):
        raise SystemExit(f"port {port} is busy (stack already up?)")
    d = STATE / "spacecdf"
    if d.exists():
        shutil.rmtree(d)
    (d / "data").mkdir(parents=True)
    dist = DESIGN / "frontend" / "dist"
    if not (dist / "index.html").exists():
        raise SystemExit("build the SpaceCDF frontend first: (cd design/frontend && npm ci && npm run build)")
    pkgs = ["spacecdf-server", "spacecdf-common", "spacecdf-kb", "spacecdf-agents", "spacecdf-ai"]
    env = dict(os.environ,
               PYTHONPATH=os.pathsep.join([str(DESIGN / "packages" / p / "src") for p in pkgs] + [str(DESIGN)]),
               DATABASE_URL=f"sqlite+aiosqlite:///{d / 'video.db'}", SPACECDF_STATIC_DIR=str(dist),
               SPACECDF_DATA_DIR=str(d / "data"), SMO_LOGBOOK_DIR=str(d / "logbook"), SPACECDF_INSTRUCTORS="")
    pid = _spawn("spacecdf", [_py(DESIGN), "-m", "uvicorn", "spacecdf_server.app:app", "--host", "127.0.0.1",
                              "--port", str(port), "--log-level", "warning"], env, DESIGN)
    ok = _wait(f"http://127.0.0.1:{port}/api/health", 90) or _wait(f"http://127.0.0.1:{port}/", 30)
    return {"spacecdf": {"pid": pid, "url": f"http://127.0.0.1:{port}", "ok": ok}}


def up_sim() -> dict:
    cfg = SIM / "configs" / "eosat1"
    bin_ = SIM / ".venv" / "bin"
    env = dict(os.environ, PYTHONUNBUFFERED="1", SMO_UI="modern", SMO_LOGBOOK_DIR=str(STATE / "sim-logbook"))
    out = {}
    plan = [
        ("sim", [str(bin_ / "smo-simulator"), "--config", str(cfg)], 8080, "/"),
        ("mcs", [str(bin_ / "smo-mcs"), "--config", str(cfg), "--port", "9090", "--connect", "localhost:8002"], 9090, "/"),
        ("planner", [str(bin_ / "smo-planner"), "--config", str(cfg), "--port", "9091"], 9091, "/"),
        ("tools", [_py(SIM), str(SIM / "tools" / "orbit_tools.py"), "--serve", "--port", "8093"], 8093, "/"),
        ("docs", [_py(SIM), str(SIM / "tools" / "doc_viewer.py"), "--port", "8094"], 8094, "/"),
    ]
    for name, cmd, port, path in plan:
        if not _free(port):
            raise SystemExit(f"port {port} is busy: stop the running simulator first (./stop.sh)")
        pid = _spawn(name, cmd, env, SIM)
        ok = _wait(f"http://127.0.0.1:{port}{path}", 60)
        out[name] = {"pid": pid, "url": f"http://127.0.0.1:{port}", "ok": ok}
        if name == "sim":
            req = urllib.request.Request("http://127.0.0.1:8080/api/command", method="POST",
                                         data=json.dumps({"type": "override_passes", "enabled": True}).encode(),
                                         headers={"Content-Type": "application/json"})
            try:
                urllib.request.urlopen(req, timeout=5)
            except Exception:
                pass
    return out


def run(action: str, which: str) -> int:
    f = STATE / f"{which}.json"
    if action == "up":
        info = up_spacecdf() if which == "spacecdf" else up_sim()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(info, indent=1))
        for k, v in info.items():
            print(f"{k:10} {v['url']}  {'up' if v['ok'] else 'NOT RESPONDING (see ' + str(STATE / (k + '.log')) + ')'}")
        return 0 if all(v["ok"] for v in info.values()) else 1
    if action == "down":
        if not f.exists():
            print("nothing to stop")
            return 0
        for k, v in json.loads(f.read_text()).items():
            try:
                os.killpg(v["pid"], signal.SIGTERM)
                print("stopped", k)
            except ProcessLookupError:
                pass
        f.unlink()
        return 0
    print(f.read_text() if f.exists() else "not running")
    return 0
