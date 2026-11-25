import asyncio
import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import replace
from functools import partial
from itertools import count
from pathlib import Path
from typing import Protocol

from pyeverand.domain import (
    DownloadProgress,
    DownloadStatus,
    ProgressListener,
    QueuedDownload,
    parse_book_id,
)
from pyeverand.errors import AppError, InvalidBookReferenceError, InvalidOutputFolderError
from pyeverand.services.ports import SavedBooks


logger = logging.getLogger(__name__)

UNEXPECTED_FAILURE = "The download stopped unexpectedly. See the terminal for details."
UNFINISHED = frozenset({DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING})


class BookDownloader(Protocol):
    async def download_book(
        self, book_id: str, output_dir: Path, on_progress: ProgressListener | None = None
    ) -> Path: ...


type DownloaderOpener = Callable[[], AbstractAsyncContextManager[BookDownloader]]


def _parse_output_dir(folder: str) -> Path:
    path = Path(folder.strip()).expanduser()

    if not folder.strip() or not path.is_absolute():
        msg = "Enter the full path of the folder to save in."
        raise InvalidOutputFolderError(msg)

    return path


def _parse_book_ids(references: str) -> list[str]:
    book_ids: list[str] = []
    problems: list[str] = []

    # Blank lines are counted too, so the numbers match the lines the person sees.
    for number, line in enumerate(references.splitlines(), start=1):
        if not line.strip():
            continue

        try:
            book_ids.append(parse_book_id(line))

        except InvalidBookReferenceError as err:
            problems.append(f"Line {number}: {err}")

    if problems:
        raise InvalidBookReferenceError("\n".join(problems))

    if not book_ids:
        msg = "Enter at least one book link or ID."
        raise InvalidBookReferenceError(msg)

    return list(dict.fromkeys(book_ids))


def check_download_request(references: str, folder: str) -> None:
    """Raise the error that ``DownloadQueue.add`` would raise for this input."""
    _parse_book_ids(references)
    _parse_output_dir(folder)


class DownloadQueue:
    """Downloads books one at a time, in the order they were added."""

    def __init__(
        self,
        open_downloader: DownloaderOpener,
        saved_books: SavedBooks,
        require_credentials: Callable[[], None],
    ) -> None:
        self._open_downloader = open_downloader
        self._saved_books = saved_books
        self._require_credentials = require_credentials
        self._active: asyncio.Task[None] | None = None
        self._cancelled: set[int] = set()
        self._items: dict[int, QueuedDownload] = {}
        self._ids = count(1)
        self._is_running = False

    def items(self) -> tuple[QueuedDownload, ...]:
        return tuple(self._items.values())

    def add(self, references: str, folder: str) -> int:
        """Queue one book per line, or none if any line is invalid. Return how many were added."""
        self._require_credentials()
        book_ids = _parse_book_ids(references)
        output_dir = _parse_output_dir(folder)
        pending = {item.book_id for item in self._items.values() if item.status in UNFINISHED}
        new_ids = [book_id for book_id in book_ids if book_id not in pending]

        for book_id in new_ids:
            item_id = next(self._ids)
            self._items[item_id] = QueuedDownload(item_id, book_id, output_dir)

        return len(new_ids)

    def retry(self, item_id: int) -> None:
        item = self._items.get(item_id)

        if item is not None and item.status is DownloadStatus.FAILED:
            self._items[item_id] = QueuedDownload(item_id, item.book_id, item.output_dir)

    async def remove(self, item_id: int) -> None:
        """Cancel an unfinished download, or drop a finished one and delete the file it saved.

        Raise ``OutputDeleteError`` when the file cannot be deleted; the item is dropped anyway.
        """
        item = self._items.get(item_id)

        if item is None:
            return

        if item.status is DownloadStatus.DOWNLOADING:
            self._cancel_active(item_id)

        elif item.status is DownloadStatus.DONE and item.saved_path is not None:
            await self._delete_saved(item.saved_path)

        else:
            del self._items[item_id]

    def _cancel_active(self, item_id: int) -> None:
        # A second cancel would interrupt the clean-up that the first one started.
        if item_id not in self._cancelled and self._active is not None:
            self._cancelled.add(item_id)
            self._active.cancel()

    async def _delete_saved(self, path: Path) -> None:
        # The same book downloaded twice has two items for one file.
        for other in self.items():
            if other.status is DownloadStatus.DONE and other.saved_path == path:
                del self._items[other.item_id]

        await self._saved_books.delete(path)

    async def run(self) -> None:
        """Download until nothing is queued. Does nothing if a run is already in progress."""
        if self._is_running:
            return

        self._is_running = True

        try:
            while (item := self._next_queued()) is not None:
                await self._process(item)

        finally:
            self._is_running = False

    def _next_queued(self) -> QueuedDownload | None:
        queued = (item for item in self._items.values() if item.status is DownloadStatus.QUEUED)
        return next(queued, None)

    async def _process(self, item: QueuedDownload) -> None:
        self._update(item.item_id, status=DownloadStatus.DOWNLOADING)

        # A task of its own, so one download can be cancelled without stopping the queue.
        task = self._active = asyncio.create_task(self._download(item))

        try:
            await asyncio.wait([task])

            if item.item_id in self._cancelled:
                await self._discard(item.item_id, task)

            else:
                task.result()

        except AppError as err:
            # One failed book must not stop the rest of the queue.
            self._fail(item.item_id, str(err))

        finally:
            task.cancel()
            current = self._items.get(item.item_id)

            if current is not None and current.status is DownloadStatus.DOWNLOADING:
                self._fail(item.item_id, UNEXPECTED_FAILURE)

    async def _download(self, item: QueuedDownload) -> None:
        async with self._open_downloader() as downloader:
            path = await downloader.download_book(
                item.book_id, item.output_dir, partial(self._record_progress, item.item_id)
            )
            # Recorded at once: a cancel while the downloader closes must still find the file.
            self._items[item.item_id] = replace(self._items[item.item_id], saved_path=path)

        self._update(item.item_id, status=DownloadStatus.DONE)

    async def _discard(self, item_id: int, task: asyncio.Task[None]) -> None:
        self._cancelled.discard(item_id)
        item = self._items.pop(item_id)

        if not task.cancelled() and (error := task.exception()) is not None:
            logger.warning("cancelled download ended with an error: %s", error)

        if item.saved_path is not None:
            try:
                await self._saved_books.delete(item.saved_path)

            except AppError as err:
                logger.warning("%s", err)

    def _record_progress(self, item_id: int, progress: DownloadProgress) -> None:
        self._items[item_id] = replace(self._items[item_id], progress=progress)

    def _update(self, item_id: int, status: DownloadStatus) -> None:
        self._items[item_id] = replace(self._items[item_id], status=status)

    def _fail(self, item_id: int, error: str) -> None:
        self._items[item_id] = replace(
            self._items[item_id], status=DownloadStatus.FAILED, error=error
        )
