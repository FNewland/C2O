"""Systems-engineering protocol: what the current phase asks of the team (SE-01). Owner S (3.S1, 3.S4).

``configs/se_protocol.yaml`` holds, per canonical gate (MDR … FRR), the phase entry checks, the
deliverables, the analysis standard and the coaching cards (data, PI ruling: the coaching
paraphrases the systems-engineering skill and cites it). This module loads and validates the
file and assembles the phase view; ``se_deliverables.py`` evaluates the items against the study.

``GET /api/studies/{study_id}/phase`` (``routers/se_phase.py``) returns :func:`phase`::

    {"study_id": "...", "gate": "mdr",            # the profile gate the study prepares for
     "gate_short": "MDR", "covers": ["mdr"],      # the canonical gates that gate covers
     "phase": "0", "phase_label": {en, fr},       # lifecycle phase that gate closes
     "current_gate": "mdr", "upcoming": ["prr", …],
     "enforcement": "warn",                       # off | warn | block (gate_profiles.yaml se_enforcement, D)
     "entry": [],          # [{id, kind, label{en,fr}, state: ok|warn|missing|info, evidence, evidence_i18n{en,fr},
                           #   fix, severity}]  "Before you start"
     "deliverables": [],   # [{id, kind: product|diagram|trade|document|criteria|object, label{en,fr},
                           #   owner_seat, state, evidence, evidence_i18n, fix, draft, severity, refs}]
     "analysis": [],       # [{id, label{en,fr}, state, evidence, items}] "Analysis standard" (open assumptions …)
     "summary": {ok, warn, missing, info, total},
     "coaching": {register, registers, phase: [card], seats: {seat: [card]}, pointers: [card]},
                           # card = {id, title{en,fr}, body{en,fr}, source, source_label, kind, approval?}
     "sources": [{id, label}]}

``?gate=srr`` shows another gate's block (the "SRR block" while the study prepares for PRR);
``?seat=power_engineer`` keeps only that seat's cards; ``?register=plain`` picks the register.

Readers: the Phase panel (D, 3.D2), the gate ``start`` warnings (D, 3.D1, through
``se_deliverables.evaluate``), the ``<GATE>-SE-01`` criterion (R, 3.R4), the pack index (X,
3.X2), the Guide drawer (S, 3.S4) and, after the recording, the optional AI coach (S, wave 4).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

#: lifecycle phase each gate closes (ECSS-M-ST-10C)
GATE_PHASE = {"mdr": "0", "prr": "A", "srr": "B", "pdr": "B", "cdr": "C", "qr": "D", "ar": "D", "frr": "D"}
CANONICAL = ("mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr")
#: gates whose block must be complete (coaching for every seat); later ones are a skeleton
FULL_GATES = ("mdr", "prr", "srr", "pdr")
REGISTERS = ("learning", "plain", "practitioner")
DEFAULT_REGISTER = "learning"
DELIVERABLE_KINDS = ("product", "diagram", "trade", "document", "criteria", "object")
ENTRY_KINDS = ("gate_passed", "reading", "object", "criteria")
ANALYSIS_KINDS = ("assumptions_due", "object")
SEVERITIES = ("info", "warn", "block")
TRADE_LEVELS = ("mission", "system", "architecture", "subsystem", "equipment")
#: diagram kinds agent X adds this wave (3.X1, ``diagrams/b_se.py``); accepted by the loader and
#: shown "not available in this build" until they are registered in ``diagrams.KINDS``
PLANNED_DIAGRAM_KINDS = ("context", "stakeholder_map", "ffbd", "v_model", "trade_matrix", "budget_flowdown",
                         "verification_flow")
#: words no card may use without a cited reference (skill: engineering analysis standards §5)
BANNED_WORDS = ("best", "optimal", "optimum", "state of the art", "state-of-the-art", "industry-leading", "proven",
                "world-class", "meilleur", "meilleure", "optimale", "de pointe", "éprouvé", "éprouvée")


class ProtocolError(ValueError):
    pass


def _file() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "configs" / "se_protocol.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("configs/se_protocol.yaml not found")


@lru_cache(maxsize=4)
def _load(path: str, stamp: int) -> tuple[dict[str, Any], tuple[str, ...]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    errs = tuple(validate(data))
    if errs:
        logger.error("se_protocol.yaml is invalid: %s", "; ".join(errs[:20]))
    return data, errs


def load_with_errors() -> tuple[dict[str, Any], list[str]]:
    p = _file()
    data, errs = _load(str(p), p.stat().st_mtime_ns)
    return data, list(errs)


def load() -> dict[str, Any]:
    """The validated protocol. Raises ProtocolError when the file is invalid (never guesses)."""
    data, errs = load_with_errors()
    if errs:
        raise ProtocolError("; ".join(errs[:10]))
    return data


def validate_at_startup() -> list[str]:
    """Load and validate once (app start-up; logs the errors). Returns the error list."""
    try:
        return load_with_errors()[1]
    except (FileNotFoundError, OSError, yaml.YAMLError) as exc:
        logger.error("se_protocol.yaml failed to load: %s", exc)
        return [str(exc)]


# ─── validation ────────────────────────────────────────────────────────────

def _known_seats() -> set[str]:
    p = _file().parent / "seats.yaml"
    try:
        return {str(s["id"]) for s in (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("seats") or []}
    except Exception:  # noqa: BLE001
        return set()


def _known_products() -> set[str]:
    try:
        from . import gate_profiles as gp
        return {str(p["id"]) for p in gp.load().get("products") or []}
    except Exception:  # noqa: BLE001
        return set()


def _known_diagrams() -> set[str]:
    try:
        from .diagrams import KINDS
        return set(KINDS) | set(PLANNED_DIAGRAM_KINDS)
    except Exception:  # noqa: BLE001
        return set(PLANNED_DIAGRAM_KINDS)


def _bi(v: Any, where: str, errs: list[str]) -> None:
    """``v`` must be {en, fr}, both non-empty strings."""
    if not isinstance(v, dict) or not str(v.get("en") or "").strip() or not str(v.get("fr") or "").strip():
        errs.append(f"{where}: needs non-empty en and fr text")


def _registered(v: Any, where: str, errs: list[str]) -> None:
    """Text given either as {en, fr} or per register {learning: {en, fr}, plain: …}."""
    if isinstance(v, dict) and any(k in v for k in REGISTERS):
        for k, t in v.items():
            if k not in REGISTERS:
                errs.append(f"{where}: unknown register {k}")
            else:
                _bi(t, f"{where}.{k}", errs)
        if "learning" not in v:
            errs.append(f"{where}: the learning register (the default) is required")
    else:
        _bi(v, where, errs)


def validate(data: dict[str, Any]) -> list[str]:
    """Structural checks of the protocol: every canonical gate present; FR text on every label,
    purpose and card; known kinds, products, diagram kinds, object queries, seats and sources;
    MDR–PDR coach every seat of ``seats.yaml``."""
    from .se_deliverables import OBJECT_QUERIES
    errs: list[str] = []
    if data.get("version") != 1:
        errs.append("version must be 1")
    if data.get("enforcement_default") not in ("off", "warn", "block"):
        errs.append("enforcement_default must be off, warn or block")
    sources = set((data.get("sources") or {}).keys())
    seats = _known_seats()
    products = _known_products()
    diagrams = _known_diagrams()
    phases = data.get("phases") or {}
    for g in CANONICAL:
        if g not in phases:
            errs.append(f"phases.{g} is missing")
    ids: set[str] = set()

    def item(it: dict, where: str, kinds: tuple[str, ...]) -> None:
        iid = it.get("id")
        if not iid:
            errs.append(f"{where}: item without id")
        elif iid in ids:
            errs.append(f"{where}: duplicate id {iid}")
        ids.add(iid)
        w = f"{where}.{iid}"
        if it.get("kind") not in kinds:
            errs.append(f"{w}: unknown kind {it.get('kind')!r}")
        _bi(it.get("label"), f"{w}.label", errs)
        if it.get("severity", "warn") not in SEVERITIES:
            errs.append(f"{w}: unknown severity {it.get('severity')!r}")
        seat = it.get("owner_seat")
        if seat and seats and seat not in seats:
            errs.append(f"{w}: unknown seat {seat!r}")
        k = it.get("kind")
        if k == "product" and products and it.get("ref") not in products:
            errs.append(f"{w}: unknown product {it.get('ref')!r}")
        if k == "diagram" and it.get("ref") not in diagrams:
            errs.append(f"{w}: unknown diagram kind {it.get('ref')!r}")
        if k == "trade":
            if not set(it.get("levels") or []) or not set(it.get("levels") or []) <= set(TRADE_LEVELS):
                errs.append(f"{w}: trade levels must be among {TRADE_LEVELS}")
            if not set(it.get("gates") or []) <= set(CANONICAL):
                errs.append(f"{w}: unknown gate in trade gates")
        if k == "object" and it.get("query") not in OBJECT_QUERIES:
            errs.append(f"{w}: unknown object query {it.get('query')!r}")
        if k == "document":
            q = (it.get("check") or {}).get("query")
            if q not in OBJECT_QUERIES:
                errs.append(f"{w}: document check needs a known query (got {q!r})")
        if k == "gate_passed" and it.get("ref") not in CANONICAL:
            errs.append(f"{w}: unknown gate {it.get('ref')!r}")
        if k == "reading" and it.get("ref") not in sources:
            errs.append(f"{w}: reading cites an unknown source {it.get('ref')!r}")

    for g, blk in phases.items():
        if g not in CANONICAL:
            errs.append(f"phases.{g}: not a canonical gate")
            continue
        where = f"phases.{g}"
        _bi((blk.get("phase") or {}).get("label"), f"{where}.phase.label", errs)
        _registered(blk.get("purpose"), f"{where}.purpose", errs)
        _bi(blk.get("exit"), f"{where}.exit", errs)
        for i, t in enumerate(blk.get("matters") or []):
            _bi(t, f"{where}.matters[{i}]", errs)
        for i, t in enumerate(blk.get("failures") or []):
            _bi(t, f"{where}.failures[{i}]", errs)
        for s in blk.get("sources") or []:
            if s not in sources:
                errs.append(f"{where}.sources: unknown source {s!r}")
        for it in blk.get("entry") or []:
            item(it, f"{where}.entry", ENTRY_KINDS)
        for it in blk.get("deliverables") or []:
            item(it, f"{where}.deliverables", DELIVERABLE_KINDS)
        for it in blk.get("analysis") or []:
            item(it, f"{where}.analysis", ANALYSIS_KINDS)
        cards = ((blk.get("coaching") or {}).get("seats") or {})
        for seat, c in cards.items():
            w = f"{where}.coaching.seats.{seat}"
            if seats and seat not in seats:
                errs.append(f"{w}: unknown seat")
            if c.get("source") not in sources:
                errs.append(f"{w}: card needs a known source")
            _bi(c.get("why"), f"{w}.why", errs)
            _bi(c.get("focus"), f"{w}.focus", errs)
        if g in FULL_GATES:
            if not blk.get("matters") or not blk.get("failures"):
                errs.append(f"{where}: a full gate needs matters and failures")
            missing = sorted(seats - set(cards))
            if missing:
                errs.append(f"{where}.coaching.seats: no card for {', '.join(missing)}")
    for p in data.get("pointers") or []:
        w = f"pointers.{p.get('id')}"
        _bi(p.get("title"), f"{w}.title", errs)
        _registered(p.get("body"), f"{w}.body", errs)
        if p.get("source") not in sources:
            errs.append(f"{w}: card needs a known source")
        if not set(p.get("gates") or []) <= set(CANONICAL):
            errs.append(f"{w}: unknown gate")
        for s in p.get("seats") or []:
            if seats and s not in seats:
                errs.append(f"{w}: unknown seat {s!r}")
    return errs


# ─── cards ─────────────────────────────────────────────────────────────────

def text_for(v: Any, register: str) -> dict[str, str]:
    """{en, fr} of a text given as {en, fr} or per register (falls back to learning)."""
    if isinstance(v, dict) and any(k in v for k in REGISTERS):
        return dict(v.get(register) or v.get(DEFAULT_REGISTER) or next(iter(v.values())))
    return dict(v or {"en": "", "fr": ""})


def _join(items: list[dict[str, str]]) -> dict[str, str]:
    return {lang: "\n".join(f"• {t.get(lang, '')}" for t in items) for lang in ("en", "fr")}


_TITLES = {
    "purpose": {"en": "Why this phase", "fr": "Pourquoi cette phase"},
    "matters": {"en": "What matters most", "fr": "Ce qui compte le plus"},
    "exit": {"en": "Ready to leave the phase when…", "fr": "Prêt à quitter la phase quand…"},
    "failures": {"en": "Common ways this phase goes wrong", "fr": "Erreurs fréquentes dans cette phase"},
}


def phase_cards(g: str, blk: dict[str, Any], register: str) -> list[dict[str, Any]]:
    src = (blk.get("sources") or ["skill_core"])[0]
    out = [{"id": f"{g.upper()}-PH-PURPOSE", "kind": "phase", "title": _TITLES["purpose"],
            "body": text_for(blk.get("purpose"), register), "source": src}]
    if blk.get("matters") and register != "plain":
        out.append({"id": f"{g.upper()}-PH-MATTERS", "kind": "phase", "title": _TITLES["matters"],
                    "body": _join(blk["matters"]), "source": src})
    if blk.get("exit"):
        out.append({"id": f"{g.upper()}-PH-EXIT", "kind": "phase", "title": _TITLES["exit"],
                    "body": dict(blk["exit"]), "source": src})
    if blk.get("failures"):
        out.append({"id": f"{g.upper()}-PH-FAILURES", "kind": "phase", "title": _TITLES["failures"],
                    "body": _join(blk["failures"]), "source": src})
    return out


def seat_card(g: str, seat: str, c: dict[str, Any], register: str, seat_label: dict[str, str] | None) -> dict[str, Any]:
    """One seat's card in a register: plain = the why (everyday words); learning = the why, then
    what to produce (why before what); practitioner = what to produce."""
    why, focus = dict(c.get("why") or {}), dict(c.get("focus") or {})
    if register == "plain":
        body = why
    elif register == "practitioner":
        body = focus
    else:
        body = {lang: f"{why.get(lang, '')}\n\n{focus.get(lang, '')}".strip() for lang in ("en", "fr")}
    label = seat_label or {"en": seat, "fr": seat}
    return {"id": f"{g.upper()}-SEAT-{seat}", "kind": "seat", "seat": seat,
            "title": {"en": f"{label.get('en', seat)}: this phase", "fr": f"{label.get('fr', seat)} : cette phase"},
            "body": body, "source": c.get("source") or "skill_core"}


def pointer_card(p: dict[str, Any], register: str) -> dict[str, Any]:
    out = {"id": p["id"], "kind": "pointer", "title": dict(p["title"]), "body": text_for(p.get("body"), register),
           "source": p.get("source"), "seats": list(p.get("seats") or [])}
    if p.get("approval"):
        out["approval"] = p["approval"]
    if p.get("legal_confidence"):
        out["legal_confidence"] = p["legal_confidence"]
    return out


def _seat_labels() -> dict[str, dict[str, str]]:
    p = _file().parent / "seats.yaml"
    try:
        return {str(s["id"]): dict(s.get("label") or {}) for s in (yaml.safe_load(p.read_text(encoding="utf-8")) or {})
                .get("seats") or []}
    except Exception:  # noqa: BLE001
        return {}


def coaching(covers: list[str], *, register: str = DEFAULT_REGISTER, seat: str | None = None,
             data: dict[str, Any] | None = None) -> dict[str, Any]:
    """The cards for the canonical gates ``covers``: phase cards, one card per seat, pointers."""
    data = data or load()
    register = register if register in REGISTERS else DEFAULT_REGISTER
    labels = _seat_labels()
    src_label = dict(data.get("sources") or {})
    phase: list[dict] = []
    seats: dict[str, list[dict]] = {}
    for g in covers:
        blk = (data.get("phases") or {}).get(g) or {}
        phase += phase_cards(g, blk, register)
        for s, c in ((blk.get("coaching") or {}).get("seats") or {}).items():
            if seat and s != seat:
                continue
            seats.setdefault(s, []).append(seat_card(g, s, c, register, labels.get(s)))
    pointers = [pointer_card(p, register) for p in data.get("pointers") or []
                if set(p.get("gates") or []) & set(covers) and (not seat or not p.get("seats") or seat in p["seats"]
                                                                 or seat == "instructor")]
    for c in [*phase, *pointers, *(x for v in seats.values() for x in v)]:
        c["source_label"] = src_label.get(c.get("source"), c.get("source"))
    return {"register": register, "registers": list(REGISTERS),
            "register_labels": dict(data.get("register_labels") or {}),
            "phase": phase, "seats": seats, "pointers": pointers}


def all_cards(data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Every card text in every register (the linter and the paraphrase check read this)."""
    data = data or load()
    out = []
    for g in CANONICAL:
        for reg in REGISTERS:
            c = coaching([g], register=reg, data=data)
            out += c["phase"] + c["pointers"] + [x for v in c["seats"].values() for x in v]
    return out


