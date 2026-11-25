import pytest

from pyeverand.domain import parse_book_id
from pyeverand.errors import InvalidBookReferenceError


@pytest.mark.parametrize(
    "reference",
    [
        "696073235",
        "  696073235 ",
        "https://www.everand.com/book/696073235/Some-Title",
        "https://everand.com/book/696073235",
        "www.everand.com/read/696073235/Some-Title?x=1",
        "HTTPS://WWW.EVERAND.COM/book/696073235/",
    ],
)
def test_parse_book_id_accepts_id_or_book_link(reference: str) -> None:
    assert parse_book_id(reference) == "696073235"


@pytest.mark.parametrize(
    "reference",
    [
        "",
        "abc",
        "https://example.com/book/1",
        "https://everand.com.example.com/book/1",
        "https://www.everand.com/audiobook/1/Title",
        "https://www.everand.com/book/Title",
    ],
)
def test_parse_book_id_rejects_other_text(reference: str) -> None:
    with pytest.raises(InvalidBookReferenceError):
        parse_book_id(reference)
