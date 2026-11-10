"""SpaceCDF export family: packs — gate-specific review data packs (W1.09g, W4.01-W4.03).

Routes (prefix /api/exports): POST /docs/{study_id}?review=<gate>&fmt=zip|markdown&lang=en|fr

A pack reports what the team entered. The study is collected once
(``services.export_context.collect``: requirements, risks, roll-up, modes, analyses...) and every
document of the pack is built from it; the parametric design loop is no longer the source (it
gave an invented X-band link, a 2 kg AOCS and an empty risk register). Its mass and power totals
appear only in a "parametric cross-check" column (``crosscheck=false`` skips the loop).

``review`` is a gate of the study's profile (full ECSS: mdr, prr, srr, pdr, cdr; ESA IOD: cr...;
the NASA skin's ids), a canonical gate, the legacy ``mcr`` (= MDR) or a gate after CDR: ``qr``,
``ar``, ``frr``. Packs to PDR are complete; CDR, QR, AR and FRR are skeletons fed by the same
collector. What each pack holds is ``spacecdf_agents.exporters.docs.pack_catalog``; the review
data package itself is ``study_pack.py`` and the workbook ``master_budget.py``.

Zip layout::

    INDEX.md                          what is included and what is still missing
    docs/<gate>.docx, docs/<gate>.md  the review data package (Word + Markdown twin)
    documents/*.docx                  MRD, ConOps, TS, IRD, VP, VCD, RMP, SEMP, launch ICD, ...
    budgets/master_budget.xlsx        mass, power, data, link, pointing, margins, cost
    budgets/bill_of_materials.xlsx
    data/*.csv                        requirements, risks, interfaces, RTM

See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations

import csv
import importlib
import inspect
import io
import logging
import re
import zipfile
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, Response

from . import _common

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────── plan

def study_pack_plan(study: Any, review: str):
    """The ``PackPlan`` of ``review`` for the study's gate profile (``KeyError`` when unknown)."""
    from spacecdf_agents.exporters.docs.pack_catalog import plan_pack
    from ...services import gate_profiles as gp
    from ..gates import study_profile
    profile = study_profile(study) if study is not None else gp.get_profile(gp.default_profile_id())
    return plan_pack(review, profile=profile, profile_products=list(gp.load().get("products") or [])), profile


def available_packs(study: Any) -> list[dict]:
    from spacecdf_agents.exporters.docs.pack_catalog import available_gates
    from ...services import gate_profiles as gp
    from ..gates import study_profile
    profile = study_profile(study) if study is not None else gp.get_profile(gp.default_profile_id())
    return available_gates(profile)


async def _checklist(study_id: str, plan, profile: dict) -> dict:
    """The gate checklist evaluated on the server for the profile gate this pack is for."""
    gid = None
    for g in profile.get("gates") or []:
        if g.get("id") == plan.gate or list(g.get("covers") or []) == plan.covers:
            gid = g["id"]
            break
    if gid is None:
        return {}
    try:
        from ..gates import evaluate_study_gate
        res = await evaluate_study_gate(study_id, gid)
        return {"gate": gid, "criteria": res.get("criteria") or [], "summary": res.get("summary") or {},
                "state": res.get("state")}
    except Exception:  # noqa: BLE001 — the pack still builds without the checklist
        logger.warning("gate checklist for the %s pack failed", plan.gate, exc_info=True)
        return {}


async def _deliverables(study_id: str, study: Any, plan, sx: Any) -> dict:
    """The protocol deliverables of the pack's gate (SE-02): agent S's deliverables service
    (``services/se_deliverables.evaluate``), else the ``se_phase`` section when the study is at
    that gate, else the stub marker (the index lists it as an open item for S)."""
    gate = plan.covers[-1]
    try:
        from ...services import se_deliverables as sd
    except ImportError:
        sd = None
    fn = getattr(sd, "evaluate", None) if sd is not None else None
    if fn is not None:
        for call in (lambda: fn(study_id, gate), lambda: fn(study_id, study, gate=gate), lambda: fn(study_id, gate=gate)):
            try:
                out = call()
                if inspect.isawaitable(out):
                    out = await out
            except TypeError:
                continue
            except Exception:  # noqa: BLE001 — the pack still builds
                logger.warning("deliverables for the %s pack failed", gate, exc_info=True)
                break
            if isinstance(out, dict):
                its = out.get("deliverables") if out.get("deliverables") is not None else out.get("items")
                if out.get("status") == "not_implemented":
                    return {**out, "gate": gate}
                return {"gate": gate, "items": list(its or [])}
            if isinstance(out, list):
                return {"gate": gate, "items": out}
            break
    ph = getattr(sx, "se_phase", None) or {}
    if ph.get("deliverables") and str(ph.get("gate") or "").lower() == gate:
        return {"gate": gate, "items": list(ph["deliverables"])}
    return {"status": "not_implemented", "owner": "S", "work_package": "3.S2", "gate": gate, "items": []}


