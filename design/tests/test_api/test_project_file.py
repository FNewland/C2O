"""Project file Save / Load (routers/project_io.py, services/project_file.py).

A richly populated EOSAT-1 study (diagram_seed + every other kind of study state: seats,
pending changes, gate review and baseline, design run, mission simulation with its series file,
logbook entry, Pugh trade, risks, custom component, layout coordinates, option, parameters,
CDR database, FDIR proposals and heaters, function ports and exchanges, trace links, legacy
session tables …) is exported, imported and exported again: both exports must be identical once
ids are mapped, no study-owned row may be missing from the file, two imports must give two
independent studies, and the endpoints the Workbench tabs call must answer the same for the
original and the imported study. The link proposer and the interface-requirement generator are
switched ON for the whole module, so any re-proposal during import would show as duplicates.
"""
from __future__ import annotations

import json

import pytest

from tests.test_api.diagram_seed import seed_eosat

INSTRUCTOR = "prof@c2o.live"


def iap(email: str, name: str, confirm: bool = False) -> dict:
    h = {"X-Goog-Authenticated-User-Email": f"accounts.google.com:{email}", "X-C2O-Name": name}
    if confirm:
        h["X-C2O-Confirm-Review"] = "1"
    return h


PROF = iap(INSTRUCTOR, "Prof")
TL = iap("tl@c2o.live", "Alex")
PWR = iap("power@c2o.live", "Sam")


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("SPACECDF_AUTO_IRD", "1")
    monkeypatch.setenv("SPACECDF_AUTO_PROPOSE", "1")
    monkeypatch.setenv("SPACECDF_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("SMO_LOGBOOK_DIR", str(tmp_path / "logbook"))
    monkeypatch.setenv("SPACECDF_INSTRUCTORS", INSTRUCTOR)
    monkeypatch.delenv("SMO_INSTRUCTORS", raising=False)
    from spacecdf_server.routers import elements, stack
    from spacecdf_server.seats import store
    stack.reset_stack_cache()
    store.reset_memory()
    elements._budget_allocations.clear()
    yield
    stack.reset_stack_cache()
    store.reset_memory()
    elements._budget_allocations.clear()


async def _ok(r, codes=(200, 201)):
    assert r.status_code in codes, f"{r.request.method} {r.request.url}: {r.status_code} {r.text[:400]}"
    return r.json()


async def _legacy_rows(sid: str, element_id: str) -> None:
    """The legacy WebSocket-session tables have no live UI: write one row of each directly."""
    from spacecdf_server.db.engine import get_session_factory
    from spacecdf_server.db.models import (
        ChangeEventRow, DesignStateSnapshotRow, ElementBaselineRow, ExportRow, OptimizationRunRow,
        ParameterEditRow, SessionRow,
    )
    async with get_session_factory()() as s:
        s.add(SessionRow(id=f"ses{sid}", study_id=sid, name="Concurrent session 1", owner_label="Prof"))
        await s.flush()
        s.add(ChangeEventRow(id=f"ce-{sid}-0001-aaaa-bbbb-cccc", session_id=f"ses{sid}", kind="parameter_edit",
                             actor_id="power_engineer", target_id=f"{element_id}.mass_kg", target_kind="element",
                             old_value="1.0", new_value="1.2"))
        s.add(ParameterEditRow(id=f"pe{sid}0001", session_id=f"ses{sid}", position_id="power_engineer",
                               param_path="power.mass_kg", old_value="1.0", new_value="1.2", source="user"))
        await s.flush()
        snap1 = DesignStateSnapshotRow(session_id=f"ses{sid}", study_id=sid, version=1, state_json="{}", name="s1")
        s.add(snap1)
        await s.flush()
        snap2 = DesignStateSnapshotRow(session_id=f"ses{sid}", study_id=None, version=2, state_json="{}",
                                       name="s2", parent_snapshot_id=snap1.id,
                                       last_change_event_id=f"ce-{sid}-0001-aaaa-bbbb-cccc")
        s.add(snap2)
        await s.flush()
        s.add(OptimizationRunRow(session_id=f"ses{sid}", study_id=sid, initial_snapshot_id=snap2.id,
                                 objective="min_mass", best_y=float("inf")))
        s.add(ExportRow(session_id=f"ses{sid}", kind="docx", path="/tmp/x.docx"))
        s.add(ElementBaselineRow(baseline_name="SRR", study_id=sid, element_id=element_id,
                                 snapshot_json={"id": element_id, "mass_kg": 1.0}))
        await s.commit()


async def build_rich_study(c, monkeypatch) -> tuple[str, dict]:
    """EOSAT-1 with something in every study-owned table."""
    sid = (await _ok(await c.post("/api/studies/", json={
        "requirements": {"name": "EOSAT-1", "spacecraft_class": "nano",
                         "orbit": {"orbit_type": "sso", "altitude_km": 590, "inclination_deg": 97.7, "ltan": "10:30"}},
        "mission_need": {"problem_statement": "Monitor Arctic sea ice", "operational_context": "Polar orbit",
                         "objectives": [{"id": "OBJ-1", "text": "Image sea ice weekly", "priority": "primary"}],
                         "stakeholders": [{"name": "CSA", "role": "sponsor", "key_need": "Data"}]},
    })))["id"]
    parts = await seed_eosat(c, sid)
    sc, eps, obc = parts["sc"], parts["EPS"], parts["OBC"]

    # custom component (no KB id) with layout coordinates, a collapsed block, a budget allocation
    custom = await _ok(await c.post(f"/api/elements/?study_id={sid}", json={
        "name": "Custom deorbit sail", "element_type": "component", "parent_id": parts["sub:structure"]["id"],
        "subsystem_domain": "structure", "mass_kg": 0.35, "power_avg_w": 0.0, "cost_nre_keur": 40.0,
        "manufacturer": "In-house", "part_number": "DS-1", "trl": 5, "performance": {"area_m2": 1.5}}))
    custom = await _ok(await c.patch(f"/api/elements/{custom['id']}", json={
        "version": custom["version"], "diagram_x": 120.5, "diagram_y": -40.0}))
    sub = parts["sub:payload"]
    await _ok(await c.patch(f"/api/elements/{sub['id']}", json={
        "version": (await _ok(await c.get(f"/api/elements/{sub['id']}")))["version"],
        "diagram_collapsed": True, "diagram_x": 10.0, "diagram_y": 20.0}))
    await _ok(await c.post(f"/api/elements/{sc['id']}/allocations", json={
        "budget_type": "mass", "allocation_value": 12.0, "unit": "kg", "source": "requirement", "rationale": "SR-003"}))

    # option + parameter overrides, one option-scoped
    opt = await _ok(await c.post(f"/api/studies/{sid}/options", json={"name": "Bigger battery"}))
    await _ok(await c.put(f"/api/elements/{eps['id']}/parameters/mass_kg", json={"manual_value": 0.2, "unit": "kg"}))
    await _ok(await c.put(f"/api/elements/{eps['id']}/parameters/mass_kg?option_id={opt['id']}",
                          json={"manual_value": 0.3, "unit": "kg"}))

    # function ports + an exchange realised by an interface; a realization; a trace relation
    funcs = await _ok(await c.get(f"/api/studies/{sid}/functions"))
    f1, f2 = funcs[1], funcs[2]
    p1 = await _ok(await c.post(f"/api/functions/{f1['id']}/ports", json={"name": "img out", "direction": "out"}))
    p2 = await _ok(await c.post(f"/api/functions/{f2['id']}/ports", json={"name": "img in", "direction": "in"}))
    ifaces = await _ok(await c.get(f"/api/studies/{sid}/interfaces"))
    acc = [i for i in ifaces if i.get("status") == "accepted"]
    await _ok(await c.post(f"/api/functional-exchanges/?study_id={sid}", json={
        "name": "image data", "from_port_id": p1["id"], "to_port_id": p2["id"],
        "realized_by_interface_id": acc[0]["id"]}))
    await _ok(await c.post(f"/api/realizations/?study_id={sid}", json={
        "source_kind": "function", "source_id": f1["id"], "target_kind": "function", "target_id": f2["id"]}))
    reqs = await _ok(await c.get(f"/api/requirements/tree?study_id={sid}"))
    sr = next(r for r in reqs if r.get("code") == "SR-001")
    await _ok(await c.post(f"/api/relations/?study_id={sid}", json={
        "kind": "satisfies", "source_kind": "element", "source_id": obc["id"], "target_kind": "requirement",
        "target_id": sr["id"], "rationale": "stores the data"}))
    # an interface agreement (IF-05)
    await _ok(await c.post(f"/api/studies/{sid}/interfaces/{acc[0]['id']}/agreement", json={"side": "both"}))
    # verification item edited
    vis = await _ok(await c.get(f"/api/studies/{sid}/verification-items"))
    vlist = vis.get("items") if isinstance(vis, dict) else vis
    await _ok(await c.patch(f"/api/verification-items/{vlist[0]['id']}", json={
        "status": "passed", "evidence_ref": "TR-001", "notes": "thermal vacuum"}))

    # CDR database, FDIR/heater/risk proposals (one heater accepted, one monitor accepted)
    await _ok(await c.post(f"/api/studies/{sid}/cdr/propose", json={}))
    await _ok(await c.post(f"/api/studies/{sid}/cdr/accept-all", json={}))
    await _ok(await c.post(f"/api/studies/{sid}/design-rules/run"))
    props = (await _ok(await c.get(f"/api/studies/{sid}/design-rules/proposals")))["proposals"]
    for kind in ("heater", "monitor"):
        p = next((x for x in props if x["kind"] == kind and x["status"] == "suggested"), None)
        if p:
            await _ok(await c.post(f"/api/studies/{sid}/design-rules/proposals/{p['id']}/accept"))

    # trades, design run, mission simulation (series file on disk), gate review + baseline
    await _ok(await c.put(f"/api/studies/{sid}/trades/pugh", json={
        "state": {"criteria": [{"id": "c1", "name": "Mass", "weight": 3}], "options": ["A", "B"], "datum": "A",
                  "scores": {"B": {"c1": 1}}}}))
    await _ok(await c.post(f"/api/design/{sid}/run"))
    await _ok(await c.post(f"/api/studies/{sid}/analyses/mission_simulation/run"))
    await _ok(await c.put(f"/api/studies/{sid}/gate-profile", json={"profile": "c2o_3gate"}))
    gates = await _ok(await c.get(f"/api/studies/{sid}/gates"))
    g0 = gates["gates"][0]["id"]
    # the seed does not satisfy every must-pass item: let the evaluator say ready, to get a baseline
    from spacecdf_server.routers import gates as gates_router
    real = gates_router._evaluate
    monkeypatch.setattr(gates_router, "_evaluate", lambda ctx, pg: {**real(ctx, pg), "ready": True})
    await _ok(await c.post(f"/api/studies/{sid}/gates/{g0}/review", json={"action": "start", "note": "go"}))
    await _ok(await c.post(f"/api/studies/{sid}/gates/{g0}/review", json={"action": "pass", "note": "passed"}))
    monkeypatch.setattr(gates_router, "_evaluate", real)

    # logbook entry tagged with the study (this client's cookie)
    await _ok(await c.post("/api/logbook/entries", json={
        "kind": "decision", "text": f"Chose S-band for {sc['id']}", "context": {"study_id": sid, "where": "decide"}}))

    await _legacy_rows(sid, eps["id"])

    # seats last (writes need a seat afterwards): preset, claims, a pending cross-seat edit
    await _ok(await c.post(f"/api/studies/{sid}/team/preset", json={"team_size": "6"}, headers=PROF))
    await _ok(await c.post(f"/api/studies/{sid}/team/claim", json={"seats": ["team_leader", "systems_engineer"]},
                           headers=TL))
    await _ok(await c.post(f"/api/studies/{sid}/team/claim", json={"seats": ["power_engineer", "thermal_engineer"]},
                           headers=PWR))
    el = await _ok(await c.get(f"/api/elements/{eps['id']}"))
    await _ok(await c.patch(f"/api/elements/{eps['id']}", json={"version": el["version"], "mass_kg": 0.25},
                            headers={**TL, "X-C2O-Confirm-Review": "1"}), codes=(202,))
    return sid, parts


# ─── comparison helpers ──────────────────────────────────────────────────────

#: values that legitimately differ after an import: hashes over ids (re-stamped), int keys
_VOLATILE_COLS = {"inputs_hash"}


def _int_cols() -> dict[str, set[str]]:
    from spacecdf_server.services import project_file as pf
    out: dict[str, set[str]] = {}
    tables = {t.name: t for t in pf._tables()}
    for name, t in tables.items():
        cols = set()
        if pf._int_pk(t):
            cols.add(pf._int_pk(t))
        for c, (ref, _) in pf._fk_targets(t).items():
            if pf._int_pk(tables[ref]):
                cols.add(c)
        cols |= {c for (tn, c) in pf.UNDECLARED_INT_REFS if tn == name}
        out[name] = cols
    return out


def _strip(v):
    if isinstance(v, dict):
        return {k: _strip(x) for k, x in v.items() if k not in _VOLATILE_COLS}
    if isinstance(v, list):
        return [_strip(x) for x in v]
    return v


def _canon_tables(doc: dict, id_map: dict[str, str] | None = None) -> dict[str, list[str]]:
    from spacecdf_server.services.project_file import IdMap
    m = None
    if id_map is not None:
        m = IdMap("", "")
        m.ids = dict(id_map)
    ints = _int_cols()
    out = {}
    for name, rows in doc["tables"].items():
        canon = []
        for r in rows:
            r = {k: v for k, v in r.items() if k not in ints.get(name, set())}
            if m is not None:
                r = m.value(r)
            canon.append(json.dumps(_strip(r), sort_keys=True))
        out[name] = sorted(canon)
    return out


def _all_pks(doc: dict) -> set[str]:
    from spacecdf_server.services import project_file as pf
    tables = {t.name: t for t in pf._tables()}
    out = set()
    for name, rows in doc["tables"].items():
        t = tables[name]
        if pf._int_pk(t):
            continue
        pk = pf._pk(t)
        out |= {r[pk] for r in rows}
    return out


@pytest.fixture()
async def rich(client, db_factory, monkeypatch):
    sid, parts = await build_rich_study(client, monkeypatch)
    return sid, parts


async def _export(c, sid) -> dict:
    r = await c.get(f"/api/studies/{sid}/export")
    assert r.status_code == 200, r.text[:400]
    assert "attachment" in r.headers.get("content-disposition", "")
    return r.json()


async def _import(c, doc, *, id_map=True) -> dict:
    return await _ok(await c.post(f"/api/studies/import{'?include_id_map=1' if id_map else ''}", json=doc))


# ─── tests ───────────────────────────────────────────────────────────────────

async def test_every_table_is_classified():
    from spacecdf_server.services import project_file as pf
    assert pf.unclassified_tables() == []
    assert "studies" in pf.study_tables() and "cdr_rows" in pf.study_tables()
    assert "function_ports" in pf.study_tables() and "mode_elements" in pf.study_tables()


async def test_round_trip_is_exact(client, rich):
    sid, _ = rich
    a = await _export(client, sid)
    assert a["format"] == "spacecdf-project" and a["version"] == 2
    # the seed touched every study-owned table
    empty = [t for t, rows in a["tables"].items() if not rows]
    assert empty == [], f"seed left tables empty: {empty}"
    assert a["files"] and a["logbook"] and a["globals"]["parameter_definitions"]

    res = await _import(client, a)
    new = res["id"]
    assert new != sid and not res["warnings"]
    b = await _export(client, new)

    # 1. same tables, same row counts, same values once ids are mapped
    assert set(a["tables"]) == set(b["tables"])
    for t in a["tables"]:
        assert len(a["tables"][t]) == len(b["tables"][t]), t
    ca, cb = _canon_tables(a, res["id_map"]), _canon_tables(b)
    for t in ca:
        assert ca[t] == cb[t], f"table {t} differs after the round trip"
    # 2. every id is new; nothing in B points at A
    pka, pkb = _all_pks(a), _all_pks(b)
    assert not (pka & pkb)
    blob_b = json.dumps(b["tables"])
    for old in pka:
        if len(old) >= 8:
            assert old not in blob_b, f"old id {old} still referenced"
    # 3. files and logbook travel with the study
    assert len(b["files"]) == len(a["files"])
    assert [e["text"] for e in b["logbook"]] == [_map_text(e["text"], res["id_map"]) for e in a["logbook"]]
    assert all(e["context"]["study_id"] == new for e in b["logbook"])
    # 4. study object
    assert b["study"]["name"] == a["study"]["name"] == "EOSAT-1"
    # 5. inf / NaN (legacy optimiser rows) survive the JSON file and come back as floats
    assert a["tables"]["optimization_runs"][0]["best_y"] == {"__float__": "inf"}
    assert b["tables"]["optimization_runs"][0]["best_y"] == {"__float__": "inf"}
    # 6. no study-owned row is missing: scan EVERY row of EVERY table; a row that mentions the
    #    study or one of its exported ids must be in the export (catches undeclared links)
    await _assert_nothing_missing(sid, a)
    await _assert_nothing_missing(new, b)
    # 7. the UI state the browser adds (breadcrumb) comes back with the new ids
    sc_id = next(e["id"] for e in a["tables"]["design_elements"] if e["element_type"] == "system"
                 and e["segment"] == "space")
    doc = dict(a, ui={"breadcrumb": [{"id": sc_id, "name": "EOSAT-1", "type": "system"}]})
    res2 = await _import(client, doc)
    crumb = res2["ui"]["breadcrumb"][0]["id"]
    assert crumb == res2["id_map"][sc_id]
    assert (await _ok(await client.get(f"/api/elements/{crumb}")))["study_id"] == res2["id"]


async def _assert_nothing_missing(sid: str, a: dict) -> None:
    from sqlalchemy import select
    from spacecdf_server.db.engine import get_session_factory
    from spacecdf_server.services import project_file as pf
    ids = _all_pks(a) | {sid}
    exported = {name: {json.dumps(r, sort_keys=True, default=str) for r in rows} for name, rows in a["tables"].items()}
    missing = []
    async with get_session_factory()() as s:
        for t in pf._tables():
            if t.name in pf.GLOBAL_TABLES:
                continue
            for r in (await s.execute(select(t))).mappings().all():
                vals = {str(v) for v in r.values() if isinstance(v, str)}
                if not (vals & ids):
                    continue
                if t.name not in exported:
                    missing.append((t.name, dict(r)))
                    continue
                enc = json.dumps(pf._enc(dict(r)), sort_keys=True, default=str)
                if enc not in exported[t.name] and t.name != "studies":
                    missing.append((t.name, dict(r)))
    assert not missing, missing[:3]


def _map_text(s: str, id_map: dict) -> str:
    from spacecdf_server.services.project_file import IdMap
    m = IdMap("", "")
    m.ids = dict(id_map)
    return m.str(s)


async def test_import_twice_gives_independent_studies(client, rich):
    sid, _ = rich
    doc = await _export(client, sid)
    r1, r2 = await _import(client, doc), await _import(client, doc)
    assert len({sid, r1["id"], r2["id"]}) == 3
    assert r1["counts"] == r2["counts"]
    assert not (set(r1["id_map"].values()) & set(r2["id_map"].values()))
    # change one copy: the other and the original do not move
    els1 = await _ok(await client.get(f"/api/studies/{r1['id']}/elements"))
    mission = next(e for e in els1 if e["element_type"] == "mission")
    await _ok(await client.patch(f"/api/elements/{mission['id']}", json={"version": mission["version"],
                                                                         "name": "Renamed"}, headers=TL))
    names2 = {e["name"] for e in await _ok(await client.get(f"/api/studies/{r2['id']}/elements"))}
    names0 = {e["name"] for e in await _ok(await client.get(f"/api/studies/{sid}/elements"))}
    assert "Renamed" not in names2 and "Renamed" not in names0
    await _ok(await client.delete(f"/api/studies/{r2['id']}", headers=PROF))
    assert len(await _ok(await client.get(f"/api/studies/{r1['id']}/elements"))) == len(els1)


# endpoints the Workbench tabs call (SPACECDF_MAP.md §2.2-2.3), with keys that are computed live
WORKBENCH = [
    "/api/studies/{sid}",
    "/api/studies/{sid}/elements",
    "/api/studies/{sid}/interfaces",
    "/api/requirements/tree?study_id={sid}",
    "/api/studies/{sid}/allocations",
    "/api/studies/{sid}/functions/tree",
    "/api/studies/{sid}/modes",
    "/api/studies/{sid}/electrical",
    "/api/studies/{sid}/cdr",
    "/api/studies/{sid}/stack",
    "/api/studies/{sid}/risks",
    "/api/studies/{sid}/trades/pugh",
    "/api/studies/{sid}/gates",
    "/api/studies/{sid}/verification-items",
    "/api/studies/{sid}/options",
    "/api/studies/{sid}/relations",
    "/api/studies/{sid}/exchange-items",
    "/api/studies/{sid}/heaters",
    "/api/studies/{sid}/design-rules/proposals",
    "/api/studies/{sid}/interface-requirements",
    "/api/studies/{sid}/team",
    "/api/studies/{sid}/parameters",
    "/api/studies/{sid}/diagrams/product_tree",
    "/api/studies/{sid}/diagrams/n2",
]


PRESENCE_KEYS = frozenset({"active_seat", "last_action", "last_action_at", "status", "last_seen", "online"})


#: endpoints whose lists the server orders by keys that contain ids (``target_key``, mode id):
#: new ids sort differently, so their nested lists are compared as sets
ORDERED_BY_IDS = ("/modes", "/design-rules/proposals")


def _deep_sorted(v):
    if isinstance(v, dict):
        return {k: _deep_sorted(x) for k, x in v.items()}
    if isinstance(v, list):
        items = [_deep_sorted(x) for x in v]
        return sorted(items, key=lambda x: json.dumps(x, sort_keys=True))
    return v


def _canon_api(v, extra_drop: frozenset = frozenset()):
    """Order-insensitive at the top level; volatile keys dropped."""
    drop = {"inputs_hash", "current_hash", "now", "generated_at", "server_time", "age_s", "idle_s",
            "status_age_s"} | set(extra_drop)

    def clean(x):
        if isinstance(x, dict):
            return {k: clean(y) for k, y in x.items() if k not in drop}
        if isinstance(x, list):
            return [clean(y) for y in x]
        return x
    v = clean(v)
    if isinstance(v, list):
        return sorted(json.dumps(x, sort_keys=True) for x in v)
    return json.dumps(v, sort_keys=True)


async def test_workbench_endpoints_answer_the_same(client, rich):
    sid, _ = rich
    doc = await _export(client, sid)
    # live stale flags of the original, before its caches are re-read below
    an_a = {x["analysis"]: x.get("stale") for x in await _ok(await client.get(f"/api/studies/{sid}/analyses"))}
    res = await _import(client, doc)
    new = res["id"]
    # the imported study is read from the database; read the original the same way (as after a
    # restart), so cache-only keys such as an element's KB ``category`` copy do not count
    from spacecdf_server.services.project_file import reload_study_caches
    await reload_study_caches(sid)
    diffs = []
    for url in WORKBENCH:
        ra = await client.get(url.format(sid=sid), headers=PROF)
        rb = await client.get(url.format(sid=new), headers=PROF)
        assert ra.status_code == rb.status_code == 200, (url, ra.status_code, rb.status_code, rb.text[:200])
        a_mapped = _map_value(ra.json(), res["id_map"])
        # seat presence (heartbeats, active seat, idle status) is memory-only by design
        xd = PRESENCE_KEYS if url.endswith("/team") else frozenset()
        va, vb = a_mapped, rb.json()
        if url.endswith(ORDERED_BY_IDS):
            va, vb = _deep_sorted(va), _deep_sorted(vb)
        ca, cb = _canon_api(va, xd), _canon_api(vb, xd)
        if ca != cb:
            diffs.append((url, _first_diff(ca, cb)))
    assert not diffs, "\n".join(f"{u}: {d}" for u, d in diffs)
    # analyses: same runs, same stale flags as the original had live (fresh runs are re-stamped)
    an_b = {x["analysis"]: x.get("stale") for x in await _ok(await client.get(f"/api/studies/{new}/analyses"))}
    assert an_a == an_b and an_a
    # the rules recognise the imported rows as their own: proposing again on the original and on
    # the copy leaves both with the same rows (a re-proposal of imported rows would add duplicates)
    for prop, get in (("/interfaces/propose", "/interfaces"), ("/electrical/propose", "/electrical"),
                      ("/cdr/propose", "/cdr")):
        shapes = []
        for s_id in (sid, new):
            await _ok(await client.post(f"/api/studies/{s_id}{prop}", json={}, headers=PROF))
            shapes.append(_row_shape(await _ok(await client.get(f"/api/studies/{s_id}{get}", headers=PROF))))
        assert shapes[0] == shapes[1], prop
    # no duplication anywhere: the proposer and the IRD generator are on in this module
    for url in ("/api/studies/{sid}/interfaces", "/api/requirements/tree?study_id={sid}"):
        na = len(await _ok(await client.get(url.format(sid=sid))))
        nb = len(await _ok(await client.get(url.format(sid=new))))
        assert na == nb, url
    # requirement parents point inside the new study
    reqs = await _ok(await client.get(f"/api/requirements/tree?study_id={new}"))
    ids = {r["id"] for r in reqs}
    assert any(r.get("parent_id") for r in reqs)
    assert all(r["parent_id"] in ids for r in reqs if r.get("parent_id"))


def _first_diff(a, b):
    """A short description of the first difference (for the assertion message)."""
    if isinstance(a, str) and isinstance(b, str) and a.startswith(("{", "[")):
        a, b = json.loads(a), json.loads(b)
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                return f"{k}: " + str(_first_diff(a.get(k), b.get(k)))
        return None
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{len(a)} vs {len(b)} items"
        if a and all(isinstance(x, dict) and "id" in x for x in a + b):
            bb = {y["id"]: y for y in b}
            for x in a:
                if x != bb.get(x["id"]):
                    return f"[id={x['id']}] " + str(_first_diff(x, bb.get(x["id"]) or {}))
            return None
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return f"[{i}] " + str(_first_diff(x, y))
        return None
    return f"{str(a)[:150]} != {str(b)[:150]}"


def _row_shape(v) -> dict:
    """Rows per collection and status: what a duplicate proposal would change."""
    from collections import Counter
    if isinstance(v, list):
        return {"": dict(Counter(str(x.get("status")) for x in v if isinstance(x, dict)))}
    out = {}
    for k, x in (v or {}).items():
        if isinstance(x, list) and x and all(isinstance(y, dict) and "id" in y for y in x):
            out[k] = dict(Counter(str(y.get("status")) for y in x))
    return out


def _map_value(v, id_map):
    from spacecdf_server.services.project_file import IdMap
    m = IdMap("", "")
    m.ids = dict(id_map)
    return m.value(v)


async def test_v1_browser_save_file_is_converted_without_duplicates(client, db_factory):
    """The old browser-built Save file: converted, parents remapped, nothing re-proposed."""
    sid, parts = await build_rich_study_small(client)
    els = await _ok(await client.get(f"/api/studies/{sid}/elements"))
    ifs = await _ok(await client.get(f"/api/studies/{sid}/interfaces"))
    reqs = await _ok(await client.get(f"/api/requirements/tree?study_id={sid}"))
    study = await _ok(await client.get(f"/api/studies/{sid}"))
    v1 = {"studyId": sid, "elements": els, "interfaces": ifs, "requirements": reqs,
          "allocations": [], "studyMetadata": study, "riskRegister": study["risk_register"], "pughMatrix": {},
          "uiState": {"breadcrumb": [{"id": parts["sc"]["id"], "name": "EOSAT-1"}]}}
    res = await _import(client, v1)
    new = res["id"]
    assert res["converted_from"] == 1
    assert len(await _ok(await client.get(f"/api/studies/{new}/elements"))) == len(els)
    assert len(await _ok(await client.get(f"/api/studies/{new}/interfaces"))) == len(ifs)
    reqs2 = await _ok(await client.get(f"/api/requirements/tree?study_id={new}"))
    assert len(reqs2) == len(reqs)
    ids2 = {r["id"] for r in reqs2}
    assert all(r["parent_id"] in ids2 for r in reqs2 if r.get("parent_id"))
    assert sum(1 for r in reqs2 if r.get("parent_id")) == sum(1 for r in reqs if r.get("parent_id"))
    s2 = await _ok(await client.get(f"/api/studies/{new}"))
    assert s2["name"] == study["name"] and len(s2["risk_register"]) == len(study["risk_register"])
    assert s2["requirements"]["orbit"]["altitude_km"] == 590
    assert res["ui"]["breadcrumb"][0]["id"] == res["id_map"][parts["sc"]["id"]]
    # the old "Full Study Export" (no studyMetadata) opens too
    res2 = await _import(client, {"studyId": sid, "elements": els, "interfaces": ifs, "requirements": reqs})
    assert len(await _ok(await client.get(f"/api/studies/{res2['id']}/elements"))) == len(els)


async def build_rich_study_small(c) -> tuple[str, dict]:
    sid = (await _ok(await c.post("/api/studies/", json={
        "requirements": {"name": "EOSAT-1", "orbit": {"orbit_type": "sso", "altitude_km": 590}}})))["id"]
    parts = await seed_eosat(c, sid, stack=False, verification=False)
    return sid, parts


async def test_bad_files_are_refused(client, db_factory):
    r = await client.post("/api/studies/import", content=b"not json", headers={"content-type": "application/json"})
    assert r.status_code == 400
    r = await client.post("/api/studies/import", json={"format": "something-else"})
    assert r.status_code == 400 and "not a SpaceCDF project" in r.text
    r = await client.post("/api/studies/import", json={"format": "spacecdf-project", "version": 99, "tables": {}})
    assert r.status_code == 400 and "newer SpaceCDF" in r.text
    r = await client.get("/api/studies/nope/export")
    assert r.status_code == 404
