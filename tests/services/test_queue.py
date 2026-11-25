import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from everand_books.domain import DownloadProgress, DownloadStatus, ProgressListener
from everand_books.errors import (
    BookNotFoundError,
    CredentialsRequiredError,
    EverandRequestError,
    InvalidBookReferenceError,
    InvalidOutputFolderError,
    OutputDeleteError,
)
from everand_books.services import DownloadQueue


class FakeDownloader:
    def __init__(self) -> None:
        self.downloaded: list[str] = []
        self.release = asyncio.Event()
        self.release.set()
        self.closing = asyncio.Event()
        self.closing.set()
        self.fails_on_cancel = False

    async def download_book(
        self, book_id: str, output_dir: Path, on_progress: ProgressListener | None = None
    ) -> Path:
        await self._wait_for_release()
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

    async def _wait_for_release(self) -> None:
        try:
            await self.release.wait()

        except asyncio.CancelledError as err:
            if self.fails_on_cancel:
                msg = "failed while stopping"
                raise EverandRequestError(msg) from err

            raise


@pytest.fixture
def downloader() -> FakeDownloader:
    return FakeDownloader()


class FakeSavedBooks:
    def __init__(self) -> None:
        self.deleted: list[Path] = []
        self.fails = False

    async def delete(self, path: Path) -> None:
        self.deleted.append(path)

        if self.fails:
            msg = "cannot delete"
            raise OutputDeleteError(msg)


@asynccontextmanager
async def unused_downloader() -> AsyncGenerator[FakeDownloader]:
    yield FakeDownloader()


@pytest.fixture
def saved_books() -> FakeSavedBooks:
    return FakeSavedBooks()


@pytest.fixture
def queue(downloader: FakeDownloader, saved_books: FakeSavedBooks) -> DownloadQueue:
    @asynccontextmanager
    async def open_downloader() -> AsyncGenerator[FakeDownloader]:
        yield downloader
        await downloader.closing.wait()

    return DownloadQueue(open_downloader, saved_books, lambda: None)


async def started(queue: DownloadQueue) -> asyncio.Task[None]:
    run = asyncio.create_task(queue.run())

    # Enough turns of the event loop for the download to reach whatever blocks it.
    for _ in range(5):
        await asyncio.sleep(0)

    return run


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


def test_add_names_the_line_number_of_every_invalid_line(
    queue: DownloadQueue, tmp_path: Path
) -> None:
    with pytest.raises(InvalidBookReferenceError) as raised:
        queue.add("1\n\nfirst bad\n2\nsecond bad", str(tmp_path))

    assert str(raised.value).splitlines() == [
        "Line 3: Not an Everand book link or ID: first bad",
        "Line 5: Not an Everand book link or ID: second bad",
    ]


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


async def test_run_while_running_returns_at_once(
    queue: DownloadQueue, downloader: FakeDownloader, tmp_path: Path
) -> None:
    downloader.release.clear()
    queue.add("1", str(tmp_path))
    first_run = await started(queue)

    await queue.run()

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


async def test_retry_and_remove_ignore_items_they_do_not_apply_to(
    queue: DownloadQueue, tmp_path: Path
) -> None:
    queue.add("1", str(tmp_path))
    before = queue.items()

    queue.retry(1)
    queue.retry(99)
    await queue.remove(99)

    assert queue.items() == before


@pytest.mark.parametrize("references", ["1", "404"])
async def test_remove_waiting_or_failed_item_drops_it_and_deletes_nothing(
    queue: DownloadQueue, saved_books: FakeSavedBooks, references: str, tmp_path: Path
) -> None:
    queue.add(references, str(tmp_path))

    if references == "404":
        await queue.run()

    await queue.remove(1)

    assert queue.items() == ()
    assert saved_books.deleted == []


async def test_remove_finished_item_deletes_its_file_and_every_item_for_that_file(
    queue: DownloadQueue, saved_books: FakeSavedBooks, tmp_path: Path
) -> None:
    for references in ("1", "1\n2"):
        queue.add(references, str(tmp_path))
        await queue.run()

    await queue.remove(1)

    assert [item.book_id for item in queue.items()] == ["2"]
    assert saved_books.deleted == [tmp_path / "1.epub"]


async def test_remove_finished_item_drops_it_even_when_the_file_cannot_be_deleted(
    queue: DownloadQueue, saved_books: FakeSavedBooks, tmp_path: Path
) -> None:
    saved_books.fails = True
    queue.add("1", str(tmp_path))
    await queue.run()

    with pytest.raises(OutputDeleteError):
        await queue.remove(1)

    assert queue.items() == ()


async def test_remove_downloading_item_cancels_it_and_the_queue_goes_on(
    queue: DownloadQueue, downloader: FakeDownloader, tmp_path: Path
) -> None:
    downloader.release.clear()
    queue.add("1\n2", str(tmp_path))
    run = await started(queue)

    await queue.remove(1)
    await queue.remove(1)
    downloader.release.set()
    await run

    assert [(item.book_id, item.status) for item in queue.items()] == [("2", DownloadStatus.DONE)]
    assert downloader.downloaded == ["2"]


async def remove_while_closing(
    queue: DownloadQueue, downloader: FakeDownloader, folder: Path
) -> None:
    downloader.closing.clear()
    queue.add("1", str(folder))
    run = await started(queue)

    await queue.remove(1)
    await run


async def test_remove_while_the_downloader_closes_deletes_the_saved_file(
    queue: DownloadQueue, downloader: FakeDownloader, saved_books: FakeSavedBooks, tmp_path: Path
) -> None:
    await remove_while_closing(queue, downloader, tmp_path)

    assert queue.items() == ()
    assert saved_books.deleted == [tmp_path / "1.epub"]


async def test_remove_while_closing_goes_on_when_the_file_cannot_be_deleted(
    queue: DownloadQueue, downloader: FakeDownloader, saved_books: FakeSavedBooks, tmp_path: Path
) -> None:
    saved_books.fails = True

    await remove_while_closing(queue, downloader, tmp_path)

    assert queue.items() == ()


async def test_remove_download_that_fails_while_being_cancelled_logs_the_error(
    queue: DownloadQueue,
    downloader: FakeDownloader,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    downloader.release.clear()
    downloader.fails_on_cancel = True
    queue.add("1", str(tmp_path))
    run = await started(queue)

    await queue.remove(1)
    await run

    assert queue.items() == ()
    assert "failed while stopping" in caplog.text


async def test_cancelling_the_run_stops_the_active_download(
    queue: DownloadQueue, downloader: FakeDownloader, tmp_path: Path
) -> None:
    downloader.release.clear()
    queue.add("1", str(tmp_path))
    run = await started(queue)

    run.cancel()

    with pytest.raises(asyncio.CancelledError):
        await run

    assert statuses(queue) == [DownloadStatus.FAILED]
    assert downloader.downloaded == []


def test_add_without_credentials_queues_nothing(tmp_path: Path) -> None:
    def refuse() -> None:
        raise CredentialsRequiredError

    queue = DownloadQueue(unused_downloader, FakeSavedBooks(), refuse)

    with pytest.raises(CredentialsRequiredError):
        queue.add("1", str(tmp_path))

    assert queue.items() == ()
