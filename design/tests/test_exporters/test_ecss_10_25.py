"""SCDF-160 Phase 2d — ECSS-E-TM-10-25 Annex C.3 exporter.

Design §6: zip structure; every Parameter has a ParameterValueSet and a
parameterType in the RDL; containment iids resolve; JSON round-trips through
the pydantic mirror.  Seed data is shared with the Capella test.
"""
from __future__ import annotations

import io
import json
import os
import zipfile

import pytest

from tests.test_repositories.conftest import db_factory, study  # noqa: F401
from tests.test_exporters.test_capella import _seed, clean_stores  # noqa: F401

CONTAINMENT = {
    "SiteDirectory": ("domain", "model", "person", "siteReferenceDataLibrary"),
    "EngineeringModelSetup": ("iterationSetup", "participant", "requiredRdl", "activeDomain"),
    "SiteReferenceDataLibrary": ("unit", "scale", "parameterType", "definedCategory"),
    "EngineeringModel": ("iteration",),
    "Iteration": ("element", "requirementsSpecification"),
    "ElementDefinition": ("containedElement", "parameter", "category"),
    "Parameter": ("valueSet",),
    "RequirementsSpecification": ("group", "requirement"),
    "Requirement": ("definition",),
}


def _read_zip(data: bytes) -> dict[str, list[dict] | dict]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return {n: json.loads(zf.read(n)) for n in zf.namelist()}


async def test_annex_c3_zip_structure_and_integrity(db_factory, study, clean_stores):  # noqa: F811
    from spacecdf_agents.exporters.ecss_10_25 import export_study_to_10_25, parse_thing
    from spacecdf_agents.exporters.ecss_10_25 import model as m

    await _seed(study)
    data = await export_study_to_10_25(study)
    files = _read_zip(data)
    names = sorted(files)

    assert "Header.json" in names and "SiteDirectory.json" in names
    rdl_files = [n for n in names if n.startswith("SiteReferenceDataLibraries/") and n.endswith(".json")]
    em_files = [n for n in names if n.startswith("EngineeringModels/") and n.endswith("/EngineeringModel.json")]
    it_files = [n for n in names if "/Iterations/" in n]
    assert len(rdl_files) == 1 and len(em_files) == 1 and len(it_files) == 1
    em_iid = em_files[0].split("/")[1]
    assert it_files[0].startswith(f"EngineeringModels/{em_iid}/Iterations/")

    header = files["Header.json"]
    assert header["exchangeFileFormatVersion"] == "1.0.0" and header["creatorPerson"]["iid"]

    # every non-header file is an array of objects with iid/classKind/revisionNumber
    things: dict[str, dict] = {}
    for n in names:
        if n == "Header.json":
            continue
        arr = files[n]
        assert isinstance(arr, list) and arr, n
        for o in arr:
            assert {"iid", "classKind", "revisionNumber"} <= set(o), (n, o)
            assert o["iid"] not in things, "duplicate iid"
            things[o["iid"]] = o
    # first entry of each file is its container
    assert files["SiteDirectory.json"][0]["classKind"] == "SiteDirectory"
    assert files[rdl_files[0]][0]["classKind"] == "SiteReferenceDataLibrary"
    assert files[rdl_files[0]][0]["iid"] == rdl_files[0].split("/")[1][:-5]
    assert files[em_files[0]][0]["classKind"] == "EngineeringModel" and files[em_files[0]][0]["iid"] == em_iid
    assert files[it_files[0]][0]["classKind"] == "Iteration"
    assert files[it_files[0]][0]["iid"] == it_files[0].rsplit("/", 1)[1][:-5]

    # containment iids resolve
    for o in things.values():
        for prop in CONTAINMENT.get(o["classKind"], ()):
            for ref in o.get(prop, []):
                ref = ref["v"] if isinstance(ref, dict) else ref
                assert ref in things, (o["classKind"], prop, ref)
    it = files[it_files[0]][0]
    assert it["topElement"] in things and things[it["topElement"]]["name"] == "Spacecraft"
    assert len(it["option"]) == 1 and things[it["option"][0]["v"]]["name"] == "Baseline"

    # every Parameter has a value set and a parameterType in the RDL
    rdl = files[rdl_files[0]][0]
    params = [o for o in things.values() if o["classKind"] == "Parameter"]
    assert params, "no parameters exported"
    for p in params:
        assert p["parameterType"] in rdl["parameterType"]
        assert things[p["parameterType"]]["classKind"] == "SimpleQuantityKind"
        assert p["scale"] in rdl["scale"]
        assert len(p["valueSet"]) == 1
        vs = things[p["valueSet"][0]]
        assert vs["classKind"] == "ParameterValueSet"
        assert vs["valueSwitch"] in ("MANUAL", "COMPUTED", "REFERENCE")
        for k in ("manual", "computed", "reference", "published", "formula"):
            assert isinstance(vs[k], list) and len(vs[k]) == 1 and isinstance(vs[k][0], str)
        assert things[p["owner"]]["classKind"] == "DomainOfExpertise"
    eps = next(o for o in things.values() if o["classKind"] == "ElementDefinition" and o["name"] == "EPS")
    eps_params = {things[things[pid]["parameterType"]]["shortName"]: things[things[pid]["valueSet"][0]]
                  for pid in eps["parameter"]}
    assert eps_params["mass_kg"]["manual"] == ["4.5"] and eps_params["mass_kg"]["valueSwitch"] == "MANUAL"
    assert eps_params["power_avg_w"]["published"] == ["30.0"]
    # scale -> unit chain
    kg_scale = things[things[eps["parameter"][0]]["scale"]]
    assert kg_scale["classKind"] == "RatioScale" and things[kg_scale["unit"]]["classKind"] == "SimpleUnit"
    assert things[eps["owner"]]["shortName"] == "POWER"

    # element tree via usages
    sc = things[it["topElement"]]
    usages = [things[u] for u in sc["containedElement"]]
    assert {u["classKind"] for u in usages} == {"ElementUsage"}
    assert sorted(things[u["elementDefinition"]]["name"] for u in usages) == ["EPS", "OBDH"]

    # requirements
    spec = next(o for o in things.values() if o["classKind"] == "RequirementsSpecification")
    assert spec["name"] == "SpaceCDF" and len(spec["requirement"]) == 2
    assert sorted(things[g]["name"] for g in spec["group"]) == ["Mission", "System"]
    for rid in spec["requirement"]:
        r = things[rid]
        assert r["group"] in spec["group"]
        assert things[r["definition"][0]]["content"].endswith(".")

    # JSON round-trips through the pydantic mirror
    for o in things.values():
        t = parse_thing(o)
        assert type(t) is not m.Thing, o["classKind"]
        assert t.model_dump(mode="json") == o

    # deterministic iids
    assert _read_zip(await export_study_to_10_25(study))[it_files[0]][0]["iid"] == it["iid"]


