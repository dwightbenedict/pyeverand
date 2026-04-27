from typing import Self

from lxml.etree import Element, SubElement


class MetadataBuilder:
    def __init__(self, container: Element) -> None:
        self.container = container
        self._namespace = "{http://purl.org/dc/elements/1.1/}"

    def _add(
            self,
            tag: str,
            text: str | None = None,
            attributes: dict[str, str] | None = None
    ) -> None:
        element = SubElement(self.container, tag, attrib=attributes)

        if text is not None:
            element.text = text

    def _add_dc(
            self,
            tag: str,
            text: str | None = None,
            attributes: dict[str, str] | None = None
    ) -> None:
        self._add(f"{self._namespace}{tag}", text, attributes)

    def _add_meta(
            self,
            tag: str,
            text: str | None = None,
            attributes: dict[str, str] | None = None
    ) -> None:
        self._add(tag, text, attributes)

    def add_identifier(self, identifier_id: str, identifier: str) -> Self:
        self._add_dc(
            "identifier",
            identifier,
            attributes={"id": identifier_id},
        )
        return self

    def add_isbn(self, isbn: str) -> Self:
        self.add_identifier("isbn", f"isbn:{isbn}")
        return self

    def add_title(self, title: str) -> Self:
        self._add_dc(
            "title",
            title,
            attributes={
                "id": "main-title"
            }
        )
        return self

    def add_description(self, description: str) -> Self:
        self._add_dc(
            "description",
            description
        )
        return self

    def add_authors(self, authors: list[str]) -> Self:
        for author in authors:
            self._add_dc(
                "creator",
                author
            )
        return self

    def add_publisher(self, publisher: str) -> Self:
        self._add_dc(
            "publisher",
            publisher
        )
        return self

    def add_date_published(self, date_published: str) -> Self:
        self._add_dc(
            "date",
            date_published
        )
        return self

    def add_subjects(self, subjects: list[str]) -> Self:
        for subject in subjects:
            self._add_dc(
                "subject",
                subject
            )
        return self

    def add_language(self, language: str) -> Self:
        self._add_dc(
            "language",
            language
        )
        return self

    def add_date_modified(self, date_modified: str) -> Self:
        self._add_meta(
            "meta",
            date_modified,
            attributes={
                "property": "dcterms:modified"
            }
        )
        return self

    def add_cover_image(self) -> Self:
        self._add_meta(
            "meta",
            attributes={
                "name": "cover",
                "content": "cover-image"
            }
        )
        return self