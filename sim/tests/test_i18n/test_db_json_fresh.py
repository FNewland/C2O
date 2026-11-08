"""fr.db.json (what the browser loads) must match db.yaml (what translators edit).

It is built by `python3 -m tools.i18n build`; forgetting that step left 30
French overlay entries off the screen for days (2026-11-08).
"""
import json
from pathlib import Path

from tools.i18n import config, overlay

SIM = Path(__file__).resolve().parents[2]


def test_fr_db_json_is_built_from_db_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(SIM)
    cfg = config.load()
    assert cfg is not None and cfg.overlay, "no yaml_overlay in sim/i18n.yaml"
    out = tmp_path / "fr.db.json"
    overlay.build(cfg.overlay, str(out))
    shipped = Path(cfg.overlay["client_json_abs"]) if "client_json_abs" in cfg.overlay else None
    shipped = shipped or SIM / "packages/smo-common/src/smo_common/ui/i18n/fr.db.json"
    assert json.loads(out.read_text("utf-8")) == json.loads(shipped.read_text("utf-8")), \
        "fr.db.json is stale: run `python3 -m tools.i18n build` in sim/"
