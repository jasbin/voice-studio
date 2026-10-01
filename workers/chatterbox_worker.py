"""Chatterbox TTS worker. Runs in .venv-chatterbox (Chatterbox needs a different transformers than Qwen).

Protocol: one JSON request per line on stdin; one line "@@RESULT <json>" per request on stdout.
Everything else the libraries print is redirected to stderr so it can't corrupt the protocol.

  {"cmd": "ping"}
  {"cmd": "generate", "model": "turbo"|"original", "text": ..., "ref": wav path,
   "exaggeration": 0.5, "cfg_weight": 0.5, "out": wav path, "device": "mps"|"cuda"|"cpu"}
"""
import json
import os
import sys
import traceback

protocol_out = sys.stdout
sys.stdout = sys.stderr

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402

MIN_REF_SECONDS = 5.0
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
models = {}
prepared = {}  # model name -> key of the reference its conditionals were built from


def reply(**payload):
    protocol_out.write("@@RESULT " + json.dumps(payload) + "\n")
    protocol_out.flush()


def get_model(name):
    if name not in models:
        if name == "turbo":
            from chatterbox.tts_turbo import ChatterboxTurboTTS
            model = ChatterboxTurboTTS.from_pretrained(device=device)
            # Turbo's loudness normalization returns float64, which MPS can't handle; cast back to float32
            norm = model.norm_loudness
            model.norm_loudness = lambda wav, sr, **kw: norm(wav, sr, **kw).astype(np.float32)
        else:
            from chatterbox.tts import ChatterboxTTS
            model = ChatterboxTTS.from_pretrained(device=device)
        models[name] = model
    return models[name]


def use_device(requested):
    """Switch devices, dropping loaded models so they reload on the new one."""
    global device
    if requested and requested != device:
        models.clear()
        prepared.clear()
        if device == "mps":
            torch.mps.empty_cache()
        elif device == "cuda":
            torch.cuda.empty_cache()
        device = requested


def generate(req):
    use_device(req.get("device"))
    name = req["model"]
    model = get_model(name)
    ref = req["ref"]
    if sf.info(ref).duration <= MIN_REF_SECONDS:
        raise ValueError(f"Chatterbox needs a reference recording longer than {MIN_REF_SECONDS:.0f} seconds.")

    # Build the voice conditionals once per reference and reuse them for every chunk of a script
    key = (ref, os.path.getmtime(ref), req.get("exaggeration") if name == "original" else None)
    if prepared.get(name) != key:
        if name == "turbo":
            model.prepare_conditionals(ref)
        else:
            model.prepare_conditionals(ref, exaggeration=req.get("exaggeration", 0.5))
        prepared[name] = key

    if name == "turbo":
        wav = model.generate(req["text"])
    else:
        wav = model.generate(req["text"], exaggeration=req.get("exaggeration", 0.5),
                             cfg_weight=req.get("cfg_weight", 0.5))
    sf.write(req["out"], wav.squeeze(0).cpu().numpy(), model.sr)
    return model.sr


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            if req["cmd"] == "ping":
                reply(ok=True, device=device)
            elif req["cmd"] == "generate":
                reply(ok=True, sr=generate(req))
            else:
                reply(ok=False, error=f"unknown command {req['cmd']!r}")
        except Exception as e:
            traceback.print_exc()
            reply(ok=False, error=f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
