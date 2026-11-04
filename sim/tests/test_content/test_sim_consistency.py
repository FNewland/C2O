"""Simulator-internal consistency (2026-11 consistency pass).

One test class per inconsistency fixed in
docs/plan_2026-11/design_sim/SIM_CONSISTENCY_FIXES.md (from
sim_design_inventory.md §17 and gaps 11/14). Each pins the single source of
the decision and recomputes or compares every copy, so the copies cannot
drift apart again:

* bus under-voltage ladder  -> simulation.yaml eps.bus_protection
* battery voltages          -> subsystems/eps.yaml battery (BPX datasheet)
* imager GSD / swath        -> subsystems/payload.yaml optics + orbit.yaml
* S15 stores vs mass memory -> mcs/pus_services.yaml s15.stores
* heater / line fallbacks   -> subsystems/tcs.yaml heaters, simulation.yaml
* SoC load-shed stage table -> eps_basic.POWER_LINE_DEFS (real lines)
* S-band patch faces        -> subsystems/ttc.yaml sband_antennas
* reference orbit           -> orbit.yaml TLE (epoch, i, RAAN -> LTAN)
* body frame +Z = zenith    -> ruling Q4, every config that encodes it
"""
from __future__ import annotations

import math
import re
import struct
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

SIM = Path(__file__).resolve().parents[2]
CONFIG = SIM / "configs" / "eosat1"
FR = CONFIG / "i18n" / "fr"


def _load(rel: str):
    return yaml.safe_load((CONFIG / rel).read_text(encoding="utf-8"))


def _text(path: Path) -> str:
    # French copy uses no-break spaces before units; compare on plain spaces.
    return path.read_text(encoding="utf-8").replace(" ", " ").replace(" ", " ")


@pytest.fixture(scope="module")
def bp():
    return _load("simulation.yaml")["eps"]["bus_protection"]


@pytest.fixture(scope="module")
def bat():
    return _load("subsystems/eps.yaml")["battery"]


def _soc(v, bat):
    return (v - bat["soc_0_v"]) / (bat["soc_100_v"] - bat["soc_0_v"]) * 100.0


# ── 1. Bus under-voltage: one named value per decision ────────────────────

