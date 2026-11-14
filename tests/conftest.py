from pathlib import Path

import pytest

from everand_books.wiring import get_settings

SETTING_VARIABLES = (
    "EVERAND_BOOKS_SESSION_TOKEN",
    "EVERAND_BOOKS_USER_ID",
    "EVERAND_BOOKS_BASE_URL",
    "EVERAND_BOOKS_ACCESS_TOKEN_TTL_SECONDS",
    "EVERAND_BOOKS_HTTP_TIMEOUT_SECONDS",
    "EVERAND_BOOKS_HTTP_MAX_ATTEMPTS",
    "EVERAND_BOOKS_HTTP_MAX_RETRY_DELAY_SECONDS",
    "EVERAND_BOOKS_HTTP_MAX_CONCURRENCY",
    "EVERAND__SESSION_TOKEN",
    "EVERAND__USER_ID",
    "EVERAND__BASE_URL",
    "EVERAND__ACCESS_TOKEN_TTLS",
    "HTTP__TIMEOUT",
    "HTTP__MAX_RETRIES",
    "HTTP__MAX_RETRY_DELAY",
)


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep the developer's own environment and .env file out of every test."""
    for name in SETTING_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
