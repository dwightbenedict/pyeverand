from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pyeverand.domain import DownloadStatus, QueuedDownload
from pyeverand.errors import AppError
from pyeverand.services import check_download_request


class ProgressDisplay(StrEnum):
    HIDDEN = "hidden"
    BUSY = "busy"
    MEASURED = "measured"


@dataclass(frozen=True, slots=True)
class RowView:
    title: str
    detail: str
    status: DownloadStatus
    progress: ProgressDisplay = ProgressDisplay.HIDDEN
    percent: int = 0

    @property
    def can_retry(self) -> bool:
        return self.status is DownloadStatus.FAILED

    @property
    def delete_question(self) -> str | None:
        """Title of the alert to confirm before the row's button deletes a file."""
        return f"Delete “{self.title}”?" if self.status is DownloadStatus.DONE else None

    @property
    def action_label(self) -> str:
        """Name the row's one button: the progress ring, or the cross that replaces it."""
        match self.status:
            case DownloadStatus.QUEUED | DownloadStatus.DOWNLOADING:
                return f"Cancel download of {self.title}, {self.percent}% done"

            case DownloadStatus.DONE:
                return f"Remove {self.title} and delete its file"

            case _:  # DownloadStatus.FAILED
                return f"Remove {self.title}"


# Run by the person in the console of a signed-in everand.com tab. Scripts cannot read an HttpOnly
# cookie, so for one that is missing it says where to find it.
COOKIE_COMMAND = (
    '["_scribd_session", "_scribd_user_id"].forEach((name) => console.log(name, '
    'document.cookie.split("; ").find((pair) => pair.startsWith(name + "="))'
    "?.slice(name.length + 1) ?? "
    '"is hidden from scripts: copy it from the cookie table in developer tools"));'
)
COOKIE_STEPS = (
    "Sign in to everand.com and open your browser's developer tools.",
    "Copy the command below and run it in the Console.",
    (
        "If a cookie shows as hidden, copy it from the Application tab (Chrome, Edge) "
        "or the Storage tab (Firefox)."
    ),
)


@dataclass(frozen=True, slots=True)
class RequestView:
    can_download: bool
    hint: str = ""


def describe_request(references: str, folder: str) -> RequestView:
    try:
        check_download_request(references, folder)

    except AppError as err:
        # A disabled button cannot be pressed to ask why, but an untouched form needs no error.
        return RequestView(can_download=False, hint=str(err) if references.strip() else "")

    return RequestView(can_download=True)


def default_output_dir() -> str:
    return str(Path.home() / "Downloads")


def describe_added(count: int) -> str:
    if count == 0:
        return "Already in the queue."

    return f"Added {count} {'book' if count == 1 else 'books'}."


def _title(item: QueuedDownload) -> str:
    return item.progress.title if item.progress else f"Book {item.book_id}"


def _describe_downloading(item: QueuedDownload) -> RowView:
    progress = item.progress

    if progress is None or progress.total_chapters == 0:
        return RowView(_title(item), "Getting the book…", item.status, ProgressDisplay.BUSY)

    done, total = progress.completed_chapters, progress.total_chapters
    detail = "Saving the EPUB…" if done == total else f"{done} of {total} chapters"
    percent = done * 100 // total
    return RowView(_title(item), detail, item.status, ProgressDisplay.MEASURED, percent)


def describe_item(item: QueuedDownload) -> RowView:
    match item.status:
        case DownloadStatus.QUEUED:
            return RowView(_title(item), "Waiting", item.status, ProgressDisplay.MEASURED)

        case DownloadStatus.DOWNLOADING:
            return _describe_downloading(item)

        case DownloadStatus.DONE:
            return RowView(_title(item), f"Saved to {item.saved_path}", item.status)

        case _:  # DownloadStatus.FAILED
            return RowView(_title(item), f"Failed: {item.error}", item.status)
