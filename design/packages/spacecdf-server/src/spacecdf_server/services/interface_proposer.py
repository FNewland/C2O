"""Rule-based proposer of the expected interfaces between design elements.

No AI. The rules live in ``configs/interface_rules.yaml`` (the C2O default
interface matrix: ECSS-E-ST-10-24C Annex E natures, CubeSat Design
Specification rev 14.1 safety interfaces, and editable C2O defaults). This
module

* loads and validates that file (:func:`load_rules`, :func:`validate_rules`);
* classifies every element into a role (EPS, OBC, transceiver, …) from its
  KB category, its name and its subsystem domain, and derives facts
  (powered, data, needs a heater, deployable) from the KB entry it was
  picked from (``kb_component_id``);
* computes the desired link set (:func:`plan`), refined by KB data (rail
  from the EPS rails, bus protocol common to both ends, RF band);
* reconciles it with the links that exist (:func:`reconcile`): a rule link
  the user rejected is never proposed again for that pair and type; an
  accepted or user-edited link is never changed; a still-suggested rule link
  is updated when its rule output changes and removed when the rule no longer
  applies. Running it twice changes nothing (idempotent);
* reports unmet needs and conflicts (protocol, voltage or band mismatches,
  through the single compatibility checker in
  ``spacecdf_common.models.cubesat_standards``).

The pure functions here never touch the database; ``routers/interfaces.py``
applies the result.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from spacecdf_common.models.cubesat_standards import (
    NON_DATA_PROTOCOLS,
    check_interface_compatibility,
    component_protocols,
    component_rails_v,
    normalise_protocol,
)
from spacecdf_common.models.interface_types import INTERFACE_TYPE_VALUES, SUBTYPES

from .interface_model import is_active

logger = logging.getLogger(__name__)

LEVELS = ("segment", "subsystem", "component")
#: Workbench level number (uiStore: L0 mission/segments … L3 equipment) → rule level
LEVEL_BY_NUMBER = {0: "segment", 1: "segment", 2: "subsystem", 3: "component"}
ELEMENT_TYPE_LEVEL = {"segment": "segment", "subsystem": "subsystem", "component": "component"}
PAIRINGS = ("provider", "sink", "all", "rf_band")
REFINERS = ("rail_voltage", "battery_bus", "protocol", "payload_protocol", "rf_band", "mount_type")
REQUIRES = ("powered", "data", "needs_heater", "deployable", "space")
SPACECRAFT_CLASSES = ("nano", "micro", "small", "medium", "large", "flagship")


# ═══════════════════════════════════════════════════════════════════════
# Config loading and validation
# ═══════════════════════════════════════════════════════════════════════

class RuleConfigError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def rules_path() -> Path:
    env = os.environ.get("SPACECDF_INTERFACE_RULES")
    if env:
        return Path(env)
    p = Path(__file__).resolve()
    for parent in p.parents:
        cand = parent / "configs" / "interface_rules.yaml"
        if cand.exists():
            return cand
    return Path(__file__).resolve().parents[5] / "configs" / "interface_rules.yaml"


def _is_bilingual(v: Any) -> bool:
    return isinstance(v, dict) and isinstance(v.get("en"), str) and isinstance(v.get("fr"), str) \
        and bool(v["en"].strip()) and bool(v["fr"].strip())


_SELECTOR_KEYS = {"roles", "domains", "segments", "exclude_roles", "exclude_domains", "require",
                  "exclude_when_present", "element_types"}
_RULE_KEYS = {"id", "level", "type", "subtype", "direction", "name", "from", "to", "pairing",
              "fallback_from", "fallback_to", "scope", "when", "properties", "refine", "exchange_items",
              "unmet", "rationale", "standard_ref"}
_ROLE_KEYS = {"label", "kb_categories", "kb_types", "names", "domains", "powered", "data",
              "needs_heater", "adcs_unit", "deployable"}


def _check_selector(where: str, sel: Any, roles: set[str], errors: list[str]) -> None:
    if not isinstance(sel, dict):
        errors.append(f"{where}: selector must be a mapping")
        return
    for k in sel:
        if k not in _SELECTOR_KEYS:
            errors.append(f"{where}: unknown selector key '{k}'")
    for k in ("roles", "exclude_roles"):
        for r in sel.get(k) or []:
            if r not in roles:
                errors.append(f"{where}.{k}: unknown role '{r}'")
    for r in sel.get("require") or []:
        if r not in REQUIRES:
            errors.append(f"{where}.require: unknown fact '{r}' (one of {', '.join(REQUIRES)})")
    ewp = sel.get("exclude_when_present")
    if ewp is not None:
        if not isinstance(ewp, dict) or not ewp.get("present") or not ewp.get("roles"):
            errors.append(f"{where}.exclude_when_present: needs 'present' and 'roles' lists")
        else:
            for r in list(ewp["present"]) + list(ewp["roles"]):
                if r not in roles:
                    errors.append(f"{where}.exclude_when_present: unknown role '{r}'")
    for k in ("roles", "domains", "segments", "exclude_roles", "exclude_domains", "require", "element_types"):
        if k in sel and not isinstance(sel[k], list):
            errors.append(f"{where}.{k}: must be a list")


def validate_rules(doc: Any) -> list[str]:
    """Return every problem found in a parsed ``interface_rules.yaml`` (empty = valid)."""
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["root: must be a mapping"]
    if doc.get("schema_version") != 1:
        errors.append("schema_version: must be 1")
    if not _is_bilingual(doc.get("disclaimer")):
        errors.append("disclaimer: needs non-empty en and fr")
    d = doc.get("defaults") or {}
    if not isinstance(d, dict):
        errors.append("defaults: must be a mapping")
        d = {}
    for k in ("rails_by_class", "battery_bus_by_class", "data_protocol_by_class", "ttc_band_by_class"):
        tbl = d.get(k)
        if not isinstance(tbl, dict) or not tbl:
            errors.append(f"defaults.{k}: must be a non-empty mapping by spacecraft class")
            continue
        for cls in tbl:
            if cls not in SPACECRAFT_CLASSES:
                errors.append(f"defaults.{k}: unknown spacecraft class '{cls}'")
    for k in ("protocol_priority", "payload_protocol_priority"):
        if not isinstance(d.get(k), list) or not d.get(k):
            errors.append(f"defaults.{k}: must be a non-empty list")
    if not isinstance(d.get("rail_preference"), dict) or "default" not in (d.get("rail_preference") or {}):
        errors.append("defaults.rail_preference: must be a mapping with a 'default' list")
    if not isinstance(d.get("cold_case_c"), (int, float)):
        errors.append("defaults.cold_case_c: must be a number")

    roles = doc.get("roles") or {}
    if not isinstance(roles, dict) or not roles:
        errors.append("roles: must be a non-empty mapping")
        roles = {}
    for name, spec in roles.items():
        if not isinstance(spec, dict):
            errors.append(f"roles.{name}: must be a mapping")
            continue
        for k in spec:
            if k not in _ROLE_KEYS:
                errors.append(f"roles.{name}: unknown key '{k}'")
        if not _is_bilingual(spec.get("label")):
            errors.append(f"roles.{name}.label: needs en and fr")
        for pat in spec.get("names") or []:
            try:
                re.compile(pat)
            except re.error as e:
                errors.append(f"roles.{name}.names: bad regex {pat!r}: {e}")
    role_names = set(roles)

    domains = doc.get("domains") or {}
    if not isinstance(domains, dict):
        errors.append("domains: must be a mapping")
        domains = {}

    xitems = doc.get("exchange_items") or {}
    if not isinstance(xitems, dict):
        errors.append("exchange_items: must be a mapping")
        xitems = {}
    from ..db.exchange_item_repo import EXCHANGE_ITEM_KINDS
    for n, spec in xitems.items():
        if not isinstance(spec, dict) or spec.get("kind") not in EXCHANGE_ITEM_KINDS:
            errors.append(f"exchange_items.{n}: kind must be one of {EXCHANGE_ITEM_KINDS}")

    rules = doc.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules: must be a non-empty list")
        rules = []
    seen: set[str] = set()
    for i, r in enumerate(rules):
        where = f"rules[{i}]"
        if not isinstance(r, dict):
            errors.append(f"{where}: must be a mapping")
            continue
        rid = r.get("id")
        if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", rid or ""):
            errors.append(f"{where}.id: must be a lower-case slug")
        elif rid in seen:
            errors.append(f"{where}.id: duplicate '{rid}'")
        else:
            seen.add(rid)
            where = f"rules[{rid}]"
        for k in r:
            if k not in _RULE_KEYS:
                errors.append(f"{where}: unknown key '{k}'")
        if r.get("level") not in LEVELS:
            errors.append(f"{where}.level: must be one of {LEVELS}")
        if r.get("type") not in INTERFACE_TYPE_VALUES:
            errors.append(f"{where}.type: '{r.get('type')}' is not a canonical interface type")
        elif r.get("subtype") is not None and r["subtype"] not in SUBTYPES[r["type"]]:
            errors.append(f"{where}.subtype: '{r['subtype']}' is not a subtype of {r['type']}")
        if r.get("direction", "bidirectional") not in ("bidirectional", "unidirectional"):
            errors.append(f"{where}.direction: bidirectional or unidirectional")
        if r.get("pairing", "provider") not in PAIRINGS:
            errors.append(f"{where}.pairing: one of {PAIRINGS}")
        if r.get("scope", "group") not in ("group", "study"):
            errors.append(f"{where}.scope: group or study")
        for k in ("name", "rationale"):
            if not _is_bilingual(r.get(k)):
                errors.append(f"{where}.{k}: needs non-empty en and fr")
        if not isinstance(r.get("standard_ref"), str) or not r["standard_ref"].strip():
            errors.append(f"{where}.standard_ref: required (say 'C2O default matrix' when it is not a standard)")
        for k in ("from", "to"):
            if k not in r:
                errors.append(f"{where}.{k}: required")
            else:
                _check_selector(f"{where}.{k}", r[k], role_names, errors)
        for k in ("fallback_from", "fallback_to"):
            if k in r:
                _check_selector(f"{where}.{k}", r[k], role_names, errors)
        for ref in r.get("refine") or []:
            if ref not in REFINERS:
                errors.append(f"{where}.refine: unknown refiner '{ref}'")
        for n in r.get("exchange_items") or []:
            if n not in xitems:
                errors.append(f"{where}.exchange_items: '{n}' is not defined under exchange_items")
        if "unmet" in r:
            u = r["unmet"]
            if not isinstance(u, dict) or not isinstance(u.get("need"), str) or not _is_bilingual(u.get("reason")):
                errors.append(f"{where}.unmet: needs 'need' and reason{{en,fr}}")
        if "when" in r and (not isinstance(r["when"], dict) or set(r["when"]) - {"cubesat"}):
            errors.append(f"{where}.when: only 'cubesat' is supported")
        if "properties" in r and not isinstance(r["properties"], dict):
            errors.append(f"{where}.properties: must be a mapping")

    for i, c in enumerate(doc.get("coverage") or []):
        where = f"coverage[{i}]"
        if not isinstance(c, dict) or c.get("type") not in INTERFACE_TYPE_VALUES or not c.get("id"):
            errors.append(f"{where}: needs id and a canonical type")
            continue
        if not _is_bilingual(c.get("label")):
            errors.append(f"{where}.label: needs en and fr")
        _check_selector(f"{where}.applies_to", c.get("applies_to") or {}, role_names, errors)
    return errors


@lru_cache(maxsize=4)
def _load_cached(path: str, mtime: float) -> dict:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    errors = validate_rules(doc)
    if errors:
        raise RuleConfigError(errors)
    # pre-compile name patterns
    for spec in doc["roles"].values():
        spec["_names_re"] = [re.compile(p, re.IGNORECASE) for p in spec.get("names") or []]
    return doc


def load_rules(path: str | Path | None = None) -> dict:
    """Parsed, validated rules (cached until the file changes). Raises :class:`RuleConfigError`."""
    p = Path(path) if path else rules_path()
    try:
        mtime = p.stat().st_mtime
    except OSError as e:
        raise RuleConfigError([f"{p}: {e}"]) from e
    return _load_cached(str(p), mtime)


def rules_status() -> dict[str, Any]:
    """``{ok, path, errors}`` — used at start-up and by the endpoints."""
    p = rules_path()
    try:
        load_rules(p)
        return {"ok": True, "path": str(p), "errors": []}
    except RuleConfigError as e:
        return {"ok": False, "path": str(p), "errors": e.errors}
    except Exception as e:  # noqa: BLE001 — YAML syntax errors etc.
        return {"ok": False, "path": str(p), "errors": [f"{type(e).__name__}: {e}"]}


# ═══════════════════════════════════════════════════════════════════════
# KB join
# ═══════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def _kb_index() -> dict[str, dict]:
    idx: dict[str, dict] = {}
    try:
        from spacecdf_kb.loader import KnowledgeBase
        kb = KnowledgeBase()
        kb.load()
        for cat, items in kb._components.items():  # noqa: SLF001 — read-only index
            for c in items:
                if not isinstance(c, dict):
                    continue
                c = dict(c)
                c.setdefault("_file", cat)
                if c.get("id"):
                    idx.setdefault(str(c["id"]), c)
                if c.get("name"):
                    idx.setdefault(str(c["name"]), c)
    except Exception:  # noqa: BLE001 — proposer still works on names/domains
        logger.exception("KB index unavailable for the interface proposer")
    return idx


def kb_lookup(kb_id: str | None) -> dict | None:
    if not kb_id:
        return None
    return _kb_index().get(str(kb_id))


# ═══════════════════════════════════════════════════════════════════════
# Element context: roles, facts, groups
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Unit:
    el: dict
    kb: dict | None
    role: str | None
    level: str | None              # segment | subsystem | component | None
    group: str                     # spacecraft/system grouping id
    facts: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.el["id"]

    @property
    def name(self) -> str:
        return self.el.get("name") or self.id

    def merged(self) -> dict:
        """KB entry overlaid with the element's own data (for the checkers)."""
        d = dict(self.kb or {})
        d["name"] = self.name
        perf = dict((self.kb or {}).get("performance") or {})
        perf.update(self.el.get("performance") or {})
        d["performance"] = perf
        if self.facts.get("protocols"):
            d["interfaces"] = list(self.facts["protocols"])
        return d


