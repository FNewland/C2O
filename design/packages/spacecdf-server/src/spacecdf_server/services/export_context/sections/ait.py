"""Section ``ait``: model philosophy, test matrix, environment levels and the verification items
by stage (W8a). Owner: A.

Shape: ``{philosophy, models[], tests[], environment{}, items[], counts{items, by_stage, by_method,
by_level, models, tests}, status}``. ``status`` is ``"proposed"`` when the study has no model or
test of its own yet (the default protoflight philosophy and test matrix are shown, not stored),
else ``"ok"``. Read only.
"""
from __future__ import annotations


def empty() -> dict:
    return {"philosophy": None, "models": [], "tests": [], "environment": {}, "items": [],
            "counts": {"items": 0, "by_stage": {}, "by_method": {}, "by_level": {}, "models": 0, "tests": 0},
            "status": "empty"}


async def collect(ctx) -> dict:
    from ...ait import DEFAULT_MODELS, DEFAULT_PHILOSOPHY, DEFAULT_TESTS, _codes_for, _env_for, verification_plan
    plan = await verification_plan(ctx.study_id)
    if plan["models"] or plan["tests"]:
        return {**plan, "status": "ok"}
    # nothing stored yet: show the default proposal so a pack is never empty, flagged as such
    reqs = [{"code": i["code"], "text": i["text"], "verification_method": "".join(i["methods"])}
            for i in plan["items"]]
    env = plan["environment"]
    models = [{**m, "philosophy": DEFAULT_PHILOSOPHY, "origin": "default"} for m in DEFAULT_MODELS]
    tests = [{"code": t["code"], "name": t["name"], "name_fr": t["name_fr"], "category": t["category"],
              "models": list(t["models"]), "level": t["level"], "stage": t["stage"], "facility": t["facility"],
              "level_source": t.get("level_source") or env.get("level_source", ""),
              "environment": _env_for(t, env), "requirement_codes": _codes_for(t.get("match") or {}, reqs),
              "origin": "default"} for t in DEFAULT_TESTS]
    from ...ait import plan_from
    out = plan_from([], models, tests, None, env)
    out["items"], out["counts"]["items"] = plan["items"], plan["counts"]["items"]
    for k in ("by_stage", "by_method", "by_level"):
        out["counts"][k] = plan["counts"][k]
    out["status"] = "proposed"
    return out
