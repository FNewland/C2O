"""One read of the stored model for the diagram builders (no writes, never raises for a
missing optional part: the part comes back empty and the builders report the gap)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

#: element types that are not hardware in the product tree
NON_TREE = {"mode", "logical", "software"}


@dataclass
class DiagramData:
    study_id: str
    study: Any = None
    ctx: Any = None                                       # AnalysisContext
    elements: list[dict] = field(default_factory=list)
    interfaces: list[dict] = field(default_factory=list)  # not rejected
    electrical: dict[str, list[dict]] = field(default_factory=dict)   # rails, lines, buses, nodes, ports (not rejected)
    modes: list[dict] = field(default_factory=list)       # mode elements, ordered
    transitions: list[dict] = field(default_factory=list)
    members: list[dict] = field(default_factory=list)
    functions: list[dict] = field(default_factory=list)
    allocations: list[dict] = field(default_factory=list)
    requirements: list[dict] = field(default_factory=list)
    verification: list[dict] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)
    heaters: list[dict] = field(default_factory=list)
    stack: dict[str, Any] = field(default_factory=dict)  # {applicable, envelope, real, which, form_factor}
    _thermal: Any = None
    _thermal_done: bool = False
    _link: Any = None
    cdr_rows: list[dict] = field(default_factory=list)   # CDR model rows (HK SIDs, stores, framing, pass plan)
    _budget: Any = None
    _budget_done: bool = False
    #: wave 3 (3.X1): the export sections the systems-engineering diagrams read (``b_se.py``):
    #: need, stakeholders, validation, allocations, trades, links, rollup, data_budget
    se: dict[str, dict] = field(default_factory=dict)
    #: functional exchanges resolved to functions: [{id, name, from_fn, to_fn}]
    exchanges: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # ---- lookups
    @property
    def by_id(self) -> dict[str, dict]:
        return {e["id"]: e for e in self.elements}

    def children(self, eid: str | None) -> list[dict]:
        return [e for e in self.elements if e.get("parent_id") == eid and e.get("element_type") not in NON_TREE]

    def domain(self, e: dict) -> str | None:
        """Subsystem domain of an element, inherited from the nearest ancestor that sets one."""
        idx = self.by_id
        cur: dict | None = e
        for _ in range(12):
            if cur is None:
                return None
            if cur.get("subsystem_domain"):
                return cur["subsystem_domain"]
            cur = idx.get(cur.get("parent_id") or "")
        return None

    def subsystem_of(self, e: dict) -> dict | None:
        """The nearest ``subsystem`` ancestor (or the element itself)."""
        idx = self.by_id
        cur: dict | None = e
        for _ in range(12):
            if cur is None:
                return None
            if cur.get("element_type") == "subsystem":
                return cur
            cur = idx.get(cur.get("parent_id") or "")
        return None

    def segment(self, e: dict) -> str:
        from ..rule_inputs import effective_segment
        return effective_segment(e, self.by_id)

    def units(self) -> list[dict]:
        """Space-segment equipment (components) in scope."""
        return [e for e in self.elements if e.get("element_type") in ("component", "equipment")
                and self.segment(e) == "space" and e.get("in_scope", True) is not False]

    def thermal(self) -> Any:
        if not self._thermal_done:
            self._thermal_done = True
            try:
                from ..physics_closure import run_thermal_closure
                if self.ctx is not None and self.ctx.elements:
                    self._thermal = run_thermal_closure(self.ctx)
            except Exception as exc:  # noqa: BLE001
                logger.info("thermal closure for diagrams failed: %s", exc)
                self.warnings.append(f"thermal closure: {exc}")
        return self._thermal

    def data_budget(self) -> dict | None:
        """The study's daily data budget (services/data_budget, W3.05), computed once on first use."""
        if not self._budget_done:
            self._budget_done = True
            try:
                from ..data_budget import from_context
                if self.ctx is not None:
                    self._budget = from_context(self.ctx, self.cdr_rows, include_degraded=False, study_id=self.study_id)
            except Exception as exc:  # noqa: BLE001
                logger.info("data budget for diagrams failed: %s", exc)
                self.warnings.append(f"data budget: {exc}")
        return self._budget

    def link(self) -> tuple[Any, list[dict], list[str]]:
        """(link inputs, station rows, warnings) as the data chain sees them."""
        if self._link is None:
            warnings: list[str] = []
            link, stations = None, []
            try:
                from .. import ground_closure as gc
                if self.ctx is not None:
                    link = gc._link_inputs(self.ctx, warnings)
                    stations = [dict(s, _default=not self.ctx.ground_stations) for s in gc._pick_stations(self.ctx, warnings)]
            except Exception as exc:  # noqa: BLE001
                warnings.append(str(exc))
            self._link = (link, stations, warnings)
        return self._link


