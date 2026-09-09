"""Equation engine for typed element parameters (SCDF-160 §1.5).

Formulas are evaluated with ``simpleeval`` (MIT) against a per-study
namespace. Inside a formula owned by element *E*:

* ``<param_name>``            bare name → that parameter on *E* itself
* ``el("<name or id>").<p>``  parameter ``p`` of another element of the study
                              (looked up by id first, then by unique name)
* ``children("<p>")``         sum of ``p`` over the direct children of *E*
                              (children without the parameter count as 0)
* ``budget("<budget_type>")`` *E*'s BudgetAllocation value for that type
                              (``None`` when no allocation is set)

Whitelisted functions: sqrt, sin, cos, tan, atan2, exp, log, log10, min,
max, abs, sum, pow. Nothing else — no attribute access on anything but the
``el()`` handle, no comprehensions, no strings beyond the call arguments.

Values seen by a formula are always *effective* values (selected by the
target row's ``value_switch``), so a manual override on an upstream
parameter propagates downstream.

``formula_kind='ref'`` → the result is persisted into ``computed_value``;
``'calc'`` → evaluated on read only (row untouched). Well-known parameters
(``mass_kg`` …) whose effective value differs from the element column are
written back to the column (through the elements cache when loaded, else
straight to the DB) so budgets and agents see the same number — but only
for ``manual`` / ``reference`` switches and ``ref`` formulas; ``calc`` and
plain ``computed`` mirrors leave the column alone.

Nothing in here raises into the API: every problem lands in the
``errors`` list of the affected parameter and in the study-level result.

Public API:
    evaluate_study(study_id) -> dict
    evaluate_element(element_id) -> dict
    recompute_study(study_id) -> dict       evaluate + persist ref values + write-back
    dependency_graph(study_id) -> dict      {nodes, edges, cycles}
    on_change(study_id, changed_element_ids) -> None   non-fatal recompute trigger
    parse_dependencies(formula) -> ParsedFormula        pure helper
"""
from __future__ import annotations

import ast
import logging
import math
from dataclasses import dataclass, field
from typing import Any

from simpleeval import (
    DEFAULT_OPERATORS, AttributeDoesNotExist, FeatureNotAvailable, FunctionNotDefined,
    InvalidExpression, NameNotDefined, SimpleEval,
)
from sqlalchemy import select

from spacecdf_common.models.parameters import WELL_KNOWN_PARAMETERS

from ..db import parameter_repo
from ..db.engine import get_session_factory
from ..db.models import BudgetAllocationRow, DesignElementRow
from .dirty_set import DirtySet

logger = logging.getLogger(__name__)

WHITELISTED_FUNCTIONS: dict[str, Any] = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "atan2": math.atan2, "exp": math.exp, "log": math.log, "log10": math.log10,
    "min": min, "max": max, "abs": abs, "sum": sum, "pow": math.pow,
}
NAMESPACE_FUNCTIONS = ("el", "children", "budget")
_CONSTANTS = {"pi": math.pi, "e": math.e, "True": True, "False": False, "None": None}

#: Dirty set shared with the reactive layer — element ids marked as
#: ``"<element_id>"`` param ids, consumed by ``recompute_study``.
_dirty = DirtySet()

NodeKey = tuple[str, str]  # (element_id, parameter_name)


# ── Formula parsing ─────────────────────────────────────────────────────

@dataclass
class ParsedFormula:
    bare_names: set[str] = field(default_factory=set)          # same-element params
    element_refs: set[tuple[str, str]] = field(default_factory=set)  # (element ref, param)
    children_params: set[str] = field(default_factory=set)
    budget_types: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)


