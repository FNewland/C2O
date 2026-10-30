"""Catalog key scanning and parity (placeholders, plurals, context, orphans)."""
import json

from tools.i18n import catalogs, cli
from tools.i18n.config import Catalog

JS = r"""
import { t, tText } from "/static/shared/i18n.js";
el.innerHTML = `<th>${t("Parameter")}</th>` + tText('Value {{v}} of {{max}}', {v: 1, max: 2});
alert(tText("Can't reach {{host}}", { host }));
const n = tText("1 file", { count: n, plural: "{{count}} files" });
const s = t("Open", { context: "door" });
t(`dynamic ${x}`);   // skipped
format("not a key");
"""

HTML = """<!doctype html><html><body>
<h1 data-i18n>Mission  control
  console</h1>
<button data-i18n-title title="Acknowledge alarm">ACK</button>
<span data-i18n="Explicit key">ignored text</span>
<p data-i18n-html>Press <b>Enter</b> to log</p>
<input data-i18n-placeholder="Console note…" placeholder="x">
<script type="module">document.title = tText("Inline script");</script>
</body></html>"""


def test_scanners():
    keys = catalogs.scan_js(JS)
    assert {"Parameter", "Value {{v}} of {{max}}", "Can't reach {{host}}", "1 file", "Open"} <= set(keys)
    assert "plural" in keys["1 file"] and "pl:{{count}} files" in keys["1 file"]
    assert "ctx:door" in keys["Open"]
    assert not any(k.startswith("dynamic") for k in keys) and "not a key" not in keys
    h = catalogs.scan_html(HTML)
    assert {"Mission control console", "Acknowledge alarm", "Explicit key",
            "Press <b>Enter</b> to log", "Console note…", "Inline script"} <= set(h)
    assert "ignored text" not in h


def _cat(tmp_path, fr: dict | None, fallback=None):
    (tmp_path / "app.js").write_text(JS, encoding="utf-8")
    p = tmp_path / "fr.json"
    if fr is not None:
        p.write_text(json.dumps(fr, ensure_ascii=False), encoding="utf-8")
    return Catalog("app", str(p), None, [str(tmp_path / "*.js")], fallback or [], [])


def test_missing_keys_are_warnings_not_errors(tmp_path):
    r = catalogs.check_catalog(_cat(tmp_path, None), {})
    assert not r["errors"]
    assert set(r["missing"]) == {"Parameter", "Value {{v}} of {{max}}", "Can't reach {{host}}",
                                 "1 file_one", "1 file_other", "Open_door"}   # "Open" only used with a context


def test_placeholder_mismatch_and_orphan_are_errors(tmp_path):
    fr = {"Parameter": "Paramètre",
          "Value {{v}} of {{max}}": "Valeur {{val}} sur {{max}}",     # wrong placeholder
          "Stale key": "Clé périmée"}                                  # not in sources
    r = catalogs.check_catalog(_cat(tmp_path, fr), {})
    errs = "\n".join(r["errors"])
    assert "placeholder mismatch" in errs and "Stale key" in errs
    assert r["stats"]["translated"] == 2


def test_plurals_and_context(tmp_path):
    fr = {"1 file_one": "1 fichier", "1 file_other": "{{count}} fichiers", "1 file_many": "{{count}} de fichiers",
          "Open_door": "Ouvrir", "Can't reach {{host}}": "Impossible de joindre {{host}}"}
    r = catalogs.check_catalog(_cat(tmp_path, fr), {})
    assert not r["errors"], r["errors"]
    assert "1 file_one" not in r["missing"] and "Open" not in r["missing"]
    assert "Open_door" not in r["missing"]


def test_plain_key_satisfies_context(tmp_path):
    r = catalogs.check_catalog(_cat(tmp_path, {"Open": "Ouvrir"}), {})
    assert "Open_door" not in r["missing"] and not r["errors"]


def test_identifiers_and_numbers_preserved():
    assert catalogs.string_problems("Send AOCS_SET_MODE now", "Envoyer AOCS_SET_MODE")== []
    assert catalogs.string_problems("Send AOCS_SET_MODE now", "Envoyer la commande")
    assert catalogs.string_problems("Wait 8 s", "Attendre 9 s")
    assert catalogs.string_problems("Battery 3.5 V", "Batterie 3,5 V") == []


def test_fallback_catalog_counts_as_translated(tmp_path):
    shared = tmp_path / "shared.json"
    shared.write_text(json.dumps({"Parameter": "Paramètre"}), encoding="utf-8")
    sc = Catalog("shared", str(shared), None, [], [], [])
    app = _cat(tmp_path, {}, fallback=["shared"])
    r = catalogs.check_catalog(app, {"shared": sc, "app": app})
    assert "Parameter" not in r["missing"]


def test_extract_adds_null_skeleton(tmp_path):
    c = _cat(tmp_path, {"Parameter": "Paramètre", "Gone": None})
    res = catalogs.extract_catalog(c, prune=True)
    data = json.loads((tmp_path / "fr.json").read_text(encoding="utf-8"))
    assert data["Parameter"] == "Paramètre" and data["1 file_one"] is None and "Gone" not in data
    assert res["orphans"] == ["Gone"]


def test_cli_catalog_check(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.js").write_text('t("Hello {{name}}")', encoding="utf-8")
    (tmp_path / "fr.json").write_text(json.dumps({"Hello {{name}}": "Bonjour {{nom}}"}), encoding="utf-8")
    (tmp_path / "i18n.yaml").write_text(
        "catalogs:\n  - name: a\n    fr: fr.json\n    sources: [src/*.js]\n", encoding="utf-8")
    assert cli.main(["--config", str(tmp_path / "i18n.yaml"), "check"]) == 1
    (tmp_path / "fr.json").write_text(json.dumps({"Hello {{name}}": "Bonjour {{name}}"}), encoding="utf-8")
    assert cli.main(["--config", str(tmp_path / "i18n.yaml"), "check"]) == 0


def test_marked_tables_are_keys():
    src = ("// English text is the i18n key; translate with t(LABELS[k])\n"
           "const LABELS: Record<number, string> = {\n  1: 'Systems',\n  4: 'V&V',\n}\n"
           "// i18n-keys\nconst STEPS = ['Load shed ladder', \"FPA cooldown\"]\n"
           "const OTHER = { a: 'not a key' }\n")
    keys = catalogs.scan_js(src)
    assert {"Systems", "V&V", "Load shed ladder", "FPA cooldown"} <= set(keys)
    assert "not a key" not in keys