class Context:
    """Everything a rule needs about one study's element tree."""

    def __init__(self, elements: list[dict], config: dict, *, spacecraft_class: str | None = None,
                 study_class: str | None = None):
        self.config = config
        self.defaults = config["defaults"]
        self.els = {e["id"]: e for e in elements if not e.get("deleted_at")}
        self.units: dict[str, Unit] = {}
        for e in self.els.values():
            kb = kb_lookup(e.get("kb_component_id"))
            self.units[e["id"]] = Unit(el=e, kb=kb, role=None,
                                       level=ELEMENT_TYPE_LEVEL.get(e.get("element_type") or ""),
                                       group="")
        for u in self.units.values():
            u.role = self._classify(u)
            u.group = self._group(u)
        self.cubesat = self._detect_cubesat(spacecraft_class)
        self.spacecraft_class = self._resolve_class(spacecraft_class, study_class)
        for u in self.units.values():
            u.facts = self._facts(u)

    # -- tree helpers --------------------------------------------------------
    def ancestors(self, eid: str) -> list[dict]:
        out, seen = [], set()
        cur = self.els.get(eid)
        while cur and cur.get("parent_id") and cur["parent_id"] not in seen:
            seen.add(cur["parent_id"])
            cur = self.els.get(cur["parent_id"])
            if cur:
                out.append(cur)
        return out

    def subtree(self, root_id: str) -> set[str]:
        children: dict[str, list[str]] = {}
        for e in self.els.values():
            if e.get("parent_id"):
                children.setdefault(e["parent_id"], []).append(e["id"])
        out, stack = {root_id}, [root_id]
        while stack:
            for c in children.get(stack.pop(), []):
                if c not in out:
                    out.add(c)
                    stack.append(c)
        return out

    def _group(self, u: Unit) -> str:
        if u.level == "component":
            anc = self.ancestors(u.id)
            for a in anc:
                if a.get("element_type") == "system":
                    return a["id"]
            for a in anc:
                if a.get("element_type") == "segment":
                    return a["id"]
            return anc[-1]["id"] if anc else "study"
        return u.el.get("parent_id") or "study"

    def domain_of(self, u: Unit) -> str | None:
        d = u.el.get("subsystem_domain")
        if d:
            return d
        for a in self.ancestors(u.id):
            if a.get("element_type") == "subsystem" and a.get("subsystem_domain"):
                return a["subsystem_domain"]
        return None

    # -- classification ------------------------------------------------------
    def _classify(self, u: Unit) -> str | None:
        if u.level != "component" or (u.el.get("segment") or "space") != "space":
            return None
        roles = self.config["roles"]
        cat = (u.kb or {}).get("category")
        kb_type = (u.kb or {}).get("type")
        for name, spec in roles.items():           # 1. KB category (+ type)
            cats = spec.get("kb_categories") or []
            if cat and cat in cats:
                types = spec.get("kb_types")
                if types and kb_type not in types:
                    continue
                return name
        text = f"{u.name} {u.el.get('description') or ''}"
        for name, spec in roles.items():           # 2. name pattern
            if any(rx.search(text) for rx in spec.get("_names_re") or []):
                return name
        dom = self.domain_of(u)
        for name, spec in roles.items():           # 3. domain fallback
            if dom and dom in (spec.get("domains") or []):
                return name
        return None

    def _detect_cubesat(self, explicit_class: str | None) -> bool:
        explicit_class = explicit_class or self._recorded_class()
        if explicit_class:
            return explicit_class == "nano"
        for u in self.units.values():
            kb = u.kb or {}
            if kb.get("category") in ("cubesat_structure", "deployer"):
                return True
            if kb.get("form_factor") == "PC/104" or "PC/104" in component_protocols(kb):
                return True
        return False

    def _recorded_class(self) -> str | None:
        """Class populate-subsystems recorded on the spacecraft system element."""
        for e in sorted(self.els.values(), key=lambda x: x["id"]):
            if e.get("element_type") == "system":
                c = (e.get("performance") or {}).get("spacecraft_class")
                if c in SPACECRAFT_CLASSES:
                    return c
        return None

    def _resolve_class(self, explicit: str | None, study_class: str | None) -> str:
        if explicit in SPACECRAFT_CLASSES:
            return explicit  # type: ignore[return-value]
        recorded = self._recorded_class()
        if recorded:
            return recorded
        if self.cubesat:
            return "nano"
        return study_class if study_class in SPACECRAFT_CLASSES else "small"  # type: ignore[return-value]

    def _facts(self, u: Unit) -> dict[str, Any]:
        e, kb = u.el, u.kb or {}
        spec: dict = {}
        if u.level == "component" and u.role:
            spec = self.config["roles"].get(u.role) or {}
        elif u.level == "subsystem":
            spec = (self.config.get("domains") or {}).get(e.get("subsystem_domain") or "", {}) or {}
        protos = component_protocols(kb)
        for p in (e.get("performance") or {}).get("interfaces") or []:
            n = normalise_protocol(p)
            if n and n not in protos:
                protos.append(n)
        watts = (e.get("power_avg_w") or 0) > 0 or (e.get("power_peak_w") or 0) > 0
        powered = spec["powered"] if "powered" in spec else watts
        data = spec["data"] if "data" in spec else bool(set(protos) - NON_DATA_PROTOCOLS)
        temp = kb.get("operating_temp_c") or (kb.get("performance") or {}).get("operating_temp_c") \
            or (e.get("performance") or {}).get("operating_temp_c")
        needs_heater = bool(spec.get("needs_heater"))
        if not needs_heater and isinstance(temp, (list, tuple)) and temp and isinstance(temp[0], (int, float)):
            needs_heater = temp[0] > float(self.defaults["cold_case_c"])
        deployable = bool(spec.get("deployable"))
        if u.role in ("antenna", "solar_array"):
            perf = kb.get("performance") or {}
            how = str(perf.get("deployment") or perf.get("type") or kb.get("type") or "").lower()
            deployable = deployable or "deploy" in how or how in ("tape_spring", "burn_wire", "hinged") \
                or "deploy" in u.name.lower()
        elif "deployable" in u.name.lower():
            deployable = True
        return {
            "powered": bool(powered), "data": bool(data), "needs_heater": needs_heater,
            "deployable": deployable, "space": (e.get("segment") or "space") == "space",
            "protocols": protos, "rails": component_rails_v(kb) if kb else [],
            "adcs_unit": bool(spec.get("adcs_unit")),
        }

    # -- selectors -----------------------------------------------------------
    def matches(self, u: Unit, sel: dict, group_units: list[Unit] | None = None) -> bool:
        e = u.el
        if sel.get("element_types") and e.get("element_type") not in sel["element_types"]:
            return False
        if sel.get("roles") and u.role not in sel["roles"]:
            return False
        dom = e.get("subsystem_domain") if u.level != "component" else self.domain_of(u)
        if sel.get("domains"):
            # domain selectors pick subsystems (or, as fallbacks, the level above components)
            if u.level == "component" or dom not in sel["domains"]:
                return False
        if sel.get("segments"):
            if (e.get("segment") or "space") not in sel["segments"]:
                return False
        if sel.get("exclude_roles") and u.role in sel["exclude_roles"]:
            return False
        if sel.get("exclude_domains") and dom in sel["exclude_domains"]:
            return False
        for req in sel.get("require") or []:
            if not u.facts.get(req):
                return False
        ewp = sel.get("exclude_when_present")
        if ewp and u.role in ewp["roles"] and group_units is not None:
            if any(g.role in ewp["present"] for g in group_units):
                return False
        return True

    def order_key(self, u: Unit, sel: dict) -> tuple:
        roles = sel.get("roles") or []
        doms = sel.get("domains") or []
        r = roles.index(u.role) if u.role in roles else len(roles)
        d = u.el.get("subsystem_domain")
        di = doms.index(d) if d in doms else len(doms)
        return (r, di, u.name.lower(), u.id)


