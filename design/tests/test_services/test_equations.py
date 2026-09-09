"""Equation engine tests (SCDF-160 §1.5 / §6): ref persists, calc doesn't,
children sum, el() cross-reference, cycle detection, whitelisted functions,
unit passthrough, recompute trigger."""
from __future__ import annotations

import pytest

from spacecdf_server.db import parameter_repo as pr
from spacecdf_server.db.models import BudgetAllocationRow, DesignElementRow
from spacecdf_server.services import equations as eq


@pytest.fixture()
async def tree(db_factory, study):
    """Spacecraft -> {EPS(mass 4), AOCS(mass 6)}; well-known columns mirrored to rows."""
    async with db_factory() as s:
        s.add(DesignElementRow(id="sc", study_id=study, name="Spacecraft", element_type="system", mass_kg=None))
        s.add(DesignElementRow(id="eps", study_id=study, name="EPS", element_type="subsystem", parent_id="sc",
                               subsystem_domain="eps", mass_kg=4.0, power_avg_w=10.0))
        s.add(DesignElementRow(id="aocs", study_id=study, name="AOCS", element_type="subsystem", parent_id="sc",
                               subsystem_domain="aocs", mass_kg=6.0, power_avg_w=5.0))
        s.add(BudgetAllocationRow(study_id=study, element_id="sc", budget_type="mass", allocation_value=12.0))
        await s.commit()
    for eid, m, p in (("eps", 4.0, 10.0), ("aocs", 6.0, 5.0)):
        await pr.mirror_well_known_columns({"id": eid, "study_id": study, "mass_kg": m, "power_avg_w": p})
    await pr.upsert_parameter_definition({"name": "mass_kg", "unit": "kg", "quantity_kind": "mass", "is_well_known": True})
    await pr.upsert_parameter_definition({"name": "mass_margin_kg", "unit": "kg", "quantity_kind": "mass"})
    return study


async def _put(study, eid, name, formula=None, kind="ref", **extra):
    return await pr.upsert_element_parameter({
        "study_id": study, "element_id": eid, "definition_name": name,
        "formula": formula, "formula_kind": kind if formula else None, **extra,
    })


def _param(res, eid, name):
    return next(p for p in res["parameters"] if p["element_id"] == eid and p["name"] == name)


async def _row(eid, name):
    defn = await pr.get_parameter_definition_by_name(name)
    rows = await pr.list_element_parameters_by_element(eid)
    return next(r for r in rows if r["definition_id"] == defn["id"])


class TestParsing:
    def test_dependency_scan(self):
        p = eq.parse_dependencies('mass_kg * 1.2 + el("EPS").power_avg_w + children("mass_kg") + budget("mass")')
        assert p.bare_names == {"mass_kg"}
        assert p.element_refs == {("EPS", "power_avg_w")}
        assert p.children_params == {"mass_kg"} and p.budget_types == {"mass"}
        assert p.errors == []

    def test_rejects_non_whitelisted(self):
        assert any("not allowed" in e for e in eq.parse_dependencies("__import__('os').system('x')").errors)
        assert any("not allowed" in e for e in eq.parse_dependencies("open('f')").errors)
        assert any("not allowed" in e for e in eq.parse_dependencies("[x for x in y]").errors)
        assert any("syntax" in e for e in eq.parse_dependencies("1 +").errors)
        assert eq.parse_dependencies("sqrt(pow(mass_kg, 2)) + log10(10) + min(1, 2) + abs(-1) + atan2(1, 1)").errors == []


