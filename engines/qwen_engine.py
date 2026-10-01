"""Qwen3-TTS: preset voices (CustomVoice), voice design (VoiceDesign) and voice cloning (Base).

Models load on first use and stay cached (at most MAX_LOADED at once to bound memory).
Run `python -m engines.qwen_engine --selftest` from the project root to check it works without the UI.
"""
import platform
import subprocess
import threading
from collections import OrderedDict
from pathlib import Path

import torch
from qwen_tts import Qwen3TTSModel

LANGUAGE = "English"
MAX_LOADED = 2

REPOS = {
    ("custom", "1.7B"): "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    ("custom", "0.6B"): "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    ("design", "1.7B"): "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    ("base", "1.7B"): "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    ("base", "0.6B"): "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
}

# (id, name, description) — native English speakers first, the rest speak English with an accent
SPEAKERS = [
    ("aiden", "Aiden", "Sunny American male, clear midrange"),
    ("ryan", "Ryan", "Dynamic male with strong rhythmic drive"),
    ("serena", "Serena", "Warm, gentle young female (Chinese accent)"),
    ("vivian", "Vivian", "Bright, slightly edgy young female (Chinese accent)"),
    ("sohee", "Sohee", "Warm, emotive female (Korean accent)"),
    ("ono_anna", "Ono Anna", "Playful, light female (Japanese accent)"),
    ("uncle_fu", "Uncle Fu", "Seasoned, low mellow male (Chinese accent)"),
    ("dylan", "Dylan", "Youthful, clear male (Beijing accent)"),
    ("eric", "Eric", "Lively, slightly husky male (Sichuan accent)"),
]

STYLE_PRESETS = {
    "Tech explainer": "Clear, confident, professional narrator. Moderate pace, warm but authoritative, "
                      "like a well-produced tech explainer video. Crisp articulation of technical terms.",
    "Documentary narrator": "Calm, measured documentary narration. Steady pace, rich and composed, "
                            "with thoughtful pauses.",
    "Product launch": "Energetic, upbeat presenter at a product launch. Lively pace, excited but polished.",
    "Podcast host": "Relaxed, conversational podcast host. Friendly and natural, like talking to a friend.",
    "Tutorial teacher": "Patient, friendly teacher walking through a tutorial step by step. "
                        "Slightly slower pace, very clear.",
}

DESIGN_EXAMPLES = [
    "A clear, confident female narrator in her 30s with a neutral American accent. Calm, professional "
    "studio delivery at a moderate pace, like a tech documentary.",
    "A deep, warm male voice in his 40s with a slight British accent. Authoritative and smooth, "
    "like a premium tech keynote narrator.",
    "A friendly, energetic young female YouTuber with an American accent. Upbeat, fast-paced and expressive.",
    "A calm, soft-spoken male voice with a neutral accent, relaxed and reassuring, like a meditation "
    "app or late-night podcast.",
]

def _cpu_name():
    try:
        if platform.system() == "Darwin":
            return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
                                  text=True).stdout.strip()
        if platform.system() == "Linux":
            for line in open("/proc/cpuinfo"):
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
        return platform.processor()
    except Exception:
        return ""


def available_devices():
    """Devices this machine can run on, fastest first."""
    devices = []
    if torch.cuda.is_available():  # NVIDIA (CUDA) and AMD Radeon (ROCm) both show up as "cuda"
        devices.append("cuda")
    if torch.backends.mps.is_available():
        devices.append("mps")
    return devices + ["cpu"]


def device_label(device):
    """Human-readable name with the detected hardware, e.g. 'NVIDIA GPU · RTX 4090'."""
    if device == "cuda" and torch.cuda.is_available():
        vendor = "AMD Radeon GPU (ROCm)" if torch.version.hip else "NVIDIA GPU (CUDA)"
        return f"{vendor} · {torch.cuda.get_device_name(0)}"
    if device == "mps":
        chip = _cpu_name()
        if platform.machine() == "arm64":
            return f"Apple Silicon GPU · {chip}" if chip else "Apple Silicon GPU"
        return "Mac GPU (Metal)"  # Intel Macs: AMD Radeon / Intel graphics through Metal
    if device == "cpu":
        return f"CPU · {_cpu_name()}" if _cpu_name() else "CPU"
    return device


