from pathlib import Path

import pytest

from pyeverand.adapters import EnvFileCredentialStore
from pyeverand.config import Settings
from pyeverand.domain import Credentials
from pyeverand.errors import ConfigurationError


def _file_names(folder: Path) -> list[str]:
    return [path.name for path in folder.iterdir()]


async def test_save_without_env_file_creates_one_that_settings_can_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    await EnvFileCredentialStore(Path(".env")).save(Credentials("abc#$%{x}=", "7"))

    settings = Settings()  # pyright: ignore[reportCallIssue]  values come from the .env file
    assert (settings.session_token, settings.user_id) == ("abc#$%{x}=", "7")
    assert _file_names(tmp_path) == [".env"]


async def test_save_replaces_old_cookie_lines_and_keeps_the_rest(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "# mine\n"
        "export PYEVERAND_SESSION_TOKEN=old\n"
        "EVERAND__USER_ID = 1\n"
        "PYEVERAND_LOG_LEVEL=DEBUG\n",
        encoding="utf-8",
    )

    await EnvFileCredentialStore(path).save(Credentials("new", "2"))

    assert path.read_text(encoding="utf-8") == (
        "# mine\nPYEVERAND_LOG_LEVEL=DEBUG\nPYEVERAND_SESSION_TOKEN='new'\nPYEVERAND_USER_ID='2'\n"
    )


async def test_save_into_missing_folder_raises_configuration_error(tmp_path: Path) -> None:
    store = EnvFileCredentialStore(tmp_path / "missing" / ".env")

    with pytest.raises(ConfigurationError, match="Could not save the cookies"):
        await store.save(Credentials("a", "1"))