# ═══════════════════════════════════════════════════════════════════════
# Planning
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Desired:
    rule: dict
    from_id: str
    to_id: str
    properties: dict

    @property
    def type(self) -> str:
        return self.rule["type"]

    @property
    def subtype(self) -> str | None:
        return self.rule.get("subtype")

    @property
    def origin(self) -> str:
        return f"rule:{self.rule['id']}"


@dataclass
class Plan:
    desired: list[Desired] = field(default_factory=list)
    unmet: list[dict] = field(default_factory=list)
    levels: tuple[str, ...] = LEVELS
    scope_ids: set[str] | None = None


def _bi(en: str, fr: str) -> dict[str, str]:
    return {"en": en, "fr": fr}


def kb_profile(ctx: Context) -> dict:
    """Defaults the selected KB parts imply (``services/electrical_kb.kb_design_profile``):
    an 8S battery gives a 28 V unregulated bus, CAN parts give CAN, an S-band
    transceiver gives S-band — before the spacecraft-class tables are used."""
    prof = getattr(ctx, "_kb_profile", None)
    if prof is None:
        from .electrical_kb import kb_design_profile
        prof = kb_design_profile(list(ctx.units.values()))
        ctx._kb_profile = prof  # type: ignore[attr-defined]
    return prof


def _class_default(ctx: Context, table: str) -> Any:
    prof = kb_profile(ctx)
    if table in prof:
        return prof[table]
    tbl = ctx.defaults[table]
    return tbl.get(ctx.spacecraft_class, next(iter(tbl.values())))


