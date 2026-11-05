"""H5P Interactive Video packages, one per language.

Libraries come from the official H5P content-type hub (the same download an
H5P site makes when you install "Interactive Video"), cached locally, and only
the runtime dependencies the package uses are bundled. Content is written from
the storyboard: the video with its own-language captions, chapter bookmarks,
the embedded questions (paused at the end of their step) and a submit screen.
French packages get the French UI strings shipped inside each library
(``language/fr.json``).

Brightspace (uOttawa's H5P) accepts the ``.h5p`` as is. The C2O welcome page
plays the unpacked copy with h5p-standalone.
"""

from __future__ import annotations

import copy
import html
import json
import shutil
import urllib.request
import uuid
import zipfile
from functools import lru_cache
from pathlib import Path

from . import worksheets
from .storyboard import Storyboard, tr
from .tts import CACHE

HUB = "https://api.h5p.org/v1/content-types/H5P.InteractiveVideo"
LIBDIR = CACHE / "h5p" / "libraries"
TEMPLATE = CACHE / "h5p" / "hub-content.json"
LANG_NAMES = {"en": {"en": "English", "fr": "anglais"}, "fr": {"en": "French", "fr": "Français"}}

L = {
    "en": {"workbook": "In your workbook", "submit": "Submit", "reflect_ph": "Your answer (copy it into your workbook)",
           "check": "Check your understanding", "ws": "Workbook: {id}"},
    "fr": {"workbook": "Dans votre cahier de travail", "submit": "Soumettre",
           "reflect_ph": "Votre réponse (reportez-la dans votre cahier de travail)",
           "check": "Vérifiez votre compréhension", "ws": "Cahier : {id}"},
}

LIBS = {
    "multichoice": ("H5P.MultiChoice", 1, 16, "Multiple Choice"),
    "truefalse": ("H5P.TrueFalse", 1, 8, "True/False Question"),
    "blanks": ("H5P.Blanks", 1, 14, "Fill in the Blanks"),
    "reflect": ("H5P.FreeTextQuestion", 1, 0, "Free Text Question"),
}
MAIN = ("H5P.InteractiveVideo", 1, 27)


def fetch_libraries(force: bool = False) -> Path:
    if LIBDIR.exists() and TEMPLATE.exists() and not force:
        return LIBDIR
    LIBDIR.parent.mkdir(parents=True, exist_ok=True)
    tmp = LIBDIR.parent / "hub.h5p"
    req = urllib.request.Request(HUB, data=b"", method="POST")
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    if LIBDIR.exists():
        shutil.rmtree(LIBDIR)
    LIBDIR.mkdir(parents=True)
    with zipfile.ZipFile(tmp) as z:
        for n in z.namelist():
            if n.startswith("content/") or n == "h5p.json":
                continue
            z.extract(n, LIBDIR)
        TEMPLATE.write_bytes(z.read("content/content.json"))
    tmp.unlink()
    return LIBDIR


def _libdir(name: str, major: int, minor: int) -> Path:
    return LIBDIR / f"{name}-{major}.{minor}"


@lru_cache(maxsize=None)
def _libjson(dirname: str) -> dict:
    return json.loads((LIBDIR / dirname / "library.json").read_text(encoding="utf-8"))


def closure(roots: list[tuple[str, int, int]]) -> list[str]:
    """Runtime library folders needed by ``roots`` (editor libraries excluded)."""
    seen: list[str] = []
    stack = [f"{n}-{a}.{b}" for n, a, b in roots]
    while stack:
        d = stack.pop()
        if d in seen or d.startswith("H5PEditor."):
            continue
        if not (LIBDIR / d).exists():
            raise FileNotFoundError(f"H5P library {d} missing from the hub download")
        seen.append(d)
        for dep in _libjson(d).get("preloadedDependencies", []):
            stack.append(f"{dep['machineName']}-{dep['majorVersion']}.{dep['minorVersion']}")
    return sorted(seen)


def licences(libs: list[str]) -> dict:
    return {d: _libjson(d).get("license", "unspecified") for d in libs}


# --------------------------------------------------------------- localisation
def _translate(sem: list, tr_sem: list, params, depth=0):
    """Replace English semantics defaults in ``params`` by the translated ones."""
    if not isinstance(params, dict):
        return params
    for f, t in zip(sem, tr_sem):
        name = f.get("name")
        if name not in params:
            continue
        v = params[name]
        typ = f.get("type")
        if typ == "text" and isinstance(v, str) and "default" in f and "default" in t and v == f["default"]:
            params[name] = t["default"]
        elif typ == "group" and isinstance(v, dict):
            _translate(f.get("fields", []), t.get("fields", []), v, depth + 1)
        elif typ == "list" and isinstance(v, list) and isinstance(f.get("field"), dict):
            ff, tf = f["field"], t.get("field", {})
            for item in v:
                if ff.get("type") == "group" and isinstance(item, dict):
                    _translate(ff.get("fields", []), tf.get("fields", []), item, depth + 1)
    return params