def parse_dependencies(formula: str) -> ParsedFormula:
    """Static scan of a formula: which names / el() / children() / budget() it uses.

    Never raises; syntax and whitelist problems are reported in ``errors``.
    """
    out = ParsedFormula()
    try:
        tree = ast.parse(formula.strip(), mode="eval")
    except SyntaxError as exc:
        out.errors.append(f"syntax error: {exc.msg} (col {exc.offset})")
        return out

    def _str_arg(call: ast.Call) -> str | None:
        if len(call.args) == 1 and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
            return call.args[0].value
        return None

    callee_ids = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                if fn.id == "el":
                    if _str_arg(node) is None:
                        out.errors.append("el() takes exactly one string literal")
                elif fn.id == "children":
                    p = _str_arg(node)
                    if p is None:
                        out.errors.append("children() takes exactly one string literal")
                    else:
                        out.children_params.add(p)
                elif fn.id == "budget":
                    b = _str_arg(node)
                    if b is None:
                        out.errors.append("budget() takes exactly one string literal")
                    else:
                        out.budget_types.add(b)
                elif fn.id not in WHITELISTED_FUNCTIONS:
                    out.errors.append(f"function '{fn.id}' is not allowed")
            else:
                out.errors.append("only plain function calls are allowed")
        elif isinstance(node, ast.Attribute):
            base = node.value
            if (isinstance(base, ast.Call) and isinstance(base.func, ast.Name)
                    and base.func.id == "el" and _str_arg(base) is not None):
                out.element_refs.add((_str_arg(base), node.attr))
            else:
                out.errors.append(f"attribute access '.{node.attr}' only allowed on el(...)")
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if id(node) in callee_ids or node.id in WHITELISTED_FUNCTIONS or node.id in NAMESPACE_FUNCTIONS or node.id in _CONSTANTS:
                continue
            out.bare_names.add(node.id)
        elif isinstance(node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp,
                               ast.GeneratorExp, ast.Subscript, ast.JoinedStr)):
            out.errors.append(f"{type(node).__name__} is not allowed in formulas")
    return out


# ── Study snapshot ──────────────────────────────────────────────────────

@dataclass
class _Snapshot:
    study_id: str
    elements: dict[str, dict]                     # id -> element dict (DB truth)
    by_name: dict[str, list[str]]                 # name -> [ids]
    children: dict[str, list[str]]                # parent id -> [child ids]
    definitions: dict[str, dict]                  # definition id -> dict
    def_by_name: dict[str, dict]                  # name -> definition
    params: dict[NodeKey, dict]                   # (element, name) -> row dict
    budgets: dict[tuple[str, str], float]         # (element, budget_type) -> value


async def _load_snapshot(study_id: str) -> _Snapshot:
    factory = get_session_factory()
    elements: dict[str, dict] = {}
    budgets: dict[tuple[str, str], float] = {}
    async with factory() as session:
        res = await session.execute(
            select(DesignElementRow).where(DesignElementRow.study_id == study_id,
                                           DesignElementRow.deleted_at.is_(None))
        )
        for row in res.scalars():
            elements[row.id] = {c.key: getattr(row, c.key) for c in DesignElementRow.__table__.columns}
        res = await session.execute(
            select(BudgetAllocationRow).where(BudgetAllocationRow.study_id == study_id)
        )
        for b in res.scalars():
            budgets[(b.element_id, b.budget_type)] = b.allocation_value

    by_name: dict[str, list[str]] = {}
    children: dict[str, list[str]] = {}
    for eid, e in elements.items():
        by_name.setdefault(e.get("name") or "", []).append(eid)
        if e.get("parent_id"):
            children.setdefault(e["parent_id"], []).append(eid)

    definitions = await parameter_repo.load_all_parameter_definitions()
    def_by_name = {d["name"]: d for d in definitions.values()}
    params: dict[NodeKey, dict] = {}
    for p in (await parameter_repo.load_all_element_parameters(study_id)).values():
        if p.get("iteration", 1) != 1 or p["element_id"] not in elements:
            continue
        defn = definitions.get(p["definition_id"])
        if not defn:
            continue
        params[(p["element_id"], defn["name"])] = p
    return _Snapshot(study_id, elements, by_name, children, definitions, def_by_name, params, budgets)


def _switch_value(row: dict) -> float | None:
    sw = row.get("value_switch") or "computed"
    if sw == "manual":
        return row.get("manual_value")
    if sw == "reference":
        return row.get("reference_value")
    return row.get("computed_value")


def _has_formula(row: dict | None) -> bool:
    return bool(row and (row.get("formula") or "").strip())


