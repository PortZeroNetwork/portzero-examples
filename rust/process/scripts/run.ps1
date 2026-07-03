$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")
if (-not $env:PZ_TUNNEL) {
    $env:PZ_TUNNEL = "rust-process.portzero.local:80"
}

cargo run --quiet
