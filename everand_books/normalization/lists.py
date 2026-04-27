from dataclasses import dataclass
from typing import Union, Literal

from everand_books.models.chapter_block import TextBlock


@dataclass
class ListBlock:
    type: Literal["list"]
    items: list[Union[TextBlock, "ListBlock"]]
    level: int = 0


class ListBuilder:
    def __init__(self):
        self.stack: list[ListBlock] = []

    def add_item(self, block: TextBlock):
        level = block.list_level

        # Start the very first list
        if not self.stack:
            lst = ListBlock(type="list", level=level, items=[block])
            self.stack.append(lst)
            return

        current = self.stack[-1]

        # Same nesting depth
        if level == current.level:
            current.items.append(block)
            return

        # Deeper nesting → create new nested ListBlock
        if level > current.level:
            nested = ListBlock(level=level, items=[block])
            current.items.append(nested)
            self.stack.append(nested)
            return

        # Shallower nesting → pop until matching level
        while self.stack and self.stack[-1].level > level:
            self.stack.pop()

        self.stack[-1].items.append(block)

    def flush(self) -> ListBlock | None:
        if not self.stack:
            return None

        root = self.stack[0]
        self.stack = []
        return root
