$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")
if (-not $env:PZ_TUNNEL) {
    $env:PZ_TUNNEL = "python-process.portzero.local:80"
}

py -3 app.py
