from aiocache import cached
from aiocache.serializers import StringSerializer

from everand_books.core.config import config
from everand_books.api.session import EverandSession
from everand_books.exceptions import BookNotAccessibleError


async def _fetch_csrf_token(session: EverandSession) -> str | None:
    response = await session.post("/csrf_token")
    response.raise_for_status()
    data = response.json()
    csrf_token = data["csrf_token"]
    return csrf_token if csrf_token else None


async def _fetch_access_token(session: EverandSession, book_id: str, csrf_token: str) -> str:
    path = f"/read2/{book_id}/access_token"
    headers = {
        "X-Tried-Csrf": "1",
        "X-Csrf-Token": csrf_token
    }
    payload = {
        "doc_id": book_id,
        "authenticity_token": csrf_token
    }
    response = await session.post(path, headers=headers, data=payload)
    response.raise_for_status()
    data = response.json()
    access_token = data["response"]
    if not access_token or data["error"]:
        raise BookNotAccessibleError("Book is not accessible. It may be private or removed.")
    return access_token


@cached(
    ttl=config.everand.access_token_ttls,
    serializer=StringSerializer(),
    key="access_token:{0}"
)
async def get_access_token(book_id: str, session: EverandSession) -> str:
    csrf_token = await _fetch_csrf_token(session)
    access_token = await _fetch_access_token(session, book_id, csrf_token)
    return access_token