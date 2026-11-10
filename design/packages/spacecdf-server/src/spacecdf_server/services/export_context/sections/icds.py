"""Section ``icds``: every ICD with its latest issue, state (draft, Issue A, B …, baselined) and the
sign-off of both owning seats, plus the inventory under issue control and the unsigned ICDs by
seat. Owner: R (3.R6). Data: ``services.interface_requirements.icd_status``.
"""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    from ...interface_requirements import icd_status
    st = await icd_status(ctx.study_id)
    keep = ("icd_ref", "title", "refs", "codes", "controlled", "issue", "revision", "state", "provider_seat",
            "consumer_seat", "signed", "agreed", "stale", "unsigned", "required_at", "history")
    return {"items": [{k: i.get(k) for k in keep} for i in st["items"]], "counts": st["counts"],
            "inventory": st["inventory"], "unsigned_by_seat": st["unsigned_by_seat"]}
