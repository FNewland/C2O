""""Where in SpaceCDF" links: the hand-maintained where_map.yaml against the frontend and the workbook.

configs/worksheets/where_map.yaml (Nov 2026 worksheet/screen audit) says, for every learner-workbook
question and every catalogue decision, which SpaceCDF screens answer it, which open-textbook sections
and which external links. These tests keep it honest:

* every target names a real view: activity tab, V&V section, Decide tool, analysis card, budget,
  mode view, TM/TC or FDIR sub-tab, Mission Definition step, dialog, anchor (drift guard);
* every label uses the screen's own words, in English and in French (the FR UI catalogue);
* audit coverage: every question has an entry and a status, every deferred one a reason, every
  "answerable from the screens" one a where link, every book reference a real OER section;
* link safety: https only, on the frontend allow-list, French URL when given, checked date;
* the audit and link documents in docs/plan_2026-11 are regenerated, not hand-edited.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest
import yaml

from spacecdf_server.logbook import decisions as dec
from spacecdf_server.logbook import where as wh
from spacecdf_server.logbook import worksheets as wsmod

DESIGN = Path(__file__).resolve().parents[2]
WS = DESIGN / "configs" / "worksheets"
FE = DESIGN / "frontend" / "src"
OER = DESIGN / "docs" / "oer" / "chapters"

STATUSES_NOW = {"screen", "screen+book", "book", "team", "ops", "deferred"}
STATUSES_BEFORE = STATUSES_NOW | {"partial", "gap"}


def _wm() -> dict:
    return yaml.safe_load((WS / "where_map.yaml").read_text(encoding="utf-8"))


def _wb() -> dict:
    return yaml.safe_load((WS / "learner_workbook.yaml").read_text(encoding="utf-8"))


def _src(rel: str) -> str:
    return (FE / rel).read_text(encoding="utf-8")


def _fr() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted((FE / "i18n" / "locales").glob("fr*.json")):
        out.update(json.loads(p.read_text(encoding="utf-8")))
    return out


def _array(src: str, pattern: str) -> set[str]:
    m = re.search(pattern, src, re.S)
    assert m, pattern
    return set(re.findall(r"'([\w-]+)'", m.group(1)))


def _panels() -> set[str]:
    return _array(_src("workbench/LevelWorkbench.tsx"), r"const PANELS[^=]*=\s*\[([^\]]+)\]")


def _panel_labels() -> dict[str, str]:
    src = _src("workbench/LevelWorkbench.tsx")
    body = re.search(r"const PANEL_LABELS[^=]*=\s*\{(.+?)\n\}", src, re.S).group(1)
    return dict(re.findall(r"(\w+):\s*'([^']+)'", body))


def _sections() -> dict[str, set[str]]:
    """Section ids each tab's panel listens for (useWhereSection) and can show."""
    decide = set(re.findall(r'whereId="([\w-]+)"', _src("workbench/DecisionPanel.tsx")))
    analyses = set(re.findall(r"id: '(\w+)', label: CARD_LABELS", _src("workbench/AnalysesPanel.tsx")))
    # panels opened by a toggle rather than a card (useWhereSection: if (sec === '…'))
    analyses |= set(re.findall(r"sec === '(\w+)'", _src("workbench/AnalysesPanel.tsx")))
    return {
        "decide": decide,
        "analyses": analyses,
        "budget": {"mass", "power", "data", "cost"},
        "modes": _array(_src("modes/ModesPanel.tsx"), r"type View = ([^\n]+)"),
        "tmtc": _array(_src("cdr/TmtcPanel.tsx"), r"type Sub = ([^\n]+)"),
        "fdir": _array(_src("cdr/FdirPanel.tsx"), r"type Sub = ([^\n]+)"),
    }


def _anchors() -> set[str]:
    text = "\n".join(p.read_text(encoding="utf-8") for p in FE.rglob("*.tsx"))
    found = set(re.findall(r'data-where="([\w-]+)"', text))
    # DesignLoopResults: data-where={g.id} on groups declared as id: 'dl-…'
    found |= set(re.findall(r"id: '(dl-[\w-]+)'", _src("workbench/DesignLoopResults.tsx")))
    return found


# ─── targets are real ─────────────────────────────────────────────────────

