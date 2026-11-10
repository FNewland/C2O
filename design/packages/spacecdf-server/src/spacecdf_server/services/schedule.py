"""SpaceCDF — schedule-lite: project settings, milestones, work packages, long-lead items (W11a).

* **Milestones** come from the study's gate profile (``configs/gate_profiles.yaml``): one per
  profile gate, then the reviews the profile does not model yet (QR, AR), the Flight Readiness
  Review (FRR, PI decision Nov 2026), the model deliveries of the model philosophy
  (``services/ait.py``) and the launch. Months are counted from the project start; the dates
  follow from ``project_settings.start_date`` (default: launch target − 37 months, else next month).
* **Work packages** (ECSS-M-ST-10C §5.4 WBS): management, systems engineering and PA, one per
  space subsystem element of the product tree, AIT, software, ground segment (one per ground
  element), launch, operations and disposal. An element can name its package through
  ``design_elements.work_package_id`` (the WBS code); the package then lists it.
* **Long-lead items** come from the BOM lead times (KB ``lead_time_weeks``).
* **Cost** is ``cost_engine.study_cost`` with the project settings (currency, launch provided).

Rows proposed here have ``origin = "proposed"``; user rows (``origin = "user"``) are kept.
"""
from __future__ import annotations

import datetime as _dt
import logging
import uuid
from typing import Any

from sqlalchemy import delete, select

logger = logging.getLogger(__name__)

#: month (from the project start) of each canonical review, for a 36-month development with
#: breadboards at month 6, the engineering model at 18 and the protoflight model at 30
GATE_MONTH = {"mdr": 0, "mcr": 0, "prr": 2, "srr": 4, "pdr": 9, "cdr": 18, "qr": 31, "ar": 34, "frr": 35,
              "launch": 37}
EXTRA_REVIEWS = [
    {"code": "QR", "gate_id": "qr", "name": "Qualification Review", "name_fr": "Revue de qualification"},
    {"code": "AR", "gate_id": "ar", "name": "Acceptance Review", "name_fr": "Revue de recette"},
    {"code": "FRR", "gate_id": "frr", "name": "Flight Readiness Review", "name_fr": "Revue d’aptitude au vol"},
]
LAUNCH = {"code": "LAUNCH", "kind": "launch", "name": "Launch", "name_fr": "Lancement"}

#: default WBS (code, name, name_fr, owner seat, start, end, kind) — ``kind`` = "space" / "ground"
#: expands into one child package per subsystem / ground element of the product tree
DEFAULT_WBS: list[dict[str, Any]] = [
    {"code": "1", "name": "Project management", "name_fr": "Gestion de projet", "owner": "team_leader", "start": 0, "end": 37},
    {"code": "2", "name": "Systems engineering and product assurance", "name_fr": "Ingénierie système et assurance produit",
     "owner": "systems_engineer", "start": 0, "end": 35},
    {"code": "3", "name": "Payload", "name_fr": "Charge utile", "owner": "payload_lead", "start": 0, "end": 30, "domain": "payload"},
    {"code": "4", "name": "Spacecraft platform", "name_fr": "Plateforme du véhicule spatial", "owner": "systems_engineer",
     "start": 2, "end": 30, "kind": "space"},
    {"code": "5", "name": "Assembly, integration and test", "name_fr": "Assemblage, intégration et essais",
     "owner": "systems_engineer", "start": 12, "end": 34},
    {"code": "6", "name": "Flight software", "name_fr": "Logiciel de vol", "owner": "comms_engineer", "start": 4, "end": 30},
    {"code": "7", "name": "Ground segment", "name_fr": "Segment sol", "owner": "mission_analyst", "start": 4, "end": 34,
     "kind": "ground"},
    {"code": "8", "name": "Launch services and licensing", "name_fr": "Services de lancement et licences",
     "owner": "team_leader", "start": 0, "end": 37},
    {"code": "9", "name": "Mission operations", "name_fr": "Exploitation de la mission", "owner": "mission_analyst",
     "start": 30, "end": 37},
    {"code": "10", "name": "Disposal", "name_fr": "Retrait de service", "owner": "propulsion_engineer", "start": 9, "end": 37},
]


def _uid() -> str:
    return uuid.uuid4().hex


