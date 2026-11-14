from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from typer.testing import CliRunner

from everand_books.errors import BookNotFoundError
from everand_books.interfaces import cli

runner = CliRunner()


class FakeService:
    async def download_book(self, book_id: str, output_dir: Path) -> Path:
        if book_id == "404":
            msg = "Book with ID 404 not found."
            raise BookNotFoundError(msg)
        return output_dir / f"{book_id}.epub"


@pytest.fixture(autouse=True)
def fake_service(monkeypatch: pytest.MonkeyPatch) -> None:
    @asynccontextmanager
    async def open_fake_service() -> AsyncGenerator[FakeService]:
        yield FakeService()

    monkeypatch.setattr(cli, "open_download_service", open_fake_service)


def test_download_known_book_prints_saved_path(tmp_path: Path) -> None:
    result = runner.invoke(cli.app, ["1", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "1.epub" in result.output


def test_download_without_output_dir_saves_to_downloads_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(cli.app, ["1"])
    assert result.exit_code == 0
    assert "Downloads" in result.output


def test_download_missing_book_exits_one_with_message() -> None:
    result = runner.invoke(cli.app, ["404"])
    assert result.exit_code == 1
    assert "error: Book with ID 404 not found." in result.output
