"""SpaceCDF — Mission Trade Analysis: Space vs Non-Space.

Before committing to building a spacecraft, this service computes
concrete alternatives with real capability data and scores them
against the mission objectives. Shows WHY space is or isn't needed.

Alternatives considered:
  - Existing satellite data (Copernicus Sentinel-2, Landsat, commercial)
  - Commercial satellite tasking (Planet, Maxar, Airbus)
  - Aerial (drones, crewed aircraft)
  - Ground sensors (IoT, weather stations)
  - New dedicated satellite (what SpaceCDF designs)
  - Hybrid approaches

Each alternative is scored against: coverage, revisit, resolution,
latency, cost, sustainability, control, and longevity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MissionAlternative:
    """A concrete alternative to building a new satellite."""
    name: str
    category: str  # existing_satellite / commercial_tasking / aerial / ground / new_satellite / hybrid
    description: str

    # Capabilities
    coverage: str                 # "global" / "regional" / "local" / "point"
    revisit_days: float           # Best achievable revisit
    gsd_m: float                  # Best achievable ground sample distance
    latency_hours: float          # Data to end user
    spectral_bands: list[str]     # Available spectral bands
    operational_lifetime_years: float

    # Cost
    cost_type: str                # "free" / "subscription" / "per_image" / "capital"
    annual_cost_keur: float       # Annual operating cost

    # Control
    data_ownership: str           # "open" / "licensed" / "owned"
    scheduling_control: str       # "none" / "request" / "full"
    customisation: str            # "none" / "limited" / "full"

    # Defaulted fields
    capital_cost_keur: float = 0  # Upfront investment
    total_3yr_cost_keur: float = 0

    # Scoring
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    meets_objectives: bool = False


# Pre-built alternative database
def _get_alternatives(target_gsd_m: float, target_revisit_days: float,
                      target_bands: list[str] | None = None) -> list[MissionAlternative]:
    """Generate concrete alternatives based on what's actually available."""
    alts = []

    # --- Existing free satellite data ---
    alts.append(MissionAlternative(
        name="Copernicus Sentinel-2 (free)",
        category="existing_satellite",
        description="ESA Sentinel-2A/2B: 10m multispectral, 13 bands, 5-day revisit at equator. "
                    "Free and open data via Copernicus Open Access Hub. Global coverage.",
        coverage="global", revisit_days=5, gsd_m=10, latency_hours=24,
        spectral_bands=["Blue", "Green", "Red", "NIR", "SWIR", "Red Edge"],
        operational_lifetime_years=99,  # Operational service, continuous
        cost_type="free", annual_cost_keur=0, capital_cost_keur=0, total_3yr_cost_keur=0,
        data_ownership="open", scheduling_control="none", customisation="none",
        pros=["Zero cost", "Global coverage", "13 spectral bands", "Well-calibrated", "Long archive",
              "Active user community", "Processing tools available (Google Earth Engine, SNAP)"],
        cons=["5-day revisit (not daily)", "10m resolution (no sub-metre)", "No tasking control",
              "Cloud contamination in tropics", "No customisation of acquisition parameters"],
    ))

    alts.append(MissionAlternative(
        name="Landsat 8/9 (free)",
        category="existing_satellite",
        description="NASA/USGS Landsat: 30m multispectral + 15m pan, 16-day revisit (8 days combined). "
                    "Free data, 50+ year archive continuity.",
        coverage="global", revisit_days=8, gsd_m=30, latency_hours=48,
        spectral_bands=["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "Thermal"],
        operational_lifetime_years=99,
        cost_type="free", annual_cost_keur=0, capital_cost_keur=0, total_3yr_cost_keur=0,
        data_ownership="open", scheduling_control="none", customisation="none",
        pros=["Zero cost", "50+ year archive", "Thermal band", "Well-calibrated"],
        cons=["30m resolution", "16-day revisit (8 combined)", "No tasking"],
    ))

    # --- Commercial satellite tasking ---
    alts.append(MissionAlternative(
        name="Planet SuperDove (commercial subscription)",
        category="commercial_tasking",
        description="Planet Labs constellation: 3m multispectral, daily revisit, global. "
                    "Subscription pricing for archive + tasking.",
        coverage="global", revisit_days=1, gsd_m=3, latency_hours=6,
        spectral_bands=["Blue", "Green", "Red", "NIR", "Red Edge", "Coastal Blue", "Green I", "Yellow"],
        operational_lifetime_years=99,
        cost_type="subscription", annual_cost_keur=50, capital_cost_keur=0, total_3yr_cost_keur=150,
        data_ownership="licensed", scheduling_control="request", customisation="limited",
        pros=["Daily revisit", "3m resolution", "8 bands", "Near-global", "6-hour latency"],
        cons=["50 kEUR/year subscription", "Licensed not owned", "No instrument customisation",
              "Dependent on Planet's business continuity"],
    ))

    alts.append(MissionAlternative(
        name="Maxar WorldView (commercial tasking)",
        category="commercial_tasking",
        description="Maxar WorldView-3: 0.3m pan, 1.2m multispectral. Tasking per image.",
        coverage="regional", revisit_days=1, gsd_m=0.3, latency_hours=4,
        spectral_bands=["Pan", "MS 8-band", "SWIR 8-band", "CAVIS 12-band"],
        operational_lifetime_years=99,
        cost_type="per_image", annual_cost_keur=100, capital_cost_keur=0, total_3yr_cost_keur=300,
        data_ownership="licensed", scheduling_control="request", customisation="limited",
        pros=["0.3m resolution", "28 spectral bands", "Same-day tasking"],
        cons=["Expensive (~$20/km²)", "Licensed data", "Regional coverage per tasking"],
    ))

    # --- Aerial ---
    alts.append(MissionAlternative(
        name="Drone survey (UAV)",
        category="aerial",
        description="Multispectral drone (e.g. DJI Matrice + MicaSense RedEdge): cm-level GSD, "
                    "on-demand, local coverage only.",
        coverage="local", revisit_days=0.1, gsd_m=0.05, latency_hours=1,
        spectral_bands=["Blue", "Green", "Red", "NIR", "Red Edge"],
        operational_lifetime_years=5,
        cost_type="per_image", annual_cost_keur=30, capital_cost_keur=20, total_3yr_cost_keur=110,
        data_ownership="owned", scheduling_control="full", customisation="full",
        pros=["cm-level resolution", "On-demand", "Full ownership", "Low capital cost", "5 spectral bands"],
        cons=["Local coverage only (1-10 km² per flight)", "Weather dependent", "Regulatory constraints",
              "Labour intensive", "Cannot scale to regional/global"],
    ))

    alts.append(MissionAlternative(
        name="Crewed aircraft survey",
        category="aerial",
        description="Aircraft-mounted multispectral/hyperspectral sensor. Regional coverage.",
        coverage="regional", revisit_days=7, gsd_m=0.5, latency_hours=24,
        spectral_bands=["Hyperspectral 200+ bands"],
        operational_lifetime_years=10,
        cost_type="per_image", annual_cost_keur=200, capital_cost_keur=0, total_3yr_cost_keur=600,
        data_ownership="owned", scheduling_control="full", customisation="full",
        pros=["Sub-metre resolution", "Hyperspectral capability", "Regional scale"],
        cons=["Expensive per survey", "Weather dependent", "Not global", "Scheduling lead time"],
    ))

    # --- Ground sensors ---
    alts.append(MissionAlternative(
        name="IoT ground sensor network",
        category="ground",
        description="Distributed soil moisture, temperature, and NDVI sensors. "
                    "Continuous point measurements, IoT-connected.",
        coverage="point", revisit_days=0.01, gsd_m=0, latency_hours=0.1,
        spectral_bands=["NDVI proxy", "Soil moisture", "Temperature"],
        operational_lifetime_years=5,
        cost_type="capital", annual_cost_keur=10, capital_cost_keur=50, total_3yr_cost_keur=80,
        data_ownership="owned", scheduling_control="full", customisation="full",
        pros=["Real-time continuous", "Very low latency", "Full ownership", "Low operating cost"],
        cons=["Point measurements only", "No spatial context", "Requires physical installation",
              "Maintenance burden", "Does not scale to large areas"],
    ))

    # --- New dedicated satellite ---
    # Cost estimate based on class advisor
    if target_gsd_m <= 5:
        sat_cost = 500  # kEUR for a capable nano/micro
    elif target_gsd_m <= 15:
        sat_cost = 300
    else:
        sat_cost = 150

    alts.append(MissionAlternative(
        name="New dedicated CubeSat",
        category="new_satellite",
        description=f"Purpose-built CubeSat with {target_gsd_m:.0f}m GSD instrument, "
                    f"optimised for your specific requirements. Full control over design, "
                    f"data, and operations.",
        coverage="global", revisit_days=max(1, target_revisit_days), gsd_m=target_gsd_m,
        latency_hours=12, spectral_bands=target_bands or ["Custom per requirement"],
        operational_lifetime_years=3,
        cost_type="capital",
        annual_cost_keur=100,  # Operations
        capital_cost_keur=sat_cost * 10,  # 3-10 MEUR depending on class
        total_3yr_cost_keur=sat_cost * 10 + 300,
        data_ownership="owned", scheduling_control="full", customisation="full",
        pros=["Full control", "Custom instrument", "Data ownership", "Educational/capacity value",
              "Technology development", "Independence from commercial providers"],
        cons=[f"Capital cost ~{sat_cost*10} kEUR", "2-3 year development time",
              "Technical risk (especially for new team)", "Operations team needed",
              "Single point of failure (one satellite)"],
    ))

    # --- Hybrid ---
    alts.append(MissionAlternative(
        name="Hybrid: Sentinel-2 + drone validation",
        category="hybrid",
        description="Use free Sentinel-2 data for regional monitoring, validate with periodic "
                    "drone surveys at key sites. Best of both worlds for agricultural monitoring.",
        coverage="global + local validation", revisit_days=5, gsd_m=10,
        latency_hours=24, spectral_bands=["Sentinel-2 13 bands + drone 5 bands"],
        operational_lifetime_years=10,
        cost_type="subscription", annual_cost_keur=30, capital_cost_keur=20, total_3yr_cost_keur=110,
        data_ownership="mixed", scheduling_control="partial", customisation="partial",
        pros=["Low cost", "Global + local", "Ground truth validation", "Operational quickly"],
        cons=["Limited to Sentinel-2 revisit for satellite component", "Drone labour-intensive",
              "Two data sources to integrate"],
    ))

    return alts


def compute_mission_trade(
    target_gsd_m: float = 10.0,
    target_revisit_days: float = 3.0,
    target_coverage: str = "regional",  # global / regional / local
    target_latency_hours: float = 24.0,
    target_bands: list[str] | None = None,
    require_data_ownership: bool = False,
    require_scheduling_control: bool = False,
    max_annual_budget_keur: float = 500.0,
) -> dict[str, Any]:
    """Compute space vs non-space mission trade study.

    Scores each alternative against mission objectives and returns
    a ranked comparison with rationale for why space is or isn't needed.
    """
    alts = _get_alternatives(target_gsd_m, target_revisit_days, target_bands)

    # Score criteria (weights)
    weights = {
        "resolution": 0.20,
        "revisit": 0.20,
        "coverage": 0.15,
        "latency": 0.10,
        "cost": 0.15,
        "control": 0.10,
        "longevity": 0.10,
    }

    coverage_map = {"global": 3, "regional": 2, "local": 1, "point": 0.5,
                    "global + local validation": 2.5}

    for alt in alts:
        # Resolution score
        if alt.gsd_m == 0:  # Ground sensor
            alt.scores["resolution"] = 0.1
        elif alt.gsd_m <= target_gsd_m:
            alt.scores["resolution"] = 1.0
        else:
            alt.scores["resolution"] = max(0, 1.0 - (alt.gsd_m - target_gsd_m) / (target_gsd_m * 3))

        # Revisit score
        if alt.revisit_days <= target_revisit_days:
            alt.scores["revisit"] = 1.0
        else:
            alt.scores["revisit"] = max(0, 1.0 - (alt.revisit_days - target_revisit_days) / (target_revisit_days * 5))

        # Coverage score
        target_cov_val = coverage_map.get(target_coverage, 2)
        alt_cov_val = coverage_map.get(alt.coverage, 1)
        alt.scores["coverage"] = min(1.0, alt_cov_val / max(target_cov_val, 0.1))

        # Latency score
        if alt.latency_hours <= target_latency_hours:
            alt.scores["latency"] = 1.0
        else:
            alt.scores["latency"] = max(0, 1.0 - (alt.latency_hours - target_latency_hours) / 48)

        # Cost score (3-year total vs budget)
        budget_3yr = max_annual_budget_keur * 3
        if alt.total_3yr_cost_keur <= budget_3yr:
            alt.scores["cost"] = 1.0 - (alt.total_3yr_cost_keur / max(budget_3yr, 1)) * 0.5
        else:
            alt.scores["cost"] = max(0, 1.0 - (alt.total_3yr_cost_keur - budget_3yr) / budget_3yr)

        # Control score
        ctrl = 0.0
        if alt.data_ownership == "owned":
            ctrl += 0.4
        elif alt.data_ownership == "open":
            ctrl += 0.3
        if alt.scheduling_control == "full":
            ctrl += 0.3
        elif alt.scheduling_control == "request":
            ctrl += 0.15
        if alt.customisation == "full":
            ctrl += 0.3
        elif alt.customisation == "limited":
            ctrl += 0.15
        alt.scores["control"] = ctrl

        # Penalise if control required but not available
        if require_data_ownership and alt.data_ownership not in ("owned", "open"):
            alt.scores["control"] *= 0.3
        if require_scheduling_control and alt.scheduling_control != "full":
            alt.scores["control"] *= 0.5

        # Longevity score
        alt.scores["longevity"] = min(1.0, alt.operational_lifetime_years / 10)

        # Total
        alt.total_score = sum(alt.scores.get(k, 0) * w for k, w in weights.items())

        # Does it meet objectives?
        alt.meets_objectives = (
            alt.gsd_m <= target_gsd_m * 1.5 and
            alt.revisit_days <= target_revisit_days * 2 and
            alt.total_3yr_cost_keur <= budget_3yr * 1.5
        )

    # Rank
    alts.sort(key=lambda a: a.total_score, reverse=True)

    # Build recommendation
    best = alts[0]
    space_option = next((a for a in alts if a.category == "new_satellite"), None)
    free_option = next((a for a in alts if a.cost_type == "free" and a.meets_objectives), None)

    if free_option and free_option.total_score >= (space_option.total_score if space_option else 0) * 0.9:
        justification = (
            f"Free existing data ({free_option.name}) scores {free_option.total_score:.2f} vs "
            f"new satellite at {space_option.total_score:.2f}. "
            f"QUESTION: Why can't you use {free_option.name}? "
            f"If {free_option.revisit_days}-day revisit and {free_option.gsd_m}m GSD are sufficient, "
            f"a new satellite may not be justified."
        )
        space_justified = False
    elif best.category == "new_satellite":
        justification = (
            f"A new dedicated satellite scores highest ({best.total_score:.2f}). "
            f"No existing alternative fully meets your requirements for "
            f"{target_gsd_m}m GSD with {target_revisit_days}-day revisit."
        )
        space_justified = True
    else:
        justification = (
            f"Best option: {best.name} (score {best.total_score:.2f}). "
            f"A new satellite scores {space_option.total_score:.2f} if space_option is present. "
            f"Consider whether the additional control and customisation of a dedicated mission "
            f"justifies the cost difference."
        )
        space_justified = best.category in ("new_satellite",)

    return {
        "question": "Is space the right answer? What alternatives exist?",
        "inputs": {
            "target_gsd_m": target_gsd_m,
            "target_revisit_days": target_revisit_days,
            "target_coverage": target_coverage,
            "target_latency_hours": target_latency_hours,
            "max_annual_budget_keur": max_annual_budget_keur,
        },
        "alternatives": [
            {
                "rank": i + 1,
                "name": a.name,
                "category": a.category,
                "description": a.description,
                "gsd_m": a.gsd_m,
                "revisit_days": a.revisit_days,
                "coverage": a.coverage,
                "latency_hours": a.latency_hours,
                "cost_type": a.cost_type,
                "annual_cost_keur": a.annual_cost_keur,
                "capital_cost_keur": a.capital_cost_keur,
                "total_3yr_cost_keur": a.total_3yr_cost_keur,
                "data_ownership": a.data_ownership,
                "scheduling_control": a.scheduling_control,
                "pros": a.pros,
                "cons": a.cons,
                "scores": {k: round(v, 2) for k, v in a.scores.items()},
                "total_score": round(a.total_score, 3),
                "meets_objectives": a.meets_objectives,
            }
            for i, a in enumerate(alts)
        ],
        "space_justified": space_justified,
        "justification": justification,
        "key_question": "If free data exists that partially meets your needs, what specifically does a new satellite provide that existing sources cannot?",
    }
