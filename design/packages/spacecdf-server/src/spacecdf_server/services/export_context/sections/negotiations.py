"""Section ``negotiations``: the negotiation records: issue, coupled parameters, seats, options with
effects, agreed values, sign-offs, reopen trigger. Owner: H (3.H6).

Shape (the keys of the step-0 stub kept): ``{"items": [...], "counts": {total, proposed, agreed,
reopened}}``. Each item is ``services/negotiations.view``: the record, ``issue_text`` in the
export language, ``live_parameters`` [{key, label, value, unit, source, owner_seat, agreed_value}],
``seat_state`` [{seat, label, signed, signoff}], ``options`` [{key, label, values, effects}],
``chosen_option``, ``agreed``, ``trigger`` {fired, condition, value} and ``links``.
"""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    from ... import negotiations as ns
    recs = await ns.list_records(ctx.study_id)
    if not recs:
        return {**empty(), "counts": ns.counts([])}
    items = await ns.views(ctx.study_id, recs)
    lang = getattr(ctx, "lang", "en") or "en"
    for it in items:
        it["issue_text"] = (it["issue"].get(lang) or it["issue"].get("en") or "")
        it["reopen_text"] = (it.get("reopen_trigger_fr") if lang == "fr" and it.get("reopen_trigger_fr") else it.get("reopen_trigger")) or ""
        it.pop("history", None)
    return {"items": items, "counts": ns.counts(recs)}
