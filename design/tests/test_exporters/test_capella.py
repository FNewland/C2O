"""SCDF-160 Phase 2c — Capella exporter / importer round trip.

Uses the repository fixtures (throw-away SQLite) and the in-memory
requirements store.  Design §6: export -> reload with capellambse ->
counts/names; export -> import -> export idempotent; zip has the four files;
the vendored template is never mutated.
"""
from __future__ import annotations

import hashlib
import io
import tempfile
import zipfile
from pathlib import Path

import pytest

from tests.test_repositories.conftest import db_factory, study  # noqa: F401

pytest.importorskip("capellambse")

TEMPLATE = Path("packages/spacecdf-agents/src/spacecdf_agents/exporters/capella/template")


def _template_hash() -> str:
    h = hashlib.sha256()
    for f in sorted(TEMPLATE.iterdir()):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def _open(zip_bytes: bytes):
    from spacecdf_agents.exporters.capella.exporter import load_model
    td = Path(tempfile.mkdtemp(prefix="capella-test-"))
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = sorted(zf.namelist())
        zf.extractall(td)
    return load_model(next(td.glob("*.aird"))), names


@pytest.fixture()
def clean_stores():
    from spacecdf_server.routers import elements, requirements
    elements._elements.clear()
    elements._interfaces.clear()
    requirements._requirements.clear()
    yield
    elements._elements.clear()
    elements._interfaces.clear()
    requirements._requirements.clear()


async def _seed(study_id: str) -> dict:
    """Elements tree (2 subsystems + 3 components), 2 interfaces / 1 exchange
    item, 3 functions with allocations + 1 functional exchange, 2 requirements
    + 1 satisfies relation, 2 element parameters."""
    from spacecdf_server.db.element_repo import db_create_element, db_create_interface
    from spacecdf_server.db.exchange_item_repo import create_exchange_item
    from spacecdf_server.db.function_repo import (
        allocate_function, create_function, create_function_port, create_functional_exchange,
    )
    from spacecdf_server.db.parameter_repo import upsert_element_parameter
    from spacecdf_server.db.relation_repo import create_relation
    from spacecdf_server.routers.requirements import _requirements

    async def el(eid, name, etype, parent=None, domain=None, **extra):
        d = {"id": eid, "study_id": study_id, "name": name, "element_type": etype,
             "parent_id": parent, "subsystem_domain": domain, "version": 1, "deleted_at": None, **extra}
        await db_create_element(d)
        return d

    await el("sc", "Spacecraft", "system")
    await el("eps", "EPS", "subsystem", "sc", "power", mass_kg=4.0)
    await el("obc", "OBDH", "subsystem", "sc", "obc")
    await el("pcdu", "PCDU", "component", "eps")
    await el("bat", "Battery", "component", "eps")
    await el("fsw", "Flight Software", "software", "obc")

    xi = await create_exchange_item({"id": "xi-pwr", "study_id": study_id, "name": "28V power", "kind": "power"})
    await db_create_interface({"id": "if-pwr", "study_id": study_id, "name": "28V bus", "interface_type": "electrical",
                               "direction": "unidirectional", "from_element_id": "pcdu", "to_element_id": "obc",
                               "exchange_item_ids_json": [xi["id"]], "version": 1, "deleted_at": None})
    await db_create_interface({"id": "if-tmtc", "study_id": study_id, "name": "TM/TC", "interface_type": "data",
                               "direction": "bidirectional", "from_element_id": "obc", "to_element_id": "eps",
                               "version": 1, "deleted_at": None})

    f1 = await create_function({"id": "fn-gen", "study_id": study_id, "name": "Generate power", "layer": "SA"})
    f2 = await create_function({"id": "fn-dist", "study_id": study_id, "name": "Distribute power", "layer": "SA",
                                "parent_id": f1["id"]})
    f3 = await create_function({"id": "fn-tm", "study_id": study_id, "name": "Process telemetry", "layer": "SA"})
    await allocate_function(study_id, f1["id"], "eps", "SA")
    await allocate_function(study_id, f2["id"], "pcdu", "SA")
    await allocate_function(study_id, f3["id"], "obc", "SA")
    p_out = await create_function_port({"function_id": f2["id"], "name": "power out", "direction": "out"})
    p_in = await create_function_port({"function_id": f3["id"], "name": "power in", "direction": "in"})
    await create_functional_exchange({"id": "fx-pwr", "study_id": study_id, "name": "Bus power",
                                      "from_port_id": p_out["id"], "to_port_id": p_in["id"],
                                      "exchange_item_ids": [xi["id"]]})

    _requirements["MR-1"] = {"id": "MR-1", "study_id": study_id, "parent_id": None, "element_id": None,
                             "level": "mission", "code": "MR-001", "text": "The mission shall image the coast.",
                             "rationale": "customer need", "status": "draft"}
    _requirements["SR-1"] = {"id": "SR-1", "study_id": study_id, "parent_id": "MR-1", "element_id": "eps",
                             "level": "system", "code": "SR-001", "text": "The EPS shall deliver 30 W average.",
                             "rationale": None, "status": "draft"}
    await create_relation({"study_id": study_id, "kind": "satisfies", "source_kind": "element",
                           "source_id": "eps", "target_kind": "requirement", "target_id": "SR-1"})

    await upsert_element_parameter({"study_id": study_id, "element_id": "eps", "definition_name": "mass_kg",
                                    "manual_value": 4.5, "value_switch": "manual"})
    await upsert_element_parameter({"study_id": study_id, "element_id": "eps", "definition_name": "power_avg_w",
                                    "manual_value": 30.0, "value_switch": "manual"})
    return {"xi": xi["id"]}


