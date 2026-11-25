import asyncio
from collections.abc import Callable

import httpx
import pytest

from pyeverand.adapters.everand import EverandSession, RequestPolicy
from pyeverand.errors import EverandRequestError


type SessionFactory = Callable[[Callable[[httpx.Request], httpx.Response]], EverandSession]


class Script:
    """Answers each request with the next scripted outcome."""

    def __init__(self, *outcomes: int | Exception) -> None:
        self._outcomes = list(outcomes)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        outcome = self._outcomes.pop(0)

        if isinstance(outcome, Exception):
            raise outcome

        return httpx.Response(outcome)


async def test_get_success_returns_response_without_retry(
    make_session: SessionFactory, sleeps: list[float]
) -> None:
    script = Script(200)

    response = await make_session(script).get("/book/1")

    assert response.status_code == 200
    assert str(script.requests[0].url) == "https://everand.test/book/1"
    assert sleeps == []


async def test_post_sends_form_and_headers(make_session: SessionFactory) -> None:
    script = Script(200)

    await make_session(script).post("/token", form={"doc_id": "1"}, headers={"X-Csrf-Token": "c"})

    request = script.requests[0]
    assert (request.method, request.content, request.headers["X-Csrf-Token"]) == (
        "POST",
        b"doc_id=1",
        "c",
    )


async def test_get_client_error_is_returned_without_retry(make_session: SessionFactory) -> None:
    script = Script(404)

    response = await make_session(script).get("/book/1")

    assert response.status_code == 404
    assert len(script.requests) == 1


@pytest.mark.parametrize("failure", [httpx.ConnectError("down"), 503, 429])
async def test_get_transient_failure_is_retried(
    make_session: SessionFactory, sleeps: list[float], failure: int | Exception
) -> None:
    response = await make_session(Script(failure, 200)).get("/book/1")

    assert response.status_code == 200
    assert sleeps == [2.0]


@pytest.mark.parametrize("policy", [RequestPolicy(max_attempts=4, max_retry_delay=3)])
async def test_get_retry_delay_grows_up_to_the_maximum(
    make_session: SessionFactory, sleeps: list[float]
) -> None:
    await make_session(Script(503, 503, 503, 200)).get("/book/1")

    assert sleeps == [2.0, 3, 3]


async def test_get_server_error_on_last_attempt_is_returned(make_session: SessionFactory) -> None:
    response = await make_session(Script(503, 503, 503)).get("/book/1")

    assert response.status_code == 503


async def test_get_connection_failing_every_attempt_raises(make_session: SessionFactory) -> None:
    script = Script(*[httpx.ConnectError("down")] * 3)

    with pytest.raises(EverandRequestError, match=r"GET /book/1 failed: down"):
        await make_session(script).get("/book/1")


@pytest.mark.parametrize("policy", [RequestPolicy(max_concurrency=2)])
async def test_get_never_exceeds_concurrency_limit(policy: RequestPolicy) -> None:
    active = 0
    peak = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0)
        active -= 1
        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://e.test")
    session = EverandSession(client, policy)

    await asyncio.gather(*(session.get(f"/{number}") for number in range(6)))

    assert peak == 2
