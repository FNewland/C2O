"""System margin ladder "C2O default" (REDESIGN_DECISIONS.md ruling 2): 25 / 20 / 20 / 10 %
at MDR / PRR–SRR / PDR / CDR for system mass and power, with the margin convention stated.
Checked against the table of the redesign (§3, "Margin defaults by phase")."""
from __future__ import annotations

import pytest

from spacecdf_server.services import margin_policy as mp
from spacecdf_server.services import rule_config as rc
from spacecdf_server.services.gate_evaluator import evaluate_gate

# Ruling 2 / redesign §3 table
TABLE = {"mdr": 25, "prr": 20, "srr": 20, "pdr": 20, "cdr": 10}
# The sources the table cites per gate: GSFC-STD-1000G Rule 1.06 (25/20/15/10) and the ESA IOD
# margin policy (20 % at PDR); the C2O default takes the stricter at each gate.
GSFC = {"mdr": 25, "prr": 20, "srr": 20, "pdr": 15, "cdr": 10}
IOD = {"pdr": 20}


def test_config_is_valid():
    assert rc.validate("margin_policy", rc.load("margin_policy")) == []


@pytest.mark.parametrize("gate,pct", TABLE.items())
def test_ladder_matches_the_table(gate, pct):
    assert mp.system_margin_percent(gate, "mass") == pct
    assert mp.system_margin_percent(gate, "power") == pct


@pytest.mark.parametrize("gate", TABLE)
def test_ladder_is_the_stricter_source(gate):
    assert TABLE[gate] == max(GSFC[gate], IOD.get(gate, 0))


def test_ladder_is_labelled_and_states_its_convention():
    lad = mp.ladder()
    assert lad["label"] == {"en": "C2O default", "fr": "Valeur par défaut C2O"}
    assert lad["convention"]["id"] == "percent_of_nominal"
    assert "nominal × (1 + margin)" in lad["convention"]["text"]["en"]
    assert "GSFC" in lad["convention"]["text"]["en"]
    assert [r["gate"] for r in lad["by_gate"]] == ["mdr", "prr", "srr", "pdr", "cdr"]
    assert lad["applies_to"] == ["mass", "power"]


def test_old_gate_name_and_unknown_gate():
    assert mp.system_margin_percent("MCR") == 25
    assert mp.system_margin_percent(None) == 20 and mp.system_margin_percent("xyz") == 20   # flat ESA 20 %


ELEMENTS = [{"id": "sc", "element_type": "system", "segment": "space"},
            {"id": "u1", "element_type": "component", "parent_id": "sc", "segment": "space",
             "mass_kg": 4.0, "power_avg_w": 10.0, "trl": 9, "heritage_json": ["x"]}]


@pytest.mark.parametrize("gate", TABLE)
def test_budgets_use_the_gate_step(gate):
    res = mp.evaluate_margins(ELEMENTS, {"power.sa_power_eol_w": 100.0}, mass_limit_kg=12.0, gate=gate)
    nominal = res["mass"]["nominal_dry_kg"]
    assert res["mass"]["system_margin_percent"] == TABLE[gate]
    assert res["mass"]["total_dry_kg"] == pytest.approx(nominal * (1 + TABLE[gate] / 100), abs=1e-3)
    assert res["power"]["system_margin_percent"] == TABLE[gate]
    assert res["system_margin"]["mass_percent"] == TABLE[gate]
    msg = next(c for c in res["checks"] if c["id"] == "MP-MASS-01")["detail"]["en"]
    assert f"system ({TABLE[gate]} %)" in msg


@pytest.mark.parametrize("gate,pct", [("MDR", 25), ("PRR", 20), ("SRR", 20), ("PDR", 20)])
def test_gate_budget_criteria_use_the_gate_step(gate, pct):
    """dry 5 kg: × 1.25 = 6.25 kg > 6 kg at MDR-level margins; × 1.2 = 6.0 kg passes."""
    params = {"mass.dry_mass_kg": 5.0, "power.total_sunlight_w": 10.0, "power.sa_power_eol_w": 30.0}
    cid = {"PRR": "PRR-EC-05", "SRR": "SRR-EC-06", "PDR": "PDR-EC-03"}.get(gate)
    if cid is None:
        return   # the MDR feasibility criterion is not a margin-ladder check
    res = evaluate_gate(gate, design_params=params, target_mass_kg=6.0)
    c = {x["id"]: x for x in res["criteria"]}[cid]
    assert c["evidence_params"]["margin"] == f"{pct}"
    assert c["status"] == "pass"
    tight = evaluate_gate(gate, design_params=params, target_mass_kg=6.0, margin_gate="mdr")
    assert {x["id"]: x for x in tight["criteria"]}[cid]["status"] == "fail", "25 % does not fit in 6 kg"


def test_budget_criterion_without_target_is_not_invented():
    params = {"mass.dry_mass_kg": 5.0, "power.total_sunlight_w": 10.0, "power.sa_power_eol_w": 30.0}
    c = {x["id"]: x for x in evaluate_gate("PRR", design_params=params)["criteria"]}["PRR-EC-05"]
    assert c["status"] == "not_evaluated"
