import asyncio
from pathlib import Path

from pyeverand.domain import (
    Book,
    BookChapter,
    DownloadProgress,
    ImageFile,
    NavChapter,
    ProgressListener,
)
from pyeverand.services.ports import BookSource, EpubWriter


class _ProgressTracker:
    def __init__(self, title: str, total: int, listener: ProgressListener | None) -> None:
        self._title = title
        self._total = total
        self._listener = listener
        self._completed = 0
        self._report()

    def chapter_done(self) -> None:
        self._completed += 1
        self._report()

    def _report(self) -> None:
        if self._listener is not None:
            self._listener(DownloadProgress(self._title, self._completed, self._total))


class DownloadBookService:
    def __init__(self, source: BookSource, writer: EpubWriter) -> None:
        self._source = source
        self._writer = writer

    async def download_book(
        self, book_id: str, output_dir: Path, on_progress: ProgressListener | None = None
    ) -> Path:
        metadata = await self._source.fetch_metadata(book_id)
        canonical_id = metadata.everand_id
        cover = await self._source.fetch_cover(metadata.cover_url) if metadata.cover_url else None
        stylesheet = await self._source.fetch_stylesheet(canonical_id)
        toc = await self._source.fetch_toc(canonical_id)
        tracker = _ProgressTracker(metadata.title, len(toc), on_progress)
        chapters = await asyncio.gather(
            *(self._download_tracked(canonical_id, nav, tracker) for nav in toc)
        )
        book = Book(metadata, stylesheet, tuple(chapters), cover)
        return await self._writer.write(book, output_dir)

    async def _download_tracked(
        self, book_id: str, nav: NavChapter, tracker: _ProgressTracker
    ) -> BookChapter:
        chapter = await self._download_chapter(book_id, nav)
        tracker.chapter_done()
        return chapter

    async def _download_chapter(self, book_id: str, nav: NavChapter) -> BookChapter:
        chapter = await self._source.fetch_chapter(book_id, nav.number)
        contents = await asyncio.gather(
            *(
                self._source.fetch_chapter_image(book_id, nav.number, filename)
                for filename in chapter.image_filenames
            )
        )
        images = tuple(map(ImageFile, chapter.image_filenames, contents))
        return BookChapter(nav, chapter, images)
