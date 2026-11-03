"""The instructor inject form in French (INSTRUCTOR_CONSOLE_DESIGN.md §13
item 5): the failure catalogue's labels and effect text come from the models'
FAILURE_SPECS in English; tools/gen_failure_strings.py exports them to
configs/eosat1/i18n/en/failure_catalog.yaml for the YAML overlay, and the
console looks them up with tdb()."""
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
DB = REPO / "configs" / "eosat1" / "i18n" / "fr" / "db.yaml"
JS = REPO / "packages/smo-simulator/src/smo_simulator/instructor/static/modern/instructor.js"


def test_exported_strings_are_fresh():
    proc = subprocess.run([sys.executable, "tools/gen_failure_strings.py", "--check"], cwd=REPO,
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_every_failure_label_and_effect_has_french():
    from smo_simulator import failure_catalog as fc
    doc = yaml.safe_load(DB.read_text(encoding="utf-8"))
    rows = doc.get("entries", doc) if isinstance(doc, dict) else doc
    entries = {e["key"]: e for e in rows}
    missing = []
    for sub, specs in fc.catalog().items():
        if f"failsub:{sub}:label" not in entries:
            missing.append(f"failsub:{sub}:label")
        for name, spec in specs.items():
            for field in ("label", "effect"):
                if getattr(spec, field):
                    k = f"fail:{sub}.{name}:{field}"
                    if not (entries.get(k) or {}).get("fr"):
                        missing.append(k)
    assert not missing, missing[:10]


def test_the_inject_form_looks_them_up():
    js = JS.read_text(encoding="utf-8")
    for prefix in ("failsub:", "fail:", "failparam:", "failval:"):
        assert f"tdb(`{prefix}" in js, prefix
