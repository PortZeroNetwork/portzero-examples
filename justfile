set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]

default:
    @just --list

[unix]
test *ARGS:
    @if ! command -v python3 >/dev/null 2>&1; then printf '%s\n' 'Missing Python 3. Install it, then rerun `just test`.' 'macOS: brew install python' 'Linux: use your distro package manager, for example sudo apt install python3'; exit 127; fi
    @PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_examples.py {{ARGS}}

[windows]
test *ARGS:
    @if (-not (Get-Command py -ErrorAction SilentlyContinue)) { Write-Error "Missing Python 3. Install it, then rerun ``just test``. Windows: winget install Python.Python.3.12"; exit 127 }
    @$env:PYTHONDONTWRITEBYTECODE = "1"; py -3 scripts/test_examples.py {{ARGS}}

[unix]
list-examples:
    @PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_examples.py --list

[windows]
list-examples:
    @$env:PYTHONDONTWRITEBYTECODE = "1"; py -3 scripts/test_examples.py --list
