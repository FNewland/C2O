"""HK packing saturates out-of-range values instead of sending 0 (2026-11-08).

aocs.att_error (0x0217) was packed H x1000, so any error above 65.5 deg went
down as 0.0: a spacecraft 121 deg off nadir during the COM-004 slew read as
perfectly pointed. It is now x100, and the packer saturates.
"""
import struct
from pathlib import Path

import yaml

from smo_common.telemetry.tm_builder import _INT_RANGE, TMBuilder
from smo_common.protocol.ecss_packet import decommutate_packet


def test_out_of_range_values_saturate():
    b = TMBuilder(apid=1, time_source=lambda: 1000.0)
    params = {1: 121.0, 2: -5.0, 3: 1e12, 4: 12.345}
    pkt = b.build_hk_packet(2, params, [(1, "H", 1000), (2, "H", 1), (3, "h", 1), (4, "H", 100)])
    data = decommutate_packet(pkt).data_field
    assert struct.unpack(">HHHhH", data[:10]) == (2, 65535, 0, 32767, 1234)


def test_att_error_fits_its_full_range():
    hk = yaml.safe_load((Path(__file__).resolve().parents[2]
                         / "configs/eosat1/telemetry/hk_structures.yaml").read_text())
    rows = [p for s in hk["structures"] if True for p in s["parameters"]
            if p["param_id"] == 0x0217]
    assert rows, "0x0217 not downlinked"
    for p in rows:
        lo, hi = _INT_RANGE[p["pack_format"]]
        assert hi / p["scale"] >= 180.0, p


def test_body_rates_cover_the_separation_tumble():
    hk = yaml.safe_load((Path(__file__).resolve().parents[2]
                         / "configs/eosat1/telemetry/hk_structures.yaml").read_text())
    for s in hk["structures"]:
        for p in s["parameters"]:
            if p["param_id"] in (0x0204, 0x0205, 0x0206):
                lo, hi = _INT_RANGE[p["pack_format"]]
                assert hi / p["scale"] >= 14.0 and lo / p["scale"] <= -14.0, p
