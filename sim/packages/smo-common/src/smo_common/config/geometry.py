"""SMO Common — spacecraft geometry description for the pictorial displays.

``configs/<mission>/geometry.yaml`` is a small, schematic description of the
spacecraft (bus box, body cell areas, deployable wings and their drive,
imager, star trackers, antennas, thrusters) that the 3D attitude view draws
and that SpaceCDF produces from a design. Nothing in the simulator reads it;
the physical numbers are COPIES of the subsystem files that own them, so
``validate_geometry`` cross-checks those copies (eps.yaml cell areas and drive
axis, planner.yaml imager FOV) and returns every problem it finds.

    load_geometry(config_dir) -> dict       # parsed + validated, JSON-ready
    validate_geometry(geo, config_dir=None) -> list[str]   # [] when valid

The MCS serves the result at ``GET /api/geometry``. Stdlib + PyYAML only.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "c2o.geometry/1"
FACES = ("px", "mx", "py", "my", "pz", "mz")
FACE_NORMALS = {
    "px": (1, 0, 0), "mx": (-1, 0, 0), "py": (0, 1, 0),
    "my": (0, -1, 0), "pz": (0, 0, 1), "mz": (0, 0, -1),
}
#: Top-level keys; anything else is a typo (the JS view ignores unknown keys,
#: so it would fail silently there).
TOP_KEYS = {
    "schema", "spacecraft", "quaternion", "bus", "body_panels", "wings",
    "array_drive", "payload", "star_trackers",
    "star_tracker_sun_exclusion_deg", "star_tracker_earth_exclusion_deg",
    "antennas", "thrusters",
}
#: Optional keys added to c2o.geometry/1 by the SpaceCDF stack builder (Nov 2026,
#: additive: a file without them is unchanged and still valid). ``frame`` states the
#: convention as text; ``internal`` lists one box per placed unit (stowed), box_m =
#: [cx, cy, cz, dx, dy, dz] in this body frame; ``mass_properties`` gives the mass and
#: CoG of the layout. See design/docs/STACK_BUILDER.md.
OPTIONAL_KEYS = {"frame", "internal", "mass_properties"}
_UNIT_TOL = 1e-3
_AREA_TOL = 1e-6


class GeometryError(ValueError):
    """geometry.yaml is missing or invalid; ``problems`` lists every issue."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def _vec(v: Any, n: int = 3) -> bool:
    return (isinstance(v, (list, tuple)) and len(v) == n
            and all(isinstance(x, (int, float)) and math.isfinite(x) for x in v))


def _unit(v: Any) -> bool:
    return _vec(v) and abs(math.sqrt(sum(x * x for x in v)) - 1.0) <= _UNIT_TOL


def _pos(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x) and x > 0


def _check_items(geo: dict, key: str, required: dict[str, Any], out: list[str]) -> list[dict]:
    items = geo.get(key)
    if not isinstance(items, list):
        out.append(f"{key}: expected a list")
        return []
    ids = set()
    for i, it in enumerate(items):
        where = f"{key}[{i}]"
        if not isinstance(it, dict):
            out.append(f"{where}: expected a mapping")
            continue
        ident = it.get("id", it.get("face"))
        if ident in ids:
            out.append(f"{where}: duplicate id {ident!r}")
        ids.add(ident)
        for field, check in required.items():
            if field not in it:
                out.append(f"{where}: missing {field}")
            elif not check(it[field]):
                out.append(f"{where}.{field}: invalid value {it[field]!r}")
    return [it for it in items if isinstance(it, dict)]


