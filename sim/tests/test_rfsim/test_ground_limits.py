"""Ground-receiver limits on BER and AGC (plan decision 2026-11-01).

BER (0x050C) and AGC (0x051A) are measured by the GROUND receiver
(``visibility: ground_derived``), so their limits moved out of
``mcs/limits.yaml`` (the spacecraft-telemetry set, where no sample ever
arrived) into the RF bridge. These tests pin the conventions (same as the
MCS: red before yellow, strict, transitions only), the no-signal
suppression, the radio page wiring and the additive API.
"""
from pathlib import Path

import pytest
import yaml
from aiohttp.test_utils import TestClient, TestServer

from smo_rfsim.config import GroundLimitsConfig, RFSimConfig
from smo_rfsim.ground_limits import NO_SIGNAL, GroundLimitChecker, build_limits
from smo_rfsim.radio.frontend import LockState, RadioFrontend
from smo_rfsim.radio.web_ui import build_app

REPO = Path(__file__).resolve().parents[2]
CFG = REPO / "configs" / "eosat1"
MODERN = REPO / "packages/smo-rfsim/src/smo_rfsim/static/modern/index.html"
FR = REPO / "packages/smo-rfsim/src/smo_rfsim/static/modern/i18n/fr.json"


def _locked(fe, mode="RF"):
    fe.status.mode = mode
    fe.update_lock(LockState.LOCKED, LockState.LOCKED, LockState.LOCKED)


def test_shipped_config_loads_the_ground_limits():
    cfg = RFSimConfig.from_yaml(CFG / "rfsim.yaml")
    gl = cfg.ground_limits
    assert (gl.ber_yellow_high, gl.ber_red_high) == (-5.0, -4.0)
    assert gl.agc_red_low < gl.agc_yellow_low < gl.agc_yellow_high < gl.agc_red_high


def test_bands_left_the_spacecraft_limit_set():
    limits = yaml.safe_load((CFG / "mcs" / "limits.yaml").read_text())["limits"]
    pids = {int(l["param_id"]) for l in limits}
    assert not pids & {0x050C, 0x051A, 0x0616}


def test_both_limited_parameters_are_ground_derived():
    params = {int(p["id"]): p for p in yaml.safe_load(
        (CFG / "telemetry" / "parameters.yaml").read_text())["parameters"]}
    for lim in build_limits(GroundLimitsConfig()):
        assert params[lim.param_id]["name"] == lim.name
        assert params[lim.param_id].get("visibility") == "ground_derived"


@pytest.mark.parametrize("value,state", [
    (-8.0, "nominal"), (-5.0, "nominal"), (-4.6, "yellow_high"),
    (-4.0, "yellow_high"), (-3.2, "red_high")])
def test_ber_classification_matches_mcs_conventions(value, state):
    ber = build_limits(GroundLimitsConfig())[0]
    assert ber.classify(value) == state


def test_good_link_is_nominal_and_fade_alarms():
    fe = RadioFrontend()
    _locked(fe)
    fe.update_rf(12.0, rssi_dbm=-115.0)           # BER ~1e-8, AGC -55
    fe.check_ground_limits(now=1.0)
    assert fe.status.ground_limit_summary == "nominal"
    assert fe.status.agc_db == pytest.approx(-55.0)
    fe.update_rf(7.5, rssi_dbm=-131.0)            # BER ~6e-4, AGC -71
    api = fe.check_ground_limits(now=2.0)
    assert api["state"] == {"0x050C": "red_high", "0x051A": "red_low"}
    assert api["summary"] == "red"
    assert all(t["source"] == "ground" for t in api["transitions"])
    assert [t["status"] for t in api["transitions"]] == ["red_high", "red_low"]


def test_steady_state_is_not_rejournalled():
    fe = RadioFrontend()
    _locked(fe)
    fe.update_rf(7.5, rssi_dbm=-131.0)
    for k in range(5):
        fe.check_ground_limits(now=float(k))
    assert fe.ground_limits.to_api()["seq"] == 2


def test_no_carrier_lock_is_not_checked_and_closes_open_alarms():
    fe = RadioFrontend()
    _locked(fe)
    fe.update_rf(7.5, rssi_dbm=-131.0)
    fe.check_ground_limits(now=1.0)
    fe.update_lock(LockState.UNLOCKED, LockState.UNLOCKED, LockState.UNLOCKED)
    api = fe.check_ground_limits(now=2.0)
    assert set(api["state"].values()) == {NO_SIGNAL}
    assert api["summary"] == NO_SIGNAL
    closing = api["transitions"][-2:]
    assert all(t["cleared"] and t["status"] == NO_SIGNAL for t in closing)


def test_packet_mode_measures_nothing():
    fe = RadioFrontend()
    _locked(fe, mode="PACKET")
    fe.update_rf(99.0)
    assert fe.check_ground_limits()["summary"] == NO_SIGNAL


def test_nominal_los_does_not_journal():
    fe = RadioFrontend()
    _locked(fe)
    fe.update_rf(12.0, rssi_dbm=-115.0)
    fe.check_ground_limits(now=1.0)
    fe.update_lock(LockState.UNLOCKED, LockState.UNLOCKED, LockState.UNLOCKED)
    fe.check_ground_limits(now=2.0)
    assert fe.ground_limits.to_api()["seq"] == 0


@pytest.mark.asyncio
async def test_api_ground_limits_and_since():
    fe = RadioFrontend()
    _locked(fe)
    fe.update_rf(7.5, rssi_dbm=-131.0)
    async with TestClient(TestServer(build_app(fe))) as client:
        d = await (await client.get("/api/ground-limits")).json()
        assert d["source"] == "ground"
        assert d["limits"]["0x050C"]["red_high"] == -4.0
        assert d["limits"]["0x051A"]["source"] == "ground"
        assert d["seq"] == 2 and len(d["transitions"]) == 2
        d2 = await (await client.get("/api/ground-limits?since=2")).json()
        assert d2["transitions"] == []
        bad = await client.get("/api/ground-limits?since=x")
        assert bad.status == 400
        st = await (await client.get("/api/status")).json()
        assert st["ground_limit_state"]["0x050C"] == "red_high"


def test_radio_page_shows_ground_limits_bilingually():
    html = MODERN.read_text()
    assert 'id="gl-card"' in html and "ground_limit_state" in html
    assert "renderParam" in html          # P3 triad + deviation bar
    fr = FR.read_text()
    for key in ("Ground limits", "BER (ground)", "AGC (ground)",
                "NOT CHECKED", "No carrier lock: nothing to measure"):
        assert f'"{key}"' in fr
