#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."
: "${PZ_TUNNEL:=rust-process.portzero.local:80}"
export PZ_TUNNEL

cargo run --quiet
