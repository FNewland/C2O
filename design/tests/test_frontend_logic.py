"""WP0 regressions for frontend-only defects (Nov 2026).

The pure helpers (no imports) run under Node's TypeScript type stripping; the wiring
fixes that live inside components are checked on the source.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"
NODE = shutil.which("node")


def _node(module: str, expr: str):
    if not NODE:
        pytest.skip("node not installed")
    code = f"import * as m from {json.dumps(str(SRC / module))}; console.log(JSON.stringify({expr}))"
    proc = subprocess.run([NODE, "--experimental-strip-types", "--no-warnings", "--input-type=module", "-e", code],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


# ── 8. Equal pairwise weights show 0 % ────────────────────────────────────────

def test_wp0_8_untouched_pairs_count_as_equal():
    w = _node("workbench/pairwise.ts", "m.pairwiseWeights(['Mass','Power','Cost','TRL','Risk'], {})")
    assert w == {k: pytest.approx(0.2) for k in ["Mass", "Power", "Cost", "TRL", "Risk"]}


def test_wp0_8_pairwise_preference_and_reverse_pairs():
    w = _node("workbench/pairwise.ts", "m.pairwiseWeights(['A','B'], {'A|B': 1})")
    assert w == {"A": 1.0, "B": 0.0}
    w = _node("workbench/pairwise.ts", "m.pairwiseWeights(['A','B','C'], {'B|A': 0})")   # A beats B, C equal
    assert w["A"] == pytest.approx(1.5 / 3) and w["B"] == pytest.approx(0.5 / 3)


def test_wp0_8_no_parent_state_update_during_render():
    src = (SRC / "workbench" / "DecisionPanel.tsx").read_text(encoding="utf-8")
    assert "useMemo(() => { onWeightsChanged" not in src


# ── 5. studyId not persisted across reloads ───────────────────────────────────

MEM = "(() => { const d = {}; return { getItem: k => (k in d ? d[k] : null), setItem: (k, v) => { d[k] = String(v) }, removeItem: k => { delete d[k] } } })()"


def test_wp0_5_study_survives_a_reload():
    out = _node("stores/studySession.ts", f"""(() => {{
      const s = {MEM}
      m.saveStudyId(s, 'ab12cd34')
      m.saveBreadcrumb(s, 'ab12cd34', [{{id: 'e1', name: 'Space Segment'}}])
      return {{ id: m.loadStudyId(s, ''), crumbs: m.loadBreadcrumb(s, 'ab12cd34'), other: m.loadBreadcrumb(s, 'zz'),
               url: m.loadStudyId(s, '?study=ff00'), bad: m.loadStudyId(null, '?study=../x') }}
    }})()""")
    assert out["id"] == "ab12cd34"
    assert out["crumbs"] == [{"id": "e1", "name": "Space Segment"}]
    assert out["other"] == [] and out["url"] == "ff00" and out["bad"] is None


def test_wp0_5_leaving_a_study_forgets_it():
    out = _node("stores/studySession.ts", f"(() => {{ const s = {MEM}; m.saveStudyId(s, 'x1'); m.saveStudyId(s, null); return m.loadStudyId(s, '') }})()")
    assert out is None


def test_wp0_5_store_reads_the_persisted_study():
    src = (SRC / "stores" / "uiStore.ts").read_text(encoding="utf-8")
    assert "studyId: initialStudy" in src and "saveStudyId(" in src


# ── 6. Level off-by-one: presets, element types, Quick Start ──────────────────

TREE = "[{id:'m', element_type:'mission', parent_id:null}, {id:'s', element_type:'segment', parent_id:'m'}, {id:'g', element_type:'segment', parent_id:'m'}]"


def test_wp0_6_types_follow_the_focus_not_the_depth():
    out = _node("workbench/blockLevels.ts", f"""(() => {{
      const els = {TREE}
      return {{ top: m.placement(els, null), mission: m.placement(els, 'm'), seg: m.placement(els, 's'),
               levels: ['segment','system','subsystem','component'].map(m.structuralLevel),
               legacy: m.placement([{{id:'s', element_type:'segment', parent_id:null}}], null) }}
    }})()""")
    # top level of a wizard study: a segment UNDER the mission root, never a second root
    assert out["top"] == {"parentId": "m", "childType": "segment"}
    assert out["mission"] == {"parentId": "m", "childType": "segment"}
    assert out["seg"] == {"parentId": "s", "childType": "system"}     # breadcrumb depth 2, structural level 1
    assert out["levels"] == [0, 1, 2, 3]
    assert out["legacy"] == {"parentId": None, "childType": "segment"}


def test_wp0_6_quick_start_shows_on_a_segment_at_any_depth():
    out = _node("workbench/blockLevels.ts", f"""(() => {{
      const els = {TREE}
      const withSys = [...els, {{id:'sc', element_type:'system', parent_id:'s'}}]
      return [m.showQuickStart(els, 's'), m.showQuickStart(withSys, 's'), m.showQuickStart(els, 'm'), m.showQuickStart(els, null)]
    }})()""")
    assert out == [True, False, False, False]


def test_wp0_6_blocks_panel_uses_the_helper():
    src = (SRC / "workbench" / "BlocksPanel.tsx").read_text(encoding="utf-8")
    assert "placement(allElements, focusElementId)" in src
    assert "currentLevel !== 1 || !isSegment" not in src


# ── 4. Run Analysis posts {} ───────────────────────────────────────────────────

def test_wp0_4_run_analysis_runs_the_study_loop():
    src = (SRC / "App.tsx").read_text(encoding="utf-8")
    assert "/design/${encodeURIComponent(studyId)}/run" in src
    assert "body: JSON.stringify({ requirements: {}, mission_need: {} })" not in src


# ── 1 (frontend half). The wizard sends alternatives_considered, all of them ─

def test_wp0_1_wizard_sends_every_alternative_under_the_model_name():
    src = (SRC / "workbench" / "MissionWizard.tsx").read_text(encoding="utf-8")
    assert "alternatives_considered: tradeResult?.alternatives?.map(" in src
    assert "alternatives?.slice(0, 5)" not in src


# ── 2 (frontend half). The gate panel sends no client state ──────────────────

def test_wp0_2_gate_panel_sends_no_client_state():
    src = (SRC / "components" / "useGateReview.ts").read_text(encoding="utf-8")
    assert "mission_need" not in src.split("*/", 1)[1] and "/rules/gates/" in src
    vv = (SRC / "workbench" / "VVPanel.tsx").read_text(encoding="utf-8")
    assert "useDesignStore" not in vv and "useActiveParameters" not in vv


# ── 9 (frontend half). No localStorage for team records ──────────────────────

def test_wp0_9_team_records_are_not_written_to_local_storage():
    for f in ("workbench/VVPanel.tsx", "workbench/DecisionPanel.tsx", "workbench/MissionWizard.tsx", "App.tsx"):
        src = (SRC / f).read_text(encoding="utf-8")
        assert "localStorage.setItem(`spacecdf-risks" not in src and "localStorage.setItem('spacecdf-pugh'" not in src, f