async def _diagram_catalogue(study_id: str, plan) -> list[dict]:
    """The diagrams the gate expects with their gaps (the figures are in Diagrams.docx)."""
    try:
        from ...services import diagrams as dg
        d = await dg.load(study_id)
        return dg.catalogue(d, list(plan.covers))
    except Exception:  # noqa: BLE001
        logger.warning("diagram catalogue for the %s pack failed", plan.gate, exc_info=True)
        return []


async def _crosscheck(study_id: str) -> dict:
    """Mass and power totals of the parametric design loop (comparison column only)."""
    try:
        _state, _req, result = await _common._run_design_for_study(study_id)
    except Exception:  # noqa: BLE001
        logger.info("parametric cross-check unavailable for %s", study_id, exc_info=True)
        return {}
    b = getattr(result, "budgets", None) or {}
    out: dict[str, Any] = {"source": "parametric design loop"}
    mass, power = b.get("mass"), b.get("power")
    if mass is not None:
        out["mass_nominal_kg"] = round(float(mass.total_nominal or 0), 3)
        out["mass_with_margin_kg"] = round(float(mass.total_with_margin or 0), 3)
    if power is not None:
        out["power_w"] = round(float(power.total_nominal or 0), 2)
    return out


# ─────────────────────────────────────────────────────────────── documents

async def _body(resp: Any) -> bytes:
    if hasattr(resp, "body_iterator"):
        chunks = []
        async for c in resp.body_iterator:
            chunks.append(c if isinstance(c, bytes) else str(c).encode("utf-8"))
        return b"".join(chunks)
    body = getattr(resp, "body", None)
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)
    raise TypeError(f"unexpected response {type(resp).__name__}")


