import asyncio
from pathlib import Path

from everand_books.domain import Book, BookChapter, ImageFile, NavChapter
from everand_books.services.ports import BookSource, EpubWriter


class DownloadBookService:
    def __init__(self, source: BookSource, writer: EpubWriter) -> None:
        self._source = source
        self._writer = writer

    async def download_book(self, book_id: str, output_dir: Path) -> Path:
        metadata = await self._source.fetch_metadata(book_id)
        canonical_id = metadata.everand_id
        cover = await self._source.fetch_cover(metadata.cover_url) if metadata.cover_url else None
        stylesheet = await self._source.fetch_stylesheet(canonical_id)
        toc = await self._source.fetch_toc(canonical_id)
        chapters = await asyncio.gather(*(self._download_chapter(canonical_id, nav) for nav in toc))
        book = Book(metadata, stylesheet, tuple(chapters), cover)
        return await self._writer.write(book, output_dir)

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
