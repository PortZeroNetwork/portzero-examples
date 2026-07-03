set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]

default:
    @just --list

[unix]
test *ARGS:
    @if ! command -v uv >/dev/null 2>&1; then printf '%s\n' 'Missing uv. Install it, then rerun `just test`.' 'See https://docs.astral.sh/uv/getting-started/installation/' 'macOS: brew install uv' 'Linux: curl -LsSf https://astral.sh/uv/install.sh | sh'; exit 127; fi
    @PYTHONDONTWRITEBYTECODE=1 uv run scripts/test_examples.py {{ARGS}}

[windows]
test *ARGS:
    @if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { Write-Error "Missing uv. Install it, then rerun ``just test``. See https://docs.astral.sh/uv/getting-started/installation/ . Windows: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""; exit 127 }
    @$env:PYTHONDONTWRITEBYTECODE = "1"; uv run scripts/test_examples.py {{ARGS}}

[unix]
list-examples:
    @PYTHONDONTWRITEBYTECODE=1 uv run scripts/test_examples.py --list

[windows]
list-examples:
    @$env:PYTHONDONTWRITEBYTECODE = "1"; uv run scripts/test_examples.py --list
