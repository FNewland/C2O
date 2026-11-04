"""Product tree levels (ECSS-M-ST-10C / NASA): placement rules, the space-segment migration,
spacecraft scoping for the stack builder, and the GC-PRODUCT-TREE level check."""
from __future__ import annotations

import itertools

from spacecdf_server.services import product_tree as pt


def _ids():
    n = itertools.count(1)
    return lambda: f"new{next(n)}"


def legacy_tree() -> list[dict]:
    """Subsystems hanging directly off the space segment, plus subsystems typed ``system``."""
    E = lambda i, t, p, **k: {"id": i, "study_id": "s", "name": k.pop("name", i), "element_type": t, "parent_id": p,
                                "deleted_at": None, "segment": k.pop("segment", "space"), **k}
    return [
        E("m", "mission", None, name="Mission"),
        E("ss", "segment", "m", name="Space Segment"),
        E("gs", "segment", "m", name="Ground Segment", segment="ground"),
        E("eps", "subsystem", "ss", name="EPS", subsystem_domain="power", position_json=[0.05, 0.1, 0.2]),
        E("bat", "component", "eps", name="Battery", subsystem_domain="power", mass_kg=0.3),
        E("aocs", "system", "ss", name="AOCS", subsystem_domain="aocs", mass_kg=0.5),       # typed one level too high
        E("cam", "component", "ss", name="Camera", subsystem_domain="payload", mass_kg=1.0),
        E("st", "system", "gs", name="Ground Station", subsystem_domain="ground", segment="ground"),
    ]


def test_levels_follow_ecss():
    assert [pt.tree_level(t) for t in ("mission", "segment", "system", "subsystem", "component")] == [0, 1, 2, 3, 4]
    seg = {"id": "ss", "element_type": "segment"}
    assert pt.placement_error("system", seg) is None
    for bad in ("subsystem", "component"):
        err = pt.placement_error(bad, seg)
        assert err and err["error"] == "product_tree_level" and err["allowed"] == ["system"]
        assert "Spacecraft" in err["message"]["en"] and "satellite" in err["message"]["fr"]
    assert pt.placement_error("subsystem", {"element_type": "mission"}) is not None
    assert pt.placement_error("subsystem", {"element_type": "system"}) is None
    assert pt.placement_error("component", None) is None          # the root is free (fragments, imports)
    assert pt.placement_error("mode", seg) is None                # not a tree type


def test_migration_inserts_a_spacecraft_and_keeps_ids():
    els = legacy_tree()
    plan = pt.plan_migration(els, _ids())
    assert len(plan["create"]) == 1 and not plan["ambiguous"]
    sc = plan["create"][0]
    assert sc["element_type"] == "system" and sc["parent_id"] == "ss" and sc["name"] == "Spacecraft"
    assert sc.get("mass_kg") is None                              # no double count in the roll-up
    moved = {u["id"]: u["changes"] for u in plan["update"]}
    assert set(moved) == {"eps", "aocs", "cam"}
    assert all(c["parent_id"] == sc["id"] for c in moved.values())
    assert moved["aocs"]["element_type"] == "subsystem" and "element_type" not in moved["eps"]
    after = {e["id"]: e for e in pt.apply_plan(els, plan)}
    assert after["bat"]["parent_id"] == "eps"                     # equipment stays with its subsystem
    assert after["eps"]["position_json"] == [0.05, 0.1, 0.2]      # placements untouched
    assert after["st"]["parent_id"] == "gs"                       # ground segment left alone
    assert pt.misplaced(list(after.values())) == []
    # idempotent
    again = pt.plan_migration(list(after.values()), _ids())
    assert again == {"create": [], "update": [], "ambiguous": []}


def test_migration_reuses_the_one_spacecraft_and_flags_ambiguity():
    els = legacy_tree() + [{"id": "sc", "study_id": "s", "name": "Spacecraft", "element_type": "system",
                            "parent_id": "ss", "deleted_at": None, "segment": "space"}]
    plan = pt.plan_migration(els, _ids())
    assert plan["create"] == [] and {u["changes"]["parent_id"] for u in plan["update"]} == {"sc"}
    two = els + [{"id": "sc2", "study_id": "s", "name": "Spacecraft 2", "element_type": "system",
                  "parent_id": "ss", "deleted_at": None, "segment": "space"}]
    plan = pt.plan_migration(two, _ids())
    assert plan["ambiguous"] == ["ss"] and not plan["update"]


def test_spacecraft_like_systems_are_not_subsystems():
    kids: dict = {}
    assert not pt.is_misplaced_subsystem({"id": "a", "element_type": "system", "name": "Spacecraft",
                                          "subsystem_domain": "payload"}, kids)   # old preset domain
    assert not pt.is_misplaced_subsystem({"id": "b", "element_type": "system", "name": "Imager",
                                          "subsystem_domain": "payload", "quantity": 4}, kids)
    assert pt.is_misplaced_subsystem({"id": "c", "element_type": "system", "name": "EPS",
                                      "subsystem_domain": "power"}, kids)


def test_stack_scope_is_one_spacecraft():
    E = lambda i, t, p, **k: {"id": i, "study_id": "s", "name": i, "element_type": t, "parent_id": p,
                                "deleted_at": None, "segment": "space", **k}
    els = [E("m", "mission", None), E("ss", "segment", "m"), E("sc1", "system", "ss"), E("sc2", "system", "ss"),
           E("p1", "subsystem", "sc1"), E("u1", "component", "p1"), E("p2", "subsystem", "sc2"), E("u2", "component", "p2")]
    assert [s["id"] for s in pt.spacecraft_systems(els)] == ["sc1", "sc2"]
    assert {e["id"] for e in pt.scope_to_spacecraft(els)} == {"m", "ss", "sc1", "p1", "u1"}
    assert {e["id"] for e in pt.scope_to_spacecraft(els, "sc2")} == {"m", "ss", "sc2", "p2", "u2"}
    one = [e for e in els if e["id"] not in ("sc2", "p2", "u2")]
    assert pt.scope_to_spacecraft(one) == one


def test_gate_product_tree_check_flags_subsystems_under_a_segment():
    from spacecdf_server.services.gate_checks import _check
    els = legacy_tree()
    ctx = {"elements": els, "requirements": [], "interfaces": [], "params": {}}
    c = _check("GC-PRODUCT-TREE", "SRR", ctx, {})
    assert c["status"] == "fail" and c["counts"]["misplaced"] == 3
    fixed = pt.apply_plan(els, pt.plan_migration(els, _ids()))
    c = _check("GC-PRODUCT-TREE", "SRR", {**ctx, "elements": fixed}, {})
    assert c["status"] == "pass" and c["counts"]["misplaced"] == 0 and c["counts"]["systems"] == 1


def test_default_architectures_put_spacecraft_under_the_space_segment():
    for arch, segs in pt.ARCHITECTURES.items():
        for s in segs:
            for sysdef in s["systems"]:
                assert not sysdef.get("spacecraft") or s["segment"] == "space", arch
        if segs:
            space = next(s for s in segs if s["segment"] == "space")
            assert any(x.get("spacecraft") for x in space["systems"]), arch
