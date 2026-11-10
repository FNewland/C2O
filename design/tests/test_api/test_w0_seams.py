"""W0 seams: the split export router, the shared study collector and the one roll-up.

* W0.1: every export route of the single-file router is still served, by the family module named
  in design/docs/dev/W0_SEAMS.md, with the same operation id (so /openapi.json is unchanged);
  the docx registry and the docx_generator shim keep their names.
* W0.2: ``export_context.collect`` returns every section, empty on an empty study, stubs marked.
* W0.3: ``rollup`` counts leaves only (no double counting of product-tree nodes), applies the
  maturity and gate margins, and the exports quote its mass and form factor.
"""
from __future__ import annotations

import pytest

from tests.test_api.conftest import make_element
from tests.test_api.diagram_seed import seed_eosat

# (method, path, endpoint function, family module) of the routes before the split
EXPORT_ROUTES = [
    ("POST", "/api/exports/smo/{study_id}", "export_smo_config", "smo"),
    ("GET", "/api/exports/smo/{study_id}/validate", "validate_smo_export", "smo"),
    ("POST", "/api/exports/docs/{study_id}", "export_design_document", "packs"),
    ("POST", "/api/exports/fsw/{study_id}", "export_fsw_architecture", "fsw"),
    ("POST", "/api/exports/mbse/{study_id}", "export_mbse", "mbse"),
    ("POST", "/api/exports/docx/{doc_type}", "generate_docx", "docx"),
    ("POST", "/api/exports/launch-icd/{study_id}", "export_launch_icd", "launch_icd"),
    ("POST", "/api/exports/rsssa/{study_id}", "export_rsssa", "rsssa"),
    ("POST", "/api/exports/deorbit/{study_id}", "export_deorbit", "deorbit"),
    ("POST", "/api/exports/thermal-report/{study_id}", "export_thermal_report", "thermal"),
    ("POST", "/api/exports/test-plan/{study_id}", "export_test_plan", "test_plan"),
    ("POST", "/api/exports/worksheet/{template_id}", "generate_worksheet", "worksheet"),
]


# ───────────────────────────────────────────────────────────── W0.1 split

def test_export_routes_are_served_by_their_family_module_in_the_original_order():
    from spacecdf_server.app import app
    from spacecdf_server.routers import exports
    seen = [(m, "/api/exports" + r.path, r.endpoint) for fam in exports.FAMILIES for r in fam.router.routes
            for m in sorted(r.methods) if not r.path.startswith("/regulatory/")]   # W5.04 routes appended
    by_key = {(m, p): ep for m, p, ep in seen}
    for method, path, fn, family in EXPORT_ROUTES:
        ep = by_key.get((method, path))
        assert ep is not None, f"{method} {path} missing"
        assert ep.__name__ == fn
        assert ep.__module__ == f"spacecdf_server.routers.exports.{family}"
    assert [(m, p) for m, p, _ in seen] == [(r[0], r[1]) for r in EXPORT_ROUTES]
    # and the app serves them in that order (openapi paths keep registration order)
    paths = [p for p in app.openapi()["paths"] if p.startswith("/api/exports/")
             and not p.startswith("/api/exports/regulatory/")]
    assert paths == list(dict.fromkeys(r[1] for r in EXPORT_ROUTES))


def test_openapi_operation_ids_of_exports_unchanged(client):
    from spacecdf_server.app import app
    ops = {(m.upper(), p): o["operationId"] for p, item in app.openapi()["paths"].items()
           if p.startswith("/api/exports/") for m, o in item.items()}
    for method, path, fn, _ in EXPORT_ROUTES:
        assert ops[(method, path)].startswith(fn + "_api_exports_")


def test_backwards_compatible_names():
    from spacecdf_server.routers import compliance, exports, lifecycle
    from spacecdf_server.services import docx_generator
    from spacecdf_server.services.docx import DOCX_GENERATORS
    assert compliance._run_design_for_study is exports._run_design_for_study is lifecycle._run_design_for_study
    assert list(DOCX_GENERATORS) == ["mrd", "conops", "vp", "ts", "ird", "semp", "rmp", "testplan", "itu_api",
                                     "iaru", "rsssa", "export", "copuos", "eol", "srr", "pdr", "cdr"]
    assert docx_generator.DOCX_GENERATORS is DOCX_GENERATORS
    assert docx_generator.generate_did_docx.__module__ == "spacecdf_server.services.docx.did"
    # W5.04 filled the regulatory seam: its routes are all under /regulatory/
    assert exports.regulatory.router.routes and all(r.path.startswith("/regulatory/")
                                                    for r in exports.regulatory.router.routes)


