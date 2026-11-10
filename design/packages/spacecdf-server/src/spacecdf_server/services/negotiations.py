"""SpaceCDF — negotiation records (wave 3, 3.H6; negotiation support #1). Owner H.

A negotiation record holds what two or more seats must agree when one number is owned by one seat
and consumed, and constrained, by others:

* the **issue** (EN/FR) and the **coupled parameters**: ``key_numbers`` keys (L's registry) plus
  the few H keys below, quoted with their live values on every read;
* the **seats** that must agree, and **one sign-off per seat** (the IF-05 interface-agreement
  pattern). The record is ``agreed`` when every seat has signed the current version; any change of
  the options, the choice or the agreed values clears the sign-offs;
* the **options** with their **computed effects** (the data-budget scenario, the energy balance,
  the roll-up or the allocation ledger: never typed), the chosen option and the agreed values;
* the **reopen trigger**: a text and an optional machine check ``{key, op, value}`` on a live
  parameter (e.g. "compression measured < 1.3:1"); ``trigger.fired`` shows on every read;
* **links** to requirements, risks, trades, RIDs, change proposals and open PI decisions;
* a **history** (who, when, what) in ``data_json``.

Four templates carry the scenes of the Northern Fire and Ice walkthrough; nothing in them names the
mission: their options are computed from the study.

* ``N1`` science volume vs downlink (Payload, Comms & OBDH, Mission analysis, Customer);
* ``N3`` payload peak and imaging duty vs battery and arrays (Payload, Power, Mission analysis,
  Thermal, Systems);
* ``N7`` mass envelopes and the system reserve (Systems and every subsystem seat with a mass line);
* ``GS4`` the ground-station ripple: one more site, and who it affects (Mission analysis, Comms &
  OBDH, Power, Systems).
"""
from __future__ import annotations

import copy
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

STATUSES = ("proposed", "agreed", "reopened")
OPS = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
       "==": lambda a, b: abs(a - b) < 1e-9, "!=": lambda a, b: abs(a - b) >= 1e-9}

#: H's own live keys (beside ``key_numbers``): key -> (unit, owner seat)
EXTRA_KEYS: dict[str, tuple[str, str]] = {
    "data.compression_ratio": (":1", "payload_lead"),
    "data.compression_needed": (":1", "payload_lead"),
    "data.science_raw_mb_per_day": ("MB/day", "payload_lead"),
    "data.largest_science_10pct_mb_per_day": ("MB/day", "comms_engineer"),
    "data.allocatable_mb_per_day": ("MB/day", "comms_engineer"),
    "power.orbit_average_cbe_w": ("W", "power_engineer"),
    "power.imaging_mode_w": ("W", "payload_lead"),
    "power.dod_percent": ("%", "power_engineer"),
    "power.worst_eclipse_dod_percent": ("%", "power_engineer"),
    "power.eol_generation_w": ("W", "power_engineer"),
    "modes.imaging_share": ("", "mission_analyst"),
    "modes.downlink_share": ("", "mission_analyst"),
}

LABELS: dict[str, dict[str, str]] = {
    "mass.cbe_kg": {"en": "Mass, current best estimate", "fr": "Masse, meilleure estimation actuelle"},
    "mass.with_maturity_kg": {"en": "Mass with maturity margins", "fr": "Masse avec marges de maturité"},
    "mass.with_system_margin_kg": {"en": "Mass with system margin", "fr": "Masse avec marge système"},
    "mass.system_margin_percent": {"en": "System mass margin", "fr": "Marge système de masse"},
    "mass.limit_kg": {"en": "Mass limit", "fr": "Masse limite"},
    "mass.margin_to_limit_kg": {"en": "Margin to the mass limit", "fr": "Marge à la masse limite"},
    "power.orbit_average_w": {"en": "Orbit-average power (CBE)", "fr": "Puissance moyenne orbitale (MEA)"},
    "power.orbit_average_with_margin_w": {"en": "Orbit-average power with margins", "fr": "Puissance moyenne orbitale avec marges"},
    "power.orbit_average_cbe_w": {"en": "Orbit-average load of the mode mix (CBE)", "fr": "Charge moyenne orbitale du mélange de modes (MEA)"},
    "power.imaging_mode_w": {"en": "Imaging mode power (CBE)", "fr": "Puissance du mode imagerie (MEA)"},
    "power.dod_percent": {"en": "Depth of discharge, operational orbit", "fr": "Profondeur de décharge, orbite opérationnelle"},
    "power.worst_eclipse_dod_percent": {"en": "Depth of discharge, longest eclipse", "fr": "Profondeur de décharge, éclipse la plus longue"},
    "power.eol_generation_w": {"en": "End-of-life array power", "fr": "Puissance des panneaux en fin de vie"},
    "data.capacity_mb_per_day": {"en": "Downlink capacity", "fr": "Capacité de transmission"},
    "data.demand_mb_per_day": {"en": "Daily demand", "fr": "Demande quotidienne"},
    "data.margin_pct": {"en": "Daily data margin", "fr": "Marge quotidienne de données"},
    "data.science_delivered_mb_per_day": {"en": "Science delivered", "fr": "Science livrée"},
    "data.science_raw_mb_per_day": {"en": "Science before compression", "fr": "Science avant compression"},
    "data.compression_ratio": {"en": "Lossless compression ratio", "fr": "Taux de compression sans perte"},
    "data.compression_needed": {"en": "Compression needed for the target", "fr": "Compression nécessaire pour la cible"},
    "data.largest_science_10pct_mb_per_day": {"en": "Largest science with 10 % margin", "fr": "Science maximale avec 10 % de marge"},
    "data.allocatable_mb_per_day": {"en": "Allocatable capacity", "fr": "Capacité allouable"},
    "contacts.union_min_per_day": {"en": "Contact, union of the passes", "fr": "Contact, union des passages"},
    "modes.imaging_share": {"en": "Imaging share of the orbit", "fr": "Part de l’orbite en imagerie"},
    "modes.downlink_share": {"en": "Downlink share of the orbit", "fr": "Part de l’orbite en liaison descendante"},
}

