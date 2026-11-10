"""Wave 2, agent A (platform) on the Northern Fire and Ice fixture.

* Link band (hand-off X→A): with an empty ``requirements.link`` the analyses take the downlink
  from the study's design link case (else its TT&C equipment), not from the last design run's
  X-band class default, so the UHF stations are not excluded.
* Drag sail (hand-off L→A): ``deorbit.drag_area_m2`` comes from the deorbit device, so the debris
  agent (MDR-EC-10, PRR-EC-12) counts the sail.
* Caching: KB and rule-file loads are parsed once and re-read when the file changes.
"""
from __future__ import annotations

import os
import time

import pytest

from tests.fixtures.nfi import load, seed_nfi

#: what the last design run would hold for a nano-satellite with no link chosen (class default)
X_BAND_DESIGN_RUN = {"link.frequency_ghz": {"value": 8.2, "unit": "GHz"},
                     "link.downlink_rate_bps": {"value": 5e6, "unit": "bps"}}


async def _empty_link(client, monkeypatch, stage: str = "S2"):
    from spacecdf_common.models.study import LinkRequirements
    from spacecdf_server.routers.studies import get_study_store
    from spacecdf_server.services import analysis_context as ac

    s = await seed_nfi(client, stage)
    study = get_study_store()[s.study_id]
    study.requirements.link = LinkRequirements()

    async def x_band_run(study_id, option_id):
        return dict(X_BAND_DESIGN_RUN)
    monkeypatch.setattr(ac, "_load_latest_design", x_band_run)
    return s


async def _ground(client, sid: str) -> dict:
    r = await client.post(f"/api/studies/{sid}/analyses/ground_segment/run", json={})
    assert r.status_code == 200, r.text[:300]
    return r.json()["summary"]


async def test_empty_mission_link_uses_the_design_link_case(client, monkeypatch):
    from spacecdf_server.services.analysis_context import build_context

    s = await _empty_link(client, monkeypatch)
    ctx = await build_context(s.study_id)
    assert ctx.link["source"] == "link_case:DL Yellowknife 1 W rural (300 K)" and ctx.link["design_case"]
    assert ctx.link["band"] == "UHF"
    assert ctx.flat["link.frequency_ghz"] == pytest.approx(0.4015)
    assert ctx.flat["link.downlink_rate_bps"] == pytest.approx(load("NUMBERS")["links"]["downlink"]["rate_kbps"] * 1e3)

    gs = await _ground(client, s.study_id)
    assert gs["band"] == "UHF"
    assert [st["status"] for st in gs["stations"]] == ["ok"] * 4, gs["stations"]


async def test_without_link_cases_the_ttc_band_is_used(client, monkeypatch):
    from spacecdf_server.services import analysis_context as ac

    s = await _empty_link(client, monkeypatch)

    async def no_cases(study_id):
        return []
    monkeypatch.setattr(ac, "_link_cases", no_cases)
    ctx = await ac.build_context(s.study_id)
    assert ctx.link["band"] == "UHF" and ctx.link["source"].startswith("ttc element")
    gs = await _ground(client, s.study_id)
    assert gs["band"] == "UHF", gs
    assert [(st["status"], st["reason"]) for st in gs["stations"]] == [("ok", None)] * 4, gs["stations"]


async def test_mission_band_alone_sets_the_band():
    from spacecdf_common.models.study import LinkRequirements, Study
    from spacecdf_server.services.analysis_context import AnalysisContext, _derive_link

    ctx = AnalysisContext(study_id="none", study=Study(id="none", name="n"))
    ctx.study.requirements.link = LinkRequirements(band="S")
    out = await _derive_link(ctx, [])
    assert out["band"] == "S" and ctx.flat["link.frequency_ghz"] == pytest.approx(2.2)
    ctx = AnalysisContext(study_id="none", study=Study(id="none", name="n"))
    ctx.flat["link.frequency_ghz"] = 0.4      # an element parameter keeps winning
    ctx.study.requirements.link = LinkRequirements(band="X")
    await _derive_link(ctx, [])
    assert ctx.flat["link.frequency_ghz"] == 0.4


async def test_drag_sail_area_reaches_the_debris_agent(client):
    from spacecdf_agents.tier2.debris import DebrisComplianceAgent
    from spacecdf_server.routers.studies import get_study_store
    from spacecdf_server.services.analysis_context import build_context, seed_design_state

    n = load("NUMBERS")["disposal"]
    s = await seed_nfi(client, "S2")
    ctx = await build_context(s.study_id)
    assert ctx.flat["deorbit.drag_area_m2"] == pytest.approx(n["sail"]["area_m2"])

    study = get_study_store()[s.study_id]
    state = seed_design_state(ctx, requirements=study.requirements, conops=study.conops)
    assert state.get("deorbit.drag_area_m2") == pytest.approx(n["sail"]["area_m2"])
    with_sail = await DebrisComplianceAgent().execute(state)
    p = {k: pv.value for k, pv in with_sail.parameters.items()}
    assert p["debris.compliance_score"] >= 50              # MDR-EC-10 / PRR-EC-12 threshold
    assert p["debris.compliant_5yr"] == 1.0
    assert p["debris.lifetime_years"] <= 5

    ctx.flat.pop("deorbit.drag_area_m2")
    without = await DebrisComplianceAgent().execute(seed_design_state(ctx, requirements=study.requirements))
    q = {k: pv.value for k, pv in without.parameters.items()}
    assert q["debris.lifetime_years"] > p["debris.lifetime_years"]
    assert q["debris.compliance_score"] < p["debris.compliance_score"]


def test_yaml_cache_returns_private_copies_and_follows_the_file(tmp_path):
    from spacecdf_common.config.loader import load_yaml

    f = tmp_path / "x.yaml"
    f.write_text("a: {b: 1}\n", encoding="utf-8")
    first = load_yaml(f)
    first["a"]["b"] = 99                      # a caller's change does not leak into the cache
    assert load_yaml(f) == {"a": {"b": 1}}
    f.write_text("a: {b: 2}\nc: 3\n", encoding="utf-8")
    st = f.stat()
    os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))
    assert load_yaml(f) == {"a": {"b": 2}, "c": 3}


def test_kb_part_lookup_is_cached_but_fresh(tmp_path, monkeypatch):
    from spacecdf_server.services import kb_copy

    d = tmp_path / "components"
    d.mkdir()
    f = d / "parts.yaml"
    f.write_text("components:\n  - {id: p1, mass_kg: 1.0}\n", encoding="utf-8")
    monkeypatch.setattr(kb_copy, "kb_dir", lambda: d)
    assert kb_copy.find_kb_part("p1")["mass_kg"] == 1.0
    f.write_text("components:\n  - {id: p1, mass_kg: 2.0}\n", encoding="utf-8")
    st = f.stat()
    os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))
    assert kb_copy.find_kb_part("p1")["mass_kg"] == 2.0     # an edited part is seen at once (staleness)


def test_rule_files_are_validated_once_per_parse():
    from spacecdf_server.services import rule_config as rc

    rc.reload()
    t0 = time.perf_counter()
    for _ in range(500):
        rc.load("margin_policy")
    assert time.perf_counter() - t0 < 1.0
    assert rc.load("margin_policy") is rc.load("margin_policy")