def _summary(model) -> dict:
    """Layer-independent shape of a model for equality checks."""
    def names(lst):
        return sorted(x.name for x in lst)
    return {
        "pa": names(model.pa.all_components),
        "la": names(model.la.all_components),
        "sa_fn": names(model.sa.all_functions),
        "ce": sorted((x.name, x.source.parent.name, x.target.parent.name) for x in model.pa.all_component_exchanges),
        "fx": sorted((x.name, x.source.parent.name, x.target.parent.name) for x in model.sa.all_function_exchanges),
        "xi": names(model.search("ExchangeItem")),
        "req": sorted((r.identifier, str(r.text)) for r in model.oa.all_requirements),
        "rel": sorted((type(x).__name__, x.type.long_name, x.source.identifier, x.target.name)
                      for r in model.oa.all_requirements for x in r.owned_relations),
        "budget": sorted((c.name, pv.name, pv.value) for c in model.pa.all_components
                         for g in c.property_value_groups if g.name == "SpaceCDF.Budgets"
                         for pv in g.property_values),
    }


async def test_capella_round_trip(db_factory, study, clean_stores):  # noqa: F811
    from spacecdf_agents.exporters.capella import export_study_to_capella, import_capella_model
    from spacecdf_server.db.function_repo import (
        load_all_function_allocations, load_all_functional_exchanges, load_all_functions,
    )
    from spacecdf_server.db.element_repo import load_all_elements
    from spacecdf_server.db.exchange_item_repo import load_all_exchange_items
    from spacecdf_server.db.relation_repo import load_all_relations
    from spacecdf_server.db.models import StudyRow
    from spacecdf_server.routers.requirements import _requirements

    template_hash = _template_hash()
    await _seed(study)

    # ── export ──────────────────────────────────────────────────────
    res = await export_study_to_capella(study)
    assert res.files == [".project", f"{study}.afm", f"{study}.aird", f"{study}.capella"]
    model, names = _open(res.zip_bytes)
    assert names == sorted(res.files)
    assert model.info.viewpoints.get("org.polarsys.capella.vp.requirements")

    pa_names = sorted(c.name for c in model.pa.all_components if c.name != "Physical System")
    assert pa_names == ["Battery", "EPS", "Flight Software", "OBDH", "PCDU", "Spacecraft"]
    eps = model.by_uuid(res.id_map["element"]["eps"])
    assert sorted(c.name for c in eps.owned_components) == ["Battery", "PCDU"]
    assert eps.parent.name == "Spacecraft"
    assert model.by_uuid(res.id_map["element"]["fsw"]).nature.name == "BEHAVIOR"
    assert eps.nature.name == "NODE"

    sa_fns = [f for f in model.sa.all_functions if f.name != "Root System Function"]
    assert sorted(f.name for f in sa_fns) == ["Distribute power", "Generate power", "Process telemetry"]
    assert model.by_uuid(res.id_map["function"]["fn-dist"]).parent.name == "Generate power"
    # SA -> PA allocations land on the SA root component ("System") in Capella
    assert sorted(f.name for f in model.sa.root_component.allocated_functions) == \
        ["Distribute power", "Generate power", "Process telemetry"]

    ces = list(model.pa.all_component_exchanges)
    assert sorted(c.name for c in ces) == ["28V bus", "TM/TC"]
    bus = next(c for c in ces if c.name == "28V bus")
    assert (bus.source.parent.name, bus.target.parent.name) == ("PCDU", "OBDH")
    assert [i.name for i in bus.convoyed_informations] == ["28V power"]
    assert len(model.search("ExchangeItem")) == 1

    fxs = list(model.sa.all_function_exchanges)
    assert len(fxs) == 1 and fxs[0].name == "Bus power"
    assert (fxs[0].source.parent.name, fxs[0].target.parent.name) == ("Distribute power", "Process telemetry")
    assert [i.name for i in fxs[0].exchanged_items] == ["28V power"]

    reqs = {r.identifier: r for r in model.oa.all_requirements}
    assert set(reqs) == {"MR-001", "SR-001"}
    assert reqs["SR-001"].parent.identifier == "MR-001"
    assert str(reqs["MR-001"].text) == "The mission shall image the coast."
    rels = [(type(x).__name__, x.type.long_name, x.target.name) for x in reqs["SR-001"].owned_relations]
    assert ("CapellaIncomingRelation", "satisfies", "EPS") in rels     # element -> req
    assert ("CapellaOutgoingRelation", "allocates", "EPS") in rels     # requirement.element_id

    budgets = {pv.name: pv.value for g in eps.property_value_groups if g.name == "SpaceCDF.Budgets"
               for pv in g.property_values}
    assert budgets == {"mass_kg": 4.5, "power_avg_w": 30.0}
    assert [g.name for g in eps.applied_property_value_groups] == ["SpaceCDF.Budgets"]

    # ids written back
    assert res.ids_recorded > 0
    elements, interfaces = await load_all_elements()
    assert elements["eps"]["performance"]["external_ids"]["capella"] == eps.uuid
    assert interfaces["if-pwr"]["properties"]["external_ids"]["capella"] == bus.uuid
    fns = await load_all_functions(study)
    assert fns["fn-gen"]["external_ids"]["capella"] == res.id_map["function"]["fn-gen"]
    assert _requirements["SR-1"]["external_ids"]["capella"] == reqs["SR-001"].uuid

    # ── re-export: same UUIDs, no duplicates; update-in-place on the base ──
    res2 = await export_study_to_capella(study)
    assert res2.id_map == res.id_map
    model2, _ = _open(res2.zip_bytes)
    assert _summary(model2) == _summary(model)

    from spacecdf_server.db.function_repo import update_function
    await update_function("fn-tm", {"name": "Process housekeeping"})
    res3 = await export_study_to_capella(study, base=res2.zip_bytes)
    model3, _ = _open(res3.zip_bytes)
    assert res3.counts == res.counts
    assert sorted(f.name for f in model3.sa.all_functions if f.name != "Root System Function") == \
        ["Distribute power", "Generate power", "Process housekeeping"]
    assert len(model3.search("ComponentPort")) == 4
    assert len([x for r in model3.oa.all_requirements for x in r.owned_relations]) == 2
    await update_function("fn-tm", {"name": "Process telemetry"})

    # ── import into a fresh study ───────────────────────────────────
    async with db_factory() as s:
        s.add(StudyRow(id="study-2", name="Imported", meta_json={}))
        await s.commit()
    imp = await import_capella_model("study-2", res.zip_bytes)
    assert imp.created["element"] == 6
    assert imp.created["function"] == 3
    assert imp.created["interface"] == 2
    assert imp.created["exchange_item"] == 1
    assert imp.created["functional_exchange"] == 1
    assert imp.created["requirement"] == 2
    assert imp.created.get("relation", 0) == 1

    elements2, interfaces2 = await load_all_elements()
    els2 = [e for e in elements2.values() if e["study_id"] == "study-2"]
    assert sorted(e["name"] for e in els2) == sorted(e["name"] for e in elements.values() if e["study_id"] == study)
    eps2 = next(e for e in els2 if e["name"] == "EPS")
    assert eps2["subsystem_domain"] == "power" and eps2["element_type"] == "subsystem"
    assert next(e for e in els2 if e["name"] == "PCDU")["parent_id"] == eps2["id"]
    assert next(e for e in els2 if e["name"] == "Flight Software")["element_type"] == "software"
    assert eps2["mass_kg"] == 4.5
    assert len([i for i in interfaces2.values() if i["study_id"] == "study-2"]) == 2
    fns2 = await load_all_functions("study-2")
    assert len(fns2) == 3
    dist = next(f for f in fns2.values() if f["name"] == "Distribute power")
    assert fns2[dist["parent_id"]]["name"] == "Generate power"
    allocs2 = await load_all_function_allocations("study-2")
    assert len(allocs2) == 3
    assert {(fns2[a["function_id"]]["name"], elements2[a["element_id"]]["name"]) for a in allocs2.values()} == \
        {("Generate power", "EPS"), ("Distribute power", "PCDU"), ("Process telemetry", "OBDH")}
    assert len(await load_all_functional_exchanges("study-2")) == 1
    assert len(await load_all_exchange_items("study-2")) == 1
    reqs2 = [r for r in _requirements.values() if r["study_id"] == "study-2"]
    assert sorted(r["code"] for r in reqs2) == ["MR-001", "SR-001"]
    sr = next(r for r in reqs2 if r["code"] == "SR-001")
    assert sr["parent_id"] == next(r for r in reqs2 if r["code"] == "MR-001")["id"]
    assert sr["element_id"] == eps2["id"]
    rels2 = await load_all_relations("study-2")
    assert len(rels2) == 1 and next(iter(rels2.values()))["kind"] == "satisfies"

    # ── export the imported study: same shape; import again: no duplicates ──
    res4 = await export_study_to_capella("study-2")
    model4, _ = _open(res4.zip_bytes)
    assert _summary(model4) == _summary(model)
    imp2 = await import_capella_model("study-2", res4.zip_bytes)
    assert not imp2.created.get("element") and imp2.updated["element"] == 6
    assert not imp2.created.get("function") and not imp2.created.get("requirement")
    assert len([e for e in (await load_all_elements())[0].values() if e["study_id"] == "study-2"]) == 6
    res5 = await export_study_to_capella("study-2")
    assert res5.id_map == res4.id_map
    model5, _ = _open(res5.zip_bytes)
    assert _summary(model5) == _summary(model4)

    # ── the vendored template is untouched ──────────────────────────
    assert _template_hash() == template_hash


