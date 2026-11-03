"""MCS pass log (smo_mcs/pass_log.py): the last completed pass for the
logbook handover form, from ground knowledge only (propagator visibility +
TM frames), and the instructor's published session label."""
from pathlib import Path

from smo_mcs.pass_log import PassLog

REPO = Path(__file__).resolve().parents[2]
MCS_JS = REPO / "packages/smo-mcs/src/smo_mcs/static/modern/mcs.js"


def _run(log, t0, t1, contact, station="Svalbard", el=None, tm=None, step=10):
    t = t0
    while t < t1:
        log.update(t, contact, station, el(t) if el else 10.0, tm(t) if tm else None)
        t += step
    return t


def test_aos_los_max_elevation_and_tm_evidence():
    log = PassLog()
    _run(log, 0, 100, False)
    assert log.view() == {"current": None, "last": None, "passes": []}
    _run(log, 100, 700, True, el=lambda t: 40 - abs(t - 400) / 10, tm=lambda t: t - 2 if t >= 130 else 50)
    cur = log.view()["current"]
    assert cur["aos"] == 100 and cur["aos_seen"] and cur["los"] is None
    _run(log, 700, 800, False, tm=lambda t: 690)
    last = log.view()["last"]
    assert last["station"] == "Svalbard" and last["aos"] == 100 and last["los"] == 700
    assert last["max_el_deg"] == 40.0
    assert last["tm"] and last["tm_first"] == 128 and last["tm_last"] == 688
    assert last["source"] == "ground" and log.view()["current"] is None


def test_a_pass_with_no_tm_says_so_and_newest_first():
    log = PassLog()
    _run(log, 0, 50, False)
    _run(log, 50, 100, True, station="Inuvik", tm=lambda t: 10)     # TM older than AOS
    _run(log, 100, 200, False)
    _run(log, 200, 300, True, station="Svalbard", tm=lambda t: t)
    _run(log, 300, 310, False)
    v = log.view()
    assert [p["station"] for p in v["passes"]] == ["Svalbard", "Inuvik"]
    assert v["passes"][1]["tm"] is False and v["last"]["tm"] is True


def test_console_started_mid_pass_and_station_handover():
    log = PassLog()
    _run(log, 0, 100, True, station="Inuvik")
    _run(log, 100, 200, True, station="Svalbard")
    _run(log, 200, 210, False)
    a, b = log.view()["passes"][1], log.view()["passes"][0]
    assert a["station"] == "Inuvik" and a["aos_seen"] is False and a["los"] == 100
    assert b["station"] == "Svalbard" and b["aos_seen"] is True


def test_time_jump_back_forgets_what_did_not_happen():
    log = PassLog()
    _run(log, 0, 100, False)
    _run(log, 100, 200, True)
    _run(log, 200, 300, False)
    _run(log, 1000, 1100, True)
    _run(log, 1100, 1200, False)
    assert len(log.view()["passes"]) == 2
    # breakpoint load back to t=250: the second pass is in the future now
    log.update(250, True, "Svalbard", 5.0, None)
    v = log.view()
    assert [p["aos"] for p in v["passes"]] == [100]
    assert v["current"]["aos_seen"] is False          # its real AOS is unknown


def test_mcs_ingests_only_the_session_label(tmp_path):
    from unittest.mock import patch

    from smo_common.config.schemas import MCSDisplayConfig
    from smo_mcs.server import MCSServer
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}):
        s = MCSServer(config_dir=str(REPO / "configs" / "eosat1"), connect_host="localhost",
                      connect_port=9999, http_port=0)
    s._time_source = "sim"
    s._ingest_session_label({"session_label": "  Day 3,   shift B ", "scenario": "Wheel seizure"})
    assert s._session_label == "Day 3, shift B"
    s._ingest_session_label({"speed": 1})              # absent: keep the last one
    assert s._session_label == "Day 3, shift B"
    s._time_source = "real"
    s._ingest_session_label({"session_label": "other"})
    assert s._session_label == "Day 3, shift B"


def test_console_fills_last_pass_and_the_hand_in_scenario():
    js = MCS_JS.read_text(encoding="utf-8")
    assert 'case "last_pass": return lbDonePassText((S.state.pass_log || {}).last);' in js
    assert "scenario: lbSessionLabel()" in js
