"""Cost pricing at MDR/PRR (wave 3, 3.A7; PI addendum): labour, test campaigns, hardware, reserve,
launch provided.

``price(study_id)`` proposes the priced lines (``cost_items``) from:

* **hardware**: the selected equipment, bottom-up (``cost_engine.study_cost``: list prices or
  flagged estimates, never invented), one line per subsystem, plus ground hardware when priced;
  spares as a share of the flight hardware;
* **labour**: one line per WBS work package (``services/schedule``): staff and student
  full-time equivalents × the package's months × the loaded rate (students on credit are counted
  in person-months at a zero rate, so the effort shows without a cost);
* **test campaigns**: one line per external environmental test of the AIT matrix and model
  (vibration, thermal-vacuum, EMC, shock): facility days × day rate;
* **other**: ground support equipment, licence and frequency-coordination fees;
* **reserve**: a management reserve, a percentage of everything above;
* **launch**: zero when the schedule settings say the launch is provided, else the study's
  launch cost.

The rates are the C2O reference class of ``configs/cost_pricing.yaml``; a line the team edits
(``origin = user``) is kept by a later ``price``. ``total(study_id)`` is what the design loop's cost
agent quotes and what MDR-EC-08 / PRR-EC-11 judge (wired by R).
"""
from __future__ import annotations

import logging
from typing import Any

from ..db.models_cost import COST_CATEGORIES, CostItemRow
from . import rule_config as rc
from . import study_rows as sr

logger = logging.getLogger(__name__)

CONFIG = "cost_pricing"
CATEGORY_LABEL = {
    "labour": {"en": "Labour", "fr": "Main-d’œuvre"}, "test_campaign": {"en": "Test campaigns", "fr": "Campagnes d’essais"},
    "hardware": {"en": "Hardware", "fr": "Matériel"}, "software": {"en": "Software", "fr": "Logiciel"},
    "facilities": {"en": "Facilities", "fr": "Installations"}, "launch": {"en": "Launch", "fr": "Lancement"},
    "operations": {"en": "Operations", "fr": "Exploitation"}, "reserve": {"en": "Reserve", "fr": "Réserve"},
    "other": {"en": "Other", "fr": "Autres"},
}
_TEST_KIND = (("thermal-vacuum", "tvac"), ("thermal vacuum", "tvac"), ("tvac", "tvac"), ("sine", "sine"),
              ("random", "random"), ("shock", "shock"), ("emc", "emc"))


def _r(v: float) -> float:
    return round(float(v), 2)


def _test_kinds(t: dict) -> list[str]:
    """External campaign kinds a test needs (a "sine + random vibration" event needs both)."""
    cat = str(t.get("category") or "").lower()
    if cat == "emc":
        return ["emc"]
    if cat not in ("environmental", ""):
        return []
    text = f"{t.get('code') or ''} {t.get('name') or ''}".lower()
    out: list[str] = []
    for word, kind in _TEST_KIND:
        if word in text and kind not in out:
            out.append(kind)
    return out


