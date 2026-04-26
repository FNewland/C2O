"""SpaceCDF — Configuration loader.

Loads YAML configuration files and validates them against Pydantic models.
Follows the same pattern as SMO's config/loader.py.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict at top level of {path}, got {type(data).__name__}")
    return data


def load_model(path: str | Path, model_class: type[T]) -> T:
    """Load a YAML file and validate it against a Pydantic model."""
    data = load_yaml(path)
    return model_class.model_validate(data)


def load_yaml_dir(directory: str | Path, pattern: str = "*.yaml") -> dict[str, dict[str, Any]]:
    """Load all YAML files in a directory. Returns {filename_stem: data}."""
    directory = Path(directory)
    result = {}
    if not directory.is_dir():
        logger.warning("Directory not found: %s", directory)
        return result
    for path in sorted(directory.glob(pattern)):
        try:
            result[path.stem] = load_yaml(path)
        except Exception as e:
            logger.warning("Failed to load %s: %s", path, e)
    return result


def load_models_from_dir(
    directory: str | Path,
    model_class: type[T],
    pattern: str = "*.yaml",
) -> list[T]:
    """Load all YAML files in a directory and validate each against a model."""
    directory = Path(directory)
    models = []
    if not directory.is_dir():
        logger.warning("Directory not found: %s", directory)
        return models
    for path in sorted(directory.glob(pattern)):
        try:
            data = load_yaml(path)
            if isinstance(data, list):
                for item in data:
                    models.append(model_class.model_validate(item))
            else:
                models.append(model_class.model_validate(data))
        except Exception as e:
            logger.warning("Failed to load/validate %s: %s", path, e)
    return models


def load_component_catalog(
    data_dir: str | Path,
) -> dict[str, list[dict[str, Any]]]:
    """Load the entire component catalog from the KB data directory.

    Returns {category: [component_dict, ...]}.
    """
    data_dir = Path(data_dir)
    catalog: dict[str, list[dict[str, Any]]] = {}

    components_dir = data_dir / "components"
    if components_dir.is_dir():
        for path in sorted(components_dir.glob("*.yaml")):
            try:
                data = load_yaml(path)
                items = data.get("components", data.get("items", []))
                if isinstance(items, list):
                    catalog[path.stem] = items
                elif isinstance(data, dict) and "id" in data:
                    catalog[path.stem] = [data]
            except Exception as e:
                logger.warning("Failed to load component file %s: %s", path, e)

    return catalog