def localise(libdir: str, params: dict, lang: str) -> dict:
    if lang == "en":
        return params
    lf = LIBDIR / libdir / "language" / f"{lang}.json"
    if not lf.exists():
        return params
    sem = json.loads((LIBDIR / libdir / "semantics.json").read_text(encoding="utf-8"))
    trs = json.loads(lf.read_text(encoding="utf-8")).get("semantics", [])
    return _translate(sem, trs, params)


# ------------------------------------------------------------------ content
@lru_cache(maxsize=1)
def _hub() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def _example(lib: str) -> dict:
    for it in _hub()["interactiveVideo"]["assets"]["interactions"]:
        if it["action"]["library"].startswith(lib + " "):
            p = copy.deepcopy(it["action"]["params"])
            p.pop("media", None)
            return p
    raise KeyError(lib)


def _p(text: str) -> str:
    return "<p>" + html.escape(text).replace("\n", "<br>") + "</p>"


def _tie_note(q: dict, lang: str) -> str:
    t = q.get("worksheet")
    if not t:
        return ""
    return f"<p><em>{html.escape(L[lang]['ws'].format(id=t))} — {html.escape(worksheets.label(t, lang))}</em></p>"


def sub_id(sb: Storyboard, lang: str, step: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"c2o:{sb.id}:{lang}:{step}"))


def question_action(q: dict, lang: str) -> tuple[str, dict, str]:
    kind = q["type"]
    name, major, minor, ctitle = LIBS[kind]
    lib = f"{name} {major}.{minor}"
    p = _example(name)
    text = tr(q["text"], lang)
    if kind == "multichoice":
        p["question"] = _p(text) + _tie_note(q, lang)
        p["answers"] = [{"correct": bool(o.get("correct")), "text": f"<div>{html.escape(tr(o['text'], lang))}</div>\n",
                         "tipsAndFeedback": {"tip": "", "chosenFeedback": _p(tr(o['why'], lang)) if o.get("why") else "",
                                             "notChosenFeedback": ""}} for o in q["options"]]
        p["behaviour"].update({"randomAnswers": True, "type": "auto", "singlePoint": True})
    elif kind == "truefalse":
        p["question"] = _p(text) + _tie_note(q, lang)
        p["correct"] = "true" if q["answer"] else "false"
    elif kind == "blanks":
        p["text"] = _p(tr(q.get("intro") or {"en": "", "fr": ""}, lang)) + _tie_note(q, lang)
        p["questions"] = [_p(text)]
        p.setdefault("behaviour", {}).update({"caseSensitive": False, "acceptSpellingErrors": True})
    elif kind == "reflect":
        p["question"] = _p(text) + _tie_note(q, lang)
        p["placeholder"] = L[lang]["reflect_ph"]
        p["isRequired"] = False
        p.setdefault("i10n", {})["language"] = lang
    p = localise(f"{name}-{major}.{minor}", p, lang)
    if kind == "reflect" and lang == "fr":
        p["i10n"].update({"requiredText": "obligatoire", "requiredMessage": "Cette question exige une réponse",
                          "skipButtonLabel": "Passer la question", "submitButtonLabel": "Répondre et continuer"})
    return lib, p, ctitle


def content(sb: Storyboard, lang: str, meta: dict, video_rel: str, vtt_rel: str, poster_rel: str | None) -> dict:
    hub = copy.deepcopy(_hub())
    iv = {
        "video": {
            "startScreenOptions": {"title": tr(sb.title, lang), "hideStartTitle": False},
            "textTracks": {"videoTrack": [{"label": LANG_NAMES[lang][lang], "kind": "subtitles", "srcLang": lang,
                                           "track": {"path": vtt_rel, "mime": "text/vtt", "copyright": {"license": "CC0 1.0"}}}],
                           "defaultTrackLabel": LANG_NAMES[lang][lang]},
            "files": [{"path": video_rel, "mime": "video/mp4", "copyright": {"license": "CC0 1.0"}}],
        },
        "assets": {"interactions": [], "bookmarks": [], "endscreens": []},
        "summary": hub["interactiveVideo"]["summary"],
    }
    if poster_rel:
        iv["video"]["startScreenOptions"]["poster"] = {"path": poster_rel, "mime": "image/jpeg", "width": 1280, "height": 720,
                                                        "copyright": {"license": "CC0 1.0"}}
    for ch in meta["chapters"]:
        m, s = divmod(int(ch["start"]), 60)
        iv["assets"]["bookmarks"].append({"time": ch["start"], "label": f"{m}:{s:02d} {ch['title']}"})
    times = {q["step"]: q["time"] for q in meta["questions"]}
    for st in sb.steps:
        if not st.question:
            continue
        lib, params, ctitle = question_action(st.question, lang)
        t = times[st.id]
        iv["assets"]["interactions"].append({
            "x": 22, "y": 12, "width": 36, "height": 24, "duration": {"from": t, "to": t + 1},
            "libraryTitle": ctitle, "pause": True, "displayType": "poster", "buttonOnMobile": False, "label": "",
            "adaptivity": {"correct": {"allowOptOut": False, "message": ""}, "wrong": {"allowOptOut": False, "message": ""},
                           "requireCompletion": False},
            "action": {"library": lib, "params": params, "subContentId": sub_id(sb, lang, st.id),
                       "metadata": {"contentType": ctitle, "license": "CC0 1.0", "title": tr(st.title, lang)}},
        })
    iv["assets"]["endscreens"].append({"time": max(0.0, meta["duration"] - 0.6), "label": f"{L[lang]['submit']}"})
    top = {"interactiveVideo": iv, "override": dict(hub.get("override", {}), showBookmarksmenuOnLoad=False, showRewind10=True),
           "l10n": hub.get("l10n", {})}
    top = localise(f"{MAIN[0]}-{MAIN[1]}.{MAIN[2]}", top, lang)
    if lang == "fr":
        top["l10n"].update(IV_FR_FIX)
    return top


