"""SpaceCDF — master budget workbook from the study (W4.03) and plain table workbooks (W1.09i).

``generate_master_budget(sx)`` takes ``StudyExport.as_dict()`` (services/export_context) and
writes one workbook with live formulas:

* **Summary**   key totals and where they come from
* **Mass**      every unit the roll-up counts (leaf x quantity), maturity category and margin,
                allocation where one is set, the system margin of the gate, harness, limit
* **Power**     every mode: share of orbit, CBE, with margins, energy per orbit, depth of
                discharge; the orbit average of the operational mix
* **Data**      the daily data budget (W3.02, agent H) when it exists, else the payload volumes
                and the open item; the housekeeping budget of the CDR model
* **Link**      bands, the design case and every named link case (W4.04)
* **Pointing**  payload pointing requirements and the physics run's AOCS figures
* **Margins**   the system margin ladder per gate and the maturity margins
* **Ledger**    the allocation ledger (wave 3): every line with owner and status, a sum per budget
* **Performance** pointing, registration (RSS) and timing (linear sum) contributors from the ledger
* **Cost**      equipment cost by subsystem and the P50-P90 spread
* **Open items**  what the workbook could not fill and who adds it

Nothing comes from the parametric design loop. The mass total equals ``services/rollup.py``
(the same units). ``table_workbook`` writes simple sheets (BOM, V&V matrix) for the Export
drawer buttons that used to download CSV under an XLSX label.
"""
from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="8F001A", end_color="8F001A", fill_type="solid")
TOTAL_FONT = Font(bold=True)
TOTAL_FILL = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
NOTE_FONT = Font(italic=True, color="80746C")

#: z-scores of the normal approximation used for the cost percentiles
Z = {"P50": 0.0, "P70": 0.5244, "P80": 0.8416, "P90": 1.2816}
#: one-sigma cost uncertainty per maturity category (C2O default, not a standard citation)
COST_SIGMA = {"A": 0.10, "B": 0.10, "C": 0.20, "D": 0.40}


def _headers(ws, row: int, headers: list[str], widths: list[int] | None = None) -> None:
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=i, value=h)
        c.font, c.fill = HEADER_FONT, HEADER_FILL
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    for i in range(1, len(headers) + 1):
        w = (widths or [])[i - 1] if widths and i - 1 < len(widths) else 18
        ws.column_dimensions[get_column_letter(i)].width = max(ws.column_dimensions[get_column_letter(i)].width or 0, w)


def _total(ws, row: int, col: int, value: Any) -> None:
    c = ws.cell(row=row, column=col, value=value)
    c.font, c.fill = TOTAL_FONT, TOTAL_FILL


def _note(ws, row: int, text: str) -> None:
    ws.cell(row=row, column=1, value=text).font = NOTE_FONT


def _f(v: Any) -> float | None:
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def _stub(section: dict | None) -> bool:
    return isinstance(section, dict) and section.get("status") == "not_implemented"


def _owner(section: dict | None, default: str) -> str:
    if isinstance(section, dict) and (section.get("owner") or section.get("work_package")):
        return f"{section.get('owner', '')} {section.get('work_package', '')}".strip()
    return default


class _Lookup:
    def __init__(self, sx: dict[str, Any]):
        els = [e for e in (sx.get("elements") or {}).get("items") or [] if e.get("id")]
        self.by_id = {e["id"]: e for e in els}
        self.els = els

    def subsystem(self, eid: str) -> str:
        e, n = self.by_id.get(eid) or {}, 0
        cur = e
        while cur.get("parent_id") in self.by_id and n < 50:
            cur = self.by_id[cur["parent_id"]]
            if cur.get("element_type") == "subsystem":
                return cur.get("name") or ""
            n += 1
        return e.get("subsystem_domain") or ""


