from collections.abc import Mapping
from dataclasses import dataclass

from everand_books.adapters.epub.layout import COVER_FILENAME
from everand_books.domain import Book


@dataclass(frozen=True, slots=True)
class ImagePlan:
    files: Mapping[str, bytes]
    """Archive file name -> content, the cover included."""
    names: Mapping[str, Mapping[str, str]]
    """Chapter id -> the name a chapter uses for an image -> its archive file name."""


def plan_images(book: Book) -> ImagePlan:
    """All chapters share one Images folder.

    Everand names images per chapter, so two chapters (or a chapter and the cover) can use one
    name for different pictures. The later one is then stored under a chapter-prefixed name.
    """
    files: dict[str, bytes] = {}

    if book.cover is not None:
        files[COVER_FILENAME] = book.cover

    names: dict[str, dict[str, str]] = {}

    for chapter in book.chapters:
        chapter_names = names.setdefault(chapter.nav.chapter_id, {})

        for image in chapter.images:
            name = image.filename

            if files.setdefault(name, image.content) != image.content:
                name = f"{chapter.nav.chapter_id}-{image.filename}"
                files[name] = image.content

            chapter_names[image.filename] = name

    return ImagePlan(files, names)
