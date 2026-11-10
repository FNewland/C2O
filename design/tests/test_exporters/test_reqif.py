"""SCDF-160 Phase 2d — ReqIF export -> parse -> import round trip."""
from __future__ import annotations

import pytest

from tests.test_repositories.conftest import db_factory, study  # noqa: F401
from tests.test_exporters.test_capella import _seed, clean_stores  # noqa: F401


async def _seed_requirements(study_id: str) -> None:
    """Three-level tree + requirement<->requirement and element->requirement relations."""
    from spacecdf_server.db.relation_repo import create_relation
    from spacecdf_server.routers.requirements import _requirements

    await _seed(study_id)  # MR-1, SR-1 (child of MR-1), eps satisfies SR-1
    _requirements["SSR-1"] = {"id": "SSR-1", "study_id": study_id, "parent_id": "SR-1", "element_id": "pcdu",
                              "level": "subsystem", "code": "SSR-001",
                              "text": "The PCDU shall regulate the bus to 28 V <±1%> & \"clean\".",
                              "rationale": "EPS need", "status": "approved", "verification_method": "test",
                              "verification_phase": "AIT", "external_id": "CUSTOMER-REQ-42"}
    _requirements["SR-2"] = {"id": "SR-2", "study_id": study_id, "parent_id": "MR-1", "element_id": None,
                             "level": "system", "code": "SR-002", "text": "The OBDH shall store 1 Gbit.",
                             "rationale": None, "status": "draft"}
    _requirements["OTHER"] = {"id": "OTHER", "study_id": "another-study", "parent_id": None, "element_id": None,
                              "level": "mission", "code": "X", "text": "not exported", "status": "draft"}
    await create_relation({"study_id": study_id, "kind": "derives", "source_kind": "requirement",
                           "source_id": "SSR-1", "target_kind": "requirement", "target_id": "SR-1"})
    await create_relation({"study_id": study_id, "kind": "traces", "source_kind": "requirement",
                           "source_id": "SR-2", "target_kind": "requirement", "target_id": "MR-1"})


async def test_export_parse_import_round_trip(db_factory, study, clean_stores):  # noqa: F811
    from reqif.parser import ReqIFParser
    from spacecdf_agents.exporters.reqif import (
        ATTRIBUTES, SPEC_OBJECT_TYPE_ID, export_requirements_reqif, import_requirements_reqif,
    )
    from spacecdf_server.db.relation_repo import load_all_relations
    from spacecdf_server.routers.requirements import _requirements

    await _seed_requirements(study)
    data = await export_requirements_reqif(study)
    assert data.startswith(b"<?xml")

    # identifiers written back (store is the API's source of truth)
    assert _requirements["MR-1"]["external_id"] == "SCDF-REQ-MR-1"
    assert _requirements["SSR-1"]["external_id"] == "CUSTOMER-REQ-42"
    assert "external_id" not in _requirements["OTHER"]

    bundle = ReqIFParser.parse_from_string(data.decode("utf-8"))
    content = bundle.core_content.req_if_content
    objs = {o.identifier: o for o in content.spec_objects}
    assert set(objs) == {"SCDF-REQ-MR-1", "SCDF-REQ-SR-1", "SCDF-REQ-SR-2", "CUSTOMER-REQ-42"}
    st = bundle.get_spec_object_type_by_ref(SPEC_OBJECT_TYPE_ID)
    assert st.long_name == "SpaceCDF Requirement"
    assert [a.long_name for a in st.attribute_definitions] == list(ATTRIBUTES)
    ssr = objs["CUSTOMER-REQ-42"]
    vals = {a.definition_ref: a.value for a in ssr.attributes}
    assert vals["SCDF-ATTR-TEXT"] == 'The PCDU shall regulate the bus to 28 V <±1%> & "clean".'
    assert vals["SCDF-ATTR-LEVEL"] == "subsystem" and vals["SCDF-ATTR-STATUS"] == "approved"

    # hierarchy
    spec = content.specifications[0]
    tree = {n.spec_object: n for n in bundle.iterate_specification_hierarchy(spec)}
    assert [n.spec_object for n in spec.children] == ["SCDF-REQ-MR-1"]
    assert tree["SCDF-REQ-MR-1"].level == 1 and tree["SCDF-REQ-SR-1"].level == 2 and tree["CUSTOMER-REQ-42"].level == 3
    assert sorted(c.spec_object for c in tree["SCDF-REQ-MR-1"].children) == ["SCDF-REQ-SR-1", "SCDF-REQ-SR-2"]

    # relations: only requirement<->requirement; element->requirement noted in header comment
    rels = {(r.relation_type_ref, r.source, r.target) for r in content.spec_relations}
    assert rels == {("SCDF-REL-DERIVES", "CUSTOMER-REQ-42", "SCDF-REQ-SR-1"),
                    ("SCDF-REL-TRACES", "SCDF-REQ-SR-2", "SCDF-REQ-MR-1")}
    assert "not expressible in ReqIF" in (bundle.req_if_header.comment or "")

    # import into a fresh study: ids / hierarchy / relations preserved
    fresh = "study-fresh"
    res = await import_requirements_reqif(fresh, data)
    assert res.created == 4 and res.updated == 0 and res.relations_created == 2
    new = {r["external_id"]: r for r in _requirements.values() if r["study_id"] == fresh}
    assert set(new) == set(objs)
    assert new["SCDF-REQ-SR-1"]["parent_id"] == new["SCDF-REQ-MR-1"]["id"]
    assert new["CUSTOMER-REQ-42"]["parent_id"] == new["SCDF-REQ-SR-1"]["id"]
    assert new["CUSTOMER-REQ-42"]["text"].endswith('"clean".')
    assert new["CUSTOMER-REQ-42"]["verification_method"] == "T" and new["CUSTOMER-REQ-42"]["level"] == "subsystem"
    assert new["SCDF-REQ-SR-2"]["rationale"] is None
    # original ids are kept for generated identifiers when free; SCDF-REQ-MR-1 collides -> new id
    assert new["SCDF-REQ-MR-1"]["id"] != "MR-1"
    new_rels = {(r["kind"], r["source_id"], r["target_id"]) for r in (await load_all_relations(fresh)).values()}
    assert new_rels == {("derives", new["CUSTOMER-REQ-42"]["id"], new["SCDF-REQ-SR-1"]["id"]),
                        ("traces", new["SCDF-REQ-SR-2"]["id"], new["SCDF-REQ-MR-1"]["id"])}

    # re-import into the same study is an upsert (no duplicates), relations not duplicated
    res2 = await import_requirements_reqif(fresh, data)
    assert res2.created == 0 and res2.updated == 4 and res2.relations_created == 0
    assert len([r for r in _requirements.values() if r["study_id"] == fresh]) == 4

    # re-export of the fresh study is stable
    data2 = await export_requirements_reqif(fresh)
    objs2 = {o.identifier for o in ReqIFParser.parse_from_string(data2.decode()).core_content.req_if_content.spec_objects}
    assert objs2 == set(objs)


