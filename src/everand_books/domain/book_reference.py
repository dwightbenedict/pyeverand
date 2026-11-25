import re
from urllib.parse import urlsplit

from everand_books.errors import InvalidBookReferenceError


BOOK_HOSTS = frozenset({"everand.com", "www.everand.com"})
BOOK_ID_PATTERN = re.compile(r"[0-9]+")
BOOK_PATH_PATTERN = re.compile(r"/(?:book|read)/([0-9]+)(?:/.*)?")


def parse_book_id(reference: str) -> str:
    """Take a book ID, or the address of a book page with or without ``https://``."""
    text = reference.strip()

    if BOOK_ID_PATTERN.fullmatch(text):
        return text

    url = urlsplit(text if "://" in text else f"https://{text}")
    match = BOOK_PATH_PATTERN.fullmatch(url.path)

    if url.netloc.lower() not in BOOK_HOSTS or match is None:
        msg = f"Not an Everand book link or ID: {text}"
        raise InvalidBookReferenceError(msg)

    return match.group(1)
