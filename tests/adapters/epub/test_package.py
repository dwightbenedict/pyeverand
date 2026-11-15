from dataclasses import replace
from datetime import UTC, datetime

import pytest

from everand_books.adapters.epub.element import XmlElement
from everand_books.adapters.epub.package import build_container_document, build_package_document
from everand_books.domain import Book, BookChapter, Chapter, ImageFile, NavChapter, SectionKind
from everand_books.errors import UnsupportedImageFormatError


MODIFIED = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
NAMESPACES = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}


def texts(package: XmlElement, path: str) -> list[str | None]:
    return [element.text for element in package.iterfind(path, NAMESPACES)]


def manifest(package: XmlElement) -> dict[str, tuple[str | None, str | None]]:
    return {
        str(item.get("id")): (item.get("href"), item.get("media-type"))
        for item in package.iterfind("opf:manifest/opf:item", NAMESPACES)
    }


def test_build_container_document_points_at_package_file() -> None:
    rootfile = build_container_document()[0][0]
    assert rootfile.get("full-path") == "OEBPS/content.opf"


def test_build_package_document_writes_all_metadata(book: Book) -> None:
    package = build_package_document(book, MODIFIED)

    assert package.get("unique-identifier") == "isbn"
    assert texts(package, "opf:metadata/dc:identifier") == ["urn:isbn:9781"]
    assert texts(package, "opf:metadata/dc:title") == ["A/B: Title?"]
    assert texts(package, "opf:metadata/dc:creator") == ["Ann", "Bo"]
    assert texts(package, "opf:metadata/dc:publisher") == ["Press"]
    assert texts(package, "opf:metadata/dc:date") == ["2020-01-02"]
    assert texts(package, "opf:metadata/dc:subject") == ["history"]
    assert texts(package, "opf:metadata/dc:language") == ["en"]
    assert texts(package, "opf:metadata/dc:description") == ["About"]
    assert texts(package, "opf:metadata/opf:meta[@property='dcterms:modified']") == [
        "2026-01-02T03:04:05Z"
    ]
    assert package.find("opf:metadata/opf:meta[@name='cover']", NAMESPACES) is not None


def test_build_package_document_without_optional_metadata_omits_it(book: Book) -> None:
    metadata = replace(
        book.metadata, isbn=None, publisher=None, date_published=None, description=None
    )

    package = build_package_document(replace(book, metadata=metadata, cover=None), MODIFIED)

    assert package.get("unique-identifier") == "everand-id"
    assert texts(package, "opf:metadata/dc:identifier") == ["42"]
    assert texts(package, "opf:metadata/dc:publisher") == []
    assert texts(package, "opf:metadata/dc:date") == []
    assert texts(package, "opf:metadata/dc:description") == []
    assert package.find("opf:metadata/opf:meta[@name='cover']", NAMESPACES) is None
    assert "cover-image" not in manifest(package)


def test_build_package_document_lists_each_file_once_with_valid_ids(book: Book) -> None:
    package = build_package_document(book, MODIFIED)

    assert manifest(package) == {
        "nav": ("nav.xhtml", "application/xhtml+xml"),
        "styles": ("Styles/styles.css", "text/css"),
        "chapter_1": ("Text/chapter_1.xhtml", "application/xhtml+xml"),
        "chapter_2": ("Text/chapter_2.xhtml", "application/xhtml+xml"),
        "chapter_3": ("Text/chapter_3.xhtml", "application/xhtml+xml"),
        "cover-image": ("Images/cover.jpg", "image/jpeg"),
        "image-1": ("Images/9-fig.JPG", "image/jpeg"),
        "image-2": ("Images/a.png", "image/png"),
        "image-3": ("Images/chapter_2-cover.jpg", "image/jpeg"),
    }
    properties = {
        item.get("id"): item.get("properties")
        for item in package.iterfind("opf:manifest/opf:item[@properties]", NAMESPACES)
    }
    assert properties == {"nav": "nav", "cover-image": "cover-image"}


def test_build_package_document_spine_lists_chapters_in_order(book: Book) -> None:
    package = build_package_document(book, MODIFIED)
    spine = [dict(item.attrib) for item in package.iterfind("opf:spine/opf:itemref", NAMESPACES)]
    assert spine == [{"idref": "chapter_1"}, {"idref": "chapter_2"}, {"idref": "chapter_3"}]


def test_build_package_document_unsupported_image_format_raises(book: Book) -> None:
    chapter = BookChapter(
        NavChapter("One", SectionKind.BODYMATTER, 0),
        Chapter("One", ()),
        (ImageFile("photo.webp", b""),),
    )

    with pytest.raises(UnsupportedImageFormatError, match=r"photo\.webp"):
        build_package_document(replace(book, chapters=(chapter,)), MODIFIED)
