"""Scenario score from the commands the team sends (scenario_scoring.py).

INSTRUCTOR_CONSOLE_DESIGN.md §13 item 3: the score was always 0 % because
nothing recorded a response. It is now computed from evidence the simulator
has — telecommands (which, when, with which arguments, what S1 said), the
resulting state, and commands the scenario marks harmful.
"""
from pathlib import Path

import pytest

from smo_common.commanding.catalog import load_catalog
from smo_common.commanding.encode import encode
from smo_simulator import scenario_scoring as sc
from smo_simulator.scenario_engine import ScenarioEngine

REPO = Path(__file__).resolve().parents[2]
CFG = REPO / "configs" / "eosat1"
SCENARIOS = CFG / "scenarios"


@pytest.fixture(scope="module")
def cat():
    return load_catalog(CFG)


def _compile(cat, expected, harmful=(), n_events=1):
    rs, hs, errs = sc.compile_rules(list(expected), list(harmful), catalog=cat,
                                    param_ids=sc._param_ids(CFG),
                                    targets=dict(sc.DEFAULT_TARGETS_S), n_events=n_events)
    assert errs == [], errs
    return rs, hs


def _send(scorer, cat, t, name, seq, args=None, fate=None, apid=0x65):
    cmd = cat.get(name)
    data = encode(name, args or {}, catalog=cat)
    data = data if isinstance(data, (bytes, bytearray)) else bytes(data)
    scorer.observe_tc(t, int(cmd["service"]), int(cmd["subtype"]), data, apid, seq)
    if fate == "completed":
        scorer.observe_verification(1, apid, seq)
        scorer.observe_verification(7, apid, seq)
    elif fate == "rejected":
        scorer.observe_verification(2, apid, seq, 0x0003, "bad arg")
    elif fate == "failed":
        scorer.observe_verification(1, apid, seq)
        scorer.observe_verification(8, apid, seq, 0x0011, "exec")


# ── parsing ─────────────────────────────────────────────────────────────────

def test_tc_notation_resolves_against_the_catalogue(cat):
    spec = sc.parse_tc("AOCS_DISABLE_WHEEL(wheel_idx=0|1)", cat)
    assert (spec["service"], spec["subtype"], spec["func_id"]) == (8, 1, 2)
    assert spec["args"] == {"wheel_idx": [0, 1]}
    with pytest.raises(ValueError, match="unknown command"):
        sc.parse_tc("AOCS_DISABLE_WHEELS", cat)
    with pytest.raises(ValueError, match="no argument"):
        sc.parse_tc("AOCS_DISABLE_WHEEL(wheel=0)", cat)


def test_state_notation_takes_names_and_ids():
    ids = sc._param_ids(CFG)
    assert sc.parse_state("payload.mode == 0", ids)["pid"] == 0x0600
    assert sc.parse_state("0x0600 <= 1", ids)["op"] == "<="
    with pytest.raises(ValueError, match="unknown parameter"):
        sc.parse_state("payload.mood == 0", ids)


def test_bad_declarations_become_load_issues_not_crashes(cat):
    _rs, _hs, errs = sc.compile_rules(
        [{"category": "recover", "tc": "NOPE"}, {"category": "x", "after": "ghost"}],
        [{"reason": "no tc"}], catalog=cat, param_ids={}, targets={}, n_events=0)
    assert len(errs) == 3


# ── the model ───────────────────────────────────────────────────────────────

def _scorer(cat, expected, harmful=(), **kw):
    rs, hs = _compile(cat, expected, harmful)
    s = sc.ScenarioScorer(rs, hs, catalog=cat, has_inject_events=True, **kw)
    s.observe_event(0, "inject", 100.0)                  # the fault at T+100 s
    return s


EXP = [
    {"category": "detect", "description": "see it"},                     # observed
    {"category": "isolate", "id": "iso", "tc": "GET_PARAM(param_id=0x014C)", "within_s": 300},
    {"category": "recover", "id": "shed", "tc": ["PAYLOAD_SET_MODE(mode=0|1)", "EPS_POWER_OFF(line_index=3)"],
     "state": "payload.mode <= 1", "within_s": 600, "after": "iso"},
]