def _sheet_mass(wb: Workbook, sx: dict, lk: _Lookup, opens: list[list[str]]) -> dict[str, str]:
    ws = wb.create_sheet("Mass")
    ru = sx.get("rollup") or {}
    m = ru.get("mass") or {}
    allocs = {a.get("element_id"): a for a in (sx.get("elements") or {}).get("allocations") or []
              if str(a.get("budget_type") or "").lower() == "mass"}
    _headers(ws, 1, ["Subsystem", "Equipment", "Qty", "Unit mass (kg)", "CBE (kg)", "Maturity category",
                     "Maturity margin (%)", "With maturity (kg)", "Allocation (kg)"], [22, 52, 6, 14, 12, 10, 12, 14, 14])
    units = sorted(m.get("units") or [], key=lambda u: (lk.subsystem(u.get("element_id")), str(u.get("name"))))
    r = 2
    for u in units:
        q = int(u.get("quantity") or 1)
        cbe = float(u.get("cbe") or 0)
        ws.cell(row=r, column=1, value=lk.subsystem(u.get("element_id")))
        ws.cell(row=r, column=2, value=u.get("name"))
        ws.cell(row=r, column=3, value=q)
        ws.cell(row=r, column=4, value=round(cbe / q, 6) if q else cbe)
        ws.cell(row=r, column=5, value=f"=C{r}*D{r}")
        ws.cell(row=r, column=6, value=u.get("category") or "")
        ws.cell(row=r, column=7, value=float(u.get("margin_percent") or 0))
        ws.cell(row=r, column=8, value=f"=E{r}*(1+G{r}/100)")
        a = allocs.get(u.get("element_id"))
        if a is not None:
            ws.cell(row=r, column=9, value=_f(a.get("allocation_value")))
        r += 1
    last = r - 1
    t = r + 1
    _total(ws, t, 1, "Total (current best estimate)")
    _total(ws, t, 5, f"=SUM(E2:E{last})" if units else 0)
    _total(ws, t, 8, f"=SUM(H2:H{last})" if units else 0)
    gate = str(ru.get("gate") or "").upper()
    _total(ws, t + 1, 1, f"System margin at {gate} (%)")
    _total(ws, t + 1, 8, float(m.get("system_margin_percent") or 0))
    _total(ws, t + 2, 1, "With system margin (kg)")
    _total(ws, t + 2, 8, f"=H{t}*(1+H{t + 1}/100)")
    _total(ws, t + 3, 1, "Harness (kg, roll-up)")
    _total(ws, t + 3, 8, float(m.get("harness_kg") or 0))
    _total(ws, t + 4, 1, "Total dry incl. harness (kg, roll-up)")
    _total(ws, t + 4, 8, float(m.get("total_dry_kg") or 0))
    _total(ws, t + 5, 1, f"Limit (kg, {m.get('limit_source') or 'not set'})")
    _total(ws, t + 5, 8, _f(m.get("limit_kg")))
    _total(ws, t + 6, 1, "Margin to limit (kg)")
    _total(ws, t + 6, 8, f"=IF(H{t + 5}=\"\",\"\",H{t + 5}-H{t + 2})")
    _note(ws, t + 8, "Roll-up of the selected equipment (services/rollup.py): leaf units x quantity, maturity margin per "
                     "unit, then the system margin of the gate (configs/margin_policy.yaml). Roll-up values: "
                     f"CBE {m.get('cbe_kg')} kg, with maturity {m.get('with_maturity_kg')} kg, with system margin "
                     f"{m.get('with_system_margin_kg')} kg.")
    # by subsystem
    s0 = t + 10
    _headers(ws, s0, ["Subsystem", "CBE (kg)", "With maturity (kg)"])
    subs = sorted({lk.subsystem(u.get("element_id")) for u in units})
    for i, s in enumerate(subs, start=s0 + 1):
        ws.cell(row=i, column=1, value=s)
        ws.cell(row=i, column=2, value=f"=SUMIF(A2:A{last},A{i},E2:E{last})")
        ws.cell(row=i, column=3, value=f"=SUMIF(A2:A{last},A{i},H2:H{last})")
    if not units:
        opens.append(["Mass", "No equipment with a mass in the study", "systems_engineer"])
    if not allocs:
        opens.append(["Mass", "No mass allocations set on the elements (Budget tab)", "systems_engineer"])
    return {"cbe": f"Mass!E{t}", "with_margin": f"Mass!H{t + 2}", "limit": f"Mass!H{t + 5}"}


