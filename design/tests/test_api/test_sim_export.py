"""Design -> simulator configuration export (design-to-ops, Nov 2026).

* the commented YAML writer round-trips every EOSAT-1 file;
* EOSAT-1 round trip: the read-only EOSAT-1 CDR import + EOSAT-1-like design elements ->
  export -> the simulator's strict loaders -> the engine flies a cold boot and a real pass;
  HK rates, the rate ladder, the TM/TC catalogue and the power budget match EOSAT-1's;
* a fresh (non-EOSAT) 3U design from KB parts with its own designed CDR database exports a
  configuration that loads and runs;
* the API: readiness checklist by CDR area, zip download.
"""
from __future__ import annotations

import io
import json
import logging
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[3]
SIM = REPO / "sim"
EOSAT1 = SIM / "configs" / "eosat1"

pytestmark = pytest.mark.skipif(not (EOSAT1 / "mission.yaml").is_file(), reason="simulator reference configuration not present")


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("SPACECDF_AUTO_IRD", "0")
    monkeypatch.setenv("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    monkeypatch.setenv("SMO_AUTO_SNAPSHOT_DIR", str(tmp_path / "snaps"))


# ───────────────────────────────────────────────────────────── helpers

async def _post(c, url, body=None, ok=(200, 201)):
    r = await c.post(url, json=body if body is not None else {})
    assert r.status_code in ok, f"{url}: {r.status_code} {r.text[:400]}"
    return r.json()


async def _el(c, sid, **b):
    return await _post(c, f"/api/elements/?study_id={sid}", b)


async def _tree(c, sid, subsystems) -> dict[str, dict]:
    mission = await _el(c, sid, name="Mission", element_type="mission")
    space = await _el(c, sid, name="Space Segment", element_type="segment", parent_id=mission["id"], segment="space")
    await _el(c, sid, name="Ground Segment", element_type="segment", parent_id=mission["id"], segment="ground")
    sc = await _el(c, sid, name="Spacecraft", element_type="system", parent_id=space["id"])
    out = {}
    for sname, dom, parts in subsystems:
        sub = await _el(c, sid, name=sname, element_type="subsystem", parent_id=sc["id"], subsystem_domain=dom)
        for p in parts:
            name, kb, q, extra = (p + ({},))[:4] if len(p) == 3 else p
            body = {"name": name, "element_type": "component", "parent_id": sub["id"], "subsystem_domain": dom,
                    "quantity": q, **extra}
            if kb:
                body["kb_component_id"] = kb
            out[name] = await _el(c, sid, **body)
    return out


async def _export(study_id: str, tmp_path: Path, name: str):
    from spacecdf_server.services.sim_export import builder, facts, template_dir, validate
    ex = builder.build(await facts.gather(study_id), template_dir())
    out = tmp_path / name
    ex.write(out)
    v = validate.validate_dir(out, template_dir())
    assert v["available"], "simulator packages not importable"
    assert not v["errors"], v["errors"]
    return ex, out


def _y(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


class _Warnings(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.msgs: list[str] = []

    def emit(self, record):
        self.msgs.append(record.getMessage())


def _fly(cfg: Path, monkeypatch, *, max_wait_s: int = 4 * 3600) -> dict:
    """Headless: cold boot in the bootloader, wait for the first real pass (no pass override),
    boot the application in it, fly to LOS. Returns what happened."""
    from smo_common.protocol.ecss_packet import build_tc_packet, decommutate_packet
    from smo_simulator.engine import SimulationEngine
    monkeypatch.setenv("SMO_CONFIG_DIR", str(cfg))
    h = _Warnings()
    logging.getLogger().addHandler(h)
    try:
        eng = SimulationEngine(cfg, speed=1.0)
        res = {"subsystems": sorted(eng.subsystems), "phase0": eng._spacecraft_phase}
        seq = [0]

        def tc(service, subtype, data=b""):
            eng._dispatch_tc(build_tc_packet(apid=100, service=service, subtype=subtype, data=data, seq_count=seq[0]))
            seq[0] += 1

        t = 0
        while not eng._in_contact and t < max_wait_s:
            eng._tick_once(1.0)
            t += 1
            if eng.tm_queue.qsize() > 1500:
                while not eng.tm_queue.empty():
                    eng.tm_queue.get_nowait()
        res["aos_s"] = t if eng._in_contact else None
        while not eng.tm_queue.empty():
            eng.tm_queue.get_nowait()
        tc(17, 1)                      # CONNECTION_TEST (bootloader allow-list)
        for _ in range(5):
            eng._tick_once(1.0)
        tc(8, 1, bytes([55]))          # OBC_BOOT_APP
        hk_sids = set()
        pass_s = 0
        for _ in range(40):
            eng._tick_once(1.0)
            pass_s += 1
        res["phase_after_boot"] = eng._spacecraft_phase
        while eng._in_contact and pass_s < 1200:
            eng._tick_once(1.0)
            pass_s += 1
            while not eng.tm_queue.empty():
                p = decommutate_packet(eng.tm_queue.get_nowait())
                if p and p.secondary and p.secondary.service == 3 and p.secondary.subtype == 25:
                    hk_sids.add(int.from_bytes(p.data_field[:2], "big"))
        res.update({"pass_s": pass_s, "hk_sids": sorted(hk_sids), "engine_fault": eng.engine_fault,
                    "fault_count": eng.engine_fault_count, "bus_v": eng.params.get(0x0105), "soc": eng.params.get(0x0101),
                    "warnings": [m for m in h.msgs if "diverge" in m or "Failed to load model" in m]})
        return res
    finally:
        logging.getLogger().removeHandler(h)


def _power_budget(cfg: Path) -> dict:
    r = subprocess.run([sys.executable, str(SIM / "tools" / "power_budget.py"), "--config", str(cfg), "--profile", "nominal",
                        "--orbits", "3", "--report", "json", "--min-margin-ratio", "0"],
                       capture_output=True, text=True, timeout=600, cwd=str(SIM))
    assert r.stdout.strip(), r.stderr[-2000:]
    d = json.loads(r.stdout)
    worst = next(iter(d["results"].values()))[0]
    return {"gen": worst["gen_avg_w"], "load": worst["load_avg_w"], "ratio": worst["margin_ratio"],
            "passes": d["contact_stats"]["passes_per_day"]}


# ───────────────────────────────────────────────────────────── unit

def test_yaml_writer_round_trips_every_eosat1_file():
    from spacecdf_server.services.sim_export.yaml_emit import dump
    n = 0
    for p in sorted(EOSAT1.rglob("*.yaml")):
        if "/i18n/" in p.as_posix():
            continue
        data = _y(p)
        assert yaml.safe_load(dump(data, {})) == data, p
        n += 1
    assert n > 60
    d = {"a": {"OFF": 1, "x": [1, 2]}, "l": [{"name": "a: b", "v": 1.0e-6}], "id": 0x0105}
    text = dump(d, {("a", "OFF"): "design: here", ("l", 0): "C2O default: there"}, ["head"])
    assert yaml.safe_load(text) == d
    assert "# design: here" in text and "# C2O default: there" in text and "0x0105" in text


# ───────────────────────────────────────────────────────────── EOSAT-1 round trip

EOSAT_LIKE = [
    ("Structure", "structure", [("Structure 6U", "struct-isis-6u", 1)]),
    ("EPS", "power", [
        ("EPS PCDU", "eps-gom-nanopow-p60", 1, {"power_avg_w": 3.0}),
        ("Battery", "bat-gom-nanopow-bp8", 1),
        ("Body solar cells", None, 1, {"performance": {"face_areas_m2": {"px": 0.06, "mx": 0.06, "py": 0.03, "my": 0.03,
                                                                         "pz": 0.018, "mz": 0.0},
                                                      "cell_efficiency_percent": 29.5, "cell_type": "triple_junction_gaas",
                                                      "deployment": "body_mounted"}}),
        ("Solar wing", None, 2, {"performance": {"area_m2": 0.12, "deployment": "deployable"}}),
        ("Solar array drive", None, 1, {"power_avg_w": 0.0}),
    ]),
    ("AOCS", "aocs", [
        ("Reaction wheel", "rw-cubespace-cubewheel-medium", 4, {"power_avg_w": 0.5}),
        ("Star tracker", "st-berlin-space-nst1", 2),
        ("Magnetorquer", "mtq-newspace-nctr-m012", 1),
        ("GNSS receiver", "gps-skyfox-picostar", 1),
    ]),
    ("Communications", "ttc", [("S-band transceiver", "txr-endurosat-sband", 1, {"power_avg_w": 5.0, "power_peak_w": 11.0}),
                               ("S-band patch", "ant-endurosat-sband-patch", 1)]),
    ("On-Board Computer", "obc", [("OBC", "obc-gom-nanomind-a3200", 1, {"power_avg_w": 3.0})]),
    ("Payload", "payload", [("Imager", "pl-imager-2u-eosat", 1, {"power_avg_w": 2.4, "power_peak_w": 5.5})]),
    ("Thermal", "thermal", [("Battery heater", "th-heater-kapton-05", 1, {"power_avg_w": 8.0})]),
]


async def test_eosat1_round_trip_loads_flies_and_matches(client, study_obj, study, tmp_path, monkeypatch):
    req = study_obj.requirements
    req.name = "EOSAT-1"
    req.orbit.altitude_km, req.orbit.inclination_deg, req.orbit.ltan = 513.0, 97.39, "10:00"
    req.design_lifetime_years = 3.0
    await _tree(client, study, EOSAT_LIKE)
    for gs in ("svalbard", "troll", "inuvik"):
        await _post(client, f"/api/studies/{study}/ground-stations", {"kb_station_id": gs})
    imp = await _post(client, f"/api/studies/{study}/cdr/import/eosat1", {})
    assert imp["dataset"] == "reference" and imp["imported"] > 900
    ex, out = await _export(study, tmp_path, "eosat1_roundtrip")
    r = ex.readiness()
    assert r["dataset"] == "reference"

    # TM/TC database, HK rates, link tiers, FDIR tables: the round trip is exact
    for rel, key, ident in (("telemetry/hk_structures.yaml", "structures", lambda s: (s["sid"], s["interval_s"], [p["param_id"] for p in s["parameters"]])),
                            ("telemetry/parameters.yaml", "parameters", lambda p: (p["id"], p["name"])),
                            ("commands/tc_catalog.yaml", "commands", lambda c: (c["name"], c["service"], c["subtype"], c.get("func_id"), c.get("position"))),
                            ("events/event_catalog.yaml", "events", lambda e: (e["id"], e["name"], e.get("severity"))),
                            ("monitoring/s12_definitions.yaml", "s12_definitions", lambda m: (m["param_id"], m.get("low_limit"), m.get("high_limit"))),
                            ("monitoring/s19_rules.yaml", "s19_rules", lambda m: (m.get("ea_id"), m.get("action_func_id")))):
        a = [ident(x) for x in _y(EOSAT1 / rel)[key]]
        b = [ident(x) for x in _y(out / rel)[key]]
        if key == "parameters":          # the CDR export lists parameters by id
            a, b = sorted(a), sorted(b)
        assert a == b, rel
    t_ref, t_out = _y(EOSAT1 / "subsystems/ttc.yaml"), _y(out / "subsystems/ttc.yaml")
    from smo_common.config.schemas import TMRateTier
    tier = lambda t: TMRateTier.model_validate(t).model_dump()  # noqa: E731  (schema defaults filled in)
    assert [tier(t) for t in t_out["tm_rate_tiers"]] == [tier(t) for t in t_ref["tm_rate_tiers"]]
    for k in ("default_tier", "beacon_tier", "safe_tier", "tc_uplink_rate_bps", "cmd_loss_switch_timeout_s"):
        assert t_out[k] == t_ref[k], k
    s_ref, s_out = _y(EOSAT1 / "simulation.yaml"), _y(out / "simulation.yaml")
    assert s_out["eps"]["bus_protection"] == s_ref["eps"]["bus_protection"]
    assert s_out["eps"]["load_shed"]["order"] == s_ref["eps"]["load_shed"]["order"]
    assert s_out["housekeeping"]["default_enabled_sids"] == s_ref["housekeeping"]["default_enabled_sids"]
    a_ref, a_out = _y(EOSAT1 / "subsystems/aocs.yaml"), _y(out / "subsystems/aocs.yaml")
    for mode, ctl in a_ref["control"]["modes"].items():
        for k, v in ctl.items():
            assert a_out["control"]["modes"][mode][k] == pytest.approx(v), (mode, k)
    # hardware from the design: within tolerance of EOSAT-1
    e_ref, e_out = _y(EOSAT1 / "subsystems/eps.yaml"), _y(out / "subsystems/eps.yaml")
    assert e_out["battery"]["capacity_wh"] == pytest.approx(e_ref["battery"]["capacity_wh"])
    assert e_out["battery"]["soc_100_v"] == pytest.approx(e_ref["battery"]["soc_100_v"])
    for k in ("px_area_m2", "py_area_m2", "pz_area_m2", "wing_py_area_m2", "wing_my_area_m2"):
        assert e_out["solar_panels"][k] == pytest.approx(e_ref["solar_panels"][k]), k
    assert e_out["obc_power_w"] == pytest.approx(e_ref["obc_power_w"])
    assert (e_out["payload_power_w"], e_out["payload_standby_power_w"]) == (5.5, 2.4)
    # every value is marked: design or a documented default
    text = (out / "subsystems/eps.yaml").read_text()
    for line in text.splitlines():
        if line and not line.startswith("#") and ":" in line and not line.rstrip().endswith(":") and not line.lstrip().startswith("-"):
            assert "# design:" in line or "# C2O default:" in line or line.startswith(" "), line
    assert "# design: battery Battery (KB capacity_wh)" in text

    # power budget (sim tool, EOL worst beta, nominal ops): within tolerance of EOSAT-1's
    pb_ref, pb_out = _power_budget(EOSAT1), _power_budget(out)
    assert pb_out["gen"] == pytest.approx(pb_ref["gen"], rel=0.10), (pb_ref, pb_out)
    assert pb_out["load"] == pytest.approx(pb_ref["load"], rel=0.20), (pb_ref, pb_out)
    assert pb_out["ratio"] > 1.10

    # the engine flies it: cold boot in the bootloader, a real pass, OBC boot in the pass
    fl = _fly(out, monkeypatch)
    assert fl["subsystems"] == ["aocs", "eps", "obdh", "payload", "prop", "tcs", "ttc"]
    assert fl["phase0"] == 3 and fl["aos_s"] is not None, fl
    assert fl["phase_after_boot"] == 4, fl
    assert fl["engine_fault"] is None and fl["fault_count"] == 0, fl
    assert fl["warnings"] == [], fl["warnings"]
    assert 1 in fl["hk_sids"], fl


# ───────────────────────────────────────────────────────────── a fresh design

FRESH_3U = [
    ("Structure", "structure", [("Structure 3U", "struct-isis-3u", 1)]),
    ("Power", "power", [("EPS board", "eps-gom-nanopow-p31us", 1), ("Battery pack", "bat-gom-nanopow-bp4", 1),
                        ("Deployable panels", "sp-dhv-csa-3u-deploy", 2), ("Body panels", "sp-isis-1u-panel", 4)]),
    ("ADCS", "aocs", [("Wheel", "rw-cubew-small", 3), ("Star camera", "st-hyperion-sagitta", 1),
                      ("Torquer board", "mtq-isis-imtq", 1), ("GPS", "gps-ublox-max-m10s", 1)]),
    ("Comms", "ttc", [("S-band radio", "txr-gom-link-s", 1), ("Patch antenna", "ant-anywaves-sband", 1)]),
    ("Avionics", "obc", [("Flight computer", "obc-isis-iobc", 1)]),
    ("Instrument", "payload", [("Multispectral camera", "pl-imager-1u-ms", 1)]),
    ("Thermal", "thermal", [("Battery heater", "th-heater-kapton-01", 1)]),
]


async def test_fresh_design_exports_a_loadable_config_that_runs(client, study_obj, study, tmp_path, monkeypatch):
    req = study_obj.requirements
    req.name = "AURORA-3U"
    req.orbit.altitude_km, req.orbit.inclination_deg, req.orbit.ltan = 550.0, 97.6, "13:30"
    req.launch_date_target = "2027-03-15"
    await _tree(client, study, FRESH_3U)
    for gs in ("fairbanks", "troll"):
        await _post(client, f"/api/studies/{study}/ground-stations", {"kb_station_id": gs})
    await _post(client, f"/api/studies/{study}/interfaces/propose", {})
    for i in (await client.get(f"/api/studies/{study}/interfaces?status=suggested")).json():
        await client.patch(f"/api/interfaces/{i['id']}", json={"status": "accepted"})
    await _post(client, f"/api/studies/{study}/electrical/propose", {})
    elec = (await client.get(f"/api/studies/{study}/electrical")).json()
    for kind in ("rails", "lines", "buses", "nodes"):
        for row in elec.get(kind) or []:
            if row.get("status") == "suggested":
                await client.patch(f"/api/studies/{study}/electrical/{kind}/{row['id']}", json={"status": "accepted"})
    await _post(client, f"/api/studies/{study}/modes/template", {})
    await _post(client, f"/api/studies/{study}/modes/propose", {})
    await _post(client, f"/api/studies/{study}/modes/members/accept-all", {})
    r = await client.post(f"/api/studies/{study}/stack/auto-place", json={})
    if r.status_code == 200:
        await client.post(f"/api/studies/{study}/stack/approve", json={})
    await _post(client, f"/api/studies/{study}/design-rules/run?thermal=false", {})
    await _post(client, f"/api/studies/{study}/cdr/propose", {})
    await _post(client, f"/api/studies/{study}/cdr/accept-all", {})

    ex, out = await _export(study, tmp_path, "fresh_3u")
    if os.environ.get("C2O_KEEP_EXPORT"):
        import shutil
        shutil.copytree(out, os.environ["C2O_KEEP_EXPORT"], dirs_exist_ok=True)
    r = ex.readiness()
    assert r["dataset"] == "design"
    by = {a["id"]: a for a in r["areas"]}
    for area in ("mission", "eps", "aocs", "ttc", "tmtc", "fdir"):
        assert by[area]["design"] > 0, area
    m = _y(out / "mission.yaml")
    assert m["name"] == "AURORA-3U"
    o = _y(out / "orbit.yaml")
    assert o["t0_epoch"] == "2027-03-15T12:00:00Z" and o["altitude_km"] == 550.0
    assert [g["name"] for g in o["ground_stations"]] and "Iqaluit" not in [g["name"] for g in o["ground_stations"]]
    e = _y(out / "subsystems/eps.yaml")
    assert e["battery"]["soc_100_v"] < 20.0, "a 4S pack, not the EOSAT-1 8S bus"
    assert any(i["item"] == "reaction wheel count" and i["status"] == "unsupported" for i in by["aocs"]["items"])
    assert (out / "ops" / "flight_rules.yaml").is_file() and (out / "design_db").is_dir()
    assert "# design:" in (out / "subsystems/eps.yaml").read_text()

    fl = _fly(out, monkeypatch, max_wait_s=6 * 3600)
    assert fl["subsystems"] == ["aocs", "eps", "obdh", "payload", "prop", "tcs", "ttc"]
    assert fl["aos_s"] is not None and fl["phase_after_boot"] == 4, fl
    assert fl["engine_fault"] is None and fl["fault_count"] == 0, fl
    assert fl["warnings"] == [], fl["warnings"]


# ───────────────────────────────────────────────────────────── API

async def test_readiness_and_zip_routes(client, study_obj, study):
    await _tree(client, study, EOSAT_LIKE[:3])
    r = await client.get(f"/api/studies/{study}/export/sim-config")
    assert r.status_code == 200, r.text
    rep = r.json()
    assert [a["id"] for a in rep["areas"]][:3] == ["mission", "eps", "aocs"]
    assert rep["validation"]["available"] and rep["validation"]["errors"] == []
    tmtc = next(a for a in rep["areas"] if a["id"] == "tmtc")
    assert tmtc["missing"] >= 1, "no CDR database: the checklist says so"
    z = await client.get(f"/api/studies/{study}/export/sim-config.zip")
    assert z.status_code == 200 and z.headers["x-c2o-validation"] == "ok"
    names = zipfile.ZipFile(io.BytesIO(z.content)).namelist()
    root = names[0].split("/")[0]
    for rel in ("mission.yaml", "orbit.yaml", "simulation.yaml", "subsystems/eps.yaml", "telemetry/parameters.yaml",
                "commands/tc_catalog.yaml", "mcs/positions.yaml", "geometry.yaml", "README.md", "export_report.json"):
        assert f"{root}/{rel}" in names, rel
    assert not any(n.startswith((f"{root}/procedures/", f"{root}/manual/", f"{root}/i18n/")) for n in names)
    old = await client.post(f"/api/exports/smo/{study}")
    assert old.status_code == 200 and old.json()["is_valid"] and "subsystems/eps.yaml" in old.json()["files"]
    em = await client.get("/api/cdr/export-map")
    keys = {m["key"] for m in em.json()["map"]}
    assert any("hk_apids" in k for k in keys) and any("control.modes" in k for k in keys)
