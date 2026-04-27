from typing import Self
from pathlib import Path

from lxml.etree import Element, SubElement

from everand_books.models.nav_chapter import NavChapter
from everand_books.epub.layout import NAV_HREF, STYLESHEET_HREF, IMAGES_HREF, chapter_href
from everand_books.exceptions import UnsupportedEPUBImageFormatError



EPUB_SAFE_IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}


class ManifestBuilder:
    def __init__(self, container: Element) -> None:
        self.container = container

        self._add_item(
            {
                "id": "nav",
                "href": NAV_HREF,
                "media-type": "application/xhtml+xml",
                "properties": "nav"
            }
        )

        self._add_item(
            {
                "id": "styles",
                "href": STYLESHEET_HREF,
                "media-type": "text/css",
            }
        )

    def _add_item(self, attributes: dict[str, str] | None = None) -> None:
        SubElement(self.container, "item", attrib=attributes)

    def add_chapters(self, nav_chapters: list[NavChapter]) -> Self:
        for chapter in nav_chapters:
            self._add_item(
                {
                    "id": chapter.id,
                    "href": chapter_href(chapter.id),
                    "media-type": "application/xhtml+xml",
                }
            )
        return self

    def add_cover_image(self) -> Self:
        self._add_item(
            {
                "id": "cover-image",
                "href": f"{IMAGES_HREF}/cover.jpg",
                "media-type": "image/jpeg",
                "properties": "cover-image"
            }
        )
        return self

    def add_images(self, image_files: list[Path]) -> Self:
        for file in image_files:
            if file.stem == "cover":
                continue

            suffix = file.suffix.lower()

            if suffix not in EPUB_SAFE_IMAGE_MEDIA_TYPES:
                raise UnsupportedEPUBImageFormatError(f"Unsupported media type for image: {suffix}")

            self._add_item(
                {
                    "id": file.stem,
                    "href": f"{IMAGES_HREF}/{file.name}",
                    "media-type": EPUB_SAFE_IMAGE_MEDIA_TYPES[suffix]
                }
            )