def _sheet_power(wb: Workbook, sx: dict, opens: list[list[str]]) -> None:
    ws = wb.create_sheet("Power")
    modes = {m.get("id"): m for m in (sx.get("modes") or {}).get("modes") or []}
    energy = (sx.get("modes") or {}).get("energy") or {}
    op_ids = {m.get("mode_id") for m in (energy.get("operational_orbit") or {}).get("modes") or []}
    _headers(ws, 1, ["Mode", "Kind", "Operational mix", "Share of orbit", "Power CBE (W)", "With maturity (W)",
                     "With all margins (W)", "Energy load per orbit (Wh)", "Battery drawn (Wh)", "DoD (%)", "Status"],
             [30, 14, 10, 10, 12, 12, 12, 14, 12, 8, 10])
    rows = energy.get("modes") or []
    r = 2
    for e in rows:
        mid = e.get("mode_id")
        ws.cell(row=r, column=1, value=e.get("name"))
        ws.cell(row=r, column=2, value=e.get("kind"))
        ws.cell(row=r, column=3, value=1 if mid in op_ids else 0)
        ws.cell(row=r, column=4, value=_f((modes.get(mid) or {}).get("orbit_fraction")) or 0.0)
        ws.cell(row=r, column=5, value=_f(e.get("power_cbe_w")))
        ws.cell(row=r, column=6, value=_f(e.get("power_with_maturity_w")))
        ws.cell(row=r, column=7, value=_f(e.get("power_total_w")))
        ws.cell(row=r, column=8, value=_f(e.get("energy_load_wh")))
        ws.cell(row=r, column=9, value=_f(e.get("battery_drawn_wh")))
        ws.cell(row=r, column=10, value=_f(e.get("dod_percent")))
        ws.cell(row=r, column=11, value=e.get("status"))
        r += 1
    last = r - 1
    t = r + 1
    pw = (sx.get("rollup") or {}).get("power") or {}
    _total(ws, t, 1, "Orbit average of the operational mix, CBE (W)")
    if rows:
        _total(ws, t, 5, f"=IF(SUMPRODUCT(C2:C{last},D2:D{last})=0,\"\",SUMPRODUCT(C2:C{last},D2:D{last},E2:E{last})/SUMPRODUCT(C2:C{last},D2:D{last}))")
    _total(ws, t + 1, 1, "Orbit average (roll-up, W)")
    _total(ws, t + 1, 5, _f(pw.get("orbit_average_w")))
    _total(ws, t + 2, 1, "Orbit average with system margin (roll-up, W)")
    _total(ws, t + 2, 5, _f(pw.get("orbit_average_with_margin_w")))
    _total(ws, t + 3, 1, "Sum of ON powers (W)")
    _total(ws, t + 3, 5, _f(pw.get("sum_on_power_w")))
    op = energy.get("operational_orbit") or {}
    inp = energy.get("inputs") or {}
    _total(ws, t + 5, 1, "Solar array EOL power (W)")
    _total(ws, t + 5, 5, _f(inp.get("sa_power_eol_w")))
    _total(ws, t + 6, 1, "Battery capacity (Wh)")
    _total(ws, t + 6, 5, _f(inp.get("battery_capacity_wh")))
    _total(ws, t + 7, 1, "Operational orbit: generated / needed / balance (Wh)")
    _total(ws, t + 7, 5, _f(op.get("generated_wh")))
    _total(ws, t + 7, 6, _f(op.get("needed_wh")))
    _total(ws, t + 7, 7, _f(op.get("balance_wh")))
    _note(ws, t + 9, str(pw.get("orbit_average_source") or "Modes tab energy balance"))
    if not rows:
        opens.append(["Power", "No energy balance per mode (Modes tab)", "H"])


#: case key of this sheet -> the export section's name for it
_EXPORT_CASE_KEYS = (("capacity_mb", "capacity"), ("rt_hk_mb", "rt_hk"), ("stored_hk_mb", "stored_hk"),
                     ("science_mb", "science"), ("other_mb", "other"), ("demand_mb", "demand"))


def data_budget_cases(db: dict) -> tuple[dict, list[dict]]:
    """(closure, cases) of the ``data_budget`` section: ``daily.closure`` / ``daily.cases`` (W3.02,
    each case {id, label, capacity_mb, rt_hk_mb, stored_hk_mb, science_mb, other_mb, demand_mb,
    margin_pct, status}); an older top-level ``cases`` list or dict is read too."""
    daily = db.get("daily") or {}
    cases = daily.get("cases") if isinstance(daily, dict) else None
    if cases is None:
        cases = db.get("cases")
    if isinstance(cases, dict):
        cases = [{"id": k, **(v or {})} for k, v in cases.items()]
    # the export section (H, wave 2) names the case figures as NUMBERS.yaml does (capacity,
    # demand, ...; ``sections/data_budget.CASE_KEYS``): map them to this sheet's keys
    cases = [{**{k: c.get(ek) for k, ek in _EXPORT_CASE_KEYS if k not in c and ek in c}, **c}
             for c in cases or [] if isinstance(c, dict)]
    closure = daily.get("closure") if isinstance(daily, dict) and isinstance(daily.get("closure"), dict) else {}
    return closure, cases


def _label(v: Any, lang: str = "en") -> str:
    if isinstance(v, dict):
        return str(v.get(lang) or v.get("en") or "")
    return "" if v is None else str(v)


