"""Video pipeline: everything that runs without a browser, a voice model or ffmpeg.

Run from ``video/``:  python -m pytest -q tests
"""
from __future__ import annotations

import json
import re
import wave
from pathlib import Path

import pytest

from c2ovideo import LANGS, captions, h5p, lexicon, storyboard, tts, uitext, worksheets
from c2ovideo.__main__ import validate


# ------------------------------------------------------------- storyboards
@pytest.mark.parametrize("sb", storyboard.all_storyboards(), ids=lambda s: s.id)
def test_every_storyboard_is_valid_in_both_languages(sb):
    assert not validate(sb), validate(sb)
    for st in sb.steps:
        for lang in LANGS:
            assert storyboard.tr(st.say, lang).strip()
    assert sb.licence == "CC0-1.0"
    # the graded quiz is never mirrored by a video
    for st in sb.steps:
        assert not (st.question or {}).get("worksheet", "").startswith("WB-5.4-Q")


def test_storyboard_rejects_missing_french(tmp_path):
    p = tmp_path / "x.yaml"
    p.write_text("id: V-X-01\ntitle: {en: T}\nsummary: {en: S, fr: R}\nsteps: []\n", encoding="utf-8")
    with pytest.raises(storyboard.StoryboardError, match="title"):
        storyboard.load(p)


def test_question_checks(tmp_path):
    p = tmp_path / "x.yaml"
    p.write_text("""
id: V-X-01
title: {en: T, fr: T}
summary: {en: S, fr: R}
steps:
  - id: a
    title: {en: A, fr: A}
    say: {en: Hello., fr: Bonjour.}
    question: {type: multichoice, text: {en: Q, fr: Q}, options: [{text: {en: x, fr: x}}, {text: {en: y, fr: y}}]}
""", encoding="utf-8")
    with pytest.raises(storyboard.StoryboardError, match="one correct"):
        storyboard.load(p)


# ----------------------------------------------------------------- lexicon
def test_lexicon_reads_identifiers_aloud_and_keeps_captions():
    en = lexicon.spoken("Send HK_REQUEST with SID 1 during LEOP-001; the bus reads 28.8 V.", "en")
    assert "H K request" in en and "S I D" in en and "lee-op zero zero one" in en and "28.8 volts" in en
    fr = lexicon.spoken("Le bus lit 28.8 V à NOM-001 ; voir LW-1.4.", "fr")
    assert "28 virgule 8 volts" in fr and "N. O. M. zéro zéro un" in fr and "fiche 1 point 4" in fr
    assert lexicon.unknown_tokens("Check the XYZ unit", "en") == ["XYZ"]


# ------------------------------------------------------------ UI strings
def test_ui_strings_come_from_the_tool_catalogue():
    assert uitext.ui("spacecdf", "Create New Mission", "fr") == "Créer une mission"
    assert uitext.ui("spacecdf", "Stakeholder 2: name / organisation", "fr").replace("\xa0", " ") == "Partie prenante 2 : nom / organisme"
    assert uitext.ui("spacecdf", {"en": "A", "fr": "B"}, "fr") == "B"
    with pytest.raises(uitext.MissingTranslation):
        uitext.ui("spacecdf", "No such button anywhere 42", "fr")


# --------------------------------------------------------------- captions
def test_captions_are_timed_from_sentences():
    placed = [captions.Placed("a", "Short one.", 3.2, 1.5, None),
              captions.Placed("a", "A much longer sentence that has to be split into more than one caption cue "
                                   "because it runs well past eighty-four characters in total length.", 5.0, 6.0, None)]
    v = captions.vtt(placed, "en")
    assert v.startswith("WEBVTT") and "00:00:03.200 --> 00:00:04.700" in v
    cues = re.findall(r"(\d\d:\d\d:\d\d\.\d{3}) --> (\d\d:\d\d:\d\d\.\d{3})\n(.+?)\n\n", v + "\n", re.S)
    assert len(cues) >= 3
    assert all(len(line) <= 60 for _, _, txt in cues for line in txt.split("\n"))
    assert cues[-1][1] == "00:00:11.000"


def test_sentence_split_keeps_abbreviations():
    assert tts.sentences("Use e.g. the planner. Then go. 3 passes remain.") == \
        ["Use e.g. the planner.", "Then go.", "3 passes remain."]


def test_silence_backend_narrates_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(tts, "CACHE", tmp_path)
    clips = tts.say("First sentence. Second one here.", "fr", override="silence")
    assert len(clips) == 2 and all(c.path.exists() and c.seconds > 0.3 for c in clips)
    with wave.open(str(clips[0].path)) as w:
        assert w.getframerate() == tts.SR


# -------------------------------------------------------------- worksheets
def test_ties_resolve_to_bilingual_labels():
    assert "Partie B" in worksheets.label("LW-1.4/B", "fr")
    assert worksheets.label("D-1.4-PROBLEM", "en").startswith("Decision record")
    with pytest.raises(worksheets.TieError):
        worksheets.resolve("WB-5.4-Q")
    with pytest.raises(worksheets.TieError):
        worksheets.resolve("LW-1.4/Z")


# ---------------------------------------------------------------- H5P
def test_h5p_french_defaults_replace_english_only():
    sem = [{"name": "l10n", "type": "group", "fields": [
        {"name": "play", "type": "text", "default": "Play"},
        {"name": "custom", "type": "text", "default": "Keep"}]}]
    trs = [{"fields": [{"default": "Lire"}, {"default": "Garder"}]}]
    params = {"l10n": {"play": "Play", "custom": "Already set"}}
    out = h5p._translate(sem, trs, params)
    assert out["l10n"] == {"play": "Lire", "custom": "Already set"}


def test_sub_content_ids_are_stable():
    sb = storyboard.load("V-SCDF-01")
    a, b = h5p.sub_id(sb, "fr", "problem"), h5p.sub_id(sb, "fr", "problem")
    assert a == b and a != h5p.sub_id(sb, "en", "problem")


@pytest.mark.skipif(not h5p.TEMPLATE.exists(), reason="H5P libraries not downloaded (python -m c2ovideo fetch-h5p)")
def test_h5p_content_for_a_storyboard():
    sb = storyboard.load("V-SCDF-01")
    meta = {"duration": 150.0, "chapters": [{"start": 3.2, "title": "Intro"}],
            "questions": [{"step": s.id, "time": 20.0 + i} for i, s in enumerate(sb.steps) if s.question]}
    c = h5p.content(sb, "fr", meta, "videos/x.mp4", "videos/x.vtt", None)
    iv = c["interactiveVideo"]
    assert iv["video"]["files"][0]["path"] == "videos/x.mp4"
    assert iv["video"]["textTracks"]["videoTrack"][0]["srcLang"] == "fr"
    acts = iv["assets"]["interactions"]
    assert len(acts) == len(meta["questions"]) and all(a["pause"] for a in acts)
    assert c["l10n"]["mute"] == "Couper le son"
    libs = h5p.closure([h5p.MAIN] + [h5p.LIBS[s.question["type"]][:3] for s in sb.steps if s.question])
    assert not any(l.startswith("H5PEditor.") for l in libs)
