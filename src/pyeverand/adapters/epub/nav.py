from collections.abc import Iterable

from pyeverand.adapters.epub.element import XmlElement
from pyeverand.adapters.epub.layout import chapter_href
from pyeverand.adapters.epub.rendering import EPUB_TYPE, E
from pyeverand.domain import NavChapter


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
