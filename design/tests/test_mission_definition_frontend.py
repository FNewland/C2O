"""Mission definition draft (frontend/src/workbench/missionDef.ts, Nov 2026): the wizard and
the editor turn the form into the requirements the server validates. Pure helpers run
under Node's type stripping; the wiring is checked on the source."""
from __future__ import annotations

import pytest

from tests.test_frontend_logic import SRC, _node

MOD = "workbench/missionDef.ts"


def test_sso_inclination_matches_the_server():
    from spacecdf_common.physics.orbit import sso_inclination
    got = _node(MOD, "[m.ssoInclination(500), m.ssoInclination(590)]")
    assert got == [pytest.approx(sso_inclination(500), abs=0.01), pytest.approx(sso_inclination(590), abs=0.01)]


def test_nfi_draft_to_requirements_and_patch():
    out = _node(MOD, """(() => {
      const d = m.defaultMissionDef()
      Object.assign(d, { altitude_km: '590', ltan: '10:30', disposal_method: 'drag_sail' })
      d.payloads = [{ ...m.emptyPayload('NIR + SWIR'), power_w: '8', power_peak_w: '12', gsd_m: '60', swath_km: '150',
                      wavelengths_nm: '865, 1610', data_per_image_mb: '32' }]
      d.link = { ...d.link, band: 'UHF', downlink_frequency_mhz: '401.5', downlink_rate_bps: '38400' }
      return { req: m.toRequirements(d), patch: m.toPatch(d), errs: m.validateDraft(d) }
    })()""")
    req = out["req"]
    assert out["errs"] == []
    assert req["orbit"]["altitude_km"] == 590 and req["orbit"]["ltan"] == "10:30"
    assert req["orbit"]["inclination_deg"] == pytest.approx(97.74, abs=0.02)
    p = req["payloads"][0]
    assert (p["gsd_m"], p["swath_km"], p["wavelengths_nm"], p["power_peak_w"]) == (60, 150, [865, 1610], 12)
    assert req["link"]["downlink_rate_bps"] == 38400 and req["link"]["uplink_rate_bps"] is None
    assert out["patch"]["orbit"]["auto_inclination"] is True


def test_round_trip_from_study_requirements_and_validation():
    out = _node(MOD, """(() => {
      const d = m.fromRequirements({ spacecraft_class: 'nano', design_lifetime_years: 3,
        orbit: { orbit_type: 'sso', altitude_km: 590, inclination_deg: 97.75, ltan: '10:30' },
        payloads: [{ name: 'Cam', mass_kg: 1, power_w: 8, wavelengths_nm: [865, 1610] }], link: { downlink_rate_bps: 38400 } })
      const bad = { ...d, altitude_km: '-1', ltan: '7h' }
      return { inc: m.effectiveInclination(d), auto: d.inclination_auto, wl: d.payloads[0].wavelengths_nm,
               rate: d.link.downlink_rate_bps, errs: m.validateDraft(bad), summary: m.orbitSummary({ orbit: { orbit_type: 'sso', altitude_km: 590, inclination_deg: 97.75, ltan: '10:30' } }) }
    })()""")
    assert out["inc"] == 97.75 and out["auto"] is False          # typed value kept, not recomputed
    assert out["wl"] == "865, 1610" and out["rate"] == "38400"
    assert "Altitude must be a positive number" in out["errs"] and "LTAN must be HH:MM" in out["errs"]
    assert out["summary"] == "SSO 590 km · 97.75° · LTAN 10:30"


def test_wiring_no_fixed_orbit_and_server_side_applies():
    wiz = (SRC / "workbench" / "MissionWizard.tsx").read_text(encoding="utf-8")
    assert "altitude_km: 500, inclination_deg: 97.4" not in wiz and "toRequirements(missionDef)" in wiz
    dec = (SRC / "workbench" / "DecisionPanel.tsx").read_text(encoding="utf-8")
    assert "orbit_altitude_km: c.altitude_km" not in dec and "/mission`" in dec
    assert "body.custom_stations" not in dec and "orbit_params" in dec
    lb = (SRC / "components" / "LinkBudgetTool.tsx").read_text(encoding="utf-8")
    assert "/mission`" in lb
    guide = (SRC / "workbench" / "GuidancePanel.tsx").read_text(encoding="utf-8")
    assert "/load`, { method: 'POST' }" in guide
