from pathlib import Path
from typing import Any
import json
import re
import asyncio

import aiofiles

from everand_books.api.session import EverandSession
from everand_books.api.resource import fetch_resource


IMAGE_PATH_PATTERN = re.compile(r"images/([A-Za-z0-9._-]+)")


async def _download_chapter_image(
        session: EverandSession, book_id: str, chapter_number: int, save_path: Path
) -> None:
    resource_path = f"chapters/{chapter_number}/images/{save_path.name}"
    resource = await fetch_resource(session, book_id, resource_path)

    save_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(save_path, "wb") as f:
        await f.write(resource.content)


def get_chapter_image_filenames(chapter_blocks: list[dict[str, Any]]) -> set[str]:
    text = json.dumps(chapter_blocks)
    return set(IMAGE_PATH_PATTERN.findall(text))


async def download_chapter_images(
        session: EverandSession,
        book_id: str,
        chapter_number: int,
        save_paths: list[Path]
) -> None:
    tasks = [
        _download_chapter_image(session, book_id, chapter_number, path)
        for path in save_paths
    ]
    await asyncio.gather(*tasks)