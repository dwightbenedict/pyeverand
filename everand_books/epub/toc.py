from lxml.etree import Element

from everand_books.epub.builders.toc_builder import TOCBuilder
from everand_books.models.nav_chapter import NavChapter


def build_toc(nav_chapters: list[NavChapter]) -> Element:
    toc_builder = TOCBuilder()
    toc_builder.add_chapters(nav_chapters)
    return toc_builder.build()