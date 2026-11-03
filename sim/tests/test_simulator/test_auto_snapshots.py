"""Auto snapshots before injected faults, on disk as well as in memory
(INSTRUCTOR_CONSOLE_DESIGN.md §13 item 6, ruled 2026-11-03; auto_snapshots.py).

Policy: newest 10 per run in workspace/snapshots/auto (configurable), named
with sim time + fault, deleted when a new scenario run starts or after 48 h,
manual snapshots untouched, size checked and bounded, restorable after a
simulator restart.
"""
import gzip
import json
import os
import time
from pathlib import Path

import pytest

from smo_simulator.auto_snapshots import AutoSnapshotStore
from smo_simulator.engine import SimulationEngine

REPO = Path(__file__).resolve().parents[2]
CFG = REPO / "configs" / "eosat1"


@pytest.fixture
def env(tmp_path, monkeypatch):
    auto = tmp_path / "auto"
    monkeypatch.setenv("SMO_AUTO_SNAPSHOT_DIR", str(auto))
    monkeypatch.setenv("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    monkeypatch.setattr(SimulationEngine, "_BREAKPOINT_DIR", tmp_path / "bp")
    e = SimulationEngine(CFG)
    for _ in range(3):
        e._tick_once(1.0)
    return e, auto


def _files(d):
    return sorted(p.name for p in Path(d).glob("auto_*.json.gz"))


def test_snapshot_goes_to_disk_named_by_sim_time_and_fault(env):
    e, auto = env
    name, _ = e._auto_snapshots.take("eps/solar_array_partial")
    e._auto_snapshots.wait()
    files = _files(auto)
    assert len(files) == 1
    stamp = e._sim_time.strftime("%Y%m%dT%H%M%SZ")
    assert files[0].endswith(f"__{stamp}__eps.solar_array_partial.json.gz"), files[0]
    assert files[0].startswith("auto_free-")                  # the free run
    with gzip.open(auto / files[0]) as f:
        state = json.loads(f.read())
    assert state["auto"] and state["auto_fault"] == "eps/solar_array_partial"
    row = e._auto_snapshots.list()[0]
    assert row["name"] == name and row["on_disk"] and 0 < row["bytes"] < 25e6


def test_instructor_inject_snapshots_first_and_restore_works_after_a_restart(env, tmp_path):
    e, auto = env
    ok, why = e.submit_instructor_cmd_sync({
        "type": "failure_schedule", "trigger": {"kind": "now"}, "snapshot_before": True,
        "injects": [{"subsystem": "tcs", "failure": "sensor_drift", "magnitude": 6.0, "zone": "obc"}]})
    assert ok, why
    e._auto_snapshots.wait()
    assert len(_files(auto)) == 1
    tick_at_snap = e._tick_count
    for _ in range(5):
        e._tick_once(1.0)

    # "restart": a new simulator on the same workspace
    e2 = SimulationEngine(CFG)
    rows = e2._auto_snapshots.list()
    assert len(rows) == 1 and rows[0]["previous_process"] and rows[0]["fault"] == "tcs/sensor_drift"
    out = {}
    e2._handle_instructor_cmd({"type": "load_breakpoint", "name": rows[0]["name"], "_outcome": out})
    assert out.get("ok"), out
    assert e2._tick_count == tick_at_snap
    assert not e2._failure_manager.active_failures(), "restored to BEFORE the fault"


def test_newest_ten_per_run(env):
    e, auto = env
    store = e._auto_snapshots
    for i in range(13):
        e._tick_once(1.0)
        store.take(f"aocs/rw_seizure{i}")
        store.wait()
    assert len(_files(auto)) == 10
    assert len(store.list()) == 10
    kept = " ".join(_files(auto))
    assert "rw_seizure0." not in kept and "rw_seizure12." in kept


def test_new_scenario_run_deletes_old_autos_but_not_manual_snapshots(env, tmp_path):
    e, auto = env
    e._handle_instructor_cmd({"type": "save_breakpoint", "name": "manual one"})
    e._auto_snapshots.take("eps/overcurrent")
    e._auto_snapshots.wait()
    (auto / "notes.txt").write_text("not ours")
    name = next(d.name for d in e._scenario_engine._scenarios.values() if d.file_id == "rw_bearing")
    e._handle_instructor_cmd({"type": "start_scenario", "name": name})
    assert _files(auto) == []
    assert e._auto_snapshots.list() == []
    assert (auto / "notes.txt").exists()
    assert "manual one" in e._breakpoints and (tmp_path / "bp" / "manual_one.json").exists()
    assert e._auto_snapshots.run_id.startswith("scn-rw_bearing-")
    # the scenario's own inject is snapshotted under the new run
    for _ in range(185):
        e._tick_once(1.0)
    e._auto_snapshots.wait()
    files = _files(auto)
    assert len(files) == 1 and files[0].startswith("auto_scn-rw_bearing-")
    assert files[0].endswith("__aocs.rw_bearing.json.gz")


def test_older_than_48_hours_is_deleted(env):
    e, auto = env
    e._auto_snapshots.take("ttc/high_ber")
    e._auto_snapshots.wait()
    old = auto / _files(auto)[0]
    t = time.time() - 49 * 3600
    os.utime(old, (t, t))
    store = AutoSnapshotStore(e, {"dir": str(auto)})
    assert _files(auto) == [] and store.list() == []


def test_oversized_snapshot_stays_in_memory_only(env, tmp_path):
    e, _auto = env
    store = AutoSnapshotStore(e, {"max_snapshot_mb": 0.001}, directory=tmp_path / "small")
    name, _ = store.take("obdh/obc_crash")
    store.wait()
    assert _files(tmp_path / "small") == []
    row = store.list()[0]
    assert not row["on_disk"] and "memory only" in row["note"]
    assert store.get(name) is not None                     # still restorable in this run


def test_folder_total_is_bounded(env, tmp_path):
    e, _auto = env
    d = tmp_path / "bounded"
    store = AutoSnapshotStore(e, {"max_total_mb": 0.15}, directory=d)
    for i in range(6):
        store.take(f"eps/f{i}")
        store.wait()
    total = sum(p.stat().st_size for p in d.glob("auto_*.json.gz"))
    assert total <= 0.15e6 and len(_files(d)) >= 1


@pytest.mark.asyncio
async def test_breakpoint_api_lists_autos_with_restore_metadata(env):
    from aiohttp.test_utils import TestClient, TestServer
    from smo_simulator.instructor.app import create_instructor_app
    e, _auto = env
    e._auto_snapshots.take("payload/cooler_failure")
    e._auto_snapshots.wait()
    client = TestClient(TestServer(create_instructor_app(e, ui_mode="modern")))
    await client.start_server()
    try:
        rows = await (await client.get("/api/breakpoints")).json()
        autos = [r for r in rows if r["auto"]]
        assert len(autos) == 1
        a = autos[0]
        assert a["fault"] == "payload/cooler_failure" and a["on_disk"] and a["bytes"] > 0
        r = await client.post("/api/breakpoint/load", json={"name": a["name"]})
        assert (await r.json())["status"] == "loaded"
    finally:
        await client.close()
