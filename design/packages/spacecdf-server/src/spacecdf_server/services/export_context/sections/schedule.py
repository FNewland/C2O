"""Section ``schedule``: project settings, milestones per gate (with QR, AR, FRR, model deliveries
and launch), the WBS, the long-lead items and the bottom-up cost in EUR and CAD (W11a). Owner: A.

Shape: ``{settings{}, milestones[], work_packages[], long_lead[], cost{}, counts{}, status}``;
``status`` is ``"proposed"`` when no milestone or work package is stored yet (the default plan is
shown, not stored), else ``"ok"``. Read only.
"""
from __future__ import annotations


def empty() -> dict:
    return {"settings": {}, "milestones": [], "work_packages": [], "long_lead": [], "cost": {},
            "counts": {"milestones": 0, "work_packages": 0}, "status": "empty"}


async def collect(ctx) -> dict:
    from ... import schedule as svc
    from ...ait import DEFAULT_MODELS, list_models
    out = await svc.schedule_summary(ctx.study_id)
    if out["milestones"] or out["work_packages"]:
        return {**out, "status": "ok"}
    start = out["settings"].get("start_date") or ""
    models = await list_models(ctx.study_id) or [dict(m) for m in DEFAULT_MODELS]
    ms = [{**m, "date": svc.add_months(start, m["month"]), "origin": "default"}
          for m in svc._proposed_milestones(ctx.study, models)]
    wps = [{**w, "origin": "default", "elements": []} for w in svc._proposed_wbs(ctx.elements)]
    return {**out, "milestones": ms, "work_packages": wps,
            "counts": {"milestones": len(ms), "work_packages": len(wps)}, "status": "proposed"}
