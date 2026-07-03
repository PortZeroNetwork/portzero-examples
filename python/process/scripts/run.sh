#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."
: "${PZ_TUNNEL:=python-process.portzero.local:80}"
export PZ_TUNNEL

python3 app.py
