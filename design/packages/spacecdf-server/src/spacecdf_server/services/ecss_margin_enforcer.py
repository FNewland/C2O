"""SpaceCDF — ECSS Margin Enforcement Engine.

Validates design budgets against ECSS margin philosophy per project phase.
Uses the margin data from ecss_margins.yaml and checks each budget domain.

Standards enforced:
  - ECSS-E-HB-10-02A §5.2 — Mass margins
  - ECSS-E-ST-20C — Power margins
  - ECSS-E-ST-50-05C — Link budget margins
  - ECSS-E-ST-31C — Thermal margins
  - ECSS-E-ST-35C — Propulsion/ΔV margins
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Phase-dependent minimum margins (from ecss_margins.yaml, inlined for speed)
MASS_MARGINS = {
    "phase_0": {"equipment": 20, "system": 20, "total": 44},
    "phase_a": {"equipment": 20, "system": 20, "total": 44},
    "phase_b": {"equipment": 10, "system": 20, "total": 32},
    "phase_c": {"equipment": 5, "system": 15, "total": 21},
    "phase_d": {"equipment": 3, "system": 10, "total": 13},
}

POWER_MARGINS = {
    "phase_0": {"equipment": 20, "system": 20},
    "phase_a": {"equipment": 20, "system": 20},
    "phase_b": {"equipment": 10, "system": 20},
    "phase_c": {"equipment": 5, "system": 15},
    "phase_d": {"equipment": 5, "system": 10},
}

LINK_MARGINS = {
    "phase_0": 6.0, "phase_a": 6.0, "phase_b": 4.0,
    "phase_c": 3.0, "phase_d": 3.0,
}

THERMAL_MARGINS = {
    "qualification": {"hot": 15, "cold": 15},
    "acceptance": {"hot": 10, "cold": 10},
    "operating": {"hot": 5, "cold": 5},
}

DV_MARGINS = {
    "phase_0": 25, "phase_a": 25, "phase_b": 15,
    "phase_c": 10, "phase_d": 5,
}


@dataclass
class MarginViolation:
    """A margin violation found during enforcement."""
    domain: str
    standard: str
    parameter: str
    required_margin: float
    actual_margin: float
    unit: str
    severity: str  # "critical" (negative), "major" (below policy), "info" (meets)
    message: str


@dataclass
class MarginReport:
    """Full margin enforcement report."""
    phase: str
    violations: list[MarginViolation] = field(default_factory=list)
    checks: list[MarginViolation] = field(default_factory=list)  # All checks including passing

    @property
    def compliant(self) -> bool:
        return not any(v.severity in ("critical", "major") for v in self.violations)

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "critical")

    @property
    def major_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "major")


def enforce_ecss_margins(
    design_params: dict[str, Any],
    phase_id: str = "phase_a",
) -> MarginReport:
    """Check all design parameters against ECSS margin policy for the given phase.

    Args:
        design_params: Dict of parameter values. Keys like "systems.mass_margin_percent".
        phase_id: Project phase for margin lookup.

    Returns:
        MarginReport with all violations and passing checks.
    """
    report = MarginReport(phase=phase_id)
    phase_key = phase_id.replace("phase_", "phase_")

    def _get(param_id: str) -> float | None:
        v = design_params.get(param_id)
        if v is None:
            return None
        if isinstance(v, dict):
            return v.get("value")
        if isinstance(v, (int, float)):
            return float(v)
        return None

    # --- Mass margin (ECSS-E-HB-10-02A) ---
    mass_policy = MASS_MARGINS.get(phase_key, MASS_MARGINS["phase_a"])
    mass_margin = _get("systems.mass_margin_percent")
    if mass_margin is not None:
        required = mass_policy["system"]
        check = MarginViolation(
            domain="mass", standard="ECSS-E-HB-10-02A §5.2",
            parameter="systems.mass_margin_percent",
            required_margin=required, actual_margin=mass_margin, unit="%",
            severity="info", message=f"Mass margin {mass_margin:.1f}% vs required {required}%",
        )
        if mass_margin < 0:
            check.severity = "critical"
            check.message = f"NEGATIVE mass margin ({mass_margin:.1f}%) — design does not close"
            report.violations.append(check)
        elif mass_margin < required:
            check.severity = "major"
            check.message = f"Mass margin {mass_margin:.1f}% below {phase_id} policy of {required}%"
            report.violations.append(check)
        report.checks.append(check)

    # --- Power margin (ECSS-E-ST-20C) ---
    power_policy = POWER_MARGINS.get(phase_key, POWER_MARGINS["phase_a"])
    power_margin = _get("systems.power_margin_percent")
    if power_margin is not None:
        required = power_policy["system"]
        check = MarginViolation(
            domain="power", standard="ECSS-E-ST-20C",
            parameter="systems.power_margin_percent",
            required_margin=required, actual_margin=power_margin, unit="%",
            severity="info", message=f"Power margin {power_margin:.1f}% vs required {required}%",
        )
        if power_margin < 0:
            check.severity = "critical"
            check.message = f"NEGATIVE power margin ({power_margin:.1f}%)"
            report.violations.append(check)
        elif power_margin < required:
            check.severity = "major"
            check.message = f"Power margin {power_margin:.1f}% below {phase_id} policy of {required}%"
            report.violations.append(check)
        report.checks.append(check)

    # --- Link margin (ECSS-E-ST-50-05C) ---
    link_margin = _get("link.downlink_margin_db")
    if link_margin is not None:
        required = LINK_MARGINS.get(phase_key, 3.0)
        check = MarginViolation(
            domain="link", standard="ECSS-E-ST-50-05C",
            parameter="link.downlink_margin_db",
            required_margin=required, actual_margin=link_margin, unit="dB",
            severity="info", message=f"Link margin {link_margin:.1f} dB vs required {required} dB",
        )
        if link_margin < 0:
            check.severity = "critical"
            check.message = f"NEGATIVE link margin ({link_margin:.1f} dB) — link does not close"
            report.violations.append(check)
        elif link_margin < required:
            check.severity = "major"
            check.message = f"Link margin {link_margin:.1f} dB below {phase_id} policy of {required} dB"
            report.violations.append(check)
        report.checks.append(check)

    # --- Thermal margin (ECSS-E-ST-31C) ---
    max_temp = _get("thermal.max_temp_c")
    max_allowed = _get("thermal.max_operating_temp_c") or 50.0
    if max_temp is not None:
        hot_margin = max_allowed - max_temp
        required = THERMAL_MARGINS["operating"]["hot"]
        check = MarginViolation(
            domain="thermal", standard="ECSS-E-ST-31C",
            parameter="thermal.max_temp_c",
            required_margin=required, actual_margin=hot_margin, unit="°C",
            severity="info", message=f"Hot case margin {hot_margin:.1f}°C vs required {required}°C",
        )
        if hot_margin < 0:
            check.severity = "critical"
            check.message = f"Hot case EXCEEDS operating limit by {abs(hot_margin):.1f}°C"
            report.violations.append(check)
        elif hot_margin < required:
            check.severity = "major"
            check.message = f"Hot case margin {hot_margin:.1f}°C below operating policy of {required}°C"
            report.violations.append(check)
        report.checks.append(check)

    # --- ΔV margin (ECSS-E-ST-35C) ---
    dv_total = _get("propulsion.delta_v_total_ms") or _get("orbit.delta_v_total_ms")
    dv_required = _get("propulsion.delta_v_required_ms")
    if dv_total is not None and dv_required is not None and dv_required > 0:
        dv_margin_pct = ((dv_total - dv_required) / dv_required) * 100
        required = DV_MARGINS.get(phase_key, 15)
        check = MarginViolation(
            domain="propulsion", standard="ECSS-E-ST-35C",
            parameter="propulsion.delta_v_total_ms",
            required_margin=required, actual_margin=dv_margin_pct, unit="%",
            severity="info", message=f"ΔV margin {dv_margin_pct:.0f}% vs required {required}%",
        )
        if dv_margin_pct < 0:
            check.severity = "critical"
            check.message = f"INSUFFICIENT ΔV: {dv_total:.1f} m/s available vs {dv_required:.1f} m/s required"
            report.violations.append(check)
        elif dv_margin_pct < required:
            check.severity = "major"
            check.message = f"ΔV margin {dv_margin_pct:.0f}% below {phase_id} policy of {required}%"
            report.violations.append(check)
        report.checks.append(check)

    return report
