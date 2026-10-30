"""Repo tests for exchange items (SCDF-160 §1.2)."""
from __future__ import annotations

import pytest

from spacecdf_server.db import exchange_item_repo as xr


async def test_crud(study):
    xi = await xr.create_exchange_item({"study_id": study, "name": "Housekeeping TM", "kind": "data",
                                        "properties": {"rate_bps": 9600, "protocol": "CAN"}})
    assert xi["id"].startswith("xi-") and xi["properties"]["rate_bps"] == 9600
    got = await xr.get_exchange_item(xi["id"])
    assert got["name"] == "Housekeeping TM"
    u = await xr.update_exchange_item(xi["id"], {"properties": {"rate_bps": 19200}}, expected_version=1)
    assert u["properties"] == {"rate_bps": 19200} and u["version"] == 2
    with pytest.raises(ValueError, match="Version conflict"):
        await xr.update_exchange_item(xi["id"], {"name": "x"}, expected_version=1)
    assert await xr.soft_delete_exchange_item(xi["id"]) is True
    assert await xr.get_exchange_item(xi["id"]) is None
    assert await xr.soft_delete_exchange_item(xi["id"]) is False
    with pytest.raises(ValueError, match="not found"):
        await xr.update_exchange_item(xi["id"], {"name": "x"})


async def test_validation(study):
    with pytest.raises(ValueError, match="kind"):
        await xr.create_exchange_item({"study_id": study, "name": "x", "kind": "magic"})
    with pytest.raises(ValueError, match="name"):
        await xr.create_exchange_item({"study_id": study})
    xi = await xr.create_exchange_item({"study_id": study, "name": "x"})
    assert xi["kind"] == "data"
    with pytest.raises(ValueError, match="kind"):
        await xr.update_exchange_item(xi["id"], {"kind": "magic"})


async def test_list_and_load(study):
    a = await xr.create_exchange_item({"study_id": study, "name": "B", "kind": "power"})
    b = await xr.create_exchange_item({"study_id": study, "name": "A", "kind": "data"})
    await xr.create_exchange_item({"study_id": "other", "name": "C"})
    names = [x["name"] for x in await xr.list_exchange_items_by_study(study)]
    assert names == ["A", "B"]
    assert [x["id"] for x in await xr.list_exchange_items_by_study(study, kind="power")] == [a["id"]]
    assert {x["id"] for x in await xr.list_exchange_items_by_ids([a["id"], b["id"], "nope"])} == {a["id"], b["id"]}
    assert await xr.list_exchange_items_by_ids([]) == []
    assert set(await xr.load_all_exchange_items(study)) == {a["id"], b["id"]}
    assert len(await xr.load_all_exchange_items()) == 3
