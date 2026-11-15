import json
import re
from collections.abc import Mapping
from http import HTTPStatus

import httpx
from pydantic import BaseModel, TypeAdapter

from everand_books.adapters.everand.auth import AccessTokenProvider
from everand_books.adapters.everand.book_page import parse_book_page
from everand_books.adapters.everand.cover import cover_as_jpeg
from everand_books.adapters.everand.responses import ensure_ok, parse_json
from everand_books.adapters.everand.session import EverandSession
from everand_books.domain import BookMetadata, Chapter, ChapterBlock, NavChapter, SectionKind
from everand_books.errors import BookNotFoundError


IMAGE_PATH_PATTERN = re.compile(r"images/([A-Za-z0-9._-]+)")
MISSING_BOOK_STATUS_CODES = frozenset({HTTPStatus.NOT_FOUND, HTTPStatus.GONE})
# styles.json maps class names to declarations, plus one "styles" entry that is not a class.
NON_CLASS_STYLE_KEY = "styles"

SECTION_KINDS = {
    "frontmatter": SectionKind.FRONTMATTER,
    "content": SectionKind.BODYMATTER,
    "backmatter": SectionKind.BACKMATTER,
}


class _TocEntry(BaseModel):
    title: str
    type: str
    anchor: int


class _ChapterPayload(BaseModel):
    title: str
    blocks: tuple[ChapterBlock, ...] = ()


_TOC = TypeAdapter(list[_TocEntry])
_STYLES = TypeAdapter(dict[str, object])
_CHAPTER = TypeAdapter(_ChapterPayload)
_JSON = TypeAdapter[object](object)


def _image_filenames(chapter_json: bytes) -> tuple[str, ...]:
    # Re-serialising undoes JSON escaping such as "images\/a.png" before the paths are searched.
    text = json.dumps(parse_json(chapter_json, _JSON))
    return tuple(sorted(set(IMAGE_PATH_PATTERN.findall(text))))


class EverandBookSource:
    def __init__(self, session: EverandSession, tokens: AccessTokenProvider) -> None:
        self._session = session
        self._tokens = tokens

    async def fetch_metadata(self, book_id: str) -> BookMetadata:
        response = await self._session.get(f"/book/{book_id}")

        if response.status_code in MISSING_BOOK_STATUS_CODES:
            msg = f"Book with ID {book_id} not found."
            raise BookNotFoundError(msg)

        return parse_book_page(ensure_ok(response).text, book_id)

    async def fetch_toc(self, book_id: str) -> list[NavChapter]:
        response = await self._fetch_resource(book_id, "toc.json")
        return [
            NavChapter(
                entry.title, SECTION_KINDS.get(entry.type, SectionKind.BODYMATTER), entry.anchor
            )
            for entry in parse_json(response.content, _TOC)
        ]

    async def fetch_stylesheet(self, book_id: str) -> Mapping[str, str]:
        response = await self._fetch_resource(book_id, "styles.json")
        return {
            class_name: declarations
            for class_name, declarations in parse_json(response.content, _STYLES).items()
            if class_name != NON_CLASS_STYLE_KEY and isinstance(declarations, str)
        }

    async def fetch_chapter(self, book_id: str, number: int) -> Chapter:
        response = await self._fetch_resource(book_id, f"chapters/{number}/contents.json")
        payload = parse_json(response.content, _CHAPTER)
        return Chapter(payload.title, payload.blocks, _image_filenames(response.content))

    async def fetch_chapter_image(self, book_id: str, number: int, filename: str) -> bytes:
        response = await self._fetch_resource(book_id, f"chapters/{number}/images/{filename}")
        return response.content

    async def fetch_cover(self, cover_url: str) -> bytes:
        response = ensure_ok(await self._session.get(cover_url))
        return cover_as_jpeg(response.content, response.headers.get("Content-Type", ""))

    async def _fetch_resource(self, book_id: str, resource_path: str) -> httpx.Response:
        token = await self._tokens.get_token(book_id)
        return ensure_ok(
            await self._session.get(f"/scepub/{book_id}/{resource_path}?token={token}")
        )
