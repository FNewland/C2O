"""Ground limits with a validity condition (`valid_when`, 2026-11-03).

The FPA/imager limits in mcs/limits.yaml apply only while 0x0426
`tcs.fpa_limits_valid` = 1 (payload powered or FPA cooler running), the
ground twin of the S12 validity condition on board.
"""
from pathlib import Path

from smo_common.config.loader import load_limits
from smo_common.config.schemas import LimitDef
from smo_mcs.tm_processor import TMProcessor

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


def _proc():
    lim = LimitDef.model_validate({
        "param_id": 0x0408, "yellow_low": -22.0, "yellow_high": 14.0,
        "red_low": -25.5, "red_high": 17.5,
        "valid_when": {"param_id": 0x0426, "mask": 1, "value": 1}})
    return TMProcessor({}, [lim])


def test_unchecked_until_the_validity_parameter_is_known():
    tp = _proc()
    tp._check_limit(0x0408, -27.0)
    assert tp.limit_statuses()[0x0408] == "unchecked"
    assert tp.pop_alarms() == []


def test_cold_unpowered_imager_is_unchecked_and_powered_one_alarms():
    tp = _proc()
    tp._params[0x0426] = 0
    tp._check_limit(0x0408, -27.0)
    assert tp.limit_statuses()[0x0408] == "unchecked"
    assert tp.pop_alarms() == []
    tp._params[0x0426] = 1
    tp._check_limit(0x0408, -27.0)
    assert tp.limit_statuses()[0x0408] == "red_low"
    (a,) = tp.pop_alarms()
    assert a["status"] == "red_low" and not a["cleared"]


def test_an_active_alarm_returns_to_normal_when_the_limit_stops_applying():
    tp = _proc()
    tp._params[0x0426] = 1
    tp._check_limit(0x0408, -27.0)
    tp.pop_alarms()
    tp._params[0x0426] = 0                      # payload switched off
    tp._check_limit(0x0408, -27.0)
    (a,) = tp.pop_alarms()
    assert a["status"] == "unchecked" and a["cleared"] and a["previous"] == "red_low"
    tp._check_limit(0x0408, -27.5)
    assert tp.pop_alarms() == []                # steady, journalled once


def test_band_exposes_the_condition():
    band = _proc().limit_band(0x0408)
    assert band["valid_when"] == {"param_id": "0x0426", "mask": 1, "value": 1}


def test_shipped_limits_parse_with_valid_when():
    by = {l.param_id: l for l in load_limits(CONFIG_DIR)}
    for pid in (0x0408, 0x0601, 0x0617):
        assert by[pid].valid_when is not None
        assert by[pid].valid_when.param_id == 0x0426
