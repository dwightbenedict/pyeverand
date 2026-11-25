from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from everand_books.domain import Book, BookMetadata, Chapter, Credentials, NavChapter


class BookSource(Protocol):
    async def fetch_metadata(self, book_id: str) -> BookMetadata:
        """Raise ``BookNotFoundError`` or ``BookNotAccessibleError`` when it cannot be read."""
        ...

    async def fetch_toc(self, book_id: str) -> list[NavChapter]: ...

    async def fetch_stylesheet(self, book_id: str) -> Mapping[str, str]: ...

    async def fetch_chapter(self, book_id: str, number: int) -> Chapter: ...

    async def fetch_chapter_image(self, book_id: str, number: int, filename: str) -> bytes: ...

    async def fetch_cover(self, cover_url: str) -> bytes: ...


class CredentialStore(Protocol):
    async def save(self, credentials: Credentials) -> None: ...


class EpubWriter(Protocol):
    async def write(self, book: Book, output_dir: Path) -> Path: ...
