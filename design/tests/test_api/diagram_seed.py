"""An EOSAT-1-like 6U Earth-observation study seeded through the public API only, so the
same steps work on the in-process test client and on a running server (screenshots).

6U structure, 28.8 V battery bus, CAN, S-band transceiver + patch, imager, ADCS, deployable
wings; interfaces proposed and accepted, rails/lines/buses proposed and accepted, the
ConOps mode set with transitions and the mode × unit matrix, an approved stack layout,
two ground stations, a small function tree with allocations, requirements with
verification items, and a few risks.
"""
from __future__ import annotations

from typing import Any

SUBSYSTEMS: list[tuple[str, str, list[tuple[str, str, int]]]] = [
    ("Payload", "payload", [("Imager", "pl-imager-2u-eosat", 1)]),
    ("EPS", "power", [("EPS", "eps-gom-nanopow-p60", 1), ("Battery", "bat-gom-nanopow-bp8", 1),
                      ("Solar wings", "sp-clyde-3u-deploy", 2)]),
    ("AOCS", "aocs", [("Reaction wheel", "rw-cubespace-cubewheel-medium", 1), ("Star tracker", "st-cubespace-cubestar", 1),
                      ("Magnetorquer", "mtq-cubespace-cubetorquer", 1), ("GNSS receiver", "gps-skyfox-picostar", 1)]),
    ("Communications", "ttc", [("S-band transceiver", "txr-endurosat-sband", 1),
                               ("S-band patch", "ant-endurosat-sband-patch", 1)]),
    ("On-Board Computer", "obc", [("OBC", "obc-gom-nanomind-a3200", 1)]),
    ("Thermal", "thermal", [("Battery heater", "th-heater-kapton-05", 1)]),
    ("Structure", "structure", [("Structure 6U", "struct-isis-6u", 1)]),
]


async def _post(c, url: str, body: Any = None, ok=(200, 201)) -> Any:
    r = await c.post(url, json=body if body is not None else {})
    assert r.status_code in ok, f"{url}: {r.status_code} {r.text[:300]}"
    return r.json()


