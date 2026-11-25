from datetime import datetime
from pathlib import PurePosixPath

from lxml.etree import Element, SubElement

from pyeverand.adapters.epub.element import XmlElement
from pyeverand.adapters.epub.images import plan_images
from pyeverand.adapters.epub.layout import (
    CONTENT_OPF_PATH,
    COVER_FILENAME,
    NAV_HREF,
    STYLESHEET_HREF,
    chapter_href,
    image_href,
)
from pyeverand.domain import Book, BookMetadata
from pyeverand.errors import UnsupportedImageFormatError


CONTAINER_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:container"
OPF_NAMESPACE = "http://www.idpf.org/2007/opf"
DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
XHTML_MEDIA_TYPE = "application/xhtml+xml"
COVER_ITEM_ID = "cover-image"

IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}


def _opf(tag: str) -> str:
    return f"{{{OPF_NAMESPACE}}}{tag}"


def _container(tag: str) -> str:
    return f"{{{CONTAINER_NAMESPACE}}}{tag}"


def build_container_document() -> XmlElement:
    container = Element(_container("container"), nsmap={None: CONTAINER_NAMESPACE}, version="1.0")
    rootfiles = SubElement(container, _container("rootfiles"))
    SubElement(
        rootfiles,
        _container("rootfile"),
        {"full-path": CONTENT_OPF_PATH, "media-type": "application/oebps-package+xml"},
    )
    return container


def _content_images(book: Book) -> list[str]:
    return sorted(set(plan_images(book).files) - {COVER_FILENAME})


def _dc(metadata: XmlElement, tag: str, text: str) -> XmlElement:
    element = SubElement(metadata, f"{{{DC_NAMESPACE}}}{tag}")
    element.text = text
    return element


def _add_identifier(package: XmlElement, metadata: XmlElement, book: BookMetadata) -> None:
    identifier_id, value = (
        ("isbn", f"urn:isbn:{book.isbn}") if book.isbn else ("everand-id", book.everand_id)
    )
    _dc(metadata, "identifier", value).set("id", identifier_id)
    package.set("unique-identifier", identifier_id)


def _add_optional(metadata: XmlElement, tag: str, text: str | None) -> None:
    if text:
        _dc(metadata, tag, text)


def _add_metadata(package: XmlElement, book: Book, modified: datetime) -> None:
    metadata = SubElement(package, _opf("metadata"))
    _add_identifier(package, metadata, book.metadata)
    _dc(metadata, "title", book.metadata.title).set("id", "main-title")

    for author in book.metadata.authors:
        _dc(metadata, "creator", author)

    _add_optional(metadata, "publisher", book.metadata.publisher)
    _add_optional(metadata, "date", book.metadata.date_published)

    for subject in book.metadata.subjects:
        _dc(metadata, "subject", subject)

    _dc(metadata, "language", book.metadata.language)
    SubElement(metadata, _opf("meta"), property="dcterms:modified").text = modified.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    _add_optional(metadata, "description", book.metadata.description)

    if book.cover is not None:
        SubElement(metadata, _opf("meta"), name="cover", content=COVER_ITEM_ID)


def _image_media_type(filename: str) -> str:
    suffix = PurePosixPath(filename).suffix.lower()

    try:
        return IMAGE_MEDIA_TYPES[suffix]
    except KeyError as err:
        msg = f"Image {filename} has a format EPUB does not support"
        raise UnsupportedImageFormatError(msg) from err


def _add_manifest(package: XmlElement, book: Book) -> None:
    manifest = SubElement(package, _opf("manifest"))

    def add_item(item_id: str, href: str, media_type: str) -> XmlElement:
        return SubElement(
            manifest, _opf("item"), {"id": item_id, "href": href, "media-type": media_type}
        )

    add_item("nav", NAV_HREF, XHTML_MEDIA_TYPE).set("properties", "nav")
    add_item("styles", STYLESHEET_HREF, "text/css")

    for chapter in book.chapters:
        add_item(chapter.nav.chapter_id, chapter_href(chapter.nav.chapter_id), XHTML_MEDIA_TYPE)

    if book.cover is not None:
        cover = add_item(COVER_ITEM_ID, image_href(COVER_FILENAME), "image/jpeg")
        cover.set("properties", "cover-image")

    # File names can start with a digit, which is not a valid XML id, so ids are numbered.
    for number, filename in enumerate(_content_images(book), start=1):
        add_item(f"image-{number}", image_href(filename), _image_media_type(filename))


def build_package_document(book: Book, modified: datetime) -> XmlElement:
    package = Element(
        _opf("package"),
        nsmap={None: OPF_NAMESPACE, "dc": DC_NAMESPACE},
        version="3.0",
    )
    _add_metadata(package, book, modified)
    _add_manifest(package, book)
    spine = SubElement(package, _opf("spine"))

    for chapter in book.chapters:
        SubElement(spine, _opf("itemref"), idref=chapter.nav.chapter_id)

    return package
