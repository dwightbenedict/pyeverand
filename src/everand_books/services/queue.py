from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import replace
from functools import partial
from itertools import count
from pathlib import Path
from typing import Protocol

from everand_books.domain import (
    DownloadProgress,
    DownloadStatus,
    ProgressListener,
    QueuedDownload,
    parse_book_id,
)
from everand_books.errors import AppError, InvalidBookReferenceError, InvalidOutputFolderError


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
    book_ids = [parse_book_id(line) for line in references.splitlines() if line.strip()]

    if not book_ids:
        msg = "Enter at least one book link or ID."
        raise InvalidBookReferenceError(msg)

    return list(dict.fromkeys(book_ids))


class DownloadQueue:
    """Downloads books one at a time, in the order they were added."""

    def __init__(self, open_downloader: DownloaderOpener) -> None:
        self._open_downloader = open_downloader
        self._items: dict[int, QueuedDownload] = {}
        self._ids = count(1)
        self._is_running = False

    def items(self) -> tuple[QueuedDownload, ...]:
        return tuple(self._items.values())

    def add(self, references: str, folder: str) -> int:
        """Queue one book per line, or none if any line is invalid. Return how many were added."""
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

    def remove(self, item_id: int) -> None:
        item = self._items.get(item_id)

        if item is not None and item.status is not DownloadStatus.DOWNLOADING:
            del self._items[item_id]

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

        try:
            await self._download(item)

        except AppError as err:
            # One failed book must not stop the rest of the queue.
            self._fail(item.item_id, str(err))

        finally:
            if self._items[item.item_id].status is DownloadStatus.DOWNLOADING:
                self._fail(item.item_id, UNEXPECTED_FAILURE)

    async def _download(self, item: QueuedDownload) -> None:
        async with self._open_downloader() as downloader:
            path = await downloader.download_book(
                item.book_id, item.output_dir, partial(self._record_progress, item.item_id)
            )

        self._items[item.item_id] = replace(
            self._items[item.item_id], status=DownloadStatus.DONE, saved_path=path
        )

    def _record_progress(self, item_id: int, progress: DownloadProgress) -> None:
        self._items[item_id] = replace(self._items[item_id], progress=progress)

    def _update(self, item_id: int, status: DownloadStatus) -> None:
        self._items[item_id] = replace(self._items[item_id], status=status)

    def _fail(self, item_id: int, error: str) -> None:
        self._items[item_id] = replace(
            self._items[item_id], status=DownloadStatus.FAILED, error=error
        )
