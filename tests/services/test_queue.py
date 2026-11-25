import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from everand_books.domain import DownloadProgress, DownloadStatus, ProgressListener
from everand_books.errors import (
    BookNotFoundError,
    InvalidBookReferenceError,
    InvalidOutputFolderError,
)
from everand_books.services import DownloadQueue


class FakeDownloader:
    def __init__(self) -> None:
        self.downloaded: list[str] = []
        self.release = asyncio.Event()
        self.release.set()

    async def download_book(
        self, book_id: str, output_dir: Path, on_progress: ProgressListener | None = None
    ) -> Path:
        await self.release.wait()
        self.downloaded.append(book_id)

        if book_id == "404":
            msg = "Book with ID 404 not found."
            raise BookNotFoundError(msg)

        if book_id == "500":
            msg = "boom"
            raise RuntimeError(msg)

        assert on_progress is not None
        on_progress(DownloadProgress("Title", 1, 1))
        return output_dir / f"{book_id}.epub"


@pytest.fixture
def downloader() -> FakeDownloader:
    return FakeDownloader()


@pytest.fixture
def queue(downloader: FakeDownloader) -> DownloadQueue:
    @asynccontextmanager
    async def open_downloader() -> AsyncGenerator[FakeDownloader]:
        yield downloader

    return DownloadQueue(open_downloader)


def statuses(queue: DownloadQueue) -> list[DownloadStatus]:
    return [item.status for item in queue.items()]


def test_add_several_lines_queues_each_book_once(queue: DownloadQueue, tmp_path: Path) -> None:
    added = queue.add("1\n\nhttps://www.everand.com/book/2/A\n1\n", str(tmp_path))

    assert added == 2
    assert [item.book_id for item in queue.items()] == ["1", "2"]


def test_add_book_already_waiting_is_skipped(queue: DownloadQueue, tmp_path: Path) -> None:
    queue.add("1", str(tmp_path))

    assert queue.add("1", str(tmp_path)) == 0


def test_add_with_one_invalid_line_queues_nothing(queue: DownloadQueue, tmp_path: Path) -> None:
    with pytest.raises(InvalidBookReferenceError):
        queue.add("1\nnot a book", str(tmp_path))

    assert queue.items() == ()


def test_add_blank_text_is_rejected(queue: DownloadQueue, tmp_path: Path) -> None:
    with pytest.raises(InvalidBookReferenceError, match="at least one"):
        queue.add(" \n ", str(tmp_path))


@pytest.mark.parametrize("folder", ["", "   ", "relative/folder"])
def test_add_without_full_folder_path_is_rejected(queue: DownloadQueue, folder: str) -> None:
    with pytest.raises(InvalidOutputFolderError):
        queue.add("1", folder)


async def test_run_downloads_in_order_and_continues_after_a_failure(
    queue: DownloadQueue, downloader: FakeDownloader, tmp_path: Path
) -> None:
    queue.add("1\n404\n2", str(tmp_path))

    await queue.run()

    first, missing, last = queue.items()
    assert downloader.downloaded == ["1", "404", "2"]
    assert first.saved_path == tmp_path / "1.epub"
    assert first.progress == DownloadProgress("Title", 1, 1)
    assert (missing.status, missing.error) == (DownloadStatus.FAILED, "Book with ID 404 not found.")
    assert last.status is DownloadStatus.DONE


async def test_run_unexpected_error_marks_item_failed_and_queue_can_resume(
    queue: DownloadQueue, tmp_path: Path
) -> None:
    queue.add("500\n2", str(tmp_path))

    with pytest.raises(RuntimeError):
        await queue.run()

    assert statuses(queue) == [DownloadStatus.FAILED, DownloadStatus.QUEUED]
    await queue.run()
    assert statuses(queue) == [DownloadStatus.FAILED, DownloadStatus.DONE]


async def test_run_while_running_returns_at_once_and_active_item_cannot_be_removed(
    queue: DownloadQueue, downloader: FakeDownloader, tmp_path: Path
) -> None:
    downloader.release.clear()
    queue.add("1", str(tmp_path))
    first_run = asyncio.create_task(queue.run())
    await asyncio.sleep(0)

    await queue.run()
    queue.remove(1)

    assert statuses(queue) == [DownloadStatus.DOWNLOADING]
    downloader.release.set()
    await first_run
    assert downloader.downloaded == ["1"]


async def test_retry_failed_item_queues_it_again(queue: DownloadQueue, tmp_path: Path) -> None:
    queue.add("404", str(tmp_path))
    await queue.run()

    queue.retry(1)

    (item,) = queue.items()
    assert (item.status, item.error) == (DownloadStatus.QUEUED, None)


def test_retry_and_remove_ignore_items_they_do_not_apply_to(
    queue: DownloadQueue, tmp_path: Path
) -> None:
    queue.add("1", str(tmp_path))
    before = queue.items()

    queue.retry(1)
    queue.retry(99)
    queue.remove(99)

    assert queue.items() == before


def test_remove_waiting_item_drops_it(queue: DownloadQueue, tmp_path: Path) -> None:
    queue.add("1", str(tmp_path))

    queue.remove(1)

    assert queue.items() == ()