async def load(study_id: str) -> DiagramData:
    from ...routers.studies import get_study_store
    d = DiagramData(study_id=study_id, study=get_study_store().get(study_id))
    try:
        from ..analysis_context import build_context
        d.ctx = await build_context(study_id)
        d.elements = [e for e in d.ctx.elements if not e.get("deleted_at")]
        d.interfaces = [i for i in d.ctx.interfaces if not i.get("deleted_at") and i.get("status") != "rejected"]
        d.functions = [f for f in d.ctx.functions if not f.get("deleted_at")]
        d.allocations = list(d.ctx.allocations)
        d.requirements = [r for r in d.ctx.requirements if r.get("status") != "retired"]
    except Exception as exc:  # noqa: BLE001
        logger.warning("diagram context failed for %s: %s", study_id, exc)
        d.warnings.append(f"context: {exc}")
        from ...routers import elements as el
        d.elements = [e for e in el._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
        d.interfaces = [i for i in el._interfaces.values() if i.get("study_id") == study_id
                        and not i.get("deleted_at") and i.get("status") != "rejected"]
    try:
        from ...db import electrical_repo
        rows = await electrical_repo.load_all(study_id)
        d.electrical = {k: [r for r in v if r.get("status") != "rejected"] for k, v in rows.items()}
    except Exception as exc:  # noqa: BLE001
        d.warnings.append(f"electrical: {exc}")
        d.electrical = {"rails": [], "lines": [], "buses": [], "nodes": [], "ports": []}
    try:
        from ...db import mode_repo
        ms = [e for e in d.elements if e.get("element_type") == "mode"]

        def order(m: dict) -> tuple:
            o = (m.get("performance") or {}).get("order")
            return (float(o) if isinstance(o, (int, float)) else 999.0, m.get("name") or "")
        d.modes = sorted(ms, key=order)
        d.transitions = await mode_repo.list_transitions(study_id)
        d.members = await mode_repo.list_members([m["id"] for m in d.modes])
        d.heaters = await mode_repo.list_heaters(study_id)
    except Exception as exc:  # noqa: BLE001
        d.warnings.append(f"modes: {exc}")
    try:
        from ...db import verification_repo
        d.verification = [v for v in await verification_repo.list_by_study(study_id) if not v.get("deleted_at")]
    except Exception as exc:  # noqa: BLE001
        d.warnings.append(f"verification: {exc}")
    try:
        from ...db import cdr_repo
        d.cdr_rows = await cdr_repo.list_rows(study_id)
    except Exception as exc:  # noqa: BLE001
        d.warnings.append(f"cdr: {exc}")
    d.risks = list(getattr(d.study, "risk_register", None) or []) if d.study is not None else []
    d.stack = await _stack(study_id)
    d.exchanges = await _exchanges(study_id, d)
    d.se = await _se_sections(study_id, d)
    return d


#: export sections read by the systems-engineering diagrams (b_se.py); collected once per load
SE_SECTIONS = ("need", "rollup", "data_budget", "links", "trades", "stakeholders", "validation", "allocations")


async def _se_sections(study_id: str, d: DiagramData) -> dict[str, dict]:
    """The export sections the SE diagrams read (the same data the review packs print)."""
    try:
        from ..export_context import collect
        sx = await collect(study_id, sections=SE_SECTIONS)
        return {k: sx.section(k) or {} for k in SE_SECTIONS}
    except Exception as exc:  # noqa: BLE001 — the other diagrams still draw
        logger.info("SE sections for diagrams failed: %s", exc)
        d.warnings.append(f"se sections: {exc}")
        return {}


async def _exchanges(study_id: str, d: DiagramData) -> list[dict]:
    """Functional exchanges with the function at each end (port -> function)."""
    try:
        from ...db import function_repo as fr
        if not d.functions:
            return []
        ports = await fr.load_all_function_ports(study_id)
        fns = {f["id"] for f in d.functions}
        out = []
        for x in await fr.list_functional_exchanges_by_study(study_id):
            if x.get("deleted_at"):
                continue
            a = (ports.get(x.get("from_port_id")) or {}).get("function_id")
            b = (ports.get(x.get("to_port_id")) or {}).get("function_id")
            if a in fns and b in fns:
                out.append({"id": x["id"], "name": x.get("name") or "", "from_fn": a, "to_fn": b})
        return out
    except Exception as exc:  # noqa: BLE001
        d.warnings.append(f"functional exchanges: {exc}")
        return []


async def _stack(study_id: str) -> dict[str, Any]:
    try:
        from ...routers import stack as st
        from .. import stack_builder as sb
        ctx = await st._context(study_id, None)
        ff = ctx["ff"]
        if not sb.applicable(ff):
            return {"applicable": False, "form_factor": ff}
        lay = ctx["layout"]
        which = "approved" if lay.get("approved") else ("proposal" if lay.get("proposal") else None)
        env = sb.envelope(ff)
        if which is None:
            return {"applicable": True, "form_factor": ff, "envelope": env, "real": None, "which": None}
        units = sb.collect_units(ctx["elements"])
        real = st._evaluate(lay.get(which), units, env, ctx)
        return {"applicable": True, "form_factor": ff, "envelope": env, "real": real, "which": which}
    except Exception as exc:  # noqa: BLE001
        logger.info("stack for diagrams failed: %s", exc)
        return {"applicable": False, "error": str(exc)}
