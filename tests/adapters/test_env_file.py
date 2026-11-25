from pathlib import Path

import pytest

from everand_books.adapters import EnvFileCredentialStore
from everand_books.config import Settings
from everand_books.domain import Credentials
from everand_books.errors import ConfigurationError


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
        "export EVERAND_BOOKS_SESSION_TOKEN=old\n"
        "EVERAND__USER_ID = 1\n"
        "EVERAND_BOOKS_LOG_LEVEL=DEBUG\n",
        encoding="utf-8",
    )

    await EnvFileCredentialStore(path).save(Credentials("new", "2"))

    assert path.read_text(encoding="utf-8") == (
        "# mine\n"
        "EVERAND_BOOKS_LOG_LEVEL=DEBUG\n"
        "EVERAND_BOOKS_SESSION_TOKEN='new'\n"
        "EVERAND_BOOKS_USER_ID='2'\n"
    )


async def test_save_into_missing_folder_raises_configuration_error(tmp_path: Path) -> None:
    store = EnvFileCredentialStore(tmp_path / "missing" / ".env")

    with pytest.raises(ConfigurationError, match="Could not save the cookies"):
        await store.save(Credentials("a", "1"))
