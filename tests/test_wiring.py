import pytest

from everand_books.errors import ConfigurationError
from everand_books.services import DownloadBookService
from everand_books.wiring import get_settings, open_download_service


@pytest.fixture
def credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVERAND_BOOKS_SESSION_TOKEN", "token")
    monkeypatch.setenv("EVERAND_BOOKS_USER_ID", "7")


@pytest.mark.usefixtures("credentials")
def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()


def test_get_settings_without_credentials_names_missing_settings() -> None:
    with pytest.raises(ConfigurationError, match="EVERAND_BOOKS_SESSION_TOKEN"):
        get_settings()


@pytest.mark.usefixtures("credentials")
async def test_open_download_service_builds_service() -> None:
    async with open_download_service() as service:
        assert isinstance(service, DownloadBookService)
