from lxml.etree import Element

from everand_books.epub.builders.container_builder import ContainerBuilder


def build_container() -> Element:
    return ContainerBuilder().build()