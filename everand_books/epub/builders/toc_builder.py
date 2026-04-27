from typing import Self

from lxml.etree import Element, SubElement

from everand_books.models.nav_chapter import NavChapter
from everand_books.epub.layout import chapter_href


class TOCBuilder:
    def __init__(self, language: str = "en") -> None:
        self._html = Element(
            "html",
            nsmap={
                None: "http://www.w3.org/1999/xhtml",
                "epub": "http://www.idpf.org/2007/ops"
            },
            attrib={
                "{http://www.w3.org/XML/1998/namespace}lang": language,
                "lang": language,
            }
        )

        self._head = SubElement(self._html, "head")

        SubElement(
            self._head, "meta", attrib={"charset": "UTF-8"}
        )

        title_element = SubElement(self._head, "title")
        title_element.text = "Table of Contents"

        body_container = SubElement(self._html, "body")
        self._nav = SubElement(
            body_container,
            "nav",
            attrib={
                "{http://www.idpf.org/2007/ops}type": "toc",
                "id": "toc"
            }
        )

    def add_chapters(self, nav_chapters: list[NavChapter]) -> Self:
        chapters_list = SubElement(self._nav, "ol")

        for chapter in nav_chapters:
            item = SubElement(chapters_list, "li")
            a = SubElement(item, "a", href=chapter_href(chapter.id))
            a.text = chapter.title

        return self

    def build(self) -> Element:
        return self._html
