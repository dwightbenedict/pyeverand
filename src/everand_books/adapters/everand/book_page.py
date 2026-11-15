from pydantic import BaseModel, Field, TypeAdapter
from selectolax.lexbor import LexborHTMLParser

from everand_books.adapters.everand.responses import parse_json
from everand_books.domain import BookMetadata
from everand_books.errors import BookNotAccessibleError, UnexpectedResponseError


READ_BUTTON_LABELS = frozenset({"read now", "continue reading"})


class _Named(BaseModel):
    name: str


class _ContentItem(BaseModel):
    id: int | str
    title: str
    language: str
    contributors: list[_Named] = Field(default_factory=lambda: [])
    publisher: _Named | None = None
    release_date: str | None = Field(default=None, alias="releaseDate")
    description: str | None = None
    isbn: int | str | None = None
    themes: list[str] | None = None
    tropes: list[str] | None = None
    retina_image_url: str | None = Field(default=None, alias="retinaImageUrl")
    image_url: str | None = Field(default=None, alias="imageUrl")


class _ReaderState(BaseModel):
    content_item: _ContentItem = Field(alias="contentItem")


_READER_STATE = TypeAdapter(_ReaderState)


def _is_accessible(page: LexborHTMLParser) -> bool:
    read_button = page.css_first('a[data-e2e="read-button"] span span')
    return read_button is not None and read_button.text().strip().lower() in READ_BUTTON_LABELS


def _reader_state_json(page: LexborHTMLParser) -> str:
    # The page embeds its state as JSON inside an HTML comment in the first script under #root.
    script = page.css_first("#root > script")
    _, opened, rest = (script.text() if script is not None else "").partition("<!--")
    payload, closed, _ = rest.partition("-->")

    if not opened or not closed:
        msg = "The book page does not contain the embedded book details"
        raise UnexpectedResponseError(msg)

    return payload.strip()


def _to_metadata(item: _ContentItem) -> BookMetadata:
    return BookMetadata(
        everand_id=str(item.id),
        title=item.title,
        language=item.language,
        authors=tuple(contributor.name for contributor in item.contributors),
        subjects=(*(item.themes or ()), *(item.tropes or ())),
        publisher=item.publisher.name if item.publisher else None,
        date_published=item.release_date,
        description=item.description,
        isbn=str(item.isbn) if item.isbn else None,
        cover_url=item.retina_image_url or item.image_url,
    )


def parse_book_page(page_html: str, book_id: str) -> BookMetadata:
    page = LexborHTMLParser(page_html)

    if not _is_accessible(page):
        msg = f"Book with ID {book_id} is not accessible."
        raise BookNotAccessibleError(msg)

    state = parse_json(_reader_state_json(page), _READER_STATE)
    return _to_metadata(state.content_item)
