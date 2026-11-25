import json

import pytest

from pyeverand.adapters.everand.book_page import parse_book_page
from pyeverand.domain import BookMetadata
from pyeverand.errors import BookNotAccessibleError, UnexpectedResponseError


CONTENT_ITEM: dict[str, object] = {
    "id": 42,
    "title": "Title",
    "language": "en",
    "contributors": [{"name": "Ann"}, {"name": "Bo"}],
    "publisher": {"name": "Press"},
    "releaseDate": "2020-01-02",
    "description": "About",
    "isbn": 9781,
    "themes": ["history"],
    "tropes": ["quest"],
    "retinaImageUrl": None,
    "imageUrl": "https://img/cover.jpg",
    "ignored": True,
}


def page(script: str, button: str = "Read now") -> str:
    return (
        f'<html><body><a data-e2e="read-button"><span><span> {button} </span></span></a>'
        f'<div id="root"><script>{script}</script></div></body></html>'
    )


def state(content_item: dict[str, object]) -> str:
    return f"<!-- {json.dumps({'contentItem': content_item})} -->"


def test_parse_book_page_readable_book_returns_metadata() -> None:
    assert parse_book_page(page(state(CONTENT_ITEM)), "42") == BookMetadata(
        everand_id="42",
        title="Title",
        language="en",
        authors=("Ann", "Bo"),
        subjects=("history", "quest"),
        publisher="Press",
        date_published="2020-01-02",
        description="About",
        isbn="9781",
        cover_url="https://img/cover.jpg",
    )


def test_parse_book_page_sparse_details_leave_optional_fields_empty() -> None:
    sparse: dict[str, object] = {"id": "42", "title": "Title", "language": "en"}

    metadata = parse_book_page(page(state(sparse), button="Continue Reading"), "42")

    assert metadata == BookMetadata(everand_id="42", title="Title", language="en")


@pytest.mark.parametrize(
    "html",
    [page(state(CONTENT_ITEM), button="Start your free trial"), "<html><body></body></html>"],
)
def test_parse_book_page_without_read_button_raises_not_accessible(html: str) -> None:
    with pytest.raises(BookNotAccessibleError, match="42"):
        parse_book_page(html, "42")


@pytest.mark.parametrize("script", ["", "<!-- {}", "var state = 1;"])
def test_parse_book_page_without_embedded_details_raises(script: str) -> None:
    with pytest.raises(UnexpectedResponseError, match="embedded book details"):
        parse_book_page(page(script), "42")


def test_parse_book_page_without_script_raises() -> None:
    html = '<a data-e2e="read-button"><span><span>Read now</span></span></a>'

    with pytest.raises(UnexpectedResponseError, match="embedded book details"):
        parse_book_page(html, "42")


def test_parse_book_page_details_in_unexpected_shape_raises() -> None:
    with pytest.raises(UnexpectedResponseError, match="unexpected shape"):
        parse_book_page(page(state({"id": 42})), "42")
