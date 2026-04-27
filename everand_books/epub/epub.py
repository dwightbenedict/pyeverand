from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from pathvalidate import sanitize_filename

from everand_books.models.metadata import BookMetadata
from everand_books.models.nav_chapter import NavChapter
from everand_books.epub.container import build_container
from everand_books.epub.package import build_package
from everand_books.epub.toc import build_toc
from everand_books.epub.utils import write_epub_resource
from everand_books.epub.layout import (
    CONTAINER_XML_PATH,
    CONTENT_OPF_PATH,
    NAV_XHTML_PATH,
    IMAGES_DIR_PATH
)


def _write_container(root: Path) -> None:
    container = build_container()
    container_filepath = root / CONTAINER_XML_PATH
    container_filepath.parent.mkdir(parents=True, exist_ok=True)
    write_epub_resource(
        resource=container,
        save_path=container_filepath,
        xml_declaration=True,
    )


def _write_package(root: Path, metadata: BookMetadata, nav_chapters: list[NavChapter]) -> None:
    images_dir = root / IMAGES_DIR_PATH
    image_files = list(images_dir.rglob("*"))
    package = build_package(metadata, nav_chapters, image_files)

    package_filepath = root / CONTENT_OPF_PATH
    package_filepath.parent.mkdir(parents=True, exist_ok=True)
    write_epub_resource(
        resource=package,
        save_path=package_filepath,
        xml_declaration=True,
    )


def _write_toc(root: Path, nav_chapters: list[NavChapter]) -> None:
    toc = build_toc(nav_chapters)
    toc_filepath = root / NAV_XHTML_PATH
    toc_filepath.parent.mkdir(parents=True, exist_ok=True)
    write_epub_resource(
        resource=toc,
        save_path=toc_filepath,
        doctype="<!DOCTYPE html>"
    )


def _write_epub(
    root: Path,
    metadata: BookMetadata,
    nav_chapters: list[NavChapter]
) -> None:
    _write_container(root)
    _write_package(root, metadata, nav_chapters)
    _write_toc(root, nav_chapters)


def _zip_epub(epub_root: Path, save_path: Path) -> None:
    with ZipFile(save_path, "w") as zf:
        # EPUB spec requires mimetype to be written first and uncompressed
        zf.writestr(
            "mimetype",
            "application/epub+zip",
            compress_type=ZIP_STORED,
        )

        for path in epub_root.rglob("*"):
            if path.is_dir():
                continue

            zf.write(
                path,
                path.relative_to(epub_root).as_posix(),
                compress_type=ZIP_DEFLATED,
            )


def package_epub(root: Path, metadata: BookMetadata, nav_chapters: list[NavChapter]) -> None:
    _write_epub(root, metadata, nav_chapters)

    epub_filename = f"{metadata.title}.epub"
    epub_filepath = root.parent / sanitize_filename(epub_filename)
    _zip_epub(root, epub_filepath)