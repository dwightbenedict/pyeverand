import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from lxml import etree
from pathvalidate import sanitize_filename

from everand_books.adapters.epub.element import XmlElement
from everand_books.adapters.epub.images import plan_images
from everand_books.adapters.epub.layout import (
    CONTAINER_XML_PATH,
    CONTENT_OPF_PATH,
    MIMETYPE_PATH,
    NAV_HREF,
    STYLESHEET_HREF,
    archive_path,
    chapter_href,
    image_href,
)
from everand_books.adapters.epub.nav import build_nav_document
from everand_books.adapters.epub.package import build_container_document, build_package_document
from everand_books.adapters.epub.rendering import render_chapter
from everand_books.adapters.epub.stylesheet import render_stylesheet
from everand_books.domain import Book


XHTML_DOCTYPE = "<!DOCTYPE html>"


def _xml(document: XmlElement, doctype: str | None = None) -> bytes:
    return etree.tostring(
        document,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
        doctype=doctype,
    )


def build_archive_entries(book: Book, modified: datetime) -> dict[str, bytes]:
    toc = [chapter.nav for chapter in book.chapters]
    entries = {
        CONTAINER_XML_PATH: _xml(build_container_document()),
        CONTENT_OPF_PATH: _xml(build_package_document(book, modified)),
        archive_path(NAV_HREF): _xml(
            build_nav_document(toc, book.metadata.language), XHTML_DOCTYPE
        ),
        archive_path(STYLESHEET_HREF): render_stylesheet(book.stylesheet).encode(),
    }
    images = plan_images(book)
    for chapter in book.chapters:
        chapter_id = chapter.nav.chapter_id
        document = render_chapter(chapter, images.names[chapter_id])
        entries[archive_path(chapter_href(chapter_id))] = _xml(document, XHTML_DOCTYPE)
    for filename, content in images.files.items():
        entries[archive_path(image_href(filename))] = content
    return entries


def _write_archive(path: Path, entries: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w") as archive:
        # The EPUB container format requires mimetype to be the first entry, uncompressed.
        archive.writestr(MIMETYPE_PATH, "application/epub+zip", compress_type=ZIP_STORED)
        for name, content in entries.items():
            archive.writestr(name, content, compress_type=ZIP_DEFLATED)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ZipEpubWriter:
    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock

    async def write(self, book: Book, output_dir: Path) -> Path:
        entries = build_archive_entries(book, self._clock())
        path = output_dir / sanitize_filename(f"{book.metadata.title}.epub")
        await asyncio.to_thread(_write_archive, path, entries)
        return path