def _csv(headers: list[str], rows: list[list[Any]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(headers)
    for r in rows:
        w.writerow(["" if v is None else v for v in r])
    return buf.getvalue().encode("utf-8-sig")


async def _route(family: str, study_id: str) -> bytes:
    from . import deorbit, launch_icd, rsssa, test_plan, thermal
    fn = {"thermal": thermal.export_thermal_report, "test_plan": test_plan.export_test_plan,
          "launch_icd": launch_icd.export_launch_icd, "deorbit": deorbit.export_deorbit,
          "rsssa": rsssa.export_rsssa}[family]
    return await _body(await fn(study_id, fmt="docx"))


async def _hook(module: str, sx: Any, plan, lang: str) -> bytes | None:
    """The owner's ``services/docx/<module>.pack_docx``, else the export core's interim hook
    (``services/docx/pack_hooks.HOOKS``), else None (listed as missing)."""
    fn = None
    try:
        mod = importlib.import_module(f"spacecdf_server.services.docx.{module}")
        fn = getattr(mod, "pack_docx", None)
    except ImportError:
        fn = None
    if fn is None:
        from ...services.docx.pack_hooks import HOOKS
        fn = HOOKS.get(module)
    if fn is None:
        return None
    out = fn(sx, gate=plan.gate, lang=lang)
    if inspect.isawaitable(out):
        out = await out
    return out or None


async def produce(doc, study_id: str, sx: Any, plan, lang: str, crosscheck: dict) -> tuple[bytes | None, str]:
    """(bytes or None, note) of one pack document."""
    from spacecdf_agents.exporters.docs.study_pack import REQ_HEADERS, View, requirement_rows
    kind, _, arg = doc.producer.partition(":")
    sxd = sx.as_dict()
    if kind == "docx":
        from .docx import docx_document
        return (await docx_document(arg, study_id, sx=sx, lang=lang))[1], ""
    if kind == "route":
        return await _route(arg, study_id), ""
    if kind == "vcd":
        from ..analyses_vv import export_vcd_docx
        return await _body(await export_vcd_docx(study_id)), ""
    if kind == "rtm":
        from ..analyses_vv import export_rtm_csv
        return await _body(await export_rtm_csv(study_id)), ""
    if kind == "diagrams":
        from ..diagrams import diagram_document
        return await _body(await diagram_document(study_id, set="all", lang=lang)), ""
    if kind == "xlsx" and arg == "master_budget":
        from spacecdf_agents.exporters.docs.master_budget import generate_master_budget
        return generate_master_budget(sxd, crosscheck=crosscheck), ""
    if kind == "xlsx" and arg == "bom":
        from spacecdf_agents.exporters.docs.master_budget import table_workbook
        from ..analyses_vv import BOM_COLUMNS, bom_rows
        _name, rows = bom_rows(study_id)
        return table_workbook([("Bill of materials", BOM_COLUMNS, rows)]), ""
    if kind == "csv":
        view = View(sxd)
        if arg == "requirements":
            reqs = view.requirements()
            return _csv(REQ_HEADERS + ["Rationale"], [row + [r.get("rationale") or ""]
                                                      for row, r in zip(requirement_rows(view, reqs), reqs)]), ""
        if arg == "risks":
            items = (sxd.get("risks") or {}).get("items") or []
            return _csv(["ID", "Description", "Category", "Likelihood", "Consequence", "Score", "Owner", "Status",
                         "Mitigation", "Source"],
                        [[r.get("id"), r.get("description"), r.get("category"), r.get("likelihood"),
                          r.get("consequence"), r.get("score"), r.get("owner"), r.get("status"), r.get("mitigation"),
                          r.get("source")] for r in items]), ""
        if arg == "interfaces":
            ifs = (sxd.get("elements") or {}).get("interfaces") or []
            return _csv(["Name", "Type", "Direction", "From", "To", "Status", "Properties"],
                        [[i.get("name"), i.get("interface_type"), i.get("direction"),
                          view.name(i.get("from_element_id") or i.get("source_element_id")),
                          view.name(i.get("to_element_id") or i.get("target_element_id")), i.get("status"),
                          "; ".join(f"{k}={v}" for k, v in (i.get("properties") or {}).items())] for i in ifs]), ""
    if kind == "hook":
        data = await _hook(arg, sx, plan, lang)
        if data is None:
            return None, f"nothing to report yet: the study has no data for it ({doc.owner} {doc.work_package})".strip()
        return data, ""
    return None, f"unknown producer {doc.producer}"


async def build_documents(study_id: str, sx: Any, plan, lang: str, crosscheck: dict) -> tuple[dict, dict]:
    """Every document of the plan except the package: ({doc id: bytes}, {doc id: status})."""
    files: dict[str, bytes] = {}
    status: dict[str, dict] = {}
    for d in plan.documents:
        try:
            data, note = await produce(d, study_id, sx, plan, lang, crosscheck)
        except HTTPException as exc:
            data, note = None, f"generator refused: {exc.detail}"
        except Exception as exc:  # noqa: BLE001 — one failing generator must not lose the pack
            logger.warning("pack document %s failed for %s", d.id, study_id, exc_info=True)
            data, note = None, f"generator failed: {type(exc).__name__}: {exc}"[:200]
        if data:
            files[d.id] = data
            status[d.id] = {"status": "included", "note": note}
        else:
            status[d.id] = {"status": "missing", "note": note or "generator returned nothing"}
    return files, status


def index_markdown(plan, pkg, status: dict, lang: str, deliverables: dict | None = None) -> str:
    from spacecdf_agents.exporters.docs.study_pack import Tr
    t = Tr("fr" if str(lang).startswith("fr") else "en")
    lines = [f"# {plan.short} — {pkg.study_name}: {t('Package index')}", ""]
    lines += [f"{t.pick(plan.name)}; " + ("gates covered" if t.lang != "fr" else "jalons couverts")
              + f": {', '.join(c.upper() for c in plan.covers)}"
              + ("" if plan.complete else (" (skeleton)" if t.lang != "fr" else " (squelette)")), ""]
    lines += [f"| {t('Document')} | {t('File')} | {t('Standard')} | {t('Status')} | {t('Note')} |", "|---|---|---|---|---|",
              f"| {pkg.subtitle} | docs/{plan.gate}.docx, docs/{plan.gate}.md | ECSS-M-ST-10C | {t('included')} | |"]
    for d in plan.documents:
        st = status.get(d.id) or {}
        lines.append(f"| {t.pick(d.title)} | {d.file if st.get('status') == 'included' else ''} | {d.standard} | "
                     f"{t(st.get('status') or 'missing')} | {st.get('note') or ''} |")
    lines += ["", f"## {t('Products expected at this review')}", "",
              f"| {t('Product')} | {t('Maturity')} | {t('Owner')} |", "|---|---|---|"]
    lines += [f"| {t.pick(p['label'])} | {p['maturity']} | {p.get('owner_seat') or ''} |" for p in plan.products]
    dl = deliverables or {}
    fr = t.lang == "fr"
    lines += ["", "## " + ("Systems-engineering deliverables" if not fr else "Livrables d’ingénierie système"), ""]
    if dl.get("items"):
        lines += [f"| {t('Item')} | {t('Owner')} | {t('Status')} | {t('Evidence')} |", "|---|---|---|---|"]
        for d in dl["items"]:
            lab = d.get("label")
            lines.append(f"| {t.pick(lab) if isinstance(lab, dict) else (lab or d.get('id') or '')} | {d.get('owner_seat') or ''} | "
                         f"{d.get('state') or ''} | {str(d.get('evidence') or '').replace('|', '/')} |")
    else:
        lines.append(("Not evaluated yet (deliverables service: " if not fr else "Pas encore évalués (service des livrables : ")
                     + f"{dl.get('owner') or 'S'} {dl.get('work_package') or '3.S2'})")
    lines += ["", f"## {t('Open items')} ({len(pkg.open_items)})", ""]
    lines += [f"{i + 1}. {o['text']}" + (f" ({o['owner']})" if o.get("owner") else "") for i, o in enumerate(pkg.open_items)]
    return "\n".join(lines).rstrip() + "\n"


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s or "").strip("_") or "study"


# ─────────────────────────────────────────────────────────────── route

@router.post("/docs/{study_id}")
async def export_design_document(
    study_id: str,
    review: str = Query(default="srr", description="Gate of the study's profile (mdr, prr, srr, pdr, cdr; cr...), "
                        "legacy mcr, or qr, ar, frr"),
    fmt: str = Query(default="zip", description="Output format: zip (default) or markdown"),
    lang: str = Query(default="en", description="Document language: en (default) or fr. Headings and fixed text of "
                      "the review data package and the index; the other Word/Excel documents stay English (W9)."),
    crosscheck: bool = Query(default=True, description="Add the parametric design loop's mass and power totals as a "
                             "cross-check column"),
):
    """The review data pack of one gate, built from what the team entered.

    ``fmt=zip`` (default) streams the pack (review data package in Word and Markdown, the
    documents the gate expects, the master budget, the index). ``fmt=markdown`` returns the
    review data package as Markdown in JSON (``review_type``, ``document_markdown``,
    ``sections``) without building the other documents.
    """
    from spacecdf_agents.exporters.docs.study_pack import build_package, render_docx, render_markdown
    from ...services.export_context import collect
    from ..studies import get_study_store

    study = get_study_store().get(study_id)
    if study is None:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    try:
        plan, profile = study_pack_plan(study, review or "srr")
    except KeyError:
        raise HTTPException(status_code=422, detail={"unknown_review": review,
                                                     "reviews": [g["id"] for g in available_packs(study)]})
    lang = "fr" if str(lang or "").lower().startswith("fr") else "en"
    sx = await collect(study_id, gate=plan.margin_gate, lang=lang)
    cross = await _crosscheck(study_id) if crosscheck else {}
    checklist = await _checklist(study_id, plan, profile)
    extras = {"checklist": checklist, "crosscheck": cross, "deliverables": await _deliverables(study_id, study, plan, sx),
              "diagrams": await _diagram_catalogue(study_id, plan)}

    if fmt.lower() == "markdown":
        status = {d.id: {"status": "missing", "note": "built in the zip pack (fmt=zip)"} for d in plan.documents}
        pkg = build_package(sx.as_dict(), plan, lang=lang, extras={"documents": status, **extras})
        md = render_markdown(pkg)
        return JSONResponse(content={"review_type": plan.gate, "short": plan.short, "covers": plan.covers,
                                     "document_markdown": md, "sections": len(pkg.sections),
                                     "section_titles": pkg.sections, "open_items": len(pkg.open_items),
                                     "open_item_list": pkg.open_items,
                                     "deliverables": extras["deliverables"]})

    files, status = await build_documents(study_id, sx, plan, lang, cross)
    pkg = build_package(sx.as_dict(), plan, lang=lang, extras={"documents": status, **extras})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("INDEX.md", index_markdown(plan, pkg, status, lang, extras["deliverables"]))
        zf.writestr(f"docs/{plan.gate}.md", render_markdown(pkg))
        zf.writestr(f"docs/{plan.gate}.docx", render_docx(pkg))
        for d in plan.documents:
            if d.id in files:
                zf.writestr(d.file, files[d.id])
    filename = f"{_slug(plan.short)}_{_slug(sx.study_name)}_review_pack.zip"
    return Response(content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
