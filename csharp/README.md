# C# Examples

This directory contains two minimal C# examples for PortZero Local:

- `process`: runs a plain .NET process on the host machine.
- `docker`: runs the same minimal C# HTTP server in a Docker container.

The process example asks the OS to listen on port `0`, so the OS assigns an available localhost port. The Docker example listens on port `8080` inside the container and asks Docker to assign an available localhost port on the host.

Both examples use ASP.NET Core minimal APIs. For C#, that is the smallest built-in web framework choice in the .NET SDK for showing PortZero Local because the example only needs one HTTP endpoint and no controllers, middleware stack, routing setup, or extra packages.

Run the process example:

```sh
cd csharp/process
PZ_TUNNEL="csharp-process.portzero.local:80" dotnet run --no-launch-profile
```

Run the Docker example:

```sh
cd csharp/docker
PZ_TUNNEL="csharp-docker.portzero.local:80" docker compose up --build
```

See `process/README.md` or `docker/README.md` inside the variant directory for the commands (including PowerShell syntax).