# Strings the official French language file leaves in English (H5P.InteractiveVideo 1.27).
IV_FR_FIX = {"mute": "Couper le son", "unmute": "Activer le son", "summary": "Résumé",
             "defaultAdaptivitySeekLabel": "Continuer", "more": "Autres options du lecteur",
             "videoProgressBar": "Progression de la vidéo", "navForwardDisabled": "L’avance rapide est désactivée",
             "endcardTableRowScore": "Note", "howToCreateInteractions": "Lancez la vidéo pour créer des interactions"}


def h5p_json(sb: Storyboard, lang: str, libs: list[str]) -> dict:
    deps = []
    for d in [f"{MAIN[0]}-{MAIN[1]}.{MAIN[2]}"] + sorted({f"{LIBS[s.question['type']][0]}-{LIBS[s.question['type']][1]}.{LIBS[s.question['type']][2]}"
                                                          for s in sb.steps if s.question}):
        j = _libjson(d)
        deps.append({"machineName": j["machineName"], "majorVersion": j["majorVersion"], "minorVersion": j["minorVersion"]})
    return {"title": tr(sb.title, lang), "language": lang, "defaultLanguage": lang, "mainLibrary": MAIN[0],
            "embedTypes": ["div", "iframe"], "license": "CC0 1.0", "authors": [{"name": "C2O / ORBIT NORTH", "role": "Author"}],
            "preloadedDependencies": deps, "extraTitle": tr(sb.title, lang)}


def build(sb: Storyboard, lang: str, media: Path, meta: dict) -> dict:
    """Write ``<slug>.<lang>.h5p`` and the unpacked ``h5p/<lang>/`` next to the media."""
    fetch_libraries()
    stem = f"{sb.slug}.{lang}"
    roots = [MAIN] + [LIBS[s.question["type"]][:3] for s in sb.steps if s.question]
    libs = closure(roots)
    vid, vtt, poster = f"videos/{stem}.mp4", f"videos/{stem}.vtt", f"images/{stem}.poster.jpg"
    c = content(sb, lang, meta, vid, vtt, poster)
    hj = h5p_json(sb, lang, libs)
    pkg = media / f"{stem}.h5p"
    with zipfile.ZipFile(pkg, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("h5p.json", json.dumps(hj, ensure_ascii=False))
        z.writestr("content/content.json", json.dumps(c, ensure_ascii=False))
        z.write(media / f"{stem}.mp4", f"content/{vid}", compress_type=zipfile.ZIP_STORED)
        z.write(media / f"{stem}.vtt", f"content/{vtt}")
        z.write(media / f"{stem}.poster.jpg", f"content/{poster}", compress_type=zipfile.ZIP_STORED)
        for d in libs:
            for f in sorted((LIBDIR / d).rglob("*")):
                if f.is_file():
                    z.write(f, f"{d}/{f.relative_to(LIBDIR / d).as_posix()}")
    # unpacked copy for the in-tool player (media shared by relative symlink)
    up = media / "h5p" / lang
    if up.exists():
        shutil.rmtree(up)
    (up / "content" / "videos").mkdir(parents=True)
    (up / "content" / "images").mkdir(parents=True)
    (up / "h5p.json").write_text(json.dumps(hj, ensure_ascii=False), encoding="utf-8")
    (up / "content" / "content.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    for rel, src in ((vid, f"{stem}.mp4"), (vtt, f"{stem}.vtt"), (poster, f"{stem}.poster.jpg")):
        dst = up / "content" / rel
        depth = len(Path(rel).parts) + 2               # content/<dir>/file -> ../../../
        dst.symlink_to(Path(*([".."] * depth)) / src)
    return {"package": pkg.name, "libraries": licences(libs)}


def export_libraries(dst: Path) -> list[str]:
    """Copy every runtime library once into ``dst`` (shared by all in-tool players)."""
    fetch_libraries()
    roots = [MAIN] + [v[:3] for v in LIBS.values()]
    libs = closure(roots)
    dst.mkdir(parents=True, exist_ok=True)
    for d in libs:
        if not (dst / d).exists():
            shutil.copytree(LIBDIR / d, dst / d)
    return libs
