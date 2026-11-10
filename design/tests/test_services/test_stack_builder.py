"""CubeSat stack builder (design rules §4): KB schema v2 mechanics, placement, checks,
frames and the geometry export. Pure service tests — no server, no database."""
from __future__ import annotations

import copy
import importlib.util
import math
from pathlib import Path

import pytest

from spacecdf_server.services import rule_config as rc
from spacecdf_server.services import stack_builder as sb

REPO = Path(__file__).resolve().parents[3]
SIM_GEOMETRY = REPO / "sim/packages/smo-common/src/smo_common/config/geometry.py"


def _el(i, name, kb=None, et="component", parent="bus", dom=None, q=1, mass=None, power=None):
    return {"id": i, "study_id": "s1", "name": name, "element_type": et, "parent_id": parent,
            "subsystem_domain": dom, "kb_component_id": kb, "quantity": q, "mass_kg": mass,
            "power_avg_w": power, "segment": "space"}


def eo_6u(wings="sp-clyde-3u-deploy") -> list[dict]:
    """A 6U Earth-observation CubeSat picked from the KB (EOSAT-1 class)."""
    return [
        {"id": "sc", "study_id": "s1", "name": "EOSAT", "element_type": "system", "parent_id": None, "segment": "space"},
        _el("bus", "Bus", et="subsystem", parent="sc", dom="structure"),
        _el("str", "Structure 6U", "struct-isis-6u", mass=1.2),
        _el("obc", "OBC", "obc-isis-iobc", dom="obc"),
        _el("eps", "EPS", "eps-gom-nanopow-p60", dom="power"),
        _el("bat", "Battery", "bat-gom-nanopow-bpx", dom="power"),
        _el("trx", "S-band transmitter", "txrx-endurosat-s-band-tx", dom="ttc", mass=0.2, power=4),
        _el("uhf", "UHF radio", "txrx-isis-trxvu", dom="ttc", mass=0.09, power=1.0),
        _el("spatch", "S-band patch", "ant-endurosat-sband-patch", dom="ttc"),
        _el("uant", "UHF antenna", "ant-endurosat-uhf-dipole", dom="ttc"),
        _el("rw", "Reaction wheels", "rw-cubespace-cubewheel-medium", dom="aocs", q=4),
        _el("mtq", "Magnetorquer board", "mtq-isis-imtq", dom="aocs"),
        _el("st", "Star tracker", "st-bct-nst", dom="aocs"),
        _el("ss", "Sun sensors", "ss-nss-css-01", dom="aocs", q=6),
        _el("gps", "GNSS receiver", "gps-novatel-oem719", dom="aocs"),
        _el("pl", "Imager", "pl-imager-2u-eosat", dom="payload"),
        _el("sp", "Solar wings", wings, dom="power", q=2),
        _el("bp", "Body panels", "sp-gom-nanopow-p110", dom="power", q=6),
    ]


@pytest.fixture()
def eo():
    els = eo_6u()
    units = sb.collect_units(els)
    env = sb.envelope("6U")
    spec, report = sb.auto_place(units, env)
    return els, units, env, spec, report


def _by(real, pid):
    return next(p for p in real["placements"] if p["id"] == pid)


