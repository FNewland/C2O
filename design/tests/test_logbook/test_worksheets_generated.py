"""The logbook worksheets are generated from the workbook and stay current (LOGBOOK_SPEC.md §4).

Same pattern as sim/tests/test_content/test_generated_command_reference.py:
regenerating must be a no-op, so the in-tool worksheet text cannot drift
from the printed learner workbook (EN + FR).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

DESIGN = Path(__file__).resolve().parents[2]
GEN = DESIGN / "scripts" / "gen_worksheets.py"
OUT = DESIGN / "configs" / "worksheets" / "learner_workbook.yaml"
MAP = DESIGN / "configs" / "worksheets" / "worksheet_map.yaml"
WORKBENCH = DESIGN / "frontend" / "src" / "workbench" / "LevelWorkbench.tsx"


def _data():
    return yaml.safe_load(OUT.read_text(encoding="utf-8"))


def test_marked_generated():
    head = OUT.read_text(encoding="utf-8")[:400]
    assert "GENERATED FILE — DO NOT EDIT BY HAND" in head and "scripts/gen_worksheets.py" in head


def test_regeneration_is_a_no_op():
    proc = subprocess.run([sys.executable, str(GEN), "--check"], cwd=DESIGN,
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, (
        "configs/worksheets/learner_workbook.yaml is stale — run python3 scripts/gen_worksheets.py\n"
        + proc.stdout + proc.stderr)
    assert "warning:" not in proc.stderr, proc.stderr


def test_every_workbook_worksheet_is_present():
    md = (DESIGN / "docs" / "course" / "learner_workbook_expanded.md").read_text(encoding="utf-8")
    nums = re.findall(r"^# Worksheet (\d+\.\d+):", md, re.M)
    assert [w["number"] for w in _data()["worksheets"]] == nums
    assert len(nums) >= 20


def test_bilingual_and_unique_ids():
    seen = set()
    for w in _data()["worksheets"]:
        assert w["id"] not in seen
        seen.add(w["id"])
        assert w["title"]["en"] and w["title"]["fr"] and w["title"]["en"] != w["title"]["fr"]
        qids = [q["id"] for q in w["questions"]]
        assert len(qids) == len(set(qids)) and qids, w["id"]
        assert qids[-1] == "notes", f"{w['id']}: every worksheet ends with Notes & Reflections"
        for q in w["questions"]:
            assert q["text"]["en"] and q["text"]["fr"], (w["id"], q["id"])
            assert q["kind"] in ("text", "check", "number")
            if "prompt" in q:
                assert q["prompt"]["en"] and q["prompt"]["fr"]
                assert "___" not in q["prompt"]["en"]


def test_ids_do_not_clash_with_the_ops_workbook():
    assert all(w["id"].startswith("LW-") for w in _data()["worksheets"])


def test_map_names_real_steps_tabs_and_gates():
    """The hand-maintained map must use the frontend's real tab ids (drift guard)."""
    src = WORKBENCH.read_text(encoding="utf-8")
    panels = set(re.findall(r"'(\w+)'", re.search(r"const PANELS[^=]*=\s*\[([^\]]+)\]", src).group(1)))
    tabs = panels | {"vv"}
    steps = {"wizard:home", "wizard:problem", "wizard:stakeholders", "wizard:alternatives", "wizard:architecture"}
    gates = {"mdr", "prr", "srr", "pdr"}   # canonical ECSS gates (Nov 2026; mcr was the old MDR)
    wmap = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    for wid, m in wmap["worksheets"].items():
        assert set(m.get("tabs", [])) <= tabs, (wid, set(m["tabs"]) - tabs)
        assert set(m.get("steps", [])) <= steps, wid
        assert set(m.get("gates", [])) <= gates, wid
        assert set(m.get("levels", [])) <= {0, 1, 2, 3, 4}, wid
        assert m.get("phase", "exercise") in ("prep", "during", "debrief", "exercise"), wid
