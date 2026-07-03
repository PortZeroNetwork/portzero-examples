FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY app.py .
EXPOSE 8080

# Run via uv (no pyproject.toml needed for this minimal stdlib example)
CMD ["uv", "run", "--no-project", "--quiet", "python", "app.py"]
