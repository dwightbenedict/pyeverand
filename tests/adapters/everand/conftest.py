from collections.abc import Callable

import httpx
import pytest

from everand_books.adapters.everand import EverandSession, RequestPolicy


type Handler = Callable[[httpx.Request], httpx.Response]
type SessionFactory = Callable[[Handler], EverandSession]


@pytest.fixture
def sleeps() -> list[float]:
    return []


@pytest.fixture
def policy() -> RequestPolicy:
    return RequestPolicy()


@pytest.fixture
def make_session(sleeps: list[float], policy: RequestPolicy) -> SessionFactory:
    async def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    def build(handler: Handler) -> EverandSession:
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://everand.test",
        )
        return EverandSession(client, policy, record_sleep)

    return build
