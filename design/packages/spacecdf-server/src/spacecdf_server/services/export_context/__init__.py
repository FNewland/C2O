"""SpaceCDF — the shared study collector for every document generator (W0.2).

One call gathers the whole study once::

    from spacecdf_server.services.export_context import collect
    sx = await collect(study_id, gate="pdr", lang="en")      # -> StudyExport
    sx.rollup["mass"]["cbe_kg"]; sx.requirements["items"]; sx.risks["items"]
    sx.as_dict()                                              # JSON-ready, every section present

Every generator (docx families, review packs, master budget, licensing documents, ConOps, ...)
codes against ``StudyExport`` instead of reading the server caches itself (EG #10: the four
independent collectors are what made the documents disagree with the workbench).

Sections, in collection order (``SECTIONS``); each lives in its own module
``export_context/sections/<name>.py`` exposing ``async def collect(ctx) -> dict``, so the agent
that owns a section edits only that file (ownership table in design/docs/dev/W0_SEAMS.md):

need, mission, elements, rollup, requirements, verification, risks, trades, decisions, gates,
analyses, modes, data_budget, links, contacts, licensing, ait, schedule, cdr, functions

(``cdr`` and ``functions`` were added by W4.01 for the review packs: the CDR design model and the
function tree.)

Contract for a section collector:

* returns a ``dict`` (JSON-serialisable; lists go under ``"items"``) and never ``None``;
* an empty study gives the empty shape (``{"items": []}``, ``{}``...), not an error;
* a section whose model does not exist yet returns ``{"status": "not_implemented", "owner": ...}``
  plus its empty shape (a *stub*); generators must treat it as "open item", never crash;
* it may read sections collected before it from ``ctx.sections`` and share expensive loads
  through ``ctx.cache``;
* it must not write anything.

A collector that raises does not break the export: the section is set to its ``EMPTY`` shape and
the error is listed in ``StudyExport.errors[section]``.
"""
from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field, fields
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

#: Section names in collection order. Adding a section = add the name here + a module.
SECTIONS: tuple[str, ...] = (
    "need", "mission", "elements", "rollup", "requirements", "verification", "risks", "trades",
    "decisions", "gates", "analyses", "modes", "data_budget", "links", "contacts", "licensing",
    "ait", "schedule", "cdr", "functions",
)

Collector = Callable[["CollectContext"], Awaitable[dict]]


@dataclass
class CollectContext:
    """What a section collector receives."""
    study_id: str
    study: Any                      # spacecdf_common Study (None when only elements exist)
    gate: str | None                # margin-ladder / review gate the document is for (mdr..cdr), or None
    lang: str = "en"
    elements: list[dict] = field(default_factory=list)      # live elements of the study (cache dicts)
    interfaces: list[dict] = field(default_factory=list)    # live, non-rejected interfaces
    sections: dict[str, dict] = field(default_factory=dict)  # sections collected so far
    cache: dict[str, Any] = field(default_factory=dict)      # shared scratch for expensive loads


@dataclass
class StudyExport:
    """The whole study, one attribute per section (all always present)."""
    study_id: str
    study_name: str
    gate: str | None
    lang: str
    need: dict = field(default_factory=dict)
    mission: dict = field(default_factory=dict)
    elements: dict = field(default_factory=dict)
    rollup: dict = field(default_factory=dict)
    requirements: dict = field(default_factory=dict)
    verification: dict = field(default_factory=dict)
    risks: dict = field(default_factory=dict)
    trades: dict = field(default_factory=dict)
    decisions: dict = field(default_factory=dict)
    gates: dict = field(default_factory=dict)
    analyses: dict = field(default_factory=dict)
    modes: dict = field(default_factory=dict)
    data_budget: dict = field(default_factory=dict)
    links: dict = field(default_factory=dict)
    contacts: dict = field(default_factory=dict)
    licensing: dict = field(default_factory=dict)
    ait: dict = field(default_factory=dict)
    schedule: dict = field(default_factory=dict)
    cdr: dict = field(default_factory=dict)
    functions: dict = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    def section(self, name: str) -> dict:
        return getattr(self, name)

    def as_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# keep the dataclass and SECTIONS in step (checked by tests as well)
assert set(SECTIONS) <= {f.name for f in fields(StudyExport)}, "StudyExport lacks a section field"

_REGISTRY: dict[str, Collector] = {}
_EMPTY: dict[str, Callable[[], dict]] = {}


def register(name: str, fn: Collector, empty: Callable[[], dict] | None = None) -> None:
    """Replace the collector of a section (tests, experiments). Modules normally need not call this."""
    if name not in SECTIONS:
        raise KeyError(f"unknown export section {name!r}")
    _REGISTRY[name] = fn
    if empty is not None:
        _EMPTY[name] = empty


def _load(name: str) -> tuple[Collector, Callable[[], dict]]:
    if name not in _REGISTRY:
        mod = importlib.import_module(f"{__name__}.sections.{name}")
        _REGISTRY[name] = mod.collect
        _EMPTY.setdefault(name, getattr(mod, "empty", dict))
    return _REGISTRY[name], _EMPTY.get(name, dict)


def empty_section(name: str) -> dict:
    return _load(name)[1]()


async def build_context(study_id: str, *, gate: str | None = None, lang: str = "en") -> CollectContext:
    from ...routers.elements import _elements, _interfaces
    from ...routers.studies import get_study_store

    study = get_study_store().get(study_id)
    els = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    ids = {e.get("id") for e in els}
    ifs = [i for i in _interfaces.values()
           if not i.get("deleted_at") and i.get("status") != "rejected" and (
               i.get("study_id") == study_id or i.get("source_element_id") in ids
               or i.get("target_element_id") in ids)]
    if gate is None and study is not None:
        try:
            from ...routers.gates import study_margin_gate
            gate = study_margin_gate(study)
        except Exception:  # noqa: BLE001
            gate = None
    return CollectContext(study_id=study_id, study=study, gate=(gate or None), lang=lang or "en",
                          elements=els, interfaces=ifs)


async def collect(study_id: str, *, gate: str | None = None, lang: str = "en",
                  sections: tuple[str, ...] | list[str] | None = None) -> StudyExport:
    """Collect the study. ``sections`` limits the work (the others stay empty); default: all.

    Raises ``LookupError`` when neither the study nor any of its elements exists.
    """
    ctx = await build_context(study_id, gate=gate, lang=lang)
    if ctx.study is None and not ctx.elements:
        raise LookupError(f"Study {study_id} not found")
    wanted = set(SECTIONS if sections is None else sections)
    unknown = wanted - set(SECTIONS)
    if unknown:
        raise KeyError(f"unknown export sections: {sorted(unknown)}")
    out = StudyExport(study_id=study_id, study_name=getattr(ctx.study, "name", "") or study_id,
                      gate=ctx.gate, lang=ctx.lang)
    for name in SECTIONS:
        fn, empty = _load(name)
        if name not in wanted:
            setattr(out, name, empty())
            continue
        try:
            data = await fn(ctx)
            if not isinstance(data, dict):
                raise TypeError(f"section {name} returned {type(data).__name__}, expected dict")
        except Exception as exc:  # noqa: BLE001 — one broken section must not break every document
            logger.warning("export section %s failed for %s", name, study_id, exc_info=True)
            out.errors[name] = f"{type(exc).__name__}: {exc}"
            data = empty()
        ctx.sections[name] = data
        setattr(out, name, data)
    return out


__all__ = ["SECTIONS", "CollectContext", "StudyExport", "build_context", "collect", "empty_section", "register"]
