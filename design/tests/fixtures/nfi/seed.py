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
S3     + every requirement of ``requirements.yaml`` (v2: 302) + the risk register (``risks.yaml``)
S4     + CDR design model proposed and accepted, stack auto-placed and approved, analyses run
       (V&V, mission simulation, ground segment, physics); AIT model philosophy and test matrix,
       schedule settings (launch provided), milestones and WBS; the design loop re-run on the placed
       stack before the analyses and the link cases' earth-station values in the licensing
       record (wave 2, agent D)
=====  ==========================================================================================

Known gaps, each owned by a later work package (the seed grows with them):

* requirement levels ``stakeholder``/``segment``/``interface`` are posted as ``tool_level`` (W2.01);
  extra parents/objectives (``derives``/``traces``), priority, category, unit and source are not
  stored (W2.02/W2.03); requirements are created one by one, not by the bulk import (W2.04);
* housekeeping SIDs (``hk_sids.yaml``) are loaded at the end of S4 (W3: the rule-proposed SIDs are
  rejected, the baseline SIDs with their per-mode intervals, stores, profiles, service reports,
  framing and payload products are entered as user rows);
* W1.03 (end of S2): the "Sail deploy / end of life" mode is the template's disposal mode (kind
  ``disposal``), so the drag sail is powered there only;

Loaded by agent D (wave 1), each at the end of its stage: S0 the mission-need fields (success
criteria, alternative types; W1.06); S2 the mission phases from ``modes.yaml`` (W7.01) and the
eight link cases of NUMBERS.yaml ``links`` with the design cases applied (W4.04); S3 every trade of
``trades.yaml`` with its pairwise weights, links to requirements, risks and elements, the decision
and decision record of each (W6), the design loop (wave 2: MDR-EC-07 reads its results) and the MDR
review record: three RIDs and the chair's decision (W4.08).

The seed never writes a person's or an institution's name; the YAML files are the frozen
teaching baseline (``NUMBERS.yaml`` wins over every other file).

Wave 3, step 0 (v2 baseline, ``/home/claude/nfi/v2``): the requirements are imported by their own
``level`` (mission 68, segment 40, system 67, subsystem 115, interface 12) with the v2 fields; the
maturity classes of ``budgets.yaml`` (``mass.items``, ``power.units``) are laid over the equipment
by item name; the study holds the 20 % system margin through PDR (``budgets.yaml``
``margin_policy.adopted``). ``seed_nfi(client, stage, recording=True)`` (``python -m
tests.fixtures.nfi --recording``) builds the walkthrough's seed: the Licensing tab, the
allocation ledger and the negotiation records are left empty because they are filled on camera
(PI ruling); the tests and the example project use the full seed.

Named step functions of the wave-3 agents (each fills only its own; append-only inside a step,
never reorder; W0_SEAMS §9): S0 ``_s0_stakeholders`` (S); S1 ``_s1_functions``, ``_s1_bindings``
(R); S2 ``_s2_allocations`` (A), ``_s2_readiness`` (L), ``_s2_conops_scenarios`` (D); S3
``_s3_trades``, ``_s3_risks``, ``_s3_open_items`` (D), ``_s3_changes`` (L), ``_s3_validation``,
``_s3_assumptions`` (S), ``_s3_negotiations`` (H); S4 ``_s4_ait_v2`` (A).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
STAGES = ("S0", "S1", "S2", "S3", "S4")

#: maturity of equipment.yaml -> margin_policy category (A/B 5 %, C 10 %, D 20 %)
MATURITY_CATEGORY = {"OTS": "A", "MOD": "C", "NEW": "D"}
#: v2 maturity percentage of budgets.yaml (mass.items, power.units) -> margin_policy category
MATURITY_PCT_CATEGORY = {5: "A", 10: "C", 20: "D"}

#: v2 element ids (functions.yaml ``elements``, requirements.yaml ``allocation``) -> the name of
#: the element the seed creates (S1). GS, OPS, SCI and SCT have no element of their own in the
#: tool: the four stations are ground-station records of the Ground Segment, the operations team
#: is the Operations segment, the science data system and the science team are the Science
#: Segment. 3.R1 resolves these into relations.
ELEMENT_IDS = {
    "MIS": "Northern Fire and Ice",
    "SSEG": "Space Segment",
    "SC": "Northern Fire and Ice spacecraft",
    "PAY": "Payload",
    "EPS": "EPS",
    "AOCS": "AOCS",
    "COM": "Communications",
    "OBC": "On-Board Computer",
    "THM": "Thermal",
    "STR": "Structure",
    "DIS": "Disposal (drag sail)",
    "HAR": "Harness",
    "GSEG": "Ground Segment",
    "MCC": "Mission control centre (Ottawa, VPN to the remote sites)",
    "GS": "Ground Segment",
    "OPS": "Operations",
    "USEG": "Science Segment",
    "SCI": "Science Segment",
    "SCT": "Science Segment",
    "LSEG": "Launch Segment",
}

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
    from spacecdf_common.config.loader import read_yaml_cached  # parsed once, a fresh copy per call
    return read_yaml_cached(HERE / f"{name}.yaml")


class SeedError(RuntimeError):
    pass


@dataclass
class NfiSeed:
    study_id: str = ""
    stage: str = "S0"
    recording: bool = False     # the walkthrough's seed: scenes filmed on camera are left empty
    elements: dict[str, dict] = field(default_factory=dict)     # name -> element
    requirements: dict[str, str] = field(default_factory=dict)  # code -> requirement id
    modes: dict[str, dict] = field(default_factory=dict)        # modes.yaml key -> mode
    risks: list[dict] = field(default_factory=list)
    trades: dict[str, dict] = field(default_factory=dict)       # trade id -> trade (state, evaluation)
    link_cases: dict[str, dict] = field(default_factory=dict)   # case name -> link case
    rids: list[dict] = field(default_factory=list)              # MDR RIDs and actions
    report: dict[str, Any] = field(default_factory=lambda: {"calls": 0, "forbidden": 0, "seconds": {}})
    negotiations: dict[str, dict] = field(default_factory=dict)  # wave 3 (H): template code -> record


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
    await _s0_mission_need(api, seed)
    await _s0_stakeholders(api, seed)


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
    # W2.09 (agent R): the elements the baseline allocates to that the tree above lacks, then the
    # whole baseline through the bulk import (W2.04): needs, objectives and every row (v2: 302)
    # with every field, extra parents and objectives; the rows posted above are updated in place.
    # Wave 3: the functions first (the v2 rows reference them), the threshold bindings after.
    await _s1_functions(api, seed)
    await _w2_import_baseline(api, seed)
    await _s1_bindings(api, seed)


