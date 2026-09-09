"""Option repo (SCDF-172): lazy baseline, branch copies overrides, option rows
shadow baseline rows on read, writes never touch the baseline, soft delete."""
from __future__ import annotations

import pytest

from spacecdf_server.db import option_repo as orepo, parameter_repo as pr
from spacecdf_server.db.models import DesignElementRow
from spacecdf_server.services import equations


@pytest.fixture()
async def tree(db_factory, study):
    async with db_factory() as s:
        s.add(DesignElementRow(id="sc", study_id=study, name="Spacecraft", element_type="system"))
        s.add(DesignElementRow(id="bat", study_id=study, name="Battery", element_type="component",
                               parent_id="sc", subsystem_domain="eps", mass_kg=2.0, power_avg_w=1.0))
        s.add(DesignElementRow(id="rw", study_id=study, name="Wheel", element_type="component",
                               parent_id="sc", subsystem_domain="aocs", mass_kg=0.5, power_avg_w=2.0))
        await s.commit()
    for eid in ("bat", "rw"):
        await pr.mirror_well_known_columns({"id": eid, "study_id": study, "mass_kg": 2.0 if eid == "bat" else 0.5,
                                            "power_avg_w": 1.0 if eid == "bat" else 2.0})
    await pr.upsert_element_parameter({"study_id": study, "element_id": "sc", "definition_name": "mass_kg",
                                       "formula": 'children("mass_kg")', "formula_kind": "ref"})
    return study


def _eff(res: dict, eid: str, name: str):
    return next(p for p in res["parameters"] if p["element_id"] == eid and p["name"] == name)


class TestBaseline:
    async def test_baseline_created_lazily_once(self, study):
        b1 = await orepo.ensure_baseline(study)
        b2 = await orepo.ensure_baseline(study)
        assert b1["id"] == b2["id"] and b1["is_baseline"] and b1["name"] == "Baseline"
        opts = await orepo.list_options(study)
        assert [o["id"] for o in opts] == [b1["id"]]
        assert await orepo.resolve_option_id(b1["id"]) is None
        assert await orepo.resolve_option_id(None) is None
        with pytest.raises(ValueError):
            await orepo.resolve_option_id("opt-ghost")
        assert not await orepo.soft_delete_option(b1["id"])   # baseline cannot go
        upd = await orepo.update_option(b1["id"], {"name": "Renamed", "description": "d"})
        assert upd["name"] == "Baseline" and upd["description"] == "d"

    async def test_create_list_update_delete(self, study):
        a = await orepo.create_option(study, "Option A", "bigger battery")
        assert not a["is_baseline"] and a["study_id"] == study
        with pytest.raises(ValueError):
            await orepo.create_option(study, "   ")
        opts = await orepo.list_options(study)
        assert opts[0]["is_baseline"] and opts[1]["id"] == a["id"]
        assert (await orepo.update_option(a["id"], {"name": "A2"}))["name"] == "A2"
        assert await orepo.soft_delete_option(a["id"])
        assert await orepo.get_option(a["id"]) is None
        assert [o["id"] for o in await orepo.list_options(study)] == [opts[0]["id"]]


