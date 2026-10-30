"""Study -> textual SysML v2 (KerML/SysML v2 textual notation) via Jinja2.

    text = await export_study_sysml(study_id)

Mapping (template ``study.sysml.j2``)::

    package <Study> {
        part def <ElementType>;                    one per distinct element_type
        part <root> : <ElementType> {              element tree (parent_id)
            attribute mass_kg = 4.5;  // unit: kg  parameters (unit in a comment —
                                                   the SysML v2 unit syntax
                                                   ``[SI::kg]`` needs the
                                                   ISQ library import, so we stay
                                                   library-free)
            part <child> : <ElementType> { ... }
        }
        action def <Function>; action <function> : <Function> { action <child> ... }
        allocate <function> to <element>;         function allocations
        connection <iface> connect <from> to <to>; interfaces
        requirement def <Code>; requirement <code> : <Code> { doc /* text */ subject s : <Element>; }
        satisfy <requirement> by <element>;      satisfies relations
    }

Identifier escaping: names are reduced to ``[A-Za-z0-9_]`` (spaces -> ``_``);
if that is not a valid identifier (empty, starts with a digit, is a keyword)
the original name is emitted as a quoted ``'...'`` unrestricted name.
Duplicates get a numeric suffix so each element has a unique short name in
its package.

``validate_sysml``: uses ``opensysml`` when importable, otherwise a smoke
check (balanced braces / comments, required keywords present).
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..capella._spine import load_snapshot
from ..capella.mapping import SpineSnapshot

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent
WELL_KNOWN_UNITS = {"mass_kg": "kg", "power_avg_w": "W", "power_peak_w": "W", "volume_cm3": "cm3",
                    "cost_nre_keur": "kEUR", "cost_recurring_keur": "kEUR"}
KEYWORDS = {
    "package", "part", "def", "attribute", "action", "allocate", "connection", "connect", "to",
    "requirement", "doc", "subject", "satisfy", "by", "import", "item", "port", "in", "out",
    "inout", "ref", "abstract", "private", "public", "protected", "flow", "state", "constraint",
    "verify", "require", "assume", "then", "if", "else", "true", "false", "null", "comment",
    "about", "library", "standard", "alias", "for", "end", "first", "from", "of", "enum", "occurrence",
}

__all__ = ["export_study_sysml", "render_sysml", "sysml_identifier", "validate_sysml"]


def sysml_identifier(name: str, fallback: str = "x") -> str:
    """Escape a display name into a SysML v2 name (basic or quoted unrestricted)."""
    raw = (name or "").strip()
    basic = re.sub(r"[^A-Za-z0-9_]+", "_", raw).strip("_")
    if basic and not basic[0].isdigit() and basic not in KEYWORDS:
        return basic
    if not raw:
        return fallback
    return "'" + raw.replace("\\", "\\\\").replace("'", "\\'") + "'"


class _Names:
    """Unique identifiers per scope."""
    def __init__(self) -> None:
        self.used: set[str] = set()

    def take(self, name: str, fallback: str) -> str:
        base = sysml_identifier(name, fallback)
        cand, n = base, 1
        while cand in self.used:
            n += 1
            cand = (base[:-1] + f"_{n}'") if base.startswith("'") else f"{base}_{n}"
        self.used.add(cand)
        return cand


def _fmt(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(float(v)) if isinstance(v, float) else str(v)
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _doc(text: str) -> str:
    return (text or "").replace("*/", "* /")


def build_context(snap: SpineSnapshot) -> dict[str, Any]:
    names = _Names()
    elements = [e for e in snap.elements if not e.get("deleted_at")]
    el_by_id = {e["id"]: e for e in elements}
    el_name = {e["id"]: names.take(e.get("name") or e["id"], "element") for e in elements}
    types = sorted({(e.get("element_type") or "component") for e in elements})
    type_name = {t: sysml_identifier(t.title().replace("_", ""), "Component") for t in types}
    params: dict[str, list[dict]] = {}
    seen: set[tuple[str, str]] = set()
    for p in snap.parameters:
        if p.get("value") is None:
            continue
        params.setdefault(p["element_id"], []).append({
            "name": sysml_identifier(p["name"], "value"), "value": _fmt(p["value"]),
            "unit": p.get("unit") or WELL_KNOWN_UNITS.get(p["name"], "")})
        seen.add((p["element_id"], p["name"]))
    for e in elements:  # well-known columns not (yet) mirrored into parameter rows
        for name, unit in WELL_KNOWN_UNITS.items():
            if (e["id"], name) not in seen and e.get(name) is not None:
                params.setdefault(e["id"], []).append({"name": name, "value": _fmt(e[name]), "unit": unit})
    children: dict[str | None, list[dict]] = {}
    for e in elements:
        pid = e.get("parent_id") if e.get("parent_id") in el_by_id else None
        children.setdefault(pid, []).append(e)

    def el_node(e: dict) -> dict:
        return {"name": el_name[e["id"]], "type": type_name[e.get("element_type") or "component"],
                "description": _doc(e.get("description") or ""), "attributes": params.get(e["id"], []),
                "children": [el_node(c) for c in children.get(e["id"], [])]}

    fns = [f for f in snap.functions if not f.get("deleted_at")]
    fn_by_id = {f["id"]: f for f in fns}
    fn_name = {f["id"]: names.take(f.get("name") or f["id"], "function") for f in fns}
    fn_children: dict[str | None, list[dict]] = {}
    for f in fns:
        pid = f.get("parent_id") if f.get("parent_id") in fn_by_id else None
        fn_children.setdefault(pid, []).append(f)

    def fn_node(f: dict) -> dict:
        return {"name": fn_name[f["id"]], "def": "Fn_" + fn_name[f["id"]].strip("'"),
                "layer": f.get("layer") or "SA", "description": _doc(f.get("description") or ""),
                "children": [fn_node(c) for c in fn_children.get(f["id"], [])]}

    allocations = [{"function": fn_name[a["function_id"]], "element": el_name[a["element_id"]], "layer": a.get("layer")}
                   for a in snap.allocations if a.get("function_id") in fn_name and a.get("element_id") in el_name]

    connections = []
    for i in snap.interfaces:
        if i.get("deleted_at") or i.get("from_element_id") not in el_name or i.get("to_element_id") not in el_name:
            continue
        connections.append({"name": names.take(i.get("name") or i["id"], "interface"),
                            "type": i.get("interface_type") or "data", "source": el_name[i["from_element_id"]],
                            "target": el_name[i["to_element_id"]]})

    reqs = [r for r in snap.requirements if r.get("status") != "retired"]
    req_name = {r["id"]: names.take(r.get("code") or r["id"], "requirement") for r in reqs}
    requirements = []
    for r in reqs:
        subject = el_name.get(r.get("element_id") or "")
        requirements.append({"name": req_name[r["id"]], "def": "Req_" + req_name[r["id"]].strip("'"),
                             "text": _doc(r.get("text") or ""), "level": r.get("level") or "",
                             "subject": subject, "subject_type": type_name.get(
                                 (el_by_id.get(r.get("element_id") or "") or {}).get("element_type") or "component"),
                             "parent": req_name.get(r.get("parent_id") or "")})

    satisfies = []
    for rel in snap.relations:
        if rel.get("kind") != "satisfies":
            continue
        req_id = rel["target_id"] if rel.get("target_kind") == "requirement" else (
            rel["source_id"] if rel.get("source_kind") == "requirement" else None)
        other_kind, other_id = ((rel["source_kind"], rel["source_id"]) if rel.get("target_kind") == "requirement"
                                else (rel["target_kind"], rel["target_id"]))
        if req_id not in req_name:
            continue
        by = el_name.get(other_id) if other_kind == "element" else (fn_name.get(other_id) if other_kind == "function" else None)
        if by:
            satisfies.append({"requirement": req_name[req_id], "by": by})

    return {
        "package": sysml_identifier(snap.study_name or snap.study_id, "Study"),
        "study_id": snap.study_id, "study_name": snap.study_name,
        "part_defs": [type_name[t] for t in types],
        "parts": [el_node(e) for e in children.get(None, [])],
        "actions": [fn_node(f) for f in fn_children.get(None, [])],
        "allocations": allocations, "connections": connections,
        "requirements": requirements, "satisfies": satisfies,
    }


def render_sysml(snap: SpineSnapshot) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), undefined=StrictUndefined,
                      trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    return env.get_template("study.sysml.j2").render(**build_context(snap))


async def export_study_sysml(study_id: str) -> str:
    return render_sysml(await load_snapshot(study_id))


def validate_sysml(text: str) -> list[str]:
    """Return a list of problems (empty == OK)."""
    try:
        import opensysml  # type: ignore  # noqa: F401
    except ImportError:
        opensysml = None  # type: ignore
    if opensysml is not None:  # pragma: no cover - optional dependency
        try:
            parse = getattr(opensysml, "parse", None) or getattr(opensysml, "load", None)
            if parse is not None:
                parse(text)
                return []
        except Exception as exc:
            return [f"opensysml: {exc}"]
    problems: list[str] = []
    stripped = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    stripped = re.sub(r"'(?:\\.|[^'\\])*'", "''", stripped)
    stripped = re.sub(r'"(?:\\.|[^"\\])*"', '""', stripped)
    stripped = re.sub(r"//[^\n]*", "", stripped)
    depth = 0
    for ch in stripped:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                problems.append("unbalanced '}'")
                break
    if depth > 0:
        problems.append(f"{depth} unclosed '{{'")
    if "/*" in stripped:
        problems.append("unterminated comment")
    if not re.search(r"^\s*package\s+", stripped, flags=re.M):
        problems.append("missing 'package'")
    return problems
