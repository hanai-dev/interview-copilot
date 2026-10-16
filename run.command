#!/bin/sh
# Interview Copilot for macOS and Linux (on Windows use run.bat).
# macOS: double-click this file. Linux: run ./run.command in a terminal.
cd "$(dirname "$0")" || exit 1

fail() {
  echo
  echo " Setup failed. Scroll up for the error."
  echo " On Debian/Ubuntu you may need: sudo apt install python3-venv"
  echo " Then delete the .venv folder and run this again."
  exit 1
}

# --- find Python 3.10+ (specific versions first: on a Mac, plain python3 may be the old 3.9) ---
PY=""
for c in python3.15 python3.14 python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
    PY="$c"
    break
  fi
done
if [ -z "$PY" ]; then
  echo
  echo " Python 3.10 or newer was not found. Install Python 3.12 from https://www.python.org/downloads/"
  echo " (Linux: sudo apt install python3 python3-venv), then run this again."
  exit 1
fi

# --- first run: create a private environment and install packages ---
if [ ! -x .venv/bin/python ]; then
  echo "Setting up for the first time. This takes a minute or two..."
  "$PY" -m venv .venv || fail
fi
if [ ! -f .venv/installed.flag ]; then
  .venv/bin/python -m pip install --upgrade pip -q
  .venv/bin/python -m pip install -r requirements.txt -q || fail
  echo ok > .venv/installed.flag
fi

# --- start the app (your browser opens automatically) ---
# python.org's Mac Python has no root certificates, so HTTPS to Deepgram/Claude/OpenAI fails; use the Mac's own
[ "$(uname)" = Darwin ] && [ -z "$SSL_CERT_FILE" ] && [ -f /etc/ssl/cert.pem ] && export SSL_CERT_FILE=/etc/ssl/cert.pem
exec .venv/bin/python -m app.server
