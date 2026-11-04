"""SpaceCDF — CubeSat stack builder: placement model, auto-placement, checks, geometry.

Design rules §4 (docs/plan_2026-11/design_sim/spacecdf_design_rules.md). Pure: plain
dicts in, plain dicts out; persistence and seats live in ``routers/stack.py``.

FRAMES (recorded once, used everywhere):

* **Stack frame** = the simulator body frame of ``sim/configs/eosat1/geometry.yaml``
  (ruling Q4): origin at the envelope's geometric centre, +X ~ velocity, +Y = orbit
  normal, **+Z = zenith, -Z = nadir**; X is the short side (100 mm), Y the 226 mm
  side of a 6U, Z the rail (insertion) axis. Millimetres inside this module, metres
  in the geometry export. Every view (elevation, face map, 3D) draws this frame.
* **Design frame** = SpaceCDF ``position_json`` (``services/physics_closure.py``,
  ``mass_properties.py``, ``cds_checks.py`` CDS-COG): metres, origin at the envelope
  **corner**, axes in the order of ``cds_rules.yaml envelope_mm``, **+Z = nadir**
  along the rails. ``to_design_m`` is the only conversion: a proper rotation
  (180 deg about X, or the X/Y swap + Z flip when ``envelope_mm`` lists the long
  side first, design rules F1) plus the corner offset.

PLACEMENT MODEL. A layout *spec* is what the user and the auto-placer edit::

    {"columns": [[pid, ...], ...],          # per stack column, nadir end first
     "layers":  {"nadir": [pid], "zenith": [pid]},   # units wider than one column
     "faces":   {element_id: [{"face": "px", "count": 2}, ...]},
     "locks":   {pid: true}}

``realise(spec)`` turns it into placements (mount class, column, slot, face, box in
the stack frame, deployed geometry, rationale). Placement ids: the element id for
column and layer units, ``<element_id>@<face>`` for face groups.

Public API:
    collect_units(elements, interfaces=None) -> list[dict]
    envelope(form_factor) -> dict
    auto_place(units, env, prev_spec=None, interfaces=None) -> (spec, report)
    realise(spec, units, env) -> dict
    run_checks(real, units, env, orbit_alt_km=None) -> list[check_item]
    evaluate(spec, units, env, ...) -> {"placements", "columns", "cog", "checks", "summary", "score", ...}
    design_positions(real, units, env) -> {element_id: [x, y, z] m, design frame}
    to_geometry(real, units, env, spacecraft="") -> c2o.geometry/1 dict (+ optional internal, frame, mass_properties)
"""
from __future__ import annotations

import copy
import logging
import itertools
import math
from typing import Any

from . import rule_config as rc
from .rule_inputs import by_id, kb_component, leaves_with, live, perf, qty, space_hardware

logger = logging.getLogger(__name__)

RULES = "stack_rules"
#: study id -> stored layout {"form_factor", "approved", "proposal", "version"} (routers/stack.py
#: writes it through to the stack_layouts table; the rule-engine hooks below read it).
LAYOUT_CACHE: dict[str, dict[str, Any]] = {}
AUTO_ORIGIN = "rule:STACK-AUTO"
FACES = ("px", "mx", "py", "my", "pz", "mz")
NORMALS: dict[str, tuple[int, int, int]] = {
    "px": (1, 0, 0), "mx": (-1, 0, 0), "py": (0, 1, 0), "my": (0, -1, 0), "pz": (0, 0, 1), "mz": (0, 0, -1)}
#: Face plane axes (u, v) in the stack frame: index of the axis and nothing else.
FACE_UV: dict[str, tuple[int, int, int]] = {   # (u axis, v axis, normal axis)
    "px": (1, 2, 0), "mx": (1, 2, 0), "py": (0, 2, 1), "my": (0, 2, 1), "pz": (0, 1, 2), "mz": (0, 1, 2)}
COLUMN_CLASSES = ("pc104_board", "pc104_module", "u_module", "bracket")
FACE_CLASSES = ("face_panel", "deployable")
SUBSYSTEM_OF_ROLE = {
    "payload": "payload", "battery": "power", "eps": "power", "solar": "power", "obc": "obdh", "radio": "ttc",
    "antenna_rf": "ttc", "antenna_gnss": "aocs", "adcs": "aocs", "star_tracker": "aocs", "gnss": "aocs",
    "propulsion": "propulsion", "structure": "structure", "other": "other", "thermal": "thermal",
}
FRAME_NOTE = {
    "stack": "simulator body frame (geometry.yaml, ruling Q4): origin at the envelope centre, +X ~ velocity, "
             "+Y orbit normal, +Z zenith, -Z nadir; Z = rail axis",
    "design": "SpaceCDF position_json: metres, origin at the envelope corner, axes in cds_rules.yaml envelope_mm "
              "order, +Z nadir along the rails",
}


# ─────────────────────────────────────────────────────────────── helpers

def _rules() -> dict[str, Any]:
    return rc.load(RULES)


def _ref(node_key: str | None = None, *, clause: str | None = None, source: str | None = None) -> dict[str, Any]:
    cfg = _rules()
    node = dict(cfg.get(node_key) or {}) if node_key else {}
    if source:
        node["source"] = source
    if clause:
        node["clause"] = clause
    node.setdefault("source", "c2o_default")
    return rc.ref_of(cfg, node)


def _cds_ref(clause: str) -> dict[str, Any]:
    cfg = rc.load("cds_rules")
    return rc.ref_of(cfg, {"source": "cds_14_1", "clause": clause})


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if math.isfinite(v) else None


def _f(v: float, d: int = 1) -> str:
    """Engineering number: '.' decimals in both languages (owner ruling R5)."""
    return f"{v:.{d}f}"


def _dist(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in range(3)))


def _unit_vec(v: Any) -> list[float] | None:
    if not (isinstance(v, (list, tuple)) and len(v) == 3):
        return None
    n = math.sqrt(sum(float(x) ** 2 for x in v))
    return [float(x) / n for x in v] if n > 1e-9 else None


def _mech_of(kb: dict | None, domain: str | None, name: str) -> dict[str, Any]:
    from spacecdf_kb.mechanical import mechanical_of
    return mechanical_of(kb, domain=domain, name=name)


def _band_key(kb: dict | None, name: str) -> str:
    from spacecdf_kb.mechanical import band_key
    p = (kb or {}).get("performance") or {}
    return band_key(str(p.get("band") or ""), _num(p.get("frequency_mhz")), f"{name} {(kb or {}).get('name') or ''}")


# ─────────────────────────────────────────────────────────────── units

def _domain_of(e: dict, idx: dict[str, dict]) -> str | None:
    cur: dict | None = e
    for _ in range(30):
        if cur is None:
            return None
        d = cur.get("subsystem_domain")
        if d:
            return str(d).lower()
        cur = idx.get(cur.get("parent_id") or "")
    return None


def _role(kb: dict | None, domain: str | None, name: str, mech: dict) -> str:
    r = _rules()["roles"]
    cat = str((kb or {}).get("category") or "")
    if mech.get("mount_class") == "structure":
        return "structure"
    role = r["by_category"].get(cat)
    low = name.lower()
    if role is None:
        for k, words in (r.get("name_keywords") or {}).items():
            if any(w in low for w in words):
                role = k
                break
    if role is None:
        role = r["by_domain"].get(domain or "", None)
    if role is None and mech.get("mount_class") == "distributed":
        return "thermal" if (domain or "") in ("thermal", "tcs") else "other"
    return role or "other"


def collect_units(elements: list[dict], interfaces: list[dict] | None = None) -> list[dict]:
    """The units the stack builder places: live space hardware components (by KB part or
    domain), and subsystems/systems that carry mass with no massive descendant (the same
    leaves CDS-COG needs a position for). Deployers and bare cells are left out."""
    els = live(elements)
    idx = by_id(els)
    hw = space_hardware(els)
    leaf_ids = {e["id"] for e in leaves_with(els, "mass_kg")}
    units: list[dict] = []
    for e in sorted(hw, key=lambda x: (str(x.get("name") or ""), x["id"])):
        et = e.get("element_type")
        if et != "component" and e["id"] not in leaf_ids:
            continue
        if e.get("in_scope") is False:
            continue
        kb = kb_component(e)
        domain = _domain_of(e, idx)
        name = str(e.get("name") or "")
        if et in ("system",) and not kb:
            mech = _mech_of(None, "structure", name)   # a system with its own mass: the bus as a whole
            mech["mount_class"] = "distributed"
        else:
            mech = _mech_of(kb, domain, name)
        if mech["mount_class"] == "none":
            continue
        q = qty(e)
        mass = _num(e.get("mass_kg"))
        if mass is None:
            mass = _num((kb or {}).get("mass_kg")) or 0.0
        power = _num(e.get("power_avg_w"))
        if power is None:
            power = _num((kb or {}).get("power_w")) or _num((kb or {}).get("power_avg_w")) or 0.0
        dims = e.get("dimensions_mm") or e.get("dimensions_json")
        if isinstance(dims, list) and len(dims) == 3 and all((_num(x) or 0) > 0 for x in dims):
            mech = {**mech, "envelope_mm": [float(x) for x in dims]}
        role = _role(kb, domain, name, mech)
        band = None
        if role == "antenna" or (kb or {}).get("category") == "antenna":
            band = _band_key(kb, name)
            role = "antenna_gnss" if band == "gnss" else "antenna_rf"
        units.append({
            "id": e["id"], "name": name, "element_type": et, "domain": domain, "role": role, "band": band,
            "subsystem": SUBSYSTEM_OF_ROLE.get(role, domain or "other"),
            "kb_id": e.get("kb_component_id"), "manufacturer": e.get("manufacturer") or (kb or {}).get("manufacturer"),
            "quantity": q, "mass_kg": round(mass * q, 4), "power_w": round(power * q, 3), "mech": mech,
            "performance": perf(e),
        })
    return units


