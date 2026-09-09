"""Repo tests for parameter definitions + element parameters, seed and mirroring (SCDF-160 §1.5)."""
from __future__ import annotations

import pytest

from spacecdf_common.models.parameters import WELL_KNOWN_PARAMETERS
from spacecdf_server.db import element_repo, parameter_repo as pr
from spacecdf_server.db.models import DesignElementRow


@pytest.fixture()
async def element(db_factory, study):
    async with db_factory() as s:
        s.add(DesignElementRow(id="el-1", study_id=study, name="Battery", element_type="component",
                               subsystem_domain="eps", mass_kg=2.5, power_avg_w=1.0))
        await s.commit()
    return "el-1"


class TestDefinitions:
    async def test_upsert_by_name(self, db_factory):
        a = await pr.upsert_parameter_definition({"name": "data_rate_bps", "quantity_kind": "data_rate", "unit": "bps"})
        b = await pr.upsert_parameter_definition({"name": "data_rate_bps", "description": "Downlink rate"})
        assert a["id"] == b["id"] == "pd-data_rate_bps"
        assert b["unit"] == "bps" and b["description"] == "Downlink rate"
        assert (await pr.get_parameter_definition_by_name("data_rate_bps"))["id"] == a["id"]
        assert (await pr.get_parameter_definition(a["id"]))["name"] == "data_rate_bps"
        assert await pr.get_parameter_definition_by_name("nope") is None
        with pytest.raises(ValueError):
            await pr.upsert_parameter_definition({"unit": "kg"})

    async def test_seed_from_reference_library(self, db_factory):
        lib = pr.load_reference_data_library()
        kinds = {q["name"]: q["unit"] for q in lib["quantity_kinds"]}
        for name, unit in {"mass": "kg", "power": "W", "energy": "Wh", "voltage": "V", "current": "A",
                           "data_rate": "bps", "data_volume": "bit", "length": "m", "volume": "cm3",
                           "area": "m2", "temperature": "K", "frequency": "Hz", "delta_v": "m/s",
                           "cost": "kEUR", "time": "s", "angle": "deg", "ratio": "-"}.items():
            assert kinds[name] == unit
        counts = await pr.seed_parameter_definitions()
        assert counts["created"] == len(lib["parameter_definitions"]) and counts["updated"] == 0
        again = await pr.seed_parameter_definitions()
        assert again["created"] == 0 and again["updated"] == counts["created"]
        wk = await pr.list_parameter_definitions(well_known_only=True)
        assert {d["name"] for d in wk} == set(WELL_KNOWN_PARAMETERS)
        assert all(d["is_well_known"] for d in wk)
        mass = await pr.get_parameter_definition_by_name("mass_kg")
        assert mass["unit"] == "kg" and mass["quantity_kind"] == "mass"
        assert len(await pr.load_all_parameter_definitions()) == counts["created"]

    async def test_well_known_names_match_element_columns(self):
        cols = {c.key for c in DesignElementRow.__table__.columns}
        assert set(WELL_KNOWN_PARAMETERS) <= cols

    async def test_seed_is_non_fatal(self, db_factory, tmp_path):
        assert await pr.seed_parameter_definitions(tmp_path / "missing.json") == {"created": 0, "updated": 0}


class TestElementParameters:
    async def test_upsert_keyed_on_element_definition_iteration(self, study, element):
        p1 = await pr.upsert_element_parameter({"study_id": study, "element_id": element,
                                                "definition_name": "energy_wh", "manual_value": 40.0,
                                                "value_switch": "manual"})
        assert p1["definition_id"] == "pd-energy_wh" and p1["version"] == 1
        p2 = await pr.upsert_element_parameter({"study_id": study, "element_id": element,
                                                "definition_id": "pd-energy_wh", "manual_value": 45.0})
        assert p2["id"] == p1["id"] and p2["manual_value"] == 45.0 and p2["version"] == 2
        assert p2["value_switch"] == "manual"
        p3 = await pr.upsert_element_parameter({"study_id": study, "element_id": element,
                                                "definition_id": "pd-energy_wh", "iteration": 2,
                                                "computed_value": 1.0})
        assert p3["id"] != p1["id"]
        assert len(await pr.list_element_parameters_by_element(element)) == 2
        assert len(await pr.list_element_parameters_by_element(element, iteration=2)) == 1
        assert len(await pr.list_element_parameters_by_study(study)) == 2
        assert len(await pr.load_all_element_parameters(study)) == 2

    async def test_validation(self, study, element):
        with pytest.raises(ValueError, match="value_switch"):
            await pr.upsert_element_parameter({"study_id": study, "element_id": element,
                                               "definition_name": "x", "value_switch": "guess"})
        with pytest.raises(ValueError, match="formula_kind"):
            await pr.upsert_element_parameter({"study_id": study, "element_id": element,
                                               "definition_name": "x", "formula_kind": "magic"})
        with pytest.raises(ValueError, match="required"):
            await pr.upsert_element_parameter({"study_id": study, "element_id": element})

    async def test_update_and_soft_delete(self, study, element):
        p = await pr.upsert_element_parameter({"study_id": study, "element_id": element,
                                               "definition_name": "area_m2", "computed_value": 0.1})
        u = await pr.update_element_parameter(p["id"], {"formula": "children('area_m2')",
                                                        "formula_kind": "ref", "element_id": "hack"},
                                              expected_version=1)
        assert u["formula_kind"] == "ref" and u["element_id"] == element and u["version"] == 2
        with pytest.raises(ValueError, match="Version conflict"):
            await pr.update_element_parameter(p["id"], {"formula": ""}, expected_version=1)
        assert await pr.soft_delete_element_parameter(p["id"])
        assert await pr.get_element_parameter(p["id"]) is None
        with pytest.raises(ValueError, match="not found"):
            await pr.update_element_parameter(p["id"], {"formula": ""})
        # upsert revives the soft-deleted row rather than violating the unique key
        r = await pr.upsert_element_parameter({"study_id": study, "element_id": element,
                                               "definition_id": p["definition_id"], "computed_value": 0.2})
        assert r["id"] == p["id"] and r["deleted_at"] is None