async def proposed_lines(study_id: str) -> list[dict[str, Any]]:
    from . import ait, schedule
    from .cost_engine import study_cost
    cfg = rc.load(CONFIG)
    settings = await schedule.get_settings(study_id)
    cost = await study_cost(study_id, settings)
    lines: list[dict[str, Any]] = []

    def add(**kw: Any) -> None:
        kw.setdefault("source", "C2O reference class (configs/cost_pricing.yaml)")
        kw["order"] = len(lines)
        kw["origin"] = "proposed"
        lines.append(kw)

    # hardware: bottom-up from the selected equipment
    for s in cost.get("by_subsystem") or []:
        add(category="hardware", name=f"Flight hardware: {s['subsystem']}", name_fr=f"Matériel de vol : {s['subsystem']}",
            wbs_code="4", quantity=1, unit="lot", unit_cost_keur=_r(s["keur"]), total_keur=_r(s["keur"]),
            source="selected equipment (list prices and flagged estimates)", basis="cost_engine.study_cost")
    gh = float((cost.get("ground_hardware") or {}).get("keur") or 0.0)
    if gh > 0:
        add(category="hardware", name="Ground station hardware", name_fr="Matériel des stations sol", wbs_code="7",
            quantity=1, unit="lot", unit_cost_keur=_r(gh), total_keur=_r(gh), source="selected equipment")
    fh = float((cost.get("flight_hardware") or {}).get("keur") or 0.0)
    sp = float(cfg.get("spares_percent_of_flight_hardware") or 0.0)
    if fh > 0 and sp > 0:
        add(category="hardware", name="Spares", name_fr="Pièces de rechange", wbs_code="4", quantity=sp, unit="% of flight HW",
            percent_of_base=sp, unit_cost_keur=None, total_keur=_r(fh * sp / 100),
            basis=f"{sp:g} % of the flight hardware")
    # labour: per work package
    rates = cfg.get("labour_rates_keur_per_pm") or {}
    fte = cfg.get("wbs_labour_fte") or {}
    wps = await schedule.list_work_packages(study_id)
    for wp in wps:
        code = str(wp.get("code") or "")
        if code not in fte:
            continue
        start, end = wp.get("start_month"), wp.get("end_month")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end <= start:
            continue
        months = float(end) - float(start)
        f = fte[code]
        staff_pm = float(f.get("staff") or 0) * months
        student_pm = float(f.get("student") or 0) * months
        total = staff_pm * float(rates.get("staff") or 0) + student_pm * float(rates.get("student") or 0)
        add(category="labour", name=f"Labour: {wp.get('name')}", name_fr=f"Main-d’œuvre : {wp.get('name_fr') or wp.get('name')}",
            wbs_code=code, quantity=_r(staff_pm + student_pm), unit="person-month",
            unit_cost_keur=_r(total / (staff_pm + student_pm)) if staff_pm + student_pm else None, total_keur=_r(total),
            basis=(f"{f.get('staff', 0):g} staff FTE × {months:g} months × {rates.get('staff', 0):g} kEUR/pm"
                   f" + {f.get('student', 0):g} student FTE × {months:g} months × {rates.get('student', 0):g} kEUR/pm"),
            data_json={"staff_pm": _r(staff_pm), "student_pm": _r(student_pm), "months": months})
    # test campaigns: one per external environmental test and model
    camp = cfg.get("test_campaigns") or {}
    seen: set[tuple[str, str]] = set()
    for t in await ait.list_tests(study_id):
        for kind in _test_kinds(t):
            if kind not in camp:
                continue
            for model in (t.get("models") or ["PFM"]):
                if (kind, model) in seen:
                    continue
                seen.add((kind, model))
                c = camp[kind]
                days, rate = float(c.get("days") or 1), float(c.get("keur_per_day") or 0)
                lab = c.get("label") or {}
                add(category="test_campaign", name=f"{lab.get('en', kind)} ({model})",
                    name_fr=f"{lab.get('fr', kind)} ({model})", wbs_code="5", quantity=days, unit="facility day",
                    unit_cost_keur=rate, total_keur=_r(days * rate),
                    basis=f"AIT test {t.get('code')}: {days:g} days × {rate:g} kEUR/day",
                    data_json={"test_code": t.get("code"), "model": model, "kind": kind})
    gse = float(cfg.get("ground_support_equipment_keur") or 0.0)
    if gse:
        add(category="other", name="Ground support equipment", name_fr="Équipements sol de soutien", wbs_code="5",
            quantity=1, unit="lot", unit_cost_keur=gse, total_keur=_r(gse))
    fees = float(cfg.get("licence_and_coordination_fees_keur") or 0.0)
    if fees:
        add(category="other", name="Licence and frequency-coordination fees", name_fr="Droits de licence et coordination des fréquences",
            wbs_code="8", quantity=1, unit="lot", unit_cost_keur=fees, total_keur=_r(fees))
    # launch
    launch = cost.get("launch") or {}
    add(category="launch", name="Launch", name_fr="Lancement", wbs_code="8", quantity=1, unit="launch",
        unit_cost_keur=_r(launch.get("keur") or 0.0), total_keur=_r(launch.get("keur") or 0.0),
        source=str(launch.get("basis") or ""), basis="provided" if launch.get("provided") else str(launch.get("basis") or ""))
    return lines


def _reserve_line(lines: list[dict], pct: float) -> dict:
    base = sum(float(ln.get("total_keur") or 0.0) for ln in lines if ln.get("category") not in ("reserve", "launch"))
    return {"category": "reserve", "name": "Management reserve", "name_fr": "Réserve pour aléas", "wbs_code": "1",
            "quantity": pct, "unit": "% of base", "percent_of_base": pct, "total_keur": _r(base * pct / 100),
            "basis": f"{pct:g} % of {base:.1f} kEUR (launch excluded)", "source": "C2O reference class (configs/cost_pricing.yaml)",
            "origin": "proposed"}