def _with_unregulated_bus(ctx: Context, rails: list[float]) -> list[float]:
    hv = kb_profile(ctx).get("unregulated_bus_v")
    return rails + [hv] if hv and hv not in rails else rails


def _eps_rails(ctx: Context, provider: Unit) -> list[float]:
    if provider.facts.get("rails") and provider.role == "eps":
        return _with_unregulated_bus(ctx, list(provider.facts["rails"]))
    # a subsystem provider: look for an EPS unit inside it
    for u in ctx.units.values():
        if u.role == "eps" and provider.id in {a["id"] for a in ctx.ancestors(u.id)} and u.facts.get("rails"):
            return _with_unregulated_bus(ctx, list(u.facts["rails"]))
    return _with_unregulated_bus(ctx, [float(v) for v in _class_default(ctx, "rails_by_class")])


def _protocols_of(ctx: Context, u: Unit) -> list[str]:
    if u.level == "component":
        return [p for p in u.facts.get("protocols") or [] if p not in NON_DATA_PROTOCOLS]
    out: list[str] = []
    for c in ctx.units.values():   # a subsystem speaks what its units speak
        if c.level == "component" and u.id in {a["id"] for a in ctx.ancestors(c.id)}:
            for p in c.facts.get("protocols") or []:
                if p not in NON_DATA_PROTOCOLS and p not in out:
                    out.append(p)
    return out


