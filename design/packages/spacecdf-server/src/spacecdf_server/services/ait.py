"""SpaceCDF — model philosophy, AIT test matrix and verification plan (W8a).

The verification and AIV plan (gate product ``aiv_plan``, baselined at PDR) is built from:

* the **model philosophy** (``ait_models``): which models are built, when, at which level and
  why (ECSS-E-ST-10-02C §5.2.5, ECSS-E-HB-10-02A §5.2). The default proposal is the protoflight
  philosophy of a university CubeSat: breadboards, an engineering model (flatsat) and a
  protoflight model that flies;
* the **test matrix** (``ait_tests``): test × models × level, the source of the test level, the
  facility, the environment levels and the requirements each test verifies (codes);
* the **verification items**: every requirement with its method(s), level and close-out stage
  (PDR, CDR, QR, AR or IOV for in-orbit verification), taken from the requirement fields
  (``verification_method`` / ``verification_methods``, ``verification_phase`` /
  ``verification_stage``, ``verification_level``) and the V&V planner's verification items;
* the **environment levels**, from the launch segment (launch vehicle or the generic CubeSat
  rideshare envelope when no launch is assigned yet).

Public API (all async functions read the database; nothing here writes except ``propose`` and
the CRUD helpers):

    await propose(study_id, replace=False) -> {"models": [...], "tests": [...], "added": n}
    await list_models(study_id) / list_tests(study_id)
    await verification_plan(study_id) -> dict      # what the VP docx and the export collector use
    environment_levels(study, elements) -> dict     # pure
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from sqlalchemy import delete, select

logger = logging.getLogger(__name__)

STAGES = ("PRR", "SRR", "PDR", "CDR", "QR", "AR", "IOV")
STAGE_LABEL = {
    "PRR": {"en": "Preliminary requirements review", "fr": "Revue préliminaire des exigences"},
    "SRR": {"en": "System requirements review", "fr": "Revue des exigences système"},
    "PDR": {"en": "Preliminary design review", "fr": "Revue de conception préliminaire"},
    "CDR": {"en": "Critical design review", "fr": "Revue critique de conception"},
    "QR": {"en": "Qualification review", "fr": "Revue de qualification"},
    "AR": {"en": "Acceptance review", "fr": "Revue de recette"},
    "IOV": {"en": "In-orbit verification", "fr": "Vérification en orbite"},
}
METHOD_LABEL = {
    "T": {"en": "Test", "fr": "Essai"}, "A": {"en": "Analysis", "fr": "Analyse"},
    "R": {"en": "Review of design", "fr": "Revue de conception"}, "I": {"en": "Inspection", "fr": "Inspection"},
    "D": {"en": "Demonstration (counted as test)", "fr": "Démonstration (comptée comme essai)"},
}
#: requirement level -> verification level when the requirement does not say
_LEVEL_FROM_REQ = {"stakeholder": "mission", "mission": "mission", "segment": "segment", "system": "system",
                   "subsystem": "subsystem", "interface": "system", "unit": "unit", "component": "unit"}

# ─────────────────────────────────────────────────────────────── default proposal

DEFAULT_PHILOSOPHY = "protoflight"

DEFAULT_MODELS: list[dict[str, Any]] = [
    {"code": "BB", "name": "Breadboards", "name_fr": "Maquettes fonctionnelles", "level": "subsystem",
     "due_month": 6, "build_standard": "commercial boards and lab harness",
     "purpose": "Retire the interface and software risks early: the payload chain (cameras, payload "
                "controller, on-board computer) and the radio link on a lab bench.",
     "purpose_fr": "Réduire tôt les risques d’interface et de logiciel : la chaîne charge utile (caméras, "
                   "calculateur charge utile, ordinateur de bord) et la liaison radio sur un banc."},
    {"code": "EM", "name": "Engineering model (flatsat)", "name_fr": "Modèle d’ingénierie (banc à plat)",
     "level": "system", "due_month": 18, "build_standard": "flight-representative electrical and software",
     "purpose": "Integrate every unit electrically and run the flight software, FDIR, end-to-end tests "
                "with the ground segment and the day in the life; no environmental qualification.",
     "purpose_fr": "Intégrer électriquement toutes les unités et exécuter le logiciel de vol, la FDIR, les "
                   "essais de bout en bout avec le segment sol et la journée type ; pas de qualification "
                   "en environnement."},
    {"code": "PFM", "name": "Protoflight model", "name_fr": "Modèle protovol", "level": "system",
     "due_month": 30, "build_standard": "flight standard",
     "purpose": "The spacecraft that flies, tested at protoflight levels (qualification levels for "
                "acceptance durations) and delivered for launch.",
     "purpose_fr": "Le véhicule qui vole, essayé aux niveaux protovol (niveaux de qualification pour des "
                   "durées de recette) et livré pour le lancement."},
]

#: (code, category, name, name_fr, models, level, stage, facility, match) — ``match`` links the
#: test to requirement codes (prefixes) and keywords of test-verified requirements.
DEFAULT_TESTS: list[dict[str, Any]] = [
    {"code": "T-FUN-01", "category": "functional", "models": ["BB", "EM"], "level": "subsystem", "stage": "CDR",
     "name": "Unit functional and interface tests", "name_fr": "Essais fonctionnels et d’interface des unités",
     "facility": "electronics lab, ESD-protected bench",
     "match": {"keywords": ["interface", "csi-2", "can bus", "i2c", "pps"]}},
    {"code": "T-FUN-02", "category": "functional", "models": ["EM"], "level": "system", "stage": "CDR",
     "name": "Flatsat integration and flight software tests", "name_fr": "Intégration sur banc à plat et essais du logiciel de vol",
     "facility": "flatsat bench with the mission control software",
     "match": {"prefixes": ["OBD-", "OPS-"], "keywords": ["software", "fdir", "safe mode"]}},
    {"code": "T-FUN-03", "category": "functional", "models": ["PFM"], "level": "system", "stage": "QR",
     "name": "Full functional test (before and after each environmental test)",
     "name_fr": "Essai fonctionnel complet (avant et après chaque essai d’environnement)",
     "facility": "clean room, electrical ground support equipment",
     "match": {"codes": ["VER-FUN-01"]}},
    {"code": "T-PHY-01", "category": "physical", "models": ["PFM"], "level": "system", "stage": "QR",
     "name": "Mass properties and CubeSat envelope check", "name_fr": "Propriétés de masse et contrôle de l’enveloppe CubeSat",
     "facility": "mass and centre-of-gravity bench, CDS fit-check jig",
     "level_source": "CubeSat Design Specification (CDS) rev. 14.1",
     "match": {"keywords": ["centre of mass", "center of mass", "cds", "envelope", "rail"]}},
    {"code": "T-ENV-01", "category": "environmental", "models": ["PFM"], "level": "system", "stage": "QR",
     "name": "Sine vibration, 3 axes", "name_fr": "Vibrations sinusoïdales, 3 axes", "env": "sine",
     "facility": "shaker (external test house)", "match": {"codes": ["VER-ENV-01"], "keywords": ["vibration"]}},
    {"code": "T-ENV-02", "category": "environmental", "models": ["PFM"], "level": "system", "stage": "QR",
     "name": "Random vibration, 3 axes", "name_fr": "Vibrations aléatoires, 3 axes", "env": "random",
     "facility": "shaker (external test house)", "match": {"codes": ["VER-ENV-01"], "keywords": ["random vibration"]}},
    {"code": "T-ENV-03", "category": "environmental", "models": ["PFM"], "level": "system", "stage": "QR",
     "name": "Thermal-vacuum cycling", "name_fr": "Cyclage thermique sous vide", "env": "tvac",
     "facility": "thermal-vacuum chamber", "match": {"codes": ["VER-ENV-02"], "keywords": ["thermal-vacuum", "thermal vacuum"]}},
    {"code": "T-EMC-01", "category": "emc", "models": ["EM", "PFM"], "level": "system", "stage": "QR",
     "name": "EMC and RF compatibility (self-compatibility, radiated emissions)",
     "name_fr": "CEM et compatibilité RF (autocompatibilité, émissions rayonnées)",
     "facility": "EMC chamber or open-area RF test", "level_source": "ECSS-E-ST-20-07C tailored; launch provider's limits",
     "match": {"keywords": ["emc", "emission", "self-compatib", "rf silence"]}},
    {"code": "T-DEP-01", "category": "deployment", "models": ["EM", "PFM"], "level": "system", "stage": "QR",
     "name": "Deployment tests: antennas, solar wings, drag sail and its independent timer",
     "name_fr": "Essais de déploiement : antennes, ailes solaires, voile de traînée et sa minuterie indépendante",
     "facility": "clean room, gravity off-loading jig",
     "match": {"codes": ["VER-DEP-01"], "prefixes": ["DIS-"], "keywords": ["deploy"]}},
    {"code": "T-E2E-01", "category": "end_to_end", "models": ["EM", "PFM"], "level": "system", "stage": "QR",
     "name": "End-to-end test through the ground stations", "name_fr": "Essai de bout en bout par les stations sol",
     "facility": "mission control and at least 2 ground stations over RF",
     "match": {"codes": ["VER-E2E-01"], "prefixes": ["SEG-GS"], "keywords": ["end-to-end"]}},
    {"code": "T-DIL-01", "category": "mission", "models": ["PFM"], "level": "system", "stage": "QR",
     "name": "Day-in-the-life test (72 h stored plan)", "name_fr": "Essai de journée type (plan stocké de 72 h)",
     "facility": "clean room with the mission control software",
     "match": {"codes": ["VER-DIL-01"], "keywords": ["day-in-the-life", "stored plan"]}},
    {"code": "T-CAL-01", "category": "performance", "models": ["PFM"], "level": "unit", "stage": "QR",
     "name": "Payload radiometric and spectral calibration", "name_fr": "Étalonnage radiométrique et spectral de la charge utile",
     "facility": "optics lab: integrating sphere, monochromator",
     "match": {"codes": ["VER-CAL-01"], "prefixes": ["PAY-"], "keywords": ["calibrat"]}},
]


def _uid() -> str:
    return uuid.uuid4().hex


# ─────────────────────────────────────────────────────────────── environment levels

def _launch_text(study: Any, elements: list[dict]) -> str:
    parts: list[str] = []
    req = getattr(study, "requirements", None)
    if req is not None and getattr(req, "launch_vehicle", None):
        parts.append(str(req.launch_vehicle))
    for e in elements:
        if str(e.get("segment") or "") == "launch" or str(e.get("name") or "").lower().startswith("launch"):
            parts.append(f"{e.get('name') or ''} {e.get('description') or ''}")
    return " ".join(parts)


#: launch vehicle keywords -> spacecdf_common.physics.structures.launch_loads key
_LV_KEYS = (("electron", "electron"), ("falcon 9", "falcon_9"), ("falcon9", "falcon_9"), ("transporter", "falcon_9"),
            ("vega", "vega_c"), ("ariane 6", "ariane_6"), ("pslv", "pslv"), ("soyuz", "soyuz"), ("h3", "h3"))


def environment_levels(study: Any, elements: list[dict], *, launch_provided: bool = False) -> dict[str, Any]:
    """Protoflight test levels for the spacecraft, from the launch segment.

    A named launch vehicle gives its quasi-static loads (``launch_loads``); otherwise, and for
    the vibration spectra in every case, the generic CubeSat rideshare envelope of GSFC-STD-7000B
    (GEVS) applies until the launch provider's interface control document is available.
    Protoflight = qualification levels for acceptance durations (ECSS-E-ST-10-03C §4.2).
    """
    text = _launch_text(study, elements).lower()
    vehicle = next((key for word, key in _LV_KEYS if word in text), None)
    qs = None
    if vehicle:
        try:
            from spacecdf_common.physics.structures import launch_loads
            ax, lat = launch_loads(vehicle)
            qs = {"axial_g": ax, "lateral_g": lat}
        except Exception:  # noqa: BLE001
            qs = None
    if launch_provided:
        source = ("launch provider's interface control document, through the agency that provides the launch; "
                  "until it is issued, the GSFC-STD-7000B (GEVS) envelope")
    elif vehicle:
        source = f"launch vehicle user's guide ({vehicle.replace('_', ' ')}); GEVS envelope for the spectra"
    else:
        source = ("GSFC-STD-7000B (GEVS) envelope for a CubeSat rideshare (no launch vehicle assigned yet); "
                  "replace with the launch provider's levels")
    return {
        "launch": text.strip() or "not assigned",
        "vehicle": vehicle,
        "level_source": source,
        "philosophy": "protoflight: qualification levels, acceptance durations (ECSS-E-ST-10-03C)",
        "quasi_static": qs or {"axial_g": None, "lateral_g": None, "note": "from the launch provider"},
        "sine": {"range_hz": [5, 100], "level_g": 2.5, "sweep_oct_per_min": 4, "axes": 3,
                 "note": "planning value until the launch provider's levels; low-level sine survey before and after each axis (< 5 % frequency shift)"},
        "random": {"range_hz": [20, 2000], "grms": 14.1, "duration_s_per_axis": 60, "axes": 3,
                   "note": "GEVS qualification level 14.1 grms for the protoflight test"},
        "tvac": {"cycles": 4, "pressure_hpa": 1e-5, "margin_c": 10,
                 "note": "predicted extremes ±10 °C (protoflight), functional test at each hot and cold plateau"},
    }


def _env_for(test: dict, env: dict) -> dict | None:
    kind = test.get("env")
    if kind == "sine":
        return {**env["sine"], "level_source": env["level_source"]}
    if kind == "random":
        return {**env["random"], "level_source": env["level_source"]}
    if kind == "tvac":
        return {**env["tvac"], "level_source": "ECSS-E-ST-10-03C; thermal analysis predictions"}
    return None


# ─────────────────────────────────────────────────────────────── requirements

def _codes_for(match: dict, reqs: list[dict]) -> list[str]:
    codes = set(match.get("codes") or [])
    prefixes = tuple(match.get("prefixes") or ())
    words = [w.lower() for w in match.get("keywords") or []]
    out: list[str] = []
    for r in reqs:
        code = str(r.get("code") or "")
        if not code:
            continue
        methods = _methods(r)
        if code in codes:
            out.append(code)
            continue
        if "T" not in methods:
            continue
        text = str(r.get("text") or "").lower()
        if (prefixes and code.startswith(prefixes) and (not words or any(w in text for w in words))) or \
                (not prefixes and words and any(w in text for w in words)):
            out.append(code)
    return sorted(dict.fromkeys(out))


def _methods(r: dict) -> list[str]:
    raw = r.get("verification_methods")
    if isinstance(raw, list) and raw:
        ms = [str(m).strip().upper()[:1] for m in raw if str(m).strip()]
    else:
        ms = [m for m in re.split(r"[,+/ ]+", str(r.get("verification_method") or "").upper()) if m]
        ms = [m[:1] for m in ms]
    return ["T" if m == "D" else m for m in ms] or []


def _stage(r: dict) -> str:
    s = str(r.get("verification_stage") or r.get("verification_phase") or "").strip().upper()
    if s in ("IOT", "IN-ORBIT", "INORBIT", "COMMISSIONING"):
        s = "IOV"
    return s if s in STAGES else "unassigned"


async def _requirements(study_id: str) -> list[dict]:
    from ..routers.requirements import _requirements, ensure_requirements_loaded
    try:
        await ensure_requirements_loaded()
    except Exception:  # noqa: BLE001 — DB unavailable: use the cache
        pass
    rows = [dict(r) for r in _requirements.values()
            if r.get("study_id") == study_id and r.get("status") != "retired"
            and not str(r.get("code") or "").startswith("IR-")]
    order = ("stakeholder", "mission", "segment", "system", "subsystem", "interface")
    rows.sort(key=lambda r: (order.index(r.get("level")) if r.get("level") in order else len(order),
                             str(r.get("code") or "~"), str(r.get("id") or "")))
    return rows


# ─────────────────────────────────────────────────────────────── database

def _model_dict(r) -> dict:
    return {"id": r.id, "study_id": r.study_id, "code": r.code, "name": r.name, "name_fr": r.name_fr,
            "philosophy": r.philosophy, "level": r.level, "due_month": r.due_month, "purpose": r.purpose,
            "purpose_fr": r.purpose_fr, "build_standard": r.build_standard, "status": r.status,
            "origin": r.origin, "order": r.order}


def _test_dict(r) -> dict:
    return {"id": r.id, "study_id": r.study_id, "code": r.code, "name": r.name, "name_fr": r.name_fr,
            "category": r.category, "models": list(r.models_json or []), "level": r.level,
            "level_source": r.level_source, "facility": r.facility, "environment": r.environment_json or None,
            "requirement_codes": list(r.requirement_codes_json or []), "stage": r.stage, "status": r.status,
            "notes": r.notes, "origin": r.origin, "order": r.order}


async def list_models(study_id: str) -> list[dict]:
    from ..db.engine import get_session_factory
    from ..db.models_ait import AitModelRow
    async with get_session_factory()() as s:
        rows = (await s.execute(select(AitModelRow).where(AitModelRow.study_id == study_id)
                                .order_by(AitModelRow.order, AitModelRow.code))).scalars().all()
        return [_model_dict(r) for r in rows]


async def list_tests(study_id: str) -> list[dict]:
    from ..db.engine import get_session_factory
    from ..db.models_ait import AitTestRow
    async with get_session_factory()() as s:
        rows = (await s.execute(select(AitTestRow).where(AitTestRow.study_id == study_id)
                                .order_by(AitTestRow.order, AitTestRow.code))).scalars().all()
        return [_test_dict(r) for r in rows]


def _study_and_elements(study_id: str) -> tuple[Any, list[dict]]:
    from ..routers.elements import _elements
    from ..routers.studies import get_study_store
    els = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    return get_study_store().get(study_id), els


async def _launch_provided(study_id: str) -> bool:
    try:
        from . import schedule
        return bool((await schedule.get_settings(study_id)).get("launch_provided"))
    except Exception:  # noqa: BLE001
        return False


async def propose(study_id: str, *, replace: bool = False) -> dict[str, Any]:
    """Write the default model philosophy and test matrix for the study.

    Existing rows the user made or edited (``origin = "user"``) are kept; proposed rows with the
    same code are refreshed (requirement links, environment levels). ``replace=True`` deletes
    every row first. Returns the rows and the number added.
    """
    from ..db.engine import get_session_factory
    from ..db.models_ait import AitModelRow, AitTestRow

    study, els = _study_and_elements(study_id)
    reqs = await _requirements(study_id)
    env = environment_levels(study, els, launch_provided=await _launch_provided(study_id))
    added = 0
    async with get_session_factory()() as s:
        if replace:
            await s.execute(delete(AitModelRow).where(AitModelRow.study_id == study_id))
            await s.execute(delete(AitTestRow).where(AitTestRow.study_id == study_id))
        have_m = {r.code: r for r in (await s.execute(
            select(AitModelRow).where(AitModelRow.study_id == study_id))).scalars()}
        for i, m in enumerate(DEFAULT_MODELS):
            row = have_m.get(m["code"])
            if row is None:
                s.add(AitModelRow(id=_uid(), study_id=study_id, philosophy=DEFAULT_PHILOSOPHY, origin="proposed",
                                  order=i, **m))
                added += 1
            elif row.origin == "proposed":
                for k, v in m.items():
                    setattr(row, k, v)
        have_t = {r.code: r for r in (await s.execute(
            select(AitTestRow).where(AitTestRow.study_id == study_id))).scalars()}
        for i, t in enumerate(DEFAULT_TESTS):
            fields = {
                "code": t["code"], "name": t["name"], "name_fr": t["name_fr"], "category": t["category"],
                "models_json": list(t["models"]), "level": t["level"], "stage": t["stage"],
                "facility": t["facility"],
                "level_source": t.get("level_source") or (env["level_source"] if t.get("env") in ("sine", "random")
                                                          else "ECSS-E-ST-10-03C"),
                "environment_json": _env_for(t, env),
                "requirement_codes_json": _codes_for(t.get("match") or {}, reqs),
            }
            row = have_t.get(t["code"])
            if row is None:
                s.add(AitTestRow(id=_uid(), study_id=study_id, origin="proposed", order=i, **fields))
                added += 1
            elif row.origin == "proposed":
                for k, v in fields.items():
                    setattr(row, k, v)
        await s.commit()
    return {"models": await list_models(study_id), "tests": await list_tests(study_id), "added": added,
            "environment": env}


# ─────────────────────────────────────────────────────────────── import of a V&V plan (wave 3, 3.A4)

#: model codes of a V&V plan -> (level, build standard)
_V2_MODEL_LEVEL = {"BB": "subsystem", "EM": "system", "PFM": "system", "LV": "system", "GS": "segment",
                   "flight": "mission", "FM": "system", "QM": "system", "STM": "system"}
_V2_MODEL_FR = {"BB": "Maquettes fonctionnelles", "EM": "Modèle d’ingénierie et banc à plat", "PFM": "Modèle protovol",
                "LV": "Vibrations finales du lanceur dans le déployeur", "GS": "Intégration du segment sol",
                "flight": "Vérification et validation en orbite"}
#: event-id prefix -> (category, models)
_EVENT_KIND = (("AN-", "analysis"), ("IN-", "inspection"), ("RV-", "review"), ("IOV-", "in_orbit"), ("TS-", "test"))
_TEST_CATEGORY_WORDS = (("VIB", "environmental"), ("TVAC", "environmental"), ("EMC", "emc"), ("DEP", "deployment"),
                        ("E2E", "end_to_end"), ("DITL", "mission"), ("-MP", "physical"), ("CAL", "performance"),
                        ("ACC", "functional"), ("SURVEY", "functional"))
_FACILITY = {"analysis": "analysis (SpaceCDF analyses and design files)",
             "inspection": "inspection (records, drawings, workmanship)",
             "review": "review of design (review data package)",
             "in_orbit": "in orbit (mission control, ground stations)"}


def _event_meta(eid: str, models: set[str]) -> tuple[str, list[str], str]:
    """(category, models, stage hint) of a verification event from its id (AN-, IN-EM-, TS-PFM- …)."""
    kind = next((k for p, k in _EVENT_KIND if eid.startswith(p)), "test")
    parts = eid.split("-")
    mods = [p for p in parts[1:3] if p in models] or (["flight"] if kind == "in_orbit" else ["design"]
                                                      if kind in ("analysis", "review") else [])
    if kind == "test":
        cat = next((c for w, c in _TEST_CATEGORY_WORDS if w in eid), "functional")
    else:
        cat = kind
    stage = parts[1] if kind == "review" and len(parts) > 1 else ""
    return cat, mods, stage


async def import_vv_plan(study_id: str, plan: dict[str, Any], *, replace_proposed: bool = True) -> dict[str, Any]:
    """The models of a V&V plan's model philosophy and its verification events (with their
    requirements) as the study's model philosophy and test-matrix events (``vv_plan.yaml`` shape:
    ``model_philosophy``, ``events``, ``matrix``). Rows the team made (``origin = "user"``) are kept;
    with ``replace_proposed`` the default proposal (``propose``) is replaced."""
    from ..db.engine import get_session_factory
    from ..db.models_ait import AitModelRow, AitTestRow

    mp = list(plan.get("model_philosophy") or [])
    events = list(plan.get("events") or [])
    matrix = list(plan.get("matrix") or [])
    stage_of: dict[str, dict[str, int]] = {}
    level_of: dict[str, dict[str, int]] = {}
    for r in matrix:
        ev = str(r.get("event") or "")
        if ev:
            st = stage_of.setdefault(ev, {})
            st[str(r.get("stage") or "")] = st.get(str(r.get("stage") or ""), 0) + 1
            lv = level_of.setdefault(ev, {})
            lv[str(r.get("verification_level") or r.get("level") or "")] = lv.get(str(r.get("verification_level") or ""), 0) + 1
    codes = {str(m.get("model")) for m in mp}
    added_m = added_t = 0
    async with get_session_factory()() as s:
        if replace_proposed:
            await s.execute(delete(AitModelRow).where(AitModelRow.study_id == study_id, AitModelRow.origin == "proposed"))
            await s.execute(delete(AitTestRow).where(AitTestRow.study_id == study_id, AitTestRow.origin == "proposed"))
        have_m = {r.code: r for r in (await s.execute(select(AitModelRow).where(AitModelRow.study_id == study_id))).scalars()}
        for i, m in enumerate(mp):
            code = str(m.get("model"))
            levels = list(m.get("levels") or [])
            fields = {"code": code, "name": str(m.get("name") or code), "name_fr": _V2_MODEL_FR.get(code, str(m.get("name") or code)),
                      "philosophy": "protoflight", "level": (levels[-1] if levels else _V2_MODEL_LEVEL.get(code, "system"))[:16],
                      "due_month": int(m["month"]) if isinstance(m.get("month"), (int, float)) else None,
                      "purpose": str(m.get("purpose") or ""), "purpose_fr": "",
                      "build_standard": str(m.get("trl_target") or "")[:64], "order": i}
            row = have_m.get(code)
            if row is None:
                s.add(AitModelRow(id=_uid(), study_id=study_id, origin="import", **fields))
                added_m += 1
            elif row.origin != "user":
                for k, v in fields.items():
                    setattr(row, k, v)
        have_t = {r.code: r for r in (await s.execute(select(AitTestRow).where(AitTestRow.study_id == study_id))).scalars()}
        for i, ev in enumerate(events):
            eid = str(ev.get("id") or "")
            cat, mods, st_hint = _event_meta(eid, codes)
            stages = stage_of.get(eid) or {}
            stage = max(stages.items(), key=lambda kv: kv[1])[0] if stages else (st_hint or "")
            levels = level_of.get(eid) or {}
            level = max(levels.items(), key=lambda kv: kv[1])[0] if levels else "system"
            desc = str(ev.get("description") or "")
            fields = {"code": eid, "name": f"{eid}: {desc}"[:160], "name_fr": "", "category": cat,
                      "models_json": mods, "level": (level or "system")[:16], "stage": (stage or "")[:8],
                      "facility": _FACILITY.get(cat, ""), "level_source": "",
                      "requirement_codes_json": list(ev.get("requirements") or []),
                      "notes": f"{len(ev.get('requirements') or [])} requirement(s); V&V plan event"}
            row = have_t.get(eid)
            if row is None:
                s.add(AitTestRow(id=_uid(), study_id=study_id, origin="import", order=100 + i, **fields))
                added_t += 1
            elif row.origin != "user":
                for k, v in fields.items():
                    setattr(row, k, v)
        await s.commit()
    return {"models": await list_models(study_id), "tests": await list_tests(study_id),
            "added": {"models": added_m, "events": added_t}}


_MODEL_FIELDS = ("code", "name", "name_fr", "philosophy", "level", "due_month", "purpose", "purpose_fr",
                 "build_standard", "status", "order")
_TEST_FIELDS = ("code", "name", "name_fr", "category", "level", "level_source", "facility", "stage", "status",
                "notes", "order")


async def upsert_model(study_id: str, data: dict, model_id: str | None = None) -> dict | None:
    from ..db.engine import get_session_factory
    from ..db.models_ait import AitModelRow
    async with get_session_factory()() as s:
        if model_id:
            row = await s.get(AitModelRow, model_id)
            if row is None or row.study_id != study_id:
                return None
        else:
            row = AitModelRow(id=_uid(), study_id=study_id, code=str(data.get("code") or "M"))
            s.add(row)
        for k in _MODEL_FIELDS:
            if k in data and data[k] is not None:
                setattr(row, k, data[k])
        row.origin = "user"
        await s.commit()
        return _model_dict(row)


async def upsert_test(study_id: str, data: dict, test_id: str | None = None) -> dict | None:
    from ..db.engine import get_session_factory
    from ..db.models_ait import AitTestRow
    async with get_session_factory()() as s:
        if test_id:
            row = await s.get(AitTestRow, test_id)
            if row is None or row.study_id != study_id:
                return None
        else:
            row = AitTestRow(id=_uid(), study_id=study_id, code=str(data.get("code") or "T"))
            s.add(row)
        for k in _TEST_FIELDS:
            if k in data and data[k] is not None:
                setattr(row, k, data[k])
        if data.get("models") is not None:
            row.models_json = [str(m) for m in data["models"]]
        if data.get("requirement_codes") is not None:
            row.requirement_codes_json = [str(c) for c in data["requirement_codes"]]
        if data.get("environment") is not None:
            row.environment_json = data["environment"]
        row.origin = "user"
        await s.commit()
        return _test_dict(row)


async def delete_row(study_id: str, kind: str, row_id: str) -> bool:
    from ..db.engine import get_session_factory
    from ..db.models_ait import AitModelRow, AitTestRow
    model = AitModelRow if kind == "models" else AitTestRow
    async with get_session_factory()() as s:
        row = await s.get(model, row_id)
        if row is None or row.study_id != study_id:
            return False
        await s.delete(row)
        await s.commit()
        return True


# ─────────────────────────────────────────────────────────────── verification plan

def _facility(methods: list[str], tests: list[dict]) -> str:
    if tests:
        return "; ".join(dict.fromkeys(t["facility"] for t in tests if t.get("facility")))
    if "T" in methods:
        return "test facility to be named"
    if "A" in methods:
        return "analysis (SpaceCDF analyses and design files)"
    if "I" in methods:
        return "inspection (records, drawings, workmanship)"
    if "R" in methods:
        return "review of design (review data package)"
    return ""


def plan_from(requirements: list[dict], models: list[dict], tests: list[dict],
              v_items: list[dict] | None = None, environment: dict | None = None) -> dict[str, Any]:
    """The verification plan as data (pure): items by stage, method and level, plus models and tests."""
    by_req_vi: dict[str, dict] = {}
    for v in v_items or []:
        if v.get("deleted_at"):
            continue
        by_req_vi.setdefault(str(v.get("requirement_id") or ""), v)
    tests_by_code: dict[str, list[dict]] = {}
    for t in tests:
        for c in t.get("requirement_codes") or []:
            tests_by_code.setdefault(c, []).append(t)

    items: list[dict] = []
    for r in requirements:
        vi = by_req_vi.get(str(r.get("id") or ""), {})
        methods = _methods(r) or ([str(vi.get("method")).upper()[:1]] if vi.get("method") else [])
        stage = _stage(r)
        if stage == "unassigned" and vi.get("phase"):
            stage = _stage({"verification_phase": vi.get("phase")})
        level = (r.get("verification_level") or vi.get("level")
                 or _LEVEL_FROM_REQ.get(str(r.get("level") or ""), "system"))
        linked = tests_by_code.get(str(r.get("code") or ""), [])
        event = str(r.get("verification_event") or "").strip()
        if event and event not in [t["code"] for t in linked]:
            linked = linked + [t for t in tests if t.get("code") == event]
        items.append({
            "requirement_id": r.get("id"), "code": r.get("code") or r.get("id"), "text": r.get("text") or "",
            "event": event or None, "model": r.get("verification_model") or None,
            "req_level": r.get("level"), "methods": methods, "stage": stage, "level": level,
            "tests": [t["code"] for t in linked],
            "facility": vi.get("facility") or _facility(methods, linked),
            "acceptance": r.get("acceptance") or vi.get("acceptance_criterion") or "",
            "status": vi.get("status") or "planned",
        })
    by_stage = {s: 0 for s in (*STAGES, "unassigned")}
    by_method: dict[str, int] = {}
    by_level: dict[str, int] = {}
    for it in items:
        by_stage[it["stage"]] = by_stage.get(it["stage"], 0) + 1
        for m in it["methods"] or ["?"]:
            by_method[m] = by_method.get(m, 0) + 1
        by_level[it["level"]] = by_level.get(it["level"], 0) + 1
    for st in ("unassigned", "PRR", "SRR"):      # shown only when a row closes there (v2: one each)
        if not by_stage.get(st):
            by_stage.pop(st, None)
    philosophy = next((m.get("philosophy") for m in models if m.get("philosophy")), DEFAULT_PHILOSOPHY) \
        if models else None
    return {
        "philosophy": philosophy, "models": models, "tests": tests, "environment": environment or {},
        "items": items, "counts": {"items": len(items), "by_stage": by_stage, "by_method": by_method,
                                   "by_level": by_level, "models": len(models), "tests": len(tests)},
    }


async def verification_plan(study_id: str) -> dict[str, Any]:
    """Collect the verification plan of a stored study (read only)."""
    from ..db import verification_repo
    study, els = _study_and_elements(study_id)
    try:
        v_items = await verification_repo.list_by_study(study_id)
    except Exception:  # noqa: BLE001
        v_items = []
    return plan_from(await _requirements(study_id), await list_models(study_id), await list_tests(study_id),
                     v_items, environment_levels(study, els, launch_provided=await _launch_provided(study_id)))


__all__ = ["DEFAULT_MODELS", "DEFAULT_TESTS", "STAGES", "environment_levels", "import_vv_plan", "list_models",
           "list_tests", "plan_from", "propose", "upsert_model", "upsert_test", "delete_row", "verification_plan"]
