"""ComplianceTracker — evaluates requirements against design state (SCDF-113).

Per SPINE_SPEC §6.5. Auto-evaluates requirements with threshold_param_path
and propagates violations up the hierarchy.

Evaluable requirements have:
  - threshold_param_path (e.g., 'power.battery_capacity_wh')
  - threshold_op (e.g., '>=')
  - threshold_value (e.g., '100')

Narrative requirements (no threshold) carry status from human approval.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ComplianceResult:
    """Result of evaluating one requirement."""
    requirement_id: str
    status: str  # "pass" | "fail" | "untestable"
    margin_pct: float | None = None
    achieved_value: float | None = None
    threshold_value: float | None = None
    evaluated_at: str | None = None


@dataclass
class ComplianceDelta:
    """Changes from a recheck — what shifted since last evaluation.

    ``affected_elements`` / ``affected_functions`` (SCDF-160 §1.4) list the
    design entities linked to the newly violated or cleared requirements by
    ``satisfies`` / ``allocates`` relations (plus ``RequirementRow.element_id``),
    so the UI can flag the component or function that owns the problem.
    """
    newly_violated: list[str] = field(default_factory=list)
    newly_cleared: list[str] = field(default_factory=list)
    now_untestable: list[str] = field(default_factory=list)
    affected_elements: list[str] = field(default_factory=list)
    affected_functions: list[str] = field(default_factory=list)


#: Relation kinds that bind a requirement to the entity that meets it.
LINK_RELATION_KINDS = ("satisfies", "allocates")


class ComplianceTracker:
    """Evaluates requirements against design state and tracks violations."""

    def __init__(self, requirements: list[dict] | None = None,
                 relations: list[dict] | None = None):
        self._requirements = requirements or []
        self._relations = relations or []
        self._last_results: dict[str, ComplianceResult] = {}

    def set_requirements(self, requirements: list[dict]) -> None:
        self._requirements = requirements

    def set_relations(self, relations: list[dict]) -> None:
        """Typed requirement relations (``db/relation_repo`` dicts) used to
        resolve ``affected_elements`` / ``affected_functions`` in the delta."""
        self._relations = relations or []

    async def load_relations(self, study_id: str) -> None:
        """Convenience: pull the study's relations from the DB."""
        from ..db.relation_repo import list_relations_by_study
        self._relations = await list_relations_by_study(study_id)

    def linked_entities(self, req_id: str) -> tuple[list[str], list[str]]:
        """(element ids, function ids) linked to ``req_id`` by satisfies/allocates
        relations in either direction, plus the requirement's own ``element_id``."""
        elements: list[str] = []
        functions: list[str] = []
        req = next((r for r in self._requirements if r.get("id") == req_id), None)
        if req and req.get("element_id"):
            elements.append(req["element_id"])
        for rel in self._relations:
            if rel.get("kind") not in LINK_RELATION_KINDS:
                continue
            if rel.get("source_kind") == "requirement" and rel.get("source_id") == req_id:
                kind, other = rel.get("target_kind"), rel.get("target_id")
            elif rel.get("target_kind") == "requirement" and rel.get("target_id") == req_id:
                kind, other = rel.get("source_kind"), rel.get("source_id")
            else:
                continue
            if kind == "element" and other and other not in elements:
                elements.append(other)
            elif kind == "function" and other and other not in functions:
                functions.append(other)
        return elements, functions

    def evaluate_single(self, req: dict, state: Any) -> ComplianceResult:
        """Evaluate a single requirement against design state."""
        req_id = req.get("id", "")
        param_path = req.get("threshold_param_path")
        op = req.get("threshold_op")
        threshold_raw = req.get("threshold_value")

        if not param_path or not op or threshold_raw is None:
            return ComplianceResult(requirement_id=req_id, status="untestable")

        # Parse threshold
        try:
            threshold = float(json.loads(threshold_raw) if isinstance(threshold_raw, str) else threshold_raw)
        except (ValueError, TypeError, json.JSONDecodeError):
            return ComplianceResult(requirement_id=req_id, status="untestable")

        # Get achieved value from state
        achieved = None
        if hasattr(state, 'get'):
            achieved = state.get(param_path)
        elif isinstance(state, dict):
            achieved = state.get(param_path)

        if achieved is None or not isinstance(achieved, (int, float)):
            return ComplianceResult(requirement_id=req_id, status="untestable",
                                   threshold_value=threshold)

        # Evaluate
        compliant = True
        if op == "<=" and achieved > threshold:
            compliant = False
        elif op == ">=" and achieved < threshold:
            compliant = False
        elif op == "==" and abs(achieved - threshold) > threshold * 0.05:
            compliant = False

        margin_pct = None
        if threshold != 0:
            if op in ("<=",):
                margin_pct = ((threshold - achieved) / abs(threshold)) * 100
            elif op in (">=",):
                margin_pct = ((achieved - threshold) / abs(threshold)) * 100

        return ComplianceResult(
            requirement_id=req_id,
            status="pass" if compliant else "fail",
            margin_pct=round(margin_pct, 1) if margin_pct is not None else None,
            achieved_value=achieved,
            threshold_value=threshold,
        )

    async def recheck(
        self,
        state: Any,
        dirty_param_ids: set[str] | None = None,
    ) -> ComplianceDelta:
        """Re-evaluate requirements whose threshold_param_path is dirty.

        Returns set of newly-violated, newly-cleared, and now-untestable IDs.
        """
        delta = ComplianceDelta()

        for req in self._requirements:
            param_path = req.get("threshold_param_path")
            if dirty_param_ids and param_path and param_path not in dirty_param_ids:
                continue  # Not dirty, skip

            result = self.evaluate_single(req, state)
            prev = self._last_results.get(result.requirement_id)

            if prev:
                if prev.status != "fail" and result.status == "fail":
                    delta.newly_violated.append(result.requirement_id)
                elif prev.status == "fail" and result.status == "pass":
                    delta.newly_cleared.append(result.requirement_id)

            if result.status == "untestable" and (not prev or prev.status != "untestable"):
                delta.now_untestable.append(result.requirement_id)

            self._last_results[result.requirement_id] = result

        for req_id in [*delta.newly_violated, *delta.newly_cleared]:
            els, fns = self.linked_entities(req_id)
            for e in els:
                if e not in delta.affected_elements:
                    delta.affected_elements.append(e)
            for f in fns:
                if f not in delta.affected_functions:
                    delta.affected_functions.append(f)

        return delta

    def violation_chain(self, req_id: str) -> list[str]:
        """Return path from violated req up to mission root."""
        chain = [req_id]
        req_map = {r["id"]: r for r in self._requirements}
        current = req_map.get(req_id)
        while current and current.get("parent_id"):
            chain.append(current["parent_id"])
            current = req_map.get(current["parent_id"])
        return chain

    def get_all_results(self) -> dict[str, ComplianceResult]:
        return dict(self._last_results)

    def get_ancestor_flags(self) -> dict[str, bool]:
        """Return {req_id: True} for ancestors that have violated descendants.

        SCDF-116: Walks parent chains of all violated requirements and flags ancestors.
        """
        req_map = {r["id"]: r for r in self._requirements}
        flags: dict[str, bool] = {}

        for req_id, result in self._last_results.items():
            if result.status == "fail":
                # Walk up the parent chain and flag all ancestors
                current = req_map.get(req_id)
                while current and current.get("parent_id"):
                    flags[current["parent_id"]] = True
                    current = req_map.get(current["parent_id"])

        return flags