class TestBusProtectionLadder:
    NAMES = ("uv_v", "eps_safe_v", "aocs_safe_v", "cascade_v", "ov_v")

    def test_ladder_is_named_and_ordered(self, bp):
        assert set(self.NAMES) <= set(bp)
        assert bp["ov_v"] > bp["uv_v"] > bp["eps_safe_v"] > bp["aocs_safe_v"] > bp["cascade_v"]

    def test_mission_config_sets_no_competing_literal(self):
        eps = _load("simulation.yaml")["eps"]
        assert eps.get("uv_threshold_v") is None and eps.get("ov_threshold_v") is None
        assert (eps.get("load_shed") or {}).get("bus_voltage_v") is None
        ev = eps.get("event_thresholds") or {}
        assert ev.get("bus_warning_v") is None and ev.get("bus_critical_v") is None

    def test_every_bus_voltage_rule_names_its_level(self, bp):
        from smo_common.config.loader import resolve_threshold_ref
        sim = _load("simulation.yaml")
        rules = [r for r in _load("subsystems/fdir.yaml")["rules"]
                 if r["parameter"] == "eps.bus_voltage"]
        rules += [c for c in _load("fdir/fault_propagation.yaml")["fault_cascades"]
                  if c.get("primary_param") == "eps.bus_voltage"]
        assert rules
        for r in rules:
            ref = r.get("threshold_ref")
            assert ref and ref.startswith("eps.bus_protection."), r
            assert r["threshold"] == pytest.approx(resolve_threshold_ref(sim, ref)), r
            assert not re.search(r"\d", r.get("condition", "")), (
                "the condition must not carry a second copy of the number", r)

    def test_fdir_actions_use_the_right_levels(self, bp):
        rules = {r["action"]: r["threshold_ref"]
                 for r in _load("subsystems/fdir.yaml")["rules"]
                 if r["parameter"] == "eps.bus_voltage"}
        assert rules == {"safe_mode_eps": "eps.bus_protection.eps_safe_v",
                         "safe_mode_aocs": "eps.bus_protection.aocs_safe_v"}

    def test_s12_and_mcs_limits_equal_named_levels(self, bp):
        s12 = {d["name"]: d["low_limit"] for d in _load("monitoring/s12_definitions.yaml")["s12_definitions"]
               if d["param_id"] == 0x0105}
        assert s12["EPS Bus Voltage Low"] == bp["uv_v"]
        assert s12["EPS Bus Voltage Critical"] == bp["eps_safe_v"]
        lim = next(d for d in _load("mcs/limits.yaml")["limits"] if d["param_id"] == 0x0105)
        assert lim["yellow_low"] == bp["uv_v"]
        assert lim["red_low"] == bp["eps_safe_v"]
        assert lim["yellow_high"] == bp["ov_v"]

    def test_event_catalogue_quotes_the_levels(self, bp):
        ev = {e["id"]: e["description"] for e in _load("events/event_catalog.yaml")["events"]}
        assert f"{bp['uv_v']}V" in ev[0x0103]
        assert f"{bp['eps_safe_v']}V" in ev[0x0104]

    def test_eps_model_reads_the_named_levels(self, bp):
        from smo_common.config.loader import load_simulation_config
        from smo_simulator.models.eps_basic import EPSBasicModel
        m = EPSBasicModel()
        cfg = dict(_load("subsystems/eps.yaml"))
        cfg["simulation"] = load_simulation_config(CONFIG).eps.model_dump()
        m.configure(cfg)
        assert m._uv_threshold == bp["uv_v"] == m._shed_voltage
        assert m._ov_threshold == bp["ov_v"]
        assert m._evt["bus_warning_v"] == bp["uv_v"]
        assert m._evt["bus_critical_v"] == bp["eps_safe_v"]

    def test_code_fallbacks_are_the_schema_defaults(self, bp):
        from smo_common.config.schemas import SimEPSBusProtection
        assert SimEPSBusProtection().model_dump() == pytest.approx(
            {k: float(v) for k, v in bp.items()})

    def test_ladder_below_the_bus_cap_and_outside_nominal_band(self, bp, bat):
        from smo_simulator.models.eps_basic import BUS_CAP_V
        restore = bp["uv_v"] + _load("simulation.yaml")["eps"]["load_shed"]["restore_hysteresis_v"]
        assert restore < BUS_CAP_V < bp["ov_v"], "shed restore must be reachable under the cap"
        for name in ("uv_v", "eps_safe_v", "aocs_safe_v", "cascade_v"):
            assert _soc(bp[name], bat) < 50.0, f"{name} trips inside the nominal band"

    @pytest.mark.parametrize("rel", ["manual/08_fdir.md", "i18n/fr/manual/08_fdir.md"])
    def test_fdir_manual_quotes_eps_safe_level(self, rel, bp):
        text = _text(CONFIG / rel)
        assert f"0x0105 < {bp['eps_safe_v']}" in text
        assert f"0x0105 > {bp['ov_v']}" in text


# ── 2. Battery: the BPX 8S-1P datasheet, one curve ────────────────────────