class TestMirroring:
    async def test_mirror_creates_and_updates_only_changed(self, study, element):
        el = {"id": element, "study_id": study, "subsystem_domain": "eps", "mass_kg": 2.5,
              "power_avg_w": 1.0, "volume_cm3": None}
        assert await pr.mirror_well_known_columns(el) == 2
        rows = {r["definition_id"]: r for r in await pr.list_element_parameters_by_element(element)}
        assert set(rows) == {"pd-mass_kg", "pd-power_avg_w"}
        assert rows["pd-mass_kg"]["computed_value"] == 2.5
        assert rows["pd-mass_kg"]["value_switch"] == "computed"
        assert rows["pd-mass_kg"]["owner_domain"] == "eps"
        assert (await pr.get_parameter_definition_by_name("mass_kg"))["is_well_known"] is True
        # unchanged -> nothing touched; changed -> one row
        assert await pr.mirror_well_known_columns(el) == 0
        el["mass_kg"] = 3.0
        assert await pr.mirror_well_known_columns(el) == 1
        rows = {r["definition_id"]: r for r in await pr.list_element_parameters_by_element(element)}
        assert rows["pd-mass_kg"]["computed_value"] == 3.0 and rows["pd-mass_kg"]["version"] == 2

    async def test_mirror_keeps_manual_switch(self, study, element):
        await pr.upsert_element_parameter({"study_id": study, "element_id": element,
                                           "definition_name": "mass_kg", "manual_value": 9.0,
                                           "value_switch": "manual"})
        await pr.mirror_well_known_columns({"id": element, "study_id": study, "mass_kg": 2.5})
        vals = await pr.effective_well_known_values(element)
        assert vals["mass_kg"] == 9.0
        rows = await pr.list_element_parameters_by_element(element)
        assert rows[0]["computed_value"] == 2.5 and rows[0]["manual_value"] == 9.0

    async def test_mirror_non_fatal_and_noop(self, study):
        assert await pr.mirror_well_known_columns({"id": "x"}) == 0
        assert await pr.mirror_well_known_columns({"id": "x", "study_id": study}) == 0
        # element FK does not exist -> SQLite without FK enforcement accepts, but even if it
        # raised, the function must return 0 rather than propagate
        assert isinstance(await pr.mirror_well_known_columns({"id": "ghost", "study_id": study, "mass_kg": 1.0}), int)

    async def test_element_repo_write_through(self, study):
        el = {"id": "el-9", "study_id": study, "name": "Radio", "element_type": "component",
              "subsystem_domain": "ttc", "mass_kg": 0.5, "power_peak_w": 4.0, "performance": {"g": 1}}
        await element_repo.db_create_element(el)
        rows = {r["definition_id"]: r["computed_value"] for r in await pr.list_element_parameters_by_element("el-9")}
        assert rows == {"pd-mass_kg": 0.5, "pd-power_peak_w": 4.0}
        el["mass_kg"] = 0.6
        el["cost_recurring_keur"] = 12.0
        await element_repo.db_update_element("el-9", el)
        rows = {r["definition_id"]: r["computed_value"] for r in await pr.list_element_parameters_by_element("el-9")}
        assert rows == {"pd-mass_kg": 0.6, "pd-power_peak_w": 4.0, "pd-cost_recurring_keur": 12.0}
        vals = await pr.effective_well_known_values("el-9")
        assert vals == {"mass_kg": 0.6, "power_peak_w": 4.0, "cost_recurring_keur": 12.0}