async def test_push_study_uses_client(db_factory, study, clean_stores):  # noqa: F811
    """push_study builds create transactions from the exporter objects (fake transport)."""
    import httpx
    from spacecdf_agents.exporters.ecss_10_25 import AnnexCClient, push_study

    await _seed(study)
    calls: list[tuple[str, dict]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.url.path, json.loads(request.content)))
        return httpx.Response(200, json=[])

    client = AnnexCClient("http://comet.test/api", ("u", "p"),
                          client=httpx.AsyncClient(transport=httpx.MockTransport(handler),
                                                   base_url="http://comet.test/api"))
    res = await push_study(study, client)
    await client.aclose()
    assert [c[0] for c in calls] == ["/api/SiteDirectory",
                                     f"/api/EngineeringModel/{res['em_iid']}/iteration/{res['iteration_iid']}"]
    assert calls[0][1]["_create"][0]["classKind"] == "SiteDirectory"
    assert calls[1][1]["_create"][0]["classKind"] == "Iteration"
    assert res["created"]["iteration"] == len(calls[1][1]["_create"])


@pytest.mark.skipif(not all(os.environ.get(k) for k in ("COMET_URL", "COMET_USER", "COMET_PASSWORD")),
                    reason="COMET_URL/COMET_USER/COMET_PASSWORD not set")
async def test_push_to_real_comet(db_factory, study, clean_stores):  # noqa: F811
    from spacecdf_agents.exporters.ecss_10_25 import AnnexCClient, push_study
    await _seed(study)
    client = AnnexCClient(os.environ["COMET_URL"], (os.environ["COMET_USER"], os.environ["COMET_PASSWORD"]))
    try:
        res = await push_study(study, client)
    finally:
        await client.aclose()
    assert res["created"]["iteration"] > 0