# ── Graph + evaluation ─────────────────────────────────────────────────

class _Graph:
    """Dependency graph over (element_id, param_name) nodes."""

    def __init__(self, snap: _Snapshot):
        self.snap = snap
        self.parsed: dict[NodeKey, ParsedFormula] = {}
        self.deps: dict[NodeKey, set[NodeKey]] = {}
        self.unresolved: dict[NodeKey, list[str]] = {}
        for key, row in snap.params.items():
            if not _has_formula(row):
                continue
            pf = parse_dependencies(row["formula"])
            self.parsed[key] = pf
            deps: set[NodeKey] = set()
            errs: list[str] = list(pf.errors)
            eid = key[0]
            for name in pf.bare_names:
                deps.add((eid, name))
            for ref, pname in pf.element_refs:
                target = self.resolve_element(ref)
                if target is None:
                    errs.append(f"el({ref!r}): unknown or ambiguous element")
                else:
                    deps.add((target, pname))
            for pname in pf.children_params:
                for cid in snap.children.get(eid, []):
                    deps.add((cid, pname))
            self.deps[key] = deps
            if errs:
                self.unresolved[key] = errs

    def resolve_element(self, ref: str) -> str | None:
        if ref in self.snap.elements:
            return ref
        ids = self.snap.by_name.get(ref, [])
        return ids[0] if len(ids) == 1 else None

    def edges(self) -> list[tuple[NodeKey, NodeKey]]:
        return [(src, dst) for dst, srcs in self.deps.items() for src in srcs]

    def order_and_cycles(self) -> tuple[list[NodeKey], list[list[NodeKey]]]:
        """Kahn topological order over formula nodes; leftover nodes are in cycles.
        Cycles are reported as node lists (found by DFS on the leftover subgraph)."""
        formula_nodes = set(self.deps)
        indeg = {n: 0 for n in formula_nodes}
        dependents: dict[NodeKey, set[NodeKey]] = {n: set() for n in formula_nodes}
        for dst, srcs in self.deps.items():
            for src in srcs:
                if src in formula_nodes:
                    indeg[dst] += 1
                    dependents[src].add(dst)
        ready = sorted(n for n, d in indeg.items() if d == 0)
        order: list[NodeKey] = []
        while ready:
            n = ready.pop(0)
            order.append(n)
            for d in sorted(dependents[n]):
                indeg[d] -= 1
                if indeg[d] == 0:
                    ready.append(d)
        leftover = formula_nodes - set(order)
        cycles: list[list[NodeKey]] = []
        seen: set[NodeKey] = set()
        for start in sorted(leftover):
            if start in seen:
                continue
            stack, path, on_path = [(start, iter(sorted(self.deps[start])))], [start], {start}
            while stack:
                node, it = stack[-1]
                nxt = next((x for x in it if x in leftover), None)
                if nxt is None:
                    stack.pop(); path.pop(); on_path.discard(node); seen.add(node)
                    continue
                if nxt in on_path:
                    cycles.append(path[path.index(nxt):] + [nxt])
                    seen.update(path)
                    stack.clear()
                    break
                path.append(nxt); on_path.add(nxt)
                stack.append((nxt, iter(sorted(self.deps[nxt]))))
        return order, cycles


class _ElementHandle:
    """What ``el("...")`` returns inside a formula."""
    __slots__ = ("_ctx", "_eid")

    def __init__(self, ctx: "_Evaluator", eid: str):
        self._ctx = ctx
        self._eid = eid

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._ctx.value_of(self._eid, name, strict=True)