# ─────────────────────────────────────────────────────────────── envelope

def envelope(form_factor: str) -> dict[str, Any]:
    """Envelope, columns and limits for a CubeSat form factor, in the stack frame (mm).

    ``cds_rules.yaml envelope_mm`` gives the CDS envelope with Z the rail axis; the
    stack frame orders X/Y like the simulator (short side = X). ``swap`` records
    whether the CDS order lists the long side first (then the design frame's X is the
    stack frame's Y).
    """
    from spacecdf_kb.mechanical import defaults as kb_defaults
    cds = rc.load("cds_rules")
    ff = str(form_factor or "").upper().replace(" ", "")
    E = (cds["envelope_mm"]["values"] or {}).get(ff)
    if not E:
        raise ValueError(f"no CDS envelope for form factor {form_factor!r}")
    E = [float(x) for x in E]
    swap = E[0] > E[1]
    sx, sy, sz = (E[1], E[0], E[2]) if swap else (E[0], E[1], E[2])
    lim = [float(x) for x in (cds["cog_limits_cm"]["values"].get(ff) or [2.0, 2.0, 2.0])]
    lim_sim = [lim[1], lim[0], lim[2]] if swap else list(lim)
    st = kb_defaults().get("structure") or {}
    end = float(st.get("end_allowance_mm", 6.0))
    wall = float(st.get("wall_allowance_mm", 1.0))
    pitch = float(st.get("column_pitch_mm", 100.0))
    nx, ny = max(1, round(sx / pitch)), max(1, round(sy / pitch))
    cw, cd = sx / nx, sy / ny
    cols = []
    for ix in range(nx):
        for iy in range(ny):
            cols.append({"index": len(cols), "cx": -sx / 2 + (ix + 0.5) * cw, "cy": -sy / 2 + (iy + 0.5) * cd,
                         "cell_mm": [cw, cd], "inner_mm": [cw - 2 * wall, cd - 2 * wall]})
    z0, z1 = -sz / 2 + end, sz / 2 - end
    prot = float(cds["mechanical"]["max_protrusion_mm"]["value"])
    return {
        "form_factor": ff, "cds_mm": E, "swap": swap, "size_mm": [sx, sy, sz],
        "cog_limits_cds_cm": lim, "cog_limits_mm": [x * 10.0 for x in lim_sim],
        "end_allowance_mm": end, "wall_allowance_mm": wall, "columns": cols,
        "z0_mm": z0, "z1_mm": z1, "internal_length_mm": z1 - z0, "inner_mm": [sx - 2 * wall, sy - 2 * wall],
        "max_protrusion_mm": prot, "frame": dict(FRAME_NOTE),
        "sources": {"envelope": rc.ref_of(cds, cds["envelope_mm"])["standard_ref"],
                    "cog": rc.ref_of(cds, cds["cog_limits_cm"])["standard_ref"],
                    "protrusion": rc.ref_of(cds, cds["mechanical"]["max_protrusion_mm"])["standard_ref"],
                    "allowances": "C2O default (KB mechanical_defaults.yaml structure)"},
    }


def to_design_m(p_mm: list[float], env: dict) -> list[float]:
    """Stack frame (mm, centre origin, +Z zenith) -> design frame (m, corner origin, +Z nadir)."""
    Ex, Ey, Ez = env["cds_mm"]
    x, y, z = p_mm
    if env["swap"]:
        out = [y + Ex / 2, x + Ey / 2, Ez / 2 - z]
    else:
        out = [x + Ex / 2, Ey / 2 - y, Ez / 2 - z]
    return [round(v / 1000.0, 5) for v in out]


def offset_to_design_axes(v_sim: list[float], env: dict) -> list[float]:
    """A stack-frame offset expressed on the design-frame axes (absolute values per axis)."""
    return [abs(v_sim[1]), abs(v_sim[0]), abs(v_sim[2])] if env["swap"] else [abs(v) for v in v_sim]


# ─────────────────────────────────────────────────────────────── spec building

def _is_column(u: dict) -> bool:
    return u["mech"]["mount_class"] in COLUMN_CLASSES


def _is_face(u: dict) -> bool:
    return u["mech"]["mount_class"] in FACE_CLASSES


def _footprint_fit(a: float, b: float, w: float, d: float) -> tuple[float, float, bool]:
    if a <= w + 1e-6 and b <= d + 1e-6:
        return a, b, True
    if b <= w + 1e-6 and a <= d + 1e-6:
        return b, a, True
    return a, b, False