def _band_of(ctx: Context, u: Unit) -> str | None:
    from .equipment_logic import _get_band
    from .electrical_kb import kb_band
    if u.level == "component":
        return kb_band(u.kb) or _get_band(u.merged())
    for c in ctx.units.values():
        if c.role == "transceiver" and u.id in {a["id"] for a in ctx.ancestors(c.id)}:
            b = kb_band(c.kb) or _get_band(c.merged())
            if b:
                return b
    return None


def _refine(ctx: Context, rule: dict, f: Unit, t: Unit) -> dict:
    """Rule default properties refined by KB data. Mismatches are reported by :func:`check_link`."""
    props = dict(rule.get("properties") or {})
    for ref in rule.get("refine") or []:
        if ref == "rail_voltage":
            rails = _eps_rails(ctx, f)
            key = t.role if t.level == "component" else f"domain:{t.el.get('subsystem_domain')}"
            prefs = ctx.defaults["rail_preference"].get(key) or ctx.defaults["rail_preference"]["default"]
            hv = kb_profile(ctx).get("unregulated_bus_v")
            if hv:   # high-voltage battery bus distributed through the PCDU switches (EOSAT-1 style)
                prefs = [hv] + [p for p in prefs if p != hv]
            need = [r for r in (t.facts.get("rails") or []) if t.role not in ("eps", "battery")]
            pool = [r for r in rails if not need or r in need]
            choice = next((p for p in prefs if p in pool), pool[0] if pool else (rails[0] if rails else None))
            if choice is not None:
                props["rail_voltage"] = choice
        elif ref == "battery_bus":
            v = (f.facts.get("rails") or [None])[0] if f.role == "battery" else None
            props["rail_voltage"] = v if v is not None else _class_default(ctx, "battery_bus_by_class")
        elif ref in ("protocol", "payload_protocol"):
            prio = ctx.defaults["payload_protocol_priority" if ref == "payload_protocol" else "protocol_priority"]
            pa, pb = _protocols_of(ctx, f), _protocols_of(ctx, t)
            default = _class_default(ctx, "data_protocol_by_class")
            if pa and pb:
                shared = [p for p in pa if p in pb]
                if shared:
                    props["protocol"] = next((p for p in prio if p in shared), shared[0])
                elif "analog" in pa or "analog" in pb:
                    props["protocol"] = "analog"     # sampled by the master's ADC, no shared bus needed
                else:
                    props["protocol"] = next((p for p in prio if p in pb), pb[0])
            else:
                known = pa or pb
                if known:
                    use_default = ref == "protocol" and default in known
                    props["protocol"] = default if use_default else next((p for p in prio if p in known), known[0])
                else:
                    props["protocol"] = default if ref == "protocol" else prio[0]
        elif ref == "rf_band":
            band = _band_of(ctx, f) or _band_of(ctx, t)
            if not band and rule.get("subtype") == "space_ground":
                band = _class_default(ctx, "ttc_band_by_class")
            if band:
                props["band"] = band
            freq = ((f.merged().get("performance") or {}).get("frequency_mhz")) if f.level == "component" else None
            if freq:
                props["frequency_mhz"] = freq
        elif ref == "mount_type":
            kb = t.kb or {}
            if kb.get("form_factor") == "PC/104" or "PC/104" in (t.facts.get("protocols") or []):
                props["mount_type"] = "PC/104 stack"
            elif t.role in ("antenna", "solar_array", "sun_sensor"):
                props["mount_type"] = "external panel"
            elif t.level == "component":
                props["mount_type"] = "bracket"
    return props


