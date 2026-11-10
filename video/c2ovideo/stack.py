"""Run the tools on capture ports, with throw-away state.

``spacecdf``: the SpaceCDF server on :18800 serving the built frontend of this
checkout (rebuilt first with ``vite build`` when missing or stale), with a fresh
database and logbook folder under ``video/out/_stack/``.
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
    for name in ("python", "python3"):
        p = venv / ".venv" / "bin" / name
        if p.exists():
            return str(p)
    return sys.executable


def _sim_venv() -> Path:
    """sim/.venv, the environment sim/start.sh creates (C2O_SIM_VENV overrides)."""
    v = Path(os.environ.get("C2O_SIM_VENV", SIM / ".venv"))
    if not (v / "bin" / "smo-simulator").exists():
        raise SystemExit(
            f"No simulator install in {v}.\n"
            "Create it once with:  python -m c2ovideo stack setup sim\n"
            "If your simulator lives in another environment, point C2O_SIM_VENV at it.")
    return v


def _spawn(name: str, cmd: list[str], env: dict, cwd: Path) -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    log = open(STATE / f"{name}.log", "w")
    p = subprocess.Popen(cmd, env=env, cwd=str(cwd), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    return p.pid


#: What the built frontend is made from: a change to any of these after the build means ``dist`` is stale.
FRONTEND_SOURCES = ("src", "index.html", "package.json", "package-lock.json", "vite.config.ts",
                    "tsconfig.json", "tsconfig.app.json", "tsconfig.node.json")


def frontend_build_problem(frontend: Path) -> str | None:
    """Why ``frontend/dist`` must not be filmed (missing, or older than a source file), else None.

    W0.5: a video recorded from a stale build shows yesterday's UI. ``dist/index.html`` is written
    last by ``vite build``, so its time is the build time.
    """
    index = frontend / "dist" / "index.html"
    if not index.exists():
        return "build the SpaceCDF frontend first: (cd design/frontend && npm ci && npm run build)"
    built = index.stat().st_mtime
    newest, newest_t = None, built
    for name in FRONTEND_SOURCES:
        p = frontend / name
        files = [p] if p.is_file() else (f for f in p.rglob("*") if f.is_file()) if p.is_dir() else []
        for f in files:
            t = f.stat().st_mtime
            if t > newest_t:
                newest, newest_t = f, t
    if newest is None:
        return None
    age_min = (newest_t - built) / 60
    return (f"the SpaceCDF frontend build is stale: {newest.relative_to(frontend)} changed {age_min:.0f} min after "
            f"dist/index.html was built. Rebuild it: (cd design/frontend && npm run build). "
            f"Set C2O_VIDEO_ALLOW_STALE_DIST=1 only to film an old build on purpose.")


def build_frontend(frontend: Path) -> bool:
    """Run ``vite build`` in ``frontend`` (writes ``dist/``). False when vite is not installed there.

    Wave 2: ``stack up spacecdf`` rebuilds a missing or stale build itself, so the server always
    serves the frontend of the checkout it runs from (a git worktree too: its ``node_modules`` may
    be a link to the main checkout's). Only ``vite build`` runs; the type check (``tsc -b``) is the
    test suite's job and its build-info file lives in the shared ``node_modules``.
    """
    vite = frontend / "node_modules" / ".bin" / "vite"
    if not vite.exists():
        return False
    print(f"building the SpaceCDF frontend in {frontend} (vite build) …", flush=True)
    r = subprocess.run([str(vite), "build", "--logLevel", "warn"], cwd=str(frontend))
    if r.returncode != 0:
        raise SystemExit(f"vite build failed in {frontend} (exit {r.returncode})")
    return True


def design_python() -> str:
    """The interpreter that runs the SpaceCDF server: ``C2O_VIDEO_SPACECDF_PYTHON``, else
    ``design/.venv``, else (in a git worktree) the main checkout's ``design/.venv``. The server
    imports the packages of *this* checkout either way (``PYTHONPATH`` comes first)."""
    explicit = os.environ.get("C2O_VIDEO_SPACECDF_PYTHON")
    if explicit:
        return explicit
    candidates = [DESIGN]
    try:
        common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                cwd=str(REPO), capture_output=True, text=True, timeout=10).stdout.strip()
        if common:
            candidates.append(Path(common).parent / "design")
    except Exception:  # noqa: BLE001 — not a git checkout
        pass
    for d in candidates:
        if (d / ".venv" / "bin" / "uvicorn").exists():
            return _py(d)
    raise SystemExit(f"No SpaceCDF install in {DESIGN / '.venv'}.\n"
                     "Create it once with:  python -m c2ovideo stack setup spacecdf\n"
                     "(or point C2O_VIDEO_SPACECDF_PYTHON at a Python that has the server's dependencies)")


def up_spacecdf() -> dict:
    port = int(os.environ.get("C2O_VIDEO_SPACECDF_PORT", 18800))
    if not _free(port):
        raise SystemExit(f"port {port} is busy (stack already up?)")
    frontend = DESIGN / "frontend"
    problem = frontend_build_problem(frontend)
    allow_stale = (frontend / "dist" / "index.html").exists() and os.environ.get("C2O_VIDEO_ALLOW_STALE_DIST") == "1"
    if problem and not allow_stale:
        # rebuild in place unless told not to (C2O_VIDEO_NO_BUILD=1) or vite is not installed
        if os.environ.get("C2O_VIDEO_NO_BUILD") == "1" or not build_frontend(frontend):
            raise SystemExit(problem)
        problem = frontend_build_problem(frontend)
        if problem:
            raise SystemExit(problem)
    py = design_python()
    d = STATE / "spacecdf"
    if d.exists():
        shutil.rmtree(d)
    (d / "data").mkdir(parents=True)
    dist = frontend / "dist"
    pkgs = DESIGN_PACKAGES
    env = dict(os.environ,
               PYTHONPATH=os.pathsep.join([str(DESIGN / "packages" / p / "src") for p in pkgs] + [str(DESIGN)]),
               DATABASE_URL=f"sqlite+aiosqlite:///{d / 'video.db'}", SPACECDF_STATIC_DIR=str(dist),
               SPACECDF_DATA_DIR=str(d / "data"), SMO_LOGBOOK_DIR=str(d / "logbook"), SPACECDF_INSTRUCTORS="")
    pid = _spawn("spacecdf", [py, "-m", "uvicorn", "spacecdf_server.app:app", "--host", "127.0.0.1",
                              "--port", str(port), "--log-level", "warning"], env, DESIGN)
    ok = _wait(f"http://127.0.0.1:{port}/api/health", 90) or _wait(f"http://127.0.0.1:{port}/", 30)
    return {"spacecdf": {"pid": pid, "url": f"http://127.0.0.1:{port}", "ok": ok}}


def up_viz() -> dict:
    """Static server for the explainer pages (video/explainers/) and shared/ui-viz.

    Serves the repository root read-only on :18801, so a page can import
    /shared/ui-viz/*.js and the explainer pages share one origin.
    """
    port = int(os.environ.get("C2O_VIDEO_VIZ_PORT", 18801))
    if not _free(port):
        raise SystemExit(f"port {port} is busy (stack already up?)")
    pid = _spawn("viz", [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1",
                         "--directory", str(REPO)], dict(os.environ), REPO)
    ok = _wait(f"http://127.0.0.1:{port}/video/explainers/", 20)
    return {"viz": {"pid": pid, "url": f"http://127.0.0.1:{port}", "ok": ok}}


def up_sim() -> dict:
    cfg = SIM / "configs" / "eosat1"
    venv = _sim_venv()
    bin_ = venv / "bin"
    py = str(bin_ / "python") if (bin_ / "python").exists() else str(bin_ / "python3")
    # card-start breakpoints (card-LEOP-001 … card-END): the simulator reads
    # workspace/breakpoints at start-up, so make them first if they are missing
    if not (SIM / "workspace" / "breakpoints" / "card-END.json").exists():
        print("flying LEOP + commissioning once to make the card breakpoints (~30 s) …", flush=True)
        r = subprocess.run([py, str(SIM / "tools" / "card_breakpoints.py")], cwd=str(SIM),
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if r.returncode:
            # only the LEOP/commissioning videos need them: carry on without
            print("  ! card breakpoints not made (videos that load card-… will fail):\n    "
                  + (r.stderr.strip().splitlines() or ["?"])[-1], flush=True)
    env = dict(os.environ, PYTHONUNBUFFERED="1", SMO_UI="modern", SMO_LOGBOOK_DIR=str(STATE / "sim-logbook"))
    out = {}
    plan = [
        ("sim", [str(bin_ / "smo-simulator"), "--config", str(cfg)], 8080, "/"),
        ("mcs", [str(bin_ / "smo-mcs"), "--config", str(cfg), "--port", "9090", "--connect", "localhost:8002"], 9090, "/"),
        ("planner", [str(bin_ / "smo-planner"), "--config", str(cfg), "--port", "9091"], 9091, "/"),
        ("tools", [py, str(SIM / "tools" / "orbit_tools.py"), "--serve", "--port", "8093"], 8093, "/"),
        ("docs", [py, str(SIM / "tools" / "doc_viewer.py"), "--port", "8094"], 8094, "/"),
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


SIM_PACKAGES = ["smo-common", "smo-simulator", "smo-mcs", "smo-planner", "smo-rfsim", "smo-link", "smo-gateway"]
DESIGN_PACKAGES = ["spacecdf-common", "spacecdf-kb", "spacecdf-agents", "spacecdf-ai", "spacecdf-server"]


def _newest_python() -> str:
    """A Python >= 3.11 on PATH (the simulator needs 3.11; laptops often default to older)."""
    import shutil
    for name in ("python3.13", "python3.12", "python3.11", "python3"):
        exe = shutil.which(name)
        if not exe:
            continue
        v = subprocess.run([exe, "-c", "import sys; print(sys.version_info[:2] >= (3, 11))"],
                           capture_output=True, text=True).stdout.strip()
        if v == "True":
            return exe
    raise SystemExit("Need Python 3.11 or newer for the tools (brew install python@3.12), then run this again.")


def setup(which: str) -> int:
    """Create sim/.venv or design/.venv and install the packages (editable), as CI does."""
    root, pkgs = (SIM, SIM_PACKAGES) if which == "sim" else (DESIGN, DESIGN_PACKAGES)
    venv = root / ".venv"
    if not (venv / "bin" / "python").exists():
        py = _newest_python()
        print(f"creating {venv} with {py}", flush=True)
        subprocess.run([py, "-m", "venv", str(venv)], check=True)
    pip = [str(venv / "bin" / "python"), "-m", "pip", "install", "-q"]
    subprocess.run(pip + ["--upgrade", "pip"], check=True)
    args = []
    for p in pkgs:
        d = root / "packages" / p
        if d.exists():
            args += ["-e", str(d) + ("[voice,iap]" if p == "smo-mcs" else "")]
    print(f"installing {len(args) // 2} packages into {venv} …", flush=True)
    subprocess.run(pip + args, check=True)
    print("ready")
    return 0


def run(action: str, which: str) -> int:
    if action == "setup":
        return setup(which)
    f = STATE / f"{which}.json"
    if action == "up":
        info = {"spacecdf": up_spacecdf, "viz": up_viz}.get(which, up_sim)()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(info, indent=1))
        for k, v in info.items():
            print(f"{k:10} {v['url']}  {'up' if v['ok'] else 'NOT RESPONDING (see ' + str(STATE / (k + '.log')) + ')'}")
        return 0 if all(v["ok"] for v in info.values()) else 1
    if action == "down":
        if not f.exists():
            print("nothing to stop")
            return 0
        info = json.loads(f.read_text())
        for k, v in info.items():
            try:
                os.killpg(v["pid"], signal.SIGTERM)
                print("stopped", k)
            except ProcessLookupError:
                pass
        f.unlink()
        # wait until the ports are free again, so an immediate `up` works
        ports = [int(v["url"].rsplit(":", 1)[1]) for v in info.values()]
        t = time.time()
        while time.time() - t < 20 and not all(_free(p) for p in ports):
            time.sleep(0.3)
        return 0
    print(f.read_text() if f.exists() else "not running")
    return 0
