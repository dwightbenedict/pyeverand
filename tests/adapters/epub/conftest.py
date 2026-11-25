import pytest

from pyeverand.domain import (
    Book,
    BookChapter,
    BookMetadata,
    Chapter,
    ImageFile,
    NavChapter,
    SectionKind,
    TextBlock,
)


@pytest.fixture
def book() -> Book:
    front = BookChapter(NavChapter("Front", SectionKind.FRONTMATTER, 0), Chapter("Front", ()))
    body = BookChapter(
        NavChapter("One", SectionKind.BODYMATTER, 1),
        Chapter("One", (TextBlock(type="text"),)),
        (ImageFile("9-fig.JPG", b"fig"), ImageFile("a.png", b"png"), ImageFile("cover.jpg", b"x")),
    )
    back = BookChapter(
        NavChapter("Back", SectionKind.BACKMATTER, 2),
        Chapter("Back", ()),
        (ImageFile("a.png", b"png"),),
    )
    metadata = BookMetadata(
        everand_id="42",
        title="A/B: Title?",
        language="en",
        authors=("Ann", "Bo"),
        subjects=("history",),
        publisher="Press",
        date_published="2020-01-02",
        description="About",
        isbn="9781",
    )
    return Book(metadata, {"s1": "color: red"}, (front, body, back), cover=b"cover-bytes")
