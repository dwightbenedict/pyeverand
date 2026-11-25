import pytest

from pyeverand.domain import Credentials
from pyeverand.errors import InvalidCredentialsError
from pyeverand.services import SaveCredentialsService


class FakeStore:
    def __init__(self) -> None:
        self.saved: list[Credentials] = []

    async def save(self, credentials: Credentials) -> None:
        self.saved.append(credentials)


async def test_save_credentials_stores_trimmed_values_then_notifies() -> None:
    store = FakeStore()
    seen_on_notify: list[int] = []
    service = SaveCredentialsService(store, lambda: seen_on_notify.append(len(store.saved)))

    await service.save_credentials(" token ", "7\n")

    assert store.saved == [Credentials("token", "7")]
    assert seen_on_notify == [1]


@pytest.mark.parametrize(
    ("token", "user_id"),
    [("", "7"), ("token", " "), ("a b", "7"), ("a'b", "7"), ("token", "7;x=1"), ("a\nB=1", "7")],
)
async def test_save_credentials_invalid_value_stores_nothing(token: str, user_id: str) -> None:
    store = FakeStore()

    with pytest.raises(InvalidCredentialsError, match="cookie"):
        await SaveCredentialsService(store, lambda: None).save_credentials(token, user_id)

    assert store.saved == []


def test_credentials_repr_hides_the_session_token() -> None:
    assert "secret" not in repr(Credentials("secret", "7"))