def _sim_geometry():
    spec = importlib.util.spec_from_file_location("sim_geometry", SIM_GEOMETRY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── KB schema v2 ──────────────────────────────────────────────────────

def test_kb_mechanics_by_category():
    from spacecdf_kb.loader import KnowledgeBase
    from spacecdf_kb.mechanical import mechanical_of
    kb = {c["id"]: c for c in KnowledgeBase().search_components()}
    obc = mechanical_of(kb["obc-isis-iobc"])
    assert obc["mount_class"] == "pc104_board" and obc["stack_height_mm"] == pytest.approx(15.24)
    assert obc["connector"] == "PC/104 H1/H2"
    assert mechanical_of(kb["bat-gom-nanopow-bpx"])["mount_class"] == "pc104_module"
    st = mechanical_of(kb["st-bct-nst"])
    assert (st["mount_class"], st["anchor"], st["boresight"]) == ("u_module", "zenith", [0, 0, 1])
    assert any("C2O default" in a for a in st["assumptions"])           # no dims in the KB: said so
    patch = mechanical_of(kb["ant-endurosat-sband-patch"])
    assert (patch["mount_class"], patch["face"]) == ("face_panel", "mz")    # S band looks at the station
    uhf = mechanical_of(kb["ant-endurosat-uhf-dipole"])
    assert (uhf["mount_class"], uhf["face"]) == ("deployable", "pz")
    assert uhf["deployable"]["kind"] == "antenna" and uhf["deployable"]["length_mm"] == pytest.approx(172, abs=1)
    wing = mechanical_of(kb["sp-clyde-3u-deploy"])
    assert wing["mount_class"] == "deployable" and wing["deployable"]["wings"] == 2
    assert mechanical_of(kb["sp-gom-nanopow-p110"])["mount_class"] == "face_panel"
    assert mechanical_of(kb["rw-gom-gsw600"])["mount_class"] == "pc104_module"        # board-size wheel module
    assert mechanical_of(kb["rw-cubespace-cubewheel-small"])["mount_class"] == "bracket"
    assert mechanical_of(kb["struct-isis-6u"])["mount_class"] == "structure"
    assert mechanical_of(kb[next(i for i in kb if kb[i].get("category") == "deployer")])["mount_class"] == "none"


def test_payload_imager_category_is_schema_v2():
    from spacecdf_kb.loader import KnowledgeBase
    from spacecdf_kb.mechanical import mechanical_of
    imagers = KnowledgeBase().search_components(category="payload_imagers")
    assert len(imagers) >= 3 and all(c["category"] == "payload_imager" for c in imagers)
    for c in imagers:
        m = mechanical_of(c)
        # a U-module imager, or a small catalogue camera on a bracket (Alvium entries)
        assert m["source"] == "kb" and m["mount_class"] in ("u_module", "bracket") and m["anchor"] == "nadir"
        assert m["boresight"] == [0, 0, -1] and m["fov_deg"] > 0 and c["mass_kg"] > 0
    eosat = next(c for c in imagers if c["id"] == "pl-imager-2u-eosat")
    assert eosat["performance"]["fov_deg"] == pytest.approx(29.856)      # = sim geometry.yaml payload.fov_deg


def test_every_space_category_has_a_mechanical_default():
    from spacecdf_kb.loader import KnowledgeBase
    from spacecdf_kb.mechanical import defaults
    cats = {c.get("category") for c in KnowledgeBase().search_components()}
    space = {c for c in cats if c and not str(c).startswith("ground")}
    assert space <= set(defaults()["categories"]), space - set(defaults()["categories"])


def test_bare_element_falls_back_to_its_domain_with_assumptions():
    from spacecdf_kb.mechanical import mechanical_of
    m = mechanical_of(None, domain="payload", name="Camera")
    assert m["mount_class"] == "u_module" and m["source"] == "default" and m["assumptions"]


# ── envelope and frames ───────────────────────────────────────────────

def test_envelope_reads_the_cds_rules_file():
    cds = rc.load("cds_rules")
    E = cds["envelope_mm"]["values"]["6U"]
    env = sb.envelope("6U")
    assert sorted(env["size_mm"][:2]) == sorted(E[:2]) and env["size_mm"][2] == E[2]
    assert env["size_mm"][0] <= env["size_mm"][1]                  # stack frame: X is the short side (sim)
    assert env["swap"] == (E[0] > E[1])
    assert len(env["columns"]) == 2 and len(sb.envelope("3U")["columns"]) == 1 and len(sb.envelope("12U")["columns"]) == 4
    assert env["internal_length_mm"] == pytest.approx(E[2] - 2 * env["end_allowance_mm"])
    assert env["max_protrusion_mm"] == cds["mechanical"]["max_protrusion_mm"]["value"]
    with pytest.raises(ValueError):
        sb.envelope("27U")


@pytest.mark.parametrize("ff", ["3U", "6U", "12U"])
def test_design_frame_is_corner_origin_nadir_positive_and_a_proper_rotation(ff):
    env = sb.envelope(ff)
    E = env["design_mm"]                                          # body-frame order, as CDS-COG (F1/D15)
    assert sb.to_design_m([0, 0, 0], env) == pytest.approx([E[0] / 2000, E[1] / 2000, E[2] / 2000])
    nadir_end = sb.to_design_m([0, 0, -E[2] / 2], env)
    assert nadir_end[2] == pytest.approx(E[2] / 1000)            # +Z nadir in the design frame
    o = sb.to_design_m([0, 0, 0], env)
    cols = [[sb.to_design_m([100 * (k == 0), 100 * (k == 1), 100 * (k == 2)], env)[i] - o[i] for i in range(3)]
            for k in range(3)]
    R = [[cols[k][i] / 0.1 for k in range(3)] for i in range(3)]
    det = (R[0][0] * (R[1][1] * R[2][2] - R[1][2] * R[2][1]) - R[0][1] * (R[1][0] * R[2][2] - R[1][2] * R[2][0])
           + R[0][2] * (R[1][0] * R[2][1] - R[1][1] * R[2][0]))
    assert det == pytest.approx(1.0)


# ── auto-placement ────────────────────────────────────────────────────

def test_auto_place_follows_the_rules(eo):
    els, units, env, spec, report = eo
    real = sb.evaluate(spec, units, env)
    pl, st = _by(real, "pl"), _by(real, "st")
    assert pl["z_mm"][0] == pytest.approx(env["z0_mm"])               # payload at the nadir end
    assert st["z_mm"][1] == pytest.approx(env["z1_mm"])               # star tracker at the zenith end
    assert _by(real, "spatch@mz")["face"] == "mz"                     # S-band patch looks nadir
    assert _by(real, "uant@pz")["deployable"]["kind"] == "antenna"     # UHF from the zenith end
    wings = [p for p in real["placements"] if p["element_id"] == "sp"]
    assert sorted(p["face"] for p in wings) == ["my", "py"]           # simulator wings on +-Y
    ss_faces = {p["face"] for p in real["placements"] if p["element_id"] == "ss"}
    assert not ss_faces & {"py", "my"}                                # not under a stowed wing
    assert report["end"]["total"] <= report["start"]["total"]
    status = {c["id"]: c["status"] for c in real["checks"]}
    for cid in ("STACK-HEIGHT", "STACK-ENV", "STACK-PROTR", "STACK-COLL", "STACK-COG", "STACK-KEEPOUT", "STACK-ST-EARTH"):
        assert status[cid] == "pass", (cid, next(c for c in real["checks"] if c["id"] == cid)["detail"]["en"])
    assert status["STACK-PC104"] == "warn"                            # GomSpace + ISIS + EnduroSat boards


def test_auto_place_is_deterministic(eo):
    els, units, env, spec, _ = eo
    spec2, _ = sb.auto_place(sb.collect_units(copy.deepcopy(els)), env)
    assert spec2["columns"] == spec["columns"] and spec2["faces"] == spec["faces"]


def test_battery_and_eps_stay_close(eo):
    _, units, env, spec, _ = eo
    real = sb.evaluate(spec, units, env)
    d = math.dist(_by(real, "bat")["center_mm"], _by(real, "eps")["center_mm"])
    assert d < 0.5 * env["size_mm"][2]


def test_locked_slots_survive_auto_place(eo):
    _, units, env, spec, _ = eo
    col = next(i for i, c in enumerate(spec["columns"]) if "obc" in c)
    locked = copy.deepcopy(spec)
    # move the OBC to the other column's first free slot and lock it there
    locked["columns"][col].remove("obc")
    other = 1 - col
    locked["columns"][other].insert(1, "obc")
    locked["locks"] = {"obc": True}
    spec2, _ = sb.auto_place(units, env, locked)
    assert "obc" in spec2["columns"][other]
    assert spec2["locks"] == {"obc": True} and spec2["origins"]["obc"] == "user"


def test_normalise_spec_drops_unknowns_and_places_new_units(eo):
    els, _, env, spec, _ = eo
    els2 = els + [_el("gps2", "Spare receiver", "gps-novatel-oem719", dom="aocs")]
    units2 = sb.collect_units(els2)
    edited = copy.deepcopy(spec)
    edited["columns"][0].append("ghost")
    norm, notes = sb.normalise_spec(edited, units2, env)
    flat = [p for c in norm["columns"] for p in c]
    assert "ghost" not in flat and "gps2" in flat and notes


def test_anchors_return_to_their_ends(eo):
    _, units, env, spec, _ = eo
    col = next(i for i, c in enumerate(spec["columns"]) if "pl" in c)
    edited = copy.deepcopy(spec)
    edited["columns"][col].remove("pl")
    edited["columns"][col].append("pl")          # dragged to the top
    real = sb.realise(edited, units, env)
    assert real["spec"]["columns"][col][0] == "pl"


# ── checks that fail ──────────────────────────────────────────────────

def test_height_overflow_fails():
    els = eo_6u() + [_el(f"x{i}", f"Extra board {i}", "obc-gom-nanomind-a3200", dom="obc") for i in range(30)]
    units = sb.collect_units(els)
    env = sb.envelope("6U")
    spec, _ = sb.auto_place(units, env)
    checks = {c["id"]: c for c in sb.evaluate(spec, units, env)["checks"]}
    assert checks["STACK-HEIGHT"]["status"] == "fail"


def test_thick_wing_breaks_the_protrusion_limit():
    els = eo_6u(wings="sp-dhv-csa-3u-deploy")     # 8 mm stowed
    units = sb.collect_units(els)
    env = sb.envelope("6U")
    spec, _ = sb.auto_place(units, env)
    c = {c["id"]: c for c in sb.evaluate(spec, units, env)["checks"]}["STACK-PROTR"]
    assert c["status"] == "fail" and c["value"] == pytest.approx(8.0) and "sp" in c["element_ids"]


def test_keep_out_and_deployed_collisions(eo):
    _, units, env, spec, _ = eo
    bad = copy.deepcopy(spec)
    bad["faces"]["sp"] = [{"face": "pz", "count": 1}, {"face": "py", "count": 1}]   # a wing unfolding into the sky
    checks = {c["id"]: c for c in sb.evaluate(bad, units, env)["checks"]}
    assert checks["STACK-KEEPOUT"]["status"] == "fail"
    assert "Star tracker" in checks["STACK-KEEPOUT"]["detail"]["en"]
    two = copy.deepcopy(spec)
    two["faces"]["uant"] = [{"face": "pz", "count": 1}]
    units2 = [copy.deepcopy(u) for u in units]
    next(u for u in units2 if u["id"] == "uant")["quantity"] = 2       # two UHF modules side by side: rods cross
    two["faces"]["uant"] = [{"face": "px", "count": 2}]
    checks = {c["id"]: c for c in sb.evaluate(two, units2, env)["checks"]}
    assert checks["STACK-COLL"]["status"] == "fail"


def test_star_tracker_looking_sideways_sees_the_earth(eo):
    _, units, env, spec, _ = eo
    units2 = [copy.deepcopy(u) for u in units]
    next(u for u in units2 if u["id"] == "st")["mech"]["boresight"] = [1, 0, 0]
    c = {c["id"]: c for c in sb.evaluate(spec, units2, env, orbit_alt_km=500)["checks"]}["STACK-ST-EARTH"]
    assert c["status"] == "fail" and c["value"] < 25


# ── outputs ───────────────────────────────────────────────────────────

def test_positions_feed_cds_cog(eo):
    from spacecdf_server.services.cds_checks import evaluate_cds
    els, units, env, spec, _ = eo
    real = sb.evaluate(spec, units, env)
    pos = sb.design_positions(real, units, env)
    placed = [dict(e, position_json=pos[e["id"]]) if e["id"] in pos else e for e in els]
    # every massive leaf has a position now: CDS-COG evaluates, and agrees with STACK-COG
    for e in placed:
        if e["id"] != "sc" and e["id"] != "bus" and e.get("kb_component_id"):
            assert e.get("position_json"), e["id"]
    kb = {c["id"]: c for c in __import__("spacecdf_kb.loader", fromlist=["KnowledgeBase"]).KnowledgeBase().search_components()}
    for e in placed:   # the CDS check needs element masses (the KB copy is the other worker's F4)
        if e.get("mass_kg") is None and e.get("kb_component_id") in kb:
            e["mass_kg"] = kb[e["kb_component_id"]].get("mass_kg")
    cds = {c["id"]: c for c in evaluate_cds(placed, [], {}, "6U")["checks"]}
    stack = {c["id"]: c for c in real["checks"]}
    assert cds["CDS-COG"]["status"] == stack["STACK-COG"]["status"] == "pass"
    assert cds["CDS-COG"]["value"] == pytest.approx(stack["STACK-COG"]["value"], abs=0.05)


def test_geometry_export_is_valid_simulator_geometry(eo):
    _, units, env, spec, _ = eo
    real = sb.evaluate(spec, units, env)
    geo = sb.to_geometry(real, units, env, "EOSAT-design")
    g = _sim_geometry()
    assert g.validate_geometry(geo) == []
    assert geo["bus"]["size_m"] == pytest.approx([x / 1000 for x in env["size_mm"]])
    assert geo["payload"]["boresight"] == [0, 0, -1] and geo["payload"]["position_m"][2] < 0
    assert geo["star_trackers"][0]["position_m"][2] > 0
    assert {w["face"] for w in geo["wings"]} == {"py", "my"} and "array_drive" in geo
    assert any(a["kind"] == "patch" for a in geo["antennas"]) and any(a["kind"] == "dipole" for a in geo["antennas"])
    assert geo["mass_properties"]["cog_m"] == pytest.approx([x / 1000 for x in real["cog_mm"]], abs=1e-5)
    ids = {b["id"] for b in geo["internal"]}
    assert {"obc", "pl", "st"} <= ids and len(ids) == len(geo["internal"])
    assert "zenith" in geo["frame"]["axes"] and "nadir" in geo["frame"]["design_frame"]


def test_gate_and_cds_hooks_read_the_approved_layout(eo):
    els, units, env, spec, _ = eo
    sb.LAYOUT_CACHE["s1"] = {"form_factor": "6U", "approved": {"spec": spec}, "proposal": None, "version": 1}
    try:
        extra = sb.cds_stack_checks(els, "6U")
        assert {c["id"] for c in extra} >= {"STACK-HEIGHT", "STACK-PROTR", "STACK-COLL"}
        assert all(c["group"] == "stack" for c in extra) and "STACK-COG" not in {c["id"] for c in extra}
        gc = sb.stack_gate_check(els, "6U")
        assert gc["id"] == "GC-STACK" and gc["status"] == "warn"          # PC/104 vendor mix is a caution
        sb.LAYOUT_CACHE["s1"] = {"form_factor": "6U", "approved": None, "proposal": {"spec": spec}, "version": 2}
        assert sb.stack_gate_check(els, "6U")["status"] == "warn"
        sb.LAYOUT_CACHE.pop("s1")
        assert sb.stack_gate_check(els, "6U")["status"] == "not_evaluated"
        assert sb.cds_stack_checks(els, "6U") == []
    finally:
        sb.LAYOUT_CACHE.pop("s1", None)
