from collections.abc import Mapping
from pathlib import Path

from pyeverand.domain import (
    Book,
    BookChapter,
    BookMetadata,
    Chapter,
    DownloadProgress,
    ImageFile,
    NavChapter,
    SectionKind,
)
from pyeverand.services import DownloadBookService


TOC = [NavChapter("One", SectionKind.BODYMATTER, 0), NavChapter("Two", SectionKind.BACKMATTER, 1)]
CHAPTERS = {1: Chapter("One", (), ("a.png", "b.png")), 2: Chapter("Two", ())}


class FakeSource:
    def __init__(self, cover_url: str | None) -> None:
        self._cover_url = cover_url

    async def fetch_metadata(self, book_id: str) -> BookMetadata:
        return BookMetadata(f"canonical-{book_id}", "Title", "en", cover_url=self._cover_url)

    async def fetch_toc(self, book_id: str) -> list[NavChapter]:
        assert book_id == "canonical-1"
        return TOC

    async def fetch_stylesheet(self, book_id: str) -> Mapping[str, str]:
        assert book_id == "canonical-1"
        return {"s1": "color: red"}

    async def fetch_chapter(self, book_id: str, number: int) -> Chapter:
        assert book_id == "canonical-1"
        return CHAPTERS[number]

    async def fetch_chapter_image(self, book_id: str, number: int, filename: str) -> bytes:
        return f"{book_id}/{number}/{filename}".encode()

    async def fetch_cover(self, cover_url: str) -> bytes:
        return cover_url.encode()


class FakeWriter:
    def __init__(self) -> None:
        self.books: list[Book] = []

    async def write(self, book: Book, output_dir: Path) -> Path:
        self.books.append(book)
        return output_dir / "book.epub"


async def test_download_book_assembles_book_and_returns_written_path(tmp_path: Path) -> None:
    writer = FakeWriter()
    service = DownloadBookService(FakeSource("https://img/cover"), writer)

    path = await service.download_book("1", tmp_path)

    assert path == tmp_path / "book.epub"
    assert writer.books == [
        Book(
            metadata=BookMetadata("canonical-1", "Title", "en", cover_url="https://img/cover"),
            stylesheet={"s1": "color: red"},
            chapters=(
                BookChapter(
                    TOC[0],
                    CHAPTERS[1],
                    (
                        ImageFile("a.png", b"canonical-1/1/a.png"),
                        ImageFile("b.png", b"canonical-1/1/b.png"),
                    ),
                ),
                BookChapter(TOC[1], CHAPTERS[2]),
            ),
            cover=b"https://img/cover",
        )
    ]


async def test_download_book_with_listener_reports_each_finished_chapter(tmp_path: Path) -> None:
    reports: list[DownloadProgress] = []
    service = DownloadBookService(FakeSource(None), FakeWriter())

    await service.download_book("1", tmp_path, reports.append)

    assert reports == [DownloadProgress("Title", done, 2) for done in (0, 1, 2)]


async def test_download_book_without_cover_url_skips_cover(tmp_path: Path) -> None:
    writer = FakeWriter()

    await DownloadBookService(FakeSource(None), writer).download_book("1", tmp_path)

    assert writer.books[0].cover is None
