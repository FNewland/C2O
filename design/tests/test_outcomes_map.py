"""The ORBIT NORTH outcomes map (configs/outcomes/orbit_north_outcomes.yaml) names only real
worksheets, decision records, videos and CLOs, tags every one of them, and the generated
documents (OUTCOMES_MAP_{en,fr}.md, the syllabus blocks) are up to date."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DESIGN = Path(__file__).resolve().parents[1]


def test_outcomes_map_ids_and_coverage():
    r = subprocess.run([sys.executable, "tools/gen_outcomes.py", "--check"], cwd=DESIGN,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_generated_outcome_documents_are_current(tmp_path):
    files = [DESIGN / f"docs/orbit_north/{n}" for n in
             ("OUTCOMES_MAP_en.md", "OUTCOMES_MAP_fr.md", "syllabus_en.md", "syllabus_fr.md")]
    before = {f: f.read_text() for f in files}
    try:
        subprocess.run([sys.executable, "tools/gen_outcomes.py"], cwd=DESIGN, check=True, capture_output=True)
        stale = [f.name for f in files if f.read_text() != before[f]]
    finally:
        for f, t in before.items():
            f.write_text(t)
    assert not stale, f"regenerate with `python3 tools/gen_outcomes.py`: {stale}"
