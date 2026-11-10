"""KB component schema v2 — the mechanical view of a part, with defaults.

``mechanical_of(component, domain=..., name=...)`` answers what the CubeSat stack
builder needs to place a unit: mount class, envelope (footprint and height), stack
height in a column, preferred face, end anchor, boresight and field of view, and how
a deployable unfolds. Values come, field by field, from:

1. the component's own schema v2 ``mechanical:`` block;
2. its v1 fields (``dimensions_mm``, ``form_factor``, ``interfaces``,
   ``performance.deployment``, ``performance.band``, ``performance.fov_deg``);
3. the category default in ``data/mechanical_defaults.yaml``;
4. the subsystem-domain default (elements with no KB part).

Everything taken from 3 or 4 is listed in ``assumptions`` (C2O defaults), so the
stack view can say which numbers are guesses. Stdlib + the KB's YAML loader only.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Any

from spacecdf_common.config.loader import load_yaml

DEFAULTS_PATH = Path(__file__).parent / "data" / "mechanical_defaults.yaml"

MOUNT_CLASSES = ("pc104_board", "pc104_module", "u_module", "face_panel", "deployable",
                 "bracket", "structure", "distributed", "none")
#: Mount classes that occupy a slot in a stack column.
COLUMN_CLASSES = frozenset({"pc104_board", "pc104_module", "u_module", "bracket"})
#: Mount classes that sit on an outside face.
FACE_CLASSES = frozenset({"face_panel", "deployable"})
FACES = ("px", "mx", "py", "my", "pz", "mz")


@lru_cache(maxsize=1)
def defaults() -> dict[str, Any]:
    """The parsed ``mechanical_defaults.yaml`` (cached)."""
    return load_yaml(DEFAULTS_PATH)


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if math.isfinite(v) else None


def _dims(v: Any) -> list[float] | None:
    if isinstance(v, (list, tuple)) and len(v) == 3 and all(_num(x) is not None and x > 0 for x in v):
        return [float(x) for x in v]
    return None


def band_key(band: str, freq_mhz: float | None, name: str) -> str:
    b = (band or "").strip().lower().replace("-band", "").replace(" band", "")
    n = name.lower()
    if "gnss" in n or "gps" in n or b in ("l", "gnss", "gps"):
        return "gnss"
    if b in ("uhf", "vhf", "s", "x", "ka"):
        return b
    if freq_mhz:
        if freq_mhz < 300:
            return "vhf"
        if freq_mhz < 1000:
            return "uhf"
        if freq_mhz < 1700:
            return "gnss"
        if freq_mhz < 4000:
            return "s"
        if freq_mhz < 12000:
            return "x"
        return "ka"
    if "uhf" in n:
        return "uhf"
    return "default"


_DISPOSAL_WORDS = ("drag sail", "sail", "drag tape", "deorbit", "de-orbit", "disposal")


def _is_disposal_device(domain: str | None, name: str) -> bool:
    """A propulsion-domain element named like a drag sail / tape / deorbit device."""
    d = str(domain or "").lower()
    if d not in ("propulsion", "prop", "disposal"):
        return False
    n = str(name or "").lower()
    return d == "disposal" or any(w in n for w in _DISPOSAL_WORDS)


def mechanical_of(component: dict | None, *, domain: str | None = None, name: str = "",
                  category: str | None = None) -> dict[str, Any]:
    """The mechanical view of a KB component (or of a bare element by its domain).

    Returns ``{mount_class, envelope_mm, stack_height_mm, face, anchor, boresight,
    fov_deg, spread, deployable, connector, manufacturer, category, source,
    assumptions}``. ``source`` is ``kb`` (everything from the entry), ``kb+default``
    or ``default``.
    """
    cfg = defaults()
    comp = component or {}
    cat = str(category or comp.get("category") or "")
    perf = comp.get("performance") if isinstance(comp.get("performance"), dict) else {}
    own = comp.get("mechanical") if isinstance(comp.get("mechanical"), dict) else {}
    if not cat and not comp and _is_disposal_device(domain, name):
        # A bare drag-sail element sits in the propulsion domain (the disposal function, PI
        # decision Nov 2026): place it like a deorbit device, not like a thruster.
        cat = "deorbit_device"
    cat_def = dict((cfg.get("categories") or {}).get(cat) or {})
    dom_def = dict((cfg.get("domains") or {}).get(str(domain or "").lower()) or {})
    if not cat_def and not dom_def:
        dom_def = dict((cfg.get("domains") or {}).get("default") or {})
    base = cat_def or dom_def
    base_src = f"category {cat}" if cat_def else f"domain {domain or 'default'}"
    assumptions: list[str] = []
    used_default = False

    def pick(field: str, *v1: Any) -> Any:
        nonlocal used_default
        if field in own and own[field] is not None:
            return own[field]
        for v in v1:
            if v is not None:
                return v
        if field in base:
            used_default = True
            assumptions.append(f"{field} = {base[field]} (C2O default, {base_src})")
            return base[field]
        return None

    deployment = str(perf.get("deployment") or comp.get("deployment") or "").lower()
    pname = f"{name} {comp.get('name') or ''}".strip()

    # mount class
    mc = own.get("mount_class")
    if mc is None:
        mc = base.get("mount_class", "bracket")
        dims_v1 = _dims(comp.get("dimensions_mm"))
        ff = str(comp.get("form_factor") or "").upper().replace(" ", "")
        ifaces = [str(i).upper().replace(" ", "") for i in (comp.get("interfaces") or [])]
        is_pc104 = ff == "PC/104" or "PC/104" in ifaces
        if base.get("by_deployment"):
            mc = "face_panel" if (not deployment or deployment in ("body_mounted", "none", "fixed")) else "deployable"
        if base.get("module_if_board_size") and dims_v1 and dims_v1[0] >= 85 and dims_v1[1] >= 85:
            mc = "pc104_module"
        if base.get("pc104_if_form_factor") and is_pc104:
            mc = "pc104_board"
        if mc == "bracket" and is_pc104 and cat not in ("reaction_wheel",):
            mc = "pc104_board"
        if not cat_def and not comp:
            used_default = True
            assumptions.append(f"mount_class = {mc} (C2O default, {base_src})")
    if mc not in MOUNT_CLASSES:
        mc = "bracket"

    env = _dims(own.get("envelope_mm")) or _dims(comp.get("dimensions_mm"))
    if env is None:
        u = _num(own.get("u_size"))
        st = cfg.get("structure") or {}
        if u and mc == "u_module":
            env = [98.0, 98.0, u * float(st.get("u_length_mm", 100.0))]
        else:
            env = _dims(pick("envelope_mm"))
    if env is None:
        env = [90.0, 90.0, 20.0]
        used_default = True
        assumptions.append("envelope_mm = [90, 90, 20] (C2O fallback)")

    pc = cfg.get("pc104") or {}
    pitch = float(pc.get("pitch_mm", 15.24))
    sh = _num(own.get("stack_height_mm"))
    if sh is None:
        if mc == "pc104_board":
            sh = max(pitch, env[2] + float(pc.get("clearance_mm", 2.0)))
            if env[2] + float(pc.get("clearance_mm", 2.0)) <= pitch:
                assumptions.append(f"stack pitch {pitch:g} mm (C2O default, PC/104 stack-through header)")
        elif mc in ("pc104_module", "bracket"):
            sh = env[2] + float(pc.get("clearance_mm", 2.0))
        elif mc == "u_module":
            sh = env[2]
        else:
            sh = env[2]

    # face / boresight / fov
    face = own.get("face")
    if face is None and (cat == "antenna" or (mc in FACE_CLASSES and "antenna" in pname.lower())):
        key = band_key(str(perf.get("band") or ""), _num(perf.get("frequency_mhz")), pname)
        face = (cfg.get("antenna_faces") or {}).get(key) or (cfg.get("antenna_faces") or {}).get("default")
        assumptions.append(f"face = {face} for a {key} antenna (C2O default)")
    if face is None:
        face = base.get("face")
    boresight = own.get("boresight") or base.get("boresight")
    fov = _num(own.get("fov_deg")) or _num(perf.get("fov_deg")) or _num(base.get("fov_deg"))
    anchor = own.get("anchor") or base.get("anchor")
    spread = own.get("spread") or base.get("spread")

    deployable = own.get("deployable") if isinstance(own.get("deployable"), dict) else None
    if mc == "deployable" and deployable is None:
        if cat == "solar_panel" or "wing" in deployment or "panel" in deployment:
            panels = 3 if "multi" in deployment else 1
            wings = 2 if "double" in deployment else 1
            deployable = {"kind": "wing", "wings": wings, "panels": panels, "hinge": "edge"}
        else:
            length = _num(perf.get("length_mm")) or _num(perf.get("element_length_mm"))
            if length is None:
                f = _num(perf.get("frequency_mhz"))
                length = round(299792.458 / f / 4.0) if f else 170.0
                assumptions.append(f"deployed element length {length:.0f} mm (quarter wave, C2O default)")
            deployable = {"kind": "antenna", "elements": 4 if "tape" in deployment or "burn" in deployment else 1,
                          "length_mm": float(length), "hinge": "edge"}
        assumptions.append(f"deployable = {deployable['kind']} (from deployment '{deployment or 'unknown'}', C2O default)")
    if mc == "deployable" and face is None:
        face = "py" if (deployable or {}).get("kind") == "wing" else "pz"

    conn = own.get("connector")
    if conn is None and mc in ("pc104_board", "pc104_module"):
        conn = "PC/104 H1/H2"

    source = "kb" if comp and not used_default else ("kb+default" if comp else "default")
    return {
        "mount_class": mc, "envelope_mm": env, "stack_height_mm": round(float(sh), 2), "face": face,
        "anchor": anchor, "boresight": boresight, "fov_deg": fov, "spread": spread, "deployable": deployable,
        "connector": conn, "manufacturer": comp.get("manufacturer"), "category": cat or None,
        "radiator_face": base.get("radiator_face"),
        "source": source, "assumptions": assumptions,
    }
