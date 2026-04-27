import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from everand_books.core.config import config
from everand_books.api.session import EverandSession
from everand_books.api.auth import get_access_token


@retry(
    stop=stop_after_attempt(config.http.max_retries),
    wait=wait_exponential(max=config.http.max_retry_delay),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    reraise=True
)
async def fetch_resource(session: EverandSession, book_id: str, resource_path: str) -> httpx.Response:
    access_token = await get_access_token(book_id, session)
    response = await session.get(f"/scepub/{book_id}/{resource_path}?token={access_token}")
    response.raise_for_status()
    return response

