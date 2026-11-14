import httpx
from pydantic import TypeAdapter

from everand_books.errors import EverandRequestError, UnexpectedResponseError


def ensure_ok(response: httpx.Response) -> httpx.Response:
    if response.is_error:
        request = response.request
        msg = f"{request.method} {request.url.path} returned HTTP {response.status_code}"
        raise EverandRequestError(msg)
    return response


def parse_json[T](content: str | bytes, adapter: TypeAdapter[T]) -> T:
    try:
        return adapter.validate_json(content)
    except ValueError as err:
        msg = f"Everand returned data in an unexpected shape: {err}"
        raise UnexpectedResponseError(msg) from err
