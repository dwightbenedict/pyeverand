import pytest

from pyeverand.domain import Credentials
from pyeverand.errors import ConfigurationError, CredentialsRequiredError
from pyeverand.services import DownloadBookService
from pyeverand.wiring import (
    get_app_options,
    get_choose_folder_service,
    get_download_queue,
    get_save_credentials_service,
    get_saved_credentials,
    get_settings,
    open_download_service,
    require_credentials,
)


def test_get_app_options_needs_no_credentials() -> None:
    assert get_app_options().gui_port == 8080


def test_get_app_options_reads_the_reload_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    assert get_app_options().gui_reload is False

    monkeypatch.setenv("PYEVERAND_GUI_RELOAD", "true")

    assert get_app_options().gui_reload is True


def test_get_app_options_invalid_value_names_the_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYEVERAND_GUI_PORT", "0")

    with pytest.raises(ConfigurationError, match="PYEVERAND_GUI_PORT"):
        get_app_options()


def test_get_choose_folder_service_is_shared() -> None:
    assert get_choose_folder_service() is get_choose_folder_service()


def test_get_download_queue_is_shared() -> None:
    assert get_download_queue() is get_download_queue()


@pytest.mark.parametrize("token", [None, ""])
def test_require_credentials_without_cookies_raises(
    monkeypatch: pytest.MonkeyPatch, token: str | None
) -> None:
    if token is not None:
        monkeypatch.setenv("PYEVERAND_SESSION_TOKEN", token)
        monkeypatch.setenv("PYEVERAND_USER_ID", "7")

    with pytest.raises(CredentialsRequiredError):
        require_credentials()


def test_get_saved_credentials_without_cookies_is_empty() -> None:
    assert get_saved_credentials() == Credentials("", "")


async def test_get_saved_credentials_returns_the_saved_cookies() -> None:
    await get_save_credentials_service().save_credentials("token", "1")

    assert get_saved_credentials() == Credentials("token", "1")


async def test_require_credentials_with_saved_cookies_passes() -> None:
    await get_save_credentials_service().save_credentials("token", "1")

    require_credentials()


async def test_saved_credentials_are_used_by_the_next_settings_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await get_save_credentials_service().save_credentials("token", "1")
    assert get_settings().user_id == "1"

    await get_save_credentials_service().save_credentials("token", "2")

    assert get_settings().user_id == "2"


@pytest.fixture
def credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYEVERAND_SESSION_TOKEN", "token")
    monkeypatch.setenv("PYEVERAND_USER_ID", "7")


@pytest.mark.usefixtures("credentials")
def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()


def test_get_settings_without_credentials_names_missing_settings() -> None:
    with pytest.raises(ConfigurationError, match="PYEVERAND_SESSION_TOKEN"):
        get_settings()


@pytest.mark.usefixtures("credentials")
async def test_open_download_service_builds_service() -> None:
    async with open_download_service() as service:
        assert isinstance(service, DownloadBookService)
