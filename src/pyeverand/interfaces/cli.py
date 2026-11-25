import asyncio
from pathlib import Path
from typing import Annotated

import typer

from pyeverand.errors import AppError
from pyeverand.logging_config import configure_logging
from pyeverand.wiring import get_settings, open_download_service


app = typer.Typer(no_args_is_help=True)


def _default_output_dir() -> Path:
    return Path.home() / "Downloads"


async def _download(book_id: str, output_dir: Path) -> Path:
    async with open_download_service() as service:
        return await service.download_book(book_id, output_dir)


@app.command()
def download(
    book_id: Annotated[str, typer.Argument(help="The number in the book's Everand URL.")],
    output_dir: Annotated[
        Path,
        typer.Option(default_factory=_default_output_dir, help="Folder the EPUB is saved in."),
    ],
) -> None:
    try:
        epub_path = asyncio.run(_download(book_id, output_dir))
    except AppError as err:
        typer.echo(f"error: {err}", err=True)
        raise typer.Exit(code=1) from err

    typer.echo(f"Saved {epub_path}")


def main() -> None:
    try:
        configure_logging(get_settings())
    except AppError as err:
        typer.echo(f"error: {err}", err=True)
        raise SystemExit(1) from err

    app()


if __name__ == "__main__":
    main()
