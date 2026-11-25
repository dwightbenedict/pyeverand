from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DownloadProgress:
    title: str
    completed_chapters: int
    total_chapters: int


type ProgressListener = Callable[[DownloadProgress], None]