def plan(elements: list[dict], config: dict, *, spacecraft_class: str | None = None,
         study_class: str | None = None, level: int | str | None = None,
         element_id: str | None = None, ctx: Context | None = None) -> tuple[Plan, Context]:
    """Compute the links the rules expect (pure; no I/O apart from the cached KB)."""
    ctx = ctx or Context(elements, config, spacecraft_class=spacecraft_class, study_class=study_class)
    out = Plan()
    if level is not None:
        lv = LEVEL_BY_NUMBER.get(int(level)) if str(level).isdigit() else str(level)
        out.levels = (lv,) if lv in LEVELS else ()
    if element_id:
        out.scope_ids = ctx.subtree(element_id) if element_id in ctx.els else set()

    units = list(ctx.units.values())
    unmet_seen: set[tuple[str, str]] = set()

    def add_unmet(u: Unit, rule: dict) -> None:
        um = rule.get("unmet")
        if not um or (u.id, um["need"]) in unmet_seen:
            return
        if out.scope_ids is not None and u.id not in out.scope_ids:
            return
        unmet_seen.add((u.id, um["need"]))
        out.unmet.append({"element_id": u.id, "need": um["need"], "rule_id": rule["id"],
                          "reason": dict(um["reason"])})

    for rule in config["rules"]:
        rlevel = rule["level"]
        if rlevel not in out.levels:
            continue
        if "when" in rule and bool(rule["when"].get("cubesat")) != ctx.cubesat:
            continue
        level_units = [u for u in units if u.level == rlevel]
        if rule.get("scope", "group") == "study":
            groups = {"study": level_units}
        else:
            groups: dict[str, list[Unit]] = {}
            for u in level_units:
                groups.setdefault(u.group, []).append(u)
        for gid, gunits in groups.items():
            frm = sorted((u for u in gunits if ctx.matches(u, rule["from"], gunits)),
                         key=lambda u: ctx.order_key(u, rule["from"]))
            to = sorted((u for u in gunits if ctx.matches(u, rule["to"], gunits)),
                        key=lambda u: ctx.order_key(u, rule["to"]))
            pairing = rule.get("pairing", "provider")

            def fallback(sel_key: str) -> list[Unit]:
                sel = rule.get(sel_key)
                if not sel:
                    return []
                cands = []
                for u in units:
                    if u.level == rlevel or u.id in {x.id for x in gunits}:
                        continue
                    if rlevel == "component" and u.level != "subsystem":
                        continue
                    if rlevel == "subsystem" and u.el.get("element_type") not in ("system", "segment"):
                        continue
                    if rule.get("scope", "group") == "group" and gid != "study":
                        if rlevel == "component" and gid not in {a["id"] for a in ctx.ancestors(u.id)} | {u.id}:
                            continue
                    if ctx.matches(u, sel):
                        cands.append(u)
                pref = {"system": 0, "segment": 1, "subsystem": 0}
                return sorted(cands, key=lambda u: (pref.get(u.el.get("element_type"), 2), u.name.lower(), u.id))

            pairs: list[tuple[Unit, Unit]] = []
            if pairing == "provider":
                providers = frm or fallback("fallback_from")
                for t in to:
                    p = next((p for p in providers if p.id != t.id), None)
                    if p is None:
                        add_unmet(t, rule)
                    else:
                        pairs.append((p, t))
            elif pairing == "sink":
                sinks = to or fallback("fallback_to")
                for f in frm:
                    s = next((s for s in sinks if s.id != f.id), None)
                    if s is None:
                        add_unmet(f, rule)
                    else:
                        pairs.append((f, s))
            elif pairing == "all":
                pairs = [(f, t) for f in frm for t in to if f.id != t.id]
            elif pairing == "rf_band":
                from .equipment_logic import check_rf_compatibility
                for f in frm:
                    matched = False
                    for t in to:
                        res = check_rf_compatibility(f.merged(), t.merged())
                        if res.get("compatible"):
                            pairs.append((f, t))
                            matched = True
                    if not matched:
                        add_unmet(f, rule)

            for f, t in pairs:
                if out.scope_ids is not None and f.id not in out.scope_ids and t.id not in out.scope_ids:
                    continue
                out.desired.append(Desired(rule=rule, from_id=f.id, to_id=t.id,
                                           properties=_refine(ctx, rule, f, t)))
    return out, ctx


