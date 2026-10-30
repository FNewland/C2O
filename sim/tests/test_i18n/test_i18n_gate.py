"""Repository gate: `i18n check` (non-strict) must report no errors.

Untranslated / stale / missing French only produces warnings; parity breakage,
placeholder mismatches, unknown FR catalog keys and lost identifiers are errors.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_i18n_check_has_no_errors():
    cfg = os.path.join(ROOT, "i18n.yaml")
    assert os.path.exists(cfg), "i18n.yaml missing at repo root"
    r = subprocess.run([sys.executable, "-m", "tools.i18n", "check", "--config", cfg],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
    out = r.stdout + r.stderr
    errors = [l for l in out.splitlines() if l.startswith("ERROR")]
    assert r.returncode == 0 and not errors, out[-4000:]
