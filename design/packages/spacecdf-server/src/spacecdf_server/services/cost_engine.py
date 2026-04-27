"""SpaceCDF — NASA CEH-Aligned Cost Estimation Engine.

Multi-model cost estimation following NASA Cost Estimating Handbook (CEH v4.0)
guidelines. Implements PCEC-style parametric CERs with WBS structure aligned
to NPR 7120.5, SSCM-style small satellite models, NICM-style instrument costs,
MOCET-style operations costs, learning curves for constellations, and
Monte Carlo cost risk analysis.

CER form: Cost = a × Mass^b × complexity_factors
DDT&E and recurring costs estimated separately.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

from spacecdf_common.agents.base import DesignState


@dataclass
class WBSElement:
    """A single WBS element with cost breakdown."""
    wbs_id: str            # e.g. "X.06.01"
    name: str              # e.g. "Structures & Mechanisms"
    ddte_keur: float = 0   # Development cost
    recurring_keur: float = 0  # Production cost per unit
    total_keur: float = 0
    confidence: float = 0.6  # Parametric uncertainty
    notes: str = ""
    cost_drivers: dict[str, Any] = field(default_factory=dict)


@dataclass
class CostEstimate:
    """Complete NASA CEH-aligned cost estimate."""
    # WBS-structured breakdown
    wbs: list[WBSElement] = field(default_factory=list)

    # Phase distribution
    phase_a_keur: float = 0
    phase_b_keur: float = 0
    phase_cd_keur: float = 0
    phase_e_keur: float = 0

    # Totals
    spacecraft_ddte_keur: float = 0
    spacecraft_recurring_keur: float = 0
    payload_keur: float = 0
    launch_keur: float = 0
    ground_keur: float = 0
    operations_keur: float = 0
    pm_se_sma_keur: float = 0  # Project management + SE + S&MA
    total_lcc_keur: float = 0  # Life-cycle cost

    # Risk analysis
    p50_keur: float = 0
    p70_keur: float = 0
    p80_keur: float = 0
    p90_keur: float = 0
    cost_hist: list[int] = field(default_factory=list)
    cost_hist_bin_edges: list[float] = field(default_factory=list)
    cost_mean_keur: float = 0
    cost_std_keur: float = 0

    # Constellation
    num_units: int = 1
    learning_rate: float = 0.95
    fleet_total_keur: float = 0

    # Metadata
    model_used: str = ""
    warnings: list[str] = field(default_factory=list)


# --- CER Coefficients by subsystem and spacecraft class ---
# Format: (a_ddte, b_ddte, a_recurring, b_recurring)
# Cost = a × mass_kg^b (in kEUR, 2025 economics)

CERS_SMALL_SAT = {
    # SSCM-style CERs for <1000 kg spacecraft
    "structures": (8.5, 0.85, 3.2, 0.82),
    "thermal": (15.0, 0.90, 5.5, 0.85),
    "eps": (45.0, 0.78, 18.0, 0.75),
    "aocs": (95.0, 0.82, 35.0, 0.78),
    "propulsion": (38.0, 0.80, 15.0, 0.77),
    "cdh": (120.0, 0.75, 45.0, 0.72),
    "ttc": (85.0, 0.80, 30.0, 0.76),
    "harness": (12.0, 0.85, 5.0, 0.82),
}

CERS_LARGE_SAT = {
    # PCEC/NAFCOM-style CERs for >1000 kg spacecraft
    "structures": (12.0, 0.82, 4.5, 0.80),
    "thermal": (22.0, 0.88, 8.0, 0.84),
    "eps": (65.0, 0.76, 25.0, 0.73),
    "aocs": (140.0, 0.80, 50.0, 0.76),
    "propulsion": (55.0, 0.78, 20.0, 0.75),
    "cdh": (180.0, 0.73, 65.0, 0.70),
    "ttc": (120.0, 0.78, 42.0, 0.74),
    "harness": (18.0, 0.83, 7.0, 0.80),
}

# Complexity factors (multiplicative adjustments to CER output)
COMPLEXITY_FACTORS = {
    "trl_9": 1.0,    # Flight proven
    "trl_8": 1.05,   # Flight qualified
    "trl_7": 1.15,   # Prototype in space
    "trl_6": 1.35,   # Prototype in relevant environment
    "trl_5": 1.60,   # Component validation in relevant environment
    "trl_4": 2.00,   # Component validation in lab
    "trl_3": 2.50,   # Proof of concept
    "new_design": 1.3,
    "modified_design": 1.1,
    "heritage_design": 0.9,
}

# NICM-style instrument cost (simplified)
# Instrument_Cost = a × mass^b × data_rate_factor
INSTRUMENT_CER = {
    "optical_imager": (180.0, 0.85),
    "radar": (250.0, 0.82),
    "spectrometer": (200.0, 0.83),
    "lidar": (220.0, 0.80),
    "magnetometer": (50.0, 0.90),
    "particle_detector": (100.0, 0.85),
    "comms_payload": (150.0, 0.78),
    "default": (160.0, 0.83),
}

# MOCET-style operations cost building blocks (kEUR per year)
OPS_COST_BLOCKS = {
    # (commissioning_factor, prime_ops_per_year, extended_ops_per_year)
    "nano": (0.5, 200, 100),
    "micro": (0.8, 400, 200),
    "small": (1.0, 1200, 600),
    "medium": (1.5, 4000, 2000),
    "large": (2.0, 12000, 6000),
    "flagship": (3.0, 40000, 20000),
}

# Phase cost distribution (fraction of DDT&E by phase)
PHASE_DISTRIBUTION = {
    "phase_a": 0.05,   # Concept study
    "phase_b": 0.15,   # Preliminary design
    "phase_cd": 0.80,  # Detailed design + fabrication
}


def estimate_cost(state: DesignState) -> CostEstimate:
    """Compute a full NASA CEH-aligned cost estimate from the design state.

    Implements:
    1. WBS-structured subsystem costs using parametric CERs
    2. NICM-style instrument costs
    3. MOCET-style operations costs
    4. Learning curves for constellations
    5. Monte Carlo cost risk via CER uncertainty
    """
    est = CostEstimate()

    sc_class = state.get("mission.spacecraft_class", "small")
    if not isinstance(sc_class, str):
        sc_class = "small"
    mission_years = state.get("mission.duration_years", 3.0) or 3.0
    num_units = state.get_requirement("num_spacecraft") or 1
    est.num_units = num_units

    # Select CER set based on spacecraft class
    dry_mass = state.get("mass.dry_mass_kg", 100) or 100
    cers = CERS_SMALL_SAT if dry_mass < 1000 else CERS_LARGE_SAT
    est.model_used = "SSCM-style" if dry_mass < 1000 else "PCEC-style"

    # --- X.06 Spacecraft Bus subsystems ---
    subsystem_masses = {
        "structures": state.get("structure.mass_kg", 0) or 0,
        "thermal": state.get("thermal.tcs_mass_kg", 0) or 0,
        "eps": state.get("power.eps_mass_kg", 0) or 0,
        "aocs": state.get("aocs.mass_kg", 0) or 0,
        "propulsion": state.get("propulsion.total_mass_kg", 0) or 0,
        "cdh": state.get("data.obdh_mass_kg", 0) or 0,
        "ttc": state.get("link.ttc_mass_kg", 0) or 0,
        "harness": (state.get("mass.dry_mass_kg", 0) or 0) * 0.05,  # ~5% for harness
    }

    wbs_counter = 1
    for subsys, mass in subsystem_masses.items():
        if mass <= 0:
            continue
        a_d, b_d, a_r, b_r = cers.get(subsys, (50, 0.80, 20, 0.77))

        # Apply complexity factor for TRL
        trl = _get_subsystem_trl(state, subsys)
        complexity = COMPLEXITY_FACTORS.get(f"trl_{trl}", 1.0)

        ddte = a_d * (mass ** b_d) * complexity
        recurring = a_r * (mass ** b_r) * complexity

        wbs_element = WBSElement(
            wbs_id=f"X.06.{wbs_counter:02d}",
            name=subsys.upper(),
            ddte_keur=round(ddte, 0),
            recurring_keur=round(recurring, 0),
            total_keur=round(ddte + recurring, 0),
            cost_drivers={"mass_kg": mass, "trl": trl, "complexity": complexity},
        )
        est.wbs.append(wbs_element)
        est.spacecraft_ddte_keur += ddte
        est.spacecraft_recurring_keur += recurring
        wbs_counter += 1

    # --- X.05 Payload (NICM-style) ---
    i = 0
    while True:
        pl_mass = state.get(f"payload.{i}.mass_kg")
        if pl_mass is None:
            break
        pl_type = state.get_requirement(f"payloads.{i}.type") or "default"
        if not isinstance(pl_type, str):
            pl_type = "default"
        a_i, b_i = INSTRUMENT_CER.get(pl_type, INSTRUMENT_CER["default"])
        inst_cost = a_i * (pl_mass ** b_i)

        est.wbs.append(WBSElement(
            wbs_id=f"X.05.{i + 1:02d}",
            name=f"Payload {i + 1}",
            ddte_keur=round(inst_cost * 0.7, 0),  # 70% DDT&E
            recurring_keur=round(inst_cost * 0.3, 0),  # 30% recurring
            total_keur=round(inst_cost, 0),
        ))
        est.payload_keur += inst_cost
        i += 1

    # --- X.01-X.03 PM, SE, S&MA (as fraction of hardware) ---
    hardware_total = est.spacecraft_ddte_keur + est.spacecraft_recurring_keur + est.payload_keur
    pm_fraction = {"nano": 0.10, "micro": 0.12, "small": 0.15, "medium": 0.18, "large": 0.20, "flagship": 0.22}
    se_fraction = {"nano": 0.08, "micro": 0.10, "small": 0.12, "medium": 0.14, "large": 0.16, "flagship": 0.18}
    sma_fraction = {"nano": 0.04, "micro": 0.05, "small": 0.06, "medium": 0.07, "large": 0.08, "flagship": 0.10}

    pm = hardware_total * pm_fraction.get(sc_class, 0.15)
    se = hardware_total * se_fraction.get(sc_class, 0.12)
    sma = hardware_total * sma_fraction.get(sc_class, 0.06)
    est.pm_se_sma_keur = pm + se + sma

    est.wbs.insert(0, WBSElement(wbs_id="X.01", name="Project Management", total_keur=round(pm, 0)))
    est.wbs.insert(1, WBSElement(wbs_id="X.02", name="Systems Engineering", total_keur=round(se, 0)))
    est.wbs.insert(2, WBSElement(wbs_id="X.03", name="Safety & Mission Assurance", total_keur=round(sma, 0)))

    # --- X.10 System Integration & Test ---
    sit = hardware_total * 0.10  # ~10% of hardware
    est.wbs.append(WBSElement(wbs_id="X.10", name="System I&T", total_keur=round(sit, 0)))

    # --- X.08 Launch ---
    wet_mass = state.get("mass.wet_mass_kg", 100) or 100
    mission_type = state.get_requirement("mission_type") or ""
    if not isinstance(mission_type, str):
        mission_type = str(mission_type)
    est.launch_keur = _estimate_launch_cost(wet_mass, sc_class, mission_type)
    est.wbs.append(WBSElement(wbs_id="X.08", name="Launch Vehicle/Services", total_keur=round(est.launch_keur, 0)))

    # --- X.09 Ground System ---
    est.ground_keur = _estimate_ground_cost(sc_class, mission_type)
    est.wbs.append(WBSElement(wbs_id="X.09", name="Ground System", total_keur=round(est.ground_keur, 0)))

    # --- X.07 Mission Operations (MOCET-style) ---
    ops_block = OPS_COST_BLOCKS.get(sc_class, OPS_COST_BLOCKS["small"])
    commissioning_months = 3
    prime_years = mission_years * 0.8
    extended_years = mission_years * 0.2

    ops_commissioning = ops_block[0] * ops_block[1] * (commissioning_months / 12)
    ops_prime = ops_block[1] * prime_years
    ops_extended = ops_block[2] * extended_years
    est.operations_keur = ops_commissioning + ops_prime + ops_extended

    # Deep-space missions add DSN / ESTRACK network fees + navigation team
    is_deep_space = mission_type in ("lunar", "mars", "deep_space", "lagrange",
                                      "science_planetary", "interplanetary")
    if is_deep_space:
        dsn_fee_per_year_keur = 8000  # ~$8-12M/yr for DSN tracking
        nav_team_per_year_keur = 3000  # Navigation + flight dynamics team
        est.operations_keur += (dsn_fee_per_year_keur + nav_team_per_year_keur) * mission_years
        est.wbs.append(WBSElement(
            wbs_id="X.07.DS", name="Deep-Space Network Fees",
            total_keur=round(dsn_fee_per_year_keur * mission_years, 0),
        ))
    est.wbs.append(WBSElement(
        wbs_id="X.07", name="Mission Operations",
        total_keur=round(est.operations_keur, 0),
        cost_drivers={"commissioning_mo": commissioning_months, "prime_yr": prime_years, "extended_yr": extended_years},
    ))

    # --- Total Life Cycle Cost ---
    est.total_lcc_keur = (
        est.spacecraft_ddte_keur + est.spacecraft_recurring_keur
        + est.payload_keur + est.pm_se_sma_keur + sit
        + est.launch_keur + est.ground_keur + est.operations_keur
    )

    # --- Phase distribution ---
    spacecraft_total = est.spacecraft_ddte_keur + est.spacecraft_recurring_keur + est.payload_keur + sit
    est.phase_a_keur = spacecraft_total * PHASE_DISTRIBUTION["phase_a"]
    est.phase_b_keur = spacecraft_total * PHASE_DISTRIBUTION["phase_b"]
    est.phase_cd_keur = spacecraft_total * PHASE_DISTRIBUTION["phase_cd"]
    est.phase_e_keur = est.operations_keur

    # --- Learning curve for constellation ---
    if num_units > 1:
        est.learning_rate = 0.95 if num_units <= 5 else (0.90 if num_units <= 50 else 0.85)
        b_learn = math.log(est.learning_rate) / math.log(2)
        fleet_recurring = sum(
            est.spacecraft_recurring_keur * (n ** b_learn)
            for n in range(1, num_units + 1)
        )
        est.fleet_total_keur = est.spacecraft_ddte_keur + fleet_recurring + est.payload_keur * num_units
        est.wbs.append(WBSElement(
            wbs_id="X.06.FL", name=f"Fleet ({num_units} units)",
            total_keur=round(est.fleet_total_keur, 0),
            cost_drivers={"learning_rate": est.learning_rate, "units": num_units},
        ))

    # --- Monte Carlo cost risk (vectorised numpy) ---
    mc = monte_carlo(est.wbs, n=1000, seed=42, sigma=0.25)
    est.p50_keur = round(mc["p50"], 0)
    est.p70_keur = round(mc["p70"], 0)
    est.p80_keur = round(mc["p80"], 0)
    est.p90_keur = round(mc["p90"], 0)
    est.cost_hist = mc["hist"]
    est.cost_hist_bin_edges = mc["hist_bin_edges"]
    est.cost_mean_keur = round(mc["mean"], 0)
    est.cost_std_keur = round(mc["std"], 0)

    return est


def monte_carlo(
    wbs: list[WBSElement],
    n: int = 1000,
    seed: int = 42,
    sigma: float = 0.25,
) -> dict:
    """Vectorised Monte Carlo cost risk analysis.

    For each WBS leaf with total_keur > 0, draws n lognormal samples with
    mu=ln(total_keur) and the configured sigma. Sums across leaves per sample
    and reports percentiles plus a 20-bin histogram for plotting.

    Args:
        wbs: List of WBS elements with total_keur.
        n: Number of Monte Carlo samples.
        seed: RNG seed for reproducibility.
        sigma: Log-normal standard deviation (CER uncertainty).

    Returns:
        Dict with keys p50, p70, p80, p90, hist (20 bin counts), hist_bin_edges,
        mean, std — all in kEUR.
    """
    rng = np.random.default_rng(seed)

    # Extract leaf totals (skip zero-cost rollup rows)
    totals = np.array(
        [w.total_keur for w in wbs if w.total_keur and w.total_keur > 0],
        dtype=float,
    )

    if totals.size == 0:
        return {
            "p50": 0.0, "p70": 0.0, "p80": 0.0, "p90": 0.0,
            "hist": [0] * 20, "hist_bin_edges": [0.0] * 21,
            "mean": 0.0, "std": 0.0,
        }

    # Lognormal: mu = ln(nominal), scale=exp(mu). Shape (n, k).
    mus = np.log(totals)
    samples_per_leaf = rng.lognormal(mean=mus, sigma=sigma, size=(n, totals.size))
    totals_per_sample = samples_per_leaf.sum(axis=1)

    p50, p70, p80, p90 = np.percentile(totals_per_sample, [50, 70, 80, 90])
    hist_counts, bin_edges = np.histogram(totals_per_sample, bins=20)

    return {
        "p50": float(p50),
        "p70": float(p70),
        "p80": float(p80),
        "p90": float(p90),
        "hist": [int(c) for c in hist_counts],
        "hist_bin_edges": [float(e) for e in bin_edges],
        "mean": float(totals_per_sample.mean()),
        "std": float(totals_per_sample.std()),
    }


def _get_subsystem_trl(state: DesignState, subsys: str) -> int:
    """Get TRL for a subsystem from the design state."""
    domain_map = {"eps": "power", "cdh": "data", "ttc": "link", "aocs": "aocs",
                  "structures": "structure", "thermal": "thermal", "propulsion": "propulsion"}
    domain = domain_map.get(subsys, subsys)

    for pid, p in state.parameters.items():
        if p.domain == domain and p.trl is not None:
            return p.trl
    return 7  # Default assumption


def _estimate_launch_cost(wet_mass_kg: float, sc_class: str, mission_type: str = "") -> float:
    """Estimate launch cost from wet mass, spacecraft class, and destination.

    Deep-space missions require dedicated launchers with upper stages,
    which cost significantly more than LEO rideshare regardless of mass.
    """
    # Deep-space missions always need dedicated launch + upper stage
    is_deep_space = mission_type in ("lunar", "mars", "deep_space", "lagrange",
                                      "science_planetary", "interplanetary")
    if is_deep_space:
        if wet_mass_kg < 500:
            return 50000   # Dedicated small launcher + kick stage (Minotaur V class)
        elif wet_mass_kg < 2000:
            return 80000   # Medium launcher (Falcon 9 + star-48 class)
        else:
            return 150000  # Large launcher (Atlas V / Ariane 6 class)

    # LEO / GEO missions
    if wet_mass_kg < 50:
        return 800   # Rideshare (CubeSat deployer)
    elif wet_mass_kg < 300:
        return 2500  # Dedicated small launcher or premium rideshare
    elif wet_mass_kg < 2000:
        return 8000  # Rideshare on medium launcher
    elif wet_mass_kg < 5000:
        return 25000  # Dedicated medium launcher
    else:
        return 70000  # Large launcher


def _estimate_ground_cost(sc_class: str, mission_type: str = "") -> float:
    """Estimate ground system development cost."""
    costs = {"nano": 500, "micro": 1000, "small": 3000, "medium": 8000, "large": 20000, "flagship": 50000}
    base = costs.get(sc_class, 3000)
    # Deep-space ground segment is substantially more complex (nav, planning, DSN interface)
    is_deep_space = mission_type in ("lunar", "mars", "deep_space", "lagrange",
                                      "science_planetary", "interplanetary")
    if is_deep_space:
        base = max(base, 8000) * 2.0  # At least 16 MEUR for deep-space ground segment
    return base


def _monte_carlo_risk(est: CostEstimate, n_samples: int = 1000) -> tuple[float, float, float]:
    """Run Monte Carlo simulation on CER uncertainties.

    Each CER has a lognormal uncertainty with sigma ~0.3 (typical for parametric models).
    Returns (P50, P70, P80) cost values in kEUR.
    """
    random.seed(42)  # Deterministic for reproducibility
    sigma = 0.25  # Log-normal standard deviation

    samples = []
    for _ in range(n_samples):
        total = 0
        for wbs_elem in est.wbs:
            if wbs_elem.total_keur > 0:
                # Apply log-normal uncertainty
                factor = random.lognormvariate(0, sigma)
                total += wbs_elem.total_keur * factor
        samples.append(total)

    samples.sort()
    p50 = samples[int(n_samples * 0.50)]
    p70 = samples[int(n_samples * 0.70)]
    p80 = samples[int(n_samples * 0.80)]
    return round(p50, 0), round(p70, 0), round(p80, 0)