class TestShadowing:
    async def test_option_row_shadows_baseline_on_read_only(self, tree):
        study = tree
        a = await orepo.create_option(study, "A")
        base = await pr.upsert_element_parameter({"study_id": study, "element_id": "bat",
                                                  "definition_name": "mass_kg", "manual_value": 2.0,
                                                  "value_switch": "manual"})
        over = await pr.upsert_element_parameter({"study_id": study, "element_id": "bat",
                                                  "definition_name": "mass_kg", "manual_value": 3.5,
                                                  "value_switch": "manual", "option_id": a["id"]})
        assert over["id"] != base["id"] and over["option_id"] == a["id"]
        # baseline untouched
        assert (await pr.get_element_parameter(base["id"]))["manual_value"] == 2.0
        assert (await pr.get_element_parameter(base["id"]))["option_id"] is None
        # second write into the option updates the same option row
        over2 = await pr.upsert_element_parameter({"study_id": study, "element_id": "bat",
                                                   "definition_name": "mass_kg", "manual_value": 4.0,
                                                   "option_id": a["id"]})
        assert over2["id"] == over["id"] and over2["manual_value"] == 4.0
        # reads: baseline vs option
        base_rows = await pr.list_element_parameters_by_element("bat", iteration=1)
        assert [r["id"] for r in base_rows if r["definition_id"] == base["definition_id"]] == [base["id"]]
        opt_rows = await pr.list_element_parameters_by_element("bat", iteration=1, option_id=a["id"])
        assert [r["id"] for r in opt_rows if r["definition_id"] == base["definition_id"]] == [over["id"]]
        assert {r["definition_id"] for r in opt_rows} == {r["definition_id"] for r in base_rows}  # union
        by_study = await pr.list_element_parameters_by_study(study, option_id=a["id"])
        assert over["id"] in {r["id"] for r in by_study} and base["id"] not in {r["id"] for r in by_study}
        assert over["id"] not in {r["id"] for r in await pr.list_element_parameters_by_study(study)}
        assert [r["id"] for r in await orepo.list_option_overrides(study, a["id"])] == [over["id"]]
        assert await orepo.list_option_overrides(study, (await orepo.ensure_baseline(study))["id"]) == []
        # well-known mirror stays baseline-only
        assert (await pr.effective_well_known_values("bat"))["mass_kg"] == 2.0

    async def test_equations_evaluate_option_and_baseline_formula_sees_override(self, tree):
        study = tree
        a = await orepo.create_option(study, "A")
        await pr.upsert_element_parameter({"study_id": study, "element_id": "bat", "definition_name": "mass_kg",
                                           "manual_value": 5.0, "value_switch": "manual", "option_id": a["id"]})
        base = await equations.evaluate_study(study)
        opt = await equations.evaluate_study(study, option_id=a["id"])
        assert base["option_id"] is None and opt["option_id"] == a["id"]
        assert _eff(base, "bat", "mass_kg")["effective_value"] == 2.0
        assert _eff(base, "sc", "mass_kg")["effective_value"] == 2.5
        assert _eff(opt, "bat", "mass_kg")["effective_value"] == 5.0
        assert _eff(opt, "bat", "mass_kg")["option_id"] == a["id"]
        assert _eff(opt, "sc", "mass_kg")["effective_value"] == 5.5     # baseline ref formula, option value
        assert _eff(opt, "sc", "mass_kg")["option_id"] is None
        # recompute under the option persists nothing into baseline rows / columns
        res = await equations.recompute_study(study, option_id=a["id"])
        assert res["written_back"] == 0
        assert _eff(await equations.evaluate_study(study), "sc", "mass_kg")["computed_value"] in (None, 2.5)
        assert (await pr.effective_well_known_values("bat"))["mass_kg"] == 2.0

    async def test_soft_delete_removes_overrides(self, tree):
        study = tree
        a = await orepo.create_option(study, "A")
        await pr.upsert_element_parameter({"study_id": study, "element_id": "rw", "definition_name": "mass_kg",
                                           "manual_value": 9.0, "value_switch": "manual", "option_id": a["id"]})
        assert await orepo.soft_delete_option(a["id"])
        assert await orepo.list_option_overrides(study, a["id"]) == []
        assert all(r.get("option_id") != a["id"] for r in (await pr.load_all_element_parameters(study)).values())


class TestBranch:
    async def test_branch_from_baseline_copies_nothing(self, tree):
        study = tree
        b = await orepo.ensure_baseline(study)
        new = await orepo.branch_option(study, b["id"], "From baseline")
        assert new["copied"] == 0 and new["branched_from_option_id"] == b["id"]
        assert await orepo.list_option_overrides(study, new["id"]) == []
        new2 = await orepo.branch_option(study, None, "From nothing")
        assert new2["copied"] == 0 and new2["branched_from_option_id"] is None

    async def test_branch_copies_overrides_as_new_rows(self, tree):
        study = tree
        a = await orepo.create_option(study, "A")
        src = await pr.upsert_element_parameter({"study_id": study, "element_id": "bat", "definition_name": "mass_kg",
                                                 "manual_value": 3.0, "value_switch": "manual", "option_id": a["id"]})
        await pr.upsert_element_parameter({"study_id": study, "element_id": "rw", "definition_name": "power_avg_w",
                                           "formula": "mass_kg * 10", "formula_kind": "calc", "option_id": a["id"]})
        b = await orepo.branch_option(study, a["id"], "B", "forked")
        assert b["copied"] == 2 and b["branched_from_option_id"] == a["id"] and b["description"] == "forked"
        rows = await orepo.list_option_overrides(study, b["id"])
        assert len(rows) == 2 and all(r["option_id"] == b["id"] for r in rows)
        assert {r["id"] for r in rows}.isdisjoint({src["id"]})
        copy = next(r for r in rows if r["element_id"] == "bat")
        assert copy["manual_value"] == 3.0 and copy["value_switch"] == "manual"
        # diverge B; A keeps its value
        await pr.upsert_element_parameter({"study_id": study, "element_id": "bat", "definition_name": "mass_kg",
                                           "manual_value": 7.0, "option_id": b["id"]})
        ev_a = await equations.evaluate_study(study, option_id=a["id"])
        ev_b = await equations.evaluate_study(study, option_id=b["id"])
        assert _eff(ev_a, "bat", "mass_kg")["effective_value"] == 3.0
        assert _eff(ev_b, "bat", "mass_kg")["effective_value"] == 7.0
        assert _eff(ev_b, "rw", "power_avg_w")["effective_value"] == 5.0
