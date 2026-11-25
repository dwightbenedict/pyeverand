from pathlib import Path

import pytest

from pyeverand.domain import DownloadProgress, DownloadStatus, QueuedDownload
from pyeverand.interfaces.gui_view import (
    ProgressDisplay,
    RequestView,
    RowView,
    default_output_dir,
    describe_added,
    describe_item,
    describe_request,
)


def queued(status: DownloadStatus, progress: DownloadProgress | None = None) -> QueuedDownload:
    return QueuedDownload(1, "42", Path("out"), status, progress, Path("a.epub"), "No access.")


@pytest.mark.parametrize(
    ("status", "detail", "can_retry"),
    [
        (DownloadStatus.QUEUED, "Waiting", False),
        (DownloadStatus.DONE, "Saved to a.epub", False),
        (DownloadStatus.FAILED, "Failed: No access.", True),
    ],
)
def test_describe_item_idle_states(status: DownloadStatus, detail: str, can_retry: bool) -> None:
    view = describe_item(queued(status))

    ring = ProgressDisplay.MEASURED if status is DownloadStatus.QUEUED else ProgressDisplay.HIDDEN
    assert view == RowView("Book 42", detail, status, ring)
    assert view.can_retry == can_retry


@pytest.mark.parametrize(
    ("status", "label"),
    [
        (DownloadStatus.QUEUED, "Cancel download of Book 42, 0% done"),
        (DownloadStatus.DOWNLOADING, "Cancel download of Book 42, 0% done"),
        (DownloadStatus.DONE, "Remove Book 42 and delete its file"),
        (DownloadStatus.FAILED, "Remove Book 42"),
    ],
)
def test_action_label_says_what_the_row_button_does(status: DownloadStatus, label: str) -> None:
    assert describe_item(queued(status)).action_label == label


@pytest.mark.parametrize("progress", [None, DownloadProgress("Title", 0, 0)])
def test_describe_item_before_chapters_are_known_shows_busy_progress(
    progress: DownloadProgress | None,
) -> None:
    view = describe_item(queued(DownloadStatus.DOWNLOADING, progress))

    assert (view.detail, view.progress) == ("Getting the book…", ProgressDisplay.BUSY)


@pytest.mark.parametrize(
    ("done", "detail", "percent"),
    [(1, "1 of 3 chapters", 33), (3, "Saving the EPUB…", 100)],
)
def test_describe_item_downloading_shows_measured_progress(
    done: int, detail: str, percent: int
) -> None:
    view = describe_item(queued(DownloadStatus.DOWNLOADING, DownloadProgress("Title", done, 3)))

    assert view == RowView(
        "Title", detail, DownloadStatus.DOWNLOADING, ProgressDisplay.MEASURED, percent
    )


@pytest.mark.parametrize(
    ("count", "message"),
    [(0, "Already in the queue."), (1, "Added 1 book."), (3, "Added 3 books.")],
)
def test_describe_added_counts_books(count: int, message: str) -> None:
    assert describe_added(count) == message


@pytest.mark.parametrize(
    ("references", "folder", "hint"),
    [
        ("", str(Path.home()), ""),
        (" \n ", "", ""),
        ("1\nnot a book\n2", str(Path.home()), "Line 2: "),
        ("1", "relative", "full path of the folder"),
    ],
)
def test_describe_request_invalid_input_disables_download(
    references: str, folder: str, hint: str
) -> None:
    view = describe_request(references, folder)

    assert not view.can_download
    assert hint in view.hint
    assert bool(view.hint) is bool(hint)


def test_describe_request_valid_input_enables_download() -> None:
    assert describe_request("1\n\n2", str(Path.home())) == RequestView(can_download=True)


def test_default_output_dir_is_the_downloads_folder() -> None:
    assert Path(default_output_dir()) == Path.home() / "Downloads"