class TestEvaluation:
    async def test_children_sum_with_ref_persists(self, tree):
        await _put(tree, "sc", "mass_kg", 'children("mass_kg")', "ref")
        res = await eq.recompute_study(tree)
        p = _param(res, "sc", "mass_kg")
        assert p["effective_value"] == 10.0 and p["computed_value"] == 10.0 and p["errors"] == []
        assert p["unit"] == "kg" and p["quantity_kind"] == "mass" and p["provenance"] == "formula"
        assert res["persisted"] == 1
        row = await _row("sc", "mass_kg")
        assert row["computed_value"] == 10.0
        # well-known + ref formula -> written back to the element column
        async with pr.get_session_factory()() as s:
            assert (await s.get(DesignElementRow, "sc")).mass_kg == 10.0
        assert res["written_back"] == 1

    async def test_calc_evaluates_on_read_only(self, tree):
        await _put(tree, "sc", "mass_margin_kg", 'budget("mass") - children("mass_kg")', "calc")
        res = await eq.recompute_study(tree)
        assert _param(res, "sc", "mass_margin_kg")["effective_value"] == 2.0
        assert res["persisted"] == 0
        assert (await _row("sc", "mass_margin_kg"))["computed_value"] is None
        # evaluate_study never persists either, but still shows the value
        res2 = await eq.evaluate_study(tree)
        assert _param(res2, "sc", "mass_margin_kg")["effective_value"] == 2.0
        assert _param(res2, "sc", "mass_margin_kg")["computed_value"] == 2.0

    async def test_el_cross_reference_by_name_and_id(self, tree):
        await _put(tree, "aocs", "mass_margin_kg", 'el("EPS").mass_kg * 0.5 + el("eps").power_avg_w', "ref")
        res = await eq.recompute_study(tree)
        assert _param(res, "aocs", "mass_margin_kg")["effective_value"] == 12.0
        # unknown element -> error, no raise
        await _put(tree, "aocs", "mass_margin_kg", 'el("Nope").mass_kg', "ref")
        res = await eq.recompute_study(tree)
        p = _param(res, "aocs", "mass_margin_kg")
        assert p["effective_value"] == 12.0 and any("Nope" in e for e in p["errors"])  # keeps last good value
        assert res["errors"] and res["errors"][0]["element_id"] == "aocs"

    async def test_chain_uses_effective_values_and_manual_override(self, tree):
        await _put(tree, "sc", "mass_kg", 'children("mass_kg")', "ref")
        await _put(tree, "sc", "mass_margin_kg", 'budget("mass") - mass_kg', "calc")
        res = await eq.recompute_study(tree)
        assert _param(res, "sc", "mass_margin_kg")["effective_value"] == 2.0
        # manual override on EPS mass propagates through the chain
        await _put(tree, "eps", "mass_kg", None, manual_value=1.0, value_switch="manual")
        res = await eq.recompute_study(tree)
        assert _param(res, "eps", "mass_kg")["effective_value"] == 1.0
        assert _param(res, "eps", "mass_kg")["provenance"] == "manual"
        assert _param(res, "sc", "mass_kg")["effective_value"] == 7.0
        assert _param(res, "sc", "mass_margin_kg")["effective_value"] == 5.0
        async with pr.get_session_factory()() as s:
            assert (await s.get(DesignElementRow, "eps")).mass_kg == 1.0

    async def test_cycle_detection(self, tree):
        await _put(tree, "eps", "mass_margin_kg", 'el("AOCS").mass_margin_kg + 1', "ref")
        await _put(tree, "aocs", "mass_margin_kg", 'el("EPS").mass_margin_kg + 1', "ref")
        await _put(tree, "sc", "mass_margin_kg", "2 + 2", "ref")
        res = await eq.recompute_study(tree)
        assert len(res["cycles"]) == 1
        cyc = {(n["element_id"], n["name"]) for n in res["cycles"][0]}
        assert cyc == {("eps", "mass_margin_kg"), ("aocs", "mass_margin_kg")}
        for eid in ("eps", "aocs"):
            p = _param(res, eid, "mass_margin_kg")
            assert p["effective_value"] is None and any("circular" in e for e in p["errors"])
        assert _param(res, "sc", "mass_margin_kg")["effective_value"] == 4.0  # unaffected node still evaluates
        graph = await eq.dependency_graph(tree)
        assert graph["cycles"] and len(graph["edges"]) == 2
        assert {n["id"] for n in graph["nodes"]} == {"eps:mass_margin_kg", "aocs:mass_margin_kg", "sc:mass_margin_kg"}

    async def test_whitelisted_functions_only_at_runtime(self, tree):
        await _put(tree, "sc", "mass_margin_kg", "sqrt(16) + max(1, 2) + log10(100)", "ref")
        res = await eq.recompute_study(tree)
        assert _param(res, "sc", "mass_margin_kg")["effective_value"] == 8.0
        await _put(tree, "sc", "mass_margin_kg", "__import__('os').getcwd()", "ref")
        res = await eq.recompute_study(tree)
        p = _param(res, "sc", "mass_margin_kg")
        assert p["errors"] and p["effective_value"] == 8.0  # last persisted value kept
        await _put(tree, "sc", "mass_margin_kg", "1 / 0", "ref")
        res = await eq.recompute_study(tree)
        assert any("ZeroDivision" in e for e in _param(res, "sc", "mass_margin_kg")["errors"])

    async def test_bare_name_and_missing_param(self, tree):
        await _put(tree, "eps", "mass_margin_kg", "mass_kg * 2 + power_avg_w", "calc")
        res = await eq.evaluate_study(tree)
        assert _param(res, "eps", "mass_margin_kg")["effective_value"] == 18.0
        await _put(tree, "eps", "mass_margin_kg", "unknown_param + 1", "calc")
        res = await eq.evaluate_study(tree)
        p = _param(res, "eps", "mass_margin_kg")
        assert p["effective_value"] is None and any("unknown_param" in e for e in p["errors"])

    async def test_on_change_recomputes_and_evaluate_element(self, tree):
        await _put(tree, "sc", "mass_kg", 'children("mass_kg")', "ref")
        await eq.on_change(tree, ["eps"])
        assert (await _row("sc", "mass_kg"))["computed_value"] == 10.0
        async with pr.get_session_factory()() as s:
            row = await s.get(DesignElementRow, "aocs")
            row.mass_kg = 9.0
            await s.commit()
        await pr.mirror_well_known_columns({"id": "aocs", "study_id": tree, "mass_kg": 9.0})
        await eq.on_change(tree, ["aocs"])
        assert (await _row("sc", "mass_kg"))["computed_value"] == 13.0
        el = await eq.evaluate_element("sc")
        assert {p["name"] for p in el["parameters"]} == {"mass_kg"}
        assert el["parameters"][0]["effective_value"] == 13.0
        assert (await eq.evaluate_element("ghost"))["parameters"] == []
        await eq.on_change(None, [])  # no-op, never raises

    async def test_provenance_column_and_agent(self, tree):
        await pr.upsert_parameter_definition({"name": "data_rate_bps", "unit": "bps"})
        await _put(tree, "eps", "data_rate_bps", None, computed_value=1500.0)
        res = await eq.evaluate_study(tree)
        assert _param(res, "eps", "mass_kg")["provenance"] == "column"
        assert _param(res, "eps", "mass_kg")["effective_value"] == 4.0
        assert _param(res, "eps", "data_rate_bps")["provenance"] == "agent"
        assert _param(res, "eps", "data_rate_bps")["unit"] == "bps"