# ═══════════════════════════════════════════════════════════════════════
# Reconciliation with existing links
# ═══════════════════════════════════════════════════════════════════════

def pair_key(a: str, b: str, itype: str) -> tuple:
    return (frozenset((a, b)), itype)


def desired_to_interface(d: Desired, ctx: Context, study_id: str) -> dict:
    """The interface dict a desired link becomes (no id/version — caller assigns)."""
    f, t = ctx.units[d.from_id], ctx.units[d.to_id]
    return {
        "study_id": study_id,
        "name": f"{d.rule['name']['en']}: {f.name} → {t.name}",
        "interface_type": d.type, "type": d.type, "subtype": d.subtype,
        "direction": d.rule.get("direction", "bidirectional"),
        "from_element_id": d.from_id, "to_element_id": d.to_id,
        "properties": dict(d.properties),
        "diagram_label": d.rule["name"]["en"],
        "origin": d.origin, "status": "suggested",
        "rationale": dict(d.rule["rationale"]),
        "standard_ref": d.rule["standard_ref"],
        "criticality": "standard",
    }


_COMPARED = ("name", "direction", "from_element_id", "to_element_id", "properties", "diagram_label",
             "rationale", "standard_ref", "subtype")


@dataclass
class Reconciled:
    create: list[tuple[Desired, dict]] = field(default_factory=list)
    update: list[tuple[dict, dict]] = field(default_factory=list)   # (existing iface, new field values)
    remove: list[dict] = field(default_factory=list)
    unchanged: int = 0
    skipped_rejected: int = 0


def reconcile(p: Plan, ctx: Context, interfaces: list[dict], study_id: str, config: dict) -> Reconciled:
    live = [i for i in interfaces if not i.get("deleted_at") and i.get("study_id") == study_id]
    rejected = {pair_key(i["from_element_id"], i["to_element_id"], i.get("interface_type") or i.get("type"))
                for i in live if i.get("status") == "rejected"}
    active = [i for i in live if is_active(i)]
    by_pair: dict[tuple, list[dict]] = {}
    for i in active:
        by_pair.setdefault(pair_key(i["from_element_id"], i["to_element_id"], i.get("interface_type")), []).append(i)

    res = Reconciled()
    produced: set[tuple] = set()          # (origin, pair_key, subtype) the rules still produce
    seen_desired: set[tuple] = set()
    for d in p.desired:
        k = pair_key(d.from_id, d.to_id, d.type)
        ident = (d.origin, k, d.subtype)
        if ident in seen_desired:
            continue
        seen_desired.add(ident)
        produced.add(ident)
        if k in rejected:
            res.skipped_rejected += 1
            continue
        existing = by_pair.get(k, [])
        own = next((i for i in existing if i.get("origin") == d.origin and i.get("subtype") == d.subtype), None)
        if own is not None:
            if own.get("status") != "suggested":
                res.unchanged += 1           # accepted: kept as the user approved it
                continue
            new = desired_to_interface(d, ctx, study_id)
            changes = {c: new[c] for c in _COMPARED if own.get(c) != new[c]}
            if changes:
                res.update.append((own, changes))
            else:
                res.unchanged += 1
            continue
        satisfied = any(
            i.get("subtype") == d.subtype or not i.get("subtype") or not str(i.get("origin", "")).startswith("rule:")
            for i in existing)
        if satisfied:
            res.unchanged += 1
            continue
        res.create.append((d, desired_to_interface(d, ctx, study_id)))

    # stale suggestions: rule no longer fires (or no longer exists) within the planned scope
    rule_levels = {r["id"]: r["level"] for r in config["rules"]}
    for i in active:
        o = str(i.get("origin") or "")
        if i.get("status") != "suggested" or not o.startswith("rule:"):
            continue
        rid = o[5:]
        if rid in rule_levels and rule_levels[rid] not in p.levels:
            continue
        if p.scope_ids is not None and i["from_element_id"] not in p.scope_ids \
                and i["to_element_id"] not in p.scope_ids:
            continue
        ident = (o, pair_key(i["from_element_id"], i["to_element_id"], i.get("interface_type")), i.get("subtype"))
        if ident not in produced:
            res.remove.append(i)
    return res