def test_every_target_names_a_real_place():
    panels, sections, anchors = _panels(), _sections(), _anchors()
    vv = _array(_src("workbench/VVPanel.tsx"), r"type Section = ([^\n]+)")
    wizard = _array(_src("workbench/MissionWizard.tsx"), r"type WizardStep = ([^\n]+)")
    domains = set(re.findall(r"\{ id: '(\w+)', label: DOMAIN_LABELS", _src("workbench/EquipmentBrowser.tsx")))
    kinds = {"tab", "vv", "dialog", "wizard", "anchor"}
    for tid, t in _wm()["targets"].items():
        assert kinds & set(t), f"{tid}: opens nothing"
        if "tab" in t:
            assert t["tab"] in panels, (tid, t["tab"])
        if "section" in t:
            assert t["section"] in sections.get(t["tab"], set()), (tid, t["section"], sorted(sections.get(t["tab"], [])))
        if "vv" in t:
            assert t["vv"] in vv, (tid, t["vv"])
        if "wizard" in t:
            assert t["wizard"] in wizard and t["wizard"] != "home", tid
        if "dialog" in t:
            assert t["dialog"] in ("export", "guide"), tid
        if "level" in t:
            assert t["level"] in (0, 1, 2, 3), tid
        if "domain" in t:
            assert t.get("level") == 3 and t["domain"] in domains, (tid, t["domain"])
        if "anchor" in t:
            assert t["anchor"] in anchors, (tid, t["anchor"], sorted(anchors))


def test_section_ids_are_what_the_panels_listen_for():
    """goWhere asks a panel for a section; the panel must listen (useWhereSection) for that tab."""
    listeners = {
        "decide": "workbench/DecisionPanel.tsx", "analyses": "workbench/AnalysesPanel.tsx",
        "budget": "workbench/BudgetPanel.tsx", "modes": "modes/ModesPanel.tsx",
        "tmtc": "cdr/TmtcPanel.tsx", "fdir": "cdr/FdirPanel.tsx", "vv": "workbench/VVPanel.tsx",
    }
    for tab, rel in listeners.items():
        assert f"useWhereSection('{tab}'" in _src(rel), rel
    assert "useWhereStore(s => s.wizard)" in _src("workbench/MissionWizard.tsx")
    used = {t.get("tab") for t in _wm()["targets"].values() if t.get("section")}
    assert used <= set(listeners), used - set(listeners)


# ─── labels use the screen's words ────────────────────────────────────────

def test_labels_use_the_screen_words_in_both_languages():
    fr = _fr()
    tabs = _panel_labels()
    vv_labels = {"budget": "Budget Rollup", "reqs": "Requirements", "gates": "Review Gates", "fmeca": "FMECA",
                 "trace": "Traceability", "risks": "Risk Register", "bom": "BOM", "maturity": "Maturity"}
    decide_titles = dict(re.findall(r'whereId="([\w-]+)" title=\{(?:hasWeights \? )?t\(\'([^\']+)\'\)',
                                    _src("workbench/DecisionPanel.tsx")))
    an = _src("workbench/AnalysesPanel.tsx")
    card = dict(re.findall(r"^\s+(\w+): '([^']+)',$", re.search(r"const CARD_LABELS[^{]+\{(.+?)\n\}", an, re.S).group(1), re.M))
    mode_views = {"machine": "Mode machine", "matrix": "Power by mode", "energy": "Energy per orbit", "data": "Data chain"}
    for tid, t in _wm()["targets"].items():
        en, frl = t["label"]["en"], t["label"]["fr"]
        assert en and frl, tid
        words: list[str] = []
        if t.get("tab"):
            words.append(tabs[t["tab"]])
        if t.get("vv"):
            words += ["V&V", vv_labels[t["vv"]]]
        if t.get("tab") == "decide" and t.get("section"):
            words.append(decide_titles[t["section"]].split(" (")[0])
        if t.get("tab") == "analyses" and t.get("section"):
            words.append(card.get(t["section"], "Link budget" if t["section"] == "link_budget" else t["section"]))
        if t.get("tab") == "modes" and t.get("section") in mode_views:
            words.append(mode_views[t["section"]])
        if t.get("tab") == "budget":
            words.append({"mass": "Mass", "power": "Power", "data": "Data", "cost": "Cost"}[t["section"]])
        for w in words:
            assert w in en, f"{tid}: EN label {en!r} lacks the screen text {w!r}"
            w_fr = fr.get(w) or w
            if w in ("Pugh Matrix",):
                w_fr = "Matrice de Pugh"
            assert w_fr.split(" (")[0] in frl, f"{tid}: FR label {frl!r} lacks the screen text {w_fr!r}"


def test_reworded_questions_use_no_missing_screen_names():
    """The audit's "gap" names must be gone from the worksheet text (EN + FR) the logbook shows."""
    gone = ["Design Dashboard", "Gate Review tab", "Positions tab", "Compliance panel", "Generate from Objectives",
            "Level filter", "amber badge", "Orbit Trade Advisor", "Interface Matrix (red", "SpaceCDF Dashboard",
            "Pointing Budget display", "Link Budget tab", "Equipment Browser", "Cost tab", "Cost Breakdown",
            "ConOps Editor", "Exports tab", "ConOps tab", "Trade Studies tab"]
    text = (WS / "learner_workbook.yaml").read_text(encoding="utf-8")
    for g in gone:
        assert g not in text, g