def test_nothing_sent_scores_zero_and_lists_not_seen(cat):
    s = _scorer(cat, EXP)
    out = s.evaluate(1000.0)
    st = [r["status"] for r in out["responses"]]
    assert st == ["observed", "missed", "missed"]
    assert out["score_pct"] == 0.0 and out["possible"] == 2.0
    assert all(r["evidence"] == [] for r in out["responses"])
    assert out["metrics"] == {}


def test_done_on_time_with_evidence_and_state(cat):
    s = _scorer(cat, EXP)
    s.observe_params(0.0, {0x0600: 2})
    _send(s, cat, 160.0, "GET_PARAM", 1, {"param_id": 0x014C}, "completed")
    _send(s, cat, 300.0, "PAYLOAD_SET_MODE", 2, {"mode": 1}, "completed")
    s.observe_params(305.0, {0x0600: 1})
    out = s.evaluate(1000.0)
    iso, shed = out["responses"][1], out["responses"][2]
    assert (iso["status"], iso["time_s"]) == ("done", 60.0)
    assert iso["evidence"][0]["name"] == "GET_PARAM" and iso["evidence"][0]["fate"] == "completed"
    assert (shed["status"], shed["time_s"]) == ("done", 205.0)      # when the state followed
    assert [e["kind"] for e in shed["evidence"]] == ["tc", "state"]
    assert out["score_pct"] == 100.0
    m = out["metrics"]
    assert m["mttd"]["inferred"] and m["mttd"]["s"] == 60.0          # first relevant command
    assert (m["mtti"]["s"], m["mtti"]["inferred"]) == (60.0, False)
    assert m["mtti"]["source"]["text"] == "iso: GET_PARAM(param_id=332)"
    assert m["mttr"]["s"] == 205.0


def test_late_wrong_and_order(cat):
    # late: after within_s
    s = _scorer(cat, EXP[:2])
    _send(s, cat, 500.0, "GET_PARAM", 1, {"param_id": 0x014D})     # wrong argument: no match
    _send(s, cat, 450.0, "GET_PARAM", 2, {"param_id": 0x014C}, "completed")
    r = s.evaluate(900.0)["responses"][1]
    assert (r["status"], r["credit"], r["time_s"]) == ("late", 0.5, 350.0)

    # wrong: rejected by the spacecraft
    s = _scorer(cat, EXP[:2])
    _send(s, cat, 150.0, "GET_PARAM", 1, {"param_id": 0x014C}, "rejected")
    r = s.evaluate(900.0)["responses"][1]
    assert r["status"] == "wrong" and "rejected" in r["note"]["text"] and r["evidence"][0]["fate"] == "rejected"

    # wrong: the state never followed the command
    s = _scorer(cat, EXP)
    s.observe_params(0.0, {0x0600: 2})
    _send(s, cat, 150.0, "GET_PARAM", 1, {"param_id": 0x014C})
    _send(s, cat, 200.0, "EPS_POWER_OFF", 2, {"line_index": 3}, "completed")
    r = s.evaluate(900.0)["responses"][2]
    assert r["status"] == "wrong" and "never followed" in r["note"]["text"]

    # wrong: sent before its prerequisite
    s = _scorer(cat, EXP)
    s.observe_params(0.0, {0x0600: 2})
    _send(s, cat, 120.0, "PAYLOAD_SET_MODE", 1, {"mode": 0}, "completed")
    s.observe_params(121.0, {0x0600: 0})
    _send(s, cat, 200.0, "GET_PARAM", 2, {"param_id": 0x014C}, "completed")
    r = s.evaluate(900.0)["responses"][2]
    assert r["status"] == "wrong" and "before iso" in r["note"]["text"]


def test_commands_before_the_fault_do_not_count(cat):
    s = _scorer(cat, EXP[:2])
    _send(s, cat, 50.0, "GET_PARAM", 1, {"param_id": 0x014C}, "completed")
    assert s.evaluate(900.0)["responses"][1]["status"] == "missed"


