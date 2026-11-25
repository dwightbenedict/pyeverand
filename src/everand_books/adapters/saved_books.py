import asyncio
from pathlib import Path

from everand_books.errors import OutputDeleteError


class LocalSavedBooks:
    async def delete(self, path: Path) -> None:
        try:
            await asyncio.to_thread(path.unlink, missing_ok=True)

        except OSError as err:
            msg = f"Removed from the list, but could not delete {path}: {err.strerror or err}"
            raise OutputDeleteError(msg) from err