def element_name(code: str) -> str | None:
    """The tool element name of a v2 element id (``ELEMENT_IDS``)."""
    return ELEMENT_IDS.get(code)


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


def maturity_overlay() -> tuple[dict[str, str], dict[str, str]]:
    """v2 maturity classes by equipment name: (mass category, power category). ``budgets.yaml``
    ``mass.items`` names the items; ``power.units`` uses the short labels of ``modes.yaml``
    (``MODE_UNITS``); two labels on one element (radio RX and TX) take the larger margin."""
    b = load("budgets")
    mass = {it["item"]: MATURITY_PCT_CATEGORY[int(it["maturity_pct"])] for it in b["mass"]["items"]}
    power: dict[str, str] = {}
    for u in b["power"]["units"]:
        name = MODE_UNITS.get(u["unit"])
        if name is None:
            continue
        cat = MATURITY_PCT_CATEGORY[int(u["maturity_pct"])]
        power[name] = max(power.get(name, "A"), cat)      # A < C < D: the larger margin wins
    return mass, power


async def _s2(api: _Api, seed: NfiSeed) -> None:
    sid, eq = seed.study_id, load("equipment")
    mass_cat, power_cat = maturity_overlay()
    for sub in eq["spacecraft"]["subsystems"]:
        parent = seed.elements[sub["name"]]
        for it in sub["items"]:
            perf = {}
            if it.get("maturity"):
                perf["maturity_category"] = MATURITY_CATEGORY[it["maturity"]]
            # v2: the classes of budgets.yaml win (DMSA wing mass, radio TX power, ADCS power)
            if it["name"] in mass_cat:
                perf["maturity_category"] = mass_cat[it["name"]]
            if it["name"] in power_cat:
                perf["power_maturity_category"] = power_cat[it["name"]]
            seed.elements[it["name"]] = await api.element(
                sid, name=it["name"], element_type="component", parent_id=parent["id"],
                subsystem_domain=sub["domain"], kb_component_id=None if it.get("custom") else it.get("kb"),
                quantity=int(it.get("qty") or 1), mass_kg=float(it.get("mass_kg") or 0.0),
                power_avg_w=float(it.get("power_w") or 0.0), trl=it.get("trl"),
                cost_recurring_keur=it.get("cost_keur"), owner_position=sub.get("seat"),
                performance=perf or None)
    await _accept_all_suggestions(api, sid)
    await _modes(api, seed)
    await _w103_disposal_mode(api, seed)
    await _s2_conops_phases(api, seed)
    await _s2_link_cases(api, seed)
    await _s2_margin_hold(api, seed)
    await _s2_allocations(api, seed)
    await _s2_readiness(api, seed)
    await _s2_conops_scenarios(api, seed)


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


async def _w103_disposal_mode(api: _Api, seed: NfiSeed) -> None:
    """W1.03: the end-of-life mode is the template's disposal mode ("Sail deploy", template key
    ``eol``), patched above to the baseline name. Its kind goes back to ``disposal`` (modes.yaml
    says custom: the baseline predates the disposal kind) and the template's ARM + FIRE transition,
    which the baseline adds again, is kept once."""
    sid = seed.study_id
    eol = seed.modes.get("eol")
    if not eol:
        return
    seed.modes["eol"] = await api.call("PATCH", f"/api/studies/{sid}/modes/{eol['id']}", {"kind": "disposal", "phase": "disposal"})
    ov = await api.call("GET", f"/api/studies/{sid}/modes")
    seen: set[tuple] = set()
    for t in sorted(ov["transitions"], key=lambda t: 0 if t.get("origin") != "template" else 1):
        k = (t["from_mode_id"], t["to_mode_id"], t.get("trigger"))
        if k in seen:
            await api.call("DELETE", f"/api/studies/{sid}/mode-transitions/{t['id']}")
        seen.add(k)


async def _s3(api: _Api, seed: NfiSeed) -> None:
    await _post_requirements(api, seed, lambda r: True)
    for r in load("risks")["risks"]:
        res = await api.post(f"/api/studies/{seed.study_id}/risks", {
            "description": r["desc"], "category": r.get("cat", "Technical"), "likelihood": int(r["L"]),
            "consequence": int(r["C"]), "mitigation": r.get("mit", ""), "owner": r.get("owner", ""),
            "status": r.get("status", "open"), "source": str(r.get("src", ""))[:120]})
        seed.risks.append(res)
    await _s3_risks(api, seed)
    # W2.07 (agent R): the 12 IF rows linked to their interfaces and ICD rows; the interfaces
    # they name that the proposer did not make (IF-02 suggestions) are accepted
    await _w2_link_interfaces(api, seed)
    await _s3_trades(api, seed)
    await _s3_mdr_review(api, seed)
    await _s3_open_items(api, seed)
    await _s3_changes(api, seed)
    await _s3_validation(api, seed)
    await _s3_assumptions(api, seed)
    await _s3_negotiations(api, seed)


async def _s4(api: _Api, seed: NfiSeed) -> None:
    sid = seed.study_id
    await api.post(f"/api/studies/{sid}/cdr/propose")
    await api.post(f"/api/studies/{sid}/cdr/accept-all")
    r = await api.call("POST", f"/api/studies/{sid}/stack/auto-place", {}, ok=(200, 409, 422))
    if r and not r.get("detail"):
        await api.call("POST", f"/api/studies/{sid}/stack/approve", {}, ok=(200, 409, 422))
    # wave 2 (agent D): the design loop again on the placed stack, before the analyses that read
    # its results, so no run is stale at S4 (its write-back feeds ground, physics and simulation)
    await _s3_design_loop(api, seed)
    for a in ("vv", "ground_segment", "physics", "mission_simulation"):
        await api.post(f"/api/studies/{sid}/analyses/{a}/run")
    # W8a / W11a: model philosophy and test matrix; the launch is provided by the agency, so the
    # cost carries no launch; milestones from the gate profile and the WBS from the product tree
    await api.post(f"/api/studies/{sid}/ait/propose")
    await _s4_ait_v2(api, seed)
    await api.call("PUT", f"/api/studies/{sid}/schedule/settings", {"launch_provided": True, "currency": "CAD"})
    await api.post(f"/api/studies/{sid}/schedule/propose")
    await _hk_sids(api, seed)
    if not seed.recording:       # PI ruling: the team fills the Licensing tab on camera
        await _s4_licensing(api, seed)
    await _s4_link_licensing(api, seed)
    await _s4_negotiations(api, seed)        # wave 3 (H): options on the S4 design, signed