# ───────────────────────────────────────────────────────────── W0.3 roll-up (pure)

def _el(eid, etype, parent=None, mass=None, power=None, qty=1, **kw):
    return {"id": eid, "element_type": etype, "parent_id": parent, "mass_kg": mass, "power_avg_w": power,
            "quantity": qty, "name": eid, **kw}


def test_rollup_counts_leaves_only_and_applies_margins():
    from spacecdf_server.services.rollup import rollup_elements
    els = [
        _el("m", "mission"), _el("seg", "segment", "m", segment="space"),
        _el("sc", "system", "seg", mass=9.0),                          # system estimate: superseded below
        _el("eps", "subsystem", "sc", mass=2.0, power=5.0),             # subsystem estimate: superseded
        _el("bat", "component", "eps", mass=0.25, power=0.3, performance={"maturity_category": "A"}),
        _el("wing", "component", "eps", mass=0.25, qty=2, performance={"maturity_category": "C"}),
        _el("pl", "subsystem", "sc", mass=0.5, power=3.0, performance={"maturity_category": "D"}),  # leaf estimate
        _el("gseg", "segment", "m", segment="ground"),
        _el("gs", "system", "gseg", mass=50.0, power=100.0, segment="ground"),   # ground: excluded
        _el("gone", "component", "eps", mass=7.0, deleted_at="2026-01-01"),      # deleted: excluded
    ]
    ru = rollup_elements(els, gate="pdr", orbit_average_w=4.0, orbit_average_source="test")
    assert ru.mass.cbe_kg == pytest.approx(0.25 + 0.5 + 0.5)
    assert ru.mass.with_maturity_kg == pytest.approx(0.25 * 1.05 + 0.5 * 1.10 + 0.5 * 1.20, abs=1e-3)
    assert ru.mass.system_margin_percent == 15.0                      # PDR on the ladder
    assert ru.mass.with_system_margin_kg == pytest.approx(ru.mass.with_maturity_kg * 1.15, abs=1e-3)
    assert ru.mass.ladder["mdr"] == pytest.approx(ru.mass.with_maturity_kg * 1.20, abs=1e-3)
    assert ru.mass.ladder["cdr"] == pytest.approx(ru.mass.with_maturity_kg * 1.10, abs=1e-3)
    assert ru.power.sum_on_power_w == pytest.approx(0.3 + 3.0)
    assert ru.power.orbit_average_with_margin_w == pytest.approx(4.0 * 1.15)
    assert ru.form_factor_source == "mass_estimate" and ru.form_factor == "1U"
    d = ru.as_dict()
    assert set(d) >= {"mass", "power", "form_factor", "form_factor_source", "warnings"}


def test_rollup_form_factor_from_the_structure_and_empty_design():
    from spacecdf_server.services.rollup import rollup_elements
    els = [_el("sc", "system"), _el("st", "component", "sc", mass=0.3, kb_component_id="struct-isis-3u",
                                     subsystem_domain="structure")]
    ru = rollup_elements(els)
    assert ru.form_factor == "3U" and ru.form_factor_source == "kb:struct-isis-3u"
    assert ru.mass.limit_kg is not None and ru.mass.limit_source == "cds:3U"
    empty = rollup_elements([])
    assert empty.mass.cbe_kg == 0 and empty.form_factor is None and empty.form_factor_source == "unknown"
    assert empty.power.orbit_average_w is None


# ───────────────────────────────────────────────────────────── W0.2 collector

