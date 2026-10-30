"""SpaceCDF — Test Procedure Generator & Verification Tracker.

Generates test procedures per requirement, environmental test specs,
and verification closure tracking. Part of Stage 6.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    PLANNED = "planned"
    PROCEDURE_WRITTEN = "procedure_written"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"


class TestProcedure(BaseModel):
    """A test procedure for verifying a requirement."""
    id: str = ""
    requirement_id: str = ""
    requirement_text: str = ""
    verification_method: str = "test"  # test / analysis / inspection / demonstration
    title: str = ""
    objective: str = ""
    prerequisites: list[str] = Field(default_factory=list)
    equipment_needed: list[str] = Field(default_factory=list)
    setup: list[str] = Field(default_factory=list)
    procedure_steps: list[str] = Field(default_factory=list)
    pass_criteria: list[str] = Field(default_factory=list)
    fail_criteria: list[str] = Field(default_factory=list)
    data_recording: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    estimated_duration_min: int = 30
    status: VerificationStatus = VerificationStatus.PLANNED


class EnvironmentalTestSpec(BaseModel):
    """Environmental test specification from launch vehicle requirements."""
    test_type: str = ""  # vibration / thermal_vacuum / emi_emc / shock
    level: str = ""
    duration: str = ""
    reference: str = ""
    notes: str = ""


def generate_test_procedures(
    requirements: list[dict[str, Any]],
    design_params: dict[str, Any] | None = None,
) -> list[TestProcedure]:
    """Generate test procedures from requirements."""
    procedures: list[TestProcedure] = []
    dp = design_params or {}

    for req in requirements:
        req_id = req.get("id", "")
        req_text = req.get("text", "")
        domain = req.get("domain", "")
        method = req.get("verification_method", "analysis")
        threshold = req.get("threshold", 0)
        operator = req.get("operator", ">=")
        unit = req.get("unit", "")

        proc = TestProcedure(
            id=f"TP-{req_id}",
            requirement_id=req_id,
            requirement_text=req_text,
            verification_method=method,
            title=f"Verification of {req_id}: {req_text[:60]}",
        )

        if method == "test":
            proc = _generate_test_procedure(proc, domain, threshold, operator, unit)
        elif method == "analysis":
            proc = _generate_analysis_procedure(proc, domain, threshold, operator, unit, dp)
        elif method == "inspection":
            proc = _generate_inspection_procedure(proc, domain)
        else:
            proc = _generate_demonstration_procedure(proc, domain)

        procedures.append(proc)

    return procedures


def _generate_test_procedure(
    proc: TestProcedure, domain: str, threshold: float, op: str, unit: str
) -> TestProcedure:
    """Generate a hardware test procedure."""
    proc.objective = f"Verify that the {domain} subsystem meets {proc.requirement_id} by functional test"

    proc.prerequisites = [
        "Spacecraft powered on in test configuration",
        "Ground support equipment (GSE) connected and verified",
        "Test environment within operating temperature range",
        f"Previous subsystem tests for {domain} completed",
    ]

    proc.equipment_needed = [
        "Spacecraft under test",
        "Ground support equipment (GSE)",
        "Test measurement equipment (DMM, oscilloscope as needed)",
        "Data recording system",
    ]

    proc.setup = [
        f"Configure spacecraft in {domain} test mode",
        "Verify all GSE connections are secure",
        "Record ambient conditions (temperature, humidity)",
        "Verify measurement equipment is calibrated",
    ]

    proc.procedure_steps = [
        f"1. Command spacecraft to {domain} operational mode",
        "2. Wait for mode transition confirmation (TM verification)",
        f"3. Measure {domain} parameter under test",
        f"4. Record measured value and compare against threshold ({op} {threshold} {unit})",
        "5. Repeat measurement 3 times for statistical confidence",
        "6. Record all telemetry during test",
        f"7. Return spacecraft to safe mode",
    ]

    proc.pass_criteria = [
        f"Measured value {op} {threshold} {unit} for all 3 measurements",
        "No anomalies in telemetry during test",
        "Mode transitions completed nominally",
    ]

    proc.fail_criteria = [
        f"Any measurement does NOT satisfy {op} {threshold} {unit}",
        "Anomaly detected in telemetry",
        "Mode transition failure",
    ]

    proc.data_recording = [
        f"Measured values (3 repetitions) with timestamps",
        "Full telemetry log for test duration",
        "Ambient conditions",
        "Test equipment serial numbers and calibration dates",
    ]

    proc.estimated_duration_min = 60
    return proc


def _generate_analysis_procedure(
    proc: TestProcedure, domain: str, threshold: float, op: str, unit: str,
    design_params: dict[str, Any],
) -> TestProcedure:
    """Generate an analysis verification procedure."""
    proc.objective = f"Verify {proc.requirement_id} by analysis using validated models"
    proc.verification_method = "analysis"

    proc.prerequisites = [
        "Design model validated against heritage data or test results",
        "Input parameters from current design baseline",
        "Analysis tool qualified for this application",
    ]

    proc.procedure_steps = [
        f"1. Review {domain} model inputs against current design baseline",
        f"2. Run {domain} analysis model with worst-case input conditions",
        f"3. Extract predicted value for parameter under verification",
        f"4. Compare predicted value against requirement ({op} {threshold} {unit})",
        "5. Compute margin: (predicted - threshold) / threshold × 100%",
        "6. Verify margin exceeds minimum analysis margin policy (typically 10-20%)",
        "7. Document analysis assumptions, model version, and input data sources",
    ]

    proc.pass_criteria = [
        f"Analysis result {op} {threshold} {unit}",
        "Analysis margin >= margin policy for current phase",
        "Model validation evidence documented",
    ]

    proc.estimated_duration_min = 120
    return proc


def _generate_inspection_procedure(proc: TestProcedure, domain: str) -> TestProcedure:
    proc.objective = f"Verify {proc.requirement_id} by visual inspection"
    proc.verification_method = "inspection"
    proc.procedure_steps = [
        "1. Access the item under inspection",
        "2. Visually verify the requirement is met (physical characteristics, markings, labels)",
        "3. Photograph the inspected item with evidence of compliance",
        "4. Record inspection result and inspector identity",
    ]
    proc.estimated_duration_min = 15
    return proc


def _generate_demonstration_procedure(proc: TestProcedure, domain: str) -> TestProcedure:
    proc.objective = f"Verify {proc.requirement_id} by operational demonstration"
    proc.verification_method = "demonstration"
    proc.procedure_steps = [
        "1. Configure system in the operational configuration",
        "2. Execute the function or operation specified in the requirement",
        "3. Observe and record the system behaviour",
        "4. Compare observed behaviour against requirement criteria",
        "5. Document results with evidence (screenshots, telemetry, video)",
    ]
    proc.estimated_duration_min = 45
    return proc


def generate_environmental_test_specs(
    launch_vehicle: str = "falcon_9",
    spacecraft_mass_kg: float = 5.0,
) -> list[EnvironmentalTestSpec]:
    """Generate environmental test specifications from launch vehicle ICD."""

    # Launch vehicle environment data (simplified)
    lv_envs = {
        "falcon_9": {
            "vibration_g_rms": 7.7, "vibration_duration_s": 120,
            "sine_sweep_hz": "5-2000", "sine_g": 1.5,
            "tvac_hot_c": 61, "tvac_cold_c": -24, "tvac_cycles": 8,
            "shock_g": 3000, "shock_hz": "100-10000",
            "acoustic_db": 139,
        },
        "vega_c": {
            "vibration_g_rms": 8.5, "vibration_duration_s": 120,
            "sine_sweep_hz": "5-2000", "sine_g": 1.6,
            "tvac_hot_c": 61, "tvac_cold_c": -24, "tvac_cycles": 8,
            "shock_g": 2000, "shock_hz": "100-10000",
            "acoustic_db": 142,
        },
    }

    env = lv_envs.get(launch_vehicle, lv_envs["falcon_9"])

    specs = [
        EnvironmentalTestSpec(
            test_type="random_vibration",
            level=f"{env['vibration_g_rms']} g RMS, {env['sine_sweep_hz']} Hz",
            duration=f"{env['vibration_duration_s']}s per axis, 3 axes",
            reference=f"{launch_vehicle} Payload User Guide",
            notes="Protoflight: qualification level × 0.75, acceptance duration",
        ),
        EnvironmentalTestSpec(
            test_type="sine_vibration",
            level=f"{env['sine_g']} g, {env['sine_sweep_hz']} Hz sweep at 2 oct/min",
            duration="1 sweep per axis, 3 axes",
            reference=f"{launch_vehicle} Payload User Guide",
        ),
        EnvironmentalTestSpec(
            test_type="thermal_vacuum",
            level=f"Hot: +{env['tvac_hot_c']}°C, Cold: {env['tvac_cold_c']}°C",
            duration=f"{env['tvac_cycles']} cycles, 1 hour dwell at each extreme",
            reference="ECSS-E-ST-10-03C (protoflight: qualification temp, acceptance cycles)",
            notes="Functional test at each temperature extreme",
        ),
        EnvironmentalTestSpec(
            test_type="shock",
            level=f"{env['shock_g']} g SRS, {env['shock_hz']} Hz",
            duration="1 shock per axis per direction (6 total)",
            reference=f"{launch_vehicle} Payload User Guide",
            notes="If shock levels are below CubeSat deployer attenuation, may be waived",
        ),
        EnvironmentalTestSpec(
            test_type="emi_emc",
            level="Per ECSS-E-ST-20-07C or MIL-STD-461G (tailored)",
            duration="Per test procedure for each test case",
            reference="ECSS-E-ST-20-07C",
            notes="Critical for CubeSats: verify TX doesn't interfere with own sensors",
        ),
    ]

    return specs


class VerificationTracker(BaseModel):
    """Tracks verification status across all requirements."""
    items: list[dict[str, Any]] = Field(default_factory=list)

    def add_item(self, req_id: str, method: str, procedure_id: str = ""):
        self.items.append({
            "requirement_id": req_id,
            "method": method,
            "procedure_id": procedure_id,
            "status": "planned",
            "result": None,
            "evidence": "",
            "verified_by": "",
            "verified_at": None,
        })

    def update_status(self, req_id: str, status: str, result: str | None = None, evidence: str = ""):
        for item in self.items:
            if item["requirement_id"] == req_id:
                item["status"] = status
                item["result"] = result
                item["evidence"] = evidence
                if status in ("passed", "failed"):
                    item["verified_at"] = datetime.now(timezone.utc).isoformat()

    @property
    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.items:
            s = item["status"]
            counts[s] = counts.get(s, 0) + 1
        return counts

    @property
    def closure_percent(self) -> float:
        closed = sum(1 for i in self.items if i["status"] in ("passed", "waived"))
        return (closed / max(len(self.items), 1)) * 100