def _column_dims(u: dict, env: dict) -> dict[str, Any]:
    """Footprint, slot height and fit of a column unit (quantity stacked or tiled)."""
    m = u["mech"]
    a, b, h = (float(x) for x in m["envelope_mm"])
    w, d = env["columns"][0]["inner_mm"]
    fa, fb, fits = _footprint_fit(a, b, w, d)
    if not fits and m["mount_class"] == "u_module":
        # a long module given lying down: put its largest dimension along the stack axis
        dims = sorted([a, b, h])
        fa2, fb2, fits2 = _footprint_fit(dims[0], dims[1], w, d)
        if fits2:
            fa, fb, h, fits = fa2, fb2, dims[2], True
    q = max(1, int(u.get("quantity") or 1))
    per_layer = 1
    if m["mount_class"] == "bracket" and fits:
        per_layer = max(1, int(w // fa) * int(d // fb))
    layers = math.ceil(q / per_layer) if m["mount_class"] in ("bracket",) else q
    slot_unit = float(m.get("stack_height_mm") or h)
    if m["mount_class"] == "u_module":
        slot_unit = max(slot_unit, h)
    iw, idp = env["inner_mm"]
    span = (not fits) and _footprint_fit(fa, fb, iw, idp)[2]
    return {"footprint": [fa, fb], "body_h": h * layers, "slot_h": slot_unit * layers, "fits": fits or span,
            "span": span, "layers": layers}


def _rank(u: dict, units: list[dict], rules: dict) -> int:
    ranks = rules["order"]["rank"]
    role = u["role"]
    if role == "radio":
        nadir = any(x["role"] == "antenna_rf" and (x["mech"].get("face") or "mz") == "mz" for x in units)
        role = "radio_nadir" if nadir else "radio_zenith"
    return int(ranks.get(role, ranks.get("other", 9)))


def _face_groups_auto(u: dict, rules: dict, taken: dict[str, float]) -> list[dict]:
    """Rule faces for a face unit (design rules §4.3 step 2)."""
    m = u["mech"]
    fr = rules["faces"]
    q = max(1, int(u.get("quantity") or 1))
    dep = m.get("deployable") or {}
    if m["mount_class"] == "deployable" and dep.get("kind") == "wing":
        n = q if q > 1 else int(dep.get("wings") or 1)
        faces = list(fr["wing_faces"])
        return [{"face": faces[i % len(faces)], "count": 1} for i in range(n)] if n <= len(faces) else \
            [{"face": f, "count": n // len(faces) + (1 if i < n % len(faces) else 0)} for i, f in enumerate(faces)]
    if m.get("spread") == "one_per_face":
        # faces covered by a stowed wing are skipped (a sensor there would be blind at launch)
        order = [f for f in fr["sun_sensor_order"] if f not in taken.get("_wings", ())] or list(fr["sun_sensor_order"])
        out: dict[str, int] = {}
        for i in range(q):
            f = order[i % len(order)]
            out[f] = out.get(f, 0) + 1
        return [{"face": f, "count": c} for f, c in out.items()]
    if u["role"] == "solar" and not m.get("face"):
        # body cells: the largest free faces first; one face per group, the rest split evenly
        order = [f for f in fr["body_solar_order"]]
        order = [f for f in order if f not in taken.get("_wings", ())] or order
        best = min(order, key=lambda f: (taken.get(f, 0.0), order.index(f)))
        if q == 1:
            return [{"face": best, "count": 1}]
        # spread over the two faces of the best pair (px/mx, py/my) when several panels
        pair = {"px": "mx", "mx": "px", "py": "my", "my": "py", "pz": "px"}[best]
        return [{"face": best, "count": q - q // 2}, {"face": pair, "count": q // 2}]
    return [{"face": m.get("face") or "mz", "count": q}]


def initial_spec(units: list[dict], env: dict, prev: dict | None = None) -> dict[str, Any]:
    """Rule placement (design rules §4.3 steps 1-3), keeping the locked items of ``prev``."""
    rules = _rules()
    prev = prev or {}
    locks = {k: True for k, v in (prev.get("locks") or {}).items() if v}
    ids = {u["id"] for u in units}
    ncol = len(env["columns"])
    spec: dict[str, Any] = {"columns": [[] for _ in range(ncol)], "layers": {"nadir": [], "zenith": []},
                            "faces": {}, "locks": {}}
    locked_col: dict[str, tuple[int, int]] = {}
    for ci, col in enumerate(prev.get("columns") or []):
        for si, pid in enumerate(col):
            if locks.get(pid) and pid in ids and ci < ncol:
                locked_col[pid] = (ci, si)
    for anchor in ("nadir", "zenith"):
        for pid in (prev.get("layers") or {}).get(anchor) or []:
            if locks.get(pid) and pid in ids:
                spec["layers"][anchor].append(pid)
    by = {u["id"]: u for u in units}

    # faces
    taken: dict[str, Any] = {"_wings": set()}
    for u in sorted([u for u in units if _is_face(u)],
                    key=lambda u: (0 if u["mech"]["mount_class"] == "deployable" else 1, -u["mass_kg"], u["id"])):
        old = (prev.get("faces") or {}).get(u["id"])
        if old and all(locks.get(f"{u['id']}@{g['face']}") for g in old):
            groups = old
        else:
            groups = _face_groups_auto(u, rules, taken)
        spec["faces"][u["id"]] = groups
        a, b, _ = u["mech"]["envelope_mm"]
        for g in groups:
            taken[g["face"]] = taken.get(g["face"], 0.0) + a * b * g["count"]
            if (u["mech"].get("deployable") or {}).get("kind") == "wing":
                taken["_wings"].add(g["face"])

    # columns
    load = [0.0] * ncol
    for pid, (ci, _) in locked_col.items():
        load[ci] += _column_dims(by[pid], env)["slot_h"]
    colu = [u for u in units if _is_column(u) and u["id"] not in locked_col and u["id"] not in spec["layers"]["nadir"]
            and u["id"] not in spec["layers"]["zenith"]]
    for u in sorted(colu, key=lambda u: (0 if u["mech"].get("anchor") else 1, -_column_dims(u, env)["slot_h"], u["id"])):
        cd = _column_dims(u, env)
        if cd["span"] and ncol > 1:
            spec["layers"][u["mech"].get("anchor") or "nadir"].append(u["id"])
            for i in range(ncol):
                load[i] += cd["slot_h"]
            continue
        anchor = u["mech"].get("anchor")
        if anchor == "zenith":   # the column with the most room, ties to the last column
            ci = min(range(ncol), key=lambda i: (load[i], -i))
        else:
            ci = min(range(ncol), key=lambda i: (load[i], i))
        spec["columns"][ci].append(u["id"])
        load[ci] += cd["slot_h"]
    for ci in range(ncol):
        spec["columns"][ci].sort(key=lambda pid: (_rank(by[pid], units, rules), -by[pid]["mass_kg"], pid))
    for pid, (ci, si) in sorted(locked_col.items(), key=lambda kv: kv[1]):
        spec["columns"][ci].insert(min(si, len(spec["columns"][ci])), pid)
    spec["locks"] = {k: True for k in locks if k in _all_pids(spec)}
    return spec


def _all_pids(spec: dict) -> set[str]:
    out = {p for col in spec.get("columns") or [] for p in col}
    out |= set((spec.get("layers") or {}).get("nadir") or []) | set((spec.get("layers") or {}).get("zenith") or [])
    for eid, groups in (spec.get("faces") or {}).items():
        out |= {f"{eid}@{g['face']}" for g in groups}
    return out


def normalise_spec(spec: dict, units: list[dict], env: dict) -> tuple[dict, list[str]]:
    """Make an edited spec consistent with the units: drop unknown ids, add new units by
    rule, merge duplicate face groups, keep anchors at their ends. Returns (spec, notes)."""
    notes: list[str] = []
    by = {u["id"]: u for u in units}
    ncol = len(env["columns"])
    out: dict[str, Any] = {"columns": [[] for _ in range(ncol)], "layers": {"nadir": [], "zenith": []},
                           "faces": {}, "locks": {}}
    seen: set[str] = set()
    for ci, col in enumerate((spec.get("columns") or [])[:ncol]):
        for pid in col:
            if pid in by and _is_column(by[pid]) and pid not in seen:
                out["columns"][ci].append(pid)
                seen.add(pid)
    for anchor in ("nadir", "zenith"):
        for pid in (spec.get("layers") or {}).get(anchor) or []:
            if pid in by and _is_column(by[pid]) and pid not in seen:
                out["layers"][anchor].append(pid)
                seen.add(pid)
    for eid, groups in (spec.get("faces") or {}).items():
        if eid not in by or not _is_face(by[eid]):
            continue
        merged: dict[str, int] = {}
        for g in groups or []:
            f = g.get("face")
            if f in FACES:
                merged[f] = merged.get(f, 0) + max(1, int(g.get("count") or 1))
        if merged:
            out["faces"][eid] = [{"face": f, "count": c} for f, c in merged.items()]
    missing = [u for u in units if (_is_column(u) and u["id"] not in seen) or (_is_face(u) and u["id"] not in out["faces"])]
    if missing:
        fill = initial_spec(missing, env)
        for ci, col in enumerate(fill["columns"]):
            out["columns"][ci].extend(col)
        for anchor in ("nadir", "zenith"):
            out["layers"][anchor].extend(fill["layers"][anchor])
        out["faces"].update(fill["faces"])
        notes.append(f"{len(missing)} new unit(s) placed by rule: " + ", ".join(u["name"] for u in missing[:6]))
    pids = _all_pids(out)
    out["locks"] = {k: True for k, v in (spec.get("locks") or {}).items() if v and k in pids}
    return out, notes


# ─────────────────────────────────────────────────────────────── realisation

def _face_rect(face: str, env: dict, rules: dict, inset: float | None = None) -> tuple[float, float, float, float]:
    sx, sy, sz = env["size_mm"]
    ui, vi, _ = FACE_UV[face]
    size = (sx, sy, sz)
    if face in ("pz", "mz"):
        ins = float(rules["faces"]["end_inset_mm"]) if inset is None else inset
        return (-size[ui] / 2 + ins, -size[vi] / 2 + ins, size[ui] / 2 - ins, size[vi] / 2 - ins)
    ins = float(rules["faces"]["side_inset_mm"]) if inset is None else inset
    endv = env["end_allowance_mm"] if inset is None else inset
    return (-size[ui] / 2 + ins, -size[vi] / 2 + endv, size[ui] / 2 - ins, size[vi] / 2 - endv)


def _overlap2(a: tuple, b: tuple, tol: float = 0.05) -> bool:
    return a[0] < b[2] - tol and b[0] < a[2] - tol and a[1] < b[3] - tol and b[1] < a[3] - tol


def _pack_rects(rect: tuple, blocked: list[tuple], sizes: list[tuple[float, float]]) -> list[tuple | None]:
    """Bottom-left fill of ``sizes`` (w along u, h along v) into ``rect`` around ``blocked``."""
    placed: list[tuple] = list(blocked)
    out: list[tuple | None] = []
    for (w, h) in sizes:
        cands = {(rect[0], rect[1])}
        for p in placed:
            cands |= {(p[2], rect[1]), (rect[0], p[3]), (p[2], p[1]), (p[0], p[3])}
        best = None
        for (u0, v0) in sorted(cands, key=lambda c: (round(c[1], 3), round(c[0], 3))):
            for (ww, hh) in ((w, h), (h, w)):
                r = (u0, v0, u0 + ww, v0 + hh)
                if r[2] > rect[2] + 1e-6 or r[3] > rect[3] + 1e-6 or r[0] < rect[0] - 1e-6 or r[1] < rect[1] - 1e-6:
                    continue
                if any(_overlap2(r, p) for p in placed):
                    continue
                best = r
                break
            if best:
                break
        out.append(best)
        if best:
            placed.append(best)
    return out


def _to3(face: str, u: float, v: float, n_off: float, env: dict) -> list[float]:
    ui, vi, ni = FACE_UV[face]
    p = [0.0, 0.0, 0.0]
    p[ui], p[vi] = u, v
    sign = NORMALS[face][ni]
    p[ni] = sign * (env["size_mm"][ni] / 2 + n_off)
    return p


def realise(spec: dict, units: list[dict], env: dict) -> dict[str, Any]:
    """Positions and boxes (stack frame, mm) of every placement of ``spec``."""
    rules = _rules()
    by = {u["id"]: u for u in units}
    locks = spec.get("locks") or {}
    placements: list[dict] = []
    z0, z1 = env["z0_mm"], env["z1_mm"]
    sx, sy, sz = env["size_mm"]

    def col_item(pid: str, ci: int | None, si: int, zlo: float, cd: dict, cx: float, cy: float, layer: str | None) -> dict:
        u = by[pid]
        m = u["mech"]
        fa, fb = cd["footprint"]
        return {
            "id": pid, "element_id": pid, "name": u["name"], "subsystem": u["subsystem"], "role": u["role"],
            "mount_class": m["mount_class"], "column": ci, "slot": si, "layer": layer, "face": m.get("face"),
            "anchor": m.get("anchor"), "center_mm": [cx, cy, zlo + cd["slot_h"] / 2],
            "size_mm": [fa, fb, cd["slot_h"]], "body_h_mm": min(cd["body_h"], cd["slot_h"]),
            "z_mm": [zlo, zlo + cd["slot_h"]], "fits": cd["fits"], "span": cd["span"],
            "mass_kg": u["mass_kg"], "power_w": u["power_w"], "count": u["quantity"],
            "boresight": m.get("boresight"), "fov_deg": m.get("fov_deg"), "locked": bool(locks.get(pid)),
            "manufacturer": u.get("manufacturer"), "connector": m.get("connector"),
            "assumptions": m.get("assumptions") or [], "deployable": None, "tiles": None,
        }

    # full-width layers at the ends
    lo, hi = z0, z1
    norm_layers: dict[str, list[str]] = {"nadir": [], "zenith": []}
    for pid in (spec.get("layers") or {}).get("nadir") or []:
        cd = _column_dims(by[pid], env)
        placements.append(col_item(pid, None, len(norm_layers["nadir"]), lo, cd, 0.0, 0.0, "nadir"))
        norm_layers["nadir"].append(pid)
        lo += cd["slot_h"]
    for pid in (spec.get("layers") or {}).get("zenith") or []:
        cd = _column_dims(by[pid], env)
        hi -= cd["slot_h"]
        placements.append(col_item(pid, None, len(norm_layers["zenith"]), hi, cd, 0.0, 0.0, "zenith"))
        norm_layers["zenith"].append(pid)

    columns_out = []
    norm_cols: list[list[str]] = []
    for ci, col in enumerate(spec.get("columns") or []):
        c = env["columns"][ci]
        nad = [p for p in col if by[p]["mech"].get("anchor") == "nadir"]
        zen = [p for p in col if by[p]["mech"].get("anchor") == "zenith"]
        free = [p for p in col if p not in nad and p not in zen]
        order = nad + free + zen
        norm_cols.append(order)
        dims = {p: _column_dims(by[p], env) for p in order}
        z = lo
        for p in nad:
            placements.append(col_item(p, ci, order.index(p), z, dims[p], c["cx"], c["cy"], None))
            z += dims[p]["slot_h"]
        top = hi
        zen_items = []
        for p in reversed(zen):
            top -= dims[p]["slot_h"]
            zen_items.append((p, top))
        F = sum(dims[p]["slot_h"] for p in free)
        A = top - z
        start = z + (A - F) / 2 if F <= A else z
        zz = start
        for p in free:
            placements.append(col_item(p, ci, order.index(p), zz, dims[p], c["cx"], c["cy"], None))
            zz += dims[p]["slot_h"]
        for p, t in zen_items:
            placements.append(col_item(p, ci, order.index(p), t, dims[p], c["cx"], c["cy"], None))
        used = sum(d["slot_h"] for d in dims.values()) + (lo - z0) + (z1 - hi)
        columns_out.append({"index": ci, "cx": c["cx"], "cy": c["cy"], "inner_mm": c["inner_mm"], "order": order,
                            "used_mm": round(used, 2), "length_mm": round(env["internal_length_mm"], 2),
                            "free_mm": round(env["internal_length_mm"] - used, 2)})

    # faces
    blocked: dict[str, list[tuple]] = {f: [] for f in FACES}
    for p in placements:
        f = p.get("face")
        if f not in FACES:
            continue
        ui, vi, ni = FACE_UV[f]
        c, s = p["center_mm"], p["size_mm"]
        touches = abs(abs(c[ni] + NORMALS[f][ni] * s[ni] / 2) - env["size_mm"][ni] / 2) < env["end_allowance_mm"] + 1 \
            if f in ("pz", "mz") else True
        if not touches:
            continue
        if f in ("pz", "mz"):
            r = (c[ui] - s[ui] / 2, c[vi] - s[vi] / 2, c[ui] + s[ui] / 2, c[vi] + s[vi] / 2)
        else:   # a nozzle / port on a side face: a 30 mm port at the unit's height
            r = (c[ui] - 15, c[vi] - 15, c[ui] + 15, c[vi] + 15)
        p["port_rect_mm"] = [round(x, 2) for x in r]
        blocked[f].append(r)
    groups_by_face: dict[str, list[tuple[str, dict, dict]]] = {f: [] for f in FACES}
    for eid, groups in (spec.get("faces") or {}).items():
        for g in groups:
            groups_by_face[g["face"]].append((eid, g, by[eid]))
    for f in FACES:
        rect = _face_rect(f, env, rules)
        # deployables first (hinged at the rail edges, they may cover the full face width),
        # then body-mounted items between the rails around what is already there
        wide = _face_rect(f, env, rules, inset=0.0)
        items = sorted(groups_by_face[f], key=lambda t: (0 if t[2]["mech"]["mount_class"] == "deployable" else 1,
                                                         -(t[2]["mech"]["envelope_mm"][0] * t[2]["mech"]["envelope_mm"][1]), t[0]))
        tiles_by: dict[str, list] = {}
        taken_f = list(blocked[f])
        for cls, r_use in (("deployable", wide), ("face_panel", rect)):
            sizes, owners = [], []
            for eid, g, u in items:
                if u["mech"]["mount_class"] != cls:
                    continue
                a, b, _ = u["mech"]["envelope_mm"]
                # long side along v (the rail axis on the side faces)
                w, h = (min(a, b), max(a, b)) if f not in ("pz", "mz") else (max(a, b), min(a, b))
                for k in range(int(g["count"])):
                    sizes.append((w, h))
                    owners.append((eid, g, u, k))
            rects = _pack_rects(r_use, taken_f, sizes)
            for (eid, g, u, k), r in zip(owners, rects):
                tiles_by.setdefault(eid, []).append(r)
                if r is not None:
                    taken_f.append(r)
        for eid, g, u in items:
            m = u["mech"]
            rs = tiles_by.get(eid, [])
            ok = [r for r in rs if r is not None]
            over = len(rs) - len(ok)
            t = float(m["envelope_mm"][2])
            if not ok:
                cu, cv = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
                a, b, _ = m["envelope_mm"]
                ok_draw = [(cu - a / 2, cv - b / 2, cu + a / 2, cv + b / 2)]
            else:
                ok_draw = ok
            u0 = min(r[0] for r in ok_draw); v0 = min(r[1] for r in ok_draw)
            u1 = max(r[2] for r in ok_draw); v1 = max(r[3] for r in ok_draw)
            ui, vi, ni = FACE_UV[f]
            recess = env["end_allowance_mm"] if f in ("pz", "mz") else 0.0
            n_off = t / 2 - recess
            center = _to3(f, (u0 + u1) / 2, (v0 + v1) / 2, n_off, env)
            size = [0.0, 0.0, 0.0]
            size[ui], size[vi], size[ni] = u1 - u0, v1 - v0, t
            tiles3 = []
            for r in ok_draw:
                tc = _to3(f, (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, n_off, env)
                ts = [0.0, 0.0, 0.0]
                ts[ui], ts[vi], ts[ni] = r[2] - r[0], r[3] - r[1], t
                tiles3.append({"center_mm": [round(x, 2) for x in tc], "size_mm": [round(x, 2) for x in ts],
                               "uv_mm": [round(x, 2) for x in r]})
            pid = f"{eid}@{f}"
            share = g["count"] / max(1, u["quantity"])
            placements.append({
                "id": pid, "element_id": eid, "name": u["name"], "subsystem": u["subsystem"], "role": u["role"],
                "mount_class": m["mount_class"], "column": None, "slot": None, "layer": None, "face": f,
                "anchor": None, "center_mm": center, "size_mm": size, "body_h_mm": t, "z_mm": None,
                "fits": over == 0 and bool(ok), "overflow": over if ok else len(rs), "span": False,
                "mass_kg": round(u["mass_kg"] * share, 4), "power_w": round(u["power_w"] * share, 3),
                "count": g["count"], "boresight": m.get("boresight") or list(NORMALS[f]), "fov_deg": m.get("fov_deg"),
                "locked": bool(locks.get(pid)), "manufacturer": u.get("manufacturer"), "connector": None,
                "assumptions": m.get("assumptions") or [], "tiles": tiles3,
                "protrusion_mm": round(max(0.0, t - recess), 2),
                "deployable": _deployed(u, f, tiles3, env) if m["mount_class"] == "deployable" else None,
            })

    # units that are not in a column or on a face: the structure and distributed mass at the centre
    for u in units:
        if u["mech"]["mount_class"] in ("structure", "distributed"):
            placements.append({
                "id": u["id"], "element_id": u["id"], "name": u["name"], "subsystem": u["subsystem"], "role": u["role"],
                "mount_class": u["mech"]["mount_class"], "column": None, "slot": None, "layer": None, "face": None,
                "anchor": None, "center_mm": [0.0, 0.0, 0.0], "size_mm": [sx, sy, sz], "body_h_mm": None, "z_mm": None,
                "fits": True, "span": False, "mass_kg": u["mass_kg"], "power_w": u["power_w"], "count": u["quantity"],
                "boresight": None, "fov_deg": None, "locked": False, "manufacturer": u.get("manufacturer"),
                "connector": None, "assumptions": u["mech"].get("assumptions") or [], "deployable": None, "tiles": None,
                "distributed": True,
            })

    for p in placements:
        p["center_mm"] = [round(x, 2) for x in p["center_mm"]]
        p["size_mm"] = [round(x, 2) for x in p["size_mm"]]
        if p.get("z_mm"):
            p["z_mm"] = [round(x, 2) for x in p["z_mm"]]
        p["origin"] = (spec.get("origins") or {}).get(p["id"], AUTO_ORIGIN if not p["locked"] else "user")

    mtot = sum(p["mass_kg"] for p in placements)
    cog = [sum(p["mass_kg"] * p["center_mm"][k] for p in placements) / mtot for k in range(3)] if mtot > 0 else [0.0, 0.0, 0.0]
    norm = {"columns": norm_cols, "layers": norm_layers, "faces": copy.deepcopy(spec.get("faces") or {}),
            "locks": {k: True for k, v in (spec.get("locks") or {}).items() if v},
            "origins": dict(spec.get("origins") or {})}
    return {"placements": placements, "columns": columns_out, "cog_mm": [round(x, 2) for x in cog],
            "mass_kg": round(mtot, 4), "spec": norm}


def _deployed(u: dict, face: str, tiles: list[dict], env: dict) -> dict[str, Any]:
    """Deployed geometry of a stowed deployable (stack frame, mm): wings unfold outward
    along the face normal in the plane of the normal and Z (simulator wings); antenna
    elements unfold in the face plane from the tile edges."""
    m = u["mech"]
    dep = m.get("deployable") or {}
    n = NORMALS[face]
    ui, vi, ni = FACE_UV[face]
    boxes: list[dict] = []
    if dep.get("kind") == "wing":
        panels = int(dep.get("panels") or 1)
        for ti, t in enumerate(tiles):
            c, s = t["center_mm"], t["size_mm"]
            along = s[vi]            # long side along Z
            out = s[ui]              # each panel's outward size = the stowed short side
            for k in range(panels):
                d = 30.0 + out * (k + 0.5)
                ctr = [c[0], c[1], c[2]]
                ctr[ni] = NORMALS[face][ni] * (env["size_mm"][ni] / 2 + d)
                ctr[ui] = c[ui]
                size = [0.0, 0.0, 0.0]
                size[ni], size[vi], size[ui] = out, along, 4.0
                boxes.append({"center_mm": [round(x, 2) for x in ctr], "size_mm": [round(x, 2) for x in size],
                              "kind": "panel", "tile": ti})
        return {"kind": "wing", "panels": panels, "boxes": boxes,
                "hinge": {"face": face, "axis": [0, 0, 1] if face in ("px", "mx", "py", "my") else [1, 0, 0]},
                "panel_size_mm": [round(tiles[0]["size_mm"][ui], 2), round(tiles[0]["size_mm"][vi], 2)] if tiles else None}
    L = float(dep.get("length_mm") or 170.0)
    k = int(dep.get("elements") or 1)
    dirs_uv = [(1, 0), (-1, 0), (0, 1), (0, -1)][:max(1, min(4, k))]
    rods = []
    for ti, t in enumerate(tiles):
        c, s = t["center_mm"], t["size_mm"]
        for (du, dv) in dirs_uv:
            d = [0.0, 0.0, 0.0]
            d[ui], d[vi] = float(du), float(dv)
            half = s[ui] / 2 if du else s[vi] / 2
            start = [c[i] + d[i] * half for i in range(3)]
            start[ni] = NORMALS[face][ni] * (env["size_mm"][ni] / 2 + 2.0)   # hinged just outside the face plane
            ctr = [start[i] + d[i] * L / 2 for i in range(3)]
            size = [3.0, 3.0, 3.0]
            size[ui if du else vi] = L
            boxes.append({"center_mm": [round(x, 2) for x in ctr], "size_mm": [round(x, 2) for x in size], "kind": "rod",
                          "tile": ti})
            rods.append({"start_mm": [round(x, 2) for x in start], "dir": d, "length_mm": L})
    return {"kind": dep.get("kind") or "antenna", "boxes": boxes, "rods": rods,
            "hinge": {"face": face, "axis": list(n)}}


# ─────────────────────────────────────────────────────────────── score

def _pairs(units: list[dict], interfaces: list[dict] | None) -> list[tuple[str, str, float]]:
    rules = _rules()
    by_role: dict[str, list[str]] = {}
    for u in units:
        by_role.setdefault(u["role"], []).append(u["id"])
    out: list[tuple[str, str, float]] = []
    for a, b, w in rules["harness"]["pairs"]:
        for x in by_role.get(a, []):
            for y in by_role.get(b, []):
                if x != y:
                    out.append((x, y, float(w)))
    ids = {u["id"] for u in units}
    iw = rules["harness"]["interface_weights"]
    for i in interfaces or []:
        if i.get("status") == "rejected" or i.get("deleted_at"):
            continue
        a, b = i.get("from_element_id"), i.get("to_element_id")
        t = str(i.get("interface_type") or i.get("type") or "").lower()
        if a in ids and b in ids and t in iw:
            out.append((a, b, float(iw[t])))
    return out


def score(real: dict, units: list[dict], env: dict, pairs: list[tuple[str, str, float]]) -> dict[str, float]:
    rules = _rules()
    opt = rules["optimise"]
    sz = env["size_mm"][2]
    lim = env["cog_limits_mm"]
    cog = real["cog_mm"]
    ratio = [abs(cog[k]) / lim[k] if lim[k] else 0.0 for k in range(3)]
    cog_term = sum(r * r for r in ratio) + 10.0 * sum(max(0.0, r - 1.0) ** 2 for r in ratio)
    centre: dict[str, list[float]] = {}
    mass: dict[str, float] = {}
    for p in real["placements"]:
        e = p["element_id"]
        m = max(p["mass_kg"], 1e-6)
        if e in centre:
            M = mass[e] + m
            centre[e] = [(centre[e][k] * mass[e] + p["center_mm"][k] * m) / M for k in range(3)]
            mass[e] = M
        else:
            centre[e], mass[e] = list(p["center_mm"]), m
    harness = sum(w * _dist(centre[a], centre[b]) / sz for a, b, w in pairs if a in centre and b in centre)
    wsum = sum(w for a, b, w in pairs if a in centre and b in centre) or 1.0
    harness /= wsum
    rad = rules["thermal"]["radiator_face"]
    ni = FACE_UV[rad][2]
    plane = NORMALS[rad][ni] * env["size_mm"][ni] / 2
    hot = [p for p in real["placements"] if p.get("column") is not None or p.get("layer")]
    ptot = sum(p["power_w"] for p in hot) or 0.0
    thermal = 0.0
    if ptot > 0:
        thermal = sum(p["power_w"] * abs(p["center_mm"][ni] - plane) / env["size_mm"][ni] for p in hot) / ptot
        d0 = float(opt["hot_spot_distance_mm"])
        hu = float(opt["hot_unit_w"])
        hs = [p for p in hot if p["power_w"] >= hu]
        thermal += 0.5 * sum(a["power_w"] * b["power_w"] / ptot ** 2 * d0 / (_dist(a["center_mm"], b["center_mm"]) + d0)
                             for a, b in itertools.combinations(hs, 2))
    total = float(opt["w_cog"]) * cog_term + float(opt["w_harness"]) * harness + float(opt["w_thermal"]) * thermal
    over = sum(max(0.0, c["used_mm"] - c["length_mm"]) for c in real["columns"]) / sz
    total += 100.0 * over
    return {"total": round(total, 6), "cog": round(cog_term, 6), "harness": round(harness, 6),
            "thermal": round(thermal, 6), "overflow": round(over, 6)}


def optimise(spec: dict, units: list[dict], env: dict, interfaces: list[dict] | None = None) -> tuple[dict, dict]:
    """Deterministic swap search (§4.3 step 4): swaps of two free units and moves of a free
    unit to any slot of any column; locked and anchored units stay. First improvement,
    candidates in sorted id order, up to ``max_passes`` passes."""
    rules = _rules()
    by = {u["id"]: u for u in units}
    pairs = _pairs(units, interfaces)
    locks = spec.get("locks") or {}
    start = score(realise(spec, units, env), units, env, pairs)
    best_spec, best = copy.deepcopy(spec), start
    movable = sorted(p for col in spec["columns"] for p in col
                     if not locks.get(p) and not by[p]["mech"].get("anchor"))

    def where(s: dict, pid: str) -> tuple[int, int]:
        for ci, col in enumerate(s["columns"]):
            if pid in col:
                return ci, col.index(pid)
        raise KeyError(pid)

    def locked_at(s: dict) -> dict[int, dict[int, str]]:
        out: dict[int, dict[int, str]] = {}
        for ci, col in enumerate(s["columns"]):
            for si, p in enumerate(col):
                if locks.get(p):
                    out.setdefault(ci, {})[si] = p
        return out

    pins = locked_at(spec)

    def rebuild(cols: list[list[str]]) -> list[list[str]]:
        out = []
        for ci, col in enumerate(cols):
            free = [p for p in col if not locks.get(p)]
            for si in sorted(pins.get(ci, {})):
                free.insert(min(si, len(free)), pins[ci][si])
            out.append(free)
        return out

    passes = moves = 0
    for _ in range(int(rules["optimise"]["max_passes"])):
        passes += 1
        improved = False
        # swaps
        for a, b in itertools.combinations(movable, 2):
            ca, ia = where(best_spec, a)
            cb, ib = where(best_spec, b)
            cand = copy.deepcopy(best_spec)
            cand["columns"][ca][ia], cand["columns"][cb][ib] = b, a
            s = score(realise(cand, units, env), units, env, pairs)
            if s["total"] < best["total"] - 1e-9:
                best_spec, best, improved = cand, s, True
                moves += 1
        # moves to another slot / column
        for a in movable:
            ca, ia = where(best_spec, a)
            for cb in range(len(best_spec["columns"])):
                base = [list(c) for c in best_spec["columns"]]
                base[ca].remove(a)
                for j in range(len(base[cb]) + 1):
                    if cb == ca and j == ia:
                        continue
                    cols = [list(c) for c in base]
                    cols[cb].insert(j, a)
                    cand = {**best_spec, "columns": rebuild(cols)}
                    s = score(realise(cand, units, env), units, env, pairs)
                    if s["total"] < best["total"] - 1e-9:
                        best_spec, best, improved = copy.deepcopy(cand), s, True
                        moves += 1
                        break
                else:
                    continue
                break
        if not improved:
            break
    return best_spec, {"start": start, "end": best, "passes": passes, "moves": moves,
                       "weights": {k: rules["optimise"][k] for k in ("w_cog", "w_harness", "w_thermal")}}


def auto_place(units: list[dict], env: dict, prev_spec: dict | None = None,
               interfaces: list[dict] | None = None) -> tuple[dict, dict]:
    """Rule placement then swap search; locked items of ``prev_spec`` keep their slot/face."""
    spec = initial_spec(units, env, prev_spec)
    spec, report = optimise(spec, units, env, interfaces)
    spec = realise(spec, units, env)["spec"]
    spec["origins"] = {p: ("user" if (spec.get("locks") or {}).get(p) else AUTO_ORIGIN) for p in _all_pids(spec)}
    return spec, report


# ─────────────────────────────────────────────────────────────── checks

def _item(cid: str, label: tuple[str, str], status: str, detail: tuple[str, str], ref: dict, **extra: Any) -> dict:
    return rc.check_item(cid, {"en": label[0], "fr": label[1]}, status, {"en": detail[0], "fr": detail[1]}, ref, **extra)


def _aabb(c: list[float], s: list[float]) -> tuple[list[float], list[float]]:
    return [c[k] - s[k] / 2 for k in range(3)], [c[k] + s[k] / 2 for k in range(3)]


def _boxes_overlap(a: tuple, b: tuple, tol: float = 0.1) -> bool:
    return all(a[0][k] < b[1][k] - tol and b[0][k] < a[1][k] - tol for k in range(3))


def _earth_half_angle_deg(alt_km: float) -> float:
    R = 6371.0
    return math.degrees(math.asin(R / (R + max(alt_km, 100.0))))


def _angle_deg(a: list[float], b: list[float]) -> float:
    ua, ub = _unit_vec(a), _unit_vec(b)
    if not ua or not ub:
        return 180.0
    d = max(-1.0, min(1.0, sum(ua[k] * ub[k] for k in range(3))))
    return math.degrees(math.acos(d))


def run_checks(real: dict, units: list[dict], env: dict, orbit_alt_km: float | None = None) -> list[dict]:
    """STACK-* checks (design rules §4.4) on a realised layout."""
    rules = _rules()
    P = real["placements"]
    out: list[dict] = []
    L = env["internal_length_mm"]

    # column height
    over = [c for c in real["columns"] if c["used_mm"] > c["length_mm"] + 0.05]
    txt = "; ".join(f"{c['index'] + 1}: {_f(c['used_mm'])}/{_f(c['length_mm'])}" for c in real["columns"])
    out.append(_item("STACK-HEIGHT", ("Column height within the internal length", "Hauteur des colonnes dans la longueur interne"),
                     "fail" if over else "pass",
                     (f"Column used/available (mm): {txt}. Internal length = envelope {_f(env['size_mm'][2])} mm "
                      f"minus 2 x {_f(env['end_allowance_mm'])} mm end allowance (C2O default).",
                      f"Colonne utilisée/disponible (mm) : {txt}. Longueur interne = enveloppe {_f(env['size_mm'][2])} mm "
                      f"moins 2 x {_f(env['end_allowance_mm'])} mm aux extrémités (valeur par défaut C2O)."),
                     _ref("order", clause="§4.4 column height", source="design_rules"),
                     value=[c["used_mm"] for c in real["columns"]], limit=round(L, 2), unit="mm",
                     element_ids=sorted({p["element_id"] for p in P for c in over if p.get("column") == c["index"]})))

    # envelope
    misfit = [p for p in P if not p.get("fits", True) and not p.get("distributed")]
    out.append(_item("STACK-ENV", ("Every unit inside the CDS envelope", "Chaque unité dans l’enveloppe CDS"),
                     "fail" if misfit else "pass",
                     ((f"{len(misfit)} unit(s) do not fit their column or face: " + ", ".join(p["name"] for p in misfit[:6]) + ".")
                      if misfit else f"All units fit (column inner {_f(env['columns'][0]['inner_mm'][0])} x "
                                     f"{_f(env['columns'][0]['inner_mm'][1])} mm, faces inside the rails).",
                      (f"{len(misfit)} unité(s) ne tiennent pas dans leur colonne ou leur face : " + ", ".join(p["name"] for p in misfit[:6]) + ".")
                      if misfit else f"Toutes les unités tiennent (intérieur de colonne {_f(env['columns'][0]['inner_mm'][0])} x "
                                     f"{_f(env['columns'][0]['inner_mm'][1])} mm, faces entre les rails)."),
                     _cds_ref("Appendix B (envelope)"), element_ids=sorted({p["element_id"] for p in misfit})))

    # protrusion of stowed face items
    lim = env["max_protrusion_mm"]
    faces = [p for p in P if p.get("face") and p.get("tiles")]
    bad = [p for p in faces if (p.get("protrusion_mm") or 0) > lim + 1e-6]
    worst = max([p.get("protrusion_mm") or 0 for p in faces], default=0.0)
    out.append(_item("STACK-PROTR", ("Stowed protrusion from the rail plane", "Dépassement replié du plan des rails"),
                     "fail" if bad else ("pass" if faces else "not_evaluated"),
                     ((f"{len(bad)} face item(s) above {_f(lim)} mm: " + ", ".join(f"{p['name']} {_f(p['protrusion_mm'])} mm" for p in bad[:5]) + ".")
                      if bad else (f"Largest stowed protrusion {_f(worst)} mm (limit {_f(lim)} mm; end faces keep "
                                   f"{_f(env['end_allowance_mm'])} mm of rail-foot recess)." if faces else "No face items."),
                      (f"{len(bad)} élément(s) de face au-delà de {_f(lim)} mm : " + ", ".join(f"{p['name']} {_f(p['protrusion_mm'])} mm" for p in bad[:5]) + ".")
                      if bad else (f"Plus grand dépassement replié {_f(worst)} mm (limite {_f(lim)} mm ; les faces d’extrémité gardent "
                                   f"{_f(env['end_allowance_mm'])} mm de retrait des pieds de rail)." if faces else "Aucun élément de face.")),
                     _cds_ref("2.2.3"), value=round(worst, 2), limit=lim, unit="mm", element_ids=sorted({p["element_id"] for p in bad})))

    # collisions: column items, face tiles, deployed geometry vs body and each other
    hits: list[tuple[str, str]] = []
    col_items = [p for p in P if p.get("z_mm")]
    for a, b in itertools.combinations(col_items, 2):
        same = (a.get("column") is not None and a.get("column") == b.get("column")) or a.get("layer") or b.get("layer")
        if same and _boxes_overlap(_aabb(a["center_mm"], a["size_mm"]), _aabb(b["center_mm"], b["size_mm"])):
            hits.append((a["name"], b["name"]))
    tiles = [(p, t) for p in faces if p.get("fits", True) for t in (p.get("tiles") or [])]
    for (pa, ta), (pb, tb) in itertools.combinations(tiles, 2):
        if pa["id"] == pb["id"] or pa["face"] != pb["face"]:
            continue
        if _overlap2(tuple(ta["uv_mm"]), tuple(tb["uv_mm"])):
            hits.append((pa["name"], pb["name"]))
    body = _aabb([0.0, 0.0, 0.0], [x - 0.5 for x in env["size_mm"]])
    dep = [(p, bx) for p in P if p.get("deployable") for bx in p["deployable"]["boxes"]]
    for p, bx in dep:
        if _boxes_overlap(_aabb(bx["center_mm"], bx["size_mm"]), body):
            hits.append((p["name"] + " (deployed)", "body"))
    for (pa, ba), (pb, bb) in itertools.combinations(dep, 2):
        if (pa["id"], ba.get("tile")) != (pb["id"], bb.get("tile")) and _boxes_overlap(_aabb(ba["center_mm"], ba["size_mm"]), _aabb(bb["center_mm"], bb["size_mm"])):
            hits.append((pa["name"] + " (deployed)", pb["name"] + " (deployed)"))
    hits = sorted(set(hits))
    htxt = "; ".join(f"{a} / {b}" for a, b in hits[:5])
    out.append(_item("STACK-COLL", ("No collisions, stowed or deployed", "Aucune collision, replié ou déployé"),
                     "fail" if hits else "pass",
                     (f"{len(hits)} overlap(s): {htxt}." if hits else "No overlapping boxes in the stack, on the faces or in the deployed configuration.",
                      f"{len(hits)} chevauchement(s) : {htxt}." if hits else "Aucune boîte ne se chevauche dans la pile, sur les faces ni en configuration déployée."),
                     _ref("keep_out", clause="§4.4 collision (STACK-COLL)", source="design_rules"), count=len(hits)))

    # CoG box (stowed)
    cog = real["cog_mm"]
    limmm = env["cog_limits_mm"]
    off_d = offset_to_design_axes(cog, env)
    lim_d = [x * 10 for x in env["cog_limits_cds_cm"]]
    okc = all(abs(cog[k]) <= limmm[k] + 1e-6 for k in range(3))
    ctxt = ", ".join(f"{'XYZ'[k]} {_f(off_d[k] / 10, 2)}/{_f(lim_d[k] / 10, 1)}" for k in range(3))
    has_mass = real["mass_kg"] > 0
    out.append(_item("STACK-COG", ("Centre of gravity within the CDS box (stowed)", "Centre de gravité dans la boîte du CDS (replié)"),
                     ("pass" if okc else "fail") if has_mass else "not_evaluated",
                     (f"Offset from the geometric centre, design-frame axes (cm, actual/limit): {ctxt}.",
                      f"Écart au centre géométrique, axes du repère de conception (cm, réel/limite) : {ctxt}."),
                     _cds_ref("2.2.11, Table 2"), value=[round(x / 10, 3) for x in off_d], limit=env["cog_limits_cds_cm"], unit="cm",
                     cog_stack_mm=cog))

    # keep-out cones vs deployed geometry
    margin = float(rules["keep_out"]["margin_deg"])
    sensors = [p for p in P if p.get("fov_deg") and p.get("boresight") and p["role"] in ("star_tracker", "payload")]
    blocked: list[str] = []
    for s in sensors:
        apex = _aperture(s, env)
        half = float(s["fov_deg"]) / 2 + margin
        for p, bx in dep:
            for pt in _sample_box(bx["center_mm"], bx["size_mm"]):
                v = [pt[k] - apex[k] for k in range(3)]
                if sum(x * x for x in v) < 1 or sum(v[k] * s["boresight"][k] for k in range(3)) <= 0:
                    continue
                if _angle_deg(v, s["boresight"]) < half:
                    blocked.append(f"{s['name']} / {p['name']}")
                    break
    blocked = sorted(set(blocked))
    out.append(_item("STACK-KEEPOUT", ("Optical keep-out cones clear of deployables", "Cônes d’exclusion optiques libres de déployables"),
                     "fail" if blocked else ("pass" if sensors else "not_evaluated"),
                     ((f"{len(blocked)} cone(s) cut by deployed geometry: " + "; ".join(blocked[:5]) + ".") if blocked else
                      (f"{len(sensors)} optical boresight(s) clear (half-angle + {_f(margin)} deg margin)." if sensors else "No optical sensor placed."),
                      (f"{len(blocked)} cône(s) coupé(s) par la géométrie déployée : " + "; ".join(blocked[:5]) + ".") if blocked else
                      (f"{len(sensors)} axe(s) optique(s) dégagé(s) (demi-angle + {_f(margin)} deg de marge)." if sensors else "Aucun capteur optique placé.")),
                     _ref("keep_out", source="design_rules", clause="§4.4 keep-out (EI-07)"), count=len(blocked)))

    # star tracker vs the Earth limb in the nominal nadir attitude
    st = rules["star_tracker"]
    alt = float(orbit_alt_km or st["default_altitude_km"])
    limb = _earth_half_angle_deg(alt)
    sts = [p for p in P if p["role"] == "star_tracker" and p.get("boresight")]
    worst_st = None
    for s in sts:
        clearance = _angle_deg(s["boresight"], [0, 0, -1]) - limb
        if worst_st is None or clearance < worst_st[1]:
            worst_st = (s, clearance)
    need = float(st["earth_exclusion_deg"])
    if worst_st is None:
        status, det = "not_evaluated", ("No star tracker placed.", "Aucun senseur stellaire placé.")
    else:
        s, cl = worst_st
        status = "pass" if cl >= need else "fail"
        det = (f"{s['name']}: boresight {_f(cl)} deg above the Earth limb at {_f(alt, 0)} km in nadir pointing "
               f"(need {_f(need)} deg; sun exclusion {_f(float(st['sun_exclusion_deg']))} deg depends on the orbit, not checked here).",
               f"{s['name']} : axe à {_f(cl)} deg au-dessus du limbe terrestre à {_f(alt, 0)} km en pointage nadir "
               f"(il faut {_f(need)} deg ; l’exclusion solaire de {_f(float(st['sun_exclusion_deg']))} deg dépend de l’orbite, non vérifiée ici).")
    out.append(_item("STACK-ST-EARTH", ("Star tracker clear of the Earth limb", "Senseur stellaire dégagé du limbe terrestre"),
                     status, det, _ref("star_tracker", source="design_rules", clause="§4.3 step 2"),
                     value=round(worst_st[1], 2) if worst_st else None, limit=need, unit="deg"))

    # PC/104 vendor mix
    pcb = [p for p in P if p["mount_class"] in ("pc104_board", "pc104_module")]
    vendors = sorted({str(p.get("manufacturer")) for p in pcb if p.get("manufacturer")})
    mixed = len(vendors) > 1
    out.append(_item("STACK-PC104", ("PC/104 header pinout from one vendor", "Brochage PC/104 d’un seul fournisseur"),
                     "warn" if mixed else ("pass" if pcb else "not_evaluated"),
                     (f"Boards from {len(vendors)} vendors on the stack ({', '.join(vendors)}): check the H1/H2 pinout of every board."
                      if mixed else (f"{len(pcb)} PC/104 unit(s), one vendor." if pcb else "No PC/104 unit."),
                      f"Cartes de {len(vendors)} fournisseurs dans la pile ({', '.join(vendors)}) : vérifier le brochage H1/H2 de chaque carte."
                      if mixed else (f"{len(pcb)} unité(s) PC/104, un seul fournisseur." if pcb else "Aucune unité PC/104.")),
                     _ref("pc104", source="design_rules", clause="§4.1 bus connector compatibility"), vendors=vendors))
    return out


def _aperture(p: dict, env: dict) -> list[float]:
    """Where an optical unit looks out: the centre of its box face along the boresight."""
    b = _unit_vec(p["boresight"]) or [0, 0, 1]
    k = max(range(3), key=lambda i: abs(b[i]))
    a = list(p["center_mm"])
    a[k] = p["center_mm"][k] + math.copysign(p["size_mm"][k] / 2, b[k])
    if p.get("z_mm") and k == 2:   # a column unit looks through the end plate
        a[2] = math.copysign(env["size_mm"][2] / 2, b[2])
    return a


def _sample_box(c: list[float], s: list[float]) -> list[list[float]]:
    pts = [list(c)]
    for dx in (-0.5, 0.0, 0.5):
        for dy in (-0.5, 0.0, 0.5):
            for dz in (-0.5, 0.0, 0.5):
                pts.append([c[0] + dx * s[0], c[1] + dy * s[1], c[2] + dz * s[2]])
    return pts


# ─────────────────────────────────────────────────────────────── evaluate / outputs

def evaluate(spec: dict, units: list[dict], env: dict, *, interfaces: list[dict] | None = None,
             orbit_alt_km: float | None = None) -> dict[str, Any]:
    real = realise(spec, units, env)
    checks = run_checks(real, units, env, orbit_alt_km)
    real["checks"] = checks
    real["summary"] = rc.summarise(checks)
    real["score"] = score(real, units, env, _pairs(units, interfaces))
    real["cog_design_m"] = to_design_m(real["cog_mm"], env)
    real["assumptions"] = sorted({a for p in real["placements"] for a in p.get("assumptions") or []})
    return real


def design_positions(real: dict, units: list[dict], env: dict) -> dict[str, list[float]]:
    """Mass-weighted centre of each element's placements, design frame (metres)."""
    acc: dict[str, list[float]] = {}
    for p in real["placements"]:
        m = max(p["mass_kg"], 1e-9)
        a = acc.setdefault(p["element_id"], [0.0, 0.0, 0.0, 0.0])
        for k in range(3):
            a[k] += m * p["center_mm"][k]
        a[3] += m
    return {eid: to_design_m([a[0] / a[3], a[1] / a[3], a[2] / a[3]], env) for eid, a in acc.items()}


def _r(v: list[float], d: int = 4) -> list[float]:
    return [round(float(x), d) for x in v]


def to_geometry(real: dict, units: list[dict], env: dict, spacecraft: str = "") -> dict[str, Any]:
    """The layout as ``c2o.geometry/1`` (simulator geometry.yaml schema), in metres.

    Additive extension (optional keys, documented in docs/STACK_BUILDER.md and accepted
    by smo_common.config.geometry): ``frame`` (the convention, as text), ``internal``
    (one box per placement/tile: id, name, subsystem, mount, column, slot, face,
    box_m [cx, cy, cz, dx, dy, dz], mass_kg) and ``mass_properties`` (mass_kg, cog_m).
    """
    sx, sy, sz = env["size_mm"]
    P = real["placements"]
    by = {u["id"]: u for u in units}
    rules = _rules()
    body_area = {f: 0.0 for f in FACES}
    wings: list[dict] = []
    antennas: list[dict] = []
    for p in P:
        if not p.get("tiles"):
            continue
        u = by.get(p["element_id"]) or {}
        if p["role"] == "solar" and p["mount_class"] == "face_panel":
            perf_area = _num((u.get("performance") or {}).get("area_m2")) or _num(
                ((kb_component({"kb_component_id": u.get("kb_id")}) or {}).get("performance") or {}).get("area_m2"))
            per = perf_area if perf_area else 0.85 * p["tiles"][0]["size_mm"][FACE_UV[p["face"]][0]] * \
                p["tiles"][0]["size_mm"][FACE_UV[p["face"]][1]] / 1e6
            body_area[p["face"]] += per * len(p["tiles"])
        dep = p.get("deployable") or {}
        if dep.get("kind") == "wing":
            for ti, t in enumerate(p["tiles"]):
                ui, vi, _ = FACE_UV[p["face"]]
                out_m, along_m = t["size_mm"][ui] / 1000, t["size_mm"][vi] / 1000
                geo_area = out_m * along_m * int(dep.get("panels") or 1)
                perf_area = _num(((kb_component({"kb_component_id": u.get("kb_id")}) or {}).get("performance") or {}).get("area_m2"))
                wings.append({"id": f"wing_{p['face']}" + (f"_{ti}" if ti else ""), "face": p["face"],
                              "mount_axis": list(NORMALS[p["face"]]), "panel_size_m": _r([out_m, along_m], 4),
                              "panels": int(dep.get("panels") or 1),
                              "cell_area_m2": round(min(perf_area or 0.85 * geo_area, geo_area), 4),
                              "deployed_bit": len(wings)})
        if p["role"] in ("antenna_rf", "antenna_gnss"):
            if dep.get("kind") == "antenna":
                for ri, rod in enumerate(dep.get("rods") or []):
                    antennas.append({"id": f"{_slug(p['name'])}_{ri + 1}", "kind": "dipole",
                                     "position_m": _r([x / 1000 for x in rod["start_mm"]]),
                                     "boresight": [float(x) for x in rod["dir"]], "length_m": round(rod["length_mm"] / 1000, 4)})
            else:
                n = NORMALS[p["face"]]
                c = p["center_mm"]
                antennas.append({"id": _slug(p["name"]), "kind": "patch", "position_m": _r([x / 1000 for x in c]),
                                 "boresight": [float(x) for x in n]})
    pl = next((p for p in P if p["role"] == "payload" and p.get("boresight")), None)
    payload = {"boresight": [float(x) for x in (_unit_vec(pl["boresight"]) or [0, 0, -1])],
               "position_m": _r([x / 1000 for x in _aperture(pl, env)]), "fov_deg": float(pl.get("fov_deg") or 10.0)} \
        if pl else {"boresight": [0.0, 0.0, -1.0], "position_m": [0.0, 0.0, round(-sz / 2000, 4)], "fov_deg": 10.0}
    sts = [{"id": f"st{i + 1}", "boresight": [float(x) for x in (_unit_vec(p["boresight"]) or [0, 0, 1])],
            "position_m": _r([x / 1000 for x in _aperture(p, env)]), "fov_deg": float(p.get("fov_deg") or 12.0)}
           for i, p in enumerate(q for q in P if q["role"] == "star_tracker")]
    thr = [{"id": f"thr{i + 1}", "position_m": _r([x / 1000 for x in _aperture(p, env)]),
            "thrust_axis": [-float(x) for x in (_unit_vec(p["boresight"]) or [-1, 0, 0])]}
           for i, p in enumerate(q for q in P if q["role"] == "propulsion")]
    internal = []
    for p in P:
        boxes = [(p["id"], p["center_mm"], p["size_mm"])] if not p.get("tiles") else \
            [(f"{p['id']}#{k + 1}" if len(p["tiles"]) > 1 else p["id"], t["center_mm"], t["size_mm"]) for k, t in enumerate(p["tiles"])]
        for bid, c, s in boxes:
            internal.append({"id": bid, "name": p["name"], "subsystem": p["subsystem"], "mount": p["mount_class"],
                             "column": p.get("column"), "slot": p.get("slot"), "face": p.get("face"),
                             "box_m": _r([c[0] / 1000, c[1] / 1000, c[2] / 1000, s[0] / 1000, s[1] / 1000, s[2] / 1000], 5),
                             "mass_kg": round(p["mass_kg"] / max(1, len(boxes)), 4),
                             **({"distributed": True} if p.get("distributed") else {})})
    st = rules["star_tracker"]
    geo: dict[str, Any] = {
        "schema": "c2o.geometry/1",
        "spacecraft": spacecraft or "SpaceCDF design",
        "quaternion": {"order": "xyzw", "maps": "eci_to_body"},
        "bus": {"size_m": _r([sx / 1000, sy / 1000, sz / 1000], 5)},
        "body_panels": [{"face": f, "normal": list(NORMALS[f]), "cell_area_m2": round(body_area[f], 4)} for f in FACES],
        "wings": wings,
        "payload": payload,
        "star_trackers": sts,
        "star_tracker_sun_exclusion_deg": float(st["sun_exclusion_deg"]),
        "star_tracker_earth_exclusion_deg": float(st["earth_exclusion_deg"]),
        "antennas": antennas,
        "thrusters": thr,
        "frame": {"origin": "envelope centre", "axes": FRAME_NOTE["stack"], "units": "m",
                  "design_frame": FRAME_NOTE["design"], "source": "SpaceCDF stack builder"},
        "internal": internal,
        "mass_properties": {"mass_kg": real["mass_kg"], "cog_m": _r([x / 1000 for x in real["cog_mm"]], 5)},
    }
    if wings:
        f0 = wings[0]["face"]
        axis = list(NORMALS[f0])
        n0 = [1, 0, 0] if f0 in ("py", "my") else [0, 1, 0]
        geo["array_drive"] = {"axis": [abs(x) for x in axis], "normal_at_0deg": n0, "normal_at_90deg": [0, 0, 1],
                              "angle_param": "eps.solar_array_drive_angle"}
    return geo


def _slug(s: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "_" for ch in s).strip("_")
    while "__" in out:
        out = out.replace("__", "_")
    return out or "item"


def applicable(form_factor: str | None) -> bool:
    try:
        cds = rc.load("cds_rules")
    except Exception:  # noqa: BLE001
        return False
    return bool(form_factor) and form_factor in cds["cubesat_form_factors"] and form_factor in cds["envelope_mm"]["values"]


# ─────────────────────────────────────────────────────────────── rule-engine hooks

def _study_of(elements: list[dict]) -> str | None:
    for e in elements:
        if e.get("study_id"):
            return str(e["study_id"])
    return None


def cds_stack_checks(elements: list[dict], form_factor: str | None) -> list[dict]:
    """STACK-* results of the APPROVED layout for the CDS compliance matrix (sync, cached
    layouts only). CoG is left to CDS-COG, which reads the positions the layout wrote."""
    sid = _study_of(elements)
    lay = LAYOUT_CACHE.get(sid or "")
    if not lay or not lay.get("approved") or not applicable(form_factor):
        return []
    try:
        env = envelope(form_factor)
        units = collect_units(elements)
        spec, _ = normalise_spec(lay["approved"]["spec"], units, env)
        real = evaluate(spec, units, env)
    except Exception:  # noqa: BLE001
        logger.warning("stack checks failed for %s", sid, exc_info=True)
        return []
    return [{**c, "group": "stack"} for c in real["checks"] if c["id"] != "STACK-COG"]


def stack_gate_check(elements: list[dict], form_factor: str | None) -> dict[str, Any]:
    """GC-STACK: a stack layout approved by Structures, with no failing STACK-* check."""
    label = {"en": "Stack layout approved by Structures", "fr": "Empilement approuvé par Structures"}
    ref = rc.ref_of(rc.load("stack_rules"), {"source": "design_rules", "clause": "§4 (STACK-*)"})
    if not applicable(form_factor):
        return rc.check_item("GC-STACK", label, "pass", {"en": "Not a CubeSat: no stack to lay out.",
                                                         "fr": "Pas un CubeSat : pas d’empilement."}, ref, applicable=False)
    sid = _study_of(elements)
    lay = LAYOUT_CACHE.get(sid or "") or {}
    if not lay.get("approved"):
        st = "warn" if lay.get("proposal") else "not_evaluated"
        return rc.check_item("GC-STACK", label, st,
                             {"en": "A proposal waits for the Structures seat." if lay.get("proposal") else "No stack layout yet: run auto-placement.",
                              "fr": "Une proposition attend le poste Structures." if lay.get("proposal") else "Pas encore d’empilement : lancer le placement automatique."},
                             ref)
    checks = cds_stack_checks(elements, form_factor)
    s = rc.summarise(checks)
    status = "fail" if s["fail"] else ("warn" if s["warn"] or lay.get("proposal") else "pass")
    return rc.check_item("GC-STACK", label, status,
                         {"en": f"Approved layout: {s['pass']} pass, {s['warn']} caution, {s['fail']} fail"
                                + ("; a newer proposal is open." if lay.get("proposal") else "."),
                          "fr": f"Empilement approuvé : {s['pass']} conformes, {s['warn']} à surveiller, {s['fail']} non conformes"
                                + ("; une proposition plus récente est ouverte." if lay.get("proposal") else ".")},
                         ref, counts=s)