class _Evaluator:
    def __init__(self, graph: _Graph):
        self.graph = graph
        self.snap = graph.snap
        self.values: dict[NodeKey, float | None] = {}
        self.errors: dict[NodeKey, list[str]] = {k: list(v) for k, v in graph.unresolved.items()}
        self.cycles: list[list[NodeKey]] = []
        self.computed_results: dict[NodeKey, float | None] = {}
        # Seed with non-formula effective values
        for key, row in self.snap.params.items():
            if not _has_formula(row):
                self.values[key] = _switch_value(row)

    def value_of(self, eid: str, name: str, *, strict: bool) -> float | None:
        key = (eid, name)
        if key in self.values:
            return self.values[key]
        el = self.snap.elements.get(eid)
        if el is None:
            raise NameNotDefined(name, f"unknown element {eid}")
        if name in WELL_KNOWN_PARAMETERS:
            return el.get(name)  # column fallback (may be None)
        if key in self.errors and key in self.graph.deps:
            raise NameNotDefined(name, f"{name} could not be evaluated on {el.get('name')}")
        if strict:
            raise NameNotDefined(name, f"{el.get('name')} has no parameter '{name}'")
        return None

    def _make_eval(self, eid: str) -> SimpleEval:
        def _names(node: ast.Name):
            if node.id in _CONSTANTS:
                return _CONSTANTS[node.id]
            return self.value_of(eid, node.id, strict=True)

        def _el(ref):
            target = self.graph.resolve_element(str(ref))
            if target is None:
                raise NameNotDefined(str(ref), "unknown or ambiguous element")
            return _ElementHandle(self, target)

        def _children(pname):
            total = 0.0
            for cid in self.snap.children.get(eid, []):
                v = self.value_of(cid, str(pname), strict=False)
                if v is not None:
                    total += float(v)
            return total

        def _budget(btype):
            return self.snap.budgets.get((eid, str(btype)))

        funcs = dict(WHITELISTED_FUNCTIONS)
        funcs.update({"el": _el, "children": _children, "budget": _budget})
        return SimpleEval(operators=dict(DEFAULT_OPERATORS), functions=funcs, names=_names)

    def run(self) -> None:
        order, self.cycles = self.graph.order_and_cycles()
        in_cycle: set[NodeKey] = {n for c in self.cycles for n in c}
        for key in in_cycle:
            self.errors.setdefault(key, []).append(
                "circular dependency: " + " -> ".join(self._label(n) for n in next(c for c in self.cycles if key in c))
            )
            self.values[key] = self._fallback(key)
        for key in order:
            row = self.snap.params[key]
            if key in self.graph.unresolved:
                self.values[key] = self._fallback(key)
                continue
            try:
                ev = self._make_eval(key[0])
                result = ev.eval(row["formula"].strip())
                if isinstance(result, bool) or not isinstance(result, (int, float)):
                    raise InvalidExpression(f"formula must yield a number, got {type(result).__name__}")
                if isinstance(result, float) and (math.isnan(result) or math.isinf(result)):
                    raise InvalidExpression("formula yielded a non-finite number")
                computed = float(result)
            except (NameNotDefined, FunctionNotDefined, AttributeDoesNotExist, FeatureNotAvailable,
                    InvalidExpression) as exc:
                self.errors.setdefault(key, []).append(str(exc))
                computed = None
            except (ZeroDivisionError, ValueError, TypeError, OverflowError) as exc:
                self.errors.setdefault(key, []).append(f"{type(exc).__name__}: {exc}")
                computed = None
            except Exception as exc:  # pragma: no cover - defensive
                self.errors.setdefault(key, []).append(f"{type(exc).__name__}: {exc}")
                computed = None
            self.computed_results[key] = computed
            sw = row.get("value_switch") or "computed"
            self.values[key] = _switch_value(row) if sw != "computed" else (
                computed if computed is not None else self._fallback(key))

    def _fallback(self, key: NodeKey) -> float | None:
        """Value used when a formula cannot be evaluated: switch value, else last persisted."""
        row = self.snap.params[key]
        v = _switch_value(row)
        return v if v is not None else row.get("computed_value")

    def _label(self, key: NodeKey) -> str:
        el = self.snap.elements.get(key[0], {})
        return f"{el.get('name', key[0])}.{key[1]}"


def _evaluate(snap: _Snapshot) -> tuple[_Graph, _Evaluator]:
    graph = _Graph(snap)
    ev = _Evaluator(graph)
    ev.run()
    return graph, ev


# ── Result shaping ──────────────────────────────────────────────────────

def _provenance(row: dict, name: str) -> str:
    sw = row.get("value_switch") or "computed"
    if sw == "manual":
        return "manual"
    if _has_formula(row):
        return "formula"
    if name in WELL_KNOWN_PARAMETERS and sw == "computed":
        return "column"
    return "agent"