# ─── audit coverage ───────────────────────────────────────────────────────

def _oer_sections() -> set[str]:
    secs: set[str] = set()
    for p in OER.glob("*.md"):
        m = re.match(r"(\d+)_", p.name)
        if m:
            secs.add(str(int(m.group(1))))
        secs |= set(re.findall(r"^## (\d+\.\d+) ", p.read_text(encoding="utf-8"), re.M))
    return secs


def test_every_question_is_audited():
    wm = _wm()
    parts = wm["parts"]
    ids = {f"{w['id']}/{q['id']}" for w in _wb()["worksheets"] for q in w["questions"]}
    assert ids == set(parts), (sorted(ids - set(parts)), sorted(set(parts) - ids))
    oer = _oer_sections()
    for key, p in parts.items():
        assert p.get("before") in STATUSES_BEFORE, key
        assert p.get("status") in STATUSES_NOW, (key, p.get("status"))
        if p["status"] in ("screen", "screen+book"):
            assert p.get("where"), f"{key}: answerable from the screens needs a where link"
        if p["status"] in ("screen+book", "book"):
            assert p.get("book"), f"{key}: needs a textbook section"
        if p["status"] == "deferred":
            assert len(str(p.get("reason") or "")) > 30, f"{key}: deferred needs a reason"
        if p["before"] in ("gap", "partial"):
            assert p.get("gap") or p.get("fix"), f"{key}: say what was missing or what was done"
        for b in p.get("book") or []:
            assert str(b) in oer, (key, b)
        for t in p.get("where") or []:
            assert t in wm["targets"], (key, t)
        for ln in p.get("links") or []:
            assert ln in wm["links"], (key, ln)


def test_every_decision_resolves_to_a_place():
    cat = yaml.safe_load((WS / "decision_catalogue.yaml").read_text(encoding="utf-8"))
    wm = _wm()
    ids = {d["id"] for d in cat["decisions"]}
    assert set(wm["decisions"]) <= ids, set(wm["decisions"]) - ids
    for d in cat["decisions"]:
        got = wh.for_decision(d["id"], d.get("part"), "fr")
        assert got["where"], f"{d['id']}: no where link (own entry or its workbook part)"
        assert all(w["label"] for w in got["where"])


def test_no_question_is_still_a_gap():
    now = [k for k, p in _wm()["parts"].items() if p["status"] in ("gap", "partial")]
    assert not now, now


# ─── links are safe ───────────────────────────────────────────────────────

def _allow() -> list[str]:
    src = _src("where/links.ts")
    return re.findall(r"'([^']+)'", re.search(r"ALLOWED_LINK_HOSTS[^=]*=\s*\[(.+?)\]", src, re.S).group(1))


def _allowed(url: str, allow: list[str]) -> bool:
    u = urlparse(url)
    if u.scheme != "https" or u.username or u.password or u.port:
        return False
    for entry in allow:
        host, _, path = entry.partition("/")
        if u.hostname == host and (not path or u.path.startswith("/" + path)):
            return True
    return False


def test_links_are_https_allow_listed_and_checked():
    allow = _allow()
    for lid, ln in _wm()["links"].items():
        for key in ("url", "url_fr"):
            if ln.get(key):
                assert _allowed(ln[key], allow), (lid, ln[key])
        assert ln["title"]["en"] and ln["title"]["fr"], lid
        assert re.match(r"\d{4}-\d{2}-\d{2}$", str(ln.get("checked"))), lid
        assert ln.get("why"), lid
        assert "wikipedia" not in ln["url"], lid


def test_links_open_safely_in_a_new_window():
    src = _src("where/WhereLinks.tsx")
    assert 'target="_blank"' in src and 'rel="noopener noreferrer"' in src
    assert "safeExternalUrl(" in src and "dangerouslySetInnerHTML" not in src


def test_server_drops_non_https_links(tmp_path):
    (tmp_path / "where_map.yaml").write_text(yaml.safe_dump({
        "targets": {"t": {"tab": "budget", "label": {"en": "Budget", "fr": "Bilans"}}},
        "links": {"ok": {"url": "https://www.esa.int/x", "url_fr": "https://www.esa.int/fr", "title": {"en": "A", "fr": "B"}},
                  "bad": {"url": "javascript:alert(1)", "title": {"en": "C", "fr": "D"}},
                  "http": {"url": "http://www.esa.int/x", "title": {"en": "E", "fr": "F"}}},
    }), encoding="utf-8")
    got = wh.links(["ok", "bad", "http", "missing"], "fr", tmp_path)
    assert [g["id"] for g in got] == ["ok"] and got[0]["url"] == "https://www.esa.int/fr" and got[0]["title"] == "B"
    assert wh.targets(["t", "nope"], "fr", tmp_path) == [{"id": "t", "label": "Bilans", "tab": "budget"}]


