"""The logbook worksheets are generated from the course workbook, never
hand-copied (LOGBOOK_SPEC §4), so the in-tool text cannot drift from the
printed workbook. Same gate as test_generated_command_reference.py.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
WS = REPO / "configs" / "eosat1" / "worksheets"
GENERATED = WS / "ops_week3.yaml"
MAP = WS / "worksheet_map.yaml"
PROC_INDEX = REPO / "configs" / "eosat1" / "procedures" / "procedure_index.yaml"
SCENARIOS = REPO / "configs" / "eosat1" / "scenarios"
WORKBOOK = REPO.parent / "design" / "docs" / "course" / "orbit_north_week3_workbook.md"

needs_workbook = pytest.mark.skipif(not WORKBOOK.exists(),
                                    reason="design/ (course workbook) not in this checkout")


def _run(*args):
    return subprocess.run([sys.executable, *args], cwd=REPO,
                          capture_output=True, text=True, timeout=120)


def test_marked_generated():
    text = GENERATED.read_text(encoding="utf-8")
    assert text.startswith("# GENERATED FILE — DO NOT EDIT BY HAND.")
    assert "tools/gen_worksheets.py" in text.splitlines()[1]


@needs_workbook
def test_regeneration_is_byte_stable(tmp_path):
    out = tmp_path / "ops_week3.yaml"
    proc = _run("tools/gen_worksheets.py", "--output", str(out))
    assert proc.returncode == 0, proc.stderr
    assert out.read_bytes() == GENERATED.read_bytes(), (
        "configs/eosat1/worksheets/ops_week3.yaml is stale: re-run "
        "tools/gen_worksheets.py and commit the result")


@needs_workbook
def test_check_mode():
    proc = _run("tools/gen_worksheets.py", "--check")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_generator_does_not_read_the_wall_clock():
    text = (REPO / "tools" / "gen_worksheets.py").read_text()
    for clock in ("date.today(", "datetime.now(", "utcnow(", "time.time("):
        assert clock not in text


def test_every_worksheet_is_bilingual_and_well_formed():
    doc = yaml.safe_load(GENERATED.read_text(encoding="utf-8"))
    sheets = doc["worksheets"]
    assert len(sheets) >= 30
    for w in sheets:
        assert w["title"]["en"] and w["title"]["fr"], w["id"]
        assert w["phase"] in ("prep", "during", "debrief", "exercise")
        assert w["questions"], w["id"]
        ids = [q["id"] for q in w["questions"]]
        assert len(ids) == len(set(ids)), w["id"]
        for q in w["questions"]:
            assert q["kind"] in ("text", "check", "number")
            assert q["text"]["en"] and q["text"]["fr"], (w["id"], q["id"])
            assert "___" not in q["text"]["en"] and "**" not in q["text"]["en"]


def test_map_targets_exist():
    """Procedure ids and scenario names in the map are real ones."""
    mp = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    procs = {p["id"] for p in yaml.safe_load(PROC_INDEX.read_text())["procedures"]}
    scns = {p.stem for p in SCENARIOS.glob("*.yaml")}
    for wid, spec in mp["worksheets"].items():
        for p in spec.get("procedures") or []:
            assert p in procs, f"{wid}: unknown procedure {p}"
        for s in spec.get("scenarios") or []:
            assert s in scns, f"{wid}: unknown scenario {s}"


def test_procedure_worksheets_follow_the_id_convention():
    """NOM-001 -> WB-5.4-N001, LEOP-00x -> WB-5.5-L00x, COM-0xx -> WB-5.6-C0xx."""
    mp = yaml.safe_load(MAP.read_text(encoding="utf-8"))["worksheets"]
    for wid, spec in mp.items():
        m = re.fullmatch(r"WB-5\.\d-([NLC])(\d{3})", wid)
        if not m:
            continue
        procs = spec.get("procedures") or []
        assert any(p.endswith(m.group(2)) for p in procs), (wid, procs)
    assert mp["WB-5.4-N001"]["procedures"] == ["NOM-001"]
    assert mp["WB-5.4-C003"]["procedures"] == ["CTG-003"]
    assert mp["WB-5.4-N012"]["procedures"] == ["NOM-012"]
    for n in ("1", "2", "3", "5", "6", "7"):
        assert mp[f"WB-5.5-L00{n}"]["procedures"] == [f"LEOP-00{n}"]


def test_appendix_sheets_checklists_and_log_grids_parse():
    """WB-B / WB-C are appendices without card sub-headings; WB-C is a ☐
    checklist; WB-5.7-FR has a log grid whose bare row labels need columns."""
    sheets = {w["id"]: w for w in yaml.safe_load(GENERATED.read_text(encoding="utf-8"))["worksheets"]}
    for wid in ("WB-5.4-VL", "WB-5.7-WI", "WB-5.7-FR", "WB-B", "WB-C"):
        assert wid in sheets, wid
    c = sheets["WB-C"]["questions"]
    assert sum(q["kind"] == "check" for q in c) >= 30
    fr = [q["text"]["en"] for q in sheets["WB-5.7-FR"]["questions"]]
    assert "Wed — Anomaly · Procedure · Outcome · Root cause" in fr
    assert "Wed" not in fr
    assert any(t.startswith("Section 6") for t in fr)
    # the graded gate quiz and the anonymous evaluation never become records
    assert "WB-5.4-Q" not in sheets and "WB-5.7-CE" not in sheets