# ───────────────────────────────────── agent D (wave 1): mission need, ConOps, links, trades, review

#: success criteria = the measures of the primary objectives (mission.yaml ``step2_objectives``)
#: alternative types from the alternative names (MissionNeed ``AlternativeType``)
_ALT_TYPES = (("Sentinel", "space_existing"), ("Landsat", "space_existing"), ("SuperDove", "space_existing"),
              ("WorldView", "space_existing"), ("Drone", "aerial_drone"), ("aircraft", "aerial_aircraft"),
              ("IoT", "ground_sensor"), ("Hybrid", "hybrid"), ("CubeSat", "space_dedicated"))


async def _s0_mission_need(api: _Api, seed: NfiSeed) -> None:
    """W1.06: success criteria (the primary objectives' measures) and alternative types."""
    wiz = load("mission")["wizard"]
    success = [f"{o['text'][0].upper()}{o['text'][1:]}: {o['measure']}"
               for o in wiz["step2_objectives"] if o["priority"] == "primary" and o.get("measure")]
    st = await api.call("GET", f"/api/studies/{seed.study_id}")
    alts = []
    for a in (st.get("mission_need") or {}).get("alternatives_considered") or []:
        kind = next((k for word, k in _ALT_TYPES if word.lower() in a["name"].lower()), "other")
        alts.append({**a, "type": kind})
    await api.call("PATCH", f"/api/studies/{seed.study_id}/mission",
                   {"mission_need": {"success_criteria": success, "alternatives_considered": alts}})


_PHASE_TYPES = (("LEOP", "leop"), ("commissioning", "commissioning"), ("Nominal", "nominal"),
                ("Extended", "extended"), ("disposal", "disposal"))


def _phase_days(window: str, start: float, n: dict) -> tuple[float, float]:
    """(start, end) day of a ``modes.yaml`` phase window such as "L+7 to L+30 d", "L+90 d to
    L+15 mo"; open windows end at the design life (extended) or the decay time (disposal)."""
    import re
    vals = []
    for num, unit in re.findall(r"L\+(\d+(?:\.\d+)?)\s*(d|mo|y)?", window):
        v = float(num) * {"mo": 365.25 / 12, "y": 365.25}.get(unit or "d", 1.0)
        vals.append(v)
    if re.match(r"^L to L\+", window):
        vals.insert(0, 0.0)
    if len(vals) >= 2:
        return vals[0], vals[1]
    if "EOL" in window:
        return start, n["schedule"]["design_life_y"] * 365.25
    return start, start + n["disposal"]["lifetime_with_sail_y_590km"]["nominal"] * 365.25


async def _s2_conops_phases(api: _Api, seed: NfiSeed) -> None:
    """W7.01: the mission phases of ``modes.yaml`` (pre-launch is not a flight phase)."""
    n, rows = load("NUMBERS"), load("modes")["phases"]
    phases, end, prev_exit = [], 0.0, "Separation from the deployer"
    for name, window, activities, exit_crit in rows:
        ptype = next((t for word, t in _PHASE_TYPES if word.lower() in name.lower()), None)
        if ptype is None:
            prev_exit = exit_crit
            continue
        a, b = _phase_days(window, end, n)
        phases.append({"id": name.lower().replace(" ", "_").replace("/", "")[:40], "name": name, "phase_type": ptype,
                       "duration_days": round(b - a, 1), "description": activities,
                       "entry_criteria": prev_exit if phases else "Separation from the deployer",
                       "exit_criteria": exit_crit})
        end, prev_exit = b, exit_crit
    await api.call("PUT", f"/api/studies/{seed.study_id}/conops/phases", {"phases": phases})


