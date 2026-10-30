"""SCDF-175 — verification_repo: CRUD, list by study / requirement, and
``upsert_generated`` that never displaces a user-edited row's filled fields."""
from __future__ import annotations

import pytest

from spacecdf_server.db import verification_repo as vr


async def test_crud_and_lists(db_factory, study):
    a = await vr.create_item({"study_id": study, "requirement_id": "SR-1", "method": "A", "level": "system",
                              "phase": "PDR", "acceptance_criterion": "x <= 1"})
    assert a["id"].startswith("vi-") and a["status"] == "planned" and a["edited_by_user"] is False
    b = await vr.create_item({"study_id": study, "requirement_id": "SR-2", "method": "T", "level": "unit"})
    assert (await vr.get_item(a["id"]))["requirement_id"] == "SR-1"
    assert await vr.get_item("nope") is None
    assert [i["requirement_id"] for i in await vr.list_by_study(study)] == ["SR-1", "SR-2"]
    assert [i["id"] for i in await vr.list_by_requirement("SR-2")] == [b["id"]]
    assert (await vr.get_by_requirement(study, "SR-1"))["id"] == a["id"]
    assert await vr.get_by_requirement(study, "SR-9") is None

    upd = await vr.update_item(a["id"], {"facility": "tvac_chamber", "study_id": "hack", "id": "hack"})
    assert upd["facility"] == "tvac_chamber" and upd["study_id"] == study and upd["id"] == a["id"]
    assert upd["edited_by_user"] is False
    upd = await vr.update_item(a["id"], {"phase": "CDR"}, by_user=True)
    assert upd["phase"] == "CDR" and upd["edited_by_user"] is True

    st = await vr.set_status(a["id"], "passed", "analysis:run-1")
    assert st["status"] == "passed" and st["evidence_ref"] == "analysis:run-1"

    with pytest.raises(ValueError):
        await vr.update_item("nope", {"phase": "CDR"})
    with pytest.raises(ValueError):
        await vr.update_item(a["id"], {"status": "bogus"})
    with pytest.raises(ValueError):
        await vr.create_item({"study_id": study, "requirement_id": "SR-3", "method": "Z"})
    with pytest.raises(ValueError):
        await vr.create_item({"study_id": study})

    assert await vr.soft_delete_item(b["id"]) is True
    assert await vr.soft_delete_item(b["id"]) is False
    assert [i["id"] for i in await vr.list_by_study(study)] == [a["id"]]
    assert await vr.get_item(b["id"]) is None


async def test_upsert_generated_respects_user_edits(db_factory, study):
    gen = {"study_id": study, "requirement_id": "SR-1", "method": "A", "level": "system", "phase": "PDR",
           "facility": "analysis desk", "acceptance_criterion": "Mass <= 4 kg (analysis), PDR"}
    first = await vr.upsert_generated(gen)
    assert first["method"] == "A" and first["status"] == "planned"

    # untouched row: generator refresh overwrites planning fields, one row per requirement
    again = await vr.upsert_generated({**gen, "phase": "CDR", "acceptance_criterion": "Mass <= 3 kg (analysis), CDR"})
    assert again["id"] == first["id"] and again["phase"] == "CDR" and "3 kg" in again["acceptance_criterion"]
    assert len(await vr.list_by_study(study)) == 1

    # closure evidence survives a refresh on an untouched row
    await vr.set_status(first["id"], "passed", "analysis:run-7")
    again = await vr.upsert_generated({**gen, "status": "planned", "evidence_ref": None})
    assert again["status"] == "passed" and again["evidence_ref"] == "analysis:run-7"

    # user edit: method + facility set by hand, phase cleared -> only the empty phase gets filled
    await vr.update_item(first["id"], {"method": "T", "facility": "shaker_table", "phase": None}, by_user=True)
    again = await vr.upsert_generated({**gen, "phase": "QR", "facility": "analysis desk", "method": "A"})
    assert again["method"] == "T" and again["facility"] == "shaker_table"
    assert again["phase"] == "QR" and again["edited_by_user"] is True
    assert again["status"] == "passed"

    with pytest.raises(ValueError):
        await vr.upsert_generated({"study_id": study})
