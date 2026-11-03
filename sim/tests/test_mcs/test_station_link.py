"""Station-measured link figures reach the MCS (walkthrough finding M1).

RSSI 0x0502, link margin 0x0503, BER 0x050C, Eb/N0 0x0519 and AGC 0x051A are
`ground_derived`: the station's receiver measures them. Nothing carried them
to the MCS, so the TT&C page "Key parameters" read "no data" all session and
25 GO/NO-GO checks on 13 cards could not be judged. Franz's ruling: feed them
to the MCS as a real station's monitoring data does, labelled as
station-measured, not spacecraft TM.

Pinned here:
* the simulator publishes a `ttc.station` block with the five receiver
  readings while a station has signal, and NO numbers (with a reason) when it
  has none;
* the MCS ingests it (and prefers the RF bridge's own receiver status when one
  is configured), publishes the values in the console state with their
  source, lists them in the catalogue as `origin: station`, and procedure
  GO/NO-GO checks can read them by name;
* none of it lands in the TM parameter cache, and no channel-model truth
  (GS penalty, injected impairments) is passed through.
"""
import asyncio
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from smo_common.config.schemas import MCSDisplayConfig
from smo_mcs.server import MCSServer
from smo_mcs.station_link import STATION_PARAMS, StationLink
from smo_mcs.procedure_runner import ProcedureRunner

REPO = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO / "configs" / "eosat1"

SIGNAL_BLOCK = {"ttc": {"station": {
    "source": "link_model", "signal": True, "band": "S", "reason": None,
    "rssi_dbm": -101.3, "link_margin_db": 12.4, "ber_log10": -9.5,
    "eb_n0_db": 16.0, "agc_db": -41.3}}}
NO_SIGNAL_BLOCK = {"ttc": {"station": {
    "source": "link_model", "signal": False, "band": None,
    "reason": "no signal: no station in view or no transponder",
    "rssi_dbm": None, "link_margin_db": None, "ber_log10": None,
    "eb_n0_db": None, "agc_db": None}}}


def _make_server() -> MCSServer:
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}):
        return MCSServer(config_dir=str(CONFIG_DIR), connect_host="localhost",
                         connect_port=9999, http_port=0)


# ── the feed itself ──────────────────────────────────────────────────

class TestStationLinkFeed:
    def test_signal_gives_the_five_readings(self):
        sl = StationLink()
        sl.ingest_sim_state(SIGNAL_BLOCK, now=100.0)
        v = sl.view(now=101.0)
        assert v["source"] == "link_model" and v["signal"] is True
        assert set(v["values"]) == {f"0x{p:04X}" for p in STATION_PARAMS}
        assert v["values"]["0x0503"] == pytest.approx(12.4)
        assert "link budget" in v["label"]

    def test_no_signal_gives_no_numbers_and_a_reason(self):
        sl = StationLink()
        sl.ingest_sim_state(NO_SIGNAL_BLOCK, now=100.0)
        v = sl.view(now=100.5)
        assert v["signal"] is False and v["values"] == {}
        assert "no signal" in v["reason"]

    def test_radio_is_preferred_and_an_unlocked_radio_measures_nothing(self):
        sl = StationLink()
        sl.ingest_sim_state(SIGNAL_BLOCK, now=100.0)
        sl.ingest_radio_status({"carrier_lock": "LOCKED", "mode": "RF",
                                "rssi_dbm": -99.0, "link_margin_db": 7.0,
                                "ber_log10": -8.0, "eb_n0_db": 16.6,
                                "agc_db": -39.0, "gs_penalty_db": 3.0},
                               now=100.0)
        v = sl.view(now=100.5)
        assert v["source"] == "radio" and "RF mode" in v["label"]
        assert v["values"]["0x0502"] == pytest.approx(-99.0)
        # Only the five receiver readings pass — never channel-model truth.
        assert set(v["values"]) == {f"0x{p:04X}" for p in STATION_PARAMS}
        assert "gs_penalty_db" not in str(v)

        sl.ingest_radio_status({"carrier_lock": "UNLOCKED", "rssi_dbm": -99.0},
                               now=101.0)
        v = sl.view(now=101.5)
        assert v["source"] == "radio" and v["signal"] is False
        assert v["values"] == {}, "an unlocked receiver reported a level"

    def test_a_silent_radio_hands_back_to_the_link_model(self):
        sl = StationLink()
        sl.ingest_radio_status({"carrier_lock": "LOCKED", "rssi_dbm": -99.0,
                                "link_margin_db": 7.0, "ber_log10": -8.0,
                                "eb_n0_db": 16.6, "agc_db": -39.0}, now=100.0)
        sl.ingest_sim_state(SIGNAL_BLOCK, now=110.0)
        assert sl.view(now=110.5)["source"] == "link_model"

    def test_nothing_fresh_is_no_data(self):
        sl = StationLink()
        sl.ingest_sim_state(SIGNAL_BLOCK, now=100.0)
        v = sl.view(now=200.0)
        assert v["source"] is None and v["values"] == {}


# ── the MCS ──────────────────────────────────────────────────────────

