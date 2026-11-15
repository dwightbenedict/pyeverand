from collections.abc import Iterable

from everand_books.adapters.epub.element import XmlElement
from everand_books.adapters.epub.layout import chapter_href
from everand_books.adapters.epub.rendering import EPUB_TYPE, E
from everand_books.domain import NavChapter


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def build_nav_document(toc: Iterable[NavChapter], language: str) -> XmlElement:
    entries = (E.li(E.a(chapter.title, href=chapter_href(chapter.chapter_id))) for chapter in toc)
    nav = E.nav(E.ol(*entries), id="toc")
    nav.set(EPUB_TYPE, "toc")
    document = E.html(
        E.head(E.meta(charset="UTF-8"), E.title("Table of Contents")),
        E.body(nav),
        lang=language,
    )
    document.set(XML_LANG, language)
    return document
