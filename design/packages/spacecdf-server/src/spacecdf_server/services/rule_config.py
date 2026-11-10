"""SpaceCDF — loader and schema check for the deterministic rule configs.

The design rules that replace AI live in YAML under ``design/configs`` so that an
instructor can change a default without touching code:

* ``margin_policy.yaml``     — ESA margin philosophy numbers (services/margin_policy.py)
* ``cds_rules.yaml``         — CubeSat Design Specification checks (services/cds_checks.py)
* ``requirement_rules.yaml`` — EARS / INCOSE checks and verification defaults
* ``failure_modes.yaml``     — FMECA skeleton library (services/fmeca_library.py)

Every file has a ``sources:`` block. Each rule value names one source id; a source
of ``kind: c2o_default`` is a SpaceCDF choice and is shown as "C2O default", never
as a standard citation (``standard_ref`` below does that formatting).

``validate_all()`` is called from the app start-up: errors are logged and kept so the
rule endpoints can report them (``config_errors()``) instead of silently using a
broken file. Set ``SPACECDF_RULES_DIR`` to point at another configs directory.
"""
from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

RULE_FILES: tuple[str, ...] = (
    "margin_policy", "cds_rules", "requirement_rules", "failure_modes",
)
SOURCE_KINDS = frozenset({"standard", "guideline", "c2o_default"})

_errors: dict[str, list[str]] = {}

try:  # libyaml when available (same data, several times faster)
    _YAML_LOADER: Any = yaml.CSafeLoader
except AttributeError:  # pragma: no cover
    _YAML_LOADER = yaml.SafeLoader


class RuleConfigError(ValueError):
    """A rule config file is missing or does not match its schema."""


def configs_dir() -> Path:
    env = os.environ.get("SPACECDF_RULES_DIR")
    if env:
        return Path(env)
    return _find_configs_dir()


@lru_cache(maxsize=1)
def _find_configs_dir() -> Path:
    """The repository's ``configs/`` (found once: the walk up the tree ran on every rule lookup)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "configs" / "margin_policy.yaml"
        if candidate.is_file():
            return candidate.parent
    raise RuleConfigError("configs/margin_policy.yaml not found above " + str(here))


@lru_cache(maxsize=64)
def _raw_at(path: str, _stamp: tuple[int, int]) -> dict[str, Any]:
    p = Path(path)
    try:
        data = yaml.load(p.read_text(encoding="utf-8"), Loader=_YAML_LOADER) or {}  # noqa: S506 — safe loader
    except yaml.YAMLError as exc:
        raise RuleConfigError(f"{p.name}: YAML error: {exc}") from exc
    if not isinstance(data, dict):
        raise RuleConfigError(f"{p.name}: top level must be a mapping")
    return data


def _raw(name: str) -> dict[str, Any]:
    """The parsed file, kept until its modification time or size changes (an instructor's edit
    is picked up on the next call without ``reload()``)."""
    path = configs_dir() / f"{name}.yaml"
    if not path.is_file():
        raise RuleConfigError(f"{path} not found")
    st = path.stat()
    return _raw_at(str(path), (st.st_mtime_ns, st.st_size))


#: name -> (the parsed object that was validated, its errors): validation runs once per parse
_validated: dict[str, tuple[dict[str, Any], list[str]]] = {}


def load(name: str) -> dict[str, Any]:
    """The validated config ``name`` (without .yaml). Raises RuleConfigError."""
    data = _raw(name)
    hit = _validated.get(name)
    if hit is None or hit[0] is not data:
        hit = (data, validate(name, data))
        _validated[name] = hit
    errs = hit[1]
    if errs:
        raise RuleConfigError(f"{name}.yaml: " + "; ".join(errs))
    return data


def reload() -> None:
    """Drop the cache (tests, or after an instructor edits a file)."""
    _raw_at.cache_clear()
    _validated.clear()
    _errors.clear()


# --------------------------------------------------------------------------- sources

def source(cfg: dict[str, Any], source_id: str | None) -> dict[str, Any]:
    src = (cfg.get("sources") or {}).get(source_id or "", {})
    kind = src.get("kind", "c2o_default")
    return {"id": source_id or "c2o_default", "kind": kind, "title": src.get("title", ""),
            "short": src.get("short") or src.get("title", "") or (source_id or ""),
            "url": src.get("url"), "verified": bool(src.get("verified", False)),
            "c2o_default": kind == "c2o_default"}


def standard_ref(cfg: dict[str, Any], source_id: str | None, clause: str | None = None) -> str:
    """Human string for the UI: a cited document + clause, or "C2O default"."""
    s = source(cfg, source_id)
    if s["c2o_default"]:
        return "C2O default" + (f" ({clause})" if clause else "")
    title = s["short"]
    return f"{title} {clause}".strip() if clause else title


def ref_of(cfg: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    """{source, standard_ref, c2o_default} for a rule node with source/clause keys."""
    sid = node.get("source")
    s = source(cfg, sid)
    return {"source": s, "standard_ref": standard_ref(cfg, sid, node.get("clause")),
            "c2o_default": s["c2o_default"]}


# --------------------------------------------------------------------------- validation

def _req(d: Any, key: str, typ: type | tuple[type, ...], where: str, errs: list[str]) -> Any:
    if not isinstance(d, dict) or key not in d:
        errs.append(f"{where}: missing '{key}'")
        return None
    v = d[key]
    if not isinstance(v, typ):
        errs.append(f"{where}.{key}: expected {getattr(typ, '__name__', typ)}, got {type(v).__name__}")
        return None
    return v


def _check_sources(data: dict, errs: list[str]) -> set[str]:
    srcs = _req(data, "sources", dict, "sources", errs) or {}
    for sid, s in srcs.items():
        if not isinstance(s, dict) or s.get("kind") not in SOURCE_KINDS:
            errs.append(f"sources.{sid}: kind must be one of {sorted(SOURCE_KINDS)}")
    return set(srcs)


def _walk_sources(node: Any, known: set[str], path: str, errs: list[str]) -> None:
    """Every ``source:`` value anywhere in the file must be a declared source id."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "source" and isinstance(v, str) and v not in known:
                errs.append(f"{path}: unknown source '{v}'")
            elif k != "sources":
                _walk_sources(v, known, f"{path}.{k}" if path else str(k), errs)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_sources(v, known, f"{path}[{i}]", errs)


