"""Repo tests for functions / ports / allocations / exchanges / realizations (SCDF-160 §1.1)."""
from __future__ import annotations

import pytest

from spacecdf_server.db import function_repo as fr
from spacecdf_server.db.models import DesignElementRow


@pytest.fixture()
async def element(db_factory, study):
    async with db_factory() as s:
        s.add(DesignElementRow(id="el-eps", study_id=study, name="EPS", element_type="subsystem",
                               subsystem_domain="eps"))
        s.add(DesignElementRow(id="el-obc", study_id=study, name="OBC", element_type="subsystem",
                               subsystem_domain="obc"))
        await s.commit()
    return "el-eps"


class TestFunctions:
    async def test_create_and_get(self, study):
        f = await fr.create_function({"study_id": study, "name": "Generate power",
                                      "external_ids": {"legacy": "F-001"}})
        assert f["id"].startswith("fn-")
        assert f["layer"] == "SA"
        assert f["version"] == 1
        assert f["external_ids"] == {"legacy": "F-001"}
        got = await fr.get_function(f["id"])
        assert got["name"] == "Generate power"

    async def test_create_requires_name_and_study(self, study):
        with pytest.raises(ValueError):
            await fr.create_function({"study_id": study})
        with pytest.raises(ValueError):
            await fr.create_function({"name": "x"})

    async def test_update_bumps_version_and_locks(self, study):
        f = await fr.create_function({"study_id": study, "name": "A"})
        u = await fr.update_function(f["id"], {"name": "B", "layer": "LA"}, expected_version=1)
        assert u["name"] == "B" and u["layer"] == "LA" and u["version"] == 2
        with pytest.raises(ValueError, match="Version conflict"):
            await fr.update_function(f["id"], {"name": "C"}, expected_version=1)
        with pytest.raises(ValueError, match="not found"):
            await fr.update_function("nope", {"name": "C"})

    async def test_update_ignores_immutable_and_unknown(self, study):
        f = await fr.create_function({"study_id": study, "name": "A"})
        u = await fr.update_function(f["id"], {"id": "hack", "study_id": "other", "bogus": 1, "level": 2})
        assert u["id"] == f["id"] and u["study_id"] == study and u["level"] == 2

    async def test_self_parent_rejected(self, study):
        f = await fr.create_function({"study_id": study, "name": "A"})
        with pytest.raises(ValueError):
            await fr.update_function(f["id"], {"parent_id": f["id"]})

    async def test_soft_delete_and_list(self, study):
        a = await fr.create_function({"study_id": study, "name": "A", "layer": "SA"})
        b = await fr.create_function({"study_id": study, "name": "B", "layer": "LA", "parent_id": a["id"]})
        assert len(await fr.list_functions_by_study(study)) == 2
        assert [x["id"] for x in await fr.list_functions_by_study(study, layer="LA")] == [b["id"]]
        assert [x["id"] for x in await fr.list_function_children(a["id"])] == [b["id"]]
        assert await fr.soft_delete_function(a["id"]) is True
        assert await fr.soft_delete_function(a["id"]) is False
        assert await fr.get_function(a["id"]) is None
        assert (await fr.get_function(a["id"], include_deleted=True))["deleted_at"]
        assert len(await fr.list_functions_by_study(study)) == 1
        assert len(await fr.list_functions_by_study(study, include_deleted=True)) == 2
        loaded = await fr.load_all_functions(study)
        assert set(loaded) == {b["id"]}


class TestPorts:
    async def test_port_crud(self, study):
        f = await fr.create_function({"study_id": study, "name": "A"})
        p = await fr.create_function_port({"function_id": f["id"], "name": "power out",
                                           "direction": "out", "exchange_item_ids": ["xi-1"]})
        assert p["exchange_item_ids"] == ["xi-1"]
        with pytest.raises(ValueError):
            await fr.create_function_port({"function_id": f["id"], "direction": "sideways"})
        with pytest.raises(ValueError, match="not found"):
            await fr.create_function_port({"function_id": "nope"})
        u = await fr.update_function_port(p["id"], {"name": "pwr", "function_id": "hack"})
        assert u["name"] == "pwr" and u["function_id"] == f["id"]
        assert len(await fr.list_ports_by_function(f["id"])) == 1
        assert len(await fr.load_all_function_ports(study)) == 1
        assert await fr.soft_delete_function_port(p["id"])
        assert await fr.list_ports_by_function(f["id"]) == []
        assert await fr.load_all_function_ports(study) == {}


