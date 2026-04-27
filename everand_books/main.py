import asyncio
from pathlib import Path

from everand_books.core.config import config
from everand_books.api.session import EverandSession
from everand_books.download import download_book


async def main() -> None:
    downloads_folder = Path.home() / "Downloads"
    book_id = "696073235"
    epub_root = downloads_folder / book_id

    async with EverandSession(config.everand.session_token, config.everand.user_id) as session:
        await download_book(session, book_id, epub_root)


if __name__ == "__main__":
    asyncio.run(main())