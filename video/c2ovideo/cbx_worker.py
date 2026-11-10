"""Chatterbox worker: one long-lived process, one JSON request per line.

C2O_CBX_MODEL picks the model: "multilingual" (default; Chatterbox Multilingual, any
language) or "english" (the original English-only Chatterbox, which keeps an English
speaker's own accent more faithfully; it ignores the language id).

Runs under its own Python (the ``python`` key of the chatterbox voice in voices.yaml),
because Chatterbox pins torch and transformers versions the rest of the pipeline does
not need. Request: {"text", "lang", "ref", "out", "exaggeration", "cfg_weight", "seed"};
reply: {"ok": true, "seconds": ...} or {"ok": false, "error": ...}.

Chatterbox Multilingual (Resemble AI) is MIT-licensed; its output carries Resemble's
inaudible Perth watermark marking the audio as synthetic.
"""
import gc
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")


def _devices(torch) -> list:
    """C2O_CBX_DEVICE if set, else Apple GPU (MPS), then CUDA, then CPU."""
    forced = os.environ.get("C2O_CBX_DEVICE")
    if forced:
        return [forced]
    out = []
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        out.append("mps")
    if torch.cuda.is_available():
        out.append("cuda")
    return out + ["cpu"]


def main() -> None:
    import torch
    import torchaudio as ta
    english = os.environ.get("C2O_CBX_MODEL", "multilingual") == "english"
    if english:
        from chatterbox.tts import ChatterboxTTS as Model
    else:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS as Model

    torch.set_num_threads(max(1, torch.get_num_threads()))
    model = None
    for device in _devices(torch):
        try:
            model = Model.from_pretrained(device=device)
            break
        except Exception as e:  # e.g. an MPS op missing on an older macOS: fall back
            print(f"chatterbox: {device} unavailable ({type(e).__name__}: {e})", file=sys.stderr, flush=True)
    if model is None:
        raise SystemExit("chatterbox: no usable device")
    print(json.dumps({"ready": True}), flush=True)
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            torch.manual_seed(int(r.get("seed", 0)))
            with torch.inference_mode():
                kw = dict(audio_prompt_path=r["ref"], exaggeration=float(r.get("exaggeration", 0.5)),
                          cfg_weight=float(r.get("cfg_weight", 0.5)))
                if not english:
                    kw["language_id"] = r["lang"]
                wav = model.generate(r["text"], **kw)
            ta.save(r["out"], wav, model.sr, encoding="PCM_S", bits_per_sample=16)
            gc.collect()
            print(json.dumps({"ok": True, "seconds": wav.shape[-1] / model.sr, "sr": model.sr}), flush=True)
        except Exception as e:  # report and keep serving
            print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}), flush=True)


if __name__ == "__main__":
    main()
