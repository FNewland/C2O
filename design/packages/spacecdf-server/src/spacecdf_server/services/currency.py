"""SpaceCDF — Multi-currency support and NewSpace paradigm cost switches.

All costs are stored internally in EUR (2025 base year). This module provides:
  1. Currency conversion with reference exchange rates
  2. Currency risk bands for multi-year programmes
  3. NewSpace paradigm switches that apply multiplicative factors to WBS elements

Reference rates are approximate 2025 mid-market rates. For live rates,
connect to ECB or Open Exchange Rates API (out of scope for v1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Reference exchange rates: 1 EUR = X foreign currency
# Source: ECB reference rates, approximate 2025 mid-market
EXCHANGE_RATES: dict[str, float] = {
    "EUR": 1.0,
    "USD": 1.08,
    "GBP": 0.86,
    "JPY": 162.0,
    "CHF": 0.96,
    "CAD": 1.47,
    "AUD": 1.66,
    "SEK": 11.2,
    "NOK": 11.5,
    "DKK": 7.46,
    "INR": 90.0,
    "CNY": 7.80,
    "KRW": 1420.0,
    "BRL": 5.40,
    "ZAR": 19.5,
}

# Annual currency volatility (standard deviation of annual log-returns)
# Used for multi-year programme risk bands
_VOLATILITY: dict[str, float] = {
    "EUR": 0.0,
    "USD": 0.08,    # ~8% annual EUR/USD volatility
    "GBP": 0.09,
    "JPY": 0.10,
    "CHF": 0.05,    # Low volatility (quasi-peg periods)
    "CAD": 0.07,
    "AUD": 0.10,
    "INR": 0.06,
    "CNY": 0.04,
    "KRW": 0.08,
    "BRL": 0.14,    # High volatility
    "ZAR": 0.13,
}


@dataclass
class CurrencyConversion:
    """Result of converting a EUR cost to another currency."""
    original_eur: float
    converted: float
    currency: str
    rate: float
    # Risk band for multi-year programmes
    risk_low: float = 0.0     # Optimistic (EUR strengthens)
    risk_high: float = 0.0    # Pessimistic (EUR weakens)
    risk_band_percent: float = 0.0
    programme_years: float = 0.0


def convert_cost(
    cost_eur: float,
    target_currency: str,
    programme_years: float = 0.0,
    confidence: float = 0.90,
) -> CurrencyConversion:
    """Convert a cost from EUR to target currency with optional risk band.

    Args:
        cost_eur: Cost in EUR.
        target_currency: ISO 4217 currency code (e.g. "USD", "GBP").
        programme_years: Programme duration for risk band calculation.
            0 = no risk band (spot conversion only).
        confidence: Confidence level for risk band (0.90 = 90% band).

    Returns:
        CurrencyConversion with converted amount and risk band.
    """
    currency = target_currency.upper()
    rate = EXCHANGE_RATES.get(currency, 1.0)
    converted = cost_eur * rate

    result = CurrencyConversion(
        original_eur=cost_eur,
        converted=round(converted, 2),
        currency=currency,
        rate=rate,
    )

    if programme_years > 0 and currency != "EUR":
        vol = _VOLATILITY.get(currency, 0.08)
        # Multi-year volatility: σ_T = σ_annual × √T
        multi_year_vol = vol * (programme_years ** 0.5)
        # Confidence interval: z-score for the given confidence level
        import math
        # Approximate z for common confidence levels
        z = {0.90: 1.645, 0.95: 1.96, 0.80: 1.28, 0.99: 2.576}.get(confidence, 1.645)
        band = multi_year_vol * z
        result.risk_low = round(converted * (1 - band), 2)
        result.risk_high = round(converted * (1 + band), 2)
        result.risk_band_percent = round(band * 100, 1)
        result.programme_years = programme_years

    return result


# -----------------------------------------------------------------------
# NewSpace paradigm cost switches
# -----------------------------------------------------------------------

@dataclass
class ParadigmSwitch:
    """A selectable cost paradigm that modifies WBS element costs."""
    id: str
    name: str
    description: str
    wbs_targets: list[str]       # WBS IDs or subsystem names this applies to
    factor: float                # Multiplicative factor (< 1 = cost reduction)
    applicable_classes: list[str]  # Spacecraft classes where this makes sense


# Available paradigm switches
PARADIGM_SWITCHES: list[ParadigmSwitch] = [
    ParadigmSwitch(
        id="cots_electronics",
        name="COTS Electronics",
        description="Use commercial off-the-shelf processors, memory, and interfaces instead of rad-hard. "
                    "Requires radiation tolerance analysis and possible shielding.",
        wbs_targets=["cdh", "eps", "aocs"],
        factor=0.30,
        applicable_classes=["nano", "micro", "small"],
    ),
    ParadigmSwitch(
        id="rideshare_launch",
        name="Rideshare Launch",
        description="Share launch vehicle with other payloads instead of dedicated launch. "
                    "Constrains orbit selection and launch timing.",
        wbs_targets=["X.08"],
        factor=0.15,
        applicable_classes=["nano", "micro", "small"],
    ),
    ParadigmSwitch(
        id="agile_pm",
        name="Agile Development",
        description="Agile/iterative project management instead of traditional waterfall. "
                    "Reduces PM and SE overhead but requires experienced team.",
        wbs_targets=["X.01", "X.02"],
        factor=0.60,
        applicable_classes=["nano", "micro", "small", "medium"],
    ),
    ParadigmSwitch(
        id="additive_manufacturing",
        name="3D-Printed Structures",
        description="Additively manufactured primary structure (Ti or Al). "
                    "Reduces part count, lead time, and NRE. Mass-neutral or lighter.",
        wbs_targets=["structures"],
        factor=0.50,
        applicable_classes=["nano", "micro", "small", "medium"],
    ),
    ParadigmSwitch(
        id="commercial_ground",
        name="Commercial Ground Network",
        description="Use commercial ground station networks (KSAT, AWS, Leaf Space) "
                    "instead of dedicated agency ground segment.",
        wbs_targets=["X.09"],
        factor=0.30,
        applicable_classes=["nano", "micro", "small", "medium"],
    ),
    ParadigmSwitch(
        id="digital_twin_ait",
        name="Digital Twin AIT",
        description="Replace physical test campaigns with high-fidelity digital twin "
                    "simulation where possible. Reduces AIT cost and schedule.",
        wbs_targets=["X.10"],
        factor=0.60,
        applicable_classes=["nano", "micro", "small"],
    ),
    ParadigmSwitch(
        id="electric_propulsion",
        name="Electric Propulsion",
        description="Replace chemical propulsion with electric (Hall/ion). "
                    "Higher Isp reduces propellant mass but longer transfer times.",
        wbs_targets=["propulsion"],
        factor=1.50,  # EP hardware costs more, but saves propellant mass
        applicable_classes=["micro", "small", "medium", "large"],
    ),
    ParadigmSwitch(
        id="open_source_sw",
        name="Open-Source Flight Software",
        description="Use open-source frameworks (cFS, COSMOS, FPrime) instead of "
                    "bespoke FSW development. Reduces FSW NRE significantly.",
        wbs_targets=["cdh"],
        factor=0.40,
        applicable_classes=["nano", "micro", "small"],
    ),
]


def apply_paradigm_switches(
    wbs_costs: dict[str, float],
    active_switches: list[str],
    spacecraft_class: str,
) -> tuple[dict[str, float], list[str]]:
    """Apply selected paradigm switches to WBS cost breakdown.

    Args:
        wbs_costs: {wbs_id_or_subsystem: cost_keur}
        active_switches: List of paradigm switch IDs to apply.
        spacecraft_class: Current spacecraft class.

    Returns:
        (modified_costs, applied_descriptions)
    """
    modified = dict(wbs_costs)
    descriptions: list[str] = []

    for switch in PARADIGM_SWITCHES:
        if switch.id not in active_switches:
            continue
        if spacecraft_class not in switch.applicable_classes:
            descriptions.append(f"{switch.name}: not applicable to {spacecraft_class} class")
            continue

        for target in switch.wbs_targets:
            if target in modified:
                original = modified[target]
                modified[target] = original * switch.factor
                saving = original - modified[target]
                descriptions.append(
                    f"{switch.name}: {target} {original:.0f} → {modified[target]:.0f} kEUR "
                    f"(×{switch.factor:.2f}, saving {saving:.0f} kEUR)"
                )

    return modified, descriptions


def list_currencies() -> list[dict[str, Any]]:
    """Return available currencies with rates and volatility."""
    return [
        {
            "code": code,
            "rate_per_eur": rate,
            "annual_volatility_percent": round(_VOLATILITY.get(code, 0.08) * 100, 1),
        }
        for code, rate in sorted(EXCHANGE_RATES.items())
    ]
