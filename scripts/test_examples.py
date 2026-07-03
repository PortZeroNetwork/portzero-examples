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
            print(f"portzero-local: {detail}")
            print("  (just test validates examples directly via their localhost endpoints; portzero-local is not needed for the test run.)")

    failures.extend(check_example_prerequisites(examples))

    print("Testing examples by launching them and verifying HTTP responses (stdout from examples is shown for visibility).")

    runners = {
        "csharp": test_http_example,
        "nodejs-typescript": test_http_example,
        "python": test_http_example,
        "rust": test_http_example,
    }
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
    if any(path.glob("*.csproj")):
        return "csharp"
    if (path / "Cargo.toml").is_file():
        return "rust"
    if (path / "app.py").is_file():
        return "python"
    if (path / "app.ts").is_file():
        return "nodejs-typescript"
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

    if any(example.kind == "csharp" for example in examples):
        dotnet = shutil.which("dotnet")
        if dotnet is None:
            failures.append("Missing .NET SDK 10 or newer. Install .NET SDK 10 or newer, then rerun `just test`.")
        else:
            try:
                completed = subprocess.run(
                    [dotnet, "--version"],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=10,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                failures.append(".NET SDK is installed but `dotnet --version` timed out.")
            else:
                version = parse_dotnet_major_version(completed.stdout)
                if completed.returncode != 0:
                    failures.append(f".NET SDK is installed but not available: {compact(completed.stdout)}")
                elif version is None or version < 10:
                    failures.append(f".NET SDK 10 or newer is required; found {compact(completed.stdout)}.")

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

    if any(example.kind == "nodejs-typescript" for example in examples):
        node = shutil.which("node")
        if node is None:
            failures.append("Missing Node.js 24 or newer. Install Node.js 24 or newer, then rerun `just test`.")
        else:
            try:
                completed = subprocess.run(
                    [node, "--version"],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=10,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                failures.append("Node.js is installed but `node --version` timed out.")
            else:
                version = parse_node_major_version(completed.stdout)
                if completed.returncode != 0:
                    failures.append(f"Node.js is installed but not available: {compact(completed.stdout)}")
                elif version is None or version < 24:
                    failures.append(
                        f"Node.js 24 or newer is required to run TypeScript directly; found {compact(completed.stdout)}."
                    )

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

            try:
                completed = subprocess.run(
                    [docker, "compose", "version"],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=20,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                failures.append("Docker Compose is installed but `docker compose version` timed out.")
            else:
                if completed.returncode != 0:
                    failures.append(f"Docker Compose is not available: {compact(completed.stdout)}")

    return failures


def test_http_example(example: Example) -> Result:
    tunnel = f"{example.language}-{example.variant}.portzero.local:80"
    env = os.environ.copy()
    env["PZ_TUNNEL"] = tunnel

    if example.variant == "docker":
        return test_docker_example(example, tunnel, env)
    else:
        command = direct_command(example)
        print(f"+ ({example.path.relative_to(ROOT)}) {' '.join(command)}")
        proc = start_example(command, example.path, env)

        try:
            fields = wait_for_listener(proc, timeout=180)
            error = validate_listener_fields(example, fields, tunnel)
            if error:
                return Result(example.name, False, error)

            body = http_get(fields["url"], timeout=10)
            expected = [f"Hello from the PortZero {language_display_name(example)}", f"PZ_TUNNEL={tunnel}"]
            missing = [text for text in expected if text not in body]
            if missing:
                return Result(example.name, False, f"HTTP response missing: {', '.join(missing)}")
            return Result(example.name, True)
        except Exception as exc:
            return Result(example.name, False, str(exc))
        finally:
            stop_process(proc)


def direct_command(example: Example) -> list[str]:
    """Return the direct command to launch a process example (no wrapper script)."""
    lang = example.kind
    if lang == "python":
        if os.name == "nt":
            return ["py", "-3", "app.py"]
        return ["python3", "app.py"]
    if lang == "nodejs-typescript":
        return ["node", "app.ts"]
    if lang == "rust":
        return ["cargo", "run", "--quiet"]
    if lang == "csharp":
        return ["dotnet", "run", "--no-launch-profile"]
    # Fallback (should not happen)
    return ["python3", "app.py"] if os.name != "nt" else ["py", "-3", "app.py"]


def test_docker_example(example: Example, tunnel: str, env: dict[str, str]) -> Result:
    """Run docker example by orchestrating compose ourselves and emitting the required listener line.

    The complex logic lives only in the test harness, not in example folders.
    """
    project = f"portzero-example-{example.language}-{example.variant}-{os.getpid()}"
    compose_base = ["docker", "compose", "-p", project]
    cwd = example.path

    # Ensure clean start
    subprocess.run(compose_base + ["down", "--remove-orphans"], cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    print(f"+ ({cwd.relative_to(ROOT)}) PZ_TUNNEL={tunnel} docker compose -p {project} up --build -d")
    up = subprocess.run(compose_base + ["up", "--build", "-d"], cwd=cwd, env=env, text=True, capture_output=True)
    if up.returncode != 0:
        if up.stdout:
            sys.stdout.write(up.stdout)
        return Result(example.name, False, f"docker compose up failed: {compact(up.stdout or '')}")
    if up.stdout:
        sys.stdout.write(up.stdout)

    container_id = ""
    try:
        ps = subprocess.run(compose_base + ["ps", "-q", "app"], cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
        container_id = ps.stdout.strip()
    except Exception:
        pass

    deadline = time.monotonic() + 120
    host_port = ""
    while time.monotonic() < deadline:
        # Refresh container id if needed
        if not container_id:
            try:
                ps = subprocess.run(compose_base + ["ps", "-q", "app"], cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
                container_id = ps.stdout.strip()
            except Exception:
                pass

        # Get current published host port if available
        try:
            port_out = subprocess.run(compose_base + ["port", "app", "8080"], cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
            hp = (port_out.stdout or "").strip()
            if hp:
                host_port = hp.rsplit(":", 1)[-1] if ":" in hp else hp.strip()
        except Exception:
            host_port = ""

        if host_port:
            # Wait until the HTTP endpoint actually responds (external, works regardless of tools inside container)
            try:
                http_get(f"http://127.0.0.1:{host_port}/", timeout=2)
                break
            except Exception:
                pass

        time.sleep(0.25)
    else:
        # timeout
        try:
            logs = subprocess.run(compose_base + ["logs", "app"], cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
            print(logs.stdout)
        except Exception:
            pass
        subprocess.run(compose_base + ["down", "--remove-orphans"], cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return Result(example.name, False, "timed out waiting for docker container to become ready")

    if not host_port:
        # last attempt
        try:
            port_out = subprocess.run(compose_base + ["port", "app", "8080"], cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
            hp = port_out.stdout.strip()
            if hp:
                host_port = hp.rsplit(":", 1)[-1] if ":" in hp else hp
        except Exception:
            pass
    if not host_port:
        subprocess.run(compose_base + ["down", "--remove-orphans"], cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return Result(example.name, False, "could not determine host port from docker compose")

    tunnel_host = tunnel.split(":", 1)[0]
    listener_line = (
        f"PORTZERO_EXAMPLE_LISTENING language={example.language} variant=docker "
        f"host=127.0.0.1 port={host_port} url=http://127.0.0.1:{host_port}/ tunnel={tunnel} tunnel_url=http://{tunnel_host}/"
    )
    explanation = (
        f"This {language_display_name(example)} container was launched with PZ_TUNNEL={tunnel}. "
        f"It is now listening on localhost port {host_port}. Port Zero detects programs with PZ_TUNNEL listening on a port; "
        "the program does not need to read its own PZ_TUNNEL value or detect what port the OS has assigned to it. "
        "Technically the program doesn't even need to listen on port 0, although that is highly recommended because avoiding port conflicts is the whole point of using PortZero. "
        f"Docker assigned localhost port {host_port} for the container's HTTP endpoint. Next, portzero-local's local "
        f"daemon will detect PZ_TUNNEL and the listening port, then make it available at http://{tunnel_host}/."
    )

    # Build a follower command whose stdout first emits the required listener lines (for the test parser),
    # then streams the container logs. This replaces the old per-example scripts.
    if os.name == "nt":
        ps_script = (
            f'Write-Output "{listener_line}"; '
            f'Write-Output "{explanation}"; '
            f'docker compose -p {project} logs -f app'
        )
        follower_cmd = [
            "powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-Command", ps_script
        ]
    else:
        sh_cmd = f'printf "%s\n%s\n" "{listener_line}" "{explanation}"; exec docker compose -p {project} logs -f app'
        follower_cmd = ["sh", "-c", sh_cmd]

    print(f"+ (docker logs follower for {project})")
    proc = start_example(follower_cmd, cwd, env)

    try:
        # The listener lines are the first output from the follower; wait_for_listener will see them
        fields = wait_for_listener(proc, timeout=30)
        error = validate_listener_fields(example, fields, tunnel)
        if error:
            return Result(example.name, False, error)

        body = http_get(fields["url"], timeout=10)
        expected = [f"Hello from the PortZero {language_display_name(example)}", f"PZ_TUNNEL={tunnel}"]
        missing = [text for text in expected if text not in body]
        if missing:
            return Result(example.name, False, f"HTTP response missing: {', '.join(missing)}")
        return Result(example.name, True)
    except Exception as exc:
        return Result(example.name, False, str(exc))
    finally:
        stop_process(proc)
        subprocess.run(compose_base + ["down", "--remove-orphans"], cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


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


def language_display_name(example: Example) -> str:
    if example.kind == "csharp":
        return "C#"
    if example.kind == "nodejs-typescript":
        return "Node.js TypeScript"
    return example.language.title()


def parse_dotnet_major_version(output: str) -> int | None:
    match = re.search(r"(\d+)\.", output)
    if match is None:
        return None
    return int(match.group(1))


def parse_node_major_version(output: str) -> int | None:
    match = re.search(r"v?(\d+)", output)
    if match is None:
        return None
    return int(match.group(1))


def read_lines(stream, output: queue.Queue[str]) -> None:
    for line in stream:
        sys.stdout.write(line)
        sys.stdout.flush()
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