async def test_import_updates_existing_by_identifier(db_factory, study, clean_stores):  # noqa: F811
    from spacecdf_agents.exporters.reqif import export_requirements_reqif, import_requirements_reqif
    from spacecdf_server.routers.requirements import _requirements

    await _seed_requirements(study)
    data = await export_requirements_reqif(study)
    _requirements["SR-1"]["text"] = "changed locally"
    res = await import_requirements_reqif(study, data)
    assert res.created == 0 and res.updated == 4
    assert _requirements["SR-1"]["text"] == "The EPS shall deliver 30 W average."
    assert _requirements["SR-1"]["parent_id"] == "MR-1"


async def test_threshold_round_trip(db_factory, study, clean_stores):  # noqa: F811
    """SCDF-170 N2: threshold_param_path/op/value survive export -> import."""
    from reqif.parser import ReqIFParser
    from spacecdf_agents.exporters.reqif import ATTRIBUTES, export_requirements_reqif, import_requirements_reqif
    from spacecdf_server.routers.requirements import _requirements

    await _seed_requirements(study)
    _requirements["SR-1"].update({"threshold_param_path": "power.eps_mass_kg", "threshold_op": "<=",
                                  "threshold_value": "5"})
    _requirements["SSR-1"].update({"threshold_param_path": "el:PCDU.mass_kg", "threshold_op": ">=",
                                   "threshold_value": "0.25"})
    assert {"threshold_param_path", "threshold_op", "threshold_value"} <= set(ATTRIBUTES)

    data = await export_requirements_reqif(study)
    content = ReqIFParser.parse_from_string(data.decode()).core_content.req_if_content
    objs = {o.identifier: {a.definition_ref: a.value for a in o.attributes} for o in content.spec_objects}
    assert objs["SCDF-REQ-SR-1"]["SCDF-ATTR-THRESHOLD_PARAM_PATH"] == "power.eps_mass_kg"
    assert objs["SCDF-REQ-SR-1"]["SCDF-ATTR-THRESHOLD_OP"] == "<="
    assert objs["SCDF-REQ-SR-1"]["SCDF-ATTR-THRESHOLD_VALUE"] == "5"
    assert objs["CUSTOMER-REQ-42"]["SCDF-ATTR-THRESHOLD_PARAM_PATH"] == "el:PCDU.mass_kg"
    assert objs["SCDF-REQ-MR-1"]["SCDF-ATTR-THRESHOLD_PARAM_PATH"] == ""

    fresh = "study-fresh"
    await import_requirements_reqif(fresh, data)
    new = {r["external_id"]: r for r in _requirements.values() if r["study_id"] == fresh}
    sr1, ssr1, mr1 = new["SCDF-REQ-SR-1"], new["CUSTOMER-REQ-42"], new["SCDF-REQ-MR-1"]
    assert (sr1["threshold_param_path"], sr1["threshold_op"], sr1["threshold_value"]) == ("power.eps_mass_kg", "<=", 5)  # W1.01: decoded
    assert (ssr1["threshold_param_path"], ssr1["threshold_op"], ssr1["threshold_value"]) == ("el:PCDU.mass_kg", ">=", 0.25)  # W1.01: decoded
    assert mr1["threshold_param_path"] is None and mr1["threshold_op"] is None and mr1["threshold_value"] is None

    # the compliance tracker can act on the imported requirement
    from spacecdf_server.services.compliance_tracker import ComplianceTracker
    res = ComplianceTracker().evaluate_single(sr1, {"power.eps_mass_kg": 6.0})
    assert res.status == "fail" and res.threshold_value == 5.0

    # re-import after the source cleared its threshold clears it on the target too
    _requirements["SR-1"].update({"threshold_param_path": None, "threshold_op": None, "threshold_value": None})
    await import_requirements_reqif(fresh, await export_requirements_reqif(study))
    assert new["SCDF-REQ-SR-1"]["threshold_param_path"] is None
