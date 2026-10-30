"""SCDF-170 §1.1 — AnalysisContext: effective overrides reach ``flat`` (and are
sticky), modes come from mode elements + ModeElementRow, stations from the KB
selection, and ``context_hash`` is stable / changes with its inputs."""
from __future__ import annotations

import pytest

from tests.test_repositories.conftest import db_factory, study  # noqa: F401


@pytest.fixture()
def clean_caches():
    from spacecdf_server.routers import elements, requirements
    elements._elements.clear()
    elements._interfaces.clear()
    elements._mode_elements.clear()
    requirements.reset_requirement_cache()
    yield
    elements._elements.clear()
    elements._interfaces.clear()
    elements._mode_elements.clear()
    requirements.reset_requirement_cache()


async def _el(study_id, eid, name, etype, parent=None, domain=None, **extra):
    from spacecdf_server.db.element_repo import db_create_element
    from spacecdf_server.routers import elements as er
    d = {"id": eid, "study_id": study_id, "name": name, "element_type": etype, "parent_id": parent,
         "subsystem_domain": domain, "segment": extra.pop("segment", "space"), "quantity": 1,
         "version": 1, "deleted_at": None, **extra}
    await db_create_element(d)
    er._elements[eid] = d
    return d


async def _seed(study_id: str) -> None:
    await _el(study_id, "mission", "Mission", "mission")
    await _el(study_id, "space", "Space Segment", "segment", "mission")
    await _el(study_id, "sc", "Spacecraft", "system", "space")
    await _el(study_id, "eps", "EPS", "subsystem", "sc", "power")
    await _el(study_id, "bat", "Battery", "component", "eps", "power", mass_kg=1.0, power_avg_w=0.5,
              performance_json={"capacity_wh": 40.0})
    await _el(study_id, "pcdu", "PCDU", "component", "eps", "power", mass_kg=0.5, power_avg_w=1.0)
    await _el(study_id, "aocs", "AOCS", "subsystem", "sc", "aocs", mass_kg=2.0, power_avg_w=3.0)
    await _el(study_id, "ground", "Ground Segment", "segment", "mission", segment="ground")
    await _el(study_id, "gs-sval", "Svalbard", "system", "ground", segment="ground", kb_component_id="svalbard")
    await _el(study_id, "gs-unknown", "Home antenna", "system", "ground", segment="ground", kb_component_id="nope")
    await _el(study_id, "ops", "Operations", "segment", "mission", segment="operations")
    await _el(study_id, "m-nom", "Nominal", "mode", "ops", segment="operations",
              description="guard: soc < 25 -> Safe")
    await _el(study_id, "m-safe", "Safe", "mode", "ops", segment="operations")