#: data budget case columns (key, header)
DB_COLUMNS = (("capacity_mb", "Capacity (MB/day)"), ("rt_hk_mb", "Real-time HK (MB/day)"),
              ("stored_hk_mb", "Stored HK (MB/day)"), ("science_mb", "Science (MB/day)"), ("other_mb", "Other (MB/day)"),
              ("demand_mb", "Demand (MB/day)"), ("margin_pct", "Margin (%)"), ("status", "Status"))


def _sheet_data(wb: Workbook, sx: dict, opens: list[list[str]]) -> None:
    ws = wb.create_sheet("Data")
    db = sx.get("data_budget") or {}
    r = 1
    closure, cases = data_budget_cases(db) if not _stub(db) else ({}, [])
    daily = db.get("daily") if not _stub(db) and isinstance(db.get("daily"), dict) else {}
    if cases:
        _headers(ws, r, ["Case", "Description"] + [h for _, h in DB_COLUMNS], [12, 60] + [14] * len(DB_COLUMNS))
        for i, c in enumerate(cases, start=r + 1):
            ws.cell(row=i, column=1, value=c.get("id"))
            ws.cell(row=i, column=2, value=_label(c.get("label")))
            for j, (k, _h) in enumerate(DB_COLUMNS, start=3):
                v = c.get(k)
                ws.cell(row=i, column=j, value=_f(v) if k != "status" else v)
            if closure and c.get("id") == closure.get("id"):
                for j in range(1, len(DB_COLUMNS) + 3):
                    ws.cell(row=i, column=j).font = TOTAL_FONT
        r = r + len(cases) + 1
        if closure:
            _note(ws, r, f"Baseline case {closure.get('id')}: demand {closure.get('demand_mb')} MB/day against a capacity "
                         f"of {closure.get('capacity_mb')} MB/day, margin {closure.get('margin_pct')} % "
                         f"(required {daily.get('margin_required_percent', '—')} %), {closure.get('status')}. "
                         "Source: data budget (Telemetry tab).")
            r += 1
        r += 1
    cap = daily.get("capacity") if isinstance(daily.get("capacity"), dict) else {}
    sci = daily.get("science") if isinstance(daily.get("science"), dict) else {}
    if not _stub(db):     # wave 2 section shape: capacity / science at the top level
        cap = cap or (db.get("capacity") if isinstance(db.get("capacity"), dict) else {})
        sci = sci or (db.get("science") if isinstance(db.get("science"), dict) else {})
    scal = [(f"capacity.{k}", v) for k, v in cap.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    scal += [(f"science.{k}", v) for k, v in sci.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    scal += [(k, v) for k, v in daily.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)]
    if scal:
        _headers(ws, r, ["Daily budget item", "Value"], [40, 16])
        for i, (k, v) in enumerate(scal, start=r + 1):
            ws.cell(row=i, column=1, value=k)
            ws.cell(row=i, column=2, value=v)
        r = r + len(scal) + 2
    prods = sci.get("products") or []
    if prods:
        _headers(ws, r, ["Science product", "MB raw", "Per day", "MB/day raw", "Priority"], [40, 12, 12, 14, 10])
        for i, p in enumerate(prods, start=r + 1):
            for j, k in enumerate(("name", "mb_raw", "per_day", "mb_per_day_raw", "priority"), start=1):
                ws.cell(row=i, column=j, value=p.get(k))
        r = r + len(prods) + 2
    if closure and closure.get("status") == "fail":
        opens.append(["Data", f"The baseline data budget case {closure.get('id')} does not close: margin "
                              f"{closure.get('margin_pct')} %", "H"])
    if _stub(db) or not (cases or scal):
        opens.append(["Data", "Daily data budget against the downlink (generated, stored, downlinked, margin per case)",
                      _owner(db, "H W3.02")])
    _headers(ws, r, ["Payload", "Frames acquired per day (GB)", "Data rate (Mbit/s)", "Duty cycle (%)"], [40, 16, 16, 14])
    pls = ((sx.get("mission") or {}).get("definition") or {}).get("payloads") or []
    for i, p in enumerate(pls, start=r + 1):
        ws.cell(row=i, column=1, value=p.get("name"))
        ws.cell(row=i, column=2, value=_f(p.get("data_volume_per_day_gb")))
        ws.cell(row=i, column=3, value=_f(p.get("data_rate_mbps")))
        ws.cell(row=i, column=4, value=_f(p.get("duty_cycle_percent")))
    if pls:
        tr = r + len(pls) + 1
        _total(ws, tr, 1, "Frames acquired on board per day (GB, before ROI selection)")
        _total(ws, tr, 2, f"=SUM(B{r + 1}:B{tr - 1})")
        r = tr + 2
    from .v_sections import payload_data_lines
    pdl = payload_data_lines(sx)
    if pdl:
        _headers(ws, r, ["Payload definition: acquired and delivered", "Value"])
        for i, (k, v) in enumerate(pdl, start=r + 1):
            ws.cell(row=i, column=1, value=k)
            ws.cell(row=i, column=2, value=v)
        r = r + len(pdl) + 2
    hk = ((sx.get("cdr") or {}).get("budget") or {})
    scal = [(k, v) for k, v in hk.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)]
    if scal:
        _headers(ws, r, ["Housekeeping budget (CDR model)", "Value"])
        for i, (k, v) in enumerate(scal, start=r + 1):
            ws.cell(row=i, column=1, value=k)
            ws.cell(row=i, column=2, value=v)