def _link_cases(n: dict) -> list[dict]:
    """The link cases of NUMBERS.yaml ``links`` (calc/link.py assumptions: spacecraft antenna 0 dBi
    with a 3 dB pattern allowance, 1 dB line loss, 3 dB polarisation, 1 dB scintillation, 0.5 dB
    pointing, a 13 dBic ground antenna and 0.3 dB cable; RS(255,223) needs 6.0 dB + 2 dB
    implementation, uncoded 10.6 dB)."""
    lk, gn = n["links"], n["ground_network"]
    el = gn["min_elevation_deg"]
    dl = {"direction": "downlink", "band": "UHF", "elevation_deg": el, "frequency_mhz": 401.5,
          "data_rate_bps": lk["downlink"]["rate_kbps"] * 1000, "rate_tier": f"high {lk['downlink']['rate_kbps']} kbit/s",
          "modulation": lk["downlink"]["modulation"], "coding": lk["downlink"]["coding"],
          "tx_antenna_gain_dbi": -3.0, "tx_losses_db": 1.0, "polarisation_loss_db": 3.0,
          "atmospheric_loss_db": 1.0, "pointing_loss_db": 0.5, "rx_antenna_gain_dbi": 13.0, "rx_losses_db": 0.3,
          "required_ebn0_db": 6.0, "implementation_loss_db": 2.0, "source": "seed"}
    sites = lk["margin_by_site"]
    cases = []
    for site in ("Ottawa", "Yellowknife", "Iqaluit", "Inuvik"):
        tsys = sites[site].get("planning_tsys_k") or sites[site]["tsys_k"]
        kind = "urban" if tsys > 300 else "rural"
        cases.append({**dl, "name": f"DL {site} 1 W {kind} ({tsys:.0f} K)", "station": site,
                      "tx_power_w": lk["downlink"]["tx_power_w"], "system_noise_temp_k": tsys})
    cases.append({**dl, "name": "DL Ottawa 2 W urban (700 K)", "station": "Ottawa", "tx_power_w": 2.0,
                  "system_noise_temp_k": sites["Ottawa"]["planning_tsys_k"]})
    cases.append({**dl, "name": "DL Ottawa 1 W urban uncoded", "station": "Ottawa", "coding": "uncoded",
                  "tx_power_w": lk["downlink"]["tx_power_w"], "system_noise_temp_k": sites["Ottawa"]["planning_tsys_k"],
                  "required_ebn0_db": 10.6})
    ul = {"direction": "uplink", "band": "UHF", "elevation_deg": el, "frequency_mhz": 450.0, "station": "all four sites",
          "data_rate_bps": lk["uplink"]["rate_kbps"] * 1000, "rate_tier": f"{lk['uplink']['rate_kbps']} kbit/s",
          "modulation": "GMSK", "coding": "uncoded", "tx_power_w": float(lk["uplink"]["ground_tx_w_max"]),
          "tx_antenna_gain_dbi": 13.0, "tx_losses_db": 1.5, "pointing_loss_db": 0.5, "polarisation_loss_db": 3.0,
          "atmospheric_loss_db": 1.0, "rx_antenna_gain_dbi": -3.0, "rx_losses_db": 1.0, "required_ebn0_db": 10.6,
          "implementation_loss_db": 2.0, "source": "seed"}
    for key in lk["uplink_margin_db_10deg_9k6"]:
        if key == "src":
            continue
        tsys = float(key.split("_")[1].rstrip("K"))
        cases.append({**ul, "name": f"UL {lk['uplink']['ground_tx_w_max']} W, spacecraft {tsys:.0f} K",
                      "system_noise_temp_k": tsys})
    return cases


async def _s2_link_cases(api: _Api, seed: NfiSeed) -> None:
    """W4.04: the eight named link cases; the rural 1 W downlink and the 600 K uplink become the
    design cases (``requirements.link``)."""
    sid = seed.study_id
    for i, c in enumerate(_link_cases(load("NUMBERS"))):
        seed.link_cases[c["name"]] = await api.post(f"/api/studies/{sid}/link-budgets", {**c, "order": i})
    for name in ("DL Yellowknife 1 W rural (300 K)", "UL 25 W, spacecraft 600 K"):
        await api.post(f"/api/studies/{sid}/link-budgets/{seed.link_cases[name]['id']}/apply")


#: requirements each trade's criteria are about (beyond the rows that cite the trade id)
TRADE_REQUIREMENTS = {
    "T-01": ["PAY-OPT-01", "PAY-OPT-02"], "T-02": ["PAY-OPT-01", "PAY-OPT-04", "PAY-FUN-01"],
    "T-03": ["PAY-FUN-03", "PAY-FUN-04"], "T-04": ["EPS-SA-01", "SYS-BUD-03"],
    "T-05": ["EPS-BAT-01", "SYS-BUD-04", "SYS-BUD-08"], "T-06": ["DIS-SAIL-01", "DIS-TRG-01", "DIS-REL-01"],
    "T-07": ["COM-DL-01", "COM-DL-03", "COM-UL-01", "SYS-BUD-06"], "T-08": ["ADC-PNT-01", "ADC-PNT-03"],
}
#: risks of risks.yaml each trade bears on
TRADE_RISKS = {"T-01": ["RSK-020"], "T-02": ["RSK-005"], "T-03": ["RSK-019"], "T-04": ["RSK-003"],
               "T-05": ["RSK-016"], "T-06": ["RSK-002"], "T-07": ["RSK-010", "RSK-011"],
               "T-08": ["RSK-009", "RSK-022"]}
#: the option each trade's decision kept (logbook.yaml "decide:pugh T-nn"), by option index
TRADE_CHOICE = {"T-01": 1, "T-02": 0, "T-03": 0, "T-04": 1, "T-05": 1, "T-06": 0, "T-07": 0, "T-08": 1}


async def _s3_trades(api: _Api, seed: NfiSeed) -> None:
    """W6: every trade of ``trades.yaml`` with its pairwise weights, linked to the requirements,
    risks and the subsystem it affects, then decided (decision record + logbook entry)."""
    import re
    sid, data = seed.study_id, load("trades")
    cites: dict[str, list[str]] = {}
    for r in load("requirements")["requirements"]:
        blob = " ".join(str(r.get(k) or "") for k in ("source", "rationale", "text"))
        for tid in set(re.findall(r"\bT-0\d\b", blob)):
            cites.setdefault(tid, []).append(r["id"])
    names = {e.get("name"): e for e in seed.elements.values()}
    trades = []
    for t in data["trades"]:
        tid = t["id"]
        reqs = [c for c in dict.fromkeys([*TRADE_REQUIREMENTS.get(tid, []), *cites.get(tid, [])]) if c in seed.requirements]
        sub = str(t.get("level") or "").split(":", 1)[-1].strip()
        els = [names[sub]["id"]] if sub in names else []
        trades.append({**t, "links": {"requirements": reqs, "risks": TRADE_RISKS.get(tid, []), "elements": els,
                                      "decision_record": t.get("decision_record")}})
    res = await api.post(f"/api/studies/{sid}/trades/import", {"trades": trades, "pairwise_inputs": data["pairwise_inputs"]})
    if len(res["added"]) != len(data["trades"]):
        raise SeedError(f"trades import: {res}")
    notes = {e["decision"].split()[-1]: e for e in load("logbook")["entries"] if str(e["decision"]).startswith("decide:pugh")}
    for t in data["trades"]:
        tid = t["id"]
        entry = notes.get(tid) or {}
        out = await api.post(f"/api/studies/{sid}/trades/{tid}/decision",
                             {"selected": t["options"][TRADE_CHOICE[tid]], "rationale": entry.get("text", ""),
                              "seat": t.get("seat", "")})
        seed.trades[tid] = out
        if entry:
            await api.post("/api/logbook/entries", {"kind": "decision", "text": f"{entry['title']}: {entry['text']}",
                                                    "context": {"study_id": sid, "where": "decide", "trade": tid,
                                                                "decision_record": t.get("decision_record") or ""}},
                           ok=(200, 201))


