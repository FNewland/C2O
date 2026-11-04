"""KB electrical and data facts, and the design profile the selected parts imply.

The interface rules used to fall back on spacecraft-class tables whenever a part had no
data (``interface_rules.yaml defaults``: nano → 7.4 V battery bus, I2C, UHF). A CubeSat
built from EOSAT-1-like parts (8S Li-ion battery, CAN OBC and units, S-band transceiver)
would then still get the nanosat defaults. :func:`kb_design_profile` reads the parts that
are actually selected and returns the defaults they imply; the proposer consults it before
the class tables (``interface_proposer._class_default``), so the class tables are only the
last resort.

Kept separate from ``routers/elements._lookup_kb_component`` (the KB → element copy is
another work package): these helpers read the KB entry itself.
"""
from __future__ import annotations

from typing import Any

from spacecdf_common.models.cubesat_standards import (
    NON_DATA_PROTOCOLS,
    component_protocols,
    component_rails_v,
)

#: Battery nominal voltage (V) from which the battery bus is distributed unregulated through
#: the PCDU line switches, as on EOSAT-1 (8S Li-ion, 21.5–29.2 V). C2O default.
HIGH_VOLTAGE_BUS_MIN_V = 20.0

_BAND_ALIASES = {"S-BAND": "S", "X-BAND": "X", "KA-BAND": "KA", "L-BAND": "L", "UHF/VHF": "UHF"}


def kb_voltage_range(kb: dict | None) -> tuple[float | None, float | None, float | None]:
    """``(nominal, min, max)`` V of a KB part (battery ``voltage_v`` {nominal,min,max} or a scalar)."""
    if not kb:
        return None, None, None
    perf = kb.get("performance") or {}
    v = perf.get("voltage_v", kb.get("voltage_v"))
    if isinstance(v, dict):
        def f(x: Any) -> float | None:
            try:
                return float(x)
            except (TypeError, ValueError):
                return None
        return f(v.get("nominal")), f(v.get("min")), f(v.get("max"))
    rails = component_rails_v(kb)
    return (rails[0] if rails else None), None, None


def kb_band(kb: dict | None) -> str | None:
    """RF band of a KB part (``frequency_band`` / ``band`` at top level or in ``performance``)."""
    if not kb:
        return None
    perf = kb.get("performance") or {}
    for src in (kb, perf):
        for key in ("frequency_band", "band", "rf_band"):
            val = src.get(key)
            if isinstance(val, str) and val.strip():
                b = val.strip().upper()
                b = _BAND_ALIASES.get(b, b.replace("-BAND", "").strip())
                return "Ka" if b == "KA" else b
    return None


def kb_data_protocols(kb: dict | None) -> list[str]:
    return [p for p in component_protocols(kb or {}) if p not in NON_DATA_PROTOCOLS]


def kb_output_channels(kb: dict | None) -> int | None:
    v = ((kb or {}).get("performance") or {}).get("output_channels")
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def kb_design_profile(units: list[Any]) -> dict[str, Any]:
    """Defaults implied by the selected KB parts.

    ``units``: objects with ``role``, ``kb`` and ``level`` (``interface_proposer.Unit``).
    Returns any of ``battery_bus_by_class`` (V), ``data_protocol_by_class`` (protocol),
    ``ttc_band_by_class`` (band) — keyed like the ``defaults`` tables they replace — and
    ``unregulated_bus_v`` (the battery bus distributed to loads) plus ``sources``
    (``{key: [kb ids]}``) so the rationale can name the parts.
    """
    out: dict[str, Any] = {}
    sources: dict[str, list[str]] = {}
    comps = [u for u in units if getattr(u, "level", None) == "component" and getattr(u, "kb", None)]

    # Battery bus voltage from the battery part(s)
    for u in comps:
        if u.role != "battery":
            continue
        nom, _, _ = kb_voltage_range(u.kb)
        if nom:
            out["battery_bus_by_class"] = nom
            sources.setdefault("battery_bus_by_class", []).append(str(u.kb.get("id")))
            if nom >= HIGH_VOLTAGE_BUS_MIN_V:
                out["unregulated_bus_v"] = round(nom, 1)
                sources.setdefault("unregulated_bus_v", []).append(str(u.kb.get("id")))
            break

    # TM/TC protocol: CAN when the OBC speaks CAN and at least half of the data units do
    obcs = [u for u in comps if u.role == "obc"]
    data_units = [u for u in comps if u.role not in ("obc",) and kb_data_protocols(u.kb)]
    for proto in ("CAN",):
        if obcs and any(proto in kb_data_protocols(o.kb) for o in obcs) and data_units:
            speak = [u for u in data_units if proto in kb_data_protocols(u.kb)]
            if len(speak) * 2 >= len(data_units):
                out["data_protocol_by_class"] = proto
                sources["data_protocol_by_class"] = [str(u.kb.get("id")) for u in obcs + speak]
                break

    # Space-ground band from the transceiver part
    for u in comps:
        if u.role == "transceiver":
            b = kb_band(u.kb)
            if b:
                out["ttc_band_by_class"] = b
                sources.setdefault("ttc_band_by_class", []).append(str(u.kb.get("id")))
                break

    if sources:
        out["sources"] = sources
    return out