SUBSYSTEM_SEATS = ("payload_lead", "power_engineer", "aocs_engineer", "comms_engineer", "thermal_engineer",
                   "structures_engineer", "propulsion_engineer")


def _bi(en: str, fr: str) -> dict[str, str]:
    return {"en": en, "fr": fr}


TEMPLATES: dict[str, dict[str, Any]] = {
    "N1": {
        "issue": _bi("Science volume against the downlink: how many MB per day of compressed products, at which compression and margin?",
                     "Volume scientifique contre liaison descendante : combien de Mo par jour de produits compressés, à quelle compression et quelle marge ?"),
        "parameters": ["data.science_delivered_mb_per_day", "data.compression_ratio", "data.compression_needed",
                       "data.capacity_mb_per_day", "data.margin_pct", "data.largest_science_10pct_mb_per_day",
                       "contacts.union_min_per_day"],
        "seats": ["payload_lead", "comms_engineer", "mission_analyst", "customer"],
        "reopen": {"text": _bi("Reopen if the compression measured on simulated scenes is below 1.3:1",
                               "Rouvrir si la compression mesurée sur des scènes simulées est inférieure à 1,3:1"),
                   "condition": {"key": "data.compression_ratio", "op": "<", "value": 1.3}},
        "links": {"requirements": ["PAY-DAT-01", "PAY-FUN-03", "SYS-BUD-05", "SEG-GS-01"], "risks": ["RSK-008"],
                  "trades": [], "rids": [], "changes": [], "decisions": ["D-PI-01", "D-PI-02"]},
    },
    "N3": {
        "issue": _bi("Payload peak power and imaging duty against the battery, the arrays and operations: which share of the orbit may the payload image, under which flight rules?",
                     "Puissance de crête de la charge utile et taux d’imagerie contre batterie, panneaux et exploitation : quelle part de l’orbite en imagerie, sous quelles règles de vol ?"),
        "parameters": ["power.imaging_mode_w", "power.orbit_average_cbe_w", "power.eol_generation_w", "power.dod_percent",
                       "power.worst_eclipse_dod_percent", "modes.imaging_share", "data.margin_pct"],
        "seats": ["payload_lead", "power_engineer", "mission_analyst", "thermal_engineer", "systems_engineer"],
        "reopen": {"text": _bi("Reopen if the measured payload peak exceeds the 12 W budget or the worst-eclipse depth of discharge exceeds 15 %",
                               "Rouvrir si la crête mesurée de la charge utile dépasse le budget de 12 W ou si la décharge de la pire éclipse dépasse 15 %"),
                   "condition": {"key": "power.worst_eclipse_dod_percent", "op": ">", "value": 15.0}},
        "links": {"requirements": ["SYS-BUD-03", "SYS-BUD-04", "SYS-BUD-10", "EPS-BAT-01"], "risks": ["RSK-003"],
                  "trades": ["T-04", "T-05"], "rids": [], "changes": [], "decisions": []},
    },
    "N7": {
        "issue": _bi("Mass envelopes: the allocation of each subsystem, the system margin held and the reserve kept by Systems",
                     "Enveloppes de masse : l’allocation de chaque sous-système, la marge système tenue et la réserve gardée par l’ingénierie système"),
        "parameters": ["mass.cbe_kg", "mass.with_maturity_kg", "mass.with_system_margin_kg", "mass.system_margin_percent",
                       "mass.limit_kg", "mass.margin_to_limit_kg"],
        "seats": ["systems_engineer", *SUBSYSTEM_SEATS],
        "reopen": {"text": _bi("Reopen if the margin to the mass limit falls below 0.3 kg",
                               "Rouvrir si la marge à la masse limite tombe sous 0,3 kg"),
                   "condition": {"key": "mass.margin_to_limit_kg", "op": "<", "value": 0.3}},
        "links": {"requirements": ["SYS-BUD-01", "SYS-BUD-02", "SYS-BUD-09"], "risks": ["RSK-024", "RSK-032"],
                  "trades": ["T-05"], "rids": [], "changes": [], "decisions": []},
    },
    "GS4": {
        "issue": _bi("One more ground station: the contact it adds, and every seat it affects (capacity, downlink share, power, allocations)",
                     "Une station sol de plus : le contact qu’elle ajoute et chaque poste qu’elle touche (capacité, part de liaison descendante, puissance, allocations)"),
        "parameters": ["contacts.union_min_per_day", "data.capacity_mb_per_day", "data.margin_pct", "modes.downlink_share",
                       "power.orbit_average_cbe_w"],
        "seats": ["mission_analyst", "comms_engineer", "power_engineer", "systems_engineer"],
        "reopen": {"text": _bi("Reopen if the union of the passes falls below 100 min per day (a site lost)",
                               "Rouvrir si l’union des passages tombe sous 100 min par jour (un site perdu)"),
                   "condition": {"key": "contacts.union_min_per_day", "op": "<", "value": 100.0}},
        "links": {"requirements": ["SEG-GS-01", "SEG-GS-02", "SYS-BUD-05", "SYS-BUD-10"], "risks": ["RSK-008", "RSK-023"],
                  "trades": [], "rids": [], "changes": [], "decisions": []},
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _r(v: Any, n: int = 2) -> Any:
    return round(float(v), n) if isinstance(v, (int, float)) and not isinstance(v, bool) else v


# ───────────────────────────────────────────────────────────── live parameter values

async def live_values(study_id: str, keys: list[str] | None = None) -> dict[str, dict[str, Any]]:
    """``key_numbers`` (L) plus H's extra keys, for the keys asked (all when ``None``)."""
    out: dict[str, dict[str, Any]] = {}
    try:
        from .key_numbers import key_numbers
        out.update(await key_numbers(study_id))
    except Exception:  # noqa: BLE001
        logger.debug("negotiations: key numbers failed for %s", study_id, exc_info=True)
    want = set(keys) if keys is not None else set(EXTRA_KEYS)
    need = {k for k in want if k in EXTRA_KEYS and k not in out}
    if need:
        out.update(await _extra_values(study_id, need))
    for k, v in out.items():
        v.setdefault("label", LABELS.get(k, {"en": k, "fr": k}))
    return out if keys is None else {k: out.get(k) or {"value": None, "unit": "", "source": "unknown", "owner_seat": "",
                                                       "label": LABELS.get(k, {"en": k, "fr": k})} for k in keys}


async def _extra_values(study_id: str, keys: set[str]) -> dict[str, dict[str, Any]]:
    vals: dict[str, Any] = {}
    src: dict[str, str] = {}
    if any(k.startswith("data.") for k in keys):
        try:
            from . import data_budget as dbs
            from .sensitivity import largest_science
            b = await dbs.for_study(study_id, include_degraded=False)
            sci, cap = b.get("science") or {}, b.get("capacity") or {}
            vals.update({"data.compression_ratio": sci.get("compression_ratio"), "data.compression_needed": sci.get("compression_needed"),
                         "data.science_raw_mb_per_day": sci.get("raw_mb_per_day"),
                         "data.largest_science_10pct_mb_per_day": largest_science(b, 10.0),
                         "data.allocatable_mb_per_day": cap.get("allocatable_mb_per_day")})
            src.update({k: "data_budget" for k in vals})
        except Exception:  # noqa: BLE001
            logger.debug("negotiations: data budget failed", exc_info=True)
    if any(k.startswith(("power.", "modes.")) for k in keys):
        try:
            from ..routers.modes import mode_energy
            en = await mode_energy(study_id, gate=None)
            ops = en.get("operational_orbit") or {}
            img = next((m for m in en.get("modes") or [] if m.get("kind") == "imaging"), None)
            fr = {m["name"]: m.get("orbit_fraction") for m in ops.get("modes") or []}
            mode_by_kind = {m.get("kind"): m.get("name") for m in en.get("modes") or []}
            worst = ((en.get("season") or {}).get("worst_eclipse_orbit") or {})
            vals.update({"power.orbit_average_cbe_w": ops.get("orbit_average_cbe_w"),
                         "power.imaging_mode_w": (img or {}).get("power_cbe_w"), "power.dod_percent": ops.get("dod_percent"),
                         "power.worst_eclipse_dod_percent": worst.get("dod_percent"),
                         "power.eol_generation_w": (en.get("inputs") or {}).get("sa_power_eol_w"),
                         "modes.imaging_share": fr.get(mode_by_kind.get("imaging")),
                         "modes.downlink_share": fr.get(mode_by_kind.get("downlink"))})
            src.update({k: "mode_energy" for k in vals if k.startswith(("power.", "modes."))})
        except Exception:  # noqa: BLE001
            logger.debug("negotiations: mode energy failed", exc_info=True)
    return {k: {"value": _r(vals.get(k), 4), "unit": EXTRA_KEYS[k][0], "source": src.get(k, "unknown"), "owner_seat": EXTRA_KEYS[k][1]}
            for k in keys}


# ───────────────────────────────────────────────────────────── computed options

async def compute_options(code: str, study_id: str) -> list[dict[str, Any]]:
    """The options of a template, each with its computed ``effects`` (never typed)."""
    from . import sensitivity as sv
    at = _now()
    if code == "N1":
        probe = await sv.science_options(study_id, [])
        target = probe.get("baseline_target_mb_per_day") or 13.0
        big = round(probe["largest_with_margin_mb_per_day"], 1) if probe.get("largest_with_margin_mb_per_day") else None
        fb = round(probe["largest_with_margin_at_fallback_mb_per_day"], 1) if probe.get("largest_with_margin_at_fallback_mb_per_day") else None
        vals = [v for v in [target, big, fb] if v]
        res = await sv.science_options(study_id, sorted(set(round(v, 1) for v in vals)))
        by = {o["science_mb_per_day"]: o for o in res["options"]}
        rate, frate = res.get("rate_bps") or 0, res.get("fallback_rate_bps")
        opts = []
        if target:
            opts.append({"key": "keep", "label": _bi(f"Keep {target:g} MB/day: robust to losing a site",
                                                    f"Garder {target:g} Mo/j : robuste à la perte d’un site"),
                         "values": {"data.science_delivered_mb_per_day": target}, "effects": by.get(round(target, 1))})
        if big:
            opts.append({"key": "raise", "label": _bi(f"Raise to {big:g} MB/day: the largest with 10 % margin at {rate / 1000:g} kbit/s",
                                                     f"Monter à {big:g} Mo/j : le maximum avec 10 % de marge à {rate / 1000:g} kbit/s"),
                         "values": {"data.science_delivered_mb_per_day": big}, "effects": by.get(round(big, 1))})
        if fb and frate:
            opts.append({"key": "fallback", "label": _bi(f"Lower to {fb:g} MB/day: closes with 10 % margin at the {frate / 1000:g} kbit/s fallback",
                                                        f"Baisser à {fb:g} Mo/j : boucle avec 10 % de marge au débit de repli de {frate / 1000:g} kbit/s"),
                         "values": {"data.science_delivered_mb_per_day": fb}, "effects": by.get(round(fb, 1))})
        for o in opts:
            need = (res.get("compression_needed") or 0) * o["values"]["data.science_delivered_mb_per_day"] / target \
                if res.get("compression_needed") and target else None
            # compression the option needs on the planned product set (1.0 = none)
            o["effects"] = {**(o["effects"] or {}), "compression_needed": _r(max(1.0, need), 3) if need else None}
    elif code == "N3":
        res = await sv.imaging_options(study_id, [])
        f0 = res.get("baseline_share") or 0.05
        alt = round(max(f0 * 1.6, f0 + 0.03), 3)
        res = await sv.imaging_options(study_id, [f0, alt])
        by = {round(p["x"], 3): p for p in res["options"]}
        keep = {k: v for k, v in (by.get(round(f0, 3)) or {}).items() if k != "x"}
        more = {k: v for k, v in (by.get(alt) or {}).items() if k != "x"}
        opts = [{"key": "keep", "label": _bi(f"Imaging {100 * f0:.0f} % of the orbit; imaging only above 40 % state of charge; no transmission during an acquisition",
                                             f"Imagerie {100 * f0:.0f} % de l’orbite ; imagerie seulement au-dessus de 40 % de charge ; pas d’émission pendant une acquisition"),
                 "values": {"modes.imaging_share": f0}, "effects": keep,
                 "flight_rules": ["no TX during an acquisition", "imaging only at state of charge >= 40 %"]},
                {"key": "more", "label": _bi(f"Imaging {100 * alt:.0f} % of the orbit (more acquisitions, products scale with them)",
                                             f"Imagerie {100 * alt:.0f} % de l’orbite (plus d’acquisitions, les produits suivent)"),
                 "values": {"modes.imaging_share": alt}, "effects": more}]
    elif code == "N7":
        alloc, basis = await _mass_allocations(study_id)
        from . import rollup
        m = (await rollup.compute(study_id, gate="pdr")).as_dict().get("mass") or {}     # the envelopes hold to PDR
        lim, held, ladder = m.get("limit_kg"), m.get("system_margin_percent"), m.get("ladder_percent")
        opts = []
        for key, pct, en, fr in (("hold", held, "Hold the {p:g} % system margin through PDR (study hold)",
                                  "Tenir la marge système de {p:g} % jusqu’à la RDP (réserve de l’étude)"),
                                 ("ladder", ladder, "Use the {p:g} % margin of the ladder at PDR",
                                  "Prendre la marge de {p:g} % de l’échelle à la RDP")):
            if pct is None or any(o["values"]["mass.system_margin_percent"] == pct for o in opts):
                continue
            total = alloc * (1 + pct / 100.0) if alloc is not None else None
            opts.append({"key": key, "label": _bi(en.format(p=pct), fr.format(p=pct)),
                         "values": {"mass.system_margin_percent": pct},
                         "effects": {"allocations_kg": _r(alloc, 3), "allocations_basis": basis, "with_margin_kg": _r(total, 3),
                                     "limit_kg": lim, "reserve_kg": _r(lim - total, 3) if (lim is not None and total is not None) else None,
                                     "closes": (total <= lim) if (lim is not None and total is not None) else None}})
    elif code == "GS4":
        res = await sv.station_options(study_id)
        opts = []
        for o in res.get("options") or []:
            if o["key"] == "without":
                lab = _bi(f"{len(o['stations'])} sites, without {o['left_out']}", f"{len(o['stations'])} sites, sans {o['left_out']}")
            else:
                lab = _bi(f"{len(o['stations'])} sites" + (f", with {res['station']}" if res.get("station") else ""),
                          f"{len(o['stations'])} sites" + (f", avec {res['station']}" if res.get("station") else ""))
            opts.append({"key": o["key"], "label": lab, "values": {"contacts.union_min_per_day": o["union_min_per_day"],
                                                                   "modes.downlink_share": o["downlink_share"]},
                         "effects": {k: v for k, v in o.items() if k not in ("key",)}})
        if len(opts) == 2:
            a, b = opts[0]["effects"], opts[1]["effects"]
            opts[1]["delta"] = {k: _r((b.get(k) or 0) - (a.get(k) or 0), 3) for k in
                                ("union_min_per_day", "capacity_mb_per_day", "margin_c1_pct", "downlink_share", "orbit_average_cbe_w")
                                if b.get(k) is not None and a.get(k) is not None}
            opts[1]["affects"] = [{"seat": "comms_engineer", "what": _bi("downlink capacity and per-pass allowances", "capacité de transmission et allocations par passage")},
                                  {"seat": "power_engineer", "what": _bi("downlink share and orbit-average power", "part de liaison descendante et puissance moyenne orbitale")},
                                  {"seat": "systems_engineer", "what": _bi("the power allocation of the communications line", "l’allocation de puissance de la ligne communications")},
                                  {"seat": "mission_analyst", "what": _bi("the contact plan and the longest gap", "le plan de contact et la plus longue interruption")}]
    else:
        return []
    for o in opts:
        o["computed_at"] = at
    return opts


async def _mass_allocations(study_id: str) -> tuple[float | None, str]:
    """Σ mass allocations from the allocation ledger (A), else the roll-up with maturity margins."""
    try:
        from sqlalchemy import select

        from ..db.engine import get_session_factory
        from ..db.models_alloc import AllocationLedgerRow
        async with get_session_factory()() as s:
            rows = (await s.execute(select(AllocationLedgerRow).where(AllocationLedgerRow.study_id == study_id,
                                                                      AllocationLedgerRow.budget_type == "mass"))).scalars().all()
        lines = [r for r in rows if (r.line_kind or "allocation") == "allocation" and r.value is not None]
        if lines:
            return sum(float(r.value) for r in lines), "allocation_ledger"
    except Exception:  # noqa: BLE001
        logger.debug("negotiations: ledger unavailable", exc_info=True)
    kn = await live_values(study_id, ["mass.with_maturity_kg"])
    return kn["mass.with_maturity_kg"]["value"], "rollup.with_maturity_kg"


# ───────────────────────────────────────────────────────────── persistence

def to_dict(row) -> dict[str, Any]:
    d = row.data_json or {}
    return {"id": row.id, "study_id": row.study_id, "code": row.code, "issue": {"en": row.issue or "", "fr": row.issue_fr or ""},
            "parameters": list(row.parameters_json or []), "seats": list(row.seats_json or []),
            "options": list(row.options_json or []), "agreed": dict(row.agreed_json or {}),
            "signoffs": dict(row.signoffs_json or {}), "reopen_trigger": row.reopen_trigger or "",
            "reopen_trigger_fr": d.get("reopen_trigger_fr") or "", "reopen_condition": d.get("reopen_condition"),
            "links": dict(row.links_json or {}), "status": row.status or "proposed", "chosen_option": d.get("chosen_option"),
            "template": d.get("template"), "version": int(d.get("version") or 1), "history": list(d.get("history") or []),
            "agreed_at": d.get("agreed_at"), "agreed_snapshot": d.get("agreed_snapshot"), "origin": row.origin, "order": row.order,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None}


async def list_records(study_id: str) -> list[dict[str, Any]]:
    from sqlalchemy import select

    from ..db.engine import get_session_factory
    from ..db.models_negotiation import NegotiationRecordRow
    async with get_session_factory()() as s:
        rows = (await s.execute(select(NegotiationRecordRow).where(NegotiationRecordRow.study_id == study_id)
                                .order_by(NegotiationRecordRow.order, NegotiationRecordRow.created_at))).scalars().all()
        return [to_dict(r) for r in rows]


async def get_record(study_id: str, record_id: str) -> dict[str, Any] | None:
    from ..db.engine import get_session_factory
    from ..db.models_negotiation import NegotiationRecordRow
    async with get_session_factory()() as s:
        row = await s.get(NegotiationRecordRow, record_id)
        if row is None or row.study_id != study_id:
            return None
        return to_dict(row)


async def _mutate(study_id: str, record_id: str, fn) -> dict[str, Any] | None:
    from sqlalchemy.orm.attributes import flag_modified

    from ..db.engine import get_session_factory
    from ..db.models_negotiation import NegotiationRecordRow
    async with get_session_factory()() as s:
        row = await s.get(NegotiationRecordRow, record_id)
        if row is None or row.study_id != study_id:
            return None
        fn(row)
        for col in ("data_json", "signoffs_json", "options_json", "agreed_json", "links_json", "seats_json", "parameters_json"):
            flag_modified(row, col)
        await s.commit()
        await s.refresh(row)
        return to_dict(row)


def _log(row, by: str, action: str, detail: dict | None = None) -> None:
    d = dict(row.data_json or {})
    d["history"] = [*(d.get("history") or []), {"at": _now(), "by": by or "", "action": action, **(detail or {})}]
    row.data_json = d


async def create(study_id: str, body: dict[str, Any], *, by: str = "") -> dict[str, Any]:
    """From a template (``{"template": "N1"}``) with computed options, or from the fields given."""
    from ..db.engine import get_session_factory
    from ..db.models_negotiation import NegotiationRecordRow
    tpl_code = body.get("template")
    tpl = copy.deepcopy(TEMPLATES.get(tpl_code) or {}) if tpl_code else {}
    if tpl_code and not tpl:
        raise ValueError(f"unknown template {tpl_code}; known: {', '.join(TEMPLATES)}")
    seats = list(body.get("seats") or tpl.get("seats") or [])
    if not seats:
        raise ValueError("a negotiation needs at least two seats")
    _check_seats(seats)
    options = body.get("options")
    if options is None and tpl_code:
        options = await compute_options(tpl_code, study_id)
    issue = body.get("issue") or tpl.get("issue") or {}
    if isinstance(issue, str):
        issue = {"en": issue, "fr": body.get("issue_fr") or ""}
    reopen = tpl.get("reopen") or {}
    rt = body.get("reopen_trigger")
    if isinstance(rt, str):
        rt_text, rt_fr = rt, str(body.get("reopen_trigger_fr") or "")
    else:
        txt = (rt if isinstance(rt, dict) else None) or reopen.get("text") or {}
        rt_text, rt_fr = str(txt.get("en", "")), str(body.get("reopen_trigger_fr") or txt.get("fr", ""))
    cond = body.get("reopen_condition", reopen.get("condition"))
    _check_condition(cond)
    existing = await list_records(study_id)
    code = str(body.get("code") or tpl_code or f"N{len(existing) + 1}")[:16]
    row = NegotiationRecordRow(
        id=uuid.uuid4().hex, study_id=study_id, code=code, issue=issue.get("en", ""), issue_fr=issue.get("fr", ""),
        parameters_json=list(body.get("parameters") or tpl.get("parameters") or []), seats_json=seats,
        options_json=list(options or []), agreed_json=dict(body.get("agreed") or {}), signoffs_json={},
        reopen_trigger=rt_text, links_json=dict(body.get("links") or tpl.get("links") or {}), status="proposed",
        data_json={"template": tpl_code, "reopen_trigger_fr": rt_fr, "reopen_condition": cond, "version": 1,
                   "chosen_option": body.get("chosen_option"),
                   "history": [{"at": _now(), "by": by, "action": "created", "template": tpl_code}]},
        origin=str(body.get("origin") or ("template" if tpl_code else "user"))[:16], order=len(existing))
    async with get_session_factory()() as s:
        s.add(row)
        await s.commit()
        await s.refresh(row)
        return to_dict(row)


def _check_seats(seats: list[str]) -> None:
    from ..seats import config as seat_cfg
    known = set(seat_cfg.seat_ids())
    bad = [x for x in seats if x not in known]
    if bad:
        raise ValueError(f"unknown seat(s): {', '.join(bad)}")
    if len(set(seats)) < 2:
        raise ValueError("a negotiation needs at least two seats")


def _check_condition(cond: Any) -> None:
    if cond in (None, {}):
        return
    if not isinstance(cond, dict) or cond.get("op") not in OPS or not cond.get("key") or \
            not isinstance(cond.get("value"), (int, float)):
        raise ValueError("reopen_condition must be {key, op (<, <=, >, >=, ==, !=), value (number)}")


PATCHABLE = ("issue", "issue_fr", "parameters", "seats", "options", "agreed", "chosen_option", "reopen_trigger",
             "reopen_trigger_fr", "reopen_condition", "links")
#: changes that void the sign-offs (what the seats signed is no longer what the record says)
SUBSTANTIVE = ("parameters", "seats", "options", "agreed", "chosen_option", "reopen_condition")


async def update(study_id: str, record_id: str, body: dict[str, Any], *, by: str = "") -> dict[str, Any] | None:
    unknown = [k for k in body if k not in PATCHABLE and k not in ("recompute_options", "by")]
    if unknown:
        raise ValueError(f"unknown field(s): {', '.join(unknown)}")
    if "seats" in body:
        _check_seats(list(body["seats"] or []))
    if "reopen_condition" in body:
        _check_condition(body["reopen_condition"])
    cur = await get_record(study_id, record_id)
    if cur is None:
        return None
    new_opts = None
    if body.get("recompute_options") and cur.get("template"):
        new_opts = await compute_options(cur["template"], study_id)
    if "chosen_option" in body and body["chosen_option"] is not None:
        keys = {o.get("key") for o in (body.get("options") or new_opts or cur["options"])}
        if body["chosen_option"] not in keys:
            raise ValueError(f"chosen_option must be one of {', '.join(str(k) for k in keys)}")

    def apply(row) -> None:
        d = dict(row.data_json or {})
        changed = []
        for k in PATCHABLE:
            if k not in body:
                continue
            v = body[k]
            if k == "issue":
                if isinstance(v, dict):
                    row.issue, row.issue_fr = v.get("en", row.issue), v.get("fr", row.issue_fr)
                else:
                    row.issue = str(v or "")
            elif k == "issue_fr":
                row.issue_fr = str(v or "")
            elif k == "parameters":
                row.parameters_json = list(v or [])
            elif k == "seats":
                row.seats_json = list(v or [])
                row.signoffs_json = {s: x for s, x in (row.signoffs_json or {}).items() if s in row.seats_json}
            elif k == "options":
                row.options_json = list(v or [])
            elif k == "agreed":
                row.agreed_json = dict(v or {})
            elif k == "chosen_option":
                d["chosen_option"] = v
                opt = next((o for o in (row.options_json or []) if o.get("key") == v), None)
                if opt is not None and "agreed" not in body:
                    row.agreed_json = dict(opt.get("values") or {})
            elif k == "reopen_trigger":
                row.reopen_trigger = str(v or "")
            elif k == "reopen_trigger_fr":
                d["reopen_trigger_fr"] = str(v or "")
            elif k == "reopen_condition":
                d["reopen_condition"] = v
            elif k == "links":
                row.links_json = dict(v or {})
            changed.append(k)
        if new_opts is not None:
            row.options_json = new_opts
            changed.append("options")
        substantive = [k for k in changed if k in SUBSTANTIVE]
        row.data_json = d
        if substantive:
            d["version"] = int(d.get("version") or 1) + 1
            if row.signoffs_json:
                row.signoffs_json = {}
                changed.append("signoffs cleared")
            if row.status == "agreed":
                row.status = "proposed"
        row.data_json = d
        _log(row, by, "updated", {"fields": changed})
    return await _mutate(study_id, record_id, apply)


async def sign(study_id: str, record_id: str, seat: str, *, agree: bool = True, by: str = "", note: str = "") -> dict[str, Any]:
    """One sign-off per seat. ``agreed`` once every seat has signed this version."""
    cur = await get_record(study_id, record_id)
    if cur is None:
        raise LookupError(record_id)
    if seat not in cur["seats"]:
        raise PermissionError(f"{seat} is not a party to this negotiation ({', '.join(cur['seats'])})")
    if agree and not (cur.get("chosen_option") or cur.get("agreed")):
        raise RuntimeError("Choose an option or record the agreed values before signing")
    snap = None
    if agree:
        remaining = [s for s in cur["seats"] if s != seat and s not in cur["signoffs"]]
        if not remaining:
            vals = await live_values(study_id, cur["parameters"]) if cur["parameters"] else {}
            snap = {k: (v or {}).get("value") for k, v in vals.items()}

    def apply(row) -> None:
        so = dict(row.signoffs_json or {})
        d = dict(row.data_json or {})
        if agree:
            so[seat] = {"by": by, "at": _now(), "version": int(d.get("version") or 1), "note": note or ""}
        else:
            so.pop(seat, None)
        row.signoffs_json = so
        if all(s in so for s in (row.seats_json or [])):
            row.status = "agreed"
            d["agreed_at"] = _now()
            d["agreed_snapshot"] = snap if snap is not None else d.get("agreed_snapshot")
        elif row.status == "agreed":
            row.status = "proposed"
        row.data_json = d
        _log(row, by, "signed" if agree else "withdrew", {"seat": seat, "note": note or ""})
    out = await _mutate(study_id, record_id, apply)
    assert out is not None
    return out


async def reopen(study_id: str, record_id: str, *, reason: str, by: str = "") -> dict[str, Any] | None:
    if not (reason or "").strip():
        raise ValueError("Reopening needs a reason")

    def apply(row) -> None:
        d = dict(row.data_json or {})
        d["version"] = int(d.get("version") or 1) + 1
        row.data_json = d
        row.signoffs_json = {}
        row.status = "reopened"
        _log(row, by, "reopened", {"reason": reason.strip()})
    return await _mutate(study_id, record_id, apply)


async def delete(study_id: str, record_id: str) -> bool:
    from ..db.engine import get_session_factory
    from ..db.models_negotiation import NegotiationRecordRow
    async with get_session_factory()() as s:
        row = await s.get(NegotiationRecordRow, record_id)
        if row is None or row.study_id != study_id:
            return False
        await s.delete(row)
        await s.commit()
        return True


# ───────────────────────────────────────────────────────────── the read view

def evaluate_trigger(rec: dict[str, Any], live: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cond = rec.get("reopen_condition")
    if not cond:
        return {"fired": None, "condition": None}
    v = (live.get(cond["key"]) or {}).get("value")
    fired = None if v is None else bool(OPS[cond["op"]](float(v), float(cond["value"])))
    return {"fired": fired, "condition": cond, "value": v}


def view(rec: dict[str, Any], live: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """A record with its live parameter values, sign-off state and trigger."""
    params = [{"key": k, **(live.get(k) or {"value": None, "unit": "", "source": "unknown", "owner_seat": "",
                                          "label": LABELS.get(k, {"en": k, "fr": k})}),
               "agreed_value": (rec.get("agreed_snapshot") or {}).get(k)} for k in rec["parameters"]]
    from ..seats import config as seat_cfg
    seats = [{"seat": s, "label": seat_cfg.label(s), "signed": s in rec["signoffs"],
              **({"signoff": rec["signoffs"][s]} if s in rec["signoffs"] else {})} for s in rec["seats"]]
    return {**rec, "live_parameters": params, "seat_state": seats,
            "signed_count": sum(1 for s in seats if s["signed"]), "seat_count": len(seats),
            "trigger": evaluate_trigger(rec, live)}


async def views(study_id: str, records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    recs = records if records is not None else await list_records(study_id)
    if not recs:
        return []
    keys = sorted({k for r in recs for k in r["parameters"]} |
                  {r["reopen_condition"]["key"] for r in recs if r.get("reopen_condition")})
    live = await live_values(study_id, keys)
    return [view(r, live) for r in recs]


def counts(records: list[dict[str, Any]]) -> dict[str, int]:
    out = {"total": len(records), **{s: 0 for s in STATUSES}}
    for r in records:
        out[r["status"]] = out.get(r["status"], 0) + 1
    return out


__all__ = ["TEMPLATES", "compute_options", "create", "update", "sign", "reopen", "delete", "list_records",
           "get_record", "views", "view", "counts", "live_values"]
