import re
from dataclasses import dataclass, field

from everand_books.errors import InvalidCredentialsError


# Cookie values never contain these, and without them a value can be single-quoted in .env.
FORBIDDEN_CHARACTERS = re.compile(r"[\s'\"\\;]")


@dataclass(frozen=True, slots=True)
class Credentials:
    session_token: str = field(repr=False)
    user_id: str


def _cookie_value(raw: str, cookie_name: str) -> str:
    value = raw.strip()

    if not value or FORBIDDEN_CHARACTERS.search(value):
        msg = f"Paste only the value of the {cookie_name} cookie, without spaces or quotes."
        raise InvalidCredentialsError(msg)

    return value


def parse_credentials(session_token: str, user_id: str) -> Credentials:
    return Credentials(
        _cookie_value(session_token, "_scribd_session"),
        _cookie_value(user_id, "_scribd_user_id"),
    )
