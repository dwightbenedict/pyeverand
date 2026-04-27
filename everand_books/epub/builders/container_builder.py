from lxml.etree import Element, SubElement

from everand_books.epub.layout import CONTENT_OPF_PATH


class ContainerBuilder:
    def __init__(self) -> None:
        self._container = Element(
            "container",
            attrib={
                "version": "1.0",
                "xmlns": "urn:oasis:names:tc:opendocument:xmlns:container",
            },
        )

        rootfiles_container = SubElement(self._container, "rootfiles")
        SubElement(
            rootfiles_container,
            "rootfile",
            attrib={
                "full-path": CONTENT_OPF_PATH,
                "media-type": "application/oebps-package+xml",
            },
        )

    def build(self) -> Element:
        return self._container

