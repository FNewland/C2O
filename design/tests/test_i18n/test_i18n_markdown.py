"""Segmentation, hashing and status transitions of the Markdown sync."""
import os
import textwrap

from tools.i18n import cli, mdsync
from tools.i18n.textutil import text_hash

EN = textwrap.dedent("""\
    ---
    title: Demo
    ---
    Intro paragraph.

    # Power {#sec-power}

    Battery is 3.5 kg.

    ## Budget

    ```python
    # not a heading
    x = 1
    ```

    ## Budget

    Second budget section.

    # Thermal

    Heaters `HTR_BAT` at 20 C.
    """)

FR = textwrap.dedent("""\
    ---
    title: Démo
    ---
    Paragraphe d'introduction.

    # Puissance {#sec-power}

    La batterie pèse 3,5 kg.

    ## Bilan

    ```python
    # not a heading
    x = 1
    ```

    ## Bilan

    Deuxième section de bilan.

    # Thermique

    Réchauffeurs `HTR_BAT` à 20 C.
    """)


def test_segmentation_ids_and_roundtrip():
    secs = mdsync.segment(EN)
    assert "".join(s.text for s in secs) == EN
    assert [s.id for s in secs] == ["_preamble", "sec-power", "sec-power/budget", "sec-power/budget~2", "thermal"]
    assert [s.level for s in secs] == [0, 1, 2, 2, 1]
    assert secs[0].text.startswith("---\ntitle: Demo")       # front matter in preamble
    assert "# not a heading" in secs[2].text                   # fence is not a heading


def test_preamble_empty_when_file_starts_with_heading():
    secs = mdsync.segment("# A\n\ntext\n")
    assert secs[0].id == "_preamble" and secs[0].text == ""
    assert secs[1].id == "a"


def test_hash_stable_under_rewrap_and_trailing_space():
    a = "Para one is long\nand wrapped.  \n\nNext."
    b = "Para one is long and wrapped.\n\n\nNext.   "
    assert text_hash(a, en=True) == text_hash(b, en=True)
    assert text_hash(a, en=True) != text_hash(a.replace("long", "short"), en=True)


def test_nbsp_folded_on_en_side_only():
    assert text_hash("20 C", en=True) == text_hash("20 C", en=True)
    assert text_hash("Note :", en=False) != text_hash("Note :", en=False)


def _setup(tmp_path, en=EN, fr=FR):
    (tmp_path / "en").mkdir()
    (tmp_path / "en" / "doc.md").write_text(en, encoding="utf-8")
    if fr is not None:
        (tmp_path / "fr").mkdir()
        (tmp_path / "fr" / "doc.md").write_text(fr, encoding="utf-8")
    (tmp_path / "i18n.yaml").write_text("docs:\n  - {group: t, en: en/doc.md, fr: fr/doc.md}\n", encoding="utf-8")
    return str(tmp_path / "i18n.yaml")


def _statuses(cfgpath):
    from tools.i18n import config, docs
    cfg = config.load(cfgpath)
    ds = docs.analyse(cfg.docs[0])
    return ds, [(p.en.id if p.en else None, p.status) for p in ds.al.pairs]


def test_status_transitions(tmp_path):
    cfg = _setup(tmp_path)
    ds, st = _statuses(cfg)
    assert {s for _, s in st} == {"untracked"}
    assert cli.main(["--config", cfg, "accept", "--init"]) == 0
    assert os.path.exists(tmp_path / "fr" / ".i18n" / "doc.md.json")
    ds, st = _statuses(cfg)
    assert {s for _, s in st} == {"ok"}
    assert cli.main(["--config", cfg, "check"]) == 0

    # rewrap only: still ok
    en = tmp_path / "en" / "doc.md"
    en.write_text(EN.replace("Battery is 3.5 kg.", "Battery is\n3.5 kg."), encoding="utf-8")
    assert dict(_statuses(cfg)[1])["sec-power"] == "ok"

    # EN change -> stale (and check stays green: stale is a warning)
    en.write_text(EN.replace("Second budget section.", "Second budget section, revised."), encoding="utf-8")
    assert dict(_statuses(cfg)[1])["sec-power/budget~2"] == "stale"
    assert cli.main(["--config", cfg, "check"]) == 0
    assert cli.main(["--config", cfg, "check", "--strict"]) == 1

    # FR change too -> conflict
    fr = tmp_path / "fr" / "doc.md"
    fr.write_text(FR.replace("Deuxième section de bilan.", "Deuxième section du bilan."), encoding="utf-8")
    assert dict(_statuses(cfg)[1])["sec-power/budget~2"] == "conflict"

    # FR-only change elsewhere -> fr-edited
    fr.write_text(FR.replace("Réchauffeurs", "Les réchauffeurs"), encoding="utf-8")
    assert dict(_statuses(cfg)[1])["thermal"] == "fr-edited"

    # accept records both hashes -> ok
    cli.main(["--config", cfg, "accept"])
    assert {s for _, s in _statuses(cfg)[1]} == {"ok"}