def _sheet_link(wb: Workbook, sx: dict, opens: list[list[str]]) -> None:
    ws = wb.create_sheet("Link")
    defn = (sx.get("mission") or {}).get("definition") or {}
    cons = defn.get("constraints") or {}
    links = sx.get("links") or {}
    _headers(ws, 1, ["Item", "Value", "Source"], [36, 30, 30])
    rows = [(k, cons[k], "mission constraints") for k in ("downlink_band_mhz", "uplink_band_mhz") if cons.get(k)]
    rows += [(k, v, "design case (requirements.link)") for k, v in (links.get("design_case") or {}).items()
             if v not in (None, "", [])]
    ttc = ((sx.get("cdr") or {}).get("rows") or {}).get("ttc") or []
    for row in ttc[:1]:
        rows += [(k, v, "CDR model (ttc)") for k, v in (row.get("data") or {}).items() if not isinstance(v, (dict, list))]
    for i, (k, v, src) in enumerate(rows, start=2):
        ws.cell(row=i, column=1, value=k)
        ws.cell(row=i, column=2, value=", ".join(str(x) for x in v) if isinstance(v, (list, tuple)) else v)
        ws.cell(row=i, column=3, value=src)
    r = len(rows) + 3
    items = [i for i in links.get("items") or [] if isinstance(i, dict)]
    if items:
        keys: list[str] = []
        for it in items:
            for k, v in it.items():
                if k not in keys and not isinstance(v, (dict, list)) and k not in ("study_id",):
                    keys.append(k)
        _headers(ws, r, keys)
        for i, it in enumerate(items, start=r + 1):
            for j, k in enumerate(keys, start=1):
                ws.cell(row=i, column=j, value=it.get(k))
    else:
        opens.append(["Link", "Named link-budget cases (per station, rate tier, direction)", "D W4.04"])
    if not (links.get("design_case") or {}) or not any(v not in (None, "", []) for v in (links.get("design_case") or {}).values()):
        opens.append(["Link", "Link design case is empty (apply a link budget to the design)", "comms_engineer"])


def _sheet_pointing(wb: Workbook, sx: dict, opens: list[list[str]]) -> None:
    ws = wb.create_sheet("Pointing")
    _headers(ws, 1, ["Item", "Value", "Source"], [44, 16, 30])
    rows = []
    for p in ((sx.get("mission") or {}).get("definition") or {}).get("payloads") or []:
        if p.get("pointing_accuracy_deg") is not None:
            rows.append((f"{p.get('name')}: pointing accuracy (deg)", _f(p.get("pointing_accuracy_deg")), "payload definition"))
        if p.get("pointing_stability_deg_s") is not None:
            rows.append((f"{p.get('name')}: pointing stability (deg/s)", _f(p.get("pointing_stability_deg_s")), "payload definition"))
    phys = (((sx.get("analyses") or {}).get("last_runs") or {}).get("physics") or {}).get("summary") or {}
    rows += [(k, float(v), "physics analysis") for k, v in sorted(phys.items())
             if k.startswith("aocs_") and isinstance(v, (int, float)) and not isinstance(v, bool)]
    for i, (k, v, s) in enumerate(rows, start=2):
        ws.cell(row=i, column=1, value=k)
        ws.cell(row=i, column=2, value=v)
        ws.cell(row=i, column=3, value=s)
    if not rows:
        opens.append(["Pointing", "No payload pointing requirement and no physics run", "aocs_engineer"])
    if not phys:
        opens.append(["Pointing", "Pointing error budget from the AOCS analysis (physics run missing)", "aocs_engineer"])