#: three MDR RIDs / actions (logbook.yaml LB-23 lists the MCR actions), neutral wording
MDR_RIDS = [
    {"kind": "rid", "severity": "major", "raised_by_seat": "systems_engineer", "owner_seat": "comms_engineer",
     "criterion_id": "", "due_date": "2027-09-30",
     "description": "The radio's receive band is not confirmed to cover the 449.75-450.25 MHz uplink; obtain the vendor confirmation or select the fallback radio."},
    {"kind": "action", "severity": "minor", "raised_by_seat": "team_leader", "owner_seat": "comms_engineer",
     "criterion_id": "", "due_date": "2027-09-30",
     "description": "Start the spectrum pre-consultation for the 450 MHz uplink and the 401 MHz downlink."},
    {"kind": "action", "severity": "minor", "raised_by_seat": "mission_analyst", "owner_seat": "propulsion_engineer",
     "criterion_id": "", "due_date": "2027-12-15",
     "description": "Obtain in-orbit deployment evidence for the selected drag sail, or keep the documented fallback."},
]


async def _s3_design_loop(api: _Api, seed: NfiSeed) -> None:
    """Wave 2: the design loop, run once the mission, equipment, modes, link design cases and the
    requirement baseline are in, as a team does before its MDR: MDR-EC-07 (and the budget criteria
    of the later gates) read its end-of-life generation and margins. Equipment values entered by
    the seats are sticky, so the roll-up is unchanged by the run."""
    res = await api.post(f"/api/design/{seed.study_id}/run")
    seed.report["design_loop"] = {"converged": res.get("converged"), "iterations": res.get("iterations")}


async def _s4_link_licensing(api: _Api, seed: NfiSeed) -> None:
    """Wave 2: the link cases' per-station earth-station values into the licensing record
    (W4.04 -> W5.04)."""
    seed.report["licensing_sync"] = await api.post(f"/api/studies/{seed.study_id}/link-budgets/licensing-sync")


async def _s3_mdr_review(api: _Api, seed: NfiSeed) -> None:
    """W4.08: the MDR review record: three RIDs / actions and the chair's GO-with-actions, after
    the design loop has run (the MDR's power and mass criterion needs it)."""
    sid = seed.study_id
    await _s3_design_loop(api, seed)
    for r in MDR_RIDS:
        seed.rids.append(await api.post(f"/api/studies/{sid}/gates/mdr/rids", r))
    await api.call("PUT", f"/api/studies/{sid}/gates/mdr/record", {
        "decision": "go_with_actions", "board": "Team leader (chair), Systems, Mission analysis & ops, Customer",
        "chair_note": "Mission definition accepted. The radio receive band, the spectrum pre-consultation and the "
                      "drag-sail evidence are carried as actions to the PRR."})



def _mode_map(seed: NfiSeed, table: dict | None) -> dict | None:
    """``{leop: 1, ...}`` keyed by the modes.yaml keys -> keyed by the study's mode ids."""
    if not isinstance(table, dict):
        return None
    return {seed.modes[k]["id"]: v for k, v in table.items() if k in seed.modes}


