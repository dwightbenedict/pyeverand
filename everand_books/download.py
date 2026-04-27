import asyncio
from pathlib import Path

from everand_books.api.session import EverandSession

from everand_books.client.metadata import get_book_metadata
from everand_books.client.book import fetch_toc, fetch_styles, fetch_chapter
from everand_books.client.cover_image import download_cover_image
from everand_books.client.chapter_image import get_chapter_image_filenames, download_chapter_images

from everand_books.adapters.metadata import book_metadata_from_raw
from everand_books.adapters.nav_chapter import nav_chapters_from_raw
from everand_books.adapters.chapter import chapter_from_raw

from everand_books.models.nav_chapter import NavChapter

from everand_books.normalization.normalize import normalize_blocks
from everand_books.renderers.chapter_renderer import render_chapter

from everand_books.epub.layout import chapter_path, image_path, stylesheet_path
from everand_books.epub.css import write_styles_css
from everand_books.epub.epub import package_epub
from everand_books.epub.utils import write_epub_resource


async def _download_chapter(
        session: EverandSession, book_id: str, nav_chapter: NavChapter, root: Path
) -> None:
    raw_chapter = await fetch_chapter(session, book_id, nav_chapter.number)
    chapter = chapter_from_raw(raw_chapter)
    normalized_chapter_blocks = normalize_blocks(chapter.blocks)
    rendered_chapter = render_chapter(chapter.title, normalized_chapter_blocks)

    chapter_filepath = root / chapter_path(nav_chapter.id)
    chapter_filepath.parent.mkdir(parents=True, exist_ok=True)
    write_epub_resource(
        rendered_chapter,
        save_path=chapter_filepath,
        method="html",
        doctype="<!DOCTYPE html>"
    )

    chapter_image_filenames = get_chapter_image_filenames(raw_chapter["blocks"])

    chapter_image_filepaths = []
    for image_filename in chapter_image_filenames:
        chapter_image_filepath = root / image_path(image_filename)
        chapter_image_filepath.parent.mkdir(parents=True, exist_ok=True)
        chapter_image_filepaths.append(chapter_image_filepath)

    await download_chapter_images(
        session,
        book_id,
        nav_chapter.number,
        chapter_image_filepaths
    )


async def _download_chapters(
        session: EverandSession, book_id: str, nav_chapters: list[NavChapter], root: Path
) -> None:
    tasks = [
        _download_chapter(session, book_id, chapter, root)
        for chapter in nav_chapters
    ]
    await asyncio.gather(*tasks)


async def _download_stylesheet(session: EverandSession, book_id: str, root: Path) -> None:
    raw_styles = await fetch_styles(session, book_id)
    stylesheet_filepath = root / stylesheet_path()
    stylesheet_filepath.parent.mkdir(parents=True, exist_ok=True)
    write_styles_css(raw_styles, stylesheet_filepath)


async def _download_cover_image(session: EverandSession, cover_url: str, root: Path) -> None:
    filepath = root / image_path("cover.jpg")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    await download_cover_image(session, cover_url, filepath)


async def download_book(session: EverandSession, book_id: str, root: Path) -> None:
    raw_metadata = await get_book_metadata(session, book_id)
    metadata = book_metadata_from_raw(raw_metadata)
    book_id = metadata.everand_id

    await _download_cover_image(session, metadata.cover_url, root)
    await _download_stylesheet(session, book_id, root)

    raw_nav_chapters = await fetch_toc(session, book_id)
    nav_chapters = nav_chapters_from_raw(raw_nav_chapters)

    await _download_chapters(session, book_id, nav_chapters, root)

    package_epub(root, metadata, nav_chapters)


