"""Section ``stakeholders``: the stakeholder register (category, authority, engagement), the
needs (SN-…), the MOEs (placeholders flagged "to co-define") and the governance notes. Owner: S (3.S3).

Shape: ``{"items": [stakeholder], "needs": [need], "moes": [moe], "counts": {stakeholders, needs,
moes, placeholder_moes, categories, by_category, unclassified, needs_without_moe},
"governance_notes": {…}}`` (``routers/moes.register``).
"""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "needs": [], "moes": [], "counts": {}}


async def collect(ctx) -> dict:
    from ....routers.moes import list_moes, register
    if ctx.study is None:
        return empty()
    return register(ctx.study, await list_moes(ctx.study_id))