def test_structure_change_realigns_by_id(tmp_path):
    cfg = _setup(tmp_path)
    cli.main(["--config", cfg, "accept", "--init"])
    en = tmp_path / "en" / "doc.md"
    # insert a new EN section before Thermal and delete the duplicate budget
    new_en = EN.replace("# Thermal", "# Orbit\n\nNew text.\n\n# Thermal")
    new_en = new_en.replace("## Budget\n\nSecond budget section.\n\n", "")
    en.write_text(new_en, encoding="utf-8")
    ds, st = _statuses(cfg)
    d = {}
    for sid, s in st:
        d.setdefault(sid, s)
    assert ds.al.structure_changed
    assert d["orbit"] == "missing"
    assert d["thermal"] == "ok" and d["sec-power"] == "ok"
    assert ("sec-power/budget~2", "orphan") not in st and any(s == "orphan" for _, s in st)
    # non-strict check: structure change is a warning, not an error
    assert cli.main(["--config", cfg, "check"]) == 0


def test_parity_breakage_is_an_error(tmp_path):
    cfg = _setup(tmp_path, fr=FR.replace("`HTR_BAT`", "`HTR_BATT`"))
    cli.main(["--config", cfg, "accept", "--init"])
    assert cli.main(["--config", cfg, "check"]) == 1
    # an explicit waiver turns the finding into a warning
    cli.main(["--config", cfg, "accept", "--waive"])
    assert cli.main(["--config", cfg, "check"]) == 0


def test_translate_bundle_and_apply_missing_file(tmp_path):
    cfg = _setup(tmp_path, fr=None)
    out = tmp_path / "work"
    assert cli.main(["--config", cfg, "translate", "--stale", "--emit", str(out)]) == 0
    import json
    man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    items = man["items"]
    assert [i["section_id"] for i in items] == ["_preamble", "sec-power", "sec-power/budget",
                                                  "sec-power/budget~2", "thermal"]
    fr_secs = mdsync.segment(FR)
    for it, sec in zip(items, fr_secs):
        (out / "docs" / (it["id"] + ".fr.md")).write_text(sec.text.replace("Note:", "Note :"), encoding="utf-8")
    assert cli.main(["--config", cfg, "apply", str(out)]) == 0
    written = (tmp_path / "fr" / "doc.md").read_text(encoding="utf-8")
    assert mdsync.levels(mdsync.segment(written)) == mdsync.levels(mdsync.segment(EN))
    _, st = _statuses(cfg)
    assert {s for _, s in st} == {"ok"}


def test_apply_updates_only_stale_section(tmp_path):
    cfg = _setup(tmp_path)
    cli.main(["--config", cfg, "accept", "--init"])
    en = tmp_path / "en" / "doc.md"
    en.write_text(EN.replace("Second budget section.", "Second budget section, revised."), encoding="utf-8")
    out = tmp_path / "w"
    cli.main(["--config", cfg, "translate", "--stale", "--emit", str(out)])
    import json
    items = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["items"]
    assert len(items) == 1 and items[0]["status"] == "stale"
    assert (out / "docs" / (items[0]["id"] + ".fr_current.md")).exists()
    (out / "docs" / (items[0]["id"] + ".fr.md")).write_text(
        "## Bilan\n\nDeuxième section de bilan, révisée !\n", encoding="utf-8")
    assert cli.main(["--config", cfg, "apply", str(out)]) == 0
    txt = (tmp_path / "fr" / "doc.md").read_text(encoding="utf-8")
    assert "révisée !" in txt and "Paragraphe d'introduction." in txt
    assert {s for _, s in _statuses(cfg)[1]} == {"ok"}


def test_accept_after_heading_rename_in_both_languages(tmp_path):
    """Renaming a heading in EN and FR together must not leave missing/orphan sections after accept."""
    cfg = _setup(tmp_path)
    cli.main(["--config", cfg, "accept", "--init"])
    (tmp_path / "en" / "doc.md").write_text(EN.replace("# Thermal", "# Thermal control"), encoding="utf-8")
    (tmp_path / "fr" / "doc.md").write_text(FR.replace("# Thermique", "# Contrôle thermique"), encoding="utf-8")
    ds, st = _statuses(cfg)
    assert any(s in ("missing", "orphan") for _, s in st)
    assert cli.main(["--config", cfg, "accept"]) == 0
    ds, st = _statuses(cfg)
    assert {s for _, s in st} == {"ok"}
    assert not ds.al.structure_changed
