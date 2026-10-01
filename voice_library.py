"""Where Voice Studio keeps its files, and the saved-voice library.

data/
  voices/<slug>/reference.wav   voice.json      saved voices (cloned, uploaded or designed)
  recordings/<YYYY-MM-DD>/<HHMMSS>_<kind>.wav   every mic take / upload used for cloning
  exports/<YYYY-MM-DD>/<HHMMSS>_<voice>.wav     generated audio, with a .json of the script + settings
  previews/<speaker>.wav                         one sample per preset voice, generated once and reused

Set VOICE_STUDIO_DATA to keep the data somewhere else.
"""
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("VOICE_STUDIO_DATA", PROJECT_DIR / "data"))
VOICES_DIR = DATA_DIR / "voices"
RECORDINGS_DIR = DATA_DIR / "recordings"
EXPORTS_DIR = DATA_DIR / "exports"
PREVIEWS_DIR = DATA_DIR / "previews"

# The passage users read when recording; used as the reference transcript for Qwen cloning
SAMPLE_PASSAGE = (
    "The quick brown fox jumps over the lazy dog. I usually start my morning with a cup of coffee, "
    "check my messages, and then plan out the rest of the day. Honestly, the best part of the week "
    "is Friday evening, when everything finally slows down."
)


def ensure_dirs():
    for d in (VOICES_DIR, RECORDINGS_DIR, EXPORTS_DIR, PREVIEWS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "voice"


def _stamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H%M%S")


def normalize(audio, sr, peak=0.9, trim=False):
    """Mono float32 scaled to `peak` (None keeps the level); optionally trim leading/trailing silence."""
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    top = np.abs(audio).max() if audio.size else 0.0
    if top < 1e-4:
        return audio
    if trim:
        loud = np.flatnonzero(np.abs(audio) > top * 0.05)
        pad = int(sr * 0.15)
        audio = audio[max(loud[0] - pad, 0):loud[-1] + pad]
    return audio * (peak / top) if peak else audio


def to_wav(src, dst):
    """Save any audio file (wav/flac/mp3/ogg, or m4a/aac via afconvert) to dst as a trimmed, normalized mono WAV."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        audio, sr = sf.read(src, always_2d=False)
    except Exception:
        converted = temp_wav()
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", str(src), converted], check=True)
        audio, sr = sf.read(converted, always_2d=False)
        os.remove(converted)
    sf.write(dst, normalize(audio, sr, trim=True), sr)
    return dst


def duration(path):
    return sf.info(str(path)).duration


def archive_recording(src, kind="mic"):
    """Keep a copy of a mic take or upload under recordings/<date>/ and return its path."""
    day, time = _stamp()
    return to_wav(src, RECORDINGS_DIR / day / f"{time}_{kind}.wav")


def new_export_path(voice_label):
    day, time = _stamp()
    path = EXPORTS_DIR / day / f"{time}_{slugify(voice_label)}.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_export_info(wav_path, info):
    Path(wav_path).with_suffix(".json").write_text(json.dumps(info, indent=2))


def list_exports():
    """Every export, newest first, with the script and settings saved next to it."""
    exports = []
    for wav in EXPORTS_DIR.glob("*/*.wav"):
        info_path = wav.with_suffix(".json")
        info = json.loads(info_path.read_text()) if info_path.exists() else {}
        exports.append({
            "path": str(wav),
            "created": info.get("created") or datetime.fromtimestamp(wav.stat().st_mtime).isoformat(timespec="seconds"),
            "voice": info.get("voice", ""),
            "engine": (info.get("settings") or {}).get("engine", ""),
            "duration": info.get("duration") or round(duration(wav), 1),
            "text": info.get("text", ""),
            "settings": info.get("settings") or {},
        })
    return sorted(exports, key=lambda e: e["created"], reverse=True)


def delete_export(path):
    """Delete an export's audio and its .json; remove the date folder once it's empty."""
    wav = Path(path).resolve()
    if wav.parent.parent != EXPORTS_DIR.resolve() or wav.suffix != ".wav":
        raise ValueError("Not an export file.")
    wav.unlink(missing_ok=True)
    wav.with_suffix(".json").unlink(missing_ok=True)
    if not any(wav.parent.iterdir()):
        wav.parent.rmdir()


def delete_all_exports():
    """Delete every export (audio + .json) and the emptied date folders. Returns how many takes were removed."""
    takes = list(EXPORTS_DIR.glob("*/*.wav"))
    for wav in takes:
        delete_export(wav)
    return len(takes)


def save_voice(name, audio_path, transcript, source):
    """Add a voice to the library. Overwrites an existing voice with the same name."""
    name = name.strip()
    if not name:
        raise ValueError("Give the voice a name.")
    folder = VOICES_DIR / slugify(name)
    folder.mkdir(parents=True, exist_ok=True)
    ref = to_wav(audio_path, folder / "reference.wav")
    meta = {
        "name": name,
        "transcript": transcript or "",
        "source": source,
        "duration": round(duration(ref), 1),
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    (folder / "voice.json").write_text(json.dumps(meta, indent=2))
    return folder.name


def list_voices():
    """[(label, slug)] for dropdowns, newest first."""
    voices = []
    for meta_path in VOICES_DIR.glob("*/voice.json"):
        meta = json.loads(meta_path.read_text())
        voices.append((meta["created"], f"{meta['name']} ({meta['source']}, {meta['duration']}s)", meta_path.parent.name))
    return [(label, slug) for _, label, slug in sorted(voices, reverse=True)]


def get_voice(slug):
    """(reference_wav_path, metadata) for a saved voice."""
    folder = VOICES_DIR / slug
    return str(folder / "reference.wav"), json.loads((folder / "voice.json").read_text())


def temp_wav():
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    return path
