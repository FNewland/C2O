"""Unit tests of the data budget pieces (W3, agent H): packet overhead, framing, intervals per mode,
the multi-queue pass allocation and the J2 contact union (fast; the fixture test covers the study)."""
from __future__ import annotations

import pytest

from spacecdf_server.services import data_budget as dbs
from spacecdf_server.services.ground_scheduler import (GroundStation, OrbitParams, PassSlot, allocate_passes,
                                                       contact_statistics, parse_ltan_h)


def test_packet_overhead_from_settings_layout():
    assert dbs.packet_overhead_bytes({}) == 23                       # full PUS-C, CUC 4+2, uint16 SID, CRC
    assert dbs.packet_overhead_bytes({"has_msg_counter": False, "has_destination_id": False}) == 19
    assert dbs.packet_overhead_bytes({"packet_overhead_bytes": 20}) == 20


def test_framing_defaults_are_ccsds_with_sdls():
    fr = dbs.framing([], 38400.0)
    assert fr["frame_bytes"] == 446 and fr["channel_bytes_per_frame"] == 514 and fr["data_field_bytes"] == 422
    assert fr["frame_efficiency"] == pytest.approx(0.821, abs=1e-3) and fr["information_rate_bps"] == pytest.approx(31527, abs=1)


def test_intervals_per_mode_and_disabled_cells():
    m_nom = {"id": "m1", "kind": "nominal", "name": "Nominal"}
    m_img = {"id": "m2", "kind": "imaging", "name": "Imaging"}
    sid = {"designed": True, "period_s": 1.0, "rt_period_by_mode": {"m1": 1, "imaging": None}, "store_sid": 101,
           "store_period_by_mode": {"nominal": 30, "m2": 10}}
    assert dbs.rt_period(sid, m_nom) == 1 and dbs.rt_period(sid, m_img) is None
    assert dbs.store_period(sid, m_nom) == 30 and dbs.store_period(sid, m_img) == 10
    assert dbs.enabled_of({"enabled_at_boot": False}) == {"realtime": False, "stored": False}
    assert dbs.enabled_of({"store_sid": 101}) == {"realtime": True, "stored": True}
    assert dbs.in_operational_mix({"kind": "custom", "phase": "nominal", "orbit_fraction": 0.01})
    assert not dbs.in_operational_mix({"kind": "custom", "phase": "disposal", "orbit_fraction": 1.0})


def test_pass_allocation_serves_vc0_then_the_selected_channel():
    slots = [PassSlot(start_s=3600, usable_s=600, rt_bps=4800, order=("VC1", "VC2")),
             PassSlot(start_s=7200, usable_s=600, rt_bps=562, order=("VC2", "VC1"))]
    res = allocate_passes(slots, 31527.0, {"VC1": 100.0, "VC2": 10000.0})
    a, b = res["slots"]
    assert a["sent_bits"]["VC0"] == pytest.approx(4800 * 600)
    assert a["sent_bits"]["VC1"] == pytest.approx(100.0 * 3600)          # the HK queue emptied first
    assert b["sent_bits"]["VC2"] > a["sent_bits"]["VC2"]                  # payload first on the dump pass
    assert res["levels_bits"]["VC1"] >= 0 and res["levels_bits"]["VC2"] >= 0


def test_union_of_passes_is_less_than_the_sum():
    sts = [GroundStation(id=n, name=n, latitude_deg=la, longitude_deg=lo, elevation_m=0, antenna_diameter_m=3, min_elevation_deg=10)
           for n, la, lo in (("A", 62.45, -114.37), ("B", 68.36, -133.72))]
    st = contact_statistics(OrbitParams(altitude_km=590, inclination_deg=97.75), sts, days=5, step_s=10, ltan_h=parse_ltan_h("22:30"))
    assert st.union["min_per_day"] < st.union["sum_of_stations_min_per_day"]
    assert st.union["min_per_day"] > max(v["min_per_day"] for v in st.stations.values())
    assert all(w.end_s > w.start_s for w in st.windows) and st.union["longest_gap_h"] > 0
