# syntax=docker/dockerfile:1
# Build:  docker build -t everand-books .
# Commit uv.lock (run `uv lock`) so image builds are reproducible.

FROM python:3.12-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv
WORKDIR /app
# Dependencies first, so this layer is cached until pyproject.toml / uv.lock change.
COPY pyproject.toml README.md uv.lock* ./
RUN uv sync --no-dev --no-install-project
COPY src ./src
RUN uv sync --no-dev

FROM python:3.12-slim
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
USER app
ENTRYPOINT ["python", "-m", "everand_books"]
CMD ["--help"]
