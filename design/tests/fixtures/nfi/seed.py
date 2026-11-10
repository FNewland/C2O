"""Staged API seed of the Northern Fire and Ice teaching mission (W0.4).

Builds the study through the public HTTP API only, so the same code runs on the in-process test
client (``httpx.AsyncClient`` over ``ASGITransport``) and against a running server (videos,
screenshots, the textbook number extractor)::

    from tests.fixtures.nfi.seed import seed_nfi
    s = await seed_nfi(client, "S2")      # -> NfiSeed(study_id, elements, requirements, modes, report)

Stages (VIDEO_REVIEW §2.4; each includes the previous one):

=====  ==========================================================================================
S0     the study, created solo (no seats) with the full mission definition and mission need
       (``mission.yaml``: what the wizard plus the mission editor produce)
S1     + product tree (mission, segments, spacecraft, 8 subsystems, 4 ground stations, mission
       control, launch segment) + the objective requirements OBJ-* and the mission-level rows
S2     + equipment (``equipment.yaml``: mass, ON power, quantity, TRL, maturity category, KB id)
       + modes (template patched to ``modes.yaml``, Night SWIR and Sail deploy added, shares of
       orbit, the mode x unit power matrix, the extra transitions) + links, electrical and data
       proposed and accepted
S3     + every requirement of ``requirements.yaml`` (216) + the risk register (``risks.yaml``)
S4     + CDR design model proposed and accepted, stack auto-placed and approved, analyses run
       (V&V, mission simulation, ground segment, physics)
=====  ==========================================================================================

Known gaps, each owned by a later work package (the seed grows with them):

* requirement levels ``stakeholder``/``segment``/``interface`` are posted as ``tool_level`` (W2.01);
  extra parents/objectives (``derives``/``traces``), priority, category, unit and source are not
  stored (W2.02/W2.03); requirements are created one by one, not by the bulk import (W2.04);
* housekeeping SIDs (``hk_sids.yaml``) are not loaded (W3.01-W3.04);
* trades (``trades.yaml``) are not loaded: the study holds one Pugh record (W6.01);
* link-budget cases (W4.04), licensing (W5.03), AIT (W8a), schedule (W11a) have no model yet.

The seed never writes a person's or an institution's name; the YAML files are the frozen
teaching baseline (``NUMBERS.yaml`` wins over every other file).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
STAGES = ("S0", "S1", "S2", "S3", "S4")

#: maturity of equipment.yaml -> margin_policy category (A/B 5 %, C 10 %, D 20 %)
MATURITY_CATEGORY = {"OTS": "A", "MOD": "C", "NEW": "D"}

#: short unit labels of modes.yaml -> element name in equipment.yaml (Radio RX + TX = one radio)
MODE_UNITS = {
    "OBC": "NanoMind A3200 (in P60 slot X3)",
    "EPS": "NanoPower P60 (Dock + ACU-200 + PDU-200)",
    "Battery heater": "NanoPower BP4 43 Wh (1P-4S, 12-16.8 V)",
    "ADCS unit": "CubeADCS Gen 2 (Core + 3x CW0017 + CR torquers + CubeStar)",
    "Sun sensor": "CubeSense Sun (fine sun sensor)",
    "GNSS": "NanoSense GPS Kit (OEM719 + TW1322)",
    "Radio RX": "Spacemanic Murgas UHF transceiver (401 TX / 450 RX, receive edge TBC)",
    "Radio TX": "Spacemanic Murgas UHF transceiver (401 TX / 450 RX, receive edge TBC)",
    "SWIR camera": "Alvium 1800 C-530 VSWIR (SWIR camera, 35 mm f/1.4, 1610/90 filter)",
    "VNIR camera": "Alvium 1800 C-1620m (VNIR camera, 50 mm f/2.4, 875/50 filter)",
    "Payload controller": "Payload controller (Raspberry Pi CM4 on custom carrier)",
    "Bench heater": "Kapton heater 2 W (payload bench survival)",
    "Drag sail": "NPC Spacemind ARTICA drag sail (config A, 2.1 m2, 0.35U)",
}


def load(name: str) -> Any:
    """One companion file of the fixture, parsed (``load("requirements")``, ``load("NUMBERS")``)."""
    return yaml.safe_load((HERE / f"{name}.yaml").read_text(encoding="utf-8"))


class SeedError(RuntimeError):
    pass


@dataclass
class NfiSeed:
    study_id: str = ""
    stage: str = "S0"
    elements: dict[str, dict] = field(default_factory=dict)     # name -> element
    requirements: dict[str, str] = field(default_factory=dict)  # code -> requirement id
    modes: dict[str, dict] = field(default_factory=dict)        # modes.yaml key -> mode
    risks: list[dict] = field(default_factory=list)
    report: dict[str, Any] = field(default_factory=lambda: {"calls": 0, "forbidden": 0, "seconds": {}})


class _Api:
    def __init__(self, client, seed: NfiSeed):
        self.c, self.s = client, seed

    async def call(self, method: str, url: str, body: Any = None, ok: tuple[int, ...] = (200, 201)) -> Any:
        r = await self.c.request(method, url, json=body if body is not None or method != "GET" else None)
        self.s.report["calls"] += 1
        if r.status_code == 403:
            self.s.report["forbidden"] += 1
        if r.status_code not in ok:
            raise SeedError(f"{method} {url}: {r.status_code} {r.text[:400]}")
        return r.json() if r.content else None

    async def post(self, url: str, body: Any = None, **kw) -> Any:
        return await self.call("POST", url, body if body is not None else {}, **kw)

    async def element(self, sid: str, **body) -> dict:
        return await self.post(f"/api/elements/?study_id={sid}", {k: v for k, v in body.items() if v is not None})


# ───────────────────────────────────────────────────────────────── stages

async def _s0(api: _Api, seed: NfiSeed) -> None:
    m = load("mission")
    wiz = m["wizard"]
    req = dict(m["mission_patch"]["requirements"])
    objectives = load("requirements")["objectives"]
    alts = wiz["step3_alternatives"]
    need = {
        "problem_statement": wiz["step1_problem"]["problem_statement"],
        "operational_context": wiz["step1_problem"]["operational_context"],
        "stakeholders": [{"id": f"SH-{i + 1:02d}", "name": s["name"], "role": s["role"], "needs": [s["need"]]}
                         for i, s in enumerate(wiz["step2_stakeholders"])],
        "objectives": [{"id": o["id"], "text": o["text"], "priority": o["priority"],
                        "measurable_criterion": o.get("measure", "")} for o in objectives],
        "alternatives_considered": [{"id": f"ALT-{i + 1:02d}", "name": n,
                                     "decision": "selected" if n == alts["select"] else "rejected"}
                                    for i, n in enumerate(alts["expected_list"])],
        "selection_rationale": alts["rationale"],
        "conops_summary": m["mission_patch"]["mission_need"]["conops_summary"],
    }
    need["selected_alternative_id"] = next(a["id"] for a in need["alternatives_considered"]
                                           if a["decision"] == "selected")
    res = await api.post("/api/studies/", {"requirements": req, "mission_need": need, "team_size": None})
    seed.study_id = res["id"]
    st = await api.call("GET", f"/api/studies/{seed.study_id}")
    if len((st.get("mission_need") or {}).get("objectives") or []) != len(objectives):
        raise SeedError("mission need was not accepted by POST /api/studies/")


async def _s1(api: _Api, seed: NfiSeed) -> None:
    sid, eq, els = seed.study_id, load("equipment"), seed.elements
    mission = await api.element(sid, name="Northern Fire and Ice", element_type="mission")
    space = await api.element(sid, name="Space Segment", element_type="segment", parent_id=mission["id"], segment="space")
    ground = await api.element(sid, name="Ground Segment", element_type="segment", parent_id=mission["id"],
                               segment="ground", subsystem_domain="ground")
    launch = await api.element(sid, name="Launch Segment", element_type="segment", parent_id=mission["id"],
                               segment="launch")
    sc_def = eq["spacecraft"]
    sc = await api.element(sid, name=sc_def["name"], element_type="system", parent_id=space["id"],
                           performance=sc_def.get("properties"))
    els.update({"mission": mission, "space": space, "ground": ground, "launch": launch, "spacecraft": sc})
    for sub in sc_def["subsystems"]:
        els[sub["name"]] = await api.element(sid, name=sub["name"], element_type="subsystem", parent_id=sc["id"],
                                             subsystem_domain=sub["domain"], owner_position=sub.get("seat"),
                                             performance=sub.get("properties"))
    for st in eq["ground_segment"]["stations"]:
        await api.post(f"/api/studies/{sid}/ground-stations",
                       {"name": st["name"], "lat": st["lat"], "lon": st["lon"], "min_elevation_deg": 10,
                        "antenna_m": eq["ground_segment"]["properties_all"].get("antenna_diameter_m"),
                        "bands": ["UHF"]})
    for op in eq.get("operations") or []:
        els[op["name"]] = await api.element(sid, name=op["name"], element_type="system", parent_id=ground["id"],
                                            segment="ground", subsystem_domain="ground", description=op.get("note", ""))
    for ls in eq.get("launch_segment") or []:
        els[ls["name"]] = await api.element(sid, name=ls["name"], element_type="system", parent_id=launch["id"],
                                            segment="launch", in_scope=bool(ls.get("in_scope", False)),
                                            description=ls.get("note", ""))
    # objective requirements, then the mission-level rows
    for o in load("requirements")["objectives"]:
        await _post_requirement(api, seed, {"id": o["code"], "level": "mission", "type": "functional",
                                            "text": f"The mission shall {o['text'][0].lower()}{o['text'][1:]}",
                                            "rationale": o.get("measure"), "objectives": [o["id"]]})
    await _post_requirements(api, seed, lambda r: r["tool_level"] == "mission")


def _element_for(seed: NfiSeed, name: str | None) -> str | None:
    """Element id by element name (requirements.yaml ``subsystem``); None when the tree has no such
    element yet (Science Segment, Harness, Operations: W2.09)."""
    for e in seed.elements.values():
        if e.get("name") == name:
            return e["id"]
    return None


async def _post_requirement(api: _Api, seed: NfiSeed, r: dict) -> None:
    code = r["id"]
    parents = [p for p in (r.get("parents") or []) if p in seed.requirements]
    th = r.get("threshold") or {}
    body = {
        "id": f"{seed.study_id}:{code}"[:32], "study_id": seed.study_id, "code": code,
        "level": r.get("tool_level") or r.get("level") or "system", "text": r["text"],
        "rationale": r.get("rationale"), "req_type": r.get("type"),
        "parent_id": seed.requirements[parents[0]] if parents else None,
        "derived_from_requirement_id": seed.requirements[parents[0]] if parents else None,
        "objective_id": (r.get("objectives") or [None])[0],
        "verification_method": r.get("verification_method"),
        "verification_phase": r.get("verification_phase"),
        "responsible_position": r.get("owner_seat"),
        "element_id": _element_for(seed, r.get("subsystem")),
        "threshold_op": th.get("op"), "threshold_value": th.get("value"),
        "status": r.get("status") or "draft",
    }
    res = await api.post("/api/requirements/", {k: v for k, v in body.items() if v is not None})
    seed.requirements[code] = res["id"]


async def _post_requirements(api: _Api, seed: NfiSeed, which) -> None:
    data = load("requirements")
    rows = {r["id"]: r for r in data["requirements"]}
    for code in data["import_order"]:
        r = rows[code]
        if code not in seed.requirements and which(r):
            await _post_requirement(api, seed, r)


async def _accept_all_suggestions(api: _Api, sid: str) -> None:
    await api.post(f"/api/studies/{sid}/interfaces/propose")
    for i in await api.call("GET", f"/api/studies/{sid}/interfaces?status=suggested"):
        await api.call("PATCH", f"/api/interfaces/{i['id']}", {"status": "accepted"})
    await api.post(f"/api/studies/{sid}/electrical/propose")
    elec = await api.call("GET", f"/api/studies/{sid}/electrical")
    for kind in ("rails", "lines", "buses", "nodes"):
        for row in elec.get(kind) or []:
            if row.get("status") == "suggested":
                await api.call("PATCH", f"/api/studies/{sid}/electrical/{kind}/{row['id']}", {"status": "accepted"})


async def _s2(api: _Api, seed: NfiSeed) -> None:
    sid, eq = seed.study_id, load("equipment")
    for sub in eq["spacecraft"]["subsystems"]:
        parent = seed.elements[sub["name"]]
        for it in sub["items"]:
            perf = {}
            if it.get("maturity"):
                perf["maturity_category"] = MATURITY_CATEGORY[it["maturity"]]
            seed.elements[it["name"]] = await api.element(
                sid, name=it["name"], element_type="component", parent_id=parent["id"],
                subsystem_domain=sub["domain"], kb_component_id=None if it.get("custom") else it.get("kb"),
                quantity=int(it.get("qty") or 1), mass_kg=float(it.get("mass_kg") or 0.0),
                power_avg_w=float(it.get("power_w") or 0.0), trl=it.get("trl"),
                cost_recurring_keur=it.get("cost_keur"), owner_position=sub.get("seat"),
                performance=perf or None)
    await _accept_all_suggestions(api, sid)
    await _modes(api, seed)


async def _modes(api: _Api, seed: NfiSeed) -> None:
    sid, md = seed.study_id, load("modes")
    await api.post(f"/api/studies/{sid}/modes/template", {})
    have = {m.get("template_key"): m for m in (await api.call("GET", f"/api/studies/{sid}/modes"))["modes"]}
    for i, row in enumerate(md["modes"]):
        body = {"name": row["name"], "kind": row["kind"], "pointing": row["pointing"],
                "sunlit_only": bool(row["sunlit_only"]), "initial": bool(row["initial"]),
                "orbit_fraction": round(float(row["share_pct"]) / 100.0, 4), "order": i}
        if row["key"] in have:
            m = await api.call("PATCH", f"/api/studies/{sid}/modes/{have[row['key']]['id']}", body)
        else:
            if row["key"] == "eol":
                body["phase"] = "disposal"
            m = await api.post(f"/api/studies/{sid}/modes", body)
        seed.modes[row["key"]] = m
    for t in md.get("transitions_added") or []:
        await api.post(f"/api/studies/{sid}/mode-transitions",
                       {"from_mode_id": seed.modes[t["from"]]["id"], "to_mode_id": seed.modes[t["to"]]["id"],
                        "trigger": t["trigger"], "description": t.get("guard", "")})
    # the power matrix: every space unit in every mode, matrix value or 0 W
    await api.post(f"/api/studies/{sid}/modes/propose")
    units = md["units"]
    names = {e.get("name"): e for e in seed.elements.values()}
    comps = [e for e in seed.elements.values() if e.get("element_type") == "component"]
    for key, row in md["matrix_w"].items():
        per_el: dict[str, float] = {}
        for label, w in zip(units, row):
            el = names.get(MODE_UNITS[label])
            if el is None:
                raise SeedError(f"mode unit {label!r} has no element")
            per_el[el["id"]] = per_el.get(el["id"], 0.0) + float(w or 0.0)
        for e in comps:
            w = round(per_el.get(e["id"], 0.0), 4)
            await api.call("PUT", f"/api/studies/{sid}/modes/{seed.modes[key]['id']}/members/{e['id']}",
                           {"power_w_in_mode": w, "power_state": "nominal" if w > 0 else "off"})


async def _s3(api: _Api, seed: NfiSeed) -> None:
    await _post_requirements(api, seed, lambda r: True)
    for r in load("risks")["risks"]:
        res = await api.post(f"/api/studies/{seed.study_id}/risks", {
            "description": r["desc"], "category": r.get("cat", "Technical"), "likelihood": int(r["L"]),
            "consequence": int(r["C"]), "mitigation": r.get("mit", ""), "owner": r.get("owner", ""),
            "status": r.get("status", "open"), "source": str(r.get("src", ""))[:120]})
        seed.risks.append(res)


async def _s4(api: _Api, seed: NfiSeed) -> None:
    sid = seed.study_id
    await api.post(f"/api/studies/{sid}/cdr/propose")
    await api.post(f"/api/studies/{sid}/cdr/accept-all")
    r = await api.call("POST", f"/api/studies/{sid}/stack/auto-place", {}, ok=(200, 409, 422))
    if r and not r.get("detail"):
        await api.call("POST", f"/api/studies/{sid}/stack/approve", {}, ok=(200, 409, 422))
    for a in ("vv", "ground_segment", "physics", "mission_simulation"):
        await api.post(f"/api/studies/{sid}/analyses/{a}/run")


_STEPS = {"S0": _s0, "S1": _s1, "S2": _s2, "S3": _s3, "S4": _s4}


async def seed_nfi(client, stage: str = "S4") -> NfiSeed:
    """Build the Northern Fire and Ice study up to ``stage`` (S0..S4). Raises SeedError on any
    unexpected HTTP status; ``report`` counts the calls, 403 responses and seconds per stage."""
    stage = stage.upper()
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    seed = NfiSeed()
    api = _Api(client, seed)
    for s in STAGES[: STAGES.index(stage) + 1]:
        t0 = time.perf_counter()
        await _STEPS[s](api, seed)
        seed.report["seconds"][s] = round(time.perf_counter() - t0, 2)
        seed.stage = s
    return seed
