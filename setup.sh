#!/bin/bash
# Creates the two Python environments Voice Studio needs.
# Qwen and Chatterbox require conflicting transformers versions, so each gets its own venv.
set -e
cd "$(dirname "$0")"

QWEN_PY="${QWEN_PY:-$(command -v python3.12)}"
CHATTERBOX_PY="${CHATTERBOX_PY:-$(command -v python3.14 || command -v python3.12)}"

echo "==> Qwen environment ($QWEN_PY)"
"$QWEN_PY" -m venv .venv-qwen
.venv-qwen/bin/python -m pip install -q -U pip
.venv-qwen/bin/python -m pip install -q -r requirements-qwen.txt

echo "==> Chatterbox environment ($CHATTERBOX_PY)"
"$CHATTERBOX_PY" -m venv .venv-chatterbox
.venv-chatterbox/bin/python -m pip install -q -U pip
.venv-chatterbox/bin/python -m pip install -q -r requirements-chatterbox.txt

echo "==> Done. Start the app with ./run.sh"
