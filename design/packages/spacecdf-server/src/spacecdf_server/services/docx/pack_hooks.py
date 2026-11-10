"""SpaceCDF — review pack hooks served by the export core until their owners add ``pack_docx``.

The pack catalogue (``spacecdf_agents.exporters.docs.pack_catalog``) lists six documents that
other work packages own: ``trades`` and ``review_report`` (D), ``ait`` and ``schedule`` (A),
``licensing`` (L) and ``tmtc`` (H). ``routers/exports/packs.py`` first calls the owner's
``spacecdf_server.services.docx.<module>.pack_docx(sx, *, gate, lang)``; when the owner has not
defined one, it calls ``HOOKS[<module>]`` here, which builds the document from the owner's own
generator or data (nothing is invented; an empty model gives ``None`` and the pack index lists the
document as missing). Owner: X. An owner who adds ``pack_docx`` overrides the entry here.
"""
from __future__ import annotations

import io
from typing import Any, Awaitable, Callable

from docx import Document

from ._common import (
    _add_cover_page,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _cell_str,
    _compact_table,
    _orient,
    _setup_margins,
    _setup_styles,
)


def _fr(lang: str) -> bool:
    return str(lang or "").lower().startswith("fr")


def _save(doc: Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _new(title: str, standard: str, name: str, code: str) -> Document:
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    _add_cover_page(doc, title, standard, name)
    _add_toc_placeholder(doc)
    _add_footer(doc, name, code)
    return doc


# ─────────────────────────────────────────────────────────────── D: trades, review report

async def trades(sx: Any, *, gate: str, lang: str) -> bytes | None:
    """The trade-off report (D, W6.01): ``services.docx.trades.generate_trades_docx``."""
    if not (getattr(sx, "trades", None) or {}).get("items"):
        return None
    from .trades import generate_trades_docx
    return generate_trades_docx(sx, lang=lang)


async def review_report(sx: Any, *, gate: str, lang: str) -> bytes | None:
    """The report of the previous review (D, W4.08): the latest gate before ``gate`` in the
    study's profile that has a review decision, else the gate just before it."""
    from fastapi import HTTPException

    from ...routers.gates import review_report_data
    from .review_report import generate_review_report_docx
    gates = getattr(sx, "gates", None) or {}
    order = [g.get("id") for g in (gates.get("profile") or {}).get("gates") or gates.get("gates") or []]
    if gate not in order or order.index(gate) == 0:
        return None
    earlier = order[: order.index(gate)]
    records = gates.get("records") or {}
    decided = [g for g in earlier if ((records.get(g) or {}).get("review") or {}).get("decision")]
    prev = decided[-1] if decided else earlier[-1]
    try:
        data = await review_report_data(sx.study_id, prev)
    except HTTPException:
        return None
    return generate_review_report_docx(data, lang=lang)


# ─────────────────────────────────────────────────────────────── A: AIT programme, schedule

async def ait(sx: Any, *, gate: str, lang: str) -> bytes | None:
    """The model philosophy and AIT programme (A, W8a): models with their dates from the schedule,
    the test campaign of each model, the AIT work packages. The verification matrix and the
    environmental levels are in the verification plan of the same pack."""
    a = getattr(sx, "ait", None) or {}
    models, tests = a.get("models") or [], a.get("tests") or []
    if not (models or tests):
        return None
    fr = _fr(lang)
    sch = getattr(sx, "schedule", None) or {}
    dates = {m.get("code"): m.get("date") for m in sch.get("milestones") or [] if m.get("kind") == "model"}
    name = getattr(sx, "study_name", "") or ""
    doc = _new("Philosophie des modèles et programme AIT" if fr else "Model philosophy and AIT programme",
               "ECSS-E-ST-10-03C / ECSS-E-ST-10-02C", name, "AIT")
    _add_section(doc, "1", "Philosophie des modèles" if fr else "Model philosophy",
                 (f"Philosophie : {a.get('philosophy') or '—'}." if fr else f"Philosophy: {a.get('philosophy') or '—'}.")
                 + (" Proposition par défaut (panneau AIT)." if fr and a.get("status") == "proposed" else
                    " Default proposal (AIT panel)." if a.get("status") == "proposed" else ""))
    _add_table(doc, ["Modèle" if fr else "Model", "Niveau" if fr else "Level", "Mois" if fr else "Month", "Date",
                     "Standard de construction" if fr else "Build standard", "Objet" if fr else "Purpose"],
               [[f"{m.get('code')}: {(m.get('name_fr') if fr else None) or m.get('name') or ''}", _cell_str(m.get("level")),
                 _cell_str(m.get("due_month")), _cell_str(dates.get(m.get("code"))), _cell_str(m.get("build_standard")),
                 _cell_str((m.get("purpose_fr") if fr else None) or m.get("purpose"))] for m in models])
    _orient(doc, landscape=True)
    _add_section(doc, "2", "Campagne d’essais par modèle" if fr else "Test campaign by model")
    for i, m in enumerate(models, start=1):
        rows = [t for t in tests if m.get("code") in (t.get("models") or [])]
        _add_section(doc, f"2.{i}", f"{m.get('code')} — {(m.get('name_fr') if fr else None) or m.get('name') or ''} ({len(rows)})")
        if rows:
            _compact_table(doc, ["Essai" if fr else "Test", "Catégorie" if fr else "Category", "Niveau" if fr else "Level",
                                 "Moyen" if fr else "Facility", "Source des niveaux" if fr else "Level source",
                                 "Étape" if fr else "Stage", "État" if fr else "Status", "Vérifie" if fr else "Verifies"],
                           [[f"{t.get('code')}: {(t.get('name_fr') if fr else None) or t.get('name') or ''}", t.get("category"),
                             t.get("level"), t.get("facility"), t.get("level_source"), t.get("stage"), t.get("status"),
                             t.get("requirement_codes") or []] for t in rows],
                           widths_cm=[5.4, 2.0, 1.8, 4.0, 3.0, 1.4, 1.6, 5.4])
    others = [t for t in tests if not set(t.get("models") or []) & {m.get("code") for m in models}]
    if others:
        _add_section(doc, f"2.{len(models) + 1}", "Essais sans modèle" if fr else "Tests without a model")
        _compact_table(doc, ["Essai" if fr else "Test", "Étape" if fr else "Stage", "Vérifie" if fr else "Verifies"],
                       [[f"{t.get('code')}: {t.get('name') or ''}", t.get("stage"), t.get("requirement_codes") or []] for t in others])
    _orient(doc, landscape=False)
    wps = [w for w in sch.get("work_packages") or [] if any(k in str(w.get("name") or "").lower()
                                                             for k in ("ait", "assembly", "integration", "test", "verification"))]
    if wps:
        _add_section(doc, "3", "Lots de travail AIT" if fr else "AIT work packages")
        _add_table(doc, ["OT" if fr else "WBS", "Nom" if fr else "Name", "Poste" if fr else "Seat", "Mois" if fr else "Months"],
                   [[_cell_str(w.get("code")), _cell_str((w.get("name_fr") if fr else None) or w.get("name")),
                     _cell_str(w.get("owner_seat")), f"{w.get('start_month')}–{w.get('end_month')}"] for w in wps])
    return _save(doc)


async def schedule(sx: Any, *, gate: str, lang: str) -> bytes | None:
    """Schedule, WBS and long-lead items (A, W11a) from the ``schedule`` section."""
    sch = getattr(sx, "schedule", None) or {}
    ms, wps = sch.get("milestones") or [], sch.get("work_packages") or []
    if not (ms or wps):
        return None
    fr = _fr(lang)
    st = sch.get("settings") or {}
    name = getattr(sx, "study_name", "") or ""
    doc = _new("Calendrier, OT et articles à long délai" if fr else "Schedule, WBS and long-lead items",
               "ECSS-M-ST-60C", name, "SCH")
    intro = (f"Début du projet : {st.get('start_date') or '—'}. Lancement fourni : {'oui' if st.get('launch_provided') else 'non'}."
             if fr else f"Project start: {st.get('start_date') or '—'}. Launch provided: {'yes' if st.get('launch_provided') else 'no'}.")
    _add_section(doc, "1", "Jalons" if fr else "Milestones", intro)
    _add_table(doc, ["Code", "Nom" if fr else "Name", "Nature" if fr else "Kind", "Mois" if fr else "Month", "Date",
                     "État" if fr else "Status"],
               [[_cell_str(m.get("code")), _cell_str((m.get("name_fr") if fr else None) or m.get("name")), _cell_str(m.get("kind")),
                 _cell_str(m.get("month")), _cell_str(m.get("date")), _cell_str(m.get("status"))] for m in ms])
    _add_section(doc, "2", "Organigramme des tâches (OT)" if fr else "Work breakdown structure")
    _add_table(doc, ["OT" if fr else "WBS", "Nom" if fr else "Name", "Poste" if fr else "Seat", "Début" if fr else "Start",
                     "Fin" if fr else "End", "Éléments" if fr else "Elements"],
               [[_cell_str(w.get("code")), _cell_str((w.get("name_fr") if fr else None) or w.get("name")),
                 _cell_str(w.get("owner_seat")), _cell_str(w.get("start_month")), _cell_str(w.get("end_month")),
                 _cell_str(w.get("elements"))] for w in wps])
    ll = sch.get("long_lead") or []
    if ll:
        _add_section(doc, "3", "Articles à long délai" if fr else "Long-lead items")
        _add_table(doc, ["Article" if fr else "Item", "Délai min (sem.)" if fr else "Min lead (weeks)",
                         "Délai max (sem.)" if fr else "Max lead (weeks)", "Source"],
                   [[_cell_str(x.get("name")), _cell_str(x.get("min_weeks")), _cell_str(x.get("max_weeks")),
                     _cell_str(x.get("source"))] for x in ll])
    cost = sch.get("cost") or {}
    if cost.get("by_subsystem"):
        cur = cost.get("currency") or "CAD"
        _add_section(doc, "4", "Coût du matériel de vol" if fr else "Flight hardware cost")
        _add_table(doc, ["Sous-système" if fr else "Subsystem", "k€", f"k{cur}"],
                   [[_cell_str(x.get("subsystem")), _cell_str(x.get("keur")), _cell_str(x.get(f"k{cur.lower()}"))]
                    for x in cost["by_subsystem"]]
                   + [["Total", _cell_str((cost.get("flight_hardware") or {}).get("keur")),
                       _cell_str((cost.get("flight_hardware") or {}).get(f"k{cur.lower()}"))]])
    return _save(doc)


# ─────────────────────────────────────────────────────────────── L: licensing

async def licensing(sx: Any, *, gate: str, lang: str) -> bytes | None:
    """The licensing status document (L, W5.04): ``licensing_docs.status`` (assignments, filings
    and their state) rendered by ``docx.regulatory``."""
    lic = getattr(sx, "licensing", None) or {}
    if lic.get("status") == "not_implemented" or not (lic.get("filings") or lic.get("assignments")):
        return None
    from .. import licensing_docs as ld
    from .regulatory import render_regulatory_docx
    return render_regulatory_docx(ld.status(sx))


# ─────────────────────────────────────────────────────────────── H: TM/TC, FDIR, AOCS

#: CDR model kinds per chapter of the TM/TC, FDIR and AOCS document
_FDIR_KINDS = ("monitors", "event_actions", "fdir_levels", "limits", "safe_mode", "load_shed", "line_states")
_AOCS_KINDS = ("aocs_modes", "aocs_transitions", "aocs_control")
_OPS_KINDS = ("ttc", "rate_tiers", "link_framing", "positions", "gonogo", "flight_rules", "pass_classes")


def _kind_table(doc: Document, rows: list[dict], max_cols: int = 8) -> None:
    datas = [r.get("data") or {} for r in rows]
    keys: list[str] = []
    for d in datas:
        for k, v in d.items():
            if k not in keys and not isinstance(v, (dict, list)) and not k.startswith("_"):
                keys.append(k)
    keys = keys[:max_cols]
    if not keys:
        for d in datas:
            doc.add_paragraph("; ".join(f"{k}: {_cell_str(v)}" for k, v in d.items() if not isinstance(v, dict))[:900])
        return
    _compact_table(doc, keys, [[d.get(k) for k in keys] for d in datas])


async def tmtc(sx: Any, *, gate: str, lang: str) -> bytes | None:
    """The TM/TC database, FDIR and AOCS specification (H, W3.06) from the CDR model of the
    collector: the TM/TC tables of ``services.tmtc_export`` and the FDIR, AOCS and operations rows."""
    cdr = getattr(sx, "cdr", None) or {}
    by_kind = cdr.get("rows") or {}
    if not by_kind:
        return None
    from .. import tmtc_export
    fr = _fr(lang)
    flat = [r for rs in by_kind.values() for r in rs]
    modes = [{"id": m.get("id"), "name": m.get("name"), "kind": m.get("kind")}
             for m in (getattr(sx, "modes", None) or {}).get("modes") or [] if m.get("id")]
    db = tmtc_export.tables(flat, modes)
    name = getattr(sx, "study_name", "") or ""
    doc = _new("Base de données TM/TC, spécification FDIR et SCAO" if fr else "TM/TC database, FDIR and AOCS specification",
               "ECSS-E-ST-70-41C (PUS-C) / ECSS-E-ST-10C", name, "TMTC")
    st = db.get("settings") or {}
    _add_section(doc, "1", "Paramètres généraux" if fr else "Settings")
    _add_table(doc, ["Paramètre" if fr else "Setting", "Valeur" if fr else "Value"], [[k, _cell_str(v)] for k, v in st.items()])
    _orient(doc, landscape=True)
    chapters = (("parameters", "Paramètres de TM" if fr else "TM parameters",
                 ["param_id", "name", "subsystem", "type", "bits", "unit", "calibration", "range", "sids"]),
                ("sids", "Paquets de TM de servitude (SID)" if fr else "Housekeeping packets (SIDs)",
                 ["sid", "copy", "apid", "name", "subsystem", "packet_bytes", "parameters", "enabled", "store_id"]),
                ("stores", "Mémoires de stockage" if fr else "Packet stores", ["id", "name", "size_mb", "circular", "location", "content"]),
                ("services", "Services PUS" if fr else "PUS services", ["service", "name", "used"]),
                ("events", "Évènements" if fr else "Events", ["event_id", "name", "subsystem", "severity", "description"]),
                ("commands", "Télécommandes" if fr else "Telecommands",
                 ["name", "service", "subtype", "func_id", "criticality", "arm_execute", "args", "description"]))
    n = 1
    for key, title, cols in chapters:
        rows = db.get(key) or []
        if not rows:
            continue
        n += 1
        _add_section(doc, str(n), f"{title} ({len(rows)})")
        _compact_table(doc, cols, [[r.get(c) for c in cols] for r in rows])
    for kinds, title in ((_FDIR_KINDS, "FDIR"), (_AOCS_KINDS, "SCAO" if fr else "AOCS"),
                         (_OPS_KINDS, "TT&C et opérations" if fr else "TT&C and operations")):
        present = [k for k in kinds if by_kind.get(k)]
        if not present:
            continue
        n += 1
        _add_section(doc, str(n), title)
        for j, k in enumerate(present, start=1):
            _add_section(doc, f"{n}.{j}", f"{k.replace('_', ' ')} ({len(by_kind[k])})")
            _kind_table(doc, by_kind[k])
    _orient(doc, landscape=False)
    checks = [c for c in cdr.get("checks") or [] if c.get("severity") in ("alarm", "caution")]
    n += 1
    _add_section(doc, str(n), "Vérifications du modèle" if fr else "Model checks",
                 (f"{len(checks)} alarmes ou avertissements ouverts." if fr else f"{len(checks)} open alarms or cautions."))
    if checks:
        _compact_table(doc, ["Sévérité" if fr else "Severity", "Règle" if fr else "Rule", "Message"],
                       [[c.get("severity"), c.get("group") or c.get("rule"), c.get("message") if isinstance(c.get("message"), str)
                         else (c.get("message") or {}).get("fr" if fr else "en") or c.get("id")] for c in checks],
                       widths_cm=[2.0, 2.0, 13.0])
    return _save(doc)


HOOKS: dict[str, Callable[..., Awaitable[bytes | None]]] = {
    "trades": trades, "review_report": review_report, "ait": ait, "schedule": schedule,
    "licensing": licensing, "tmtc": tmtc,
}