# ─── the logbook serves them ──────────────────────────────────────────────

def test_worksheet_questions_carry_where_book_and_links():
    sheets = {w["id"]: w for w in wsmod.for_context("design", {}, "fr", include_all=True)}
    q = next(q for q in sheets["LW-2.3"]["questions"] if q["id"] == "A")
    assert q["where"][0]["id"] == "analyses.dl_orbit"
    assert q["where"][0]["label"].startswith("Analyses › Boucle de conception")
    assert q["book"] == ["7.1", "7.2"] and {ln["id"] for ln in q["links"]} >= {"esa-orbits"}
    notes = next(q for q in sheets["LW-2.3"]["questions"] if q["id"] == "notes")
    assert notes["where"] == [] and notes["links"] == []


def test_catalogue_carries_where():
    c = dec.localised("en", [], None)
    d = next(x for x in c["decisions"] if x["id"] == "D-2.3-ORBIT")
    assert [w["id"] for w in d["where"]][:1] == ["decide.orbit_trade"]
    d = next(x for x in c["decisions"] if x["id"] == "D-1.2-RSSSA")      # from its part
    assert d["where"][0]["dialog"] == "export" and d["links"][0]["url"].startswith("https://")


# ─── generated documents are current ──────────────────────────────────────

@pytest.mark.parametrize("script", ["gen_worksheets.py", "gen_ws_audit.py"])
def test_generated_files_are_current(script):
    proc = subprocess.run([sys.executable, str(DESIGN / "scripts" / script), "--check"], cwd=DESIGN,
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "warning:" not in proc.stderr, proc.stderr


# ─── pure frontend helpers (Node type stripping, as tests/test_frontend_logic.py) ──

def _node(module: str, expr: str):
    import shutil
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    code = f"import * as m from {json.dumps(str(FE / module))}; console.log(JSON.stringify({expr}))"
    proc = subprocess.run([node, "--experimental-strip-types", "--no-warnings", "--input-type=module", "-e", code],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_safe_external_url_allows_only_listed_https_hosts():
    got = _node("where/links.ts", "["
                "'https://www.esa.int/x', 'http://www.esa.int/x', 'javascript:alert(1)', 'https://evil.example/x',"
                "'https://user:pw@www.esa.int/', 'https://www.esa.int:8443/', 'https://www.esa.int.evil.example/',"
                "'https://storage.googleapis.com/rideshare-static/a.pdf', 'https://storage.googleapis.com/other/a.pdf'"
                "].map(u => m.safeExternalUrl(u))")
    assert got == ["https://www.esa.int/x", None, None, None, None, None, None,
                   "https://storage.googleapis.com/rideshare-static/a.pdf", None]


def test_sun_synchronous_inclination():
    got = _node("workbench/orbitMath.ts", "[m.ssoInclinationDeg(500), m.ssoInclinationDeg(800), m.ssoInclinationDeg(40000)]")
    assert got[0] == pytest.approx(97.40, abs=0.02) and got[1] == pytest.approx(98.60, abs=0.03) and got[2] is None


def test_where_path_finds_space_segment_spacecraft_and_domain():
    els = json.dumps([
        {"id": "m", "name": "M", "element_type": "mission"},
        {"id": "g", "name": "Ground", "parent_id": "m", "element_type": "segment", "segment": "ground"},
        {"id": "s", "name": "Space", "parent_id": "m", "element_type": "segment", "segment": "space"},
        {"id": "c", "name": "SC", "parent_id": "s", "element_type": "system", "segment": "space"},
        {"id": "e", "name": "EPS", "parent_id": "c", "element_type": "subsystem", "subsystem_domain": "power"},
        {"id": "a", "name": "AOCS", "parent_id": "c", "element_type": "subsystem", "subsystem_domain": "aocs"},
    ])
    got = _node("where/path.ts", f"[0,1,2,3].map(l => (m.pathToLevel({els}, l) || []).map(e => e.id))"
                                 f".concat([(m.pathToLevel({els}, 3, 'aocs') || []).map(e => e.id)])"
                                 f".concat([m.pathToLevel([], 2)])")
    assert got == [["m"], ["m", "s"], ["m", "s", "c"], ["m", "s", "c", "e"], ["m", "s", "c", "a"], None]
