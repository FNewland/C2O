"""Exchange items, interface binding and ICD projection (SCDF-160 §1.2)."""
from __future__ import annotations

import csv
import io

from tests.test_api.conftest import make_element, make_interface


async def _item(client, study, name, kind="data", **props):
    r = await client.post(f"/api/exchange-items/?study_id={study}", json={
        "name": name, "kind": kind, "properties": props})
    assert r.status_code == 200, r.text
    return r.json()


async def test_exchange_item_crud(client, study_obj, study):
    xi = await _item(client, study, "Housekeeping TM", rate_bps=9600, protocol="CAN")
    assert xi["kind"] == "data" and xi["properties"]["rate_bps"] == 9600 and xi["version"] == 1

    assert (await client.get(f"/api/exchange-items/{xi['id']}")).json()["name"] == "Housekeeping TM"
    r = await client.patch(f"/api/exchange-items/{xi['id']}", json={"version": 1, "properties": {"rate_bps": 19200}})
    assert r.status_code == 200 and r.json()["properties"] == {"rate_bps": 19200} and r.json()["version"] == 2
    assert (await client.patch(f"/api/exchange-items/{xi['id']}", json={"version": 1, "name": "x"})).status_code == 409
    assert (await client.patch(f"/api/exchange-items/{xi['id']}", json={"kind": "plasma"})).status_code == 400
    assert (await client.post(f"/api/exchange-items/?study_id={study}", json={"name": "x", "kind": "plasma"})).status_code == 400

    pw = await _item(client, study, "28V bus", kind="power", voltage_v=28)
    assert len((await client.get(f"/api/studies/{study}/exchange-items")).json()) == 2
    assert [i["id"] for i in (await client.get(f"/api/studies/{study}/exchange-items?kind=power")).json()] == [pw["id"]]

    r = await client.delete(f"/api/exchange-items/{pw['id']}")
    assert r.status_code == 200 and r.json()["deleted"] is True
    assert (await client.get(f"/api/exchange-items/{pw['id']}")).status_code == 404
    assert (await client.delete(f"/api/exchange-items/{pw['id']}")).status_code == 404


async def test_interface_binding_and_icd(client, study_obj, study):
    from spacecdf_server.db._arcadia_common import get_session_factory
    from spacecdf_server.db.models import ElementInterfaceRow

    obc = await make_element(client, study, "OBC", subsystem_domain="obc")
    eps = await make_element(client, study, "EPS", subsystem_domain="eps")
    pl = await make_element(client, study, "Payload", subsystem_domain="payload")
    can = await make_interface(client, study, obc["id"], eps["id"], name="CAN bus", interface_type="data")
    pwr = await make_interface(client, study, eps["id"], pl["id"], name="PL power", interface_type="electrical")

    tm = await _item(client, study, "HK TM", rate_bps=9600)
    tc = await _item(client, study, "TC", rate_bps=1200)
    bus = await _item(client, study, "28V", kind="power", voltage_v=28, current_a=2.5)

    r = await client.patch(f"/api/interfaces/{can['id']}/exchange-items", json={"exchange_item_ids": [tm["id"], tc["id"], tm["id"]]})
    assert r.status_code == 200, r.text
    assert r.json()["exchange_item_ids"] == [tm["id"], tc["id"]]  # de-duplicated
    assert (await client.patch(f"/api/interfaces/{can['id']}/exchange-items", json={"exchange_item_ids": ["ghost"]})).status_code == 400
    assert (await client.patch("/api/interfaces/ghost/exchange-items", json={"exchange_item_ids": []})).status_code == 404
    assert (await client.patch(f"/api/interfaces/{pwr['id']}/exchange-items", json={"exchange_item_ids": [bus["id"]]})).status_code == 200

    # write-through: the DB row carries the ids
    async with get_session_factory()() as s:
        row = await s.get(ElementInterfaceRow, can["id"])
        assert row.exchange_item_ids_json == [tm["id"], tc["id"]]

    listed = (await client.get(f"/api/interfaces/{can['id']}/exchange-items")).json()
    assert [i["name"] for i in listed] == ["HK TM", "TC"]

    icd = (await client.get(f"/api/studies/{study}/icd")).json()
    assert len(icd) == 3
    by_name = {(r["name"], (r["exchange_item"] or {}).get("name")): r for r in icd}
    row = by_name[("CAN bus", "HK TM")]
    assert row["interface_id"] == can["id"] and row["interface_type"] == "data"
    assert row["from_element"] == {"id": obc["id"], "name": "OBC"}
    assert row["to_element"] == {"id": eps["id"], "name": "EPS"}
    assert row["exchange_item"]["kind"] == "data" and row["exchange_item"]["properties"] == {"rate_bps": 9600}
    assert by_name[("PL power", "28V")]["exchange_item"]["properties"]["voltage_v"] == 28

    # interfaces without exchange items still appear (one row, exchange_item=None)
    bare = await make_interface(client, study, obc["id"], pl["id"], name="PL data", interface_type="data")
    icd = (await client.get(f"/api/studies/{study}/icd")).json()
    assert len(icd) == 4
    assert next(r for r in icd if r["interface_id"] == bare["id"])["exchange_item"] is None

    # CSV
    r = await client.get(f"/api/studies/{study}/icd.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(r.text)))
    assert rows[0][:4] == ["interface_id", "interface", "interface_type", "direction"]
    assert len(rows) == 5
    assert any(r[1] == "CAN bus" and r[9] == "HK TM" and '"rate_bps": 9600' in r[11] for r in rows[1:])

    # deleting an exchange item detaches it from interfaces
    r = await client.delete(f"/api/exchange-items/{tm['id']}")
    assert r.json()["interfaces_detached"] == 1
    assert (await client.get(f"/api/interfaces/{can['id']}/exchange-items")).json()[0]["id"] == tc["id"]
    icd = (await client.get(f"/api/studies/{study}/icd")).json()
    assert not any((r["exchange_item"] or {}).get("id") == tm["id"] for r in icd)
