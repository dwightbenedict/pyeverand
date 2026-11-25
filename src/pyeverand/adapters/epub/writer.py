import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from lxml import etree
from pathvalidate import sanitize_filename

from pyeverand.adapters.epub.element import XmlElement
from pyeverand.adapters.epub.images import plan_images
from pyeverand.adapters.epub.layout import (
    CONTAINER_XML_PATH,
    CONTENT_OPF_PATH,
    MIMETYPE_PATH,
    NAV_HREF,
    STYLESHEET_HREF,
    archive_path,
    chapter_href,
    image_href,
)
from pyeverand.adapters.epub.nav import build_nav_document
from pyeverand.adapters.epub.package import build_container_document, build_package_document
from pyeverand.adapters.epub.rendering import render_chapter
from pyeverand.adapters.epub.stylesheet import render_stylesheet
from pyeverand.domain import Book
from pyeverand.errors import OutputWriteError


logger = logging.getLogger(__name__)

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


async def _write_in_thread(path: Path, entries: dict[str, bytes]) -> None:
    write = asyncio.create_task(asyncio.to_thread(_write_archive, path, entries))

    try:
        await asyncio.shield(write)

    except asyncio.CancelledError:
        # A thread cannot be stopped: let it finish, then take its file away.
        await asyncio.wait([write])
        _remove_cancelled(path, write)
        raise


def _remove_cancelled(path: Path, write: asyncio.Task[None]) -> None:
    error = write.exception()

    if error is not None:
        logger.warning("cancelled write ended with an error: %s", error)
        return

    try:
        path.unlink(missing_ok=True)

    except OSError:
        logger.warning("could not delete a cancelled download", exc_info=True)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ZipEpubWriter:
    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock

    async def write(self, book: Book, output_dir: Path) -> Path:
        entries = build_archive_entries(book, self._clock())
        path = output_dir / sanitize_filename(f"{book.metadata.title}.epub")

        try:
            await _write_in_thread(path, entries)

        except OSError as err:
            msg = f"Could not save {path}: {err.strerror or err}"
            raise OutputWriteError(msg) from err

        return path