async def _hk_sids(api: _Api, seed: NfiSeed) -> None:
    """W3: the housekeeping design of ``hk_sids.yaml`` replaces the rule-proposed SIDs: every SID
    with its parameter list, real-time and stored intervals per mode, enable flags and stores; the
    real-time profiles, service reports, link framing and the payload products of NUMBERS.yaml."""
    sid, hk, n = seed.study_id, load("hk_sids"), load("NUMBERS")
    view = await api.call("GET", f"/api/studies/{sid}/cdr")
    for r in view["rows"]["hk"]:
        if r["status"] != "rejected":
            await api.call("DELETE", f"/api/studies/{sid}/cdr/hk/{r['id']}")
    for x in hk["sids"]:
        rt = _mode_map(seed, x.get("rt_interval_s"))
        st = _mode_map(seed, x.get("store_interval_s")) if x.get("store_sid") is not None else None
        nominal = (x.get("rt_interval_s") or {}).get("nominal") or (x.get("rt_interval_s") or {}).get("leop") or 30
        data = {"sid": x["id"], "store_sid": x.get("store_sid"), "name": x["name"], "subsystem": x["subsystem"],
                "apid": x["apid"], "params": x["parameters"], "period_s": nominal,
                "enabled": dict(x["enabled_by_default"]), "enabled_at_boot": bool(x["enabled_by_default"]["realtime"]),
                "diagnostic": bool(x.get("diagnostic")), "beacon": bool(x.get("beacon")),
                "rt_period_by_mode": rt, "store_period_by_mode": st,
                "store_id": (3 if x.get("diagnostic") else 1) if x.get("store_sid") is not None else None,
                "rationale_text": x.get("rationale")}
        if x.get("diagnostic"):
            data.update({"auto_disable_s": 5796, "obcp": "disable SID 20 and 120 after one orbit"})
        await api.post(f"/api/studies/{sid}/cdr/hk", {"data": data})
    rows = (await api.call("GET", f"/api/studies/{sid}/cdr"))["rows"]

    async def put(kind: str, key_field: str | None, data: dict) -> None:
        mine = [r for r in rows.get(kind) or [] if r["status"] != "rejected" and
                (key_field is None or str(r["data"].get(key_field)) == str(data.get(key_field)))]
        if mine:
            await api.call("PATCH", f"/api/studies/{sid}/cdr/{kind}/{mine[0]['id']}", {"data": data})
        else:
            await api.post(f"/api/studies/{sid}/cdr/{kind}", {"data": data})

    fr = hk["link_framing"]
    await put("link_framing", None, {"rs_n": 255, "rs_k": 223, "rs_interleave": 2, "asm_bytes": 4,
                                     **{f"{k}_bytes" if not k.endswith("_bytes") else k: v for k, v in
                                        {"tf_header": fr["frame_overhead_bytes"]["tf_primary_header"],
                                         "sdls_header": fr["frame_overhead_bytes"]["sdls_security_header"],
                                         "sdls_mac": fr["frame_overhead_bytes"]["sdls_mac_truncated"],
                                         "ocf": fr["frame_overhead_bytes"]["ocf_clcw"]}.items()},
                                     "acquisition_s": n["data_budget"]["pass_overheads"]["acquisition_s_per_window"],
                                     "availability": n["data_budget"]["pass_overheads"]["availability"],
                                     "virtual_channels": fr["virtual_channels"]})
    for st in hk["stores"]:
        content = ({"sids": list(range(101, 111))} if st["id"] == 1 else {"services": [5]} if st["id"] == 2 else
                   {"stored_diagnostic": True} if st["id"] == 3 else {"payload": True} if st["id"] == 5 else {"services": [6, 23]})
        await put("stores", "id", {"id": st["id"], "name": st["name"], "size_mb": st.get("size_mb"), "size_gb": st.get("size_gb"),
                                   "circular": bool(st.get("circular")), "content": content, "location": st.get("location") or "OBC",
                                   "description": st.get("content")})
    pr = hk["rt_profiles"]
    await put("rt_profiles", "name", {"name": "FULL", "mode_intervals": True, "allocation_bps": pr["FULL"]["allocation_bps"],
                                      "interval_factor": None, "description": {"en": pr["FULL"]["note"], "fr": pr["FULL"]["note"]}})
    await put("rt_profiles", "name", {"name": "LEAN", "mode_intervals": False, "interval_factor": None,
                                      "intervals_s": {str(k): v for k, v in pr["LEAN"]["intervals_s"].items()},
                                      "description": {"en": pr["LEAN"]["note"], "fr": pr["LEAN"]["note"]}})
    sa = hk["service_allowances"]
    await put("service_allowances", None, {k: sa[k] for k in ("S1_verification", "S5_events", "S9_time_report", "S15_store_status")})
    pp = n["data_budget"]["products"]
    await put("payload_products", None, {
        "science_mb_per_day": n["data_budget"]["science_target_mb_per_day_after_compression"]["value"],
        "compression_ratio": 1.5, "cfdp_efficiency": n["data_budget"]["pass_overheads"]["cfdp_efficiency"],
        "products": [{"name": "ROI pair", "mb_raw": pp["roi_pair_mb_raw"]["value"], "per_day": pp["planned_set_per_day"]["roi_pairs"], "priority": 2},
                     {"name": "Quicklook", "mb_raw": pp["quicklook_mb_raw"]["value"], "per_day": pp["planned_set_per_day"]["quicklooks"], "priority": 1}],
        "compression_required": pp["compression_required"]["value"]})
    # wave 3 (3.H5): the radio's rate ladder of hk_sids.yaml (1.2 / 9.6 / 19.2 / 38.4 kbit/s) over the
    # rule-proposed tiers, so the fallback case and the sensitivity run at the baseline's 19.2 kbit/s.
    # The rule-proposed tier names are kept (the TT&C configuration names them).
    ladder = {t["name"]: t for t in hk["rate_tiers"]}
    tiers = [r for r in rows.get("rate_tiers") or [] if r["status"] != "rejected"]
    by_role = {r["data"].get("role"): r for r in tiers}
    for role, src in (("beacon", "BEACON"), ("default", "LOW"), ("downlink", "HIGH")):
        if role in by_role and src in ladder:
            await api.call("PATCH", f"/api/studies/{sid}/cdr/rate_tiers/{by_role[role]['id']}",
                           {"data": {**by_role[role]["data"], "bps": ladder[src]["bps"]}})
    if "DEFAULT" in ladder and not any(r["data"].get("bps") == ladder["DEFAULT"]["bps"] for r in tiers):
        base = dict((by_role.get("default") or {}).get("data") or {})
        await api.post(f"/api/studies/{sid}/cdr/rate_tiers", {"data": {**base, "name": "DEFAULT", "role": "fallback",
                                                                      "bps": ladder["DEFAULT"]["bps"]}})


_STEPS ={"S0": _s0, "S1": _s1, "S2": _s2, "S3": _s3, "S4": _s4}


async def seed_nfi(client, stage: str = "S4", recording: bool = False) -> NfiSeed:
    """Build the Northern Fire and Ice study up to ``stage`` (S0..S4). Raises SeedError on any
    unexpected HTTP status; ``report`` counts the calls, 403 responses and seconds per stage.

    ``recording=True`` builds the walkthrough's seed: the scenes filmed on camera (the Licensing
    tab, the allocation ledger, the negotiation records) are left for the team to fill."""
    stage = stage.upper()
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    seed = NfiSeed(recording=bool(recording))
    api = _Api(client, seed)
    for s in STAGES[: STAGES.index(stage) + 1]:
        t0 = time.perf_counter()
        await _STEPS[s](api, seed)
        seed.report["seconds"][s] = round(time.perf_counter() - t0, 2)
        seed.stage = s
    return seed


# ───────────────────────────────────────────── W2 (agent R): bulk import of the baseline

#: elements the requirement baseline allocates rows to, beyond the S1 tree above
W2_EXTRA_ELEMENTS = (
    # name, element_type, parent key in seed.elements, segment
    ("Science Segment", "segment", "mission", "user"),
    ("Operations", "segment", "mission", "operations"),
    ("Harness", "subsystem", "spacecraft", "space"),
)


async def _w2_import_baseline(api: _Api, seed: NfiSeed) -> None:
    sid = seed.study_id
    for name, etype, parent, segment in W2_EXTRA_ELEMENTS:
        if name not in seed.elements:
            seed.elements[name] = await api.element(
                sid, name=name, element_type=etype, parent_id=seed.elements[parent]["id"], segment=segment,
                subsystem_domain="harness" if name == "Harness" else ("ground" if segment == "operations" else None),
                owner_position="systems_engineer" if name == "Harness" else None)
    rep = await api.post(f"/api/studies/{sid}/requirements/import",
                         {"document": load("requirements"), "study_id": sid})
    if rep.get("errors"):
        raise SeedError(f"requirement import: {rep['errors'][:5]}")
    for code, rid in rep["id_map"].items():
        if not code.startswith("SN-"):
            seed.requirements[code] = rid
    seed.report["requirements_import"] = {k: rep[k] for k in ("created", "updated", "unchanged", "by_level",
                                                                "relations_created", "unallocated", "seconds")}
    # wave 2 integration: the budget rows are checked against the study's budget figures
    # (gate_evaluator.BUDGET_PARAMS: roll-up, data budget, design link case), as a student sets
    # "checked against" on the Requirements tab; SRR-EC-03 and PDR-EC-01 then evaluate them
    for code, path in BUDGET_PARAM_PATHS.items():
        if code in seed.requirements:
            await api.call("PATCH", f"/api/requirements/{seed.requirements[code]}", {"threshold_param_path": path})


