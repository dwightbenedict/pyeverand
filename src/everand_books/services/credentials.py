from collections.abc import Callable

from everand_books.domain import parse_credentials
from everand_books.services.ports import CredentialStore


class SaveCredentialsService:
    def __init__(self, store: CredentialStore, on_saved: Callable[[], None]) -> None:
        self._store = store
        self._on_saved = on_saved

    async def save_credentials(self, session_token: str, user_id: str) -> None:
        await self._store.save(parse_credentials(session_token, user_id))
        self._on_saved()