def _bilingual(v: Any, where: str, errs: list[str]) -> None:
    if not (isinstance(v, dict) and isinstance(v.get("en"), str) and isinstance(v.get("fr"), str)
            and v["en"].strip() and v["fr"].strip()):
        errs.append(f"{where}: needs non-empty 'en' and 'fr' strings")


def _num_value(d: Any, where: str, errs: list[str]) -> None:
    if not isinstance(d, dict) or not isinstance(d.get("value"), (int, float, bool)) or "source" not in d:
        errs.append(f"{where}: expected {{value: number, source: id}}")


def validate(name: str, data: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    known = _check_sources(data, errs)
    _walk_sources(data, known, "", errs)

    if name == "margin_policy":
        mm = _req(data, "maturity_margins", dict, "maturity_margins", errs) or {}
        cats = _req(mm, "categories", dict, "maturity_margins", errs) or {}
        for c in ("A", "B", "C", "D"):
            if not isinstance((cats.get(c) or {}).get("percent"), (int, float)):
                errs.append(f"maturity_margins.categories.{c}.percent: number required")
            else:
                _bilingual(cats[c].get("label"), f"maturity_margins.categories.{c}.label", errs)
        rules = (_req(data, "category_from_trl", dict, "category_from_trl", errs) or {}).get("rules") or []
        if not rules or any(r.get("category") not in cats for r in rules if isinstance(r, dict)):
            errs.append("category_from_trl.rules: list of {min_trl, category in A-D}")
        for sect, keys in (("mass", ("system_margin_percent", "harness_percent", "propellant_residual_percent",
                                     "tank_volume_margin_percent")),
                           ("power", ("system_margin_percent",)),
                           ("delta_v", ("calculated_manoeuvre_percent", "orbit_maintenance_percent",
                                        "attitude_control_percent")),
                           ("data_handling", ("ram_max_used_percent", "cpu_max_peak_percent")),
                           ("thermal", ("heat_rejection_margin_percent",))):
            s = _req(data, sect, dict, sect, errs) or {}
            for k in keys:
                _num_value(s.get(k), f"{sect}.{k}", errs)
        lad = _req(data, "system_margin_ladder", dict, "system_margin_ladder", errs) or {}
        _bilingual(lad.get("label"), "system_margin_ladder.label", errs)
        _bilingual((lad.get("convention") or {}).get("text"), "system_margin_ladder.convention.text", errs)
        by_gate = lad.get("by_gate") or {}
        for g in ("mdr", "prr", "srr", "pdr", "cdr"):
            _num_value(by_gate.get(g), f"system_margin_ladder.by_gate.{g}", errs)

    elif name == "cds_rules":
        for k in ("max_mass_kg", "cog_limits_cm", "envelope_mm"):
            node = _req(data, k, dict, k, errs) or {}
            vals = _req(node, "values", dict, k, errs) or {}
            for ff, v in vals.items():
                ok = isinstance(v, (int, float)) if k == "max_mass_kg" else (
                    isinstance(v, list) and len(v) == 3 and all(isinstance(x, (int, float)) for x in v))
                if not ok:
                    errs.append(f"{k}.values.{ff}: bad value {v!r}")
        for sect in ("mechanical", "safety", "materials"):
            for k, v in (_req(data, sect, dict, sect, errs) or {}).items():
                _num_value(v, f"{sect}.{k}", errs)
        recog = _req(data, "recognition", dict, "recognition", errs) or {}
        for kind in ("rf_inhibit", "deployable_inhibit", "propulsion_inhibit", "deployment_switch", "rbf"):
            spec = (recog.get("links") or {}).get(kind)
            if not (isinstance(spec, dict) and isinstance(spec.get("subtypes"), list)):
                errs.append(f"recognition.links.{kind}: {{subtypes: [...], target?}} required")

    elif name == "requirement_rules":
        ears = _req(data, "ears", dict, "ears", errs) or {}
        for i, p in enumerate(ears.get("patterns") or []):
            for lang in ("en", "fr"):
                try:
                    re.compile(p.get(lang, ""), re.I)
                except re.error as exc:
                    errs.append(f"ears.patterns[{i}].{lang}: bad regex: {exc}")
            _bilingual(p.get("label"), f"ears.patterns[{i}].label", errs)
        kinds = {"words", "regex", "no_modal", "multi_modal", "number_without_unit", "number_without_bound"}
        ids: set[str] = set()
        for i, c in enumerate(_req(data, "checks", list, "checks", errs) or []):
            where = f"checks[{i}]"
            if c.get("id") in ids:
                errs.append(f"{where}: duplicate id {c.get('id')}")
            ids.add(c.get("id"))
            if c.get("kind") not in kinds:
                errs.append(f"{where}: kind must be one of {sorted(kinds)}")
            if c.get("severity") not in ("error", "warning", "info"):
                errs.append(f"{where}: severity must be error|warning|info")
            _bilingual(c.get("message"), f"{where}.message", errs)
            for key in ("pattern", "pattern_en", "pattern_fr"):
                if key in c:
                    try:
                        re.compile(c[key])
                    except re.error as exc:
                        errs.append(f"{where}.{key}: bad regex: {exc}")
            if c.get("kind") == "words" and not isinstance(c.get("words"), dict):
                errs.append(f"{where}.words: mapping en/fr -> list required")
        ver = _req(data, "verification", dict, "verification", errs) or {}
        methods = ver.get("methods") or {}
        for t in ver.get("types") or []:
            if t.get("method") not in methods:
                errs.append(f"verification.types.{t.get('id')}: method must be one of {sorted(methods)}")

    elif name == "failure_modes":
        types = _req(data, "types", dict, "types", errs) or {}
        for tid, t in {**types, "generic": data.get("generic") or {}}.items():
            for i, m in enumerate((t or {}).get("modes") or []):
                where = f"{tid}.modes[{i}]"
                for k in ("s", "o", "d"):
                    if not (isinstance(m.get(k), int) and 1 <= m[k] <= 5):
                        errs.append(f"{where}.{k}: integer 1..5 required")
                for k in ("mode", "cause", "local", "system", "mitigation"):
                    _bilingual(m.get(k), f"{where}.{k}", errs)
    return errs


def validate_all() -> dict[str, list[str]]:
    """Validate every rule file; log and remember the errors. Called at start-up."""
    _errors.clear()
    for name in RULE_FILES:
        try:
            errs = validate(name, _raw(name))
        except RuleConfigError as exc:
            errs = [str(exc)]
        if errs:
            _errors[name] = errs
            logger.error("Rule config %s.yaml is invalid: %s", name, "; ".join(errs))
    if not _errors:
        logger.info("Rule configs valid: %s", ", ".join(RULE_FILES))
    return dict(_errors)


def config_errors() -> dict[str, list[str]]:
    return dict(_errors)


# --------------------------------------------------------------------------- check items

#: status -> display severity (the mission-control alarm vocabulary)
_SEVERITY = {"pass": "nominal", "warn": "caution", "fail": "alarm", "not_evaluated": "info"}


def check_item(cid: str, label: dict[str, str], status: str, detail: dict[str, str],
               ref: dict[str, Any], *, severity: str | None = None, **values: Any) -> dict[str, Any]:
    """One rule result, the shape every deterministic engine returns.

    ``status``: pass | warn | fail | not_evaluated. ``ref`` comes from ``ref_of``.
    Extra keyword values (value, limit, unit, counts...) are passed through.
    """
    if status not in _SEVERITY:
        raise ValueError(f"bad status {status}")
    return {"id": cid, "label": label, "status": status,
            "severity": severity or _SEVERITY[status], "detail": detail,
            "standard_ref": ref["standard_ref"], "c2o_default": ref["c2o_default"],
            "source": ref["source"], **values}


def summarise(checks: list[dict[str, Any]]) -> dict[str, int]:
    out = {"total": len(checks), "pass": 0, "warn": 0, "fail": 0, "not_evaluated": 0}
    for c in checks:
        out[c["status"]] = out.get(c["status"], 0) + 1
    return out


def fmt(v: float | None, d: int = 1) -> str:
    """Number for messages; French decimal comma is applied by ``fmt_fr``."""
    return "–" if v is None else f"{v:.{d}f}"


def fmt_fr(v: float | None, d: int = 1) -> str:
    return fmt(v, d).replace(".", ",")
