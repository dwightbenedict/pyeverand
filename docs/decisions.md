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

## Second interface: a local web GUI with NiceGUI (2026-11-25)
`everand-books-gui` serves one page on this computer for people who prefer not to use the CLI. NiceGUI was chosen over Tkinter and PySide6: it runs on asyncio like the rest of the code and is the UI framework the project template supports. It is a new dependency with many sub-dependencies of its own.
- Added by hand: the template answers still say `interfaces: [cli]`. `docs/design.md`, `tests/test_conventions.py` and the coverage exclusion for `nicegui_app.py` (layout only) are the template's.
- The server listens on 127.0.0.1 only and rejects other `Host` headers (DNS rebinding). It has no sign-in, so it must not be exposed to a network; the container image still runs only the CLI.
- tvOS idiom not built: a television cannot reach a server that only listens on this computer.
- System font stack (replaced by Inter, see "Typeface: Inter"); the two navigation icons are from Lucide (ISC), inline in `nicegui_app.py`.
- Text fields are Quasar inputs restyled to the tokens; buttons, lists and progress bars are plain elements.

## Download queue
`services/queue.py` downloads one book at a time and lives in memory, so it is shared by all browser tabs and lost when the program stops. It catches `AppError` per book, outside the interface layer, because one failed book must not stop the others; the message is kept on the item for the interface to show. The page polls the queue instead of receiving events, so a reloaded page shows the current state.

## One screen without a sidebar; settings in a sheet
At the owner's request the GUI has no tab bar or sidebar in any idiom: with one section there is nothing to navigate. A toolbar carries the title and a gear button that opens Settings as a sheet (from the bottom under 744px, centred above). Pressing Download without cookies opens the same sheet. Only missing or malformed cookies are detected there; expired ones show up as a failed download, because telling them apart needs a request to Everand. The gear and cross icons are Lucide's; the two navigation icons are gone.

## Cancelling and deleting downloads
Each row has one button: a progress ring that cancels, replaced by a cross once the download ends. On a finished row the cross also deletes the EPUB (`SavedBooks` port), at once and without confirmation, as the owner asked; the HIG would offer undo or a confirmation for data that costs time to get back. If the file cannot be deleted the row still goes and the page says why. The queue runs each download as its own task so that one can be cancelled; the EPUB writer lets its thread finish and then removes the file.

## Typeface: Inter
At the owner's request, an exception to the system font of `docs/design.md`. The variable web font is served by the program itself from `interfaces/fonts/`, with its SIL Open Font License beside it, so no font service is contacted; the system stack stays as the fallback.

## Reload during development
`EVERAND_BOOKS_GUI_RELOAD=true` restarts the GUI when a Python or CSS file of the package changes. NiceGUI can do that only when the module is the program run, so it needs `python -m everand_books.interfaces.nicegui_app`, not `everand-books-gui`. A restart empties the download queue. Off by default.

## Native folder dialog
A browser does not tell a page the path of a folder, but the server runs on the same computer, so "Choose…" opens the system's own folder dialog there (`FolderPicker` port, `tkinter` from the standard library, no new dependency). Tk needs a main thread, so the dialog is a short-lived process (`adapters/folder_window.py`), started with `subprocess.run` in a thread because the Windows event loop used with reload has no asyncio subprocesses. The path field is read-only. It needs a desktop session and a Python with Tk; without them the page shows an error and the default Downloads folder still works.

## Saved cookies shown in Settings
At the owner's request the sheet starts with the saved cookies, both masked, each with an eye button; this replaces never showing saved values. They are sent to the page when the sheet opens and cleared when it closes. The page has no sign-in, so anyone who can open it on this computer can now read them. Cookies from real environment variables are shown too.

## Console command for the cookies
The sheet itself says one line; the steps are in a popover (a bottom sheet under 744px), opened by a "?" help button on macOS (in the sheet's upper right corner at the owner's request; the HIG puts it in a lower corner) and by "How to Find Your Cookies" elsewhere. The command is copied, not displayed. Settings offers a one-line command to run in a signed-in everand.com console. It reads `document.cookie`, so it cannot see an `HttpOnly` cookie and says so for any it does not find. Whether Everand marks these two that way is unverified: it does not set them for signed-out visitors. The sheet is 440px wide from 744px up, narrower than the HIG form sheet, at the owner's request.

## Renamed to pyeverand (2026-11-26)
At the owner's request, replacing the old names in the entries above: the package is `pyeverand` (was `everand_books`), the distribution `pyeverand` and its GUI command `pyeverand-gui` (were `everand-books`, `everand-books-gui`), and settings are named `PYEVERAND_*` (were `EVERAND_BOOKS_*`). Deliberate break: the `EVERAND_BOOKS_*` variables are no longer read, so rename them in any `.env` or container configuration. The older `EVERAND__*` and `HTTP__*` names still work. `.copier-answers.yml` keeps `project_name: everand-books`, because it is not edited by hand.

## Cookie setup from the GUI
`AppOptions` holds the settings that need no cookies, so the GUI can start before they exist; `Settings` extends it. The GUI writes the two cookies into `.env` in the working directory, keeping other lines, and clears the settings cache. Real environment variables still take priority over `.env`.

## Confirming a delete (2026-11-26)
At the owner's request, replacing "at once and without confirmation" under "Cancelling and deleting downloads": the cross on a finished row opens a HIG alert (Cancel, Delete) before the EPUB is deleted. The cross on a failed row and the progress ring still act at once. `DownloadQueue.remove` deletes a finished download's file only with `delete_saved=True`, which the page passes after the alert, so a cancel pressed just as the download finishes deletes nothing.