def validate_geometry(geo: Any, config_dir: str | Path | None = None) -> list[str]:
    """Every problem with *geo* (empty list = valid).

    With *config_dir*, also cross-check the copied numbers against the
    subsystem files that own them (eps.yaml, planning/planner.yaml).
    """
    out: list[str] = []
    if not isinstance(geo, dict):
        return ["geometry: expected a mapping at the top level"]
    for k in sorted(set(geo) - TOP_KEYS - OPTIONAL_KEYS):
        out.append(f"unknown key {k!r}")
    if geo.get("schema") != SCHEMA:
        out.append(f"schema: expected {SCHEMA!r}, got {geo.get('schema')!r}")
    if not isinstance(geo.get("spacecraft"), str) or not geo.get("spacecraft"):
        out.append("spacecraft: expected a name")

    q = geo.get("quaternion")
    if not isinstance(q, dict) or q.get("order") not in ("xyzw", "wxyz") \
            or q.get("maps") not in ("eci_to_body", "body_to_eci"):
        out.append("quaternion: expected {order: xyzw|wxyz, maps: eci_to_body|body_to_eci}")

    bus = geo.get("bus")
    if not isinstance(bus, dict) or not _vec(bus.get("size_m")) \
            or not all(_pos(x) for x in bus.get("size_m")):
        out.append("bus.size_m: expected three positive lengths [x, y, z]")

    panels = _check_items(geo, "body_panels", {
        "face": lambda f: f in FACES, "normal": _unit,
        "cell_area_m2": lambda a: isinstance(a, (int, float)) and a >= 0}, out)
    for p in panels:
        f = p.get("face")
        if f in FACE_NORMALS and _vec(p.get("normal")) \
                and tuple(round(x) for x in p["normal"]) != FACE_NORMALS[f]:
            out.append(f"body_panels.{f}: normal {p['normal']} is not the {f} face normal")

    wings = _check_items(geo, "wings", {
        "id": lambda s: isinstance(s, str) and bool(s), "face": lambda f: f in FACES,
        "mount_axis": _unit,
        "panel_size_m": lambda v: _vec(v, 2) and all(_pos(x) for x in v),
        "panels": lambda n: isinstance(n, int) and n >= 1,
        "cell_area_m2": _pos,
        "deployed_bit": lambda b: isinstance(b, int) and 0 <= b <= 31}, out)
    for w in wings:
        if w.get("face") in FACE_NORMALS and _vec(w.get("mount_axis")) \
                and tuple(round(x) for x in w["mount_axis"]) != FACE_NORMALS[w["face"]]:
            out.append(f"wings.{w.get('id')}: mount_axis must be the {w['face']} face normal")
        if _vec(w.get("panel_size_m"), 2) and isinstance(w.get("panels"), int) \
                and _pos(w.get("cell_area_m2")):
            geom = w["panel_size_m"][0] * w["panel_size_m"][1] * w["panels"]
            if w["cell_area_m2"] > geom + _AREA_TOL:
                out.append(f"wings.{w.get('id')}: cell_area_m2 exceeds the panel area {geom:.3f} m2")

    drive = geo.get("array_drive")
    if wings:
        if not isinstance(drive, dict):
            out.append("array_drive: required when wings are declared")
        else:
            for k in ("axis", "normal_at_0deg", "normal_at_90deg"):
                if not _unit(drive.get(k)):
                    out.append(f"array_drive.{k}: expected a unit vector")
            if all(_unit(drive.get(k)) for k in ("axis", "normal_at_0deg", "normal_at_90deg")):
                a, n0, n9 = drive["axis"], drive["normal_at_0deg"], drive["normal_at_90deg"]
                dot = lambda u, v: sum(x * y for x, y in zip(u, v))  # noqa: E731
                if max(abs(dot(a, n0)), abs(dot(a, n9)), abs(dot(n0, n9))) > _UNIT_TOL:
                    out.append("array_drive: axis, normal_at_0deg and normal_at_90deg must be orthogonal")
            if not isinstance(drive.get("angle_param"), str):
                out.append("array_drive.angle_param: expected a telemetry parameter name")

    pl = geo.get("payload")
    if not isinstance(pl, dict) or not _unit(pl.get("boresight")) \
            or not _vec(pl.get("position_m")) or not _pos(pl.get("fov_deg")) \
            or pl.get("fov_deg", 0) >= 180:
        out.append("payload: expected {boresight: unit vector, position_m: [x,y,z], fov_deg: 0-180}")

    _check_items(geo, "star_trackers", {
        "id": lambda s: isinstance(s, str) and bool(s), "boresight": _unit,
        "position_m": _vec, "fov_deg": lambda x: _pos(x) and x < 180}, out)
    for k in ("star_tracker_sun_exclusion_deg", "star_tracker_earth_exclusion_deg"):
        if not (_pos(geo.get(k)) and geo.get(k) < 180):
            out.append(f"{k}: expected an angle in (0, 180) deg")

    _check_items(geo, "antennas", {
        "id": lambda s: isinstance(s, str) and bool(s),
        "kind": lambda s: s in ("patch", "dipole", "helix", "dish"),
        "position_m": _vec, "boresight": _unit}, out)
    for a in geo.get("antennas") or []:
        if isinstance(a, dict) and "length_m" in a and not _pos(a["length_m"]):
            out.append(f"antennas.{a.get('id')}.length_m: expected a positive length")
    _check_items(geo, "thrusters", {
        "id": lambda s: isinstance(s, str) and bool(s),
        "position_m": _vec, "thrust_axis": _unit}, out)

    if "frame" in geo and not isinstance(geo["frame"], dict):
        out.append("frame: expected a mapping")
    if "internal" in geo:
        boxes = _check_items(geo, "internal", {
            "id": lambda s: isinstance(s, str) and bool(s),
            "box_m": lambda v: _vec(v, 6) and all(x >= 0 for x in v[3:])}, out)
        for b in boxes:
            if "mass_kg" in b and not (isinstance(b["mass_kg"], (int, float)) and b["mass_kg"] >= 0):
                out.append(f"internal.{b.get('id')}.mass_kg: expected a mass >= 0")
            if b.get("face") is not None and b.get("face") not in FACES:
                out.append(f"internal.{b.get('id')}.face: expected one of {', '.join(FACES)}")
    if "mass_properties" in geo:
        mp = geo["mass_properties"]
        if not isinstance(mp, dict) or not _vec(mp.get("cog_m")) \
                or not (isinstance(mp.get("mass_kg"), (int, float)) and mp["mass_kg"] >= 0):
            out.append("mass_properties: expected {mass_kg: >= 0, cog_m: [x, y, z]}")

    if config_dir is not None and not out:
        out.extend(_cross_check(geo, Path(config_dir)))
    return out


