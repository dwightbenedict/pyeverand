# everand-books

Download Everand books you can read and package them as EPUB files

## Setup
```bash
uv sync
uv run pre-commit install
cp .env.example .env
```
Fill in `.env` with two cookies from a browser that is signed in to everand.com:
`_scribd_session` goes into `EVERAND_BOOKS_SESSION_TOKEN` and `_scribd_user_id` into `EVERAND_BOOKS_USER_ID`.

## Usage
```bash
uv run python -m everand_books 696073235                      # saves "<title>.epub" in ~/Downloads
uv run python -m everand_books 696073235 --output-dir ./books
```
The argument is the number in the book's URL (`everand.com/book/<number>/...`). The book has to be one your account can read.

## Development
```bash
uv run ruff format .
uv run ruff check --fix .
uv run pyright
uv run lint-imports
uv run pytest        # fails below 100% coverage
```
Run it:
- CLI: `uv run python -m everand_books --help`

## Layout
- `domain/`: book, chapter and block models, plus grouping of bullets into lists and rows into tables.
- `services/`: the download use case and the two ports it needs (`BookSource`, `EpubWriter`).
- `adapters/everand/`: the Everand HTTP client. `adapters/epub/`: XHTML rendering and EPUB packaging.
- `interfaces/cli.py`: the command line.


See `docs/principles.md` for the design rules and `docs/decisions.md` for the architecture decisions. Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#specification).