# ─── the phase view ────────────────────────────────────────────────────────

def empty_phase(gate: str | None = None) -> dict[str, Any]:
    """The phase shape with nothing in it."""
    g = (gate or "").lower() or None
    return {"gate": g, "phase": GATE_PHASE.get(g or "", None), "entry": [], "deliverables": [], "analysis": [],
            "coaching": {}}


def current_gate_id(study: Any) -> str | None:
    """The id of the first gate of the study's profile that has not passed (lower case)."""
    from ..routers.gates import current_gate, study_profile
    from . import gate_profiles as gp
    g = current_gate(study_profile(study), study)
    if g is None:
        return None
    return gp.legacy_gate_id(g.get("id")) or str(g.get("id") or "").lower() or None


def profile_gate(study: Any, gate: str | None) -> dict[str, Any] | None:
    """The profile gate ``gate`` (default: the current one) of the study's profile."""
    from ..routers.gates import current_gate, study_profile
    from . import gate_profiles as gp
    prof = study_profile(study) if study is not None else gp.get_profile(None)
    if gate:
        return gp.gate_of(prof, gate) or ({"id": gate, "short": gate.upper(), "covers": [gate]}
                                          if gate in CANONICAL else None)
    return current_gate(prof, study) if study is not None else (prof.get("gates") or [None])[0]


