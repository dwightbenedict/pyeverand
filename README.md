# everand-books

Download Everand books you can read and package them as EPUB files. Only books your account can read can be downloaded.

## Install
You need Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).
```bash
uv sync
```

## Use the app
```bash
uv run everand-books-gui
```
This opens `http://127.0.0.1:8080` in your browser. Press Ctrl+C in the terminal to quit.

1. Open **Settings** (the gear button) and save the two cookies of a signed-in everand.com session. **?** (**How to Find Your Cookies** on touch screens) shows how to get them.
2. Paste book links or IDs, one per line.
3. Press **Choose…** to save somewhere other than your Downloads folder, then press **Download**.

## Good to know
- **The cross beside a downloaded book deletes its EPUB file**, without asking first.
- The ring beside a book shows its progress. Press it to cancel the download.
- The download list is cleared when you quit.
- **Your cookies give access to your account, so do not share them.** They are saved in a `.env` file in the folder you start the app from.
- The app can only be reached from your own computer and has no sign-in: anyone who can open it there can see your saved cookies.
- If port 8080 is taken, set `EVERAND_BOOKS_GUI_PORT` to another one.
- The folder dialog needs Python with Tk, which some Linux systems install as a separate package.

## Command line
Save the cookies in the app first, or copy `.env.example` to `.env` and fill them in.
```bash
uv run python -m everand_books 696073235                       # saves to your Downloads folder
uv run python -m everand_books 696073235 --output-dir ./books
```
The number is the book's ID, found in its address: `everand.com/book/<number>/...`
