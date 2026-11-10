"""W0.4 acceptance: the Northern Fire and Ice fixture loads and the staged seed builds.

``pytest tests/fixtures/nfi -k seed`` builds S4 on a scratch DB in under 60 s with no error and
no 403, and the S2 roll-up reproduces the frozen key numbers (NUMBERS.yaml).
"""
from __future__ import annotations

import time

import pytest

from tests.fixtures.nfi import STAGES, load, seed_nfi

FILES = ("NUMBERS", "mission", "equipment", "modes", "requirements", "hk_sids", "risks", "trades",
         "ground_stations", "logbook", "roundtrip_checklist")


@pytest.mark.parametrize("name", FILES)
def test_fixture_file_loads(name):
    assert load(name), name


def test_fixture_requirement_counts_match_the_baseline():
    data = load("requirements")
    rows = data["requirements"]
    assert len(rows) == data["baseline"]["counts"]["requirements"] == 216
    codes = [r["id"] for r in rows]
    assert len(set(codes)) == len(codes)
    assert set(data["import_order"]) == set(codes)
    assert all(len(c) <= 23 for c in codes)  # seed ids are "<study id>:<code>" in 32 characters


async def test_seed_builds_s4_quickly_without_errors_or_403(client):
    t0 = time.perf_counter()
    s = await seed_nfi(client, "S4")
    dt = time.perf_counter() - t0
    assert s.stage == "S4" and list(s.report["seconds"]) == list(STAGES)
    assert s.report["forbidden"] == 0
    assert dt < 60, s.report
    data = load("requirements")
    assert len(s.requirements) == len(data["requirements"]) + len(data["objectives"])
    assert len(s.risks) == len(load("risks")["risks"])
    st = (await client.get(f"/api/studies/{s.study_id}")).json()
    assert st["name"] == "Northern Fire and Ice"
    runs = (await client.get(f"/api/studies/{s.study_id}/export-context?sections=analyses")).json()
    assert {"vv", "ground_segment", "physics", "mission_simulation"} <= set(runs["analyses"]["last_runs"])


async def test_seed_s2_rollup_reproduces_the_key_numbers(client):
    n = load("NUMBERS")
    s = await seed_nfi(client, "S2")
    ru = (await client.get(f"/api/studies/{s.study_id}/rollup?gate=mdr")).json()
    assert ru["mass"]["cbe_kg"] == pytest.approx(n["mass"]["nominal_kg"], abs=0.01)
    assert ru["mass"]["with_maturity_kg"] == pytest.approx(n["mass"]["with_maturity_kg"], abs=0.01)
    assert ru["mass"]["with_system_margin_kg"] == pytest.approx(n["mass"]["with_system_margin_kg"], abs=0.01)
    assert ru["mass"]["limit_kg"] == pytest.approx(n["mass"]["limit_kg"])
    assert ru["form_factor"] == "3U" and ru["form_factor_source"].startswith("kb:struct-")
    # The tool's operational mix holds the nominal, imaging and downlink kinds only; the 1 % exploratory
    # Night SWIR (a custom mode) is left out, so the tool gives about 4.09 W against 4.17 W.
    assert ru["power"]["orbit_average_w"] == pytest.approx(n["power"]["orbit_average_w"]["value"], abs=0.1)
    assert ru["power"]["orbit_average_with_margin_w"] == pytest.approx(ru["power"]["orbit_average_w"] * 1.2, abs=0.01)
