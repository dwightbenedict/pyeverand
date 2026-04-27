from typing import Any

from everand_books.models.chapter import Chapter


def chapter_from_raw(data: dict[str, Any]) -> Chapter:
    return Chapter.model_validate(data)