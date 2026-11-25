from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

import httpx
from pydantic import ValidationError

from everand_books.adapters import (
    AccessTokenProvider,
    EnvFileCredentialStore,
    EverandBookSource,
    EverandSession,
    LocalSavedBooks,
    RequestPolicy,
    SystemFolderDialog,
    ZipEpubWriter,
)
from everand_books.config import ENV_FILE, AppOptions, Settings, load_app_options, load_settings
from everand_books.domain import Credentials, parse_credentials
from everand_books.errors import (
    ConfigurationError,
    CredentialsRequiredError,
    InvalidCredentialsError,
)
from everand_books.services import (
    ChooseFolderService,
    DownloadBookService,
    DownloadQueue,
    SaveCredentialsService,
)


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0"
    ),
    "Accept": "*/*",
}


def _configuration_error(err: ValidationError) -> ConfigurationError:
    fields = ", ".join(str(error["loc"][0]) for error in err.errors())
    msg = f"Missing or invalid settings: {fields}. Set them in the environment or in .env"
    return ConfigurationError(msg)


def get_app_options() -> AppOptions:
    try:
        return load_app_options()

    except ValidationError as err:
        raise _configuration_error(err) from err


@lru_cache
def get_settings() -> Settings:
    try:
        return load_settings()

    except ValidationError as err:
        raise _configuration_error(err) from err


def _read_credentials() -> Credentials:
    settings = get_settings()
    return parse_credentials(settings.session_token, settings.user_id)


def get_saved_credentials() -> Credentials:
    """Return empty values when there are no usable cookies, for a form to start from."""

    try:
        return _read_credentials()

    except (ConfigurationError, InvalidCredentialsError):
        return Credentials(session_token="", user_id="")


def require_credentials() -> None:
    try:
        _read_credentials()

    except (ConfigurationError, InvalidCredentialsError) as err:
        raise CredentialsRequiredError(str(err)) from err


@lru_cache
def get_download_queue() -> DownloadQueue:
    return DownloadQueue(open_download_service, LocalSavedBooks(), require_credentials)


@lru_cache
def get_choose_folder_service() -> ChooseFolderService:
    return ChooseFolderService(SystemFolderDialog())


def get_save_credentials_service() -> SaveCredentialsService:
    # Clearing the cache makes the next download read the new cookies.
    return SaveCredentialsService(EnvFileCredentialStore(Path(ENV_FILE)), get_settings.cache_clear)


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
