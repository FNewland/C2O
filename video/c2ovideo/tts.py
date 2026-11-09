"""Offline text-to-speech, one clip per sentence, cached.

Backends (``video/voices.yaml`` picks one per language):

* ``kokoro`` — Kokoro-82M through kokoro-onnx (weights Apache-2.0, runtime MIT).
  English ``af_heart`` (default) and European French ``ff_siwis``. No usage
  restriction on the audio, so it can be published under CC0.
* ``piper`` — the ``piper`` command line with a downloaded ``.onnx`` voice
  (check each voice's model card before publishing; licences differ by voice).
* ``chatterbox`` — Chatterbox Multilingual (Resemble AI, MIT) cloning a reference
  recording, through ``cbx_worker.py`` in its own Python (``python`` key). The reference
  recording is personal: keep it outside the repository (``ref`` is resolved under
  ``$C2O_VIDEO_CACHE/voices`` when relative). Output carries Resemble's Perth watermark.
* ``silence`` — silent audio of a plausible length; for tests and dry runs.

Sentences are synthesised separately so caption timing is exact.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.request
import wave
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml

from . import lexicon
from .storyboard import ROOT

SR = 24000
CACHE = Path(os.environ.get("C2O_VIDEO_CACHE", Path.home() / ".cache" / "c2o-video"))
MODELS = Path(os.environ.get("C2O_VIDEO_MODELS", CACHE / "models"))
KOKORO_FILES = {
    "kokoro-v1.0.int8.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
GAP_S = 0.28          # pause between sentences
ABBREV = ("e.g.", "i.e.", "p. ex.", "c.-à-d.", "vs.", "etc.", "fig.", "No.", "n°")


def voices() -> dict:
    return yaml.safe_load((ROOT / "voices.yaml").read_text(encoding="utf-8"))


def sentences(text: str) -> list[str]:
    t = " ".join(text.split())
    protected = t
    for i, a in enumerate(ABBREV):
        protected = protected.replace(a, f"\x00{i}\x00")
    parts = re.split(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ«\"“(0-9])", protected)
    out = []
    for p in parts:
        for i, a in enumerate(ABBREV):
            p = p.replace(f"\x00{i}\x00", a)
        if p.strip():
            out.append(p.strip())
    return out


def fetch_models(verbose: bool = True) -> Path:
    MODELS.mkdir(parents=True, exist_ok=True)
    for name, url in KOKORO_FILES.items():
        dst = MODELS / name
        if dst.exists() and dst.stat().st_size > 1_000_000:
            continue
        if verbose:
            print(f"downloading {name} …")
        tmp = dst.with_suffix(".part")
        with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
        tmp.rename(dst)
    return MODELS


@lru_cache(maxsize=1)
def _kokoro():
    from kokoro_onnx import Kokoro  # imported lazily: optional dependency
    d = MODELS
    if not (d / "kokoro-v1.0.int8.onnx").exists():
        raise RuntimeError("Kokoro model not found: run `python -m c2ovideo fetch-models` first")
    return Kokoro(str(d / "kokoro-v1.0.int8.onnx"), str(d / "voices-v1.0.bin"))


@dataclass
class Clip:
    text: str            # written form (captions)
    spoken: str          # what was sent to the engine
    path: Path
    seconds: float


VOICES_DIR = CACHE / "voices"
_CBX = None


def _ref_path(engine: dict) -> Path:
    p = Path(engine["ref"]).expanduser()
    return p if p.is_absolute() else VOICES_DIR / p


def _cbx(engine: dict):
    """Start (once) the Chatterbox worker under the voice's own Python."""
    global _CBX
    if _CBX is None or _CBX.poll() is not None:
        py = str(Path(engine.get("python", "python3")).expanduser())
        _CBX = subprocess.Popen([py, str(Path(__file__).with_name("cbx_worker.py"))], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        while True:
            line = _CBX.stdout.readline()
            if not line:
                raise RuntimeError("Chatterbox worker exited during start-up")
            if line.startswith("{") and json.loads(line).get("ready"):
                break
    return _CBX


def _synth(engine: dict, text: str, lang: str) -> np.ndarray:
    kind = engine["backend"]
    if kind == "silence":
        words = max(1, len(text.split()))
        return np.zeros(int(SR * (0.35 + words / (2.5 if lang == "en" else 2.6))), dtype=np.float32)
    if kind == "kokoro":
        samples, sr = _kokoro().create(text, voice=engine["voice"], speed=float(engine.get("speed", 1.0)),
                                       lang=engine.get("lang", "en-us" if lang == "en" else "fr-fr"))
        a = np.asarray(samples, dtype=np.float32)
        if sr != SR:
            a = np.interp(np.linspace(0, len(a), int(len(a) * SR / sr), endpoint=False), np.arange(len(a)), a).astype(np.float32)
        return a
    if kind == "piper":
        exe = shutil.which(engine.get("command", "piper")) or engine.get("command", "piper")
        model = Path(engine["model"]).expanduser()
        if not model.is_absolute():
            model = MODELS / model
        out = subprocess.run([exe, "--model", str(model), "--output-raw"], input=text.encode("utf-8"),
                             capture_output=True, check=True)
        sr = int(engine.get("sample_rate", 22050))
        a = np.frombuffer(out.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        return np.interp(np.linspace(0, len(a), int(len(a) * SR / sr), endpoint=False), np.arange(len(a)), a).astype(np.float32)
    if kind == "chatterbox":
        import tempfile
        w = _cbx(engine)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            out = f.name
        req = {"text": text, "lang": engine.get("lang", lang)[:2], "ref": str(_ref_path(engine)), "out": out,
               "exaggeration": engine.get("exaggeration", 0.5), "cfg_weight": engine.get("cfg_weight", 0.5),
               "seed": int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)}
        w.stdin.write(json.dumps(req) + "\n")
        w.stdin.flush()
        rep = json.loads(w.stdout.readline() or "{}")
        if not rep.get("ok"):
            raise RuntimeError(f"Chatterbox failed: {rep.get('error', 'worker died')}")
        a = read_wav(Path(out))
        os.unlink(out)
        sr = int(rep["sr"])
        if sr != SR:
            a = np.interp(np.linspace(0, len(a), int(len(a) * SR / sr), endpoint=False), np.arange(len(a)), a).astype(np.float32)
        return a
    raise ValueError(f"unknown TTS backend {kind!r}")



def _trim(a: np.ndarray, thr: float = 0.004) -> np.ndarray:
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    lo = max(0, idx[0] - int(0.03 * SR))
    hi = min(len(a), idx[-1] + int(0.08 * SR))
    return a[lo:hi]


def write_wav(path: Path, a: np.ndarray) -> None:
    pcm = (np.clip(a, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767.0


def engine_for(lang: str, override: str | None = None) -> dict:
    v = voices()[lang]
    if override:
        v = dict(v, backend=override)
    return v


def say(text: str, lang: str, override: str | None = None) -> list[Clip]:
    """Synthesise ``text`` sentence by sentence; return cached clips."""
    engine = engine_for(lang, override)
    if engine["backend"] == "chatterbox":
        # key the cache on the reference recording's content, not just its name
        engine = dict(engine, ref_sha=hashlib.sha256(_ref_path(engine).read_bytes()).hexdigest()[:16])
    clips = []
    for sent in sentences(text):
        spoken_text = lexicon.spoken(sent, lang)
        key = hashlib.sha256(json.dumps([engine, spoken_text], sort_keys=True).encode()).hexdigest()[:24]
        d = CACHE / "tts" / lang
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{key}.wav"
        if not path.exists():
            a = _trim(_synth(engine, spoken_text, lang)) if engine["backend"] != "silence" else _synth(engine, spoken_text, lang)
            # gentle loudness normalisation (peak -1 dBFS, RMS towards -20 dBFS)
            peak = float(np.max(np.abs(a))) or 1.0
            rms = float(np.sqrt(np.mean(a ** 2))) or 1e-6
            g = min(0.89 / peak, 0.1 / rms)
            write_wav(path, (a * g).astype(np.float32))
        n = wave.open(str(path), "rb")
        secs = n.getnframes() / n.getframerate()
        n.close()
        clips.append(Clip(text=sent, spoken=spoken_text, path=path, seconds=secs))
    return clips


def total_seconds(clips: list[Clip]) -> float:
    return sum(c.seconds for c in clips) + GAP_S * max(0, len(clips) - 1)
