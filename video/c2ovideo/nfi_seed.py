"""Setup helper for the Northern Fire and Ice walkthrough videos (V-SCDF-08 … V-SCDF-24).

Storyboards call it before the capture starts::

    - python: {call: "video/c2ovideo/nfi_seed.py:seed", app: spacecdf, save: study,
               kwargs: {stage: S4, after: "licensing ledger"}}

It runs ``design/tests/fixtures/nfi/recording.py`` with the SpaceCDF server's own Python (the seed
imports the server's packages): the recording seed, the scenes filmed in the earlier videos, and
the team of script §0.3 (9 seats + Propulsion + Cost & risk, all held by the browser whose
``scdf.client_id`` is ``client``). Returns the study id. Kept out of ``helpers.py`` so that adding
it does not change the fingerprint of every other video.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

CLIENT = "nfirec"


def seed(client, stage: str = "S4", after: str = "", team: bool = True, claim: bool = True,
         name: str = "NFI Team") -> str:
    if str(REPO / "video") not in sys.path:      # loaded by file path from a storyboard
        sys.path.insert(0, str(REPO / "video"))
    from c2ovideo import stack

    design = REPO / "design"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(
        [str(design / "packages" / p / "src") for p in stack.DESIGN_PACKAGES] + [str(design)]))
    cmd = [stack.design_python(), "-m", "tests.fixtures.nfi.recording", "--url", client.base,
           "--stage", stage, "--after", after or "", "--client", CLIENT if team else "", "--name", name]
    if not claim:
        cmd.append("--no-claim")
    r = subprocess.run(cmd, cwd=str(design), env=env, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError(f"nfi seed failed ({r.returncode}): {r.stderr[-1500:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])["study"]


def after(client, study: str, steps: str) -> str:
    """Mid-video: apply ``recording.py`` steps to the filmed study (what the other seats do off
    camera, e.g. ``ledger-agree`` once one seat has agreed its line on camera)."""
    if str(REPO / "video") not in sys.path:
        sys.path.insert(0, str(REPO / "video"))
    from c2ovideo import stack

    design = REPO / "design"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(
        [str(design / "packages" / p / "src") for p in stack.DESIGN_PACKAGES] + [str(design)]))
    r = subprocess.run([stack.design_python(), "-m", "tests.fixtures.nfi.recording", "--url", client.base,
                        "--study", study, "--after", steps, "--client", CLIENT], cwd=str(design), env=env,
                       capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise RuntimeError(f"nfi after-steps failed ({r.returncode}): {r.stderr[-1500:]}")
    return study
