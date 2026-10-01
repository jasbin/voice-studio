#!/bin/bash
# ./run.sh          this Mac only (http://127.0.0.1:7860)
# ./run.sh --lan    also reachable from phones/computers on the same Wi-Fi
cd "$(dirname "$0")"
if [ "$1" = "--lan" ]; then
  export VS_HOST=0.0.0.0
  if [ -f certs/cert.pem ] && [ -f certs/key.pem ]; then
    export VS_SSL_CERT=certs/cert.pem VS_SSL_KEY=certs/key.pem; scheme=https
  else
    scheme=http
  fi
  ip=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
  echo "==> On your phone (same Wi-Fi), open: $scheme://${ip:-<this-mac-ip>}:7860"
  [ -z "$VS_AUTH" ] && echo "    Tip: VS_AUTH=user:password ./run.sh --lan adds a login."
fi
exec .venv-qwen/bin/python app.py
