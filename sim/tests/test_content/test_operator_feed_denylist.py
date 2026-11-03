"""No simulator truth or instructor knowledge in a student/operator feed.

SCREEN_REVIEW.md §12 ("leak surfaces outside the pages"): removing a caption
is not enough, the field has to leave the feed. This test drives each
student- or operator-facing feed with a simulator that HAS the truth to leak
(sc_mode, the HK enable map, the fault-cascade block, the pass override, the
channel model…) and asserts none of it comes out:

* the MCS state broadcast (``/api/state`` and the WebSocket carry the same
  ``_latest_state``) and ``/api/fdir``;
* the MCS and planner config browsers (read-only mounts);
* the radio ``/api/status`` / WS as a student sees it behind IAP;
* the documentation viewer's index;
* the welcome page status feed as a student sees it.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

SIM = Path(__file__).resolve().parents[2]
CONFIG_DIR = SIM / "configs" / "eosat1"
for pkg in ("smo-common", "smo-mcs", "smo-planner", "smo-rfsim"):
    src = SIM / "packages" / pkg / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

#: Keys that only the simulator or the instructor knows.
DENY_KEYS = {
    "sim_health", "hk_enabled", "autonomy", "active_faults", "pending_cascades",
    "pass_override", "fading_enabled", "fading_k_db", "gs_penalty_db",
    "n_interferers", "phase_noise_enabled", "sc_tx_on", "sc_pa_on",
    "tx_packet_drops", "tx_frames_transmitted", "tx_buffer_overflows",
}
#: Values that name the simulator as the source of a displayed datum.
DENY_VALUES = {"sim_state", "derived_from_sc_mode"}


def _instructor_params() -> tuple[set[str], set[str]]:
    data = yaml.safe_load((CONFIG_DIR / "telemetry/parameters.yaml").read_text())
    rows = [p for p in data["parameters"] if p.get("visibility") == "instructor"]
    return ({f"0x{int(p['id']):04X}" for p in rows}, {p["name"] for p in rows})


INSTR_IDS, INSTR_NAMES = _instructor_params()


def _walk(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path, k, v
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def assert_clean(feed, name, *, top_level_deny=()):
    assert INSTR_IDS and INSTR_NAMES
    bad = []
    if isinstance(feed, dict):
        bad += [f"{name}.{k}" for k in top_level_deny if k in feed]
    for path, k, v in _walk(feed):
        if k in DENY_KEYS or k in INSTR_IDS or k in INSTR_NAMES:
            bad.append(f"{path}.{k}")
        if isinstance(v, str) and (v in DENY_VALUES or v in INSTR_NAMES):
            bad.append(f"{path}.{k}={v}")
    assert not bad, f"{name} leaks simulator/instructor truth: {bad[:10]}"


# ── MCS ────────────────────────────────────────────────────────────────

SIM_PAYLOAD = {
    "sim_time": "2026-08-20T12:00:00Z", "speed": 1.0,
    "sc_mode": 0, "engine_fault": None, "tm_rate_bps": 1000,
    "hk_enabled": {"1": True, "2": False, "4": True},
    "fdir": {"active_faults": [{"name": "gyro_bias"}],
             "pending_cascades": [{"name": "x"}], "procedures": []},
    "ttc": {"tm_tier": 1, "tm_tier_name": "LOW", "station": {"signal": False}},
}


def _mcs():
    from smo_mcs.server import MCSServer
    from smo_common.config.schemas import MCSDisplayConfig
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}):
        return MCSServer(config_dir=str(CONFIG_DIR), connect_host="localhost",
                         connect_port=9999, http_port=0)


async def test_mcs_state_and_fdir_feeds_carry_no_truth():
    srv = _mcs()
    # Everything the sim-state poll would ingest, simulator truth included.
    srv._ingest_hk_enable_reset(None)
    srv._ingest_sim_health(SIM_PAYLOAD)
    srv._station_link.ingest_sim_state(SIM_PAYLOAD)
    srv._running = True
    task = asyncio.create_task(srv._state_poll_loop())
    await asyncio.sleep(1.3)
    srv._running = False
    await asyncio.wait_for(task, 3.0)
    state = srv._latest_state
    assert state, "the state loop produced nothing"
    assert_clean(state, "MCS /api/state", top_level_deny=("sc_mode",))
    fdir = json.loads((await srv._handle_fdir_display(None)).body)
    assert_clean(fdir, "MCS /api/fdir")
    assert fdir["state"]["sc_mode"] is None          # not downlinked: unknown
    hk = json.loads((await srv._handle_hk_structures(None)).body)
    assert_clean(hk, "MCS /api/hk-structures")
    cat = json.loads((await srv._handle_param_catalog(None)).body)
    assert_clean(cat, "MCS /api/param-catalog")


def test_mcs_and_planner_mount_the_config_browser_read_only():
    for rel in ("packages/smo-mcs/src/smo_mcs/server.py",
                "packages/smo-planner/src/smo_planner/server.py"):
        src = (SIM / rel).read_text(encoding="utf-8")
        i = src.index("register_config_routes(")
        call = src[i:src.index(")", i)]
        assert "readonly=True" in call and "student_facing" not in call, rel


async def test_read_only_config_browser_serves_no_instructor_file(tmp_path):
    from smo_common.confedit import register_config_routes
    from smo_common.confedit.editor import ConfigEditor
    app = web.Application()
    register_config_routes(app, ConfigEditor(CONFIG_DIR, history_dir=tmp_path / "h"),
                           readonly=True, owner="planner")
    async with TestClient(TestServer(app)) as c:
        files = (await (await c.get("/api/config/files")).json())["files"]
        paths = [f["path"] for f in files]
        assert not [p for p in paths if p.startswith(("scenarios/", "i18n/"))
                    or p in ("rfsim.yaml", "fdir/fault_propagation.yaml")]
        for p in paths:
            if not p.endswith((".yaml", ".yml")):
                continue
            text = (await (await c.get("/api/config/file",
                                       params={"path": p})).json())["text"]
            leaked = [n for n in INSTR_NAMES if n in text]
            assert not leaked, f"{p} names instructor parameters {leaked[:5]}"


# ── radio ──────────────────────────────────────────────────────────────

async def test_radio_student_feed(monkeypatch):
    from smo_rfsim.radio.frontend import RadioFrontend
    from smo_rfsim.radio.web_ui import build_app
    monkeypatch.setenv("SMO_REQUIRE_IAP", "1")
    monkeypatch.setenv("SMO_INSTRUCTORS", "prof@c2o.live")
    fe = RadioFrontend()
    fe.status.pass_override = True
    fe.status.gs_penalty_db = 6.0
    fe.status.diagnostics = {"tx_packet_drops": 1, "rx_good_frames": 3}
    hdr = {"X-Goog-Authenticated-User-Email": "accounts.google.com:s@c2o.live"}
    async with TestClient(TestServer(build_app(fe))) as c:
        d = await (await c.get("/api/status", headers=hdr)).json()
    assert_clean(d, "radio /api/status")
    assert "range_km" not in d and "config" not in d


# ── docs viewer and portal ─────────────────────────────────────────────

def _tool(name):
    spec = importlib.util.spec_from_file_location(f"_deny_{name}", SIM / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_docs_index_lists_no_training_system_document():
    dv = _tool("doc_viewer")
    cats = dv.discover_docs(CONFIG_DIR)
    listed = [e["path"] for es in cats.values() for e in es]
    assert listed and "manual/01_eps.md" in listed
    for p in ("manual/software_architecture.md", "manual/installation_guide.md",
              "manual/installation_guide_rfsim.md", "manual/11_rf_simulation.md",
              "manual/commissioning_walkthrough_changelog.md",
              "mcs/role_analysis/aocs_role.md",
              "procedures/contingency/boot_loader_recovery.md"):
        assert p not in listed, p
    assert dv.resolve_doc(CONFIG_DIR, "manual/software_architecture.md", "en")[0] is None
    assert "mcs" not in cats


async def test_portal_student_status_feed(monkeypatch):
    pt = _tool("portal")
    monkeypatch.setenv("SMO_INSTRUCTORS", "prof@c2o.live")
    snap = {"checked_at": "2026-11-03T17:18:33Z", "link": {"state": "UP"},
            "mode": None, "pass": None,
            "services": {s.key: {"state": "up", "port": s.ports[0]} for s in pt.SERVICES}}
    out = pt.status_for(snap, instructor=False, local=False)
    assert set(out["services"]) == {s.key for s in pt.SERVICES if not s.instructors_only}
    assert "checked_at" not in out
    assert all("port" not in v for v in out["services"].values())
    assert_clean(out, "portal /api/status")


# ── text that operators read ───────────────────────────────────────────

@pytest.mark.parametrize("root", ["procedures", "i18n/fr/procedures"])
def test_procedure_cards_do_not_name_fault_injection(root):
    """SCREEN_REVIEW #6: operator procedures describe the spacecraft, not
    the instructor's injections."""
    import re
    # "orbit injection" is spacecraft vocabulary; a fault injection is not.
    pat = re.compile(r"\binjected\b|injecté|injection de panne|failure injection|"
                     r"fault injection|instructor|instructeur|pass override|"
                     r"forçage (du |de )?passage")
    bad = []
    for f in sorted((CONFIG_DIR / root).rglob("*.md")):
        for m in pat.finditer(f.read_text(encoding="utf-8").lower()):
            bad.append(f"{f.relative_to(CONFIG_DIR)}: {m.group(0)}")
    assert not bad, bad


def test_operator_parameter_descriptions_do_not_name_injection():
    data = yaml.safe_load((CONFIG_DIR / "telemetry/parameters.yaml").read_text())
    bad = [p["name"] for p in data["parameters"]
           if p.get("visibility") != "instructor"
           and any(w in str(p.get("description", "")).lower()
                   for w in ("inject", "instructor"))]
    assert not bad, bad