def add_months(start: str, months: int) -> str:
    """``"YYYY-MM"`` + n months → ``"YYYY-MM"`` (empty when ``start`` is not a date)."""
    try:
        y, m = int(start[:4]), int(start[5:7])
    except (ValueError, TypeError, IndexError):
        return ""
    total = y * 12 + (m - 1) + int(months)
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def default_start(study: Any) -> str:
    """Project start: 37 months before the launch target, else the month after today."""
    req = getattr(study, "requirements", None)
    target = str(getattr(req, "launch_date_target", "") or "") if req is not None else ""
    if len(target) >= 7 and target[4] == "-":
        s = add_months(target[:7], -GATE_MONTH["launch"])
        if s:
            return s
    today = _dt.date.today()
    return add_months(f"{today.year:04d}-{today.month:02d}", 1)


# ─────────────────────────────────────────────────────────────── settings

_SETTING_FIELDS = ("start_date", "currency", "eur_to_cad", "launch_provided", "launch_cost_keur", "notes")


def _settings_dict(r, study: Any = None) -> dict:
    if r is None:
        from .cost_engine import DEFAULT_EUR_TO_CAD
        return {"study_id": None, "start_date": default_start(study), "currency": "EUR",
                "eur_to_cad": DEFAULT_EUR_TO_CAD, "launch_provided": False, "launch_cost_keur": None, "notes": "",
                "stored": False}
    return {"study_id": r.study_id, "start_date": r.start_date or default_start(study), "currency": r.currency,
            "eur_to_cad": r.eur_to_cad, "launch_provided": bool(r.launch_provided),
            "launch_cost_keur": r.launch_cost_keur, "notes": r.notes, "stored": True}


def _study(study_id: str) -> Any:
    from ..routers.studies import get_study_store
    return get_study_store().get(study_id)


async def get_settings(study_id: str) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_schedule import ProjectSettingsRow
    async with get_session_factory()() as s:
        row = (await s.execute(select(ProjectSettingsRow).where(ProjectSettingsRow.study_id == study_id))).scalars().first()
        out = _settings_dict(row, _study(study_id))
        out["study_id"] = study_id
        return out


async def put_settings(study_id: str, data: dict) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_schedule import ProjectSettingsRow
    async with get_session_factory()() as s:
        row = (await s.execute(select(ProjectSettingsRow).where(ProjectSettingsRow.study_id == study_id))).scalars().first()
        if row is None:
            from .cost_engine import DEFAULT_EUR_TO_CAD
            row = ProjectSettingsRow(id=_uid(), study_id=study_id, start_date=default_start(_study(study_id)),
                                     currency="EUR", eur_to_cad=DEFAULT_EUR_TO_CAD, launch_provided=False)
            s.add(row)
        for k in _SETTING_FIELDS:
            if k in data:
                v = data[k]
                if k == "currency" and v:
                    v = str(v).upper()[:3]
                setattr(row, k, v if v is not None or k == "launch_cost_keur" else getattr(row, k))
        await s.commit()
    await _redate(study_id)
    return await get_settings(study_id)


# ─────────────────────────────────────────────────────────────── rows

def _ms_dict(r) -> dict:
    return {"id": r.id, "code": r.code, "kind": r.kind, "gate_id": r.gate_id, "name": r.name, "name_fr": r.name_fr,
            "month": r.month, "date": r.date, "status": r.status, "origin": r.origin, "order": r.order}


def _wp_dict(r) -> dict:
    return {"id": r.id, "code": r.code, "parent_code": r.parent_code, "name": r.name, "name_fr": r.name_fr,
            "element_id": r.element_id, "owner_seat": r.owner_seat, "start_month": r.start_month,
            "end_month": r.end_month, "deliverables": list(r.deliverables_json or []), "origin": r.origin,
            "order": r.order}


def _wbs_key(code: str) -> tuple:
    out = []
    for p in str(code).split("."):
        out.append((0, int(p)) if p.isdigit() else (1, p))
    return tuple(out)


async def list_milestones(study_id: str) -> list[dict]:
    from ..db.engine import get_session_factory
    from ..db.models_schedule import MilestoneRow
    async with get_session_factory()() as s:
        rows = (await s.execute(select(MilestoneRow).where(MilestoneRow.study_id == study_id))).scalars().all()
        out = [_ms_dict(r) for r in rows]
    out.sort(key=lambda m: (m["month"] if m["month"] is not None else 10_000, m["order"], m["code"]))
    return out


async def list_work_packages(study_id: str) -> list[dict]:
    from ..db.engine import get_session_factory
    from ..db.models_schedule import WorkPackageRow
    async with get_session_factory()() as s:
        rows = (await s.execute(select(WorkPackageRow).where(WorkPackageRow.study_id == study_id))).scalars().all()
        out = [_wp_dict(r) for r in rows]
    out.sort(key=lambda w: _wbs_key(w["code"]))
    # elements that name their package (design_elements.work_package_id = WBS code)
    from .rollup import study_elements
    named: dict[str, list[dict]] = {}
    for e in study_elements(study_id):
        if e.get("work_package_id"):
            named.setdefault(str(e["work_package_id"]), []).append({"id": e["id"], "name": e.get("name", "")})
    for w in out:
        w["elements"] = named.get(w["code"], [])
    return out


