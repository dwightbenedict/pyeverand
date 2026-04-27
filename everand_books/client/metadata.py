from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from selectolax.parser import HTMLParser
import orjson

from everand_books.core.config import config
from everand_books.api.session import EverandSession
from everand_books.exceptions import BookNotFoundError, BookNotAccessibleError


def extract_between(text: str, left: str, right: str) -> str | None:
    left_index = text.find(left)

    # .find() returns -1 if the substring is not found
    if left_index == -1:
        return None

    start_index = left_index + len(left)
    right_index = text.find(right, start_index)

    if right_index == -1:
        return None

    return text[start_index:right_index].strip()


@retry(
    stop=stop_after_attempt(config.http.max_retries),
    wait=wait_exponential(max=config.http.max_retry_delay),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    reraise=True
)
async def _fetch_book_page(session: EverandSession, book_id: str) -> str:
    response = await session.get(f"/book/{book_id}")

    if response.status_code in {404, 410}:
        raise BookNotFoundError(f"Book with ID {book_id} not found.")

    response.raise_for_status()
    return response.text


def _is_book_accessible(html: HTMLParser) -> bool:
    read_btn = html.css_first('a[data-e2e="read-button"] span span')

    if not read_btn:
        return False

    return read_btn.text().strip().lower() in {"read now", "continue reading"}


def _parse_book_metadata(html: HTMLParser) -> dict[str, Any]:
    reader_script = html.css_first("#root > script")
    reader_json = extract_between(reader_script.text(), left="<!--", right="-->")
    reader_json = orjson.loads(reader_json)
    return reader_json["contentItem"]


async def get_book_metadata(session: EverandSession, book_id: str) -> dict[str, Any]:
    book_page = await _fetch_book_page(session, book_id)
    html = HTMLParser(book_page)

    if not _is_book_accessible(html):
        raise BookNotAccessibleError(f"Book with ID {book_id} is not accessible.")

    return _parse_book_metadata(html)