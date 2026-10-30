"""YAML overlay extraction round trip, staleness, build; mini YAML reader."""
import json
import textwrap

import pytest

from tools.i18n import cli, config, overlay, yamlmini

SRC = textwrap.dedent("""\
    commands:
      - name: AOCS_SET_MODE
        description: Set the AOCS mode
        fields:
          - {name: mode, type: uint8, description: "Target mode",
             enum: [{value: 5, label: FINE_POINT, description: "Refused unless ready"}]}
      - name: PING
        description: "Connection test: S17"
    quick_commands:
      - {group: TTC, label: PA ON, command: TTC_PA_ON}
      - {group: TTC, label: PA OFF, command: TTC_PA_OFF}
    roles:
      fd: {label: Flight Director, roles: {a: "Authorize pass", b: "GO/NO-GO"}}
    """)

CFG = textwrap.dedent("""\
    yaml_overlay:
      base: src
      output: out/db.yaml
      client_json: out/fr.db.json
      rules:
        - {kind: tc, files: cat.yaml, items: commands.*, id: "{name}", fields: [description]}
        - {kind: tcarg, files: cat.yaml, items: commands.*.fields.*, id: "{^name}.{name}", fields: [description]}
        - {kind: tcenum, files: cat.yaml, items: commands.*.fields.*.enum.*, id: "{^^name}.{^name}.{label}", fields: [description]}
        - {kind: qc, files: cat.yaml, items: quick_commands.*, id: "{name|command}", fields: [label]}
        - {kind: role, files: cat.yaml, items: roles.*, id: "{$key}", fields: [label, roles.*]}
    """)


def _setup(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "cat.yaml").write_text(SRC, encoding="utf-8")
    (tmp_path / "i18n.yaml").write_text(CFG, encoding="utf-8")
    return str(tmp_path / "i18n.yaml")


def test_extract_keys_and_roundtrip(tmp_path):
    pytest.importorskip("yaml")
    cfgp = _setup(tmp_path)
    assert cli.main(["--config", cfgp, "extract", "--only", "overlay"]) == 0
    cfg = config.load(cfgp)
    ents = overlay.load_db(cfg.overlay["output_abs"])
    keys = [e["key"] for e in ents]
    assert keys == ["tc:AOCS_SET_MODE:description", "tc:PING:description",
                    "tcarg:AOCS_SET_MODE.mode:description",
                    "tcenum:AOCS_SET_MODE.mode.FINE_POINT:description",
                    "qc:TTC_PA_ON:label", "qc:TTC_PA_OFF:label",
                    "role:fd:label", "role:fd:roles.a", "role:fd:roles.b"]
    assert all(e["fr"] is None for e in ents)
    # the fast reader (no PyYAML) and PyYAML agree on the written file
    text = open(cfg.overlay["output_abs"], encoding="utf-8").read()
    assert overlay._load_db_fast(text)["entries"] == yamlmini.load(text)["entries"]

    # translate two, change the English of one, re-extract → stale with en_prev
    for e in ents:
        if e["key"] == "tc:PING:description":
            e["fr"] = "Test de connexion : S17"
        if e["key"] == "qc:TTC_PA_ON:label":
            e["fr"] = "PA ON"
    overlay.save_db(cfg.overlay["output_abs"], ents)
    (tmp_path / "src" / "cat.yaml").write_text(SRC.replace("Connection test: S17", "Link test: S17"),
                                                encoding="utf-8")
    cli.main(["--config", cfgp, "extract", "--only", "overlay"])
    ents = {e["key"]: e for e in overlay.load_db(cfg.overlay["output_abs"])}
    ping = ents["tc:PING:description"]
    assert ping["en"] == "Link test: S17" and ping["en_prev"] == "Connection test: S17"
    assert overlay.is_stale(ping)
    assert overlay.summary(list(ents.values()))["stale"] == 1

    # build emits translated, non-stale entries only
    cli.main(["--config", cfgp, "build"])
    built = json.loads((tmp_path / "out" / "fr.db.json").read_text(encoding="utf-8"))
    assert built == {"qc:TTC_PA_ON:label": "PA ON"}

    # accept → no longer stale
    cli.main(["--config", cfgp, "accept", "--key", "tc:PING:description"])
    ents = {e["key"]: e for e in overlay.load_db(cfg.overlay["output_abs"])}
    assert not overlay.is_stale(ents["tc:PING:description"]) and "en_prev" not in ents["tc:PING:description"]

    # removing a source key keeps translated entries as orphans, drops untranslated ones
    (tmp_path / "src" / "cat.yaml").write_text(SRC.replace("  - {group: TTC, label: PA ON, command: TTC_PA_ON}\n", "")
                                                .replace("  - name: AOCS_SET_MODE", "  - name: AOCS_SET_MODE2"),
                                                encoding="utf-8")
    cli.main(["--config", cfgp, "extract", "--only", "overlay"])
    ents = {e["key"]: e for e in overlay.load_db(cfg.overlay["output_abs"])}
    assert ents["qc:TTC_PA_ON:label"]["orphan"] is True
    assert "tc:AOCS_SET_MODE:description" not in ents


def test_overlay_check_placeholder_error(tmp_path):
    pytest.importorskip("yaml")
    cfgp = _setup(tmp_path)
    cli.main(["--config", cfgp, "extract", "--only", "overlay"])
    cfg = config.load(cfgp)
    ents = overlay.load_db(cfg.overlay["output_abs"])
    ents[0]["fr"] = "Régler le mode"
    ents[1]["fr"] = "Test de liaison : S18"          # number changed → error
    overlay.save_db(cfg.overlay["output_abs"], ents)
    assert cli.main(["--config", cfgp, "check"]) == 1


def test_mini_yaml_matches_pyyaml_on_repo_config():
    yaml = pytest.importorskip("yaml")
    import os
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    text = open(os.path.join(root, "i18n.yaml"), encoding="utf-8").read()
    assert yamlmini.load(text, force_mini=True) == yaml.safe_load(text)
