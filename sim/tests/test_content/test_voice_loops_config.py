"""configs/eosat1/voice/voice_loops.yaml: schema, and consistency with
mcs/positions.yaml and Franz's rulings V3/V4 (docs/plan_2026-11/
REDESIGN_DECISIONS.md): an FD loop for all positions, Ops coordination, one
loop per subsystem, an Instructor/SIM loop hidden from students, recordings
off. The validator itself (smo_mcs.voice.validate) is also exercised on
broken copies so it keeps catching each class of mistake.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from smo_mcs import voice

SIM = Path(__file__).resolve().parents[2]
CONFIG = SIM / "configs" / "eosat1"
RAW = yaml.safe_load((CONFIG / "voice" / "voice_loops.yaml").read_text())
MCS_POSITIONS = list((yaml.safe_load((CONFIG / "mcs" / "positions.yaml").read_text()) or {})["positions"])
CFG = voice.load_voice_loops(CONFIG)
BY_ID = {lp.id: lp for lp in CFG.loops}


def test_the_shipped_file_validates():
    assert voice.validate(RAW, MCS_POSITIONS) == []


def test_positions_are_the_mcs_positions_plus_the_two_roles():
    assert len(MCS_POSITIONS) == 7
    assert list(CFG.positions) == MCS_POSITIONS
    assert CFG.all_positions == tuple(MCS_POSITIONS) + ("instructor", "sim")


def test_recordings_are_off_by_default():
    assert RAW["recordings"] is False                     # V3


def test_fd_loop_lets_every_position_talk():
    fd = BY_ID["fd"]
    assert not fd.instructor_only
    assert all(fd.access_for(p) == "TALK" for p in CFG.all_positions)
    assert all(fd.start_for(p) in ("MON", "TALK") for p in CFG.all_positions), \
        "everyone hears the FD loop from the start"


def test_ops_coordination_and_one_loop_per_subsystem_exist():
    want = {"ops_coord", "eps_tcs", "aocs_fd", "ttc", "payload", "fdir_systems", "propulsion"}
    assert want <= set(BY_ID)


def test_each_console_position_owns_its_subsystem_loop():
    owner = {"eps_tcs": "eps_tcs", "aocs": "aocs_fd", "ttc": "ttc", "payload_ops": "payload",
             "fdir_systems": "fdir_systems", "propulsion": "propulsion"}
    for pos, lid in owner.items():
        assert BY_ID[lid].access_for(pos) == "TALK" and BY_ID[lid].start_for(pos) == "TALK", pos
        assert BY_ID[lid].access_for("flight_director") == "TALK", lid


def test_instructor_loop_is_hidden_from_every_student_position():
    inst = [lp for lp in CFG.loops if lp.instructor_only]
    assert [lp.id for lp in inst] == ["instructor_sim"]
    lp = inst[0]
    for pos in MCS_POSITIONS:
        assert lp.access_for(pos) == "OFF", pos
    assert lp.access_for("instructor") == "TALK" and lp.access_for("sim") == "TALK"


def test_labels_are_bilingual_and_colours_are_tokens():
    for lp in CFG.loops:
        assert lp.label["en"].strip() and lp.label["fr"].strip()
        assert lp.colour in voice.COLOURS
    for role, lab in CFG.role_labels.items():
        assert lab["en"].strip() and lab["fr"].strip(), role


def test_at_most_one_talk_loop_at_start_for_every_position():
    for pos in CFG.all_positions:
        assert sum(lp.start_for(pos) == "TALK" for lp in CFG.loops) <= 1, pos


def test_every_position_hears_something_and_room_ids_are_identifiers():
    for pos in CFG.all_positions:
        assert any(lp.access_for(pos) != "OFF" for lp in CFG.loops), pos
    assert len({lp.id for lp in CFG.loops}) == len(CFG.loops)


# ── the validator catches each class of mistake ─────────────────────────

def _broken(mutate) -> list[str]:
    d = copy.deepcopy(RAW)
    mutate(d)
    return voice.validate(d, MCS_POSITIONS)


def _loop(d, lid):
    return next(lp for lp in d["loops"] if lp["id"] == lid)


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: _loop(d, "instructor_sim")["access"].update(eps_tcs="MON"), "gives student position eps_tcs"),
    (lambda d: _loop(d, "instructor_sim")["access"].update(default="MON"), "access.default OFF"),
    (lambda d: _loop(d, "ttc")["access"].update(default=False), 'write "OFF" in quotes'),
    (lambda d: _loop(d, "ttc")["access"].update(astronaut="TALK"), "unknown position"),
    (lambda d: _loop(d, "ttc")["start"].update(eps_tcs="TALK"), "above its access"),
    (lambda d: _loop(d, "fd")["start"].update(eps_tcs="TALK"), "one talk loop at a time"),
    (lambda d: _loop(d, "ttc").update(colour="#ff0000"), "colour"),
    (lambda d: _loop(d, "ttc")["label"].pop("fr"), "needs non-empty en and fr"),
    (lambda d: _loop(d, "ttc").update(id="TTC loop"), "is not an identifier"),
    (lambda d: d["loops"].append(copy.deepcopy(_loop(d, "ttc"))), "duplicate"),
    (lambda d: _loop(d, "ttc").update(extra=1), "unknown keys"),
    (lambda d: d.update(recordings="no"), "recordings"),
    (lambda d: d["role_positions"].pop("sim"), "role_positions"),
    (lambda d: d.update(loops=[]), "non-empty list"),
])
def test_validator_rejects(mutate, needle):
    errs = _broken(mutate)
    assert any(needle in e for e in errs), errs