def _sheet_margins(wb: Workbook, sx: dict) -> None:
    ws = wb.create_sheet("Margins")
    m = (sx.get("rollup") or {}).get("mass") or {}
    _headers(ws, 1, ["Gate", "System margin (%)", "Mass with system margin (kg)"], [10, 18, 26])
    wm = _f(m.get("with_maturity_kg")) or 0.0
    for i, (g, v) in enumerate((m.get("ladder") or {}).items(), start=2):
        ws.cell(row=i, column=1, value=g.upper())
        pct = round((float(v) / wm - 1) * 100, 1) if wm else None
        ws.cell(row=i, column=2, value=pct)
        ws.cell(row=i, column=3, value=_f(v))
    r = len(m.get("ladder") or {}) + 3
    _headers(ws, r, ["Maturity category", "Maturity margin (%)", "Units"])
    cats: dict[str, list] = {}
    for u in m.get("units") or []:
        cats.setdefault(u.get("category") or "?", [u.get("margin_percent"), 0])[1] += 1
    for i, (c, (pct, n)) in enumerate(sorted(cats.items()), start=r + 1):
        ws.cell(row=i, column=1, value=c)
        ws.cell(row=i, column=2, value=_f(pct))
        ws.cell(row=i, column=3, value=n)
    _note(ws, ws.max_row + 2, "configs/margin_policy.yaml: maturity margins A/B 5 %, C 10 %, D 20 %; "
                              "system margin ladder per gate.")


LEDGER_COLUMNS = ["Budget", "Element", "Kind", "Allocation", "Unit", "CBE", "With maturity", "Requirement", "Budget ref",
                  "Owner", "Status", "Contributor"]


def _sheet_ledger(wb: Workbook, sx: dict, opens: list[list[str]]) -> dict[str, float]:
    """The allocation ledger (3.A2): every line with its owner and sign-off; a SUM per budget."""
    from .v_sections import BUDGET_LABEL, g, items
    ws = wb.create_sheet("Ledger")
    sec = sx.get("allocations") or {}
    _headers(ws, 1, LEDGER_COLUMNS, [16, 10, 11, 12, 9, 10, 12, 14, 22, 18, 10, 40])
    if _stub(sec):
        opens.append(["Ledger", "Allocation ledger (budget shares agreed by their owners)", _owner(sec, "A 3.A2")])
        return {}
    lines = items(sec)
    r = 2
    sums: dict[str, float] = {}
    for bt in list(BUDGET_LABEL) + sorted({str(g(x, "budget_type", default="")) for x in lines} - set(BUDGET_LABEL)):
        mine = [x for x in lines if str(g(x, "budget_type", default="")) == bt]
        if not mine:
            continue
        first = r
        for x in mine:
            reserve = str(g(x, "line_kind", default="")) == "reserve" or str(g(x, "element_code", default="")).upper() == "SYS"
            row = [BUDGET_LABEL.get(bt, (bt, bt))[0], g(x, "element_code", default=""), g(x, "line_kind", default="allocation"),
                   _f(g(x, "value")), g(x, "unit", default=""), _f(g(x, "cbe")), _f(g(x, "margined")),
                   g(x, "requirement_code", default=""), g(x, "budget_ref", default=""), g(x, "owner_seat", default=""),
                   g(x, "status", default=""), (g(x, "data", default={}) or {}).get("contributor") or g(x, "mode_key", default="")]
            for j, v in enumerate(row, start=1):
                ws.cell(row=r, column=j, value=v)
            if not reserve:
                sums[bt] = round(sums.get(bt, 0.0) + (_f(g(x, "value")) or 0.0), 6)
            r += 1
        _total(ws, r, 1, f"Sum of the {BUDGET_LABEL.get(bt, (bt,))[0].lower()} allocations")
        _total(ws, r, 4, f'=SUMIFS(D{first}:D{r - 1},C{first}:C{r - 1},"<>reserve")')
        r += 2
    if not lines:
        opens.append(["Ledger", "Allocation ledger is empty", "systems_engineer"])
    _note(ws, r + 1, "Allocation ledger of the study (agreed, proposed or disputed by the element owner). The Systems "
                     "reserve is its own line (kind reserve) and is not in the sums.")
    return sums


