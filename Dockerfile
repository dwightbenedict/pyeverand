# syntax=docker/dockerfile:1
# Build:  docker build -t everand-books .
# Commit uv.lock (run `uv lock`) so image builds are reproducible.

# uv comes from its own image as one static binary (a named stage so Dependabot can bump the tag).
FROM ghcr.io/astral-sh/uv:0.13.1 AS uv

# Third-party dependencies only: rebuilt when pyproject.toml / uv.lock change, not on a code change.
FROM python:3.12-slim AS deps
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml README.md uv.lock* ./
# The cache mount keeps uv's download cache between builds; it never becomes part of a layer.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

# The project itself, installed (not editable) into its own directory so it ships as its own layer.
FROM deps AS project
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-deps --target /app/site .

FROM python:3.12-slim
# /app belongs to the app user so the process can create files in its working directory
# (a SQLite file, for example); the installed code below stays root-owned and read-only to it.
RUN useradd --create-home --uid 1000 app && install -d -o app -g app /app
WORKDIR /app
# Two layers: dependencies (large, rarely changes) and the project (small, changes every build),
# so a code change rebuilds, pushes and pulls only the small one.
COPY --from=deps /app/.venv /app/.venv
COPY --from=project /app/site /app/site
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/site \
    PYTHONUNBUFFERED=1
USER app
ENTRYPOINT ["python", "-m", "everand_books"]
CMD ["--help"]
