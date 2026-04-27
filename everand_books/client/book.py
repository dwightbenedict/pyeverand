from typing import Any

from everand_books.api.session import EverandSession
from everand_books.api.resource import fetch_resource


async def fetch_toc(session: EverandSession, book_id: str) -> list[dict[str, Any]]:
    resource = await fetch_resource(session, book_id, "toc.json")
    return resource.json()


async def fetch_styles(session: EverandSession, book_id: str) -> dict[str, Any]:
    resource = await fetch_resource(session, book_id, "styles.json")
    return resource.json()


async def fetch_chapter(session: EverandSession, book_id: str, chapter_num: int) -> dict[str, Any]:
    resource = await fetch_resource(session, book_id, f"chapters/{chapter_num}/contents.json")
    return resource.json()


