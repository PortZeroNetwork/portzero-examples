# Python Examples

This directory contains two minimal Python examples for PortZero Local:

- `process`: runs a plain Python process on the host machine.
- `docker`: runs the same minimal Python HTTP server in a Docker container.

The process example asks the OS to listen on port `0`, so the OS assigns an available localhost port. The Docker example listens on port `8080` inside the container and asks Docker to assign an available localhost port on the host.

Both examples use Python's standard library `http.server` instead of a web framework. For Python, that is the smallest useful choice for showing PortZero Local because the example only needs one HTTP endpoint and no routing, middleware, async runtime, or framework configuration.

Run the process example:

```sh
cd python/process
PZ_TUNNEL="python-process.portzero.local:80" python3 app.py
```

Run the Docker example:

```sh
cd python/docker
PZ_TUNNEL="python-docker.portzero.local:80" docker compose up --build
```

See `process/README.md` or `docker/README.md` inside the variant directory for the commands (including PowerShell syntax).
