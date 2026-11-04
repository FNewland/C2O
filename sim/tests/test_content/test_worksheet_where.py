"""Where to find each workbook answer (worksheet screen audit, 2026-11-04).

configs/eosat1/worksheets/worksheet_where.yaml says, for every question of the
generated workbook sheets, whether a tool screen answers it and where; the
generator copies the places onto the questions (``where``) and writes the
audit table of docs/plan_2026-11/WORKSHEET_SCREEN_AUDIT_OPS.md. Pinned here:

* every place exists: the MCS page, panel id, PUS tab, drawer tab and the
  parameter row (a parameter of that page, in the operator dictionary); the
  planner / orbit tools / radio / delayed-TM element ids; the manual file and
  its heading anchor, in English and in French; the procedure card;
* the audit is complete: every generated question has a status, and every
  question the screens do not answer is either fixed or deferred with a
  reason; the audit document is current;
* open references are https only, open in a new window, and are listed in
  docs/plan_2026-11/EXTERNAL_LINKS.md with their reason and check date;
* the generated questions carry ``where`` only in the shape the logbook
  renders, and the logbook API never hands out a non-https URL.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

SIM = Path(__file__).resolve().parents[2]
C2O = SIM.parent
CFG = SIM / "configs" / "eosat1"
WS = CFG / "worksheets"
WHERE = WS / "worksheet_where.yaml"
GENERATED = WS / "ops_week3.yaml"
AUDIT = C2O / "docs" / "plan_2026-11" / "WORKSHEET_SCREEN_AUDIT_OPS.md"
LINKS_MD = C2O / "docs" / "plan_2026-11" / "EXTERNAL_LINKS.md"
WORKBOOK = C2O / "design" / "docs" / "course" / "orbit_north_week3_workbook.md"
MCS_STATIC = SIM / "packages" / "smo-mcs" / "src" / "smo_mcs" / "static" / "modern"
PLANNER_HTML = SIM / "packages" / "smo-planner" / "src" / "smo_planner" / "static" / "modern" / "index.html"
RADIO_HTML = SIM / "packages" / "smo-rfsim" / "src" / "smo_rfsim" / "static" / "modern" / "index.html"
ORBIT_PY = SIM / "tools" / "orbit_tools.py"
DTM_PY = SIM / "tools" / "delayed_tm_viewer.py"

if str(SIM / "tools") not in sys.path:
    sys.path.insert(0, str(SIM / "tools"))
for pkg in ("smo-common",):
    src = SIM / "packages" / pkg / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

import gen_worksheets as gen  # noqa: E402

needs_workbook = pytest.mark.skipif(not WORKBOOK.exists(),
                                    reason="design/ (course workbook) not in this checkout")


def _where_map() -> dict:
    return yaml.safe_load(WHERE.read_text(encoding="utf-8"))


def _ids(text: str) -> set[str]:
    return set(re.findall(r"""\bid=["']([A-Za-z][\w-]*)["']""", text))


def _mcs_ids() -> set[str]:
    """Literal element ids of the modern MCS, plus the per-page ones the
    subsystem-page skeleton builds from `${pageId}-…`."""
    js = (MCS_STATIC / "mcs.js").read_text(encoding="utf-8")
    html = (MCS_STATIC / "index.html").read_text(encoding="utf-8")
    ids = _ids(js) | _ids(html)
    suffixes = set(re.findall(r'id="\$\{pageId\}-([\w-]+)"', js))
    sub_pages = re.search(r"const SUB_PAGES = \[([^\]]+)\]", js).group(1)
    for page in re.findall(r'"(\w+)"', sub_pages):
        ids |= {f"{page}-{s}" for s in suffixes}
    # ids set by a template helper (projRow) or given to a table at render time
    ids |= set(re.findall(r'projRow\("([\w-]+)"', js))
    ids |= set(re.findall(r'<table class="plain" id="([\w-]+)"', js))
    return ids


def _mcs_rail() -> set[str]:
    js = (MCS_STATIC / "mcs.js").read_text(encoding="utf-8")
    body = re.search(r"const RAIL = \[(.*?)\];", js, re.S).group(1)
    return {p for p in re.findall(r'\["(\w+)",', body)}


def _mcs_diag_tabs() -> set[str]:
    js = (MCS_STATIC / "mcs.js").read_text(encoding="utf-8")
    return set(re.findall(r'\["(s\d+|params)", "[^"]+"\]', js))


def _mcs_bd_tabs() -> set[str]:
    html = (MCS_STATIC / "index.html").read_text(encoding="utf-8")
    return set(re.findall(r'data-bd="(\w+)"', html))


def _anchors(md: Path) -> set[str]:
    return set(re.findall(r"\{#([^}\s]+)\}", md.read_text(encoding="utf-8")))


def _targets(wm: dict) -> list[tuple[str, dict]]:
    """Every place the map names: the named targets and the inline ones."""
    out = list(wm["targets"].items())
    for wid, spec in (wm.get("sheets") or {}).items():
        entries = [("default", spec.get("default") or {})] + list((spec.get("items") or {}).items())
        for key, e in entries:
            for i, ref in enumerate((e or {}).get("where") or []):
                if isinstance(ref, dict):
                    out.append((f"{wid}/{key}/where[{i}]", ref))
    return out


def test_every_place_exists():
    wm = _where_map()
    rail, tabs, bds, mcs_ids = _mcs_rail(), _mcs_diag_tabs(), _mcs_bd_tabs(), _mcs_ids()
    assert "eps" in rail and "s9" in tabs and "gonogo" in bds, "parsers out of date"
    tool_ids = {
        "planner": _ids(PLANNER_HTML.read_text(encoding="utf-8")),
        "orbit": _ids(ORBIT_PY.read_text(encoding="utf-8")),
        "radio": _ids(RADIO_HTML.read_text(encoding="utf-8")),
        "delayed_tm": _ids(DTM_PY.read_text(encoding="utf-8")),
    }
    procs = {p["id"]: p["file"] for p in yaml.safe_load(
        (CFG / "procedures" / "procedure_index.yaml").read_text())["procedures"]}
    problems = []
    for name, t in _targets(wm):
        tool = t.get("tool")
        if tool == "mcs":
            if t.get("page") and t["page"] not in rail:
                problems.append(f"{name}: MCS page {t['page']} not on the rail")
            if t.get("focus") and t["focus"] not in mcs_ids:
                problems.append(f"{name}: MCS has no element #{t['focus']}")
            if t.get("tab") and t["tab"] not in tabs:
                problems.append(f"{name}: PUS tab {t['tab']} does not exist")
            if t.get("bd") and t["bd"] not in bds:
                problems.append(f"{name}: drawer tab {t['bd']} does not exist")
        elif tool in tool_ids:
            if t.get("focus") and t["focus"] not in tool_ids[tool]:
                problems.append(f"{name}: {tool} has no element #{t['focus']}")
            if tool == "delayed_tm" and t.get("path") and t["path"] != "reports":
                problems.append(f"{name}: delayed TM has no page /{t['path']}")
        elif tool == "docs":
            if t.get("proc"):
                if t["proc"] not in procs:
                    problems.append(f"{name}: unknown procedure {t['proc']}")
                continue
            md = CFG / t["path"]
            fr = CFG / "i18n" / "fr" / t["path"]
            if not md.is_file():
                problems.append(f"{name}: {t['path']} does not exist")
                continue
            if t.get("anchor") and t["anchor"] not in _anchors(md):
                problems.append(f"{name}: {t['path']} has no heading #{t['anchor']}")
            if fr.is_file() and t.get("anchor") and t["anchor"] not in _anchors(fr):
                problems.append(f"{name}: French {t['path']} has no heading #{t['anchor']}")
        else:
            problems.append(f"{name}: unknown tool {tool!r}")
    assert not problems, "\n".join(problems)


def test_parameter_rows_are_on_their_page():
    """Every parameter a question links to is in the operator dictionary and
    listed on the page the link opens (that subsystem's Parameters table)."""
    params = gen._dictionary()
    doc = yaml.safe_load(GENERATED.read_text(encoding="utf-8"))
    n = 0
    for w in doc["worksheets"]:
        for q in w["questions"]:
            for it in q.get("where") or []:
                if it.get("tool") != "mcs" or not it.get("param"):
                    continue
                pid = int(it["param"], 16)
                assert params[pid]["operator"], (w["id"], q["id"], it["param"])
                assert it["page"] == gen.SUB_PAGE.get(params[pid]["subsystem"], "diag"), (w["id"], q["id"], it)
                n += 1
    assert n > 200


@needs_workbook
def test_audit_is_complete_and_current():
    audit: list = []
    gen.generate(audit=audit)
    rows = [r for sh in audit for r in sh["rows"]]
    assert len(rows) > 400
    for r in rows:
        assert r["status"] in gen.STATUSES
        if r["status"] == "none":
            # not answerable from the system: fixed (a reworded question
            # that still has no screen is not a fix) or deferred with reason
            assert r["deferred"], f"{r['text']}: not answerable, no deferral reason"
        if r["status"] in ("screen", "manual"):
            assert r["where"], r["text"]
        if r["before"] != r["status"]:
            assert r["fix"], f"{r['text']}: changed status without saying what fixed it"
    text = AUDIT.read_text(encoding="utf-8")
    assert gen.audit_text(audit) in text, \
        "WORKSHEET_SCREEN_AUDIT_OPS.md is stale: run tools/gen_worksheets.py --audit"


def test_every_where_key_matches_a_question():
    """Already enforced by the generator (it stops); pinned so a silent
    change there is caught."""
    wm = gen.WhereMap()
    with pytest.raises(gen.WhereError):
        wm.sheets = {"WB-5.0": {"items": {"No such question": {"status": "na"}}}}
        wm.apply("WB-5.0", [{"id": "q1", "text": {"en": "Orbit altitude (km)"}}])


def test_open_references_are_https_and_listed():
    wm = _where_map()
    listed = LINKS_MD.read_text(encoding="utf-8")
    assert wm["links"], "no open references"
    for key, ln in wm["links"].items():
        assert ln["url"].startswith("https://"), key
        assert ln["url"] in listed, f"{key}: {ln['url']} missing from EXTERNAL_LINKS.md"
        if ln.get("url_fr"):
            assert ln["url_fr"].startswith("https://") and ln["url_fr"] in listed, key
    # and each one is used somewhere
    used = WHERE.read_text(encoding="utf-8")
    for key in wm["links"]:
        assert len(re.findall(rf"\b{re.escape(key)}\b", used)) >= 2, f"link {key} is never used"


def test_generated_where_shape():
    doc = yaml.safe_load(GENERATED.read_text(encoding="utf-8"))
    n = 0
    for w in doc["worksheets"]:
        for q in w["questions"]:
            for it in q.get("where") or []:
                n += 1
                assert it["tool"] in gen.WHERE_TOOLS, it
                assert it["label"]["en"] and it["label"]["fr"], it
                if it["tool"] == "ext":
                    assert it["url"].startswith("https://"), it
                else:
                    assert set(it) <= set(gen.WHERE_KEYS) | {"label"}, it
    assert n > 500


def test_localised_where_drops_unsafe_links():
    from smo_common.logbook.worksheets import localise_where
    lab = {"en": "x", "fr": "y"}
    items = [
        {"tool": "ext", "url": "javascript:alert(1)", "label": lab},
        {"tool": "ext", "url": "http://example.org/", "label": lab},
        {"tool": "ext", "url": "https://example.org/a b", "label": lab},
        {"tool": "ext", "url": 'https://example.org/"onmouseover=x', "label": lab},
        {"tool": "ext", "url": "https://example.org/en", "url_fr": "data:text/html,1", "label": lab},
        {"tool": "ftp", "url": "https://example.org/", "label": lab},
        {"tool": "mcs", "page": "eps", "param": "0x0101", "onclick": "x", "label": lab},
        {"tool": "mcs", "page": "eps"},
    ]
    out = localise_where(items, "fr")
    assert out == [
        {"tool": "ext", "label": "y", "url": "https://example.org/en"},
        {"tool": "mcs", "label": "y", "page": "eps", "param": "0x0101"},
    ]


def test_logbook_serves_where_with_the_sheet():
    from smo_common.logbook.worksheets import WorksheetCatalog
    cat = WorksheetCatalog(WS)
    sheet = next(w for w in cat.match("mcs", {"procedure": "LEOP-006"}, "fr") if w["id"] == "WB-5.5-L006")
    step2 = next(q for q in sheet["questions"] if q.get("step") == "2")
    places = {(w["tool"], w.get("tab"), w.get("focus")) for w in step2["where"]}
    assert ("mcs", "s9", "s9-owlt") in places
    assert all(w["label"] for w in step2["where"])
    assert any(w["label"].startswith("MCS › PUS › S9 TIME") for w in step2["where"])


def test_no_question_names_a_parameter_the_console_cannot_show():
    """The 2026-11-04 audit found worksheet rows asking for ttc.range_km,
    ttc.active_gs and ttc.beacon_active — none in the operator dictionary.
    The generator refuses that now; pinned on the output too."""
    params = gen._dictionary()
    doc = yaml.safe_load(GENERATED.read_text(encoding="utf-8"))
    for w in doc["worksheets"]:
        for q in w["questions"]:
            text = q["text"]["en"] + " " + ((q.get("hint") or {}).get("en") or "")
            for m in gen._PID.finditer(text):
                pid = int(m.group(1), 16)
                if pid in params:
                    assert params[pid]["operator"], (w["id"], q["id"], m.group(0))