def _sheet_performance(wb: Workbook, sx: dict, opens: list[list[str]]) -> None:
    """Performance budgets (pointing, registration, timing) from the ledger contributors."""
    from .v_sections import g, items
    ws = wb.create_sheet("Performance")
    sec = sx.get("allocations") or {}
    _headers(ws, 1, ["Budget", "Contributor", "Allocation", "Unit", "Requirement", "Status"], [14, 50, 12, 8, 22, 10])
    if _stub(sec):
        opens.append(["Performance", "Pointing, registration and timing budgets (ledger contributors)", _owner(sec, "A 3.A2")])
        return
    r = 2
    for bt, rule in (("pointing", "each contributor against its requirement"), ("registration", "root sum of squares"),
                     ("timing", "worst-case linear sum")):
        mine = [x for x in items(sec) if str(g(x, "budget_type", default="")) == bt]
        if not mine:
            opens.append(["Performance", f"No {bt} budget lines in the ledger", "systems_engineer"])
            continue
        first = r
        for x in mine:
            row = [bt, (g(x, "data", default={}) or {}).get("contributor") or g(x, "element_code", default=""), _f(g(x, "value")),
                   g(x, "unit", default=""), g(x, "requirement_code", default=""), g(x, "status", default="")]
            for j, v in enumerate(row, start=1):
                ws.cell(row=r, column=j, value=v)
            r += 1
        if bt == "registration":
            _total(ws, r, 2, "RSS (" + rule + ")")
            _total(ws, r, 3, f"=SQRT(SUMSQ(C{first}:C{r - 1}))")
        elif bt == "timing":
            _total(ws, r, 2, "Sum (" + rule + ")")
            _total(ws, r, 3, f"=SUM(C{first}:C{r - 1})")
        else:
            _total(ws, r, 2, rule)
        r += 2


def cost_spread(lines: list[tuple[float, str]]) -> dict[str, float]:
    """P50..P90 of the equipment cost: each line normal with sigma by maturity category, lines
    independent (C2O default, not a standard citation)."""
    p50 = sum(c for c, _ in lines)
    sigma = math.sqrt(sum((c * COST_SIGMA.get(cat or "C", 0.2)) ** 2 for c, cat in lines))
    return {k: round(p50 + z * sigma, 1) for k, z in Z.items()}


def _sheet_cost(wb: Workbook, sx: dict, lk: _Lookup, opens: list[list[str]]) -> dict[str, float]:
    ws = wb.create_sheet("Cost")
    units = {u.get("element_id"): u for u in ((sx.get("rollup") or {}).get("mass") or {}).get("units") or []}
    comps = [e for e in lk.els if e.get("element_type") == "component"]
    _headers(ws, 1, ["Subsystem", "Equipment", "Qty", "Unit cost recurring (k€)", "Recurring (k€)", "Non-recurring (k€)",
                     "Maturity category", "Total (k€)"], [22, 52, 6, 14, 14, 14, 10, 14])
    lines: list[tuple[float, str]] = []
    r = 2
    for e in sorted(comps, key=lambda x: (lk.subsystem(x["id"]), str(x.get("name")))):
        if (e.get("segment") or "space") not in ("space",) and e.get("segment") is not None:
            continue
        q = int(e.get("quantity") or 1)
        uc, nre = _f(e.get("cost_recurring_keur")) or 0.0, _f(e.get("cost_nre_keur")) or 0.0
        cat = (units.get(e["id"]) or {}).get("category") or (e.get("performance") or {}).get("maturity_category") or "C"
        ws.cell(row=r, column=1, value=lk.subsystem(e["id"]))
        ws.cell(row=r, column=2, value=e.get("name"))
        ws.cell(row=r, column=3, value=q)
        ws.cell(row=r, column=4, value=uc)
        ws.cell(row=r, column=5, value=f"=C{r}*D{r}")
        ws.cell(row=r, column=6, value=nre)
        ws.cell(row=r, column=7, value=cat)
        ws.cell(row=r, column=8, value=f"=E{r}+F{r}")
        lines.append((uc * q + nre, cat))
        r += 1
    last = r - 1
    t = r + 1
    _total(ws, t, 1, "Total flight hardware (k€)")
    _total(ws, t, 8, f"=SUM(H2:H{last})" if lines else 0)
    spread = cost_spread(lines)
    _headers(ws, t + 2, ["Percentile", "Cost (k€)"])
    for i, (k, v) in enumerate(spread.items(), start=t + 3):
        ws.cell(row=i, column=1, value=k)
        ws.cell(row=i, column=2, value=v)
    tc = _f(((sx.get("mission") or {}).get("definition") or {}).get("target_cost_meur"))
    if tc:
        ws.cell(row=t + 8, column=1, value="Cost target (k€)")
        ws.cell(row=t + 8, column=2, value=tc * 1000)
    _note(ws, t + 10, "P50 = sum of the equipment cost entered on the elements (unit cost x quantity + non-recurring). "
                      "P70-P90: normal approximation, independent lines, one-sigma 10 % (category A/B), 20 % (C), "
                      "40 % (D) (C2O default). Ground segment, labour, launch and operations are not included.")
    if not any(c for c, _ in lines):
        opens.append(["Cost", "No equipment cost entered", "team_leader"])
    sch = sx.get("schedule") or {}
    if _stub(sch):
        opens.append(["Cost", "Labour, ground segment, schedule and long-lead items", _owner(sch, "A W11a")])
    return spread