def _param_view(snap: _Snapshot, ev: _Evaluator, key: NodeKey) -> dict:
    row = snap.params[key]
    defn = snap.definitions.get(row["definition_id"], {})
    eid, name = key
    computed = ev.computed_results.get(key, row.get("computed_value")) if _has_formula(row) else row.get("computed_value")
    return {
        "id": row["id"],
        "element_id": eid,
        "element_name": snap.elements.get(eid, {}).get("name"),
        "name": name,
        "unit": defn.get("unit", ""),
        "quantity_kind": defn.get("quantity_kind", ""),
        "manual_value": row.get("manual_value"),
        "computed_value": computed,
        "reference_value": row.get("reference_value"),
        "value_switch": row.get("value_switch") or "computed",
        "effective_value": ev.values.get(key),
        "formula": row.get("formula"),
        "formula_kind": row.get("formula_kind"),
        "errors": list(ev.errors.get(key, [])),
        "owner_domain": row.get("owner_domain"),
        "provenance": _provenance(row, name),
        "version": row.get("version"),
        "updated_at": row.get("updated_at"),
    }


def _study_result(snap: _Snapshot, graph: _Graph, ev: _Evaluator) -> dict:
    params = [_param_view(snap, ev, k) for k in sorted(snap.params)]
    errors = [{"element_id": k[0], "name": k[1], "errors": v} for k, v in sorted(ev.errors.items()) if v]
    return {
        "study_id": snap.study_id,
        "parameters": params,
        "errors": errors,
        "cycles": [[{"element_id": e, "name": n} for e, n in c] for c in ev.cycles],
    }


# ── Public API ─────────────────────────────────────────────────────────

async def evaluate_study(study_id: str) -> dict:
    """Evaluate every formula in the study without persisting anything."""
    try:
        snap = await _load_snapshot(study_id)
        graph, ev = _evaluate(snap)
        return _study_result(snap, graph, ev)
    except Exception as exc:
        logger.exception("evaluate_study failed for %s", study_id)
        return {"study_id": study_id, "parameters": [], "cycles": [],
                "errors": [{"element_id": None, "name": None, "errors": [f"engine failure: {exc}"]}]}


async def evaluate_element(element_id: str) -> dict:
    """Study-wide evaluation, filtered to one element's parameters."""
    study_id = await _study_of(element_id)
    if study_id is None:
        return {"element_id": element_id, "parameters": [], "errors": [f"element {element_id} not found"]}
    res = await evaluate_study(study_id)
    return {
        "element_id": element_id,
        "study_id": study_id,
        "parameters": [p for p in res["parameters"] if p["element_id"] == element_id],
        "errors": [e for e in res["errors"] if e.get("element_id") in (element_id, None)],
    }


async def dependency_graph(study_id: str) -> dict:
    """{nodes, edges, cycles} for the study's formula network."""
    try:
        snap = await _load_snapshot(study_id)
        graph = _Graph(snap)
        _, cycles = graph.order_and_cycles()
        involved: set[NodeKey] = set(graph.deps)
        for srcs in graph.deps.values():
            involved.update(srcs)
        nodes = []
        for key in sorted(involved):
            row = snap.params.get(key)
            nodes.append({
                "id": f"{key[0]}:{key[1]}", "element_id": key[0], "name": key[1],
                "element_name": snap.elements.get(key[0], {}).get("name"),
                "has_formula": _has_formula(row), "formula_kind": row.get("formula_kind") if row else None,
                "errors": list(graph.unresolved.get(key, [])),
            })
        edges = [{"from": f"{s[0]}:{s[1]}", "to": f"{d[0]}:{d[1]}"} for s, d in sorted(graph.edges())]
        return {"study_id": study_id, "nodes": nodes, "edges": edges,
                "cycles": [[f"{e}:{n}" for e, n in c] for c in cycles]}
    except Exception as exc:
        logger.exception("dependency_graph failed for %s", study_id)
        return {"study_id": study_id, "nodes": [], "edges": [], "cycles": [], "errors": [str(exc)]}


