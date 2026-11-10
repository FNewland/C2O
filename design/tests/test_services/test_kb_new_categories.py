"""KB additions (Nov 2026): the four new component categories and the researched entries.

adcs_integrated (AOCS), deorbit_devices (propulsion: drag sails, the disposal function), payload_optics and
payload_controllers (payload); plus researched cameras, bus units and ground equipment
that carry a ``sources:`` list. Checks the loader, the entry schema, the mechanical
defaults, the Equipment Catalog domain map, the mode / interface / FMECA classes and
the equipment-needs coverage (integrated ADCS and drag sail as alternatives).
"""
from __future__ import annotations

import math

import pytest

NEW = {  # file stem -> (singular category, entries from the research drafts)
    "adcs_integrated": ("adcs_integrated", 4),
    "deorbit_devices": ("deorbit_device", 6),
    "payload_optics": ("payload_optic", 9),
    "payload_controllers": ("payload_controller", 5),
}
NEW_IN_EXISTING = {  # researched entries added to existing files
    "payload_imagers": ["pl-av-alvium-1800c-530-vswir", "pl-av-alvium-1800c-1620m", "pl-raptor-owl-640m",
                        "pl-dragonfly-chameleon-swir", "pl-dragonfly-gecko", "pl-simera-multiscape100-cis"],
    "obcs": ["obc-gom-nanomind-z7000"],
    "transponders": ["txr-aac-spacequest-trx-u", "txr-spacemanic-murgas", "txr-gom-ax100ul", "txr-stt-r0405"],
    "antennas": ["ant-endurosat-uhf-antenna-iii"],
    "gps_receivers": ["gps-skyfox-pinav-ng"],
    "solar_panels": ["sp-endurosat-3u-body", "sp-endurosat-3u-deploy-single", "sp-endurosat-3u-deploy-double",
                     "sp-exa-dmsa-3u-a", "sp-clyde-photon-3u-side", "sp-isis-3u-xl-body"],
    "cubesat_structures": ["struct-clyde-3u"],
    "star_trackers": ["st-arcsec-twinkle"],
    "ground_antennas": ["gs-ant-m2-400cp24", "gs-ant-m2-401cp14", "gs-ant-m2-450cp-custom", "gs-ant-m2-436cp42ug",
                        "gs-ant-wimo-xquad-70", "gs-rot-yaesu-g5500dc", "gs-rot-spid-ras", "gs-rot-spid-big-ras",
                        "gs-rot-satnogs-v3"],
    "ground_rf": ["gs-rf-lna-403-filtered", "gs-rf-lna-minicircuits-zx60-p33uln", "gs-rf-lna-ssb-mast-70cm",
                  "gs-rf-pa-minicircuits-zhl-50w-52"],
    "ground_baseband": ["gs-bb-usrp-b210", "gs-bb-adalm-pluto", "gs-bb-limesdr-mini-2", "gs-bb-airspy-r2"],
}
#: Entries whose source publishes no mass / power / cost (reference only): null, never invented.
UNPUBLISHED = {"deorb-vestigo-spinnaker-2p4", "deorb-sfl-canx7-dsm"}


@pytest.fixture(scope="module")
def kb():
    from spacecdf_kb.loader import KnowledgeBase
    k = KnowledgeBase()
    k.load()
    return k


def _num_or_none(v) -> bool:
    return v is None or (isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v))


def test_new_categories_load(kb):
    for stem, (cat, n) in NEW.items():
        assert stem in kb.categories, stem
        items = kb.search_components(category=stem)
        assert len(items) == n, (stem, len(items))
        assert {c["category"] for c in items} == {cat}


def test_new_entries_in_existing_files(kb):
    for stem, ids in NEW_IN_EXISTING.items():
        have = {c["id"] for c in kb.search_components(category=stem)}
        assert set(ids) <= have, (stem, set(ids) - have)


def _new_entries(kb):
    out = [c for stem in NEW for c in kb.search_components(category=stem)]
    for stem, ids in NEW_IN_EXISTING.items():
        out += [c for c in kb.search_components(category=stem) if c["id"] in ids]
    return out


def test_each_new_entry_validates(kb):
    from spacecdf_kb.mechanical import mechanical_of
    entries = _new_entries(kb)
    assert len(entries) == sum(n for _, n in NEW.values()) + sum(len(v) for v in NEW_IN_EXISTING.values())
    for c in entries:
        cid = c["id"]
        for key in ("id", "name", "manufacturer", "category", "trl", "performance", "sources"):
            assert key in c, (cid, key)
        for key in ("mass_kg", "power_w", "cost_keur"):
            if key == "power_w" and key not in c and c["category"] in ("antenna", "solar_panel", "cubesat_structure"):
                continue                     # unpowered parts omit power_w, like the existing entries
            assert key in c and _num_or_none(c[key]), (cid, key, c.get(key))
            if c[key] is None:
                assert cid in UNPUBLISHED, (cid, key)
        assert isinstance(c["trl"], int) and 1 <= c["trl"] <= 9, cid
        assert isinstance(c["performance"], dict), cid
        assert isinstance(c["sources"], list) and c["sources"], cid
        assert all(isinstance(u, str) and u.startswith("http") for u in c["sources"]), cid
        if not str(c["category"]).startswith("ground"):
            assert (c["mass_kg"] or 0) <= 10.0, cid
            m = mechanical_of(c)
            assert m["mount_class"] and m["envelope_mm"], cid
        if c.get("estimated") is not None:
            assert isinstance(c["estimated"], list) and c["estimated"], cid
        for key in ("dimensions_mm", "operating_temp_c"):  # optional, but never null
            assert c.get(key, []) is not None, (cid, key)


