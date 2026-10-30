"""Config bind set hashing (LINK_DESIGN §6, LINK_INTERFACES §5).

Both ends hash the files that define the wire (HK layout, parameter ids, TC
catalogue, ...). A difference in a STRICT file makes the GSG refuse the bind;
a difference in a WARN file binds with a NOTICE. Line endings are normalised
so a Windows checkout hashes the same as a Unix one.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

#: Reject on mismatch.
STRICT_FILES: tuple[str, ...] = (
    "commands/tc_catalog.yaml",
    "events/event_catalog.yaml",
    "memory/memory_map.yaml",
    "mission.yaml",               # identity subset only, see MISSION_KEYS
    "monitoring/s12_definitions.yaml",
    "monitoring/s19_rules.yaml",
    "orbit.yaml",
    "subsystems/ttc.yaml",
    "telemetry/hk_structures.yaml",
    "telemetry/parameters.yaml",
)

#: Bind, but post a NOTICE on mismatch.
WARN_FILES: tuple[str, ...] = (
    "fdir/fault_propagation.yaml",
    "planning/ground_stations.yaml",
    "subsystems/eps.yaml",
    "subsystems/payload.yaml",
    "subsystems/prop.yaml",
)

#: The identity subset of mission.yaml (deployment keys legitimately differ).
MISSION_KEYS: tuple[str, ...] = (
    "name", "spacecraft_apid", "bootloader_apid", "pus_version",
    "time_epoch", "start_in_bootloader",
)

MISSING = "missing"


def _normalise(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def file_bytes(config_dir: Path, relpath: str) -> bytes | None:
    p = Path(config_dir) / relpath
    try:
        data = _normalise(p.read_bytes())
    except OSError:
        return None
    if relpath == "mission.yaml":
        import yaml  # PyYAML ships with smo-common
        doc = yaml.safe_load(data.decode("utf-8")) or {}
        subset = {k: doc.get(k) for k in MISSION_KEYS}
        data = json.dumps(subset, sort_keys=True, default=str).encode()
    return data


def compute(config_dir: str | Path) -> dict[str, Any]:
    """``{"hash": <overall strict-set sha256>, "files": {relpath: sha256}}``.

    ``files`` covers the strict and warn sets; the overall hash covers the
    strict set (the bind identity).
    """
    config_dir = Path(config_dir)
    files: dict[str, str] = {}
    overall = hashlib.sha256()
    for rel in sorted(STRICT_FILES + WARN_FILES):
        data = file_bytes(config_dir, rel)
        files[rel] = hashlib.sha256(data).hexdigest() if data is not None else MISSING
        if rel in STRICT_FILES:
            blob = data if data is not None else b""
            overall.update(rel.encode() + b"\0" + len(blob).to_bytes(8, "big") + blob)
    return {"hash": overall.hexdigest(), "files": files}


def compare(local_files: dict[str, str], remote_files: dict[str, str] | None
            ) -> tuple[list[str], list[str]]:
    """Return ``(strict_mismatches, warn_mismatches)``."""
    remote_files = remote_files or {}
    strict = [p for p in STRICT_FILES if local_files.get(p) != remote_files.get(p)]
    warn = [p for p in WARN_FILES if local_files.get(p) != remote_files.get(p)]
    return sorted(strict), sorted(warn)
