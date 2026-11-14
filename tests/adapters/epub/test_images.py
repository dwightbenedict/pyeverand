from dataclasses import replace

from everand_books.adapters.epub.images import plan_images
from everand_books.domain import Book, BookChapter, Chapter, ImageFile, NavChapter, SectionKind


def chapter(anchor: int, *images: ImageFile) -> BookChapter:
    return BookChapter(NavChapter("T", SectionKind.BODYMATTER, anchor), Chapter("T", ()), images)


def test_plan_images_same_picture_in_two_chapters_is_stored_once(book: Book) -> None:
    shared = ImageFile("logo.png", b"logo")
    chapters = (chapter(0, shared), chapter(1, shared))

    plan = plan_images(replace(book, chapters=chapters, cover=None))

    assert plan.files == {"logo.png": b"logo"}
    assert plan.names == {
        "chapter_1": {"logo.png": "logo.png"},
        "chapter_2": {"logo.png": "logo.png"},
    }


def test_plan_images_same_name_for_different_pictures_keeps_both(book: Book) -> None:
    chapters = (
        chapter(0, ImageFile("fig1.jpg", b"first")),
        chapter(1, ImageFile("fig1.jpg", b"second")),
    )

    plan = plan_images(replace(book, chapters=chapters, cover=None))

    assert plan.files == {"fig1.jpg": b"first", "chapter_2-fig1.jpg": b"second"}
    assert plan.names["chapter_2"] == {"fig1.jpg": "chapter_2-fig1.jpg"}


def test_plan_images_chapter_picture_named_like_the_cover_does_not_replace_it(book: Book) -> None:
    chapters = (chapter(0, ImageFile("cover.jpg", b"inside")),)

    plan = plan_images(replace(book, chapters=chapters, cover=b"cover"))

    assert plan.files == {"cover.jpg": b"cover", "chapter_1-cover.jpg": b"inside"}
