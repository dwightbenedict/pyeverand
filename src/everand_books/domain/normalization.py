from collections.abc import Iterable
from dataclasses import dataclass, field

from everand_books.domain.blocks import (
    BorderBlock,
    ChapterBlock,
    HTMLBlock,
    ImageBlock,
    PageBreakBlock,
    SpacerBlock,
    TableRowBlock,
    TextBlock,
)


@dataclass(frozen=True, slots=True)
class ListBlock:
    level: int
    items: tuple["TextBlock | ListBlock", ...]


@dataclass(frozen=True, slots=True)
class TableBlock:
    rows: tuple[TableRowBlock, ...]


# Rows never appear here on their own: normalising always folds them into a TableBlock.
NormalizedBlock = (
    SpacerBlock
    | BorderBlock
    | PageBreakBlock
    | TextBlock
    | ImageBlock
    | HTMLBlock
    | ListBlock
    | TableBlock
)


@dataclass(slots=True)
class _OpenList:
    level: int
    items: list["TextBlock | _OpenList"] = field(default_factory=lambda: [])

    def close(self) -> ListBlock:
        return ListBlock(
            self.level,
            tuple(item.close() if isinstance(item, _OpenList) else item for item in self.items),
        )


def group_list_items(bullets: Iterable[TextBlock]) -> ListBlock | None:
    stack: list[_OpenList] = []
    for bullet in bullets:
        if stack and bullet.list_level <= stack[-1].level:
            # An item shallower than the first one stays in the outermost list.
            while len(stack) > 1 and stack[-1].level > bullet.list_level:
                stack.pop()
            stack[-1].items.append(bullet)
            continue
        opened = _OpenList(bullet.list_level, [bullet])
        if stack:
            stack[-1].items.append(opened)
        stack.append(opened)
    return stack[0].close() if stack else None


@dataclass(slots=True)
class _Grouping:
    normalized: list[NormalizedBlock] = field(default_factory=lambda: [])
    rows: list[TableRowBlock] = field(default_factory=lambda: [])
    bullets: list[TextBlock] = field(default_factory=lambda: [])

    def close_table(self) -> None:
        if self.rows:
            self.normalized.append(TableBlock(tuple(self.rows)))
            self.rows.clear()

    def close_list(self) -> None:
        if grouped := group_list_items(self.bullets):
            self.normalized.append(grouped)
            self.bullets.clear()

    def add(self, block: ChapterBlock) -> None:
        if isinstance(block, TableRowBlock):
            self.close_list()
            self.rows.append(block)
        elif isinstance(block, TextBlock) and block.is_bullet:
            self.close_table()
            self.bullets.append(block)
        else:
            self.close_table()
            self.close_list()
            self.normalized.append(block)


def normalize_blocks(blocks: Iterable[ChapterBlock]) -> list[NormalizedBlock]:
    grouping = _Grouping()
    for block in blocks:
        grouping.add(block)
    grouping.close_table()
    grouping.close_list()
    return grouping.normalized
