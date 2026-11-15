import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, TypeAdapter

from everand_books.adapters.everand.responses import ensure_ok, parse_json
from everand_books.adapters.everand.session import EverandSession
from everand_books.errors import BookNotAccessibleError, UnexpectedResponseError


class _CsrfPayload(BaseModel):
    csrf_token: str | None = None


class _AccessTokenPayload(BaseModel):
    response: str | None = None
    error: object = None


_CSRF = TypeAdapter(_CsrfPayload)
_ACCESS_TOKEN = TypeAdapter(_AccessTokenPayload)


@dataclass(frozen=True, slots=True)
class _CachedToken:
    value: str
    expires_at: float


class AccessTokenProvider:
    def __init__(
        self,
        session: EverandSession,
        ttl_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._session = session
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._tokens: dict[str, _CachedToken] = {}
        # Chapters are fetched concurrently; the lock makes them share one token request.
        self._lock = asyncio.Lock()

    async def get_token(self, book_id: str) -> str:
        async with self._lock:
            cached = self._tokens.get(book_id)

            if cached is not None and cached.expires_at > self._clock():
                return cached.value

            token = await self._fetch_access_token(book_id, await self._fetch_csrf_token())
            self._tokens[book_id] = _CachedToken(token, self._clock() + self._ttl_seconds)
            return token

    async def _fetch_csrf_token(self) -> str:
        response = ensure_ok(await self._session.post("/csrf_token"))
        csrf_token = parse_json(response.content, _CSRF).csrf_token

        if not csrf_token:
            msg = "Everand returned no CSRF token; the session cookies may be invalid or expired"
            raise UnexpectedResponseError(msg)

        return csrf_token

    async def _fetch_access_token(self, book_id: str, csrf_token: str) -> str:
        response = await self._session.post(
            f"/read2/{book_id}/access_token",
            form={"doc_id": book_id, "authenticity_token": csrf_token},
            headers={"X-Tried-Csrf": "1", "X-Csrf-Token": csrf_token},
        )
        payload = parse_json(ensure_ok(response).content, _ACCESS_TOKEN)

        if not payload.response or payload.error:
            msg = f"Book {book_id} is not accessible. It may be private or removed."
            raise BookNotAccessibleError(msg)

        return payload.response
