from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from everand_books.domain.blocks import ChapterBlock


class SectionKind(StrEnum):
    FRONTMATTER = "frontmatter"
    BODYMATTER = "bodymatter"
    BACKMATTER = "backmatter"


@dataclass(frozen=True, slots=True)
class BookMetadata:
    everand_id: str
    title: str
    language: str
    authors: tuple[str, ...] = ()
    subjects: tuple[str, ...] = ()
    publisher: str | None = None
    date_published: str | None = None
    description: str | None = None
    isbn: str | None = None
    cover_url: str | None = None


@dataclass(frozen=True, slots=True)
class NavChapter:
    title: str
    kind: SectionKind
    anchor: int

    @property
    def number(self) -> int:
        return self.anchor + 1

    @property
    def chapter_id(self) -> str:
        return f"chapter_{self.number}"


@dataclass(frozen=True, slots=True)
class Chapter:
    title: str
    blocks: tuple[ChapterBlock, ...]
    image_filenames: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ImageFile:
    filename: str
    content: bytes


@dataclass(frozen=True, slots=True)
class BookChapter:
    nav: NavChapter
    chapter: Chapter
    images: tuple[ImageFile, ...] = ()


@dataclass(frozen=True, slots=True)
class Book:
    metadata: BookMetadata
    stylesheet: Mapping[str, str]
    chapters: tuple[BookChapter, ...]
    cover: bytes | None = None
