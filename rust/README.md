# Rust Examples

This directory contains two minimal Rust examples for PortZero Local:

- `process`: runs a plain Rust process on the host machine.
- `docker`: runs the same minimal Rust HTTP server in a Docker container.

The process example asks the OS to listen on port `0`, so the OS assigns an available localhost port. The Docker example listens on port `8080` inside the container and asks Docker to assign an available localhost port on the host.

Both examples use Rust's standard library instead of a web framework. For Rust, that is the smallest useful choice for showing PortZero Local because the example only needs one HTTP endpoint and no routing, middleware, async runtime, or framework configuration.

Run the process example:

```sh
cd rust/process
PZ_TUNNEL="rust-process.portzero.local:80" ./scripts/run.sh
```

Run the Docker example:

```sh
cd rust/docker
PZ_TUNNEL="rust-docker.portzero.local:80" ./scripts/run.sh
```

On Windows, run the matching `scripts/run.ps1` script from PowerShell.