class TestMCSIntegration:
    async def test_values_reach_console_state_and_go_nogo(self):
        server = _make_server()
        server._station_link.ingest_sim_state(SIGNAL_BLOCK)
        server._running = True
        task = asyncio.create_task(server._state_poll_loop())
        await asyncio.sleep(1.3)
        server._running = False
        await asyncio.wait_for(task, 3.0)

        state = server._latest_state
        assert state["params"]["0x0502"] == pytest.approx(-101.3)
        assert state["params"]["0x051A"] == pytest.approx(-41.3)
        assert str(0x0503) in state["params_age"]
        assert state["station_link"]["source"] == "link_model"
        assert state["station_link"]["signal"] is True
        # Not spacecraft TM: never in the TM cache.
        for pid in STATION_PARAMS:
            assert pid not in server._param_cache

        # GO/NO-GO checks name them by their catalogue names.
        assert server._proc_get_telemetry("ttc.link_margin") == pytest.approx(12.4)
        assert server._proc_get_telemetry("ttc.rssi") == pytest.approx(-101.3)
        runner = ProcedureRunner(send_command_fn=None,
                                 get_telemetry_fn=server._proc_get_telemetry,
                                 time_fn=server.sim_now_ts)
        ok = await runner._wait_for_condition(
            {"parameter": "ttc.link_margin", "operator": ">", "value": 3.0,
             "timeout_s": 2})
        assert ok is True

    async def test_no_signal_is_published_as_such(self):
        server = _make_server()
        server._station_link.ingest_sim_state(NO_SIGNAL_BLOCK)
        server._running = True
        task = asyncio.create_task(server._state_poll_loop())
        await asyncio.sleep(1.3)
        server._running = False
        await asyncio.wait_for(task, 3.0)
        state = server._latest_state
        assert "0x0502" not in state["params"]
        assert state["station_link"]["signal"] is False
        assert "no signal" in state["station_link"]["reason"]
        assert server._proc_get_telemetry("ttc.rssi") is None

    async def test_catalogue_lists_station_params_but_no_other_ground_truth(self):
        server = _make_server()
        resp = await server._handle_param_catalog(None)
        import json
        cat = {p["id"]: p for p in json.loads(resp.body)["parameters"]}
        for pid in STATION_PARAMS:
            assert cat[pid]["origin"] == "station"
            assert cat[pid]["on_demand"] is False and cat[pid]["in_hk"] is False
            assert "Station-measured" in cat[pid]["description"]
        # Other ground-derived and instructor parameters stay out.
        for pid in (0x0509, 0x050A, 0x0216, 0x0538):
            assert pid not in cat


# ── the simulator side ───────────────────────────────────────────────

class TestSimulatorPublishesStationBlock:
    def _engine(self, tmp_path):
        os.environ.setdefault("SMO_DUMP_DIR", str(tmp_path / "dumps"))
        from smo_simulator.engine import SimulationEngine
        eng = SimulationEngine(CONFIG_DIR)
        eng._spacecraft_phase = 6
        eng.subsystems["obdh"]._state.sw_image = 1
        eng.subsystems["eps"]._state.power_lines["ttc_tx"] = True
        return eng

    def test_block_present_with_signal_and_without(self, tmp_path):
        eng = self._engine(tmp_path)
        st = eng.get_state_summary()["ttc"]["station"]
        assert set(st) >= {"source", "signal", "reason", "rssi_dbm",
                           "link_margin_db", "ber_log10", "eb_n0_db", "agc_db"}
        # Pass override: a station is in view; after lock the S-band budget
        # gives the five readings.
        eng._override_passes = True
        eng.params[0x05FF] = 1
        for _ in range(60):
            eng._tick_once(1.0)
        st = eng.get_state_summary()["ttc"]["station"]
        assert st["signal"] is True and st["band"] == "S"
        assert st["rssi_dbm"] > -140 and st["link_margin_db"] is not None
        assert "gs_penalty" not in str(st)
        # Both transponders dead: the station hears nothing (S4) and says so.
        ttc = eng.subsystems["ttc"]
        ttc.inject_failure("primary_failure", 1.0)
        ttc.inject_failure("redundant_failure", 1.0)
        for _ in range(3):
            eng._tick_once(1.0)
        st = eng.get_state_summary()["ttc"]["station"]
        assert st["signal"] is False and st["rssi_dbm"] is None
        assert st["reason"].startswith("no signal")


# ── the TT&C page ────────────────────────────────────────────────────

def test_ttc_page_shows_the_station_figures_and_says_where_they_come_from():
    js = (REPO / "packages/smo-mcs/src/smo_mcs/static/modern/mcs.js").read_text()
    i = js.index("ttc: { title:")
    ttc_cfg = js[i:js.index("pld: {", i)]
    for pid in STATION_PARAMS:
        assert f'"0x{pid:04X}"' in ttc_cfg, f"0x{pid:04X} missing from TT&C key parameters"
    assert 'id="ttc-station-note"' in js and "function stationLinkNote" in js
    note = js[js.index("function stationLinkNote"):]
    note = note[:note.index("\n}\n")]
    assert "not spacecraft TM" in note and "no signal" in note
    # A station measurement is never offered as a TC(20,3) on-demand fetch.
    assert 'p.origin !== "station"' in js
