#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import queue
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LISTENER_PREFIX = "PORTZERO_EXAMPLE_LISTENING "
VARIANTS = {"process", "docker"}


@dataclass(frozen=True)
class Example:
    language: str
    variant: str
    name: str
    path: Path
    kind: str


@dataclass
class Result:
    name: str
    ok: bool
    detail: str = ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover and test all PortZero examples.")
    parser.add_argument("--list", action="store_true", help="list discovered examples without running them")
    parser.add_argument(
        "--skip-portzero-local",
        action="store_true",
        help="skip the portzero-local prerequisite check and run direct local smoke tests only",
    )
    args = parser.parse_args()

    examples = discover_examples(ROOT)
    if not examples:
        print("No examples found.")
        return 1

    if args.list:
        for example in examples:
            print(f"{example.name}: {example.kind}/{example.variant} ({example.path.relative_to(ROOT)})")
        return 0

    failures: list[str] = []
    if not args.skip_portzero_local:
        ok, detail = check_portzero_local()
        if ok:
            print(f"portzero-local: {detail}")
        else:
            failures.append(detail)

    failures.extend(check_example_prerequisites(examples))

    runners = {"python": test_scripted_http_example, "rust": test_scripted_http_example}
    results: list[Result] = []

    for example in examples:
        runner = runners.get(example.kind)
        if runner is None:
            results.append(Result(example.name, False, f"no runner for {example.kind} examples"))
            continue
        results.append(runner(example))

    for result in results:
        status = "ok" if result.ok else "FAILED"
        suffix = f" - {result.detail}" if result.detail else ""
        print(f"{status}: {result.name}{suffix}")
        if not result.ok:
            failures.append(f"{result.name}: {result.detail}")

    if failures:
        print()
        print("Missing prerequisites or failed examples:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    return 0


def discover_examples(root: Path) -> list[Example]:
    examples: list[Example] = []
    for language_path in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not language_path.is_dir() or language_path.name.startswith(".") or language_path.name in {"scripts", "target"}:
            continue
        for variant_path in sorted(language_path.iterdir(), key=lambda item: item.name.lower()):
            if not variant_path.is_dir() or variant_path.name not in VARIANTS:
                continue
            kind = detect_kind(variant_path)
            if kind is not None:
                name = f"{language_path.name}/{variant_path.name}"
                examples.append(Example(language_path.name, variant_path.name, name, variant_path, kind))
    return examples


def detect_kind(path: Path) -> str | None:
    if (path / "Cargo.toml").is_file():
        return "rust"
    if (path / "app.py").is_file():
        return "python"
    return None


def check_portzero_local() -> tuple[bool, str]:
    binary = shutil.which("portzero-local")
    if binary is None:
        return (
            False,
            "Missing portzero-local. Install PortZero Local through your PortZero release channel, "
            "then ensure `portzero-local` is on PATH.",
        )

    try:
        completed = subprocess.run(
            [binary, "--version"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=False,
        )
    except OSError as exc:
        return False, f"Could not execute portzero-local at {binary}: {exc}"
    except subprocess.TimeoutExpired:
        return False, "portzero-local --version timed out"

    version = completed.stdout.strip() or f"found at {binary}"
    if completed.returncode != 0:
        return False, f"portzero-local --version failed: {version}"
    return True, version


def check_example_prerequisites(examples: list[Example]) -> list[str]:
    failures: list[str] = []

    if any(example.kind == "rust" for example in examples) and shutil.which("cargo") is None:
        failures.append("Missing Cargo. Install Rust with rustup, then rerun `just test`: https://rustup.rs/")

    if any(example.kind == "python" for example in examples):
        if os.name == "nt":
            python = shutil.which("py")
            command = [python, "-3", "--version"] if python is not None else None
        else:
            python = shutil.which("python3")
            command = [python, "--version"] if python is not None else None

        if command is None:
            failures.append("Missing Python 3. Install Python 3, then rerun `just test`.")
        else:
            try:
                completed = subprocess.run(
                    command,
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=10,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                failures.append("Python 3 is installed but `python --version` timed out.")
            else:
                if completed.returncode != 0:
                    failures.append(f"Python 3 is installed but not available: {compact(completed.stdout)}")

    if any(example.variant == "docker" for example in examples):
        docker = shutil.which("docker")
        if docker is None:
            failures.append(
                "Missing Docker. Install Docker Desktop on macOS/Windows or Docker Engine on Linux, then rerun `just test`."
            )
        else:
            try:
                completed = subprocess.run(
                    [docker, "info"],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=20,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                failures.append("Docker is installed but `docker info` timed out. Start Docker, then rerun `just test`.")
            else:
                if completed.returncode != 0:
                    failures.append(f"Docker is installed but not available: {compact(completed.stdout)}")

    return failures


def test_scripted_http_example(example: Example) -> Result:
    tunnel = f"{example.language}-{example.variant}.portzero.local:80"
    env = os.environ.copy()
    env["PZ_TUNNEL"] = tunnel

    command = example_command(example)
    print(f"+ ({example.path.relative_to(ROOT)}) {' '.join(command)}")
    proc = start_example(command, example.path, env)

    try:
        fields = wait_for_listener(proc, timeout=180)
        error = validate_listener_fields(example, fields, tunnel)
        if error:
            return Result(example.name, False, error)

        body = http_get(fields["url"], timeout=10)
        expected = [f"Hello from the PortZero {example.language.title()}", f"PZ_TUNNEL={tunnel}"]
        missing = [text for text in expected if text not in body]
        if missing:
            return Result(example.name, False, f"HTTP response missing: {', '.join(missing)}")
        return Result(example.name, True)
    except Exception as exc:
        return Result(example.name, False, str(exc))
    finally:
        stop_process(proc)


def example_command(example: Example) -> list[str]:
    if os.name == "nt":
        return [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(example.path / "scripts" / "run.ps1"),
        ]
    return [str(example.path / "scripts" / "run.sh")]


def start_example(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen[str]:
    kwargs = {}
    if os.name != "nt":
        kwargs["start_new_session"] = True

    return subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        **kwargs,
    )


def wait_for_listener(proc: subprocess.Popen[str], timeout: int) -> dict[str, str]:
    assert proc.stdout is not None
    output: queue.Queue[str] = queue.Queue()
    reader = threading.Thread(target=read_lines, args=(proc.stdout, output), daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout
    lines: list[str] = []

    while time.monotonic() < deadline:
        if proc.poll() is not None:
            drain(output, lines)
            raise RuntimeError(f"example exited before printing listener line: {compact(''.join(lines))}")

        try:
            line = output.get(timeout=0.1)
        except queue.Empty:
            continue

        lines.append(line)
        if line.startswith(LISTENER_PREFIX):
            fields = parse_listener_line(line)
            port = int(fields["port"])
            wait_for_tcp("127.0.0.1", port, timeout=10)
            return fields

    raise TimeoutError(f"timed out waiting for listener line: {compact(''.join(lines))}")


def parse_listener_line(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for part in line.removeprefix(LISTENER_PREFIX).strip().split():
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        fields[key] = value
    return fields


def validate_listener_fields(example: Example, fields: dict[str, str], tunnel: str) -> str | None:
    required = {"language", "variant", "host", "port", "url", "tunnel", "tunnel_url"}
    missing = sorted(required - fields.keys())
    if missing:
        return f"listener line missing fields: {', '.join(missing)}"

    if fields["language"] != example.language:
        return f"listener language {fields['language']} did not match {example.language}"
    if fields["variant"] != example.variant:
        return f"listener variant {fields['variant']} did not match {example.variant}"
    if fields["host"] != "127.0.0.1":
        return f"listener host {fields['host']} did not match 127.0.0.1"
    if fields["tunnel"] != tunnel:
        return f"listener tunnel {fields['tunnel']} did not match {tunnel}"

    try:
        port = int(fields["port"])
    except ValueError:
        return f"listener port {fields['port']} was not numeric"

    expected_url = f"http://127.0.0.1:{port}/"
    expected_tunnel_url = f"http://{tunnel.split(':', 1)[0]}/"
    if fields["url"] != expected_url:
        return f"listener url {fields['url']} did not match {expected_url}"
    if fields["tunnel_url"] != expected_tunnel_url:
        return f"listener tunnel_url {fields['tunnel_url']} did not match {expected_tunnel_url}"

    return None


def read_lines(stream, output: queue.Queue[str]) -> None:
    for line in stream:
        output.put(line)


def drain(output: queue.Queue[str], lines: list[str]) -> None:
    while True:
        try:
            lines.append(output.get_nowait())
        except queue.Empty:
            return


def wait_for_tcp(host: str, port: int, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"timed out connecting to {host}:{port}")


def http_get(url: str, timeout: int) -> str:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"HTTP check failed for {url}: {exc}") from exc


def stop_process(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return

    if os.name == "nt":
        proc.terminate()
    else:
        os.killpg(proc.pid, signal.SIGTERM)

    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def compact(text: str, limit: int = 1200) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


if __name__ == "__main__":
    sys.exit(main())