class TestBatteryVoltages:
    def test_curve_is_the_bpx_8s1p_datasheet(self, bat):
        # GomSpace NanoPower BPX 100 Wh datasheet DS 1076870, 8S-1P column.
        assert (bat["soc_0_v"], bat["soc_100_v"], bat["voltage_nom"]) == (24.0, 33.6, 28.8)
        assert bat["capacity_wh"] == 100.0

    def test_nominal_is_the_linear_ocv_midpoint(self, bat):
        assert bat["voltage_nom"] == pytest.approx((bat["soc_0_v"] + bat["soc_100_v"]) / 2)

    def test_schema_and_model_defaults_match(self, bat):
        from smo_common.config.schemas import BatteryConfig
        from smo_simulator.models.eps_basic import EPSBasicModel
        d = BatteryConfig()
        assert (d.soc_0_v, d.soc_100_v, d.voltage_nom) == (bat["soc_0_v"], bat["soc_100_v"], bat["voltage_nom"])
        m = EPSBasicModel()
        assert (m._soc_0_v, m._soc_100_v) == (bat["soc_0_v"], bat["soc_100_v"])

    @pytest.mark.parametrize("rel", ["manual/01_eps.md", "i18n/fr/manual/01_eps.md",
                                     "manual/00_mission_overview.md",
                                     "i18n/fr/manual/00_mission_overview.md"])
    def test_manual_quotes_the_range(self, rel):
        t = _text(CONFIG / rel).replace(",", ".")
        assert "24.0–33.6 V" in t and "28.8 V" in t
        assert "21.5–29.2" not in t and "26.4 V" not in t

    @pytest.mark.parametrize("rel", ["procedures/commissioning/eps_checkout.md",
                                     "i18n/fr/procedures/commissioning/eps_checkout.md"])
    def test_eps_checkout_card_quotes_the_range(self, rel):
        t = _text(CONFIG / rel)
        assert "[24.0V, 33.6V]" in t
        assert "29.2" not in t and "21.5" not in t

    def test_mcs_battery_limits_bracket_the_curve(self, bat):
        lim = next(d for d in _load("mcs/limits.yaml")["limits"] if d["param_id"] == 0x0100)
        assert lim["red_low"] > bat["soc_0_v"]
        assert lim["yellow_high"] > bat["soc_100_v"]


# ── 3. Imager: GSD and swath from ONE set of optics ───────────────────────

@pytest.fixture(scope="module")
def derived():
    pl = _load("subsystems/payload.yaml")
    h = _load("orbit.yaml")["altitude_km"]
    half = math.atan(pl["pixels_across_track"] * pl["pixel_pitch_um"] * 1e-3 / 2
                     / pl["focal_length_mm"])
    return {"gsd_m": h * 1e3 * pl["pixel_pitch_um"] * 1e-6 / (pl["focal_length_mm"] * 1e-3),
            "swath_km": 2 * h * math.tan(half),
            "fov_deg": math.degrees(2 * half)}


def _km(text: str) -> float:
    return float(re.search(r"~(\d+(?:\.\d)?) km", text).group(1))


class TestImagerOptics:

    def test_values(self, derived):
        assert derived["gsd_m"] == pytest.approx(33.4, abs=0.05)
        assert derived["swath_km"] == pytest.approx(273.4, abs=0.5)

    def test_copies(self, derived):
        params = {p["id"]: p for p in _load("telemetry/parameters.yaml")["parameters"]}
        assert f"{derived['gsd_m']:.1f} m" in params[0x0628]["description"]
        assert _km(params[0x0619]["description"]) == pytest.approx(derived["swath_km"], abs=1.0)
        assert _load("planning/planner.yaml")["imaging"]["fov_deg"] == pytest.approx(
            derived["fov_deg"], abs=1e-3)
        assert _load("geometry.yaml")["payload"]["fov_deg"] == pytest.approx(
            derived["fov_deg"], abs=1e-3)
        man = _text(CONFIG / "manual" / "06_payload.md")
        assert f"~{derived['gsd_m']:.1f} m" in man
        assert _km(man[man.index("Swath Width"):]) == pytest.approx(derived["swath_km"], abs=1.0)

    def test_triscape100_is_cited_for_power_not_optics(self):
        """The TriScape100 (580 mm, 4.75 m GSD) must never again be quoted as
        if it were EOSAT-1's optics: every comment block that gives its GSD
        also says those optics are NOT the mission's."""
        for rel in ("subsystems/eps.yaml", "subsystems/payload.yaml"):
            text = (CONFIG / rel).read_text(encoding="utf-8")
            for block in re.split(r"\n(?!#)", text):
                if "TriScape" in block and "4.75 m" in block:
                    assert "NOT" in block, f"{rel}: TriScape GSD quoted as EOSAT-1's"


# ── 4. S15 packet stores vs the payload mass memory ───────────────────────