def _sheet_summary(ws, sx: dict, spread: dict[str, float], crosscheck: dict | None) -> None:
    ru = sx.get("rollup") or {}
    m, pw = ru.get("mass") or {}, ru.get("power") or {}
    _headers(ws, 1, ["Item", "Value", "Unit", "Parametric cross-check", "Source"], [44, 14, 8, 20, 50])
    cx = crosscheck or {}
    rows = [
        ("Study", sx.get("study_name"), "", None, ""),
        ("Margin-ladder gate", str(ru.get("gate") or "").upper(), "", None, "gate profile"),
        ("Form factor", ru.get("form_factor"), "", None, ru.get("form_factor_source")),
        ("Mass, current best estimate", m.get("cbe_kg"), "kg", cx.get("mass_nominal_kg"), "roll-up (Mass sheet)"),
        ("Mass with maturity margins", m.get("with_maturity_kg"), "kg", None, "roll-up"),
        ("Mass with system margin", m.get("with_system_margin_kg"), "kg", cx.get("mass_with_margin_kg"), "roll-up"),
        ("Mass limit", m.get("limit_kg"), "kg", None, m.get("limit_source")),
        ("Orbit-average power (operational mix)", pw.get("orbit_average_w"), "W", None, "modes energy balance"),
        ("Orbit-average power with system margin", pw.get("orbit_average_with_margin_w"), "W", None, "roll-up"),
        ("Sum of ON powers", pw.get("sum_on_power_w"), "W", cx.get("power_w"), "roll-up"),
        ("Equipment cost P50", spread.get("P50"), "k€", None, "Cost sheet"),
        ("Equipment cost P90", spread.get("P90"), "k€", None, "Cost sheet"),
    ]
    for i, row in enumerate(rows, start=2):
        for j, v in enumerate(row, start=1):
            ws.cell(row=i, column=j, value=v)
    _note(ws, len(rows) + 3, "Every value comes from the study (services/export_context + services/rollup). The "
                             "parametric cross-check column is the parametric design loop, shown for comparison only.")


def generate_master_budget(sx: dict[str, Any], output: Path | None = None, *, crosscheck: dict | None = None) -> bytes:
    """The master budget workbook of the study (``StudyExport.as_dict()``)."""
    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    lk = _Lookup(sx)
    opens: list[list[str]] = []
    _sheet_mass(wb, sx, lk, opens)
    _sheet_power(wb, sx, opens)
    _sheet_data(wb, sx, opens)
    _sheet_link(wb, sx, opens)
    _sheet_pointing(wb, sx, opens)
    _sheet_margins(wb, sx)
    _sheet_ledger(wb, sx, opens)
    _sheet_performance(wb, sx, opens)
    spread = _sheet_cost(wb, sx, lk, opens)
    _sheet_summary(summary, sx, spread, crosscheck)
    ws = wb.create_sheet("Open items")
    _headers(ws, 1, ["Sheet", "Open item", "Owner / work package"], [12, 80, 24])
    for i, row in enumerate(opens, start=2):
        for j, v in enumerate(row, start=1):
            ws.cell(row=i, column=j, value=v)
    buf = io.BytesIO()
    wb.save(buf)
    data = buf.getvalue()
    if output is not None:
        Path(output).write_bytes(data)
    return data


def table_workbook(sheets: list[tuple[str, list[str], list[list[Any]]]]) -> bytes:
    """A plain workbook: one sheet per (title, headers, rows), header row styled and frozen."""
    wb = Workbook()
    wb.remove(wb.active)
    for title, headers, rows in sheets:
        ws = wb.create_sheet(title[:31])
        _headers(ws, 1, headers, [max(10, min(60, len(h) + 6)) for h in headers])
        for i, row in enumerate(rows, start=2):
            for j, v in enumerate(row, start=1):
                if isinstance(v, (list, tuple)):
                    v = ", ".join(str(x) for x in v)
                elif isinstance(v, dict):
                    v = "; ".join(f"{k}={x}" for k, x in v.items())
                ws.cell(row=i, column=j, value=v)
        ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


__all__ = ["generate_master_budget", "table_workbook", "cost_spread"]
