from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from everand_books.domain.progress import DownloadProgress


class DownloadStatus(StrEnum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    DONE = "done"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class QueuedDownload:
    item_id: int
    book_id: str
    output_dir: Path
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: DownloadProgress | None = None
    saved_path: Path | None = None
    error: str | None = None