async def test_collect_on_an_empty_study_returns_every_section(client, study_obj):
    from spacecdf_server.services.export_context import SECTIONS, StudyExport, collect
    sx = await collect(study_obj.id)
    assert isinstance(sx, StudyExport)
    d = sx.as_dict()
    assert set(SECTIONS) <= set(d) and sx.errors == {}
    assert sx.requirements["items"] == [] and sx.risks["items"] == [] and sx.elements["items"] == []
    assert sx.rollup["mass"]["cbe_kg"] == 0
    for stub in ("data_budget", "contacts", "licensing", "ait", "schedule"):
        # a stub names its owner; an implemented section answers with its empty or proposed shape
        assert d[stub].get("status") != "not_implemented" or d[stub]["owner"] in {"H", "L", "A"}
    assert d["ait"]["status"] == d["schedule"]["status"] == "proposed"     # W8a / W11a defaults
    assert d["licensing"]["owner"] == "L" and d["licensing"]["filings"]     # W5.06: no longer a stub
    assert "closure" in d["data_budget"]["daily"] and isinstance(d["contacts"]["stations"], list)   # W3.02 / W4.05 (H)
    r = await client.get(f"/api/studies/{study_obj.id}/export-context")
    assert r.status_code == 200 and set(SECTIONS) <= set(r.json())


async def test_collect_unknown_study_and_sections(client, study_obj):
    from spacecdf_server.services.export_context import collect
    with pytest.raises(LookupError):
        await collect("no-such-study")
    assert (await client.get("/api/studies/no-such-study/export-context")).status_code == 404
    assert (await client.get("/api/studies/no-such-study/rollup")).status_code == 404
    r = await client.get(f"/api/studies/{study_obj.id}/export-context?sections=risks,nope")
    assert r.status_code == 422


async def test_a_failing_section_is_reported_not_raised(client, study_obj, monkeypatch):
    from spacecdf_server.services import export_context as xc

    async def boom(ctx):
        raise RuntimeError("broken collector")
    monkeypatch.setitem(xc._REGISTRY, "risks", boom)
    sx = await xc.collect(study_obj.id)
    assert sx.risks == xc.empty_section("risks") and "broken collector" in sx.errors["risks"]
    assert sx.need == {} or isinstance(sx.need, dict)


async def test_collect_on_the_eosat_seed_and_the_exports_use_the_rollup(client, study_obj):
    from spacecdf_server.services.export_context import collect
    from spacecdf_server.services.rollup import compute
    out = await seed_eosat(client, study_obj.id)
    sx = await collect(study_obj.id, gate="pdr")
    assert sx.errors == {}
    assert sx.gate == "pdr" and sx.rollup["mass"]["system_margin_percent"] == 15.0
    assert sx.requirements["counts"]["total"] == 6 and sx.requirements["items"][0]["level"] == "mission"
    assert sx.risks["counts"]["total"] == 3 and sx.risks["items"][0]["score"] == 16   # sorted L x C
    assert len(sx.verification["items"]) == 6
    assert len(sx.modes["modes"]) >= 7 and sx.gates["current_gate"]
    ids = {e["id"] for e in sx.elements["items"]}
    assert out["sc"]["id"] in ids
    ru = await compute(study_obj.id)
    assert ru.form_factor == "6U" and ru.form_factor_source == "kb:struct-isis-6u"
    # a subsystem estimate added on top of its components must not change the roll-up (EG D6)
    eps = out["sub:power"]
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 5.0})
    assert r.status_code == 200, r.text
    assert (await compute(study_obj.id)).mass.cbe_kg == pytest.approx(ru.mass.cbe_kg)
    for ep in ("launch-icd", "rsssa", "deorbit", "thermal-report"):
        j = (await client.post(f"/api/exports/{ep}/{study_obj.id}")).json()
        blob = str(j)
        if ep != "thermal-report":   # the thermal report quotes neither (it uses them for areas)
            assert "'form_factor': '6U'" in blob, ep
            assert f"'total_mass_kg': {round(ru.mass.cbe_kg, 2)}" in blob, ep


async def test_rollup_endpoint(client, study_obj):
    sc = await make_element(client, study_obj.id, "Spacecraft", "system")
    r = await client.post(f"/api/elements/?study_id={study_obj.id}", json={
        "name": "Radio", "element_type": "component", "parent_id": sc["id"], "mass_kg": 0.1, "power_avg_w": 2.0,
        "quantity": 2})
    assert r.status_code == 200, r.text
    ru = (await client.get(f"/api/studies/{study_obj.id}/rollup?gate=CDR")).json()
    assert ru["gate"] == "cdr" and ru["mass"]["cbe_kg"] == pytest.approx(0.2)
    assert ru["power"]["sum_on_power_w"] == pytest.approx(4.0)