#: requirement code -> the budget figure its threshold is checked against (W2 integration)
BUDGET_PARAM_PATHS = {
    "SYS-BUD-01": "budget.mass_total_dry_kg",                     # <= 6.0 kg (predicted until weighed)
    "SYS-BUD-02": "budget.mass_system_margin_available_percent",  # >= 20 % system margin on the margined mass
    "SYS-BUD-03": "budget.power_margin_eol_percent",              # >= 20 % EOL power margin
    "SYS-BUD-05": "budget.data_margin_percent",                   # >= 10 % daily data-volume margin
    "SYS-BUD-06": "budget.link_margin_design_case_db",            # >= 3 dB at 10 deg (design link case)
}


async def _w2_link_interfaces(api: _Api, seed: NfiSeed) -> None:
    sid = seed.study_id
    rep = await api.post(f"/api/studies/{sid}/interface-requirements/link")
    for i in await api.call("GET", f"/api/studies/{sid}/interfaces?status=suggested"):
        if i.get("origin") == "rule:IF-02":
            await api.call("PATCH", f"/api/interfaces/{i['id']}", {"status": "accepted"})
    await api.post(f"/api/studies/{sid}/interface-requirements/sync")
    seed.report["interface_link"] = rep


# ───────────────────────────────────── agent L (wave 2): the Licensing tab

#: Neutral applicant placeholders: the example names no institution, person or real address.
LICENSING_APPLICANT = {
    "legal_name": "Example university (applicant placeholder)", "address": "Example address, Ottawa, Ontario, Canada",
    "country": "Canada", "canadian_entity": True, "contact_name": "Mission manager (placeholder)",
    "contact_email": "licensing@example.org", "contact_phone": "+1 555 0100",
    "security_officer": "Security officer (placeholder)",
}


def licensing_record(n: dict) -> dict:
    """The Licensing tab of the Northern Fire and Ice mission at S4, from the baseline requirements
    (codes cited) and NUMBERS.yaml. What the baseline does not say (backup facility, personnel and
    physical security, data disposal, priority access, launch provider and vehicle) stays empty, so
    the documents print it as an applicant input."""
    d = n["disposal"]
    return {
        "applicant": dict(LICENSING_APPLICANT),
        "contacts": [{"role": "24/7 operations contact (conjunction screening, REG-DEB-02)",
                      "name": "Operations duty officer (placeholder)", "email": "ops@example.org", "phone": "+1 555 0101"}],
        "participants": [
            {"name": "Student engineering team (placeholder)", "role": "design, build and operation", "country": "Canada"},
            {"name": "Science team (placeholder)", "role": "science processing and archive", "country": "Canada"},
            {"name": "Funding agency student CubeSat programme (placeholder)", "role": "sponsor", "country": "Canada"}],
        "itu_network_name": "NFI-1",
        "cdpp": {
            "command_facility": "Mission control centre, Ottawa: the single licensed command centre; the four ground "
                                "stations are reached only over its site-to-site VPN (MIS-OPS-03, SEG-GS-08).",
            "data_facility": "Science segment: Level-0 to Level-2 processing and archive for at least 10 years after "
                             "the end of the mission (MIS-DAT-07).",
            "command_encryption": "CCSDS SDLS authenticated encryption, AES-256, in the on-board computer software, "
                                  "independent of the radio (REG-RSS-03).",
            "command_authentication": "Every accepted telecommand authenticated (SDLS); irreversible commands need "
                                      "ARM + FIRE, a second certified operator and a GO from the Team leader.",
            "downlink_encryption": "Payload data encrypted on the space-to-ground link (SDLS, AES-256) and held in "
                                   "access-controlled storage on the ground (REG-RSS-04).",
            "key_management": "Encrypted key store with two-person access control, logged key loading and a "
                              "documented key-compromise procedure (SEG-GS-10).",
            "key_custody": "Mission control centre, two-person control (SEG-GS-10).",
            "command_process": "Pass schedule for all four stations at least 24 h ahead (SEG-GS-09); every "
                               "telecommand logged with operator identity, time and verification result for the "
                               "life of the licence (SEG-GS-11).",
            "network_security": "Site-to-site VPN between mission control and each station, mutual certificate "
                                "authentication and AES-256 (SEG-GS-08).",
        },
        "data_policy": {
            "distribution": "Level-1C and Level-2 products released openly within 6 months of acquisition, subject "
                            "to the RSSSA licence conditions (MIS-DAT-05).",
            "eula": "CC BY 4.0 or an equivalent open licence (MIS-DAT-05).",
            "retention": "All Level-0 data, products, calibration data and software versions for at least 10 years "
                         "after the end of the mission (MIS-DAT-07).",
            "sensed_state_access": "Raw data of a sensed state's territory provided within 30 days of a request when "
                                   "the licence requires it (REG-RSS-05).",
        },
        "launch": {"deployer": "3U CubeSat deployer (rideshare)"},
        "disposal": {"independent_circuits": int(d["release_circuits"]),
                     "independent_timer_days": int(d["independent_timer_days"]),
                     "trigger": ["ground command (ARM + FIRE)", "independent timer (OBC-independent)",
                                 "battery under-voltage"],
                     "mass_basis": "allocation"},
        "notes": "Applicant placeholder for the teaching example: replace with the real applicant, its ownership and "
                 "control before any filing.",
    }


async def _s4_licensing(api: _Api, seed: NfiSeed) -> None:
    """W5.03 / W5.04: the Licensing tab filled from the baseline (neutral applicant placeholders)."""
    sid = seed.study_id
    cur = await api.call("GET", f"/api/lifecycle/licensing/{sid}")
    saved = await api.call("PUT", f"/api/lifecycle/licensing/{sid}",
                           {**licensing_record(load("NUMBERS")), "version": cur["version"]})
    seed.report["licensing_version"] = saved["version"]


