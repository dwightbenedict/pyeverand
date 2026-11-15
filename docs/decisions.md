# Architecture decisions

Append a new entry when you make an architectural decision (new dependency, new layer or package, change to a port, switch to migrations, ...). Newest last. Keep entries to a few lines: what, why, consequence.

## Layered architecture with enforced dependency direction
interfaces -> adapters -> services -> domain, checked by `lint-imports`. Business rules live in `domain/` and `services/` so they can be tested without any framework.

## Project kind: application
Runs on its own. Configuration is read once into `Settings` and the object graph is built in `wiring.py` (the composition root).

## Concurrency: async
I/O-bound work with concurrent operations. Ports, services and adapters that do I/O are `async def`; pure domain code stays synchronous. Switching back to sync touches every port, service and test.

## Interfaces: cli
Each interface is a thin adapter: parse input, call one service, render the result. No business logic in handlers.

## Container image
Multi-stage Docker build with uv, non-root user, configuration only through environment variables.

## Fixed project policies
- 100% line and branch coverage, enforced in `pyproject.toml`.
- Ruff (format and lint), pyright strict, import-linter contracts, pre-commit.
- Standard-library first; new dependencies need an entry here.

## Restructured from the pre-template layout (2026-11-14)
The project predates the template. Its code moved from `everand_books/{api,client,adapters,models,normalization,renderers,epub}` into `src/everand_books/{domain,services,adapters,interfaces}`. Deliberate breaks:
- Entry point: `python -m everand_books.main` (book ID hard-coded) became `python -m everand_books <book-id> [--output-dir DIR]`.
- Settings are named `EVERAND_BOOKS_*`. The old names (`EVERAND__SESSION_TOKEN`, `EVERAND__USER_ID`, `EVERAND__BASE_URL`, `EVERAND__ACCESS_TOKEN_TTLS`, `HTTP__TIMEOUT`, `HTTP__MAX_RETRIES`, `HTTP__MAX_RETRY_DELAY`) are still read, so an existing `.env` keeps working. The three HTTP settings now have defaults.
- The EPUB is written straight into a zip archive from memory. The unpacked working folder `<output>/<book-id>/` is no longer left behind.
- `EverandBooksException` is now `AppError`; unused error classes were removed.

## Renderer registry: `functools.singledispatch` keyed by block class
The hand-written registry was keyed by each block's `type` string and filled by importing every renderer module for its side effect. Dispatching on the class removes the string keys (and the `image` to `inline_image` renaming they forced, because block images and word images shared a string), keeps registration next to the dispatcher in one module, and lets a test assert that every block and word class has a renderer.

## Hosting: unconstrained
A local command-line tool, not a hosted service, so the Render free-tier budget and its dependency guard do not apply (Pillow and lxml are needed).

## Dependencies
- Kept: httpx, lxml, pillow, pydantic, pydantic-settings, selectolax, pathvalidate. Added by the template: typer.
- Removed: tenacity (a short retry loop in `adapters/everand/session.py` replaces it and takes an injectable sleep for tests), aiocache (replaced by a per-book token cache in `adapters/everand/auth.py`), aiofiles and orjson (standard library is enough), the `http2` extra of httpx (HTTP/2 was never switched on).
- Added for development: `types-lxml`, so pyright strict can check the lxml code.
- selectolax 1.x no longer ships the `HTMLParser` class the old code imported; the code uses `LexborHTMLParser`.

## EPUB output changes made with the restructure
- Chapters are serialised as XML (XHTML), not HTML, so void elements such as `<img>` are closed.
- `frontmatter` / `bodymatter` / `backmatter` moved from the spine `properties` attribute, where they are not valid values, to `epub:type` on each chapter's `<body>`.
- Manifest image ids are numbered (`image-1`, ...) because file names may start with a digit, which is not a valid XML id. ISBN identifiers are written as `urn:isbn:<isbn>`.
- Images from all chapters share one `Images/` folder. When two chapters (or a chapter and the cover) use one file name for different pictures, the later one is stored as `<chapter-id>-<name>` and that chapter's links follow it (`adapters/epub/images.py`). Identical pictures are stored once.
- Image links inside raw HTML blocks are pointed at the packaged file when its name matches a downloaded chapter image.

## HTTP behaviour
- Retries cover connection errors and HTTP 429/500/502/503/504 only. Other 4xx answers fail at once instead of being retried.
- At most `EVERAND_BOOKS_HTTP_MAX_CONCURRENCY` (default 8) requests run at a time; previously every chapter and image was requested at once.

## Line endings pinned to LF (`.gitattributes`)
The repository lives on a Windows drive and is used from WSL. `* text=auto eol=lf` keeps the commit hook and `scripts/*.sh` runnable there regardless of each machine's `core.autocrlf`. Not part of the template.

## Settings errors at start-up
As in the template, `main()` configures logging from settings before the Typer app starts. Settings need the Everand credentials, so every invocation, `--help` included, needs them; when they are missing `main()` prints the error and exits 1.

## Template update to `v0.3.0-4-ge1afde8` merged by hand
The project was adopted (`adopt: true`), so `copier update` only moves `.copier-answers.yml`. The changes between `v0.3.0` and that commit (logging settings and `logging_config.py`, ruff `LOG`/`G` and `lines-after-imports = 2`, the layered `Dockerfile`, the wider `.dockerignore`) were applied from a diff of the project generated at both versions.
