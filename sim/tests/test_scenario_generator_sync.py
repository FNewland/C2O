"""Guard against drift between tools/scenario_generator.py and the simulator.

The generator used to ship a hard-coded ``SUBSYSTEMS`` catalog that mirrored the
``inject_failure()`` handlers in each subsystem model. Because it was a manual
copy it silently drifted: at one point it was missing the entire ``payload``
subsystem plus several TTC/OBDH failure modes, so those failures could never be
selected from the generator UI and broken scenarios looked fine.

It now builds ``SUBSYSTEMS`` from ``smo_simulator.failure_catalog`` — the same
declarative FAILURE_SPECS the instructor console and the FailureManager use — so
the drift is structurally impossible. These tests hold that property: the
generator must expose exactly the catalogue's failures, per subsystem, with the
typed parameter specs attached.
"""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "tools" / "scenario_generator.py"

# Subsystems the generator must cover. `prop` is here because propulsion
# (S8 funcs 108-118, HK SID 9) landed after the generator's hand-copied table
# was written and never made it in.
SUBSYSTEMS = ("eps", "aocs", "tcs", "ttc", "obdh", "payload", "prop")


def _generator_catalog() -> dict[str, dict]:
    """The generator's live SUBSYSTEMS catalogue.

    Imported (not ast-parsed) now that it is derived rather than literal.
    """
    import sys

    sys.path.insert(0, str(REPO_ROOT / "tools"))
    import scenario_generator  # noqa: PLC0415

    return scenario_generator.SUBSYSTEMS


def _catalog_failures() -> dict[str, set[str]]:
    from smo_simulator.failure_catalog import catalog

    return {sub: set(specs) for sub, specs in catalog().items()}


def test_generator_covers_every_subsystem():
    """Every subsystem model must be represented in the generator catalog."""
    catalog = _generator_catalog()
    missing = set(SUBSYSTEMS) - set(catalog)
    assert not missing, f"Generator SUBSYSTEMS missing subsystem(s): {sorted(missing)}"


@pytest.mark.parametrize("subsystem", sorted(SUBSYSTEMS))
def test_generator_matches_model_failures(subsystem):
    """The generator's failure list for each subsystem equals the catalogue's."""
    gen = set(_generator_catalog().get(subsystem, {}).get("failures", {}))
    model = _catalog_failures().get(subsystem, set())
    assert gen == model, (
        f"{subsystem}: generator/catalogue failure lists differ.\n"
        f"  in catalogue but not generator: {sorted(model - gen)}\n"
        f"  in generator but not catalogue: {sorted(gen - model)}"
    )


def test_generator_covers_the_propulsion_subsystem():
    """Propulsion landed after the generator's hand-copied table was written."""
    assert "prop" in _generator_catalog(), (
        "the scenario generator cannot author a propulsion failure")


@pytest.mark.parametrize("subsystem", sorted(SUBSYSTEMS))
def test_generator_carries_the_typed_parameter_specs(subsystem):
    """Each generator failure entry carries its ParamSpec list.

    The generator's form is rendered from these, so an entry without them
    would fall back to the model defaults — which is exactly the "no way to
    choose which wheel" complaint this work fixes.
    """
    from smo_simulator.failure_catalog import get_spec

    for name, entry in _generator_catalog()[subsystem]["failures"].items():
        assert "params" in entry and "magnitude" in entry, (
            f"{subsystem}.{name}: generator entry has no parameter spec")
        spec = get_spec(subsystem, name)
        assert [p["name"] for p in entry["params"]] == [p.name for p in spec.params], (
            f"{subsystem}.{name}: generator parameter list differs from the spec")


def test_generator_writes_the_scoring_fields_the_simulator_reads(tmp_path):
    """Expected responses keep their evidence (tc / state / within_s) and
    harmful commands; the file loads into the scenario engine without issue
    (scenario_scoring.py) and the schema accepts it."""
    import sys
    import yaml

    sys.path.insert(0, str(REPO_ROOT / "tools"))
    import scenario_generator  # noqa: PLC0415
    from smo_common.config.schemas import ScenarioConfig
    from smo_simulator.scenario_engine import ScenarioEngine

    data = {
        "name": "Gen scoring", "duration_s": 900,
        "events": [{"type": "inject", "subsystem": "aocs", "failure": "rw_bearing",
                    "time_offset_s": 60, "wheel": 1}],
        "expected_responses": [
            {"category": "recover", "description": "Disable RW2",
             "tc": "AOCS_DISABLE_WHEEL(wheel_idx=1); AOCS_DESATURATE",
             "state": "aocs.rw2_enabled == 0", "within_s": "600"},
            {"category": "detect", "description": "Notice the temperature", "tc": "", "state": ""}],
        "harmful_commands": [{"tc": "AOCS_ENABLE_WHEEL(wheel_idx=1)", "reason": "Re-enables it",
                              "penalty": "10"}],
    }
    text, filename = scenario_generator.generate_yaml(data)
    doc = yaml.safe_load(text)
    ScenarioConfig.model_validate(doc)
    r0 = doc["expected_responses"][0]
    assert r0["tc"] == ["AOCS_DISABLE_WHEEL(wheel_idx=1)", "AOCS_DESATURATE"]
    assert r0["state"] == "aocs.rw2_enabled == 0" and r0["within_s"] == 600
    assert "tc" not in doc["expected_responses"][1]
    assert doc["harmful_commands"][0]["penalty"] == 10
    (tmp_path / filename).write_text(text)
    se = ScenarioEngine()
    se.load_scenarios_from_dir(tmp_path)
    assert se.load_issues() == []
    assert scenario_generator.check_scoring(data) == []
    bad = dict(data, expected_responses=[{"category": "recover", "description": "x",
                                          "tc": "AOCS_DISABLE_WHEEL(wheel=1)"}])
    assert any("no argument" in e for e in scenario_generator.check_scoring(bad))