class TestAllocations:
    async def test_allocate_is_upsert_per_layer(self, study, element):
        f = await fr.create_function({"study_id": study, "name": "A"})
        a1 = await fr.allocate_function(study, f["id"], "el-eps", "SA")
        a2 = await fr.allocate_function(study, f["id"], "el-obc", "SA")
        assert a1["id"] == a2["id"] and a2["element_id"] == "el-obc"
        a3 = await fr.allocate_function(study, f["id"], "el-eps", "PA")
        assert a3["id"] != a1["id"]
        assert len(await fr.list_allocations_by_function(f["id"])) == 2
        assert len(await fr.list_allocations_by_element("el-eps")) == 1
        assert len(await fr.list_allocations_by_study(study)) == 2
        assert len(await fr.load_all_function_allocations(study)) == 2
        assert await fr.unallocate_function(f["id"], "SA") is True
        assert await fr.unallocate_function(f["id"], "SA") is False
        assert len(await fr.list_allocations_by_function(f["id"])) == 1


class TestExchanges:
    async def test_exchange_crud(self, study):
        a = await fr.create_function({"study_id": study, "name": "A"})
        b = await fr.create_function({"study_id": study, "name": "B"})
        pa = await fr.create_function_port({"function_id": a["id"], "direction": "out"})
        pb = await fr.create_function_port({"function_id": b["id"], "direction": "in"})
        x = await fr.create_functional_exchange({"study_id": study, "name": "28V",
                                                 "from_port_id": pa["id"], "to_port_id": pb["id"]})
        assert x["id"].startswith("fx-") and x["realized_by_interface_id"] is None
        with pytest.raises(ValueError, match="differ"):
            await fr.create_functional_exchange({"study_id": study, "from_port_id": pa["id"], "to_port_id": pa["id"]})
        with pytest.raises(ValueError, match="not found"):
            await fr.create_functional_exchange({"study_id": study, "from_port_id": pa["id"], "to_port_id": "nope"})
        u = await fr.update_functional_exchange(x["id"], {"exchange_item_ids": ["xi-9"]}, expected_version=1)
        assert u["exchange_item_ids"] == ["xi-9"] and u["version"] == 2
        assert len(await fr.list_functional_exchanges_by_study(study)) == 1
        assert await fr.soft_delete_functional_exchange(x["id"])
        assert await fr.list_functional_exchanges_by_study(study) == []
        assert await fr.load_all_functional_exchanges(study) == {}


class TestRealizations:
    async def test_realization_idempotent(self, study):
        sa = await fr.create_function({"study_id": study, "name": "SA fn", "layer": "SA"})
        la = await fr.create_function({"study_id": study, "name": "LA fn", "layer": "LA"})
        d = {"study_id": study, "source_kind": "function", "source_id": la["id"],
             "target_kind": "function", "target_id": sa["id"]}
        r1 = await fr.create_realization(d)
        r2 = await fr.create_realization(d)
        assert r1["id"] == r2["id"]
        assert len(await fr.list_realizations_by_study(study)) == 1
        assert len(await fr.list_realizations_for("function", sa["id"])) == 1
        assert await fr.soft_delete_realization(r1["id"])
        assert await fr.list_realizations_by_study(study) == []
        r3 = await fr.create_realization(d)  # revived
        assert r3["id"] == r1["id"] and r3["deleted_at"] is None
        assert len(await fr.load_all_realizations(study)) == 1
        with pytest.raises(ValueError):
            await fr.create_realization({**d, "source_kind": "requirement"})
