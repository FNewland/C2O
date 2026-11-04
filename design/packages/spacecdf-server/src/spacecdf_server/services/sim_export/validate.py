"""Validate an exported configuration with the simulator's own loaders (Nov 2026).

The simulator's schemas are strict (``extra="forbid"``); this runs every loader the
simulator, MCS and planner use on start-up against an exported directory and returns the
problems as text. It needs the simulator packages (``sim/packages/*/src``); they are found
next to the template directory (the monorepo layout) and added to ``sys.path`` on demand.
When they are not available the result says so instead of failing.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def sim_packages(template_dir: Path) -> list[Path]:
    root = Path(template_dir).resolve().parents[1]          # sim/configs/eosat1 -> sim
    return [p for p in sorted((root / "packages").glob("*/src")) if p.is_dir()]


def ensure_sim_importable(template_dir: Path) -> bool:
    for p in sim_packages(template_dir):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    try:
        import smo_common.config.loader  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def validate_dir(config_dir: Path, template_dir: Path) -> dict[str, Any]:
    """``{"available": bool, "errors": [str], "checked": [str]}``."""
    if not ensure_sim_importable(template_dir):
        return {"available": False, "errors": [], "checked": []}
    from smo_common.config import loader as L
    from smo_common.config.geometry import GeometryError, load_geometry
    from smo_common.config.schemas import ScenarioConfig
    import yaml

    cfg = Path(config_dir)
    errors: list[str] = []
    checked: list[str] = []

    def run(name: str, fn) -> Any:
        checked.append(name)
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {exc}")
            return None

    run("mission.yaml", lambda: L.load_mission_config(cfg))
    run("orbit.yaml", lambda: L.load_orbit_config(cfg))
    sub = {"eps": "EPSConfig", "aocs": "AOCSConfig", "tcs": "TCSConfig", "obdh": "OBDHConfig", "ttc": "TTCConfig",
           "payload": "PayloadConfig", "prop": "PropConfig"}
    from smo_common.config import schemas as S
    for n, cls in sub.items():
        if not (cfg / "subsystems" / f"{n}.yaml").is_file():
            errors.append(f"subsystems/{n}.yaml: missing")
            continue
        run(f"subsystems/{n}.yaml", lambda n=n, cls=cls: L.load_subsystem_config(cfg, n, getattr(S, cls)))
    run("subsystems/fdir.yaml", lambda: L.load_fdir_config(cfg))
    run("simulation.yaml", lambda: L.load_simulation_config(cfg))
    run("telemetry/hk_structures.yaml", lambda: L.load_hk_structures(cfg))
    run("telemetry/parameters.yaml", lambda: L.load_parameters(cfg))
    run("mcs/limits.yaml", lambda: L.load_limits(cfg))
    run("commands/tc_catalog.yaml", lambda: L.load_tc_catalog(cfg))
    run("events/event_catalog.yaml", lambda: L.load_event_catalog(cfg))
    run("mcs/displays.yaml", lambda: L.load_mcs_displays(cfg))
    run("mcs/positions.yaml", lambda: L.load_positions(cfg))
    run("subsystems/memory_map.yaml", lambda: L.load_memory_map(cfg))
    run("mcs/pus_services.yaml", lambda: L.load_pus_service_config(cfg))
    run("planning/activity_types.yaml", lambda: L.load_activity_types(cfg))

    def geom() -> None:
        try:
            load_geometry(cfg)
        except GeometryError as exc:
            raise ValueError("; ".join(exc.args[0] if exc.args and isinstance(exc.args[0], list) else map(str, exc.args)))
    run("geometry.yaml", geom)
    for p in sorted((cfg / "scenarios").glob("*.yaml")):
        run(f"scenarios/{p.name}", lambda p=p: ScenarioConfig.model_validate(yaml.safe_load(p.read_text(encoding="utf-8"))))
    try:
        from smo_simulator.monitoring_loader import load_s12_definitions, load_s19_rules
        run("monitoring/s12_definitions.yaml", lambda: load_s12_definitions(cfg))
        run("monitoring/s19_rules.yaml", lambda: load_s19_rules(cfg))
    except Exception:  # noqa: BLE001 — simulator package not importable: the common loaders still ran
        pass
    # the TC catalogue must still be a valid commanding catalogue (aliases, quick commands)
    try:
        from smo_common.commanding.catalog import load_catalog
        run("commands (commanding catalogue)", lambda: load_catalog(cfg))
    except Exception:  # noqa: BLE001
        pass
    return {"available": True, "errors": errors, "checked": checked}
