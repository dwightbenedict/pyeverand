import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from pyeverand.wiring import get_settings


SETTING_VARIABLES = (
    "PYEVERAND_SESSION_TOKEN",
    "PYEVERAND_USER_ID",
    "PYEVERAND_BASE_URL",
    "PYEVERAND_ACCESS_TOKEN_TTL_SECONDS",
    "PYEVERAND_HTTP_TIMEOUT_SECONDS",
    "PYEVERAND_HTTP_MAX_ATTEMPTS",
    "PYEVERAND_HTTP_MAX_RETRY_DELAY_SECONDS",
    "PYEVERAND_HTTP_MAX_CONCURRENCY",
    "PYEVERAND_LOG_LEVEL",
    "PYEVERAND_LOG_FORMAT",
    "PYEVERAND_GUI_PORT",
    "PYEVERAND_GUI_RELOAD",
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


@pytest.fixture(autouse=True)
def restore_root_logger() -> Iterator[None]:
    """The CLI calls configure_logging, which replaces the root handlers."""
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
