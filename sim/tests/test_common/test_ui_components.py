"""Shared state vocabulary (smo_common/ui/components.js) under node.

Brief §1.3: every control and value is in exactly one state — enabled,
disabled (with a reason), armed, active, stale (last value kept, with its
age), no data (labelled, never an em-dash), alarm (colour + shape + text).
These pin the markup contract workers B–D build on.
"""
from __future__ import annotations

import pytest

from tests.test_common.test_i18n_runtime import NODE, run_js

pytestmark = pytest.mark.skipif(NODE is None, reason="node is required")

C = "const C = await import('./components.js');\n"


def test_value_state_verdicts(tmp_path):
    out = run_js(tmp_path, C + """
      return [C.valueState(82.1), C.valueState(null, 1), C.valueState(82.1, 1, {intervalS: 4}),
              C.valueState(82.1, 15, {intervalS: 4}), C.valueState(82.1, 59, {intervalS: 4}),
              C.valueState(82.1, 900, {verdict: 'disabled'}), C.valueState(undefined, null),
              C.valueState(3, 2, {verdict: 'stale'})];
    """)
    assert out == ["live", "nodata", "live", "degraded", "stale", "off", "nodata", "stale"]


def test_param_stale_keeps_its_value_and_age(tmp_path):
    out = run_js(tmp_path, C + """
      const def = {name: 'eps.bat_soc', hex: '0x0101', units: '%', hk_interval_s: 4};
      const lim = {yellow_low: 25, yellow_high: 95, red_low: 15, red_high: 100};
      return { stale: C.renderParam(def, 82.1, {...lim, age_s: 59}),
               none: C.renderParam(def, null, lim),
               off: C.renderParam(def, 82.1, {...lim, age_s: 900, verdict: 'disabled'}),
               warn: C.renderParam(def, 22, {...lim, age_s: 1}) };
    """)
    s = out["stale"]
    assert 'class="ds-param stale"' in s and "82.1" in s and "ds-age" in s and "59 s" in s
    assert "—" not in s.split('class="vl"')[1].split("</span></span>")[0]
    assert "no data" in out["none"] and "is-nodata" in out["none"] and "—" not in out["none"]
    assert "not enabled" in out["off"] and "82.1" not in out["off"].split('class="vl"')[1].split("ds-devbar")[0]
    w = out["warn"]
    assert 'class="ds-param w"' in w and "g-warn-down" in w and ">L<" in w.replace("</span>", "<")


def test_render_value_states(tmp_path):
    out = run_js(tmp_path, C + """
      const lim = {yellow_low: 25, yellow_high: 95, red_low: 15, red_high: 100};
      return [C.renderValue(82.1, {units: '%', digits: 1}),
              C.renderValue(82.1, {units: '%', digits: 1, ageS: 59, intervalS: 4}),
              C.renderValue(null), C.renderValue(12.4, {limits: lim, digits: 1}),
              C.renderValue(3, {eng: 'COARSE_SUN (3)'})];
    """)
    live, stale, none, alarm, eng = out
    assert live.startswith('<span class="ds-readout"><span class="ds-value">82.1<span class="u">%</span>')
    assert "is-stale" in stale and "ds-age" in stale and "59 s" in stale
    assert none == '<span class="ds-nodata">no data</span>'
    assert "is-alarm" in alarm and "g-alarm-down" in alarm and "LL" in alarm and "below the alarm limit" in alarm
    assert "COARSE_SUN (3)" in eng


def test_disabled_button_has_a_reachable_reason(tmp_path):
    out = run_js(tmp_path, C + """
      return [C.renderButton({label: 'Send', state: 'disabled', reason: 'No contact', id: 'b1'}),
              C.renderButton({label: 'Send TC', kind: 'critical', state: 'armed'}),
              C.renderButton({label: 'Running', state: 'active', toggle: true}),
              C.renderButton({label: 'Refresh'})];
    """)
    dis, armed, active, plain = out
    assert 'aria-disabled="true"' in dis and 'data-reason="No contact"' in dis
    assert 'aria-describedby="b1-why"' in dis and '<span id="b1-why" class="ds-sr" hidden>No contact</span>' in dis
    assert " disabled" not in dis.replace("aria-disabled", ""), "must stay focusable"
    assert "is-armed" in armed and "Confirm: Send TC" in armed and "ds-arm-t" in armed
    assert "is-active" in active and 'aria-pressed="true"' in active
    assert plain == '<button type="button" class="ds-btn">Refresh</button>'


