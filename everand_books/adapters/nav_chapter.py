from typing import Any

from everand_books.models.nav_chapter import NavChapter


PROPERTY_MAP = {
    "frontmatter": "frontmatter",
    "content": "bodymatter",
    "backmatter": "backmatter",
}


def nav_chapters_from_raw(data: list[dict[str, Any]]) -> list[NavChapter]:
    chapters = []

    for item in data:
        normalized = item.copy()
        normalized["type"] = PROPERTY_MAP[item["type"]]
        chapters.append(NavChapter.model_validate(normalized))

    return chapters