@pytest.fixture(scope="module")
def stores():
    return {s["id"]: s for s in _load("mcs/pus_services.yaml")["services"]["s15"]["stores"]}


class TestStores:

    def test_engine_enforces_the_configured_packet_limits(self, stores):
        from smo_simulator.engine import SimulationEngine
        eng = SimulationEngine(CONFIG, speed=1.0)
        caps = eng._tm_storage._capacities
        for sid, st in stores.items():
            assert caps[sid] == st["capacity_packets"], sid

    def test_partitions_match_memory_map(self, stores):
        regions = {r["name"]: r for r in _load("subsystems/memory_map.yaml")["memory_regions"]}
        for st in stores.values():
            assert regions[st["name"]]["size"] == st["capacity_bytes"], st["name"]

    def test_hk_partition_holds_its_packets(self, stores):
        largest = 0
        for s in _load("telemetry/hk_structures.yaml")["structures"]:
            data = sum(struct.calcsize(">" + p["pack_format"]) for p in s["parameters"])
            largest = max(largest, 6 + 10 + 1 + data + 2)   # primary + PUS sec + SID + CRC
        hk = stores[1]
        assert hk["capacity_packets"] * largest <= hk["capacity_bytes"]

    def test_science_store_is_not_the_mass_memory(self, stores):
        mass_mb = _load("subsystems/payload.yaml")["total_storage_mb"]
        assert mass_mb * 1e6 > 100 * stores[3]["capacity_bytes"]
        txt = (CONFIG / "mcs" / "pus_services.yaml").read_text(encoding="utf-8")
        assert "product" in txt.lower() and "20 GB" in txt


# ── 5. Code fallbacks equal the config they fall back from ────────────────

class TestFallbacks:
    def test_tcs_heater_fallbacks(self):
        from smo_simulator.models.tcs_basic import TCSBasicModel
        for h in _load("subsystems/tcs.yaml")["heaters"]:
            assert TCSBasicModel._HEATER_POWER[h["name"]] == h["power_w"], h["name"]
            assert TCSBasicModel._THERMOSTAT[h["name"]] == (h["off_temp_c"], h["on_temp_c"]), h["name"]

    def test_eps_line_power_fallbacks(self):
        from smo_simulator.models.eps_basic import EPSBasicModel
        cfg = _load("simulation.yaml")["eps"]["line_power_w"]
        for line, w in EPSBasicModel.LINE_POWER_DEFAULTS_W.items():
            assert cfg[line] == w, line


# ── 6. SoC load-shed stages name real, switchable lines ───────────────────

class TestLoadShedStages:
    def test_lines_exist_and_are_switchable(self):
        from smo_simulator.models.eps_basic import POWER_LINE_SWITCHABLE
        stages = _load("fdir/fault_propagation.yaml")["load_shedding_stages"]
        for key, st in stages.items():
            for entry in st.get("power_lines") or []:
                assert entry["line"] in POWER_LINE_SWITCHABLE, (key, entry)
                assert POWER_LINE_SWITCHABLE[entry["line"]], (key, entry)
                assert entry["action"] == "power_off", (key, entry)
                assert entry["line"] != "aocs_wheels", "MTQ and AOCS sensors hang off it"

    def test_aocs_safe_hold_is_coarse_sun(self):
        codes = _load("aocs/aocs_mode_codes.yaml")
        names = {int(k): v["name"] for k, v in (codes.get("modes") or codes).items()
                 if str(k).isdigit()}
        for st in _load("fdir/fault_propagation.yaml")["load_shedding_stages"].values():
            for c in st.get("subsystem_commands") or []:
                if c["subsystem"] == "aocs" and c["command"] == "mode":
                    assert names[int(c["value"])] == "COARSE_SUN"

    def test_stage_power_lines_are_executed(self):
        from smo_simulator.fdir import LoadSheddingManager
        stages = _load("fdir/fault_propagation.yaml")["load_shedding_stages"]
        m = LoadSheddingManager()
        off: list[str] = []
        m.register_callback("eps_power_line_off", off.append)
        m.register_stage_config(3, stages["stage_3"])
        m.execute_stage(3)
        assert off == [e["line"] for e in stages["stage_3"]["power_lines"]]