# ───────────────────────────────────── wave 3, step 0: v2 margin hold and the agents' steps

async def _s2_margin_hold(api: _Api, seed: NfiSeed) -> None:
    """3.0c: the study holds 20 % system margin on mass and power through PDR (``budgets.yaml``
    ``margin_policy``: "hold 20 % system margin on mass and power through PDR"); the course
    ladder (15 % at SRR and PDR) is unchanged and quoted next to it."""
    mp = load("budgets")["margin_policy"]
    pct = load("budgets")["mass"]["system_margin_pct"]
    await api.call("PUT", f"/api/studies/{seed.study_id}/margin-policy", {"study_override": {
        "percent": pct, "through_gate": "pdr", "resources": ["mass", "power"],
        "rationale": f"{mp['adopted']}. {mp['note']}"}})


# Each step below is EMPTY in step 0 and belongs to one agent of the parallel wave; the owner
# fills it (append-only, never reorder the calls in the stage functions above). Use
# ``seed.recording`` to leave out what the walkthrough films on camera.

async def _s0_stakeholders(api: _Api, seed: NfiSeed) -> None:
    """TODO(S, 3.S3): ``stakeholders.yaml``: 12 stakeholders in 5 categories with authority and
    engagement, the 12 needs (SN-*), the 15 MOEs (MOE-04 and MOE-10 placeholders)."""


async def _s1_functions(api: _Api, seed: NfiSeed) -> None:
    """TODO(R, 3.R1): ``functions.yaml`` in at most 3 calls, before the requirements: 86 functions
    (13 / 70 / 3), 5 enabling processes (PR-*), leaf allocations to the elements (``ELEMENT_IDS``),
    37 functional exchanges."""


async def _s1_bindings(api: _Api, seed: NfiSeed) -> None:
    """TODO(R, 3.R2): accept the threshold-binding proposals (``budget_ref`` → roll-up, data-budget,
    link paths); then drop ``BUDGET_PARAM_PATHS`` and its loop in ``_w2_import_baseline``."""


async def _s2_allocations(api: _Api, seed: NfiSeed) -> None:
    """TODO(A, 3.A2): every allocation of ``budgets.yaml`` (8 mass, 8 power, peak, mode, data,
    pointing, registration, timing lines) agreed by its seat. Not in the recording seed (the
    scene is filmed)."""


async def _s2_readiness(api: _Api, seed: NfiSeed) -> None:
    """TODO(L, 3.L7): ``risks.yaml`` ``readiness.trl``: TRL targets at PDR and CDR per element."""


async def _s2_conops_scenarios(api: _Api, seed: NfiSeed) -> None:
    """TODO(D, 3.D5): the 12 ConOps scenarios of ``vv_plan.yaml``
    ``conops_scenarios_for_requirements_validation`` with their requirement links."""


async def _s3_risks(api: _Api, seed: NfiSeed) -> None:
    """TODO(D, 3.D6): residual L/C and owner seats of the v2 risks (the loop in ``_s3`` posts the
    37 risks without them today)."""


async def _s3_open_items(api: _Api, seed: NfiSeed) -> None:
    """TODO(D, 3.D4): NUMBERS ``open_decisions`` (D-PI-01/02 closed by the PI ruling, D-GND-01/02,
    D-PAY-01, D-COM-01 open); the T-07 condition and fallback."""


async def _s3_changes(api: _Api, seed: NfiSeed) -> None:
    """TODO(L, 3.L4): ``risks.yaml`` ``configuration_management.change_records``: ECP-01, ECP-02, CR-V2."""


async def _s3_validation(api: _Api, seed: NfiSeed) -> None:
    """TODO(S, 3.S5): the v2 validation plan V1–V7 (``vv_plan.yaml``) and the 12 need-validation
    rows (``stakeholders.yaml``)."""


async def _s3_assumptions(api: _Api, seed: NfiSeed) -> None:
    """TODO(S, 3.S6): the ``[ASSUMPTION]`` tags of ``budgets.yaml`` and the requirement rows whose
    ``open_item_note`` names an assumption."""


#: wave 3 (3.H6): the four negotiation scenes and the option each ends on (PI: all four in the
#: walkthrough, each signed by every involved seat); the recording seed leaves them to the team
NEGOTIATIONS = (("N1", "keep"), ("N3", "keep"), ("N7", "hold"), ("GS4", "with"))


async def _s3_negotiations(api: _Api, seed: NfiSeed) -> None:
    """Negotiation records from the four templates: N1 (science volume and downlink), N3 (payload
    peak and imaging duty against the battery), N7 (mass envelopes) and GS4 (the ground-station
    ripple), proposed with their options computed from the study. Not in the recording seed (the
    scenes are filmed); ``_s4_negotiations`` recomputes the options on the full S4 design and signs."""
    if seed.recording:
        return
    for code, _opt in NEGOTIATIONS:
        rec = await api.post(f"/api/studies/{seed.study_id}/negotiations?live=false", {"template": code})
        seed.negotiations[code] = rec


async def _s4_negotiations(api: _Api, seed: NfiSeed) -> None:
    """Wave 3 (3.H6): the S3 records with their options recomputed on the S4 design (housekeeping,
    products, stations), the option of the baseline chosen and every seat's sign-off."""
    if seed.recording:
        return
    sid = seed.study_id
    for code, opt in NEGOTIATIONS:
        rec = seed.negotiations.get(code)
        if not rec:
            continue
        url = f"/api/studies/{sid}/negotiations/{rec['id']}"
        rec = await api.call("PATCH", f"{url}?live=false", {"recompute_options": True})
        if any(o.get("key") == opt for o in rec["options"]):
            rec = await api.call("PATCH", f"{url}?live=false", {"chosen_option": opt})
        for seat in rec["seats"]:
            rec = await api.post(f"{url}/signoff?live=false",
                                 {"seat": seat, "by": "seed", "note": "baseline"})
        seed.negotiations[code] = rec


async def _s4_ait_v2(api: _Api, seed: NfiSeed) -> None:
    """TODO(A, 3.A4): the 6 models of the v2 model philosophy and the 75 verification events of
    ``vv_plan.yaml`` with their requirements, as test-matrix events."""