def test_mapping_is_pure_and_deterministic():
    from spacecdf_agents.exporters.capella.mapping import (
        ModelAnchors, SpineSnapshot, build_instructions, capella_uuid, guess_subsystem_domain,
    )
    anchors = ModelAnchors(*(f"root-{i}" for i in range(8)))
    snap = SpineSnapshot(study_id="s", elements=[{"id": "a", "name": "EPS", "element_type": "subsystem"}],
                         functions=[{"id": "f", "name": "F", "layer": "SA"}],
                         allocations=[{"function_id": "f", "element_id": "a"}])
    r1 = build_instructions(snap, anchors)
    r2 = build_instructions(snap, anchors)
    assert r1.instructions == r2.instructions
    assert r1.id_map[("element", "a")] == capella_uuid("s", "element", "a")
    assert r1.warnings and "cross layers" in r1.warnings[0]
    # recorded external id wins over the derived uuid
    snap.elements[0]["external_ids"] = {"capella": "keep-me"}
    assert build_instructions(snap, anchors).id_map[("element", "a")] == "keep-me"
    assert guess_subsystem_domain("EPS PCDU") == "power"
    assert guess_subsystem_domain("ADCS Reaction wheel") == "aocs"
    assert guess_subsystem_domain("Harness") is None
    assert guess_subsystem_domain("OBC") == "obc"


def test_render_is_optional():
    from spacecdf_agents.exporters.capella.exporter import TEMPLATE_DIR, load_model
    from spacecdf_agents.exporters.capella.render import render_context_svgs
    import shutil
    td = Path(tempfile.mkdtemp())
    for f in TEMPLATE_DIR.iterdir():
        shutil.copy(f, td / f.name)
    warnings: list[str] = []
    svgs = render_context_svgs(load_model(td / "empty.aird"), warnings=warnings)
    assert isinstance(svgs, dict)
    assert all(v.lstrip().startswith("<") for v in svgs.values())
