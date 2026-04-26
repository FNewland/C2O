"""SpaceCDF KB — Knowledge Base loader and search.

Loads all YAML data files and provides search/filter capabilities
for the design agents and UI.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from spacecdf_common.config.loader import load_yaml

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"


class KnowledgeBase:
    """In-memory knowledge base loaded from YAML files."""

    def __init__(self, data_dir: str | Path | None = None):
        self._data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._components: dict[str, list[dict]] = {}
        self._launch_vehicles: list[dict] = []
        self._ground_stations: list[dict] = []
        self._cost_models: dict[str, Any] = {}
        self._standards: dict[str, Any] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all knowledge base data from YAML files."""
        if self._loaded:
            return

        # Load components
        comp_dir = self._data_dir / "components"
        if comp_dir.is_dir():
            for path in sorted(comp_dir.glob("*.yaml")):
                try:
                    data = load_yaml(path)
                    items = data.get("components", data.get("items", []))
                    if isinstance(items, list):
                        self._components[path.stem] = items
                        logger.info("Loaded %d %s components", len(items), path.stem)
                except Exception as e:
                    logger.warning("Failed to load %s: %s", path, e)

        # Load launch vehicles
        lv_path = self._data_dir / "launch_vehicles" / "vehicles.yaml"
        if lv_path.exists():
            try:
                data = load_yaml(lv_path)
                self._launch_vehicles = data.get("vehicles", data.get("items", []))
                logger.info("Loaded %d launch vehicles", len(self._launch_vehicles))
            except Exception as e:
                logger.warning("Failed to load launch vehicles: %s", e)

        # Load ground stations
        gs_path = self._data_dir / "ground_stations" / "networks.yaml"
        if gs_path.exists():
            try:
                data = load_yaml(gs_path)
                self._ground_stations = data.get("stations", data.get("items", []))
                logger.info("Loaded %d ground stations", len(self._ground_stations))
            except Exception as e:
                logger.warning("Failed to load ground stations: %s", e)

        # Load cost models
        cost_dir = self._data_dir / "cost_models"
        if cost_dir.is_dir():
            for path in sorted(cost_dir.glob("*.yaml")):
                try:
                    self._cost_models[path.stem] = load_yaml(path)
                except Exception as e:
                    logger.warning("Failed to load cost model %s: %s", path, e)

        # Load standards
        std_dir = self._data_dir / "standards"
        if std_dir.is_dir():
            for path in sorted(std_dir.glob("*.yaml")):
                try:
                    self._standards[path.stem] = load_yaml(path)
                except Exception as e:
                    logger.warning("Failed to load standard %s: %s", path, e)

        self._loaded = True

    def search_components(
        self,
        category: str | None = None,
        min_trl: int = 1,
        max_mass_kg: float | None = None,
        max_power_w: float | None = None,
    ) -> list[dict]:
        """Search components with filtering."""
        if not self._loaded:
            self.load()

        results = []
        categories = [category] if category else list(self._components.keys())
        for cat in categories:
            for comp in self._components.get(cat, []):
                if comp.get("trl", 9) < min_trl:
                    continue
                if max_mass_kg and comp.get("mass_kg", 0) > max_mass_kg:
                    continue
                if max_power_w and comp.get("power_w", 0) > max_power_w:
                    continue
                results.append(comp)
        return results

    def get_launch_vehicles(
        self,
        min_capacity_kg: float | None = None,
        orbit: str | None = None,
    ) -> list[dict]:
        """Get launch vehicles matching capacity requirements."""
        if not self._loaded:
            self.load()

        results = []
        for lv in self._launch_vehicles:
            if min_capacity_kg and orbit:
                cap = lv.get("performance_kg", {}).get(orbit)
                if cap is None or cap < min_capacity_kg:
                    continue
            results.append(lv)
        return results

    @property
    def categories(self) -> list[str]:
        if not self._loaded:
            self.load()
        return list(self._components.keys())