# ═══════════════════════════════════════════════════════════════════════
# Conflicts (protocol / voltage / band) on any active link
# ═══════════════════════════════════════════════════════════════════════

def check_link(ctx: Context, iface: dict) -> list[dict]:
    """Bilingual reasons why this link's two ends do not fit together (empty = fine)."""
    f, t = ctx.units.get(iface.get("from_element_id")), ctx.units.get(iface.get("to_element_id"))
    if not f or not t:
        return []
    itype = iface.get("interface_type") or iface.get("type")
    props = iface.get("properties") or {}
    out: list[dict] = []
    if itype == "data":
        pa, pb = _protocols_of(ctx, f), _protocols_of(ctx, t)
        chk = check_interface_compatibility({"name": f.name, "interfaces": pa}, {"name": t.name, "interfaces": pb})
        analog = "analog" in pa or "analog" in pb       # an analog sensor is read through an ADC
        if not chk.compatible and not analog:
            out.append({"kind": "protocol", "reason": _bi(
                f"No shared bus protocol: {f.name} supports {', '.join(pa)}, {t.name} supports {', '.join(pb)}.",
                f"Aucun protocole de bus commun : {f.name} prend en charge {', '.join(pa)}, "
                f"{t.name} prend en charge {', '.join(pb)}.")})
        elif props.get("protocol"):
            proto = normalise_protocol(str(props["protocol"]))
            for u, lst in ((f, pa), (t, pb)):
                if lst and proto not in lst and not (proto == "analog" and analog):
                    out.append({"kind": "protocol", "reason": _bi(
                        f"{u.name} does not support {proto} (it supports {', '.join(lst)}).",
                        f"{u.name} ne prend pas en charge {proto} (il prend en charge {', '.join(lst)}).")})
    elif itype == "power" and (iface.get("subtype") in (None, "regulated", "switched")):
        rail = props.get("rail_voltage", props.get("voltage_v"))
        try:
            rail = float(rail) if rail is not None else None
        except (TypeError, ValueError):
            rail = None
        if rail is not None:
            src_rails = f.facts.get("rails") if f.role == "eps" else None
            if src_rails and rail not in src_rails:
                out.append({"kind": "voltage", "reason": _bi(
                    f"{f.name} has no {rail:g} V rail (it offers {', '.join(f'{v:g}' for v in src_rails)} V).",
                    f"{f.name} n'a pas de rail à {rail:g} V (il fournit {', '.join(f'{v:g}' for v in src_rails)} V).")})
            need = t.facts.get("rails") if t.role not in ("eps", "battery") else None
            if need and rail not in need:
                out.append({"kind": "voltage", "reason": _bi(
                    f"{t.name} needs {', '.join(f'{v:g}' for v in need)} V, the link carries {rail:g} V.",
                    f"{t.name} demande {', '.join(f'{v:g}' for v in need)} V, la liaison porte {rail:g} V.")})
    elif itype == "rf" and f.level == "component" and t.level == "component":
        from .equipment_logic import _get_band, check_rf_compatibility
        res = check_rf_compatibility(f.merged(), t.merged())
        if not res.get("compatible"):
            bf, bt = _get_band(f.merged()), _get_band(t.merged())
            out.append({"kind": "band", "reason": _bi(
                f"{f.name} is {bf}-band but {t.name} is {bt}-band.",
                f"{f.name} est en bande {bf} mais {t.name} est en bande {bt}.")})
    return out


def conflicts_for(ctx: Context, interfaces: list[dict], scope_ids: set[str] | None = None) -> list[dict]:
    out: list[dict] = []
    for i in interfaces:
        if not is_active(i):
            continue
        if scope_ids is not None and i.get("from_element_id") not in scope_ids \
                and i.get("to_element_id") not in scope_ids:
            continue
        for issue in check_link(ctx, i):
            out.append({
                "interface_id": i.get("id"),
                "element_ids": [i.get("from_element_id"), i.get("to_element_id")],
                "kind": issue["kind"],
                "reason": issue["reason"],
                "severity": "caution" if i.get("status") == "suggested" else "alarm",
            })
    return out