async def test_override_reaches_flat_and_is_sticky(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db.parameter_repo import upsert_element_parameter
    from spacecdf_server.services.analysis_context import build_context, seed_design_state
    from spacecdf_common.models.parameter import ParameterSource

    await _seed(study)
    ctx = await build_context(study)
    assert ctx.flat["power.eps_mass_kg"] == pytest.approx(1.5)       # leaves only (bat + pcdu)
    assert ctx.flat["aocs.mass_kg"] == pytest.approx(2.0)             # subsystem without children counts
    assert ctx.flat["power.battery_capacity_wh"] == 40.0
    assert ctx.flat["mass.dry_mass_kg"] == pytest.approx(3.5)
    assert ctx.overridden_paths == set()
    assert ctx.mission_root["id"] == "mission"

    # manual override on the battery mass -> EPS aggregate changes, path becomes sticky
    await upsert_element_parameter({"study_id": study, "element_id": "bat", "definition_name": "mass_kg",
                                    "manual_value": 3.0, "value_switch": "manual"})
    ctx = await build_context(study)
    assert ctx.params["bat"]["mass_kg"].provenance == "manual"
    assert ctx.flat["power.eps_mass_kg"] == pytest.approx(3.5)
    assert "power.eps_mass_kg" in ctx.overridden_paths
    assert "aocs.mass_kg" not in ctx.overridden_paths
    assert ctx.resolve("el:bat.mass_kg") == 3.0
    assert ctx.resolve("el:Battery.mass_kg") == 3.0
    assert ctx.resolve("el:AOCS.mass_kg") == 2.0                      # column fallback
    assert ctx.canonical_path("el:Battery.mass_kg") == "el:bat.mass_kg"
    assert ctx.resolve("power.eps_mass_kg") == pytest.approx(3.5)
    assert ctx.resolve("el:nobody.mass_kg") is None

    state = seed_design_state(ctx)
    assert state.get_param("power.eps_mass_kg").source == ParameterSource.POSITION_OVERRIDE
    assert state.get_param("aocs.mass_kg").source == ParameterSource.COMPUTED

    # a ref formula counts as an override too
    await upsert_element_parameter({"study_id": study, "element_id": "aocs", "definition_name": "power_avg_w",
                                    "formula": "mass_kg * 2", "formula_kind": "ref", "computed_value": 3.0})
    ctx = await build_context(study)
    assert ctx.flat["aocs.power_w"] == pytest.approx(4.0)
    assert "aocs.power_w" in ctx.overridden_paths


async def test_modes_from_mode_elements_and_rows(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db.models import ModeElementRow
    from spacecdf_server.routers import elements as er
    from spacecdf_server.services.analysis_context import build_context

    await _seed(study)
    # in-memory activation (router path) + a persisted row
    er._mode_elements.append({"mode_id": "m-nom", "element_id": "aocs", "is_active": True,
                              "power_w_in_mode": None, "duty_cycle_percent": 100.0})
    async with db_factory() as s:
        s.add(ModeElementRow(mode_id="m-nom", element_id="pcdu", is_active=True, power_w_in_mode=4.0,
                             duty_cycle_percent=50.0))
        s.add(ModeElementRow(mode_id="m-safe", element_id="pcdu", is_active=True, power_w_in_mode=None,
                             duty_cycle_percent=100.0))
        await s.commit()

    ctx = await build_context(study)
    modes = {m.name: m for m in ctx.modes}
    assert set(modes) == {"Nominal", "Safe"}
    assert modes["Nominal"].power_w == pytest.approx(3.0 + 4.0 * 0.5)
    assert sorted(modes["Nominal"].active_element_ids) == ["aocs", "pcdu"]
    assert modes["Nominal"].guards == [{"condition": "soc < 25", "target_mode": "Safe", "priority": 10}]
    assert modes["Safe"].power_w == pytest.approx(1.0)               # falls back to power_avg_w
    assert all(m.source == "element" for m in ctx.modes)


async def test_stations_from_kb_selection(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.analysis_context import build_context
    await _seed(study)
    ctx = await build_context(study)
    assert len(ctx.all_kb_stations) > 10
    assert [s["id"] for s in ctx.ground_stations] == ["svalbard"]
    assert ctx.ground_stations[0]["element_id"] == "gs-sval"
    assert ctx.ground_stations[0]["lat"] == pytest.approx(78.23)
    assert ctx.orbit["period_s"] > 5000 and 0 < ctx.orbit["eclipse_fraction"] < 0.5


async def test_context_hash_stable_and_sensitive(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db.parameter_repo import upsert_element_parameter
    from spacecdf_server.routers import elements as er
    from spacecdf_server.services.analysis_context import HASH_KEYS, build_context, context_hash

    await _seed(study)
    ctx1 = await build_context(study)
    h_all = context_hash(ctx1, list(HASH_KEYS))
    h_el = context_hash(ctx1, ["elements", "params"])
    ctx2 = await build_context(study)
    assert context_hash(ctx2, list(HASH_KEYS)) == h_all
    assert context_hash(ctx2, ["params", "elements"]) == h_el          # order-insensitive
    assert context_hash(ctx2, ["stations"]) != h_el

    await upsert_element_parameter({"study_id": study, "element_id": "bat", "definition_name": "mass_kg",
                                    "manual_value": 3.0, "value_switch": "manual"})
    ctx3 = await build_context(study)
    assert context_hash(ctx3, ["elements", "params"]) != h_el
    assert context_hash(ctx3, ["stations"]) == context_hash(ctx1, ["stations"])

    er._elements["gs-sval"]["kb_component_id"] = "kiruna"
    ctx4 = await build_context(study)
    assert context_hash(ctx4, ["stations"]) != context_hash(ctx1, ["stations"])

    with pytest.raises(KeyError):
        context_hash(ctx4, ["nope"])
