# PortZero Examples Guidance

These examples are teaching material for the smallest useful PortZero Local setup. Keep them minimal, predictable, and parseable.

## Repository Layout

- Organize examples by language, then runtime variant.
- Use `<language>/process` for the plain local process example.
- Use `<language>/docker` for the Docker container example.
- Do not combine process and Docker variants in the same folder.
- The root `README.md` must list every language directory that has examples, link only to that language folder, and avoid listing individual examples or variants.
- Each variant directory must be a complete minimal working example.
- Each variant directory must include:
  - `README.md` (with a code-fenced block showing the minimal commands to run the example)
  - the smallest source/build files needed to run that variant
- Each Docker variant directory must use Docker Compose and include `docker-compose.yml`.
- Each language directory must include `README.md` that lists `process` and `docker`, explains the difference consistently, and states the one web framework choice for that language.

## Scope

- Prefer one web framework per language across all examples.
- Do not add examples that demonstrate multiple PortZero approaches in one folder.
- Do not add extra routes, UI, background workers, databases, auth, config systems, or framework features unless the bare PortZero behavior cannot be shown without them.
- Every example must expose at least one HTTP endpoint.
- Terminal output must list an `http://` endpoint. Do not assume HTTPS is enabled in `portzero-local`.

## Runtime Output Contract

Every process or container launch must print exactly one parseable listener line after the HTTP endpoint is reachable:

```text
PORTZERO_EXAMPLE_LISTENING language=<language> variant=<process|docker> host=127.0.0.1 port=<port> url=http://127.0.0.1:<port>/ tunnel=<PZ_TUNNEL value> tunnel_url=http://<PZ_TUNNEL host>/
```

Rules:

- `language`, `variant`, `host`, `port`, `url`, `tunnel`, and `tunnel_url` are required.
- `host` must be `127.0.0.1`.
- `port` must be the localhost port assigned by the OS or Docker.
- `url` must use `http://`.
- `tunnel_url` must use `http://` and must omit the port from `PZ_TUNNEL`.
- Keep this line stable; test tooling and `../portzero-local` instructions may parse it.

Each launch must also print a very brief human explanation immediately after the parseable line:

```text
This <language> <process|container> was launched with PZ_TUNNEL=<value>. It is now listening on localhost port <port>. For process examples, the program asked to listen on port 0, so the OS assigned an available port. Next, portzero-local's local daemon will detect PZ_TUNNEL and the listening port, then make it available at http://<PZ_TUNNEL host>/.
```

For Docker examples, adjust the sentence to explain Docker's assigned localhost port instead of process port `0`.

## Running Examples

- Examples are run via the minimal commands shown in each variant directory's `README.md`.
- The code block in `README.md` shows the canonical command(s) (shell and PowerShell forms).
- For Docker variants, always use `docker compose up --build` (Compose handles build and run).
- The `PZ_TUNNEL` environment variable should be set by the user when following the example (apps and compose files provide matching defaults).
- The `just test` harness is responsible for friendly prerequisite messages and for executing the examples (it does not rely on scripts inside example dirs).

## Test Harness

- `just test` must discover examples automatically.
- Adding a new `<language>/<variant>` example with recognized project files should make it run on the next `just test`.
- When a language or variant needs a new detector, update `scripts/test_examples.py` in the same change.
