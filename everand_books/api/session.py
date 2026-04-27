import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from everand_books.core.config import config


BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Accept": "*/*"
}


class EverandSession:
    """
    Asynchronous authenticated session for the Everand API.

    This session initializes an httpx.AsyncClient with the required
    Everand authentication cookies, default headers, and base URL.

    This only exposes `get` and `post` verbs for making requests.

    The session may be used directly or as an async context manager.
    When used without a context manager, `close()` must be called
    manually to release network resources.
    """

    def __init__(self, session_token: str, user_id: str):
        self.session_token = session_token
        self.user_id = user_id

        self._client = httpx.AsyncClient(
            base_url=config.everand.base_url,
            headers=BASE_HEADERS,
            cookies={
                "_scribd_session": self.session_token,
                "_scribd_user_id": self.user_id
            },
            timeout=httpx.Timeout(config.http.timeout),
            follow_redirects=True,
        )

    async def __aenter__(self) -> "EverandSession":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._client.aclose()

    @retry(
        stop=stop_after_attempt(config.http.max_retries),
        wait=wait_exponential(max=config.http.max_retry_delay),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True
    )
    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        response = await self._client.request(method, path, **kwargs)
        return response

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self._request("POST", path, **kwargs)

    async def close(self) -> None:
        await self._client.aclose()