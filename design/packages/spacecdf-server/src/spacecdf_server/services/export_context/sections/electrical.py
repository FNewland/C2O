"""Section ``electrical``: the electrical and data architecture of the study and its exchange
items, for the IRD/ICD (W4.07): power rails, power lines (LCL, switch, inhibits, loads), data
buses, bus nodes (address, rate), the port count by kind, and the exchange items (ICD rows) with
the interfaces that carry them. Rejected proposals are left out. Owner: X (the model: the
electrical tab, ``routers/electrical.py``; exchange items: ``routers/exchange_items.py``)."""
from __future__ import annotations


def empty() -> dict:
    return {"rails": [], "lines": [], "buses": [], "nodes": [], "ports": {"total": 0, "by_kind": {}},
            "exchange_items": [], "counts": {}}


def _live(rows: list[dict]) -> list[dict]:
    return [r for r in rows or [] if r.get("status") != "rejected" and not r.get("deleted_at")]


async def collect(ctx) -> dict:
    from ....db import electrical_repo, exchange_item_repo
    rows = await electrical_repo.load_all(ctx.study_id)
    names = {e.get("id"): e.get("name") for e in ctx.elements}
    rails = sorted(_live(rows.get("rails")), key=lambda r: (-(r.get("voltage_v") or 0), r.get("name") or ""))
    rail_names = {r["id"]: r.get("name") for r in rails}
    lines = sorted(_live(rows.get("lines")), key=lambda r: (names.get(r.get("eps_element_id")) or "",
                                                             r.get("line_no") or 0, r.get("name") or ""))
    for ln in lines:
        ln["rail"] = rail_names.get(ln.get("rail_id"), "")
        ln["loads"] = [names.get(i, i) for i in ln.get("load_element_ids") or []]
        ln["eps"] = names.get(ln.get("eps_element_id"), "")
    for r in rails:
        r["eps"] = names.get(r.get("eps_element_id"), "")
    buses = sorted(_live(rows.get("buses")), key=lambda b: (b.get("protocol") or "", b.get("name") or ""))
    bus_names = {b["id"]: b.get("name") for b in buses}
    for b in buses:
        b["master"] = names.get(b.get("master_element_id"), "")
    nodes = [n for n in _live(rows.get("nodes")) if n.get("bus_id") in bus_names]
    for n in nodes:
        n["bus"] = bus_names.get(n.get("bus_id"), "")
        n["element"] = names.get(n.get("element_id"), n.get("element_id"))
    nodes.sort(key=lambda n: (n["bus"] or "", n.get("role") != "master", n.get("address") if n.get("address") is not None else 1e9))
    ports = _live(rows.get("ports"))
    by_kind: dict[str, int] = {}
    for p in ports:
        by_kind[p.get("kind") or ""] = by_kind.get(p.get("kind") or "", 0) + 1

    items = await exchange_item_repo.load_all_exchange_items(ctx.study_id)
    carried: dict[str, list[str]] = {}
    for i in ctx.interfaces:
        for xid in i.get("exchange_item_ids_json") or i.get("exchange_item_ids") or []:
            carried.setdefault(xid, []).append(i.get("id"))
    xis = []
    for xid, x in items.items():
        if x.get("deleted_at"):
            continue
        xis.append({"id": xid, "name": x.get("name"), "kind": x.get("kind"), "properties": x.get("properties") or {},
                    "interface_ids": carried.get(xid, [])})
    xis.sort(key=lambda x: (str(x.get("name") or ""), x["id"]))
    return {"rails": rails, "lines": lines, "buses": buses, "nodes": nodes,
            "ports": {"total": len(ports), "by_kind": by_kind}, "exchange_items": xis,
            "counts": {"rails": len(rails), "lines": len(lines), "buses": len(buses), "nodes": len(nodes),
                       "ports": len(ports), "exchange_items": len(xis)}}
