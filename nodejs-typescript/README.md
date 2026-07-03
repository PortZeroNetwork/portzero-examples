# Node.js TypeScript Examples

This directory contains two minimal Node.js TypeScript examples for PortZero Local:

- `process`: runs a plain Node.js TypeScript process on the host machine.
- `docker`: runs the same minimal Node.js TypeScript HTTP server in a Docker container.

The process example asks the OS to listen on port `0`, so the OS assigns an available localhost port. The Docker example listens on port `8080` inside the container and asks Docker to assign an available localhost port on the host.

Both examples use Node.js's standard library `http` module instead of a web framework. For Node.js TypeScript, that is the smallest useful choice for showing PortZero Local because the example only needs one HTTP endpoint and no routing, middleware, async runtime, or framework configuration.

Run the process example:

```sh
cd nodejs-typescript/process
PZ_TUNNEL="nodejs-typescript-process.portzero.local:80" node app.ts
```

Run the Docker example:

```sh
cd nodejs-typescript/docker
PZ_TUNNEL="nodejs-typescript-docker.portzero.local:80" docker compose up --build
```

See `process/README.md` or `docker/README.md` inside the variant directory for the commands (including PowerShell syntax).