def test_link_refused_command_is_wrong_not_done(cat):
    s = _scorer(cat, EXP[:2])
    cmd = cat.get("GET_PARAM")
    s.observe_tc(150.0, 20, 3, encode("GET_PARAM", {"param_id": 0x014C}, catalog=cat), 0x65, 9,
                 link_refused=True)
    r = s.evaluate(900.0)["responses"][1]
    assert r["status"] == "wrong" and "not uplinked" in r["note"]["text"]
    assert cmd["service"] == 20


def test_harmful_penalty_once_per_entry(cat):
    harm = [{"tc": "AOCS_ENABLE_WHEEL(wheel_idx=0)", "reason": "seized wheel", "penalty": 15}]
    s = _scorer(cat, EXP[:2], harm)
    _send(s, cat, 150.0, "GET_PARAM", 1, {"param_id": 0x014C}, "completed")
    _send(s, cat, 160.0, "AOCS_ENABLE_WHEEL", 2, {"wheel_idx": 0}, "completed")
    _send(s, cat, 170.0, "AOCS_ENABLE_WHEEL", 3, {"wheel_idx": 0}, "completed")
    _send(s, cat, 180.0, "AOCS_ENABLE_WHEEL", 4, {"wheel_idx": 1}, "completed")   # another wheel: fine
    out = s.evaluate(900.0)
    assert out["harmful"][0]["applied"] and len(out["harmful"][0]["evidence"]) == 2
    assert out["penalty"] == 15 and out["score_pct"] == 85.0


def test_only_observational_responses_are_not_scored(cat):
    s = _scorer(cat, [{"category": "detect", "description": "watch"}])
    out = s.evaluate(900.0)
    assert out["score_pct"] is None and out["responses"][0]["status"] == "observed"


def test_state_only_response_and_reference_start(cat):
    rs, hs = _compile(cat, [{"category": "command", "state": "obdh.sw_image == 1",
                             "ref": "start", "within_s": 100}])
    s = sc.ScenarioScorer(rs, hs, catalog=cat, has_inject_events=False)
    s.observe_params(0.0, {0x0311: 0})
    s.observe_params(80.0, {0x0311: 1})
    r = s.evaluate(200.0)["responses"][0]
    assert (r["status"], r["time_s"], r["evidence"][0]["kind"]) == ("done", 80.0, "state")


def test_inject_that_never_fired_is_not_reached(cat):
    rs, hs = _compile(cat, EXP[1:2])
    s = sc.ScenarioScorer(rs, hs, catalog=cat, has_inject_events=True)
    _send(s, cat, 10.0, "GET_PARAM", 1, {"param_id": 0x014C})
    out = s.evaluate(900.0)
    assert out["responses"][0]["status"] == "not_reached" and out["score_pct"] is None


def test_log_round_trips_for_breakpoints(cat):
    s = _scorer(cat, EXP)
    _send(s, cat, 150.0, "GET_PARAM", 1, {"param_id": 0x014C}, "completed")
    s.observe_params(0.0, {0x0600: 2})
    s2 = _scorer(cat, EXP)
    s2.set_state(s.get_state())
    assert s2.evaluate(900.0) == s.evaluate(900.0)


# ── through the scenario engine ─────────────────────────────────────────────

class _FM:
    def __init__(self):
        self.n = 0

    def inject(self, **kw):
        self.n += 1
        return f"f{self.n}"

    def clear(self, fid):
        return True

    def clear_all(self):
        pass


