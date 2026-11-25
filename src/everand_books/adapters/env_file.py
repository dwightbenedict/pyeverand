import asyncio
import tempfile
from pathlib import Path

from everand_books.domain import Credentials
from everand_books.errors import ConfigurationError


SESSION_TOKEN_NAME = "EVERAND_BOOKS_SESSION_TOKEN"  # noqa: S105  a variable name, not a secret
USER_ID_NAME = "EVERAND_BOOKS_USER_ID"
# The EVERAND__ names are read by Settings too, so stale lines under them are removed as well.
REPLACED_NAMES = frozenset(
    {SESSION_TOKEN_NAME, USER_ID_NAME, "EVERAND__SESSION_TOKEN", "EVERAND__USER_ID"}
)


def _assigned_name(line: str) -> str:
    return line.partition("=")[0].strip().removeprefix("export ").strip().upper()


def _replace_file(path: Path, text: str) -> None:
    # The temporary name starts with ".env." so that it is ignored by git like .env itself.
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, prefix=".env.", delete=False
    ) as temporary:
        temporary.write(text)

    Path(temporary.name).replace(path)


def _write_credentials(path: Path, credentials: Credentials) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    kept = [line for line in lines if _assigned_name(line) not in REPLACED_NAMES]
    added = [
        f"{SESSION_TOKEN_NAME}='{credentials.session_token}'",
        f"{USER_ID_NAME}='{credentials.user_id}'",
    ]
    _replace_file(path, "\n".join([*kept, *added]) + "\n")


class EnvFileCredentialStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    async def save(self, credentials: Credentials) -> None:
        try:
            await asyncio.to_thread(_write_credentials, self._path, credentials)

        except (OSError, UnicodeDecodeError) as err:
            msg = f"Could not save the cookies to {self._path.resolve()}"
            raise ConfigurationError(msg) from err