# ── 7. S-band patch accommodation ─────────────────────────────────────────

class TestSBandPatches:
    FACE = {"px": [1, 0, 0], "mx": [-1, 0, 0], "py": [0, 1, 0],
            "my": [0, -1, 0], "pz": [0, 0, 1], "mz": [0, 0, -1]}

    def test_faces_and_boresights(self):
        ants = _load("subsystems/ttc.yaml")["sband_antennas"]
        assert {a["face"] for a in ants} == {"pz", "mz"}
        for a in ants:
            assert a["boresight"] == self.FACE[a["face"]]
            assert a["gain_dbi"] == _load("subsystems/ttc.yaml")["sc_gain_dbi"]

    def test_geometry_draws_exactly_these(self):
        from smo_common.config.geometry import validate_geometry
        assert validate_geometry(_load("geometry.yaml"), CONFIG) == []

    @pytest.mark.parametrize("rel", ["manual/05_ttc.md", "i18n/fr/manual/05_ttc.md"])
    def test_manual_lists_both_patches(self, rel):
        t = _text(CONFIG / rel)
        assert "(+Z)" in t and "(-Z)" in t


# ── 8. Reference orbit ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def orbit():
    return _load("orbit.yaml")


class TestReferenceOrbit:

    def test_tle_epoch_is_t0(self, orbit):
        f = orbit["tle_line1"].split()[3]
        yy, doy = int(f[:2]), float(f[2:])
        t0 = datetime.fromisoformat(orbit["t0_epoch"].replace("Z", "+00:00"))
        assert 2000 + yy == t0.year
        assert doy == pytest.approx(t0.timetuple().tm_yday + t0.hour / 24 + t0.minute / 1440)

    def test_inclination_declared_once(self, orbit):
        assert float(orbit["tle_line2"].split()[2]) == pytest.approx(orbit["inclination_deg"], abs=1e-3)

    def test_raan_gives_ltan_1000(self, orbit):
        """RAAN at epoch minus the Sun's right ascension at epoch -> LTAN."""
        raan = float(orbit["tle_line2"].split()[3])
        t0 = datetime.fromisoformat(orbit["t0_epoch"].replace("Z", "+00:00"))
        n = (t0 - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).total_seconds() / 86400
        L = (280.460 + 0.9856474 * n) % 360
        g = math.radians((357.528 + 0.9856003 * n) % 360)
        lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
        eps = math.radians(23.439 - 4e-7 * n)
        ra_sun = math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))) % 360
        ltan_h = (12.0 + (raan - ra_sun) / 15.0) % 24
        assert ltan_h == pytest.approx(10.0, abs=10 / 60)

    def test_code_fallbacks_use_the_tle_orbit(self, orbit):
        from smo_planner.budget_tracker import ORBIT_ALTITUDE_KM
        assert ORBIT_ALTITUDE_KM == orbit["altitude_km"]
        src = (SIM / "packages/smo-planner/src/smo_planner/constraint_checkers.py").read_text()
        assert "450km" not in src and "450 km" not in src


# ── 9. Body frame: +Z = zenith, -Z = nadir (ruling Q4) ────────────────────

class TestBodyFrame:
    def test_every_copy_agrees(self):
        from smo_simulator.models.aocs_basic import _ST_BORESIGHTS
        geo = _load("geometry.yaml")
        assert geo["payload"]["boresight"] == [0, 0, -1]           # imager to nadir
        assert _load("subsystems/eps.yaml")["solar_panels"]["mz_area_m2"] == 0.0
        assert tuple(geo["star_trackers"][0]["boresight"]) == pytest.approx(_ST_BORESIGHTS[1])
        assert tuple(geo["star_trackers"][1]["boresight"]) == pytest.approx(_ST_BORESIGHTS[2])
        assert _ST_BORESIGHTS[1][2] > 0                            # ST1 to zenith
        for rel in ("geometry.yaml", "subsystems/eps.yaml"):
            assert "+Z = zenith" in (CONFIG / rel).read_text(encoding="utf-8")