def test_engine_level_debrief_for_a_shipped_scenario(cat):
    se = ScenarioEngine(failure_manager=_FM())
    se.load_scenarios_from_dir(SCENARIOS)
    assert se.load_issues() == []
    name = next(d.name for d in se._scenarios.values() if d.file_id == "aocs_wheel_failure")
    assert se.start(name)
    params = {0x0256: 1}
    for _ in range(250):
        se.tick(1.0, params)                       # inject at T+200
    data = encode("AOCS_DISABLE_WHEEL", {"wheel_idx": 2}, catalog=cat)
    se.observe_tc(8, 1, bytes(data), 0x65, 42)
    se._scorer.observe_verification(7, 0x65, 42)
    params[0x0256] = 0
    se.tick(1.0, params)
    se.record_response("detect", "instructor saw them look at RW3")
    d = se.stop()
    assert d.id == "aocs_wheel_failure"
    rec = d.responses[2]
    assert rec["status"] == "done" and rec["evidence"][0]["name"] == "AOCS_DISABLE_WHEEL"
    assert 49.0 <= rec["time_s"] <= 52.0
    assert d.score_pct == 100.0 and d.mttr_s == rec["time_s"]
    assert d.marks and d.marks[0]["category"] == "detect"
    assert d.mttd_s is not None


def test_every_shipped_scenario_compiles_and_most_are_scored():
    se = ScenarioEngine(failure_manager=_FM())
    se.load_scenarios_from_dir(SCENARIOS)
    assert se.load_issues() == []
    scored = [d for d in se._scenarios.values()
              if any(r["tc"] or r["state"] for r in d.scoring[0])]
    assert len(scored) >= 30, "scenarios lost their machine-checkable responses"
    # every scored scenario checks at least one team ACTION, not only looks
    for d in scored:
        assert any(r["tc"] for r in d.scoring[0]), d.file_id


def test_scenario_schema_accepts_the_scoring_fields():
    from smo_common.config.loader import load_scenarios
    scns = load_scenarios(CFG)
    assert len(scns) == len(list(SCENARIOS.glob("*.yaml")))
    assert any(s.harmful_commands for s in scns)


# ── the real engine: telecommands and S1 reports reach the scorer ──────────

def test_real_engine_scores_a_wheel_disable(tmp_path, monkeypatch, cat):
    import os
    from smo_common.protocol.ecss_packet import build_tc_packet
    from smo_simulator.engine import SimulationEngine
    monkeypatch.setenv("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    monkeypatch.setenv("SMO_AUTO_SNAPSHOT_DIR", str(tmp_path / "auto"))
    e = SimulationEngine(CFG)
    e._handle_instructor_cmd({"type": "set_phase", "phase": 6})
    e.subsystems["eps"]._state.power_lines["aocs_wheels"] = True
    e.subsystems["aocs"]._state.active_wheels = [True] * 4
    se = e._scenario_engine
    name = next(d.name for d in se._scenarios.values() if d.file_id == "rw_bearing")
    e._handle_instructor_cmd({"type": "start_scenario", "name": name})
    for _ in range(185):
        e._tick_once(1.0)                                  # inject at T+180
    assert se._scorer.first_inject is not None
    assert e.params.get(0x0255) == 1                       # RW2 degrading, still enabled

    def send(seq, args):
        e._dispatch_tc(build_tc_packet(apid=0x65, service=8, subtype=1,
                                       data=encode("AOCS_DISABLE_WHEEL", args, catalog=cat),
                                       seq_count=seq))
        for _ in range(3):
            e._tick_once(1.0)
    send(11, {"wheel_idx": 2})                             # the wrong wheel: no match
    send(12, {"wheel_idx": 1})
    e._handle_instructor_cmd({"type": "stop_scenario"})
    d = se.last_debrief()
    r = d.responses[2]
    assert r["status"] == "done", r
    assert [c["seq"] for c in d.commands] == [11, 12]
    ev = r["evidence"][0]
    assert ev["name"] == "AOCS_DISABLE_WHEEL" and ev["fate"] in ("accepted", "completed")
    assert [x["kind"] for x in r["evidence"]] == ["tc", "state"]
    assert d.score_pct == 100.0
    # the auto snapshot before the scenario inject is on disk
    e._auto_snapshots.wait()
    files = list((tmp_path / "auto").glob("auto_scn-rw_bearing-*__aocs.rw_bearing.json.gz"))
    assert len(files) == 1, list((tmp_path / "auto").iterdir())
    assert os.path.getsize(files[0]) < 5_000_000
