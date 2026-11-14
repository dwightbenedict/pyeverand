from collections.abc import Callable
from urllib.parse import parse_qs

import httpx
import pytest

from everand_books.adapters.everand import AccessTokenProvider, EverandSession
from everand_books.errors import (
    BookNotAccessibleError,
    EverandRequestError,
    UnexpectedResponseError,
)

type SessionFactory = Callable[[Callable[[httpx.Request], httpx.Response]], EverandSession]


class Everand:
    def __init__(self) -> None:
        self.csrf: httpx.Response = httpx.Response(200, json={"csrf_token": "csrf"})
        self.token_requests: list[httpx.Request] = []
        self.token_payload: dict[str, object] | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/csrf_token":
            return self.csrf
        self.token_requests.append(request)
        book_id = request.url.path.split("/")[2]
        number = len(self.token_requests)
        payload = self.token_payload or {"response": f"token-{book_id}-{number}", "error": None}
        return httpx.Response(200, json=payload)


@pytest.fixture
def everand() -> Everand:
    return Everand()


async def test_get_token_sends_csrf_token_with_access_token_request(
    make_session: SessionFactory, everand: Everand
) -> None:
    issued = await AccessTokenProvider(make_session(everand), 540).get_token("1")

    request = everand.token_requests[0]
    assert issued == "token-1-1"
    assert request.url.path == "/read2/1/access_token"
    assert (request.headers["X-Csrf-Token"], request.headers["X-Tried-Csrf"]) == ("csrf", "1")
    assert parse_qs(request.content.decode()) == {"doc_id": ["1"], "authenticity_token": ["csrf"]}


async def test_get_token_is_cached_per_book_until_it_expires(
    make_session: SessionFactory, everand: Everand
) -> None:
    now = 0.0
    provider = AccessTokenProvider(make_session(everand), ttl_seconds=540, clock=lambda: now)

    first = await provider.get_token("1")
    other_book = await provider.get_token("2")
    now = 539.0
    cached = await provider.get_token("1")
    now = 540.0
    refreshed = await provider.get_token("1")

    assert (first, other_book, cached, refreshed) == (
        "token-1-1",
        "token-2-2",
        "token-1-1",
        "token-1-3",
    )


async def test_get_token_without_csrf_token_raises(
    make_session: SessionFactory, everand: Everand
) -> None:
    everand.csrf = httpx.Response(200, json={"csrf_token": ""})
    with pytest.raises(UnexpectedResponseError, match="CSRF"):
        await AccessTokenProvider(make_session(everand), 540).get_token("1")


async def test_get_token_csrf_request_rejected_raises(
    make_session: SessionFactory, everand: Everand
) -> None:
    everand.csrf = httpx.Response(403)
    with pytest.raises(EverandRequestError, match="POST /csrf_token returned HTTP 403"):
        await AccessTokenProvider(make_session(everand), 540).get_token("1")


async def test_get_token_response_not_json_raises(
    make_session: SessionFactory, everand: Everand
) -> None:
    everand.csrf = httpx.Response(200, text="<html>sign in</html>")
    with pytest.raises(UnexpectedResponseError):
        await AccessTokenProvider(make_session(everand), 540).get_token("1")


@pytest.mark.parametrize(
    "payload", [{"response": None, "error": None}, {"response": "token", "error": "denied"}]
)
async def test_get_token_denied_raises_book_not_accessible(
    make_session: SessionFactory, everand: Everand, payload: dict[str, object]
) -> None:
    everand.token_payload = payload
    with pytest.raises(BookNotAccessibleError, match="Book 1 is not accessible"):
        await AccessTokenProvider(make_session(everand), 540).get_token("1")