def _proposed_milestones(study: Any, models: list[dict]) -> list[dict]:
    from . import gate_profiles as gp
    profile = gp.get_profile(getattr(study, "gate_profile", "") or None) if study is not None else gp.get_profile(None)
    out: list[dict] = []
    seen_ids: set[str] = set()
    for g in profile.get("gates") or []:
        covers = [str(c).lower() for c in (g.get("covers") or [g.get("id")])]
        month = max(GATE_MONTH.get(c, 0) for c in covers)
        name = g.get("name") or {}
        out.append({"code": str(g.get("short") or g["id"]).upper(), "kind": "review", "gate_id": g["id"],
                    "name": name.get("en", g["id"]), "name_fr": name.get("fr", ""), "month": month})
        seen_ids.update(covers)
        seen_ids.add(str(g["id"]).lower())
    for r in EXTRA_REVIEWS:
        if r["gate_id"] not in seen_ids:
            out.append({**r, "kind": "review", "month": GATE_MONTH[r["gate_id"]]})
    for m in models:
        if m.get("due_month") is None:
            continue
        out.append({"code": m["code"], "kind": "model", "gate_id": "",
                    "name": f"{m.get('name') or m['code']} delivered",
                    "name_fr": f"{m.get('name_fr') or m['code']} livré", "month": int(m["due_month"])})
    out.append({**LAUNCH, "gate_id": "", "month": GATE_MONTH["launch"]})
    # wave 3 (3.A3): the licence filings (licensing record, DEFAULT_FILINGS) are milestones too,
    # counted from the launch; a filing that starts before the project shows as a negative month
    for f in filing_milestones(study, GATE_MONTH["launch"]):
        out.append(f)
    return out


def filing_milestones(study: Any, launch_month: int, filings: list[dict] | None = None) -> list[dict]:
    """One milestone per licence filing: ``month = launch month + start_months`` (negative when
    the filing starts before the project), with ``before_project_start`` set (pure)."""
    try:
        from .licensing import DEFAULT_FILINGS
    except Exception:  # noqa: BLE001
        return []
    rows = filings if filings is not None else [dict(f) for f in DEFAULT_FILINGS]
    out = []
    for f in rows:
        sm = f.get("start_months")
        if not isinstance(sm, (int, float)):
            continue
        title = f.get("title") or {}
        month = int(launch_month + sm)
        out.append({"code": f"FIL-{str(f.get('id') or '').upper()[:20]}", "kind": "filing", "gate_id": "",
                    "name": f"{f.get('authority') or ''}: {title.get('en', f.get('id'))}"[:200],
                    "name_fr": f"{f.get('authority') or ''} : {title.get('fr', '')}"[:200], "month": month})
    return out


#: months between a part's delivery and the model it goes into (incoming inspection, unit tests)
RECEIVING_MONTHS = 1
WEEKS_PER_MONTH = 4.345


