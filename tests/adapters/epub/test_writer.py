from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

import pytest
from lxml import etree

from everand_books.adapters.epub import ZipEpubWriter
from everand_books.domain import Book
from everand_books.errors import OutputWriteError


def fixed_clock() -> datetime:
    return datetime(2026, 1, 2, tzinfo=UTC)


async def test_write_creates_epub_archive_named_after_the_title(book: Book, tmp_path: Path) -> None:
    output_dir = tmp_path / "missing" / "folder"

    path = await ZipEpubWriter(fixed_clock).write(book, output_dir)

    assert path.parent == output_dir
    assert path.name == "AB Title.epub"

    with ZipFile(path) as archive:
        first = archive.infolist()[0]
        assert (first.filename, first.compress_type) == ("mimetype", ZIP_STORED)
        assert archive.read("mimetype") == b"application/epub+zip"
        assert sorted(archive.namelist()) == [
            "META-INF/container.xml",
            "OEBPS/Images/9-fig.JPG",
            "OEBPS/Images/a.png",
            "OEBPS/Images/chapter_2-cover.jpg",
            "OEBPS/Images/cover.jpg",
            "OEBPS/Styles/styles.css",
            "OEBPS/Text/chapter_1.xhtml",
            "OEBPS/Text/chapter_2.xhtml",
            "OEBPS/Text/chapter_3.xhtml",
            "OEBPS/content.opf",
            "OEBPS/nav.xhtml",
            "mimetype",
        ]
        assert archive.read("OEBPS/Images/cover.jpg") == b"cover-bytes"
        assert archive.read("OEBPS/Styles/styles.css") == b".s1 {\n  color: red;\n}\n"
        chapter = archive.read("OEBPS/Text/chapter_2.xhtml")

    assert chapter.startswith(b"<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n")
    assert etree.QName(etree.fromstring(chapter)).localname == "html"


async def test_write_into_a_file_path_raises_output_write_error(book: Book, tmp_path: Path) -> None:
    not_a_folder = tmp_path / "taken"
    not_a_folder.write_text("")

    with pytest.raises(OutputWriteError, match="Could not save"):
        await ZipEpubWriter().write(book, not_a_folder)


async def test_write_without_cover_leaves_cover_out(book: Book, tmp_path: Path) -> None:
    chapters = tuple(replace(chapter, images=()) for chapter in book.chapters)

    path = await ZipEpubWriter().write(replace(book, chapters=chapters, cover=None), tmp_path)

    with ZipFile(path) as archive:
        assert not [name for name in archive.namelist() if "Images" in name]
