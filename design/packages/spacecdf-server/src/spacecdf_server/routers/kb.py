"""SpaceCDF — Knowledge Base API."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from spacecdf_common.config.loader import load_yaml_dir

router = APIRouter()

# KB data directory
KB_DATA_DIR = Path(__file__).resolve().parents[4] / "spacecdf-kb" / "src" / "spacecdf_kb" / "data"


@router.get("/components/{category}")
async def list_components(category: str) -> list[dict]:
    """List components in a category (e.g. 'reaction_wheels', 'batteries')."""
    path = KB_DATA_DIR / "components" / f"{category}.yaml"
    if not path.exists():
        return []
    from spacecdf_common.config.loader import load_yaml
    data = load_yaml(path)
    return data.get("components", data.get("items", []))


@router.get("/launch-vehicles")
async def list_launch_vehicles() -> list[dict]:
    """List all launch vehicles in the knowledge base."""
    path = KB_DATA_DIR / "launch_vehicles" / "vehicles.yaml"
    if not path.exists():
        return []
    from spacecdf_common.config.loader import load_yaml
    data = load_yaml(path)
    return data.get("vehicles", data.get("items", []))


@router.get("/ground-stations")
async def list_ground_stations() -> list[dict]:
    """List all ground stations in the knowledge base."""
    path = KB_DATA_DIR / "ground_stations" / "networks.yaml"
    if not path.exists():
        return []
    from spacecdf_common.config.loader import load_yaml
    data = load_yaml(path)
    return data.get("stations", data.get("items", []))


@router.get("/categories")
async def list_categories() -> list[str]:
    """List available KB categories."""
    components_dir = KB_DATA_DIR / "components"
    if not components_dir.is_dir():
        return []
    return sorted(p.stem for p in components_dir.glob("*.yaml"))