async def seed_eosat(c, sid: str, *, stack: bool = True, verification: bool = True) -> dict[str, dict]:
    el = lambda **b: _post(c, f"/api/elements/?study_id={sid}", b)  # noqa: E731
    mission = await el(name="EOSAT mission", element_type="mission")
    space = await el(name="Space Segment", element_type="segment", parent_id=mission["id"], segment="space")
    ground = await el(name="Ground Segment", element_type="segment", parent_id=mission["id"], segment="ground")
    sc = await el(name="EOSAT-1", element_type="system", parent_id=space["id"])
    await el(name="Mission control centre", element_type="system", parent_id=ground["id"], segment="ground",
             subsystem_domain="ground")
    out: dict[str, dict] = {"mission": mission, "sc": sc}
    for sname, dom, parts in SUBSYSTEMS:
        sub = await el(name=sname, element_type="subsystem", parent_id=sc["id"], subsystem_domain=dom)
        out[f"sub:{dom}"] = sub
        for name, kb, q in parts:
            out[name] = await el(name=name, element_type="component", parent_id=sub["id"], subsystem_domain=dom,
                                 kb_component_id=kb, quantity=q)
    # links: propose, accept every suggestion
    await _post(c, f"/api/studies/{sid}/interfaces/propose", {})
    for i in (await c.get(f"/api/studies/{sid}/interfaces?status=suggested")).json():
        r = await c.patch(f"/api/interfaces/{i['id']}", json={"status": "accepted"})
        assert r.status_code == 200, r.text
    # electrical: rails, lines, buses, nodes
    await _post(c, f"/api/studies/{sid}/electrical/propose", {})
    elec = (await c.get(f"/api/studies/{sid}/electrical")).json()
    for kind in ("rails", "lines", "buses", "nodes"):
        for row in elec.get(kind) or []:
            if row.get("status") == "suggested":
                r = await c.patch(f"/api/studies/{sid}/electrical/{kind}/{row['id']}", json={"status": "accepted"})
                assert r.status_code == 200, r.text
    # modes: template set, matrix, accept
    await _post(c, f"/api/studies/{sid}/modes/template", {})
    await _post(c, f"/api/studies/{sid}/modes/propose", {})
    await _post(c, f"/api/studies/{sid}/modes/members/accept-all", {})
    # stack
    if stack:
        r = await c.post(f"/api/studies/{sid}/stack/auto-place", json={})
        if r.status_code == 200:
            await c.post(f"/api/studies/{sid}/stack/approve", json={})
    # ground stations
    for gs in ("svalbard", "kiruna"):
        await c.post(f"/api/studies/{sid}/ground-stations", json={"kb_station_id": gs})
    # functions + allocations
    fn = lambda **b: _post(c, f"/api/functions/?study_id={sid}", b)  # noqa: E731
    root = await fn(name="Provide Earth imagery", level=0)
    tree = {
        "Acquire images": ("Imager", ["Point the imager", "Expose and read out"]),
        "Provide power": ("EPS", ["Generate power", "Store energy", "Distribute power"]),
        "Communicate with ground": ("S-band transceiver", ["Downlink payload data", "Receive telecommands"]),
        "Control attitude": ("Reaction wheel", ["Determine attitude", "Actuate attitude"]),
        "Manage data": ("OBC", ["Store payload data", "Handle telecommands"]),
    }
    alloc_leaf = {"Generate power": "Solar wings", "Store energy": "Battery", "Distribute power": "EPS",
                  "Determine attitude": "Star tracker", "Actuate attitude": "Reaction wheel",
                  "Downlink payload data": "S-band transceiver", "Store payload data": "OBC",
                  "Handle telecommands": "OBC", "Expose and read out": "Imager"}
    for mid, (_, leaves) in tree.items():
        f = await fn(name=mid, parent_id=root["id"], level=1)
        for leaf in leaves:
            lf = await fn(name=leaf, parent_id=f["id"], level=2, is_leaf=True)
            if leaf in alloc_leaf:
                await _post(c, f"/api/functions/{lf['id']}/allocate", {"element_id": out[alloc_leaf[leaf]]["id"], "layer": "SA"})
    # requirements
    reqs = [
        ("MR-001", "mission", None, "The mission shall image any point between ±70° latitude at 5 m GSD.", "A"),
        ("SR-001", "system", "MR-001", "The spacecraft shall downlink 2 GB of payload data per day.", "A"),
        ("SR-002", "system", "MR-001", "The spacecraft shall point the imager with 0.1° accuracy (3σ).", "T"),
        ("SR-003", "system", None, "The spacecraft mass shall not exceed 12 kg.", "I"),
        ("SS-PWR-001", "subsystem", "SR-001", "The EPS shall provide 28.8 V unregulated to the PCDU.", "T"),
        ("SS-COM-001", "subsystem", "SR-001", "The transceiver shall support 125 kbit/s S-band downlink.", None),
    ]
    rid: dict[str, str] = {}
    for code, level, parent, text, vm in reqs:
        body = {"study_id": sid, "level": level, "code": code, "text": text, "parent_id": rid.get(parent or ""),
                "verification_method": vm}
        r = await c.post("/api/requirements/", json={k: v for k, v in body.items() if v is not None})
        assert r.status_code == 200, r.text
        rid[code] = r.json()["id"]
    if verification:
        await c.post(f"/api/studies/{sid}/analyses/vv/run")
    # risks
    for desc, lk, cq, mit in (("Star tracker blinding during imaging", 3, 4, "Keep-out cone in the pointing plan"),
                              ("Battery capacity fade beyond 2 years", 2, 3, ""),
                              ("S-band licence delayed", 4, 4, "File ITU API early")):
        await _post(c, f"/api/studies/{sid}/risks", {"description": desc, "likelihood": lk, "consequence": cq,
                                                      "mitigation": mit})
    return out
