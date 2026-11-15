import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass

import httpx

from everand_books.errors import EverandRequestError


RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class RequestPolicy:
    max_attempts: int = 3
    max_retry_delay: float = 10
    max_concurrency: int = 8


class EverandSession:
    def __init__(
        self,
        client: httpx.AsyncClient,
        policy: RequestPolicy,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._client = client
        self._policy = policy
        self._sleep = sleep
        self._slots = asyncio.Semaphore(policy.max_concurrency)

    async def get(self, url: str) -> httpx.Response:
        return await self._send(self._client.build_request("GET", url))

    async def post(
        self,
        url: str,
        form: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return await self._send(self._client.build_request("POST", url, data=form, headers=headers))

    async def _send(self, request: httpx.Request) -> httpx.Response:
        async with self._slots:
            for attempt in range(1, self._policy.max_attempts):
                response = await self._attempt(request)

                if response is not None:
                    return response

                await self._sleep(min(2.0**attempt, self._policy.max_retry_delay))

            return await self._final_attempt(request)

    async def _attempt(self, request: httpx.Request) -> httpx.Response | None:
        try:
            response = await self._client.send(request)
        except httpx.RequestError:
            return None

        return None if response.status_code in RETRYABLE_STATUS_CODES else response

    async def _final_attempt(self, request: httpx.Request) -> httpx.Response:
        try:
            return await self._client.send(request)
        except httpx.RequestError as err:
            msg = f"{request.method} {request.url.path} failed: {err}"
            raise EverandRequestError(msg) from err
