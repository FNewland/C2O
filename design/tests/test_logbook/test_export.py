"""Export layout: day → tool → time, worksheet grouping, header and footer (LOGBOOK_SPEC.md §3)."""
from __future__ import annotations

from datetime import datetime, timezone

from spacecdf_server.logbook import export as ex

NOW = datetime(2026, 11, 3, 9, 30, tzinfo=timezone.utc)
EXP = datetime(2026, 11, 5, 8, 0, tzinfo=timezone.utc)


def _e(i, ts, tool="design", kind="thought", text=None, **kw):
    return {"id": f"e{i}", "ts": ts, "updated_ts": ts, "edited": False, "tool": tool, "kind": kind,
            "text": text or f"entry {i}", "context": kw.pop("context", {}), "worksheet": kw.pop("worksheet", None),
            "sim_ts": kw.pop("sim_ts", None), "lang": "en", **kw}


ENTRIES = [
    _e(1, "2026-11-02T14:00:00.000Z", kind="decision", text="Body-mounted arrays",
       context={"study_id": "s1", "study_name": "AuroraSat", "tab": "decide", "element": "EPS"}),
    _e(2, "2026-11-02T10:00:00.000Z", tool="mcs", kind="observation", text="Battery at 71 %",
       sim_ts="2026-03-10T04:18:22Z"),
    _e(3, "2026-11-03T08:00:00.000Z", kind="worksheet", text="SSO 550 km", worksheet={"id": "LW-2.3", "q": "B"}),
    _e(4, "2026-11-03T08:05:00.000Z", kind="worksheet", text="Pegasus first",
       worksheet={"id": "LW-2.3", "q": "A"}),
    _e(5, "2026-11-03T08:10:00.000Z", kind="worksheet", text="Ops answer",
       worksheet={"id": "WB-5.5-DB", "q": "q3", "title": "Day 3 Post-Shift Debrief", "question": "What surprised you?"}),
]


def lookup(wid, q, lang):
    if wid == "LW-2.3":
        return ("Orbit Selection", {"A": "Part A: Orbital Mechanics", "B": "Part B: Orbit Trade Matrix"}[q],
                {"A": 0, "B": 1}[q])
    return None, None, 10_000


def _md(lang="en", entries=ENTRIES, expires=EXP):
    return ex.render_markdown(entries=entries, person_label="alice@c2o.live", exported_at=NOW,
                              expires_at=expires, retention_h=48, lang=lang, lookup=lookup)


def test_header_and_footer():
    md = _md()
    assert md.startswith("# C2O logbook")
    assert "| **Person** | alice@c2o.live |" in md
    assert "| **Exported** | 2026-11-03 09:30 UTC |" in md
    assert "| **Tools** | Mission control (MCS), SpaceCDF (design) |" in md
    assert "| **Entries** | 5 |" in md
    assert "Deleted from the C2O server on 2026-11-05 08:00 UTC (48 h after the last entry)" in md


def test_grouped_by_day_then_tool_then_time():
    md = _md()
    d1, d2 = md.index("## 2026-11-02"), md.index("## 2026-11-03")
    assert d1 < md.index("### Mission control (MCS)") < md.index("### SpaceCDF (design)") < d2
    assert md.index("Battery at 71 %") < md.index("Body-mounted arrays")
    assert "sim time 2026-03-10 04:18 UTC" in md
    assert "study AuroraSat" in md and "s1" not in md.split("Body-mounted arrays")[1].split("##")[0]


def test_worksheet_answers_under_their_question_in_order():
    md = _md()
    assert "#### Worksheets — LW-2.3 Orbit Selection" in md
    a, b = md.index("**Part A: Orbital Mechanics**"), md.index("**Part B: Orbit Trade Matrix**")
    assert a < md.index("Pegasus first") and b < md.index("SSO 550 km") and a < b
    # an ops worksheet this tool has no YAML for still prints its stored question text
    assert "Day 3 Post-Shift Debrief" in md and "**What surprised you?**" in md


def test_french():
    md = _md("fr")
    assert md.startswith("# Journal de bord C2O")
    assert "Supprimé du serveur C2O le 2026-11-05 08:00 UTC (48 h" in md
    assert "Décision" in md and "Contrôle de mission (MCS)" in md


def test_empty():
    md = _md(entries=[], expires=None)
    assert "No entries." in md and "Nothing is stored on the C2O server." in md


def test_markdown_does_not_let_text_become_a_heading():
    md = _md(entries=[_e(9, "2026-11-02T14:00:00Z", text="# not a heading\nline two")])
    assert "\\# not a heading" in md


def test_html_is_self_contained_and_escaped():
    html = ex.render_html(entries=ENTRIES + [_e(8, "2026-11-02T15:00:00Z", text="<b>x</b> & y")],
                          person_label="alice@c2o.live", exported_at=NOW, expires_at=EXP,
                          retention_h=48, lang="en", lookup=lookup)
    assert html.startswith("<!doctype html>") and "<script" not in html
    assert "&lt;b&gt;x&lt;/b&gt; &amp; y" in html
    assert "@page" in html and "@media print" in html
    assert "http://" not in html and "https://" not in html, "no external resources"
    assert "Deleted from the C2O server on 2026-11-05 08:00 UTC" in html
