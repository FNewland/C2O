"""Wave 2 (agent R): the pure parts of services/requirement_queries.py and the wave-2 rules of
services/interface_requirements.py (half-known rows, member values, template sets, parents)."""
from __future__ import annotations

from spacecdf_server.services import interface_requirements as irs
from spacecdf_server.services.requirement_queries import TS_GROUPS, counts_of, kind_of, threshold_text, ts_group


def test_ts_group_folds_types_and_categories_into_seven_groups():
    assert ts_group({"level": "interface", "req_type": "functional"}) == "interface"
    assert ts_group({"req_type": "regulatory", "category": "disposal"}) == "regulatory"
    assert ts_group({"req_type": "performance", "category": "environment"}) == "environmental"
    assert ts_group({"req_type": "performance", "category": "launch_segment",
                     "text": "The spacecraft shall withstand the launch environments"}) == "environmental"
    assert ts_group({"req_type": "functional", "category": "operations"}) == "operational"
    assert ts_group({"req_type": "process", "category": "verification"}) == "product_assurance"
    assert ts_group({"req_type": "functional", "category": "payload"}) == "functional"
    assert ts_group({"req_type": "performance", "category": "payload"}) == "performance"
    assert ts_group({"code": "OBJ-O1", "category": "objective"}) == "functional"
    assert len(TS_GROUPS) == 7


def test_threshold_text_and_counts():
    assert threshold_text({"threshold_op": ">=", "threshold_value": 3.0, "threshold_unit": "inhibits"}) == "≥ 3 inhibits"
    assert threshold_text({"threshold_op": "before", "threshold_value": "2028-06-30"}) == "before 2028-06-30"
    assert threshold_text({"threshold_op": None}) == ""
    rows = [{"level": "stakeholder", "code": "SN-01"}, {"level": "mission", "code": "OBJ-O1", "category": "objective"},
            {"level": "interface", "code": "IR-DAT-001", "ir_json": {"origin": "rule:IF-01"}},
            {"level": "system", "code": "SYS-1", "req_type": "functional"}]
    assert [kind_of(r) for r in rows] == ["stakeholder", "objective", "generated_interface", "user"]
    c = counts_of(rows)
    assert (c["all"], c["specification"], c["specification_without_generated"]) == (4, 3, 2)


def _els():
    return {e["id"]: e for e in [
        {"id": "sc", "element_type": "system", "name": "Spacecraft"},
        {"id": "obdh", "element_type": "subsystem", "parent_id": "sc", "name": "On-Board Computer"},
        {"id": "eps", "element_type": "subsystem", "parent_id": "sc", "name": "EPS"},
        {"id": "str", "element_type": "subsystem", "parent_id": "sc", "name": "Structure", "subsystem_domain": "structure"},
        {"id": "obc", "element_type": "component", "parent_id": "obdh", "name": "OBC unit"},
        {"id": "pdu", "element_type": "component", "parent_id": "eps", "name": "PDU"},
        {"id": "bat", "element_type": "component", "parent_id": "eps", "name": "Battery"},
        {"id": "frame", "element_type": "component", "parent_id": "str", "name": "Frame"},
    ]}


def _iface(i, f, t, typ, sub, **props):
    return {"id": i, "from_element_id": f, "to_element_id": t, "type": typ, "subtype": sub, "status": "accepted",
            "properties": props}


def test_half_known_rule_and_subtypes_except():
    tpl = {"values": ["protocol", "bus", "address", "rate"]}
    assert irs.known_enough(tpl, ["bus", "address"]) and not irs.known_enough(tpl, ["bus", "address", "rate"])
    assert irs.known_enough({"values": []}, [])
    ids = lambda sub: [t["id"] for t in irs.templates_for({"type": "electrical_signal", "subtype": sub})]  # noqa: E731
    assert ids("inhibit") == ["IRT-SIG-INHIBIT"] and ids("rbf") == ids("deployment_switch") == ["IRT-SIG-POWER-PATH"]
    assert ids("umbilical") == ["IRT-SIG-SEPARATION"] and ids("other") == ["IRT-SIG-GENERIC"]


def test_boundary_row_takes_agreed_member_values_and_one_row_per_template_set():
    els = _els()
    rows = {"buses": [{"id": "b1", "name": "CAN-A", "protocol": "CAN", "bit_rate_bps": 1e6, "master_element_id": "obc"}],
            "nodes": [{"id": "n1", "bus_id": "b1", "element_id": "pdu", "address": 16, "interface_id": "u1"}]}
    sub = _iface("s1", "obdh", "eps", "data", "tm_tc", protocol="CAN")
    unit = _iface("u1", "obc", "pdu", "data", "tm_tc", protocol="CAN")
    sw = _iface("p1", "str", "eps", "electrical_signal", "deployment_switch", signal="switch and RBF")
    rbf = _iface("p2", "frame", "bat", "electrical_signal", "rbf", signal="RBF pin")
    plan = irs.coverage_plan([sub, unit, sw, rbf], els, [])
    assert plan["u1"] == ("link", "s1") and plan["p2"] == ("link", "p1")
    v = irs.fill_from_members(irs.resolve_values(sub, els, None, rows), irs.members_of("s1", plan, [sub, unit]),
                              els, None, rows)
    assert (v["bus"], v["address"], v["rate"]) == ("CAN-A", "0x10", 1000000)
    # two units at two addresses: no address for the boundary row
    rows["nodes"].append({"id": "n2", "bus_id": "b1", "element_id": "bat", "address": 17, "interface_id": "u2"})
    unit2 = _iface("u2", "obc", "bat", "data", "tm_tc", protocol="CAN")
    v2 = irs.fill_from_members(irs.resolve_values(sub, els, None, rows), [unit, unit2], els, None, rows)
    assert v2["address"] is None and v2["bus"] == "CAN-A"


def test_parent_is_the_best_matching_requirement_on_either_end():
    els = _els()
    tpl = next(t for t in irs.load_templates()["templates"] if t["id"] == "IRT-SIG-POWER-PATH")
    sw = _iface("p1", "str", "eps", "electrical_signal", "deployment_switch", signal="switch and RBF")
    reqs = [
        {"id": "a", "code": "EPS-INH-01", "level": "subsystem", "element_id": "eps",
         "text": "The EPS shall keep every load unpowered while the deployment switches are depressed, through 3 inhibits."},
        {"id": "b", "code": "VER-DEP-01", "level": "system", "element_id": "sc", "req_type": "process",
         "text": "Each deployment switch and inhibit shall be tested."},
        {"id": "c", "code": "OBD-1", "level": "subsystem", "element_id": "obdh", "text": "Unrelated inhibit."},
    ]
    assert irs.parent_for("", tpl, sw, els, reqs)["code"] == "EPS-INH-01"
    assert irs.parent_for("", tpl, sw, els, reqs[1:]) is None      # process rows and other subsystems are not parents
