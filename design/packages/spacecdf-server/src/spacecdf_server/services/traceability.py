"""SpaceCDF — Full Traceability Chain (SCDF-145: canonical traceability service).

When a budget is at risk, traces ALL the way up:
  Budget exceedance → System requirement → Function → Objective → Stakeholder need

And back down with recovery options:
  "To recover pointing margin: (a) better star tracker, (b) stiffer structure,
   (c) relax GSD requirement (needs stakeholder approval)"

For component-level spec analysis (fit/gap), see fit_gap_analysis.py which
provides component-to-requirement matching. Both services complement each other:
  - traceability.py: budget → requirement → need chain (this file)
  - fit_gap_analysis.py: component specs vs requirement thresholds

This is the bidirectional V-model traceability that makes the tool useful
for understanding WHY a problem matters and WHAT to do about it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceLink:
    """A single link in the traceability chain."""
    level: str          # budget / requirement / function / objective / stakeholder_need
    id: str
    text: str
    status: str = ""    # green / amber / red / at_risk


@dataclass
class RecoveryOption:
    """A way to recover from a budget or requirement exceedance."""
    description: str
    subsystem: str
    impact: str          # What it costs (mass, money, schedule)
    feasibility: str     # easy / moderate / hard / requires_stakeholder_approval
    trade_off: str       # What you give up


@dataclass
class TraceabilityReport:
    """Full traceability chain from a budget problem to stakeholder impact."""
    trigger: str          # What triggered this trace (e.g. "mass margin < 0%")
    chain: list[TraceLink] = field(default_factory=list)
    recovery_options: list[RecoveryOption] = field(default_factory=list)
    stakeholder_impact: str = ""
    severity: str = ""    # info / warning / critical


def trace_budget_to_need(
    budget_name: str,
    budget_status: str,
    budget_margin_percent: float,
    parameters: dict[str, Any] | None = None,
    requirements: list[dict] | None = None,
    functions: list[dict] | None = None,
    objectives: list[dict] | None = None,
    stakeholders: list[dict] | None = None,
) -> TraceabilityReport:
    """Trace a budget exceedance all the way to stakeholder impact.

    This is the key question: "My mass margin is 0% — so what? Who cares?"
    The answer: "The mass margin threatens REQ-SYS-MASS, which implements
    function F-005 (generate power — SA needs area → needs mass), which
    serves objective OBJ-1 (3-year science mission), which fulfills
    stakeholder need (funding agency requires 3-year data return)."
    """
    report = TraceabilityReport(
        trigger=f"{budget_name} budget: margin {budget_margin_percent:.1f}% ({budget_status})",
        severity="critical" if budget_status == "red" else ("warning" if budget_status == "amber" else "info"),
    )

    requirements = requirements or []
    functions = functions or []
    objectives = objectives or []
    stakeholders = stakeholders or []

    # Level 1: Budget
    report.chain.append(TraceLink(
        level="budget", id=budget_name,
        text=f"{budget_name} budget: margin {budget_margin_percent:.1f}%",
        status=budget_status,
    ))

    # Level 2: Find requirements this budget relates to
    budget_domain_map = {
        "mass_dry": ["mass", "structure", "power", "aocs", "link", "thermal"],
        "power": ["power"],
        "volume": ["volume"],
        "pointing": ["aocs"],
        "data": ["data", "link"],
        "delta_v": ["propulsion", "orbit"],
    }
    domains = budget_domain_map.get(budget_name, [budget_name])

    related_reqs = [r for r in requirements if r.get("domain", "") in domains]
    for req in related_reqs[:3]:  # Top 3 related requirements
        report.chain.append(TraceLink(
            level="requirement", id=req.get("id", ""),
            text=req.get("text", ""),
            status="at_risk" if budget_status == "red" else "amber",
        ))

    # Level 3: Find functions these requirements derive from
    req_ids = {r.get("id", "") for r in related_reqs}
    related_funcs = [f for f in functions
                     if any(rid in (f.get("derived_requirement_ids", []) or []) for rid in req_ids)]
    if not related_funcs:
        # Try matching by domain/allocated_to
        related_funcs = [f for f in functions if f.get("allocated_to", "") in domains]

    for func in related_funcs[:2]:
        report.chain.append(TraceLink(
            level="function", id=func.get("id", ""),
            text=func.get("name", ""),
        ))

    # Level 4: Find objectives these functions serve
    func_obj_ids: set[str] = set()
    for func in related_funcs:
        func_obj_ids.update(func.get("objective_ids", []) or [])

    related_objs = [o for o in objectives if o.get("id", "") in func_obj_ids]
    if not related_objs and objectives:
        related_objs = objectives[:1]  # Fallback: first objective

    for obj in related_objs[:2]:
        report.chain.append(TraceLink(
            level="objective", id=obj.get("id", ""),
            text=obj.get("text", ""),
            status="at_risk" if budget_status == "red" else "",
        ))

    # Level 5: Stakeholder impact
    if stakeholders:
        for sh in stakeholders[:2]:
            report.chain.append(TraceLink(
                level="stakeholder_need", id=sh.get("name", ""),
                text=f"{sh.get('name', '')}: {', '.join(sh.get('needs', [])[:2])}",
            ))

    # Stakeholder impact summary
    if related_objs:
        obj_text = related_objs[0].get("text", "mission objective")
        report.stakeholder_impact = (
            f"If {budget_name} budget is not recovered, objective '{obj_text}' "
            f"may not be achievable. This impacts stakeholders: "
            f"{', '.join(sh.get('name', '?') for sh in stakeholders[:2])}."
        )

    # Recovery options (generic by budget type + specific where possible)
    report.recovery_options = _generate_recovery_options(budget_name, budget_margin_percent, parameters)

    return report


def _generate_recovery_options(
    budget_name: str,
    margin_percent: float,
    parameters: dict[str, Any] | None = None,
) -> list[RecoveryOption]:
    """Generate concrete recovery options for a budget exceedance."""
    options: list[RecoveryOption] = []

    if budget_name in ("mass_dry", "mass_wet"):
        options.extend([
            RecoveryOption(
                description="Select lighter component (check KB for alternatives with lower mass)",
                subsystem="heaviest subsystem",
                impact="May cost more or have less performance",
                feasibility="easy",
                trade_off="Performance or cost for mass savings",
            ),
            RecoveryOption(
                description="Reduce structural mass (3D-printed structure, topology optimisation)",
                subsystem="structure",
                impact="-15 to -30% structure mass, +50% structure cost, +4 week lead time",
                feasibility="moderate",
                trade_off="Cost and schedule for mass savings",
            ),
            RecoveryOption(
                description="Remove propulsion (rely on natural deorbit if orbit allows)",
                subsystem="propulsion",
                impact="Saves 0.5-2 kg but no orbit maintenance or active deorbit",
                feasibility="easy" if margin_percent > -10 else "moderate",
                trade_off="Orbit control for mass savings — check debris compliance",
            ),
            RecoveryOption(
                description="Relax mass requirement (negotiate with launch provider for higher mass allocation)",
                subsystem="systems",
                impact="May need to move to larger deployer or different rideshare slot",
                feasibility="requires_stakeholder_approval",
                trade_off="Launch cost or schedule flexibility",
            ),
        ])

    elif budget_name == "power":
        options.extend([
            RecoveryOption(
                description="Increase solar array area (larger or additional deployable panels)",
                subsystem="power",
                impact="+0.2-0.5 kg, +5-15 kEUR",
                feasibility="easy",
                trade_off="Mass and cost for power generation",
            ),
            RecoveryOption(
                description="Reduce payload duty cycle (less imaging time per orbit)",
                subsystem="payload",
                impact="Reduces data volume → may affect revisit or coverage",
                feasibility="moderate",
                trade_off="Science return for power margin",
            ),
            RecoveryOption(
                description="Schedule payload and downlink in different parts of orbit (never simultaneous)",
                subsystem="systems",
                impact="Reduces peak power but increases operational complexity",
                feasibility="easy",
                trade_off="Operational simplicity for power margin",
            ),
        ])

    elif budget_name == "pointing":
        options.extend([
            RecoveryOption(
                description="Select higher-precision star tracker",
                subsystem="aocs",
                impact="+0.3 kg, +5-10 kEUR",
                feasibility="easy",
                trade_off="Mass and cost for pointing accuracy",
            ),
            RecoveryOption(
                description="Increase structural stiffness (thicker panels, stiffer brackets)",
                subsystem="structure",
                impact="+0.2 kg, reduces thermal distortion contribution",
                feasibility="moderate",
                trade_off="Mass for alignment stability",
            ),
            RecoveryOption(
                description="Relax GSD requirement (larger GSD needs less pointing accuracy)",
                subsystem="payload",
                impact="Science return degrades proportionally",
                feasibility="requires_stakeholder_approval",
                trade_off="Science performance for pointing margin",
            ),
        ])

    elif budget_name == "volume":
        options.extend([
            RecoveryOption(
                description="Move to larger form factor (e.g. 3U → 6U)",
                subsystem="structure",
                impact="Doubles available volume, +0.3 kg structure, different deployer",
                feasibility="moderate",
                trade_off="Larger spacecraft → higher launch cost",
            ),
            RecoveryOption(
                description="Select more compact components",
                subsystem="all",
                impact="May reduce performance or increase cost",
                feasibility="easy",
                trade_off="Performance for volume",
            ),
        ])

    # Always add the "do nothing and accept risk" option
    options.append(RecoveryOption(
        description=f"Accept {budget_name} margin exceedance as design risk",
        subsystem="systems",
        impact=f"Margin policy violated — risk accepted at programme level",
        feasibility="requires_stakeholder_approval",
        trade_off="Accepting technical risk for schedule/cost savings",
    ))

    return options
