from pathlib import Path

from everand_books.models.chapter import Chapter
from everand_books.renderers.chapter_renderer import render_chapter
from everand_books.normalization.normalize import normalize_blocks
from everand_books.epub.utils import write_epub_resource


def write_chapter(chapter: Chapter, save_path: Path) -> None:
    normalized_blocks = normalize_blocks(chapter.blocks)
    root = render_chapter(chapter.title, normalized_blocks)
    write_epub_resource(root, save_path, method="xml", doctype="<!DOCTYPE html>")