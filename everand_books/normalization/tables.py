from dataclasses import dataclass
from typing import Literal

from everand_books.models.chapter_block import TableRowBlock


@dataclass
class TableBlock:
    type: Literal["table"]
    rows: list[TableRowBlock]


class TableBuilder:
    def __init__(self) -> None:
        self._rows: list[TableRowBlock] = []

    def add_row(self, row: TableRowBlock) -> None:
        self._rows.append(row)

    def flush(self) -> TableBlock | None:
        if not self._rows:
            return None

        block = TableBlock(type="table", rows=self._rows)
        self._rows = []
        return block