def enforcement(study: Any) -> str:
    """off | warn | block: the profile's ``se_enforcement`` (gate_profiles.yaml, owner D), else the
    protocol default (warn, PI ruling)."""
    try:
        from ..routers.gates import study_profile
        v = (study_profile(study) or {}).get("se_enforcement") if study is not None else None
    except Exception:  # noqa: BLE001
        v = None
    if v in ("off", "warn", "block"):
        return v
    try:
        return load().get("enforcement_default") or "warn"
    except Exception:  # noqa: BLE001
        return "warn"


async def phase(study_id: str, study: Any, *, lang: str = "en", gate: str | None = None,
                register: str = DEFAULT_REGISTER, seat: str | None = None) -> dict[str, Any]:
    """What the phase the study is in (or ``gate``) asks of it: entry, deliverables, analysis,
    coaching. Item states are evaluated live (``se_deliverables.evaluate``)."""
    from . import se_deliverables
    data = load()
    cur = current_gate_id(study) if study is not None else None
    pg = profile_gate(study, gate)
    if pg is None:
        return {"study_id": study_id, **empty_phase(gate), "current_gate": cur, "upcoming": [], "summary": {},
                "status": "complete" if study is not None else "no_study"}
    from . import gate_profiles as gp
    covers = [c for c in (pg.get("covers") or []) if c in CANONICAL]
    gid = gp.legacy_gate_id(pg.get("id")) or pg.get("id")
    ev = await se_deliverables.evaluate(study_id, gid, study=study, lang=lang, covers=covers)
    last = covers[-1] if covers else gid
    blk = (data.get("phases") or {}).get(last) or {}
    order = []
    try:
        from ..routers.gates import study_profile
        order = [g["id"] for g in (study_profile(study).get("gates") or [])] if study is not None else []
    except Exception:  # noqa: BLE001
        order = []
    upcoming = order[order.index(gid) + 1:] if gid in order else []
    srcs = []
    for c in covers:
        for s in ((data.get("phases") or {}).get(c) or {}).get("sources") or []:
            if s not in srcs:
                srcs.append(s)
    return {
        "study_id": study_id, "gate": gid, "gate_short": pg.get("short", str(gid).upper()), "covers": covers,
        "phase": GATE_PHASE.get(last), "phase_label": dict((blk.get("phase") or {}).get("label") or {}),
        "skeleton": bool(blk.get("skeleton")), "current_gate": cur, "upcoming": upcoming,
        "enforcement": enforcement(study),
        "entry": ev["entry"], "deliverables": ev["deliverables"], "analysis": ev["analysis"], "summary": ev["summary"],
        "coaching": coaching(covers, register=register, seat=seat, data=data),
        "sources": [{"id": s, "label": (data.get("sources") or {}).get(s, s)} for s in srcs],
    }


__all__ = ["GATE_PHASE", "ProtocolError", "all_cards", "coaching", "current_gate_id", "empty_phase", "enforcement",
           "load", "phase", "validate", "validate_at_startup"]
