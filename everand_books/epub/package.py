from pathlib import Path
from datetime import datetime, timezone

from lxml.etree import Element

from everand_books.models.metadata import BookMetadata
from everand_books.models.nav_chapter import NavChapter
from everand_books.epub.builders.package_builder import PackageBuilder


def _generate_date_modified() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_metadata(package_builder: PackageBuilder, metadata: BookMetadata) -> None:
    metadata_builder = package_builder.metadata

    if metadata.isbn:
        metadata_builder.add_isbn(metadata.isbn)
        package_builder.set_unique_identifier("isbn")
    else:
        metadata_builder.add_identifier("everand-id", metadata.everand_id)
        package_builder.set_unique_identifier("everand-id")

    (
        metadata_builder
        .add_title(metadata.title)
        .add_authors(metadata.authors)
        .add_publisher(metadata.publisher)
        .add_date_published(metadata.date_published)
        .add_subjects(metadata.subjects)
        .add_language(metadata.language)
        .add_date_modified(_generate_date_modified())
    )

    if metadata.description:
        metadata_builder.add_description(metadata.description)

    if metadata.cover_url:
        metadata_builder.add_cover_image()


def _build_manifest(
        package_builder: PackageBuilder,
        nav_chapters: list[NavChapter],
        image_files: list[Path],
) -> None:
    manifest = package_builder.manifest

    manifest.add_chapters(nav_chapters)

    cover_image = next((p for p in image_files if p.stem == "cover"), None)
    images = [p for p in image_files if p is not cover_image]

    if cover_image:
        manifest.add_cover_image()

    manifest.add_images(images)


def _build_spine(
        package_builder: PackageBuilder,
        nav_chapters: list[NavChapter],
) -> None:
    spine = package_builder.spine
    spine.add_chapters(nav_chapters)


def build_package(
        metadata: BookMetadata,
        nav_chapters: list[NavChapter],
        image_files: list[Path]
) -> Element:
    package_builder = PackageBuilder()
    _build_metadata(package_builder, metadata)
    _build_manifest(package_builder, nav_chapters, image_files)
    _build_spine(package_builder, nav_chapters)
    return package_builder.build()



