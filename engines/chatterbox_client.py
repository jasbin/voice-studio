"""Talks to workers/chatterbox_worker.py, which runs in .venv-chatterbox and keeps Chatterbox models loaded."""
import atexit
import json
import os
import subprocess
import threading
from pathlib import Path

import soundfile as sf

PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKER_PYTHON = os.environ.get("CHATTERBOX_PYTHON", str(PROJECT_DIR / ".venv-chatterbox" / "bin" / "python"))
WORKER_SCRIPT = PROJECT_DIR / "workers" / "chatterbox_worker.py"
PREFIX = "@@RESULT "

_proc = None
_lock = threading.Lock()


def _start():
    global _proc
    if not Path(WORKER_PYTHON).exists():
        raise RuntimeError(f"Chatterbox environment not found at {WORKER_PYTHON}. Run ./setup.sh first.")
    # stderr is inherited, so model loading logs show up in the terminal running the app
    _proc = subprocess.Popen([WORKER_PYTHON, str(WORKER_SCRIPT)], cwd=PROJECT_DIR, text=True, bufsize=1,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def _request(payload):
    with _lock:
        if _proc is None or _proc.poll() is not None:
            _start()
        _proc.stdin.write(json.dumps(payload) + "\n")
        _proc.stdin.flush()
        for line in _proc.stdout:
            if line.startswith(PREFIX):
                result = json.loads(line[len(PREFIX):])
                if not result.get("ok"):
                    raise RuntimeError(result.get("error", "Chatterbox worker failed"))
                return result
        raise RuntimeError("Chatterbox worker exited unexpectedly; see the terminal for details.")


def generate(text, ref_path, model="turbo", exaggeration=0.5, cfg_weight=0.5, device=None):
    """Returns (waveform, sample_rate). `device` is "mps", "cuda" or "cpu"; None keeps the worker's current one."""
    from voice_library import temp_wav

    out = temp_wav()
    try:
        _request({"cmd": "generate", "model": model, "text": text, "ref": str(ref_path),
                  "exaggeration": exaggeration, "cfg_weight": cfg_weight, "out": out, "device": device})
        wav, sr = sf.read(out, dtype="float32")
    finally:
        os.remove(out)
    return wav, sr


@atexit.register
def shutdown():
    if _proc is not None and _proc.poll() is None:
        _proc.stdin.close()
        try:
            _proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _proc.kill()
