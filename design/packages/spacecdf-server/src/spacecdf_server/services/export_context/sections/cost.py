"""Section ``cost``: the priced cost model: labour, test campaigns, hardware, reserve, launch (zero
when provided), total. Owner: A (3.A7).

Shape (``services/cost_pricing.summary``)::

    items:        [{category, name, name_fr, wbs_code, quantity, unit, unit_cost_keur, percent_of_base,
                    total_keur, source, basis}]
    by_category:  {labour, test_campaign, hardware, other, reserve, launch: kEUR}
    total_keur:   the priced total (None until priced); total_meur, target_meur, within_target,
                  labour_person_months, reference_class{en, fr}
"""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "by_category": {}, "total_keur": None}


_KEEP = ("category", "name", "name_fr", "wbs_code", "quantity", "unit", "unit_cost_keur", "percent_of_base",
         "total_keur", "source", "basis", "origin")


async def collect(ctx) -> dict:
    from ...cost_pricing import summary
    s = await summary(ctx.study_id)
    if not s["priced"]:
        return {"status": "empty", **empty()}
    return {"status": "ok", "items": [{k: r.get(k) for k in _KEEP} for r in s["items"]],
            "by_category": s["by_category"], "total_keur": s["total_keur"], "total_meur": s["total_meur"],
            "target_meur": s["target_meur"], "within_target": s["within_target"],
            "labour_person_months": s["labour_person_months"], "reference_class": s["reference_class"],
            "category_labels": s["category_labels"]}
