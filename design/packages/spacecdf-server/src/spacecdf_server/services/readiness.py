"""Server-side level readiness (Nov 2026): one checklist for the workbench and the gates.

``GET /api/studies/{sid}/readiness?level=&element_id=`` returns::

    {study_id, level, element_id, items: [{id, label{en,fr}, ok, detail{en,fr}, counts}],
     passed, total, ready}

"Interfaces defined" uses the coverage rules of ``configs/interface_rules.yaml``
(every powered unit has a power link, every data unit a data link, every unit a
mechanical mount and a thermal path); suggested links count, rejected ones do
not. "Suggested links reviewed" passes when no suggestion is left at the level.
The same coverage feeds the consistency check (CON-IF-01) and the PDR gate
criterion PDR-EC-02.
"""
from __future__ import annotations

from typing import Any

from .interface_model import is_active
from .interface_proposer import Context, conflicts_for, load_rules, RuleConfigError


def _bi(en: str, fr: str) -> dict[str, str]:
    return {"en": en, "fr": fr}


def _names(items: list[str], limit: int = 6) -> str:
    return ", ".join(items[:limit]) + (" …" if len(items) > limit else "")


def study_class(study_id: str) -> str | None:
    try:
        from ..routers.studies import get_study_store
        st = get_study_store().get(study_id)
        req = getattr(st, "requirements", None)
        return getattr(req, "spacecraft_class", None)
    except Exception:  # noqa: BLE001
        return None


def build_context(study_id: str, elements: list[dict], spacecraft_class: str | None = None) -> Context:
    return Context(elements, load_rules(), spacecraft_class=spacecraft_class, study_class=study_class(study_id))


def interface_coverage(ctx: Context, interfaces: list[dict], unit_ids: list[str] | None = None) -> dict[str, Any]:
    """Which coverage needs are met. ``unit_ids`` limits the check (default: every element)."""
    cov_rules = ctx.config.get("coverage") or []
    touching: dict[tuple[str, str], int] = {}
    for i in interfaces:
        if not is_active(i):
            continue
        t = i.get("interface_type") or i.get("type")
        for end in (i.get("from_element_id"), i.get("to_element_id")):
            touching[(end, t)] = touching.get((end, t), 0) + 1
    ids = unit_ids if unit_ids is not None else list(ctx.units)
    by_type: dict[str, dict[str, int]] = {}
    missing: list[dict] = []
    covered_units: set[str] = set()
    for uid in ids:
        u = ctx.units.get(uid)
        if not u or u.el.get("in_scope") is False:
            continue
        for c in cov_rules:
            sel = c.get("applies_to") or {}
            if not ctx.matches(u, sel):
                continue
            covered_units.add(uid)
            bt = by_type.setdefault(c["id"], {"required": 0, "met": 0})
            bt["required"] += 1
            if touching.get((uid, c["type"])):
                bt["met"] += 1
            else:
                missing.append({"element_id": uid, "name": u.name, "need": c["id"], "type": c["type"],
                                "label": dict(c["label"])})
    required = sum(v["required"] for v in by_type.values())
    met = sum(v["met"] for v in by_type.values())
    return {"required": required, "met": met, "by_type": by_type, "missing": missing,
            "units": sorted(covered_units)}


