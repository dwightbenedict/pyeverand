from typing import Any

from everand_books.models.metadata import BookMetadata


def book_metadata_from_raw(data: dict[str, Any]) -> BookMetadata:
    return BookMetadata(
        everand_id=str(data["id"]),
        title=data["title"],
        authors=[contributor["name"] for contributor in data["contributors"]],
        publisher=data["publisher"]["name"],
        date_published=data["releaseDate"],
        description=data["description"],
        isbn=data["isbn"],
        subjects=data["themes"] + data["tropes"],
        language=data["language"],
        cover_url=data["retinaImageUrl"] or data["imageUrl"]
    )