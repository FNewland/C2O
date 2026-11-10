"""Canonical interface-type vocabulary for SpaceCDF (one enum for the whole tool).

Before November 2026 six vocabularies disagreed (``electrical`` vs ``power``,
``propulsion``, ``software``, ``command``, ``signal`` …; codebase audit §2.6).
This module is the single source. The frontend union
(``frontend/src/types/interfaces.ts``) must list exactly the same values; a
test (``tests/test_services/test_interface_types.py``) keeps the two in step.

The natures follow ECSS-E-ST-10-24C Annex E (informative) where they apply:
``mechanical`` = Structural + Mechanisms, ``data`` = Data representation +
Software + the communication protocol, ``rf`` = Communications. ``timing``
and ``electrical_signal`` are electrical natures split out because a CubeSat
design team reasons about them separately (PPS distribution; deployment
switches, RBF and inhibits from the CubeSat Design Specification rev 14.1).

Old spellings are accepted on input and mapped by :func:`canonical_interface_type`;
an unknown spelling returns ``None`` so callers can reject it (HTTP 400).
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class InterfaceType(str, Enum):
    """The nature of an interface (ECSS-E-ST-10-24C Annex E, adapted)."""

    POWER = "power"                          # Electrical: power rails, battery bus, array input
    DATA = "data"                            # Data representation + software + bus protocol (TM/TC, payload data)
    RF = "rf"                                # Communications: coax, space–ground link
    MECHANICAL = "mechanical"                # Structural + Mechanisms: mounts, deployer, launcher adapter
    THERMAL = "thermal"                      # Thermal control: conductive/radiative paths, heaters
    TIMING = "timing"                        # PPS / onboard clock distribution
    OPTICAL = "optical"                      # Boresight, field of view, keep-out
    FLUID = "fluid"                          # Propulsion / hydraulics: propellant, pressurant
    ELECTRICAL_SIGNAL = "electrical_signal"  # Discretes: deployment switch, RBF, inhibits, release


INTERFACE_TYPE_VALUES: tuple[str, ...] = tuple(t.value for t in InterfaceType)

#: Interface status lifecycle for rule-made baselines (brief, 2 Nov 2026).
INTERFACE_STATUSES: tuple[str, ...] = ("suggested", "accepted", "rejected")

#: Old spellings found in saved studies, imports and the legacy models.
TYPE_ALIASES: dict[str, str] = {
    # power
    "electrical": "power", "eps": "power", "power_bus": "power", "electric": "power",
    # data
    "software": "data", "command": "data", "commands": "data", "tm_tc": "data", "tmtc": "data",
    "telemetry": "data", "bus": "data", "data_bus": "data", "data_representation": "data",
    # rf
    "radio": "rf", "link": "rf", "communications": "rf", "comms": "rf", "rf_link": "rf",
    # mechanical
    "structural": "mechanical", "structure": "mechanical", "mechanisms": "mechanical",
    "mechanism": "mechanical", "mount": "mechanical",
    # timing
    "pps": "timing", "clock": "timing", "time": "timing",
    # fluid
    "propulsion": "fluid", "propellant": "fluid", "pressurant": "fluid", "hydraulics": "fluid",
    "fluidic": "fluid",
    # discrete signals
    "signal": "electrical_signal", "discrete": "electrical_signal", "inhibit": "electrical_signal",
    "electrical-signal": "electrical_signal",
    # thermal / optical are already canonical
    "thermal_control": "thermal", "heat": "thermal", "optics": "optical",
}

#: Subtypes per type (the values the proposer emits; users may add others).
SUBTYPES: dict[str, tuple[str, ...]] = {
    "power": ("regulated", "battery_bus", "switched", "array_input"),
    "data": ("tm_tc", "payload_data", "bus", "csi2", "timing"),   # csi2, timing: W2.07
    "rf": ("coax", "space_ground"),
    "mechanical": ("mount", "deployer", "launcher"),
    "thermal": ("conductive", "radiative", "heater"),
    "timing": ("pps", "clock"),
    "optical": ("boresight", "fov"),
    "fluid": ("propellant", "pressurant"),
    "electrical_signal": ("deployment_switch", "inhibit", "rbf", "release", "umbilical"),
}


def canonical_interface_type(raw: Any) -> str | None:
    """Map any spelling to the canonical value; ``None`` when unknown."""
    if isinstance(raw, InterfaceType):
        return raw.value
    if raw is None:
        return None
    key = str(raw).strip().lower().replace(" ", "_").replace("/", "_")
    if not key:
        return None
    if key in INTERFACE_TYPE_VALUES:
        return key
    if key in TYPE_ALIASES:
        return TYPE_ALIASES[key]
    key2 = key.replace("-", "_")
    if key2 in INTERFACE_TYPE_VALUES:
        return key2
    return TYPE_ALIASES.get(key2)


def coerce_interface_type(raw: Any) -> Any:
    """Pydantic ``BeforeValidator``: map old spellings, leave unknown values for the enum to reject."""
    return canonical_interface_type(raw) or raw


# ── Presentation and Annex E reference data (served by /interfaces/types) ──

def _f(key: str, en: str, fr: str, unit: str | None = None) -> dict[str, Any]:
    return {"key": key, "label": {"en": en, "fr": fr}, "unit": unit}


#: Per type: labels EN/FR, the glyph name the frontend draws, the Annex E
#: nature(s) and the reference-data fields (Annex E attribute lists, cut down to
#: what a CubeSat team fills in). Field keys are the ``properties`` keys.
TYPE_METADATA: dict[str, dict[str, Any]] = {
    "power": {
        "label": {"en": "Power", "fr": "Alimentation"},
        "glyph": "bolt",
        "annex_e": ["Electrical"],
        "fields": [
            _f("rail_voltage", "Rail voltage", "Tension du rail", "V"),
            _f("current_a", "Current", "Courant", "A"),
            _f("power_w", "Power", "Puissance", "W"),
            _f("switched", "Switched (LCL)", "Commutée (LCL)"),
            _f("grounding", "Grounding", "Mise à la masse"),
            _f("connector", "Connector", "Connecteur"),
        ],
    },
    "data": {
        "label": {"en": "Data (TM/TC)", "fr": "Données (TM/TC)"},
        "glyph": "arrows",
        "annex_e": ["Data representation", "Software", "Communications"],
        "fields": [
            _f("protocol", "Protocol", "Protocole"),
            _f("data_rate_bps", "Data rate", "Débit", "bit/s"),
            _f("data_format", "Data format", "Format des données"),
            _f("address", "Bus address", "Adresse sur le bus"),
            _f("endianness", "Endianness", "Boutisme"),
            _f("connector", "Connector", "Connecteur"),
        ],
    },
    "rf": {
        "label": {"en": "RF", "fr": "RF"},
        "glyph": "antenna",
        "annex_e": ["Communications"],
        "fields": [
            _f("band", "Band", "Bande"),
            _f("frequency_mhz", "Frequency", "Fréquence", "MHz"),
            _f("power_dbm", "TX power", "Puissance d'émission", "dBm"),
            _f("polarisation", "Polarisation", "Polarisation"),
            _f("connector", "RF connector", "Connecteur RF"),
        ],
    },
    "mechanical": {
        "label": {"en": "Mechanical", "fr": "Mécanique"},
        "glyph": "nut",
        "annex_e": ["Structural", "Mechanisms"],
        "fields": [
            _f("mount_type", "Mount type", "Type de fixation"),
            _f("fastener", "Fasteners", "Fixations"),
            _f("torque_nm", "Torque", "Couple de serrage", "N·m"),
            _f("envelope_mm", "Envelope", "Enveloppe", "mm"),
            _f("material", "Material", "Matériau"),
        ],
    },
    "thermal": {
        "label": {"en": "Thermal", "fr": "Thermique"},
        "glyph": "waves",
        "annex_e": ["Thermal control"],
        "fields": [
            _f("conductance_w_k", "Conductance", "Conductance", "W/K"),
            _f("heat_flow_w", "Heat flow", "Flux thermique", "W"),
            _f("interface_temp_c", "Interface temperature", "Température d'interface", "°C"),
            _f("contact_area_mm2", "Contact area", "Surface de contact", "mm²"),
            _f("heater_power_w", "Heater power", "Puissance de chauffage", "W"),
        ],
    },
    "timing": {
        "label": {"en": "Timing (PPS)", "fr": "Synchronisation (PPS)"},
        "glyph": "clock",
        "annex_e": ["Electrical"],
        "fields": [
            _f("signal", "Signal", "Signal"),
            _f("accuracy_us", "Accuracy", "Précision", "µs"),
        ],
    },
    "optical": {
        "label": {"en": "Optical", "fr": "Optique"},
        "glyph": "lens",
        "annex_e": ["Optical"],
        "fields": [
            _f("boresight", "Boresight", "Axe de visée"),
            _f("fov_deg", "Field of view", "Champ de vue", "°"),
            _f("keep_out", "Keep-out", "Zone d'exclusion"),
        ],
    },
    "fluid": {
        "label": {"en": "Fluid (propellant)", "fr": "Fluide (ergol)"},
        "glyph": "drop",
        "annex_e": ["Propulsion", "Hydraulics"],
        "fields": [
            _f("medium", "Medium", "Fluide"),
            _f("pressure_bar", "Pressure", "Pression", "bar"),
            _f("fitting", "Fitting", "Raccord"),
        ],
    },
    "electrical_signal": {
        "label": {"en": "Discrete signal", "fr": "Signal discret"},
        "glyph": "square_wave",
        "annex_e": ["Electrical"],
        "fields": [
            _f("signal", "Signal", "Signal"),
            _f("inhibit_count", "Inhibits", "Inhibitions"),
            _f("delay_min", "Delay", "Délai", "min"),
            _f("level", "Level", "Niveau", "V"),
        ],
    },
}

SUBTYPE_LABELS: dict[str, dict[str, str]] = {
    "regulated": {"en": "Regulated rail", "fr": "Rail régulé"},
    "battery_bus": {"en": "Battery bus", "fr": "Bus batterie"},
    "switched": {"en": "Switched rail", "fr": "Rail commuté"},
    "array_input": {"en": "Array input", "fr": "Entrée du générateur solaire"},
    "tm_tc": {"en": "TM/TC", "fr": "TM/TC"},
    "payload_data": {"en": "Payload data", "fr": "Données de charge utile"},
    "bus": {"en": "Bus", "fr": "Bus"},
    "csi2": {"en": "Camera link (MIPI CSI-2)", "fr": "Liaison caméra (MIPI CSI-2)"},
    "timing": {"en": "Time signal", "fr": "Signal de temps"},
    "coax": {"en": "Coax", "fr": "Coaxial"},
    "space_ground": {"en": "Space–ground link", "fr": "Liaison sol–espace"},
    "mount": {"en": "Mount", "fr": "Fixation"},
    "deployer": {"en": "Deployer", "fr": "Déployeur"},
    "launcher": {"en": "Launcher", "fr": "Lanceur"},
    "conductive": {"en": "Conductive", "fr": "Conductif"},
    "radiative": {"en": "Radiative", "fr": "Radiatif"},
    "heater": {"en": "Heater", "fr": "Réchauffeur"},
    "pps": {"en": "PPS", "fr": "PPS"},
    "clock": {"en": "Clock", "fr": "Horloge"},
    "boresight": {"en": "Boresight", "fr": "Axe de visée"},
    "fov": {"en": "Field of view", "fr": "Champ de vue"},
    "propellant": {"en": "Propellant", "fr": "Ergol"},
    "pressurant": {"en": "Pressurant", "fr": "Gaz de pressurisation"},
    "deployment_switch": {"en": "Deployment switch", "fr": "Interrupteur de déploiement"},
    "inhibit": {"en": "Inhibit", "fr": "Inhibition"},
    "rbf": {"en": "Remove-before-flight", "fr": "À retirer avant le vol (RBF)"},
    "release": {"en": "Release", "fr": "Libération"},
    "umbilical": {"en": "Umbilical", "fr": "Ombilical"},
}


def interface_type_catalog() -> list[dict[str, Any]]:
    """The canonical types with labels, glyph, Annex E reference fields and subtypes."""
    out = []
    for t in InterfaceType:
        meta = TYPE_METADATA[t.value]
        out.append({
            "id": t.value,
            "label": dict(meta["label"]),
            "glyph": meta["glyph"],
            "annex_e": list(meta["annex_e"]),
            "standard_ref": "ECSS-E-ST-10-24C Annex E (informative)",
            "fields": [dict(f, label=dict(f["label"])) for f in meta["fields"]],
            "subtypes": [{"id": s, "label": dict(SUBTYPE_LABELS.get(s, {"en": s, "fr": s}))}
                         for s in SUBTYPES[t.value]],
        })
    return out
