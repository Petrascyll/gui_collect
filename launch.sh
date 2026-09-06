#!/usr/bin/env bash

set -euo pipefail

script=$0
if resolved=$(readlink -f "$script" 2>/dev/null); then
    script=$resolved
fi
cd -- "$(dirname -- "$script")"

if [ -x .venv/bin/python ]; then
    PYTHON=.venv/bin/python
else
    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            PYTHON=$candidate
            break
        fi
    done
fi

if [ -z "${PYTHON:-}" ]; then
    echo "Python not found!" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import sys; raise SystemExit(sys.version_info < (3, 9))'; then
    echo "You must have at least Python 3.9 installed! (found $("$PYTHON" --version 2>&1))" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
    echo "Missing dependency: tkinter" >&2
    echo "Most distributions ship it separately, e.g. pacman -S tk, apt install python3-tk" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import PIL' >/dev/null 2>&1; then
    echo "Missing dependency: Pillow" >&2
    echo "Install it with your package manager (e.g. pacman -S python-pillow)," >&2
    echo "or into a virtualenv this script will then pick up automatically:" >&2
    echo "    $PYTHON -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi

exec "$PYTHON" collect.py