async def price(study_id: str, *, replace: bool = False) -> dict[str, Any]:
    """(Re)price the model: proposed lines are replaced, the team's lines are kept; the reserve is
    recomputed on the new base unless the team set it."""
    cfg = rc.load(CONFIG)
    existing = await sr.list_rows(CostItemRow, study_id)
    keep = [r for r in existing if r.get("origin") == "user" and not replace]
    await sr.delete_rows(CostItemRow, study_id, ids=[r["id"] for r in existing if r not in keep])
    kept_names = {(r.get("category"), r.get("name")) for r in keep}
    new = [ln for ln in await proposed_lines(study_id) if (ln["category"], ln["name"]) not in kept_names]
    if not any(r.get("category") == "reserve" for r in keep):
        new.append({**_reserve_line(keep + new, float(cfg.get("reserve_percent") or 0.0)), "order": 900})
    await sr.insert_rows(CostItemRow, study_id, new, prefix="ci")
    await refresh_reserve(study_id)
    return await summary(study_id)


async def refresh_reserve(study_id: str) -> None:
    rows = await sr.list_rows(CostItemRow, study_id)
    for r in rows:
        if r.get("category") == "reserve" and r.get("percent_of_base") is not None:
            base = sum(float(x.get("total_keur") or 0.0) for x in rows if x.get("category") not in ("reserve", "launch"))
            await sr.update_row(CostItemRow, r["id"], {"total_keur": _r(base * float(r["percent_of_base"]) / 100),
                                                       "basis": f"{float(r['percent_of_base']):g} % of {base:.1f} kEUR (launch excluded)"})


async def summary(study_id: str) -> dict[str, Any]:
    rows = await sr.list_rows(CostItemRow, study_id)
    by_cat: dict[str, float] = {}
    for r in rows:
        by_cat[r.get("category") or "other"] = by_cat.get(r.get("category") or "other", 0.0) + float(r.get("total_keur") or 0.0)
    total = sum(by_cat.values())
    target = None
    try:
        from ..routers.studies import get_study_store
        st = get_study_store().get(study_id)
        target = getattr(getattr(st, "requirements", None), "target_cost_meur", None)
    except Exception:  # noqa: BLE001
        pass
    labour_pm = sum(float(r.get("quantity") or 0.0) for r in rows if r.get("category") == "labour")
    return {"study_id": study_id, "items": rows,
            "by_category": {k: _r(v) for k, v in sorted(by_cat.items(), key=lambda kv: COST_CATEGORIES.index(kv[0])
                                                          if kv[0] in COST_CATEGORIES else 99)},
            "category_labels": CATEGORY_LABEL, "total_keur": _r(total) if rows else None,
            "total_meur": round(total / 1000, 3) if rows else None, "target_meur": target,
            "within_target": (total / 1000 <= target) if rows and target else None,
            "labour_person_months": _r(labour_pm), "priced": bool(rows),
            "reference_class": (rc.load(CONFIG).get("reference_class") or {})}


async def total(study_id: str) -> dict[str, Any] | None:
    """The priced total (None until the model is priced): what the cost agent and the cost
    criteria quote."""
    s = await summary(study_id)
    if not s["priced"]:
        return None
    return {"total_keur": s["total_keur"], "total_meur": s["total_meur"], "by_category": s["by_category"],
            "launch_keur": s["by_category"].get("launch", 0.0), "labour_keur": s["by_category"].get("labour", 0.0),
            "target_meur": s["target_meur"], "within_target": s["within_target"]}


ITEM_FIELDS = ("category", "name", "name_fr", "wbs_code", "element_id", "quantity", "unit", "unit_cost_keur",
               "percent_of_base", "total_keur", "source", "basis")


def clean_item(body: dict) -> dict:
    f = {k: body[k] for k in ITEM_FIELDS if k in body}
    if f.get("category") and f["category"] not in COST_CATEGORIES:
        raise ValueError(f"category must be one of {COST_CATEGORIES}")
    q, u = f.get("quantity"), f.get("unit_cost_keur")
    if "total_keur" not in f and isinstance(q, (int, float)) and isinstance(u, (int, float)):
        f["total_keur"] = _r(q * u)
    return f
