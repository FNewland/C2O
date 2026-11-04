"""mission.yaml ``hk_apids`` (2026-11): a per-subsystem APID plan for HK.

Default (empty) keeps every application packet on ``spacecraft_apid``; a map
sends a SID's S3.25 from its own APID with its own sequence counter, in the
application image only (the bootloader keeps its APID)."""
import shutil
import struct
from pathlib import Path

import pytest
import yaml

from smo_common.protocol.ecss_packet import build_tc_packet, decommutate_packet
from smo_common.telemetry.tm_builder import TMBuilder

CFG = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


def test_builder_keeps_one_sequence_counter_per_apid():
    b = TMBuilder(apid=1, time_source=lambda: 0.0)
    hk = [(0x0100, "H", 100)]
    p1 = decommutate_packet(b.build_hk_packet(1, {}, hk))
    p2 = decommutate_packet(b.build_hk_packet(1, {}, hk, apid=0x120))
    p3 = decommutate_packet(b.build_hk_packet(1, {}, hk, apid=0x120))
    p4 = decommutate_packet(b.build_hk_packet(1, {}, hk))
    assert (p1.primary.apid, p2.primary.apid, p3.primary.apid, p4.primary.apid) == (1, 0x120, 0x120, 1)
    assert p2.primary.sequence_count == 1 and p3.primary.sequence_count == 2
    assert p4.primary.sequence_count == p1.primary.sequence_count + 1
    assert b.apid == 1


def test_default_plan_is_empty():
    m = yaml.safe_load((CFG / "mission.yaml").read_text())
    assert not m.get("hk_apids")


@pytest.mark.slow
def test_engine_sends_mapped_sids_from_their_apid(tmp_path, monkeypatch):
    from smo_simulator.engine import SimulationEngine
    cfg = tmp_path / "cfg"
    shutil.copytree(CFG, cfg, ignore=shutil.ignore_patterns("i18n", "manual", "procedures", "worksheets", "xtce", "smdl"))
    m = yaml.safe_load((cfg / "mission.yaml").read_text())
    m["hk_apids"] = {1: 0x101, 3: 0x103}
    (cfg / "mission.yaml").write_text(yaml.safe_dump(m, sort_keys=False))
    monkeypatch.setenv("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    eng = SimulationEngine(cfg, speed=1.0)
    eng._override_passes = True
    eng.params[0x05FF] = 1
    eng._dispatch_tc(build_tc_packet(apid=100, service=17, subtype=1, data=b"", seq_count=0))
    eng._dispatch_tc(build_tc_packet(apid=100, service=8, subtype=1, data=bytes([55]), seq_count=1))
    for _ in range(25):
        eng._tick_once(1.0)
    while not eng.tm_queue.empty():
        eng.tm_queue.get_nowait()
    eng._dispatch_tc(build_tc_packet(apid=100, service=3, subtype=5, data=struct.pack(">H", 3), seq_count=2))
    for _ in range(70):
        eng._tick_once(1.0)
    by_sid: dict[int, set[int]] = {}
    while not eng.tm_queue.empty():
        p = decommutate_packet(eng.tm_queue.get_nowait())
        if p and p.secondary and p.secondary.service == 3 and p.secondary.subtype == 25:
            sid = struct.unpack(">H", p.data_field[:2])[0]
            by_sid.setdefault(sid, set()).add(p.primary.apid)
    assert by_sid.get(1) == {0x101}
    assert by_sid.get(3) == {0x103}