def _read(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def _cross_check(geo: dict, config_dir: Path) -> list[str]:
    """The copies must equal their owners' values."""
    out: list[str] = []
    eps = _read(config_dir / "subsystems" / "eps.yaml").get("solar_panels") or {}
    if eps:
        for p in geo["body_panels"]:
            want = eps.get(f"{p['face']}_area_m2")
            if want is not None and abs(float(want) - float(p["cell_area_m2"])) > _AREA_TOL:
                out.append(f"body_panels.{p['face']}.cell_area_m2 = {p['cell_area_m2']} "
                           f"but eps.yaml solar_panels.{p['face']}_area_m2 = {want}")
        for w in geo["wings"]:
            want = eps.get(f"wing_{w['face']}_area_m2")
            if want is not None and abs(float(want) - float(w["cell_area_m2"])) > _AREA_TOL:
                out.append(f"wings.{w['id']}.cell_area_m2 = {w['cell_area_m2']} "
                           f"but eps.yaml solar_panels.wing_{w['face']}_area_m2 = {want}")
        axis = str(eps.get("sada_axis", "")).lower()
        if geo["wings"] and axis in ("x", "y", "z"):
            want = [1 if c == axis else 0 for c in "xyz"]
            got = [abs(round(x)) for x in geo["array_drive"]["axis"]]
            if got != want:
                out.append(f"array_drive.axis {geo['array_drive']['axis']} "
                           f"but eps.yaml solar_panels.sada_axis = {axis}")
    imaging = (_read(config_dir / "planning" / "planner.yaml").get("imaging") or {})
    fov = imaging.get("fov_deg")
    if fov is not None and abs(float(fov) - float(geo["payload"]["fov_deg"])) > 1e-3:
        out.append(f"payload.fov_deg = {geo['payload']['fov_deg']} "
                   f"but planning/planner.yaml imaging.fov_deg = {fov}")
    return out


def load_geometry(config_dir: str | Path, *, cross_check: bool = True) -> dict:
    """Parse and validate ``<config_dir>/geometry.yaml``.

    Raises ``GeometryError`` (with every problem) when the file is missing
    or invalid; returns the plain dict (JSON-serialisable) otherwise.
    """
    path = Path(config_dir) / "geometry.yaml"
    if not path.is_file():
        raise GeometryError([f"{path} not found"])
    with open(path, "r", encoding="utf-8") as f:
        geo = yaml.safe_load(f)
    probs = validate_geometry(geo, config_dir if cross_check else None)
    if probs:
        raise GeometryError(probs)
    return geo
