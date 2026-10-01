# Voice Studio

A local text-to-speech app for English narration, built on Qwen3-TTS and Chatterbox. Everything runs locally on your GPU or CPU.

- **Preset Voices:** 9 Qwen voices with instant previews and style direction (Tech explainer, Documentary, Podcast…)
- **Design a Voice:** describe a voice in words; save the ones you like
- **Clone a Voice:** record in the browser or upload a clip, then generate with Qwen or Chatterbox (Turbo / Original)
- **Library:** play, inspect (script + settings) and delete every take you've generated
- **Compute:** choose the device from the header. Apple Silicon (MPS), NVIDIA (CUDA) and AMD Radeon (ROCm) GPUs are detected automatically, with CPU as a fallback

Only clone voices you have permission to use.

## Setup (once)

Needs Python 3.12, plus Python 3.14 for Chatterbox if you have it (3.12 is used otherwise). Built and tested on macOS.

```bash
./setup.sh
```

This creates two environments, because Qwen and Chatterbox need different `transformers` versions:
- `.venv-qwen` (Python 3.12) runs the UI and Qwen.
- `.venv-chatterbox` (Python 3.14) runs Chatterbox as a background worker.

To use a specific Python, pass `QWEN_PY=/path/to/python3.12` or `CHATTERBOX_PY=/path/to/python3.14`.

## Run

```bash
./run.sh
```

Then open http://127.0.0.1:7860. Models download the first time each is used (about 1–4 GB each) into `~/.cache/huggingface/hub/`.

## Use it from your phone

```bash
VS_AUTH=user:password ./run.sh --lan
```

This makes the app reachable from other devices on the same Wi-Fi, and prints the address to open. `VS_AUTH` adds a login; always set it with `--lan`, because without it anyone on the network can use the app and your saved voices.

Browsers only allow the microphone on HTTPS pages (or on localhost). To record from a phone, put a certificate in `certs/` and `run.sh` will serve HTTPS automatically:

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=voice-studio" \
  -keyout certs/key.pem -out certs/cert.pem
```

The browser will warn that the certificate is self-signed, which is expected for one you made yourself. `certs/` is git-ignored.

## Where files go

```
data/
  voices/<name>/reference.wav, voice.json    saved voices (My Voices)
  recordings/<date>/<time>_mic.wav            every recording or upload used for cloning
  exports/<date>/<time>_<voice>.wav, .json    generated audio, plus its script and settings
  previews/<speaker>.wav                      preset voice previews (generated once)
```

Set `VOICE_STUDIO_DATA=/some/path` to store data elsewhere.

`data/` is git-ignored and never leaves your machine. Keep it that way: `voices/` and `recordings/` hold real voice samples that could be used to clone someone's voice.

## Tips for studio-quality narration

- Use the 1.7B models. The 0.6B preset model ignores style direction.
- Long scripts are fine: they're generated paragraph by paragraph and joined with natural pauses. Separate paragraphs with a blank line.
- Spell out things as they should be said: "G P U", "version two point one".
- For cloning, record 10–20 s in a quiet room and read the on-screen passage word for word (Qwen uses it as the transcript).
- Uploads can be WAV, FLAC, MP3 or OGG. M4A/AAC (such as iPhone Voice Memos) is converted with macOS's `afconvert`, so on Linux or Windows convert those first.
- Chatterbox needs a reference clip longer than 5 s. Turbo supports `[laugh]`, `[chuckle]` and `[cough]` tags.

## Project layout

| File | Purpose |
|---|---|
| `app.py` | Gradio UI and handlers |
| `engines/qwen_engine.py` | Qwen models (preset, design, clone), cached in memory |
| `engines/chatterbox_client.py` | Starts and talks to the Chatterbox worker |
| `workers/chatterbox_worker.py` | Runs in `.venv-chatterbox`; one JSON request per line |
| `text_utils.py` | Splits scripts into chunks, joins audio with pauses |
| `voice_library.py` | Data folders, saved voices, exports, audio normalization |
| `ui_theme.py` | Theme, fonts and CSS (Apple Liquid Glass style) |

Gradio is pinned to 6.17.3 in `requirements-qwen.txt` because `ui_theme.py` hooks into Gradio's page structure. Check the look before upgrading it.

Test without the UI: `.venv-qwen/bin/python -m engines.qwen_engine --selftest --mode preset`
