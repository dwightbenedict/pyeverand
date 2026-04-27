from lxml.etree import Element, SubElement

from everand_books.epub.builders.metadata_builder import MetadataBuilder
from everand_books.epub.builders.manifest_builder import ManifestBuilder
from everand_books.epub.builders.spine_builder import SpineBuilder


class PackageBuilder:
    def __init__(self) -> None:
        self._package = Element(
            "package",
            nsmap={
                None: "http://www.idpf.org/2007/opf",
                "dc": "http://purl.org/dc/elements/1.1/",
            },
            attrib={
                "version": "3.0",
            }
        )

        metadata_container = SubElement(
            self._package,
            "metadata",
            nsmap={
                "dc": "http://purl.org/dc/elements/1.1/",
                "opf": "http://www.idpf.org/2007/opf"
            }
        )
        manifest_container = SubElement(self._package, "manifest")
        spine_container = SubElement(self._package, "spine")

        self.metadata = MetadataBuilder(metadata_container)
        self.manifest = ManifestBuilder(manifest_container)
        self.spine = SpineBuilder(spine_container)

    def set_unique_identifier(self, identifier_id: str) -> None:
        self._package.set("unique-identifier", identifier_id)

    def build(self) -> Element:
        return self._package


