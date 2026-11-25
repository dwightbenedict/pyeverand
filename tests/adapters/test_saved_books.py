from pathlib import Path

import pytest

from pyeverand.adapters import LocalSavedBooks
from pyeverand.errors import OutputDeleteError


async def test_delete_removes_the_file_and_accepts_a_missing_one(tmp_path: Path) -> None:
    book = tmp_path / "a.epub"
    book.write_bytes(b"epub")

    await LocalSavedBooks().delete(book)
    await LocalSavedBooks().delete(book)

    assert not book.exists()


async def test_delete_that_the_system_refuses_raises_output_delete_error(tmp_path: Path) -> None:
    with pytest.raises(OutputDeleteError, match="could not delete"):
        await LocalSavedBooks().delete(tmp_path)