async def compute_readiness(study_id: str, *, level: int | None = None, element_id: str | None = None) -> dict:
    from ..routers.elements import _elements, _interfaces

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    interfaces = [i for i in _interfaces.values() if i.get("study_id") == study_id and not i.get("deleted_at")]
    children = [e for e in elements if (e.get("parent_id") == element_id if element_id else not e.get("parent_id"))]
    in_scope = [e for e in children if e.get("in_scope") is not False]
    child_ids = {e["id"] for e in children}
    items: list[dict] = []

    # 1. Elements defined
    n = len(children)
    items.append({
        "id": "elements_defined", "label": _bi("Elements defined", "Éléments définis"), "ok": n > 0,
        "detail": _bi(f"{n} elements at this level", f"{n} éléments à ce niveau") if n
        else _bi("Add at least one element", "Ajoutez au moins un élément"),
        "counts": {"elements": n, "in_scope": len(in_scope)},
    })

    # 2. Requirements defined (same rule as the former client-side check)
    if in_scope:
        try:
            from ..routers.requirements import _requirements, ensure_requirements_loaded
            try:
                await ensure_requirements_loaded()
            except Exception:  # noqa: BLE001
                pass
            reqs = [r for r in _requirements.values() if r.get("study_id") == study_id]
        except Exception:  # noqa: BLE001
            reqs = []
        with_reqs = {r.get("element_id") for r in reqs if r.get("element_id") in child_ids}
        parent_reqs = any(r.get("element_id") == element_id for r in reqs) if element_id else False
        missing = [e.get("name", "") for e in in_scope if e["id"] not in with_reqs]
        items.append({
            "id": "requirements_defined", "label": _bi("Requirements defined", "Exigences définies"),
            "ok": parent_reqs or bool(with_reqs),
            "detail": _bi(f"Missing requirements: {_names(missing)}", f"Exigences manquantes : {_names(missing)}")
            if missing else _bi(f"{len(with_reqs)} elements have requirements",
                                f"{len(with_reqs)} éléments ont des exigences"),
            "counts": {"with_requirements": len(with_reqs), "missing": len(missing)},
        })

    # 3. Interfaces defined (expected-link coverage) + 4. suggestions reviewed + 5. conflicts
    scope_ifaces = [i for i in interfaces if i.get("from_element_id") in child_ids or i.get("to_element_id") in child_ids]
    ctx = None
    try:
        ctx = build_context(study_id, elements)
    except RuleConfigError as e:
        items.append({
            "id": "interfaces_defined", "label": _bi("Interfaces defined", "Interfaces définies"), "ok": False,
            "detail": _bi("Interface rules are invalid: " + "; ".join(e.errors[:3]),
                          "Les règles d'interface sont invalides : " + "; ".join(e.errors[:3])),
            "counts": {"errors": len(e.errors)},
        })
    if ctx is not None and in_scope:
        cov = interface_coverage(ctx, interfaces, [e["id"] for e in in_scope])
        # Elements no coverage rule applies to (segments, systems): with siblings, each needs at least one link
        others = [e for e in in_scope if e["id"] not in cov["units"]]
        loose: list[str] = []
        if len(in_scope) > 1:
            linked = {x for i in interfaces if is_active(i) for x in (i.get("from_element_id"), i.get("to_element_id"))}
            loose = [e.get("name", "") for e in others if e["id"] not in linked]
        required = cov["required"] + (len(others) if len(in_scope) > 1 else 0)
        met = cov["met"] + ((len(others) - len(loose)) if len(in_scope) > 1 else 0)
        if required:
            miss_en = [f"{m['name']} ({m['label']['en']})" for m in cov["missing"]] + \
                      [f"{n_} (any link)" for n_ in loose]
            miss_fr = [f"{m['name']} ({m['label']['fr']})" for m in cov["missing"]] + \
                      [f"{n_} (aucune liaison)" for n_ in loose]
            ok = not miss_en
            items.append({
                "id": "interfaces_defined", "label": _bi("Interfaces defined", "Interfaces définies"), "ok": ok,
                "detail": _bi(f"{met}/{required} expected links present", f"{met}/{required} liaisons attendues présentes")
                if ok else _bi(f"Missing: {_names(miss_en)}", f"Manquantes : {_names(miss_fr)}"),
                "counts": {"required": required, "met": met, "by_type": cov["by_type"],
                           "missing": cov["missing"] + [{"element_id": e["id"], "name": e.get("name", ""), "need": "any",
                                                         "type": None, "label": _bi("any link", "une liaison")}
                                                        for e in others if e.get("name", "") in loose]},
            })

    suggested = [i for i in scope_ifaces if i.get("status") == "suggested"]
    items.append({
        "id": "suggested_reviewed", "label": _bi("Suggested links reviewed", "Liaisons suggérées examinées"),
        "ok": not suggested,
        "detail": _bi(f"{len(suggested)} suggested links to accept, edit or reject",
                      f"{len(suggested)} liaisons suggérées à accepter, modifier ou rejeter") if suggested
        else _bi("No suggestion left to review", "Aucune suggestion à examiner"),
        "counts": {"suggested": len(suggested),
                   "accepted": sum(1 for i in scope_ifaces if i.get("status") == "accepted"),
                   "rejected": sum(1 for i in scope_ifaces if i.get("status") == "rejected")},
    })

    if ctx is not None and scope_ifaces:
        conf = conflicts_for(ctx, scope_ifaces)
        alarms = sum(1 for c in conf if c["severity"] == "alarm")
        items.append({
            "id": "interface_conflicts", "label": _bi("No interface conflicts", "Aucun conflit d'interface"),
            "ok": not conf,
            "detail": _bi(f"{len(conf)} conflicts ({alarms} on accepted links)",
                          f"{len(conf)} conflits ({alarms} sur des liaisons acceptées)") if conf
            else _bi("Protocols, voltages and bands agree", "Protocoles, tensions et bandes concordent"),
            "counts": {"conflicts": len(conf), "alarm": alarms, "caution": len(conf) - alarms},
        })

    # 5b. Allocations agreed (wave 3, 3.A2): the ledger lines of the elements at this level, each
    # agreed by its owner seat (shown only once the ledger has lines for this level)
    try:
        from ..db.models_alloc import AllocationLedgerRow
        from . import study_rows
        led = [r for r in await study_rows.list_rows(AllocationLedgerRow, study_id)
               if r.get("line_kind") != "reserve" and r.get("element_id") in child_ids]
    except Exception:  # noqa: BLE001
        led = []
    if led:
        open_ = [r for r in led if r.get("status") != "agreed"]
        disputed = sum(1 for r in open_ if r.get("status") == "disputed")
        names = sorted({f"{r.get('element_code') or ''} {r.get('budget_type')}".strip() for r in open_})
        items.append({
            "id": "allocations_agreed", "label": _bi("Allocations agreed", "Allocations acceptées"), "ok": not open_,
            "detail": _bi(f"{len(led) - len(open_)}/{len(led)} agreed; waiting: {_names(names)}",
                          f"{len(led) - len(open_)}/{len(led)} acceptées ; en attente : {_names(names)}") if open_
            else _bi(f"All {len(led)} allocation lines agreed by their owners",
                     f"Les {len(led)} lignes d’allocation sont acceptées par leurs responsables"),
            "counts": {"lines": len(led), "agreed": len(led) - len(open_), "disputed": disputed},
        })

    # 6. All elements frozen
    if in_scope:
        unfrozen = [e.get("name", "") for e in in_scope if not e.get("frozen")]
        items.append({
            "id": "all_frozen", "label": _bi("All elements frozen", "Tous les éléments figés"), "ok": not unfrozen,
            "detail": _bi(f"Unfrozen: {_names(unfrozen)}", f"Non figés : {_names(unfrozen)}") if unfrozen
            else _bi("All elements frozen — ready for next level", "Tous les éléments sont figés — prêt pour le niveau suivant"),
            "counts": {"unfrozen": len(unfrozen)},
        })

    passed = sum(1 for i in items if i["ok"])
    return {"study_id": study_id, "level": level, "element_id": element_id, "items": items,
            "passed": passed, "total": len(items), "ready": passed == len(items)}