def test_and_table_states(tmp_path):
    out = run_js(tmp_path, C + """
      const params = [{id: 0x0101, hex: '0x0101', name: 'eps.bat_soc', units: '%'},
                      {id: 0x0100, hex: '0x0100', name: 'eps.bat_voltage', units: 'V'},
                      {id: 0x0406, hex: '0x0406', name: 'tcs.temp_obc', units: 'C'}];
      return C.renderAndTable(params, {
        params: {'0x0101': 82.1, '0x0100': 26.4}, ages: {'257': 1, '256': 59},
        limitState: {}, limits: {}, verdicts: {'0x0100': 'stale'} });
    """)
    rows = out.split("<tr ")[1:]
    assert ">82.1<" in rows[0]
    assert 'class="stale"' in rows[1] and ">26.4<" in rows[1], "stale keeps the last value"
    assert 'class="is-nodata"' in rows[2] and "no data" in rows[2]
    assert "—" not in out


def test_gauge_link_and_mode(tmp_path):
    out = run_js(tmp_path, C + """
      const S = await import('./state.js');
      const lim = {yellow_low: 2, yellow_high: 40, red_low: 0, red_high: 45};
      return { cau: C.renderGauge(41.4, lim, {label: 'bat_temp', units: 'C', digits: 1}),
               off: C.renderGauge(null, lim, {label: 'fpa', reason: 'Payload is off'}),
               none: C.renderGauge(null, lim, {label: 'x'}),
               up: C.renderLinkBanner(S.linkState({sa: {in_contact: true, ground_station_name: 'Troll', last_frame_age_s: 1}})),
               late: C.renderLinkBanner(S.linkState({sa: {in_contact: true, ground_station_name: 'Troll', last_frame_age_s: 82}})),
               down: C.renderLinkBanner(S.linkState({sa: {in_contact: false}})),
               safe: C.renderModeBanner(S.modeState({params: {'0x0300': 1}})),
               emg: C.renderModeBanner(S.modeState({params: {'0x0300': 2}})),
               unk: C.renderModeBanner(S.modeState({})) };
    """)
    assert 'class="ds-gauge is-caution"' in out["cau"] and "41.4" in out["cau"]
    assert "is-disabled" in out["off"] and 'data-reason="Payload is off"' in out["off"]
    assert "is-nodata" in out["none"] and "no data" in out["none"]
    assert 'ds-banner ok' in out["up"] and "In contact" in out["up"] and "Troll" in out["up"]
    assert "is-stale" in out["late"] and "telemetry stale" in out["late"]
    assert "is-nodata" in out["down"] and "No contact" in out["down"]
    assert "is-caution" in out["safe"] and ">SAFE<" in out["safe"]
    assert "is-alarm" in out["emg"] and "no data" in out["unk"]


def test_state_strings_are_translated(tmp_path, monkeypatch):
    """With the REAL shared catalog: the state labels read in French."""
    import json
    from tests.test_common import test_i18n_runtime as rt
    real = json.loads((rt.SHARED / "i18n" / "fr.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(rt, "FR_CAT", real)
    out = run_js(tmp_path, C + """
      await M.setLang('fr');
      return [C.renderNoData(), C.renderNoData({off: true}),
              C.renderButton({label: 'Envoyer', state: 'armed'}),
              C.renderParam({name: 'V', hex: '0x0001'}, 1)];
    """)
    assert ">aucune donnée<" in out[0]
    assert "non activé" in out[1]
    assert "Confirmer\u00a0: Envoyer" in out[2]
    assert "aucune limite définie" in out[3]
