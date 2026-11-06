"""Is a video's build up to date? A fingerprint of everything that changes what it shows or says.

A build writes ``out/<slug>/build.json`` with the fingerprint of its inputs. ``build-all``
rebuilds a video only when that fingerprint changed:

* the storyboard itself;
* how it is spoken: ``lexicon/*.yaml``, ``voices.yaml``, the TTS and lexicon code;
* how it is filmed and packaged: capture, assembly, captions, H5P code, the cursor overlay;
* what is on screen: the sources of every tool the storyboard films (``apps:``), plus
  the configs, procedure cards and worksheets an ops video reads, or the explainer page
  and its data for a ``viz`` video.

Content is hashed (not dates), so a ``git pull`` that changes nothing relevant changes
nothing here. Files are listed through git (tracked and untracked, ignoring ignored
files), so build output and caches never count.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from functools import lru_cache
from pathlib import Path

from .storyboard import REPO, ROOT

PIPELINE = ["video/c2ovideo/capture.py", "video/c2ovideo/assemble.py", "video/c2ovideo/captions.py",
            "video/c2ovideo/h5p.py", "video/c2ovideo/tts.py", "video/c2ovideo/lexicon.py",
            "video/c2ovideo/storyboard.py", "video/c2ovideo/uitext.py", "video/c2ovideo/worksheets.py",
            "video/c2ovideo/helpers.py", "video/c2ovideo/overlay.js",
            "video/lexicon", "video/voices.yaml"]

SIM_COMMON = ["sim/configs/eosat1", "sim/packages/smo-simulator/src", "sim/packages/smo-common/src"]
APP_SOURCES = {
    "mcs": ["sim/packages/smo-mcs/src"] + SIM_COMMON,
    "instructor": SIM_COMMON,
    "planner": ["sim/packages/smo-planner/src"] + SIM_COMMON,
    "tools": ["sim/tools/orbit_tools.py"] + SIM_COMMON,
    "docs": ["sim/docs", "sim/tools/doc_viewer.py"],
    "portal": ["sim/packages/smo-common/src/smo_common/ui"],
    "spacecdf": ["design/frontend/src", "design/packages", "design/configs"],
    "viz": ["video/explainers/explainer.js", "video/explainers/explainer.css", "shared/ui-viz"],
    "file": [],
}


@lru_cache(maxsize=None)
def _files(rel: str) -> tuple:
    p = REPO / rel
    if p.is_file():
        return (rel,)
    if not p.exists():
        return ()
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "--", rel],
                         cwd=REPO, capture_output=True, text=True, check=False).stdout.split()
    return tuple(sorted(out))


@lru_cache(maxsize=None)
def _hash_file(rel: str) -> str:
    try:
        return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()
    except OSError:
        return "missing"


def inputs(sb) -> list[str]:
    """Every path whose content goes into this video's fingerprint."""
    paths = [str(sb.path.resolve().relative_to(REPO))] + PIPELINE
    for app in sb.apps:
        paths += APP_SOURCES.get(app, [])
    # an explainer page and its data, from the goto paths of the viz app
    for act in sb.setup:
        g = act.get("goto") if isinstance(act, dict) else None
        if isinstance(g, dict) and g.get("app") == "viz":
            page = g.get("path", "").split("?")[0].lstrip("/")
            paths += [page, str(Path(page).parent / "data")]
    for src in sb.sources or []:          # the files a storyboard says it was written from
        rel = str(src).split(" ")[0]
        if (REPO / rel).exists():
            paths.append(rel)
    return sorted(set(paths))


def _spoken(sb) -> str:
    """What the narrator will actually say, after the lexicon: so a lexicon edit
    rebuilds only the videos whose speech it changes."""
    from . import LANGS, lexicon, tts
    h = hashlib.sha256()
    for step in sb.steps:
        for lang in LANGS:
            for sent in tts.sentences((step.say or {}).get(lang, "")):
                h.update(f"{lang}|{lexicon.spoken(sent, lang)}\n".encode())
    return h.hexdigest()


def compute(sb, legacy: bool = False) -> str:
    h = hashlib.sha256()
    for rel in inputs(sb):
        if rel == "video/lexicon" and not legacy:
            continue
        for f in _files(rel):
            h.update(f.encode())
            h.update(_hash_file(f).encode())
    if not legacy:
        h.update(b"spoken:" + _spoken(sb).encode())
    return h.hexdigest()[:20]


def record_path(sb) -> Path:
    return ROOT / "out" / sb.slug / "build.json"


def recorded(sb) -> dict:
    try:
        return json.loads(record_path(sb).read_text())
    except (OSError, ValueError):
        return {}


def save(sb, fp: str, langs: list[str]) -> None:
    import time
    f = record_path(sb)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"fingerprint": fp, "langs": sorted(langs),
                             "built": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=1))


def status(sb, langs: list[str]) -> tuple[bool, str]:
    """(needs_build, why)."""
    rec = recorded(sb)
    if not rec:
        return True, "never built here"
    if not set(langs) <= set(rec.get("langs") or []):
        return True, "a language is missing"
    for lang in langs:
        if not (ROOT / "out" / sb.slug / f"{sb.slug}.{lang}.h5p").exists():
            return True, f"{lang} package missing"
    fp = compute(sb)
    if fp != rec.get("fingerprint"):
        # a record from before the lexicon was fingerprinted by spoken text:
        # if it matches the old scheme, move it to the new one without a rebuild
        if rec.get("fingerprint") == compute(sb, legacy=True):
            rec["fingerprint"] = fp
            record_path(sb).write_text(json.dumps(rec, indent=1))
        else:
            return True, "inputs changed"
    return False, f"up to date (built {rec.get('built', '?')})"