async def recompute_study(study_id: str) -> dict:
    """Evaluate, persist ``ref`` results into ``computed_value`` and write back
    well-known columns whose effective value moved. Returns the evaluation
    result plus ``persisted`` / ``written_back`` counts."""
    try:
        snap = await _load_snapshot(study_id)
        graph, ev = _evaluate(snap)
        persisted = 0
        for key, computed in ev.computed_results.items():
            row = snap.params[key]
            if row.get("formula_kind") != "ref":
                continue
            if computed is None or row.get("computed_value") == computed:
                continue
            try:
                await parameter_repo.update_element_parameter(row["id"], {"computed_value": computed})
                row["computed_value"] = computed
                persisted += 1
            except Exception:
                logger.exception("persisting computed_value for %s failed", row["id"])
        written = await _write_back_columns(snap, ev)
        result = _study_result(snap, graph, ev)
        result["persisted"] = persisted
        result["written_back"] = written
        return result
    except Exception as exc:
        logger.exception("recompute_study failed for %s", study_id)
        return {"study_id": study_id, "parameters": [], "cycles": [], "persisted": 0, "written_back": 0,
                "errors": [{"element_id": None, "name": None, "errors": [f"engine failure: {exc}"]}]}


async def on_change(study_id: str | None, changed_element_ids: list[str] | set[str] | None = None) -> None:
    """Recompute trigger for element / parameter mutations. Never raises,
    never blocks the caller on failure (all errors are logged)."""
    if not study_id:
        return
    try:
        await _dirty.mark(param_ids=set(changed_element_ids or ()), domains={study_id})
        await _dirty.consume()
        await recompute_study(study_id)
    except Exception:
        logger.exception("equations.on_change failed for %s", study_id)


# ── Write-back to well-known columns ───────────────────────────────────

def _should_write_back(row: dict) -> bool:
    sw = row.get("value_switch") or "computed"
    if sw in ("manual", "reference"):
        return True
    return _has_formula(row) and row.get("formula_kind") == "ref"


async def _write_back_columns(snap: _Snapshot, ev: _Evaluator) -> int:
    per_element: dict[str, dict[str, float]] = {}
    for key, row in snap.params.items():
        eid, name = key
        if name not in WELL_KNOWN_PARAMETERS or not _should_write_back(row):
            continue
        value = ev.values.get(key)
        if value is None:
            continue
        el = snap.elements.get(eid)
        if el is None or el.get(name) == value:
            continue
        per_element.setdefault(eid, {})[name] = float(value)
    written = 0
    for eid, cols in per_element.items():
        try:
            await _apply_element_columns(snap.study_id, eid, cols)
            snap.elements[eid].update(cols)
            written += len(cols)
        except Exception:
            logger.exception("write-back of %s onto element %s failed", list(cols), eid)
    return written


async def _apply_element_columns(study_id: str, element_id: str, cols: dict[str, float]) -> None:
    """Route the write through the elements router cache when it holds the
    element (so agents / budgets / WS clients see it), else straight to DB."""
    from ..db.element_repo import db_update_element
    from ..routers import elements as elements_router

    el = elements_router._elements.get(element_id)
    if el and not el.get("deleted_at"):
        el.update(cols)
        el["version"] = int(el.get("version") or 1) + 1
        await db_update_element(element_id, el)
        try:
            from ..routers.ws import _broadcast_study
            await _broadcast_study(study_id, {"type": "element_updated", "element": el})
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Broadcast failed: %s", exc)
        return
    factory = get_session_factory()
    async with factory() as session:
        row = await session.get(DesignElementRow, element_id)
        if row is None:
            return
        for k, v in cols.items():
            setattr(row, k, v)
        row.version = int(row.version or 1) + 1
        await session.commit()
        full = {c.key: getattr(row, c.key) for c in DesignElementRow.__table__.columns}
    await parameter_repo.mirror_well_known_columns(full)


async def _study_of(element_id: str) -> str | None:
    factory = get_session_factory()
    async with factory() as session:
        row = await session.get(DesignElementRow, element_id)
        return row.study_id if row is not None and row.deleted_at is None else None