def test_estimated_values_stay_flagged(kb):
    """Estimated numbers keep their flag: '(est.)' / 'unverified' in notes, or an `estimated:` list."""
    import re
    flagged = 0
    for c in _new_entries(kb):
        text = f"{c.get('notes') or ''}"
        if c.get("estimated") or re.search(r"\(est\.\)|unverified|estimate", text, re.I):
            flagged += 1
    assert flagged >= 35


def test_corrections_applied(kb):
    by = {c["id"]: c for c in kb.search_components()}
    a3200 = by["obc-gom-nanomind-a3200"]
    assert a3200["mass_kg"] == 0.024 and a3200["dimensions_mm"] == [65, 40, 7.1] and a3200["sources"]
    assert by["bat-gom-nanopow-bpx"]["performance"]["capacity_wh"] == 86.0
    assert by["eps-gom-nanopow-p60"]["mass_kg"] == 0.181
    assert by["st-cubespace-cubestar"]["performance"]["accuracy_arcsec"] == 72
    assert by["rw-cubespace-cubewheel-medium"]["performance"]["momentum_nms"] == 0.0057
    assert by["struct-isis-3u"]["cost_keur"] == 4.9


def test_new_categories_have_mechanical_defaults():
    from spacecdf_kb.mechanical import defaults, mechanical_of
    cats = defaults()["categories"]
    for _, (cat, _) in NEW.items():
        assert cat in cats, cat
    assert mechanical_of({"category": "adcs_integrated"})["mount_class"] == "pc104_module"
    sail = mechanical_of({"category": "deorbit_device"})
    assert sail["anchor"] == "zenith" and sail["face"] == "pz"
    assert mechanical_of({"category": "payload_optic"})["mount_class"] == "none"     # rides on its camera


def test_domain_map_and_rules_know_the_new_categories(kb):
    from spacecdf_server.services.equipment import DOMAIN_TO_CATEGORIES
    from spacecdf_server.services.mode_model import cfg, unit_class
    assert "adcs_integrated" in DOMAIN_TO_CATEGORIES["aocs"]
    assert "deorbit_devices" in DOMAIN_TO_CATEGORIES["propulsion"]   # PI decision: disposal = Propulsion seat
    assert {"payload_optics", "payload_controllers", "payload_imagers"} <= set(DOMAIN_TO_CATEGORIES["payload"])
    first = {stem: kb.search_components(category=stem)[0]["id"] for stem in NEW}
    classes = {stem: unit_class({"kb_component_id": kid, "name": "x"}, cfg()) for stem, kid in first.items()}
    assert classes == {"adcs_integrated": "adcs_unit", "deorbit_devices": "passive",
                       "payload_optics": "passive", "payload_controllers": "payload_electronics"}


def test_rule_files_validate_with_the_new_roles():
    from spacecdf_server.services import interface_proposer as ip
    from spacecdf_server.services.mode_model import cfg, validate_config
    assert validate_config(cfg()) == []
    rules = ip.load_rules()                      # raises RuleConfigError when invalid
    assert rules["roles"]["adcs_computer"]["kb_categories"] == ["adcs_integrated"]
    assert rules["roles"]["deorbit_device"]["deployable"] is True


def test_fmeca_library_types(kb):
    from spacecdf_server.services import rule_config as rc
    from spacecdf_server.services.fmeca_library import CONFIG, match_type
    lib = rc.load(CONFIG)
    first = {stem: kb.search_components(category=stem)[0]["id"] for stem in NEW}
    got = {stem: match_type({"name": "Unit", "kb_component_id": kid}, lib) for stem, kid in first.items()}
    assert got == {"adcs_integrated": "adcs_unit", "deorbit_devices": "deorbit_device",
                   "payload_optics": "payload", "payload_controllers": "payload"}


def test_integrated_adcs_and_drag_sail_satisfy_needs():
    from spacecdf_server.services.equipment_logic import determine_equipment_needs, needs_coverage
    needs = determine_equipment_needs(pointing_accuracy_deg=0.5, altitude_km=590, has_propulsion=False)
    cats = {n.category for n in needs}
    assert {"reaction_wheels", "magnetorquers", "sun_sensors", "deorbit_devices"} <= cats
    cov = {r["category"]: r for r in needs_coverage(needs, {"adcs_integrated", "deorbit_devices"})}
    for part in ("reaction_wheels", "magnetorquers", "sun_sensors", "star_trackers"):
        assert cov[part]["satisfied_by"] == "adcs_integrated", part
    assert cov["deorbit_devices"]["satisfied_by"] == "deorbit_devices"
    assert not cov["eps_boards"]["satisfied"]
    # separate parts still satisfy their own needs; no drag device at low altitude
    cov = {r["category"]: r for r in needs_coverage(needs, {"reaction_wheels"})}
    assert cov["reaction_wheels"]["satisfied_by"] == "reaction_wheels" and not cov["magnetorquers"]["satisfied"]
    low = determine_equipment_needs(altitude_km=400, has_propulsion=False)
    assert "deorbit_devices" not in {n.category for n in low}
    high = {n.category: n for n in determine_equipment_needs(altitude_km=700, has_propulsion=False)}
    assert high["deorbit_devices"].required


def test_null_mass_entries_do_not_break_search(kb):
    assert kb.search_components(category="deorbit_devices", max_mass_kg=1.0)
    from spacecdf_common.agents.base import DesignState
    from spacecdf_server.services.equipment import search_compatible_equipment
    res = search_compatible_equipment("propulsion", DesignState(), {"deorbit_devices": kb.search_components(category="deorbit_devices")})
    assert {m.component["id"] for m in res["deorbit_devices"]} >= UNPUBLISHED
