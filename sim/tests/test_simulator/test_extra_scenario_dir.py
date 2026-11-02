"""Scenarios authored in the scenario generator reach the simulator.

On the hosted deployment the generator saves to a persistent volume
(SMO_SCENARIO_DIR) and the simulator loads that folder as well as the built-in
one (SMO_EXTRA_SCENARIO_DIR). See deploy/gcp and docker/compose.yaml.
"""
import importlib.util
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer
from aiohttp import web

from smo_simulator.engine import SimulationEngine

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs" / "eosat1"
GENERATOR = REPO_ROOT / "tools" / "scenario_generator.py"

SCENARIO = 'name: "Extra Dir Scenario"\ndifficulty: BASIC\nduration_s: 600\nbriefing: x\nevents: []\n'


def _load_generator(monkeypatch, out_dir: Path):
    monkeypatch.setenv("SMO_SCENARIO_DIR", str(out_dir))
    spec = importlib.util.spec_from_file_location("scenario_generator_extra", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_engine_loads_extra_scenario_dir(tmp_path, monkeypatch):
    (tmp_path / "extra.yaml").write_text(SCENARIO)
    monkeypatch.setenv("SMO_EXTRA_SCENARIO_DIR", str(tmp_path))
    engine = SimulationEngine(CONFIG_DIR, speed=1.0)
    names = [s["name"] for s in engine._scenario_engine.list_scenarios()]
    assert "Extra Dir Scenario" in names
    assert len(names) > 1  # the built-in scenarios are still there


def test_engine_without_extra_dir_has_only_builtins(monkeypatch):
    monkeypatch.delenv("SMO_EXTRA_SCENARIO_DIR", raising=False)
    engine = SimulationEngine(CONFIG_DIR, speed=1.0)
    names = [s["name"] for s in engine._scenario_engine.list_scenarios()]
    assert "Extra Dir Scenario" not in names


async def test_generator_saves_to_redirected_dir(tmp_path, monkeypatch):
    out = tmp_path / "scenarios"
    gen = _load_generator(monkeypatch, out)
    assert gen.SCENARIO_DIR == out
    app = web.Application()
    app.router.add_post("/generate", gen.handle_generate)
    async with TestClient(TestServer(app)) as client:
        resp = await client.post("/generate", json={
            "name": "Saved Here", "difficulty": "BASIC", "duration_s": 600,
            "briefing": "b", "events": [], "save": True})
        body = await resp.json()
    assert body["ok"], body
    assert (out / body["filename"]).is_file()
    # Outside the repository: never the absolute server path on the page.
    assert not body["path"].startswith("/")
