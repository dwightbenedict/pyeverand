from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache

import httpx
from pydantic import ValidationError

from everand_books.adapters import (
    AccessTokenProvider,
    EverandBookSource,
    EverandSession,
    RequestPolicy,
    ZipEpubWriter,
)
from everand_books.config import Settings, load_settings
from everand_books.errors import ConfigurationError
from everand_books.services import DownloadBookService


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0"
    ),
    "Accept": "*/*",
}


@lru_cache
def get_settings() -> Settings:
    try:
        return load_settings()
    except ValidationError as err:
        fields = ", ".join(str(error["loc"][0]) for error in err.errors())
        msg = f"Missing or invalid settings: {fields}. Set them in the environment or in .env"
        raise ConfigurationError(msg) from err


def _build_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.base_url,
        headers=BROWSER_HEADERS,
        cookies={"_scribd_session": settings.session_token, "_scribd_user_id": settings.user_id},
        timeout=httpx.Timeout(settings.http_timeout_seconds),
        follow_redirects=True,
    )


@asynccontextmanager
async def open_download_service() -> AsyncGenerator[DownloadBookService]:
    settings = get_settings()
    policy = RequestPolicy(
        max_attempts=settings.http_max_attempts,
        max_retry_delay=settings.http_max_retry_delay_seconds,
        max_concurrency=settings.http_max_concurrency,
    )
    async with _build_client(settings) as client:
        session = EverandSession(client, policy)
        tokens = AccessTokenProvider(session, settings.access_token_ttl_seconds)
        yield DownloadBookService(EverandBookSource(session, tokens), ZipEpubWriter())
