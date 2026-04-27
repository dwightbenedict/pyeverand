from typing import Union

from everand_books.models.chapter_block import (
    ChapterBlock,
    TextBlock,
    TableRowBlock,
)
from everand_books.normalization.tables import TableBlock, TableBuilder
from everand_books.normalization.lists import ListBlock, ListBuilder


type NormalizedBlock = Union[ChapterBlock, ListBlock, TableBlock]


def normalize_blocks(blocks: list[ChapterBlock]) -> list[NormalizedBlock]:
    result: list[NormalizedBlock] = []

    list_builder = ListBuilder()
    table_builder = TableBuilder()

    def flush():
        if table_block := table_builder.flush():
            result.append(table_block)

        if list_block := list_builder.flush():
            result.append(list_block)

    for block in blocks:
        if isinstance(block, TableRowBlock):
            table_builder.add_row(block)
            continue

        if isinstance(block, TextBlock) and block.is_bullet():
            list_builder.add_item(block)
            continue

        # Flush any ongoing list or table before adding a non-list, non-table block
        flush()
        result.append(block)

    # Flush any remaining list or table at the end
    flush()
    return result