_device = available_devices()[0]
_models = OrderedDict()   # (kind, size) -> model, least recently used first
_prompts = {}             # (size, ref_path, mtime, transcript) -> voice clone prompt
_lock = threading.RLock()


def _free_memory():
    if _device == "mps":
        torch.mps.empty_cache()
    elif _device == "cuda":
        torch.cuda.empty_cache()


def get_device():
    return _device


def set_device(device):
    """Switch devices. Loaded models are dropped and reload on the new device when next used."""
    global _device
    if device not in available_devices():
        raise ValueError(f"{device_label(device)} isn't available on this machine.")
    with _lock:
        if device != _device:
            _models.clear()
            _prompts.clear()
            _free_memory()
            _device = device


def _get_model(kind, size):
    key = (kind, size)
    with _lock:
        if key in _models:
            _models.move_to_end(key)
            return _models[key]
        while len(_models) >= MAX_LOADED:
            old_key, _ = _models.popitem(last=False)
            if old_key[0] == "base":
                for k in [k for k in _prompts if k[0] == old_key[1]]:
                    del _prompts[k]
            _free_memory()
        print(f"[qwen] loading {REPOS[key]} on {_device}...", flush=True)
        dtype = torch.float32 if _device == "cpu" else torch.bfloat16
        model = Qwen3TTSModel.from_pretrained(REPOS[key], device_map=_device, dtype=dtype,
                                              attn_implementation="sdpa")
        _models[key] = model
        return model


def preset_voice(text, speaker, style, size="1.7B"):
    """Returns (waveform, sample_rate). The 0.6B model ignores `style`."""
    with _lock:
        model = _get_model("custom", size)
        wavs, sr = model.generate_custom_voice(text=text, speaker=speaker, language=LANGUAGE,
                                               instruct=style or None)
    return wavs[0], sr


def design_voice(text, description):
    with _lock:
        model = _get_model("design", "1.7B")
        wavs, sr = model.generate_voice_design(text=text, instruct=description, language=LANGUAGE)
    return wavs[0], sr


def clone_voice(text, ref_path, transcript=None, size="0.6B"):
    """Without a transcript, only the speaker embedding is used (faster to prepare, less faithful)."""
    transcript = (transcript or "").strip() or None
    with _lock:
        model = _get_model("base", size)
        key = (size, str(ref_path), Path(ref_path).stat().st_mtime, transcript)
        if key not in _prompts:
            _prompts[key] = model.create_voice_clone_prompt(ref_audio=str(ref_path), ref_text=transcript,
                                                            x_vector_only_mode=transcript is None)
        wavs, sr = model.generate_voice_clone(text=text, language=LANGUAGE, voice_clone_prompt=_prompts[key])
    return wavs[0], sr


if __name__ == "__main__":
    import argparse
    import time

    import soundfile as sf

    from voice_library import temp_wav

    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--mode", choices=["clone", "preset", "design"], default="preset")
    parser.add_argument("--ref", help="clone mode: reference recording")
    parser.add_argument("--ref-text", help="clone mode: transcript of the reference")
    args = parser.parse_args()

    start = time.time()
    text = "This is a quick self test of the Voice Studio Qwen engine."
    if args.mode == "clone":
        wav, sr = clone_voice(text, args.ref, args.ref_text, "0.6B")
    elif args.mode == "preset":
        wav, sr = preset_voice(text, "aiden", STYLE_PRESETS["Tech explainer"])
    else:
        wav, sr = design_voice(text, DESIGN_EXAMPLES[0])
    out = temp_wav()
    sf.write(out, wav, sr)
    print(f"OK {args.mode}: {len(wav) / sr:.1f}s of audio at {sr} Hz in {time.time() - start:.1f}s -> {out}")
