from typing import Self

from lxml.etree import Element, SubElement

from everand_books.models.nav_chapter import NavChapter


class SpineBuilder:
    def __init__(self, container: Element) -> None:
        self.container = container

    def add_chapters(self, nav_chapters: list[NavChapter]) -> Self:
        for chapter in nav_chapters:
            SubElement(
                self.container,
                "itemref",
                attrib={
                    "idref": chapter.id,
                    "properties": chapter.type,
                }
            )

        return self