def need_by(long_lead: list[dict], models: list[dict], start_date: str = "") -> list[dict]:
    """Order and freeze dates of the long-lead parts (pure). A part is needed one month before the
    first model built with flight-representative hardware (the engineering model, else the
    protoflight or flight model); the order goes out its (longest) lead time earlier; the
    specification freezes one month before the order."""
    first = None
    for code in ("EM", "QM", "PFM", "FM"):
        m = next((x for x in models if x.get("code") == code and x.get("due_month") is not None), None)
        if m is not None:
            first = m
            break
    out = []
    for item in long_lead:
        weeks = item.get("max_weeks") or item.get("lead_time_weeks") or 0
        lt_months = int(-(-float(weeks) // WEEKS_PER_MONTH)) if weeks else 0     # ceil
        row = {"name": item.get("name") or item.get("part") or "", "lead_time_weeks": weeks,
               "lead_time_min_weeks": item.get("min_weeks", item.get("lead_time_min_weeks")),
               "lead_time_source": item.get("source", item.get("lead_time_source")),
               "model": first.get("code") if first else None}
        if first is not None:
            need = int(first["due_month"]) - RECEIVING_MONTHS
            order = need - lt_months
            row.update(model_month=int(first["due_month"]), need_by_month=need, order_by_month=order,
                       freeze_by_month=order - 1, before_project_start=order - 1 < 0)
            if start_date:
                row.update(order_by_date=add_months(start_date, order), freeze_by_date=add_months(start_date, order - 1),
                           need_by_date=add_months(start_date, need))
        out.append(row)
    return out


def _proposed_wbs(elements: list[dict]) -> list[dict]:
    from .rule_inputs import by_id, effective_segment
    idx = by_id(elements)
    subsystems = [e for e in elements if e.get("element_type") == "subsystem"
                  and effective_segment(e, idx) == "space"]
    subsystems.sort(key=lambda e: (str(e.get("subsystem_domain") or ""), e.get("name") or ""))
    ground = [e for e in elements if effective_segment(e, idx) == "ground"
              and e.get("element_type") in ("system", "subsystem") and e.get("parent_id") in idx
              and idx[e["parent_id"]].get("element_type") == "segment"]
    ground.sort(key=lambda e: e.get("name") or "")
    out: list[dict] = []
    for w in DEFAULT_WBS:
        base = {"code": w["code"], "parent_code": "", "name": w["name"], "name_fr": w["name_fr"],
                "owner_seat": w["owner"], "start_month": w["start"], "end_month": w["end"], "element_id": None}
        if w.get("domain"):
            hit = next((e for e in subsystems if e.get("subsystem_domain") == w["domain"]), None)
            base["element_id"] = hit["id"] if hit else None
        out.append(base)
        children: list[dict] = []
        if w.get("kind") == "space":
            children = [e for e in subsystems if e.get("subsystem_domain") != "payload"]
        elif w.get("kind") == "ground":
            children = ground
        for i, e in enumerate(children, start=1):
            out.append({"code": f"{w['code']}.{i}", "parent_code": w["code"], "name": e.get("name") or "",
                        "name_fr": e.get("name") or "", "owner_seat": e.get("owner_position") or w["owner"],
                        "start_month": w["start"], "end_month": w["end"], "element_id": e["id"]})
    return out


async def _redate(study_id: str) -> None:
    """Recompute every milestone date from its month and the project start."""
    from ..db.engine import get_session_factory
    from ..db.models_schedule import MilestoneRow
    start = (await get_settings(study_id))["start_date"]
    async with get_session_factory()() as s:
        for r in (await s.execute(select(MilestoneRow).where(MilestoneRow.study_id == study_id))).scalars():
            if r.month is not None:
                r.date = add_months(start, r.month)
        await s.commit()


async def propose(study_id: str, *, replace: bool = False) -> dict[str, Any]:
    """Write the default milestones and work packages (user rows are kept)."""
    from ..db.engine import get_session_factory
    from ..db.models_schedule import MilestoneRow, WorkPackageRow
    from . import ait
    from .rollup import study_elements

    study = _study(study_id)
    models = await ait.list_models(study_id) or [dict(m) for m in ait.DEFAULT_MODELS]
    start = (await get_settings(study_id))["start_date"]
    ms = _proposed_milestones(study, models)
    wps = _proposed_wbs(study_elements(study_id))
    added = 0
    async with get_session_factory()() as s:
        if replace:
            await s.execute(delete(MilestoneRow).where(MilestoneRow.study_id == study_id))
            await s.execute(delete(WorkPackageRow).where(WorkPackageRow.study_id == study_id))
        have = {r.code: r for r in (await s.execute(select(MilestoneRow).where(MilestoneRow.study_id == study_id))).scalars()}
        for i, m in enumerate(ms):
            row = have.get(m["code"])
            fields = {**m, "date": add_months(start, m["month"]), "order": i}
            if row is None:
                s.add(MilestoneRow(id=_uid(), study_id=study_id, origin="proposed", **fields))
                added += 1
            elif row.origin == "proposed":
                for k, v in fields.items():
                    setattr(row, k, v)
        have_w = {r.code: r for r in (await s.execute(select(WorkPackageRow).where(WorkPackageRow.study_id == study_id))).scalars()}
        for i, w in enumerate(wps):
            row = have_w.get(w["code"])
            if row is None:
                s.add(WorkPackageRow(id=_uid(), study_id=study_id, origin="proposed", order=i, **w))
                added += 1
            elif row.origin == "proposed":
                for k, v in w.items():
                    setattr(row, k, v)
                row.order = i
        await s.commit()
    return {"milestones": await list_milestones(study_id), "work_packages": await list_work_packages(study_id),
            "added": added}


_MS_FIELDS = ("code", "kind", "gate_id", "name", "name_fr", "month", "date", "status", "order")
_WP_FIELDS = ("code", "parent_code", "name", "name_fr", "element_id", "owner_seat", "start_month", "end_month", "order")


async def upsert(study_id: str, kind: str, data: dict, row_id: str | None = None) -> dict | None:
    """Create or update a milestone (``kind = "milestones"``) or work package (``"work_packages"``)."""
    from ..db.engine import get_session_factory
    from ..db.models_schedule import MilestoneRow, WorkPackageRow
    model, fields, conv = ((MilestoneRow, _MS_FIELDS, _ms_dict) if kind == "milestones"
                           else (WorkPackageRow, _WP_FIELDS, _wp_dict))
    start = (await get_settings(study_id))["start_date"]
    async with get_session_factory()() as s:
        if row_id:
            row = await s.get(model, row_id)
            if row is None or row.study_id != study_id:
                return None
        else:
            row = model(id=_uid(), study_id=study_id, code=str(data.get("code") or "X"))
            s.add(row)
        for k in fields:
            if k in data:
                setattr(row, k, data[k])
        if kind == "work_packages" and data.get("deliverables") is not None:
            row.deliverables_json = [str(d) for d in data["deliverables"]]
        if kind == "milestones" and "month" in data and "date" not in data and row.month is not None:
            row.date = add_months(start, row.month)
        row.origin = "user"
        await s.commit()
        return conv(row)


async def delete_row(study_id: str, kind: str, row_id: str) -> bool:
    from ..db.engine import get_session_factory
    from ..db.models_schedule import MilestoneRow, WorkPackageRow
    model = MilestoneRow if kind == "milestones" else WorkPackageRow
    async with get_session_factory()() as s:
        row = await s.get(model, row_id)
        if row is None or row.study_id != study_id:
            return False
        await s.delete(row)
        await s.commit()
        return True


# ─────────────────────────────────────────────────────────────── long lead and summary

def long_lead_items(elements: list[dict], n: int = 5) -> list[dict]:
    """The ``n`` space parts with the longest procurement lead time (KB or element values only)."""
    from .bom_generator import generate_bom_from_elements
    bom = generate_bom_from_elements(elements)
    rows = [r for r in bom.get("long_lead") or []]
    seg = {l["line"]: l.get("segment", "space") for l in bom.get("lines") or []}
    return [r for r in rows if seg.get(r["line"], "space") == "space"][:n]


async def schedule_summary(study_id: str) -> dict[str, Any]:
    """Everything the Project panel and the export collector show (read only)."""
    from . import cost_engine
    from .rollup import study_elements
    settings = await get_settings(study_id)
    els = study_elements(study_id)
    try:
        cost = await cost_engine.study_cost(study_id, settings)
    except Exception as exc:  # noqa: BLE001 — the schedule must show even if the cost fails
        logger.warning("study cost failed for %s: %s", study_id, exc)
        cost = {"error": f"{type(exc).__name__}: {exc}"}
    ms = await list_milestones(study_id)
    wps = await list_work_packages(study_id)
    from . import ait
    lead = long_lead_items(els, n=10)
    models = await ait.list_models(study_id) or [dict(m) for m in ait.DEFAULT_MODELS]
    nb = need_by(lead, models, settings.get("start_date") or "")
    warnings = []
    for m in ms:
        if m.get("kind") == "filing" and isinstance(m.get("month"), int) and m["month"] < 0:
            warnings.append({"code": m["code"], "kind": "filing_before_start", "month": m["month"],
                             "text": {"en": f"{m['name']} starts {-m['month']} month(s) before the project start",
                                      "fr": f"{m.get('name_fr') or m['name']} commence {-m['month']} mois avant le début du projet"}})
    for r in nb:
        if r.get("before_project_start"):
            warnings.append({"code": r["name"], "kind": "order_before_start", "month": r.get("freeze_by_month"),
                             "text": {"en": f"{r['name']}: the specification must freeze before the project start",
                                      "fr": f"{r['name']} : la spécification doit être figée avant le début du projet"}})
    return {"settings": settings, "milestones": ms, "work_packages": wps, "long_lead": lead, "need_by": nb,
            "warnings": warnings, "cost": cost,
            "counts": {"milestones": len(ms), "work_packages": len(wps), "filings": sum(1 for m in ms if m.get("kind") == "filing")}}


__all__ = ["GATE_MONTH", "add_months", "filing_milestones", "need_by", "default_start", "get_settings", "put_settings", "list_milestones",
           "list_work_packages", "propose", "upsert", "delete_row", "long_lead_items", "schedule_summary"]
