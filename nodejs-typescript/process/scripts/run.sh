#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."
: "${PZ_TUNNEL:=nodejs-typescript-process.portzero.local:80}"
export PZ_TUNNEL

node app.ts
