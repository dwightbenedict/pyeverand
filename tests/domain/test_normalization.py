from pyeverand.domain import (
    ListBlock,
    PageBreakBlock,
    TableBlock,
    TableRowBlock,
    TextBlock,
    normalize_blocks,
)
from pyeverand.domain.normalization import group_list_items


def bullet(level: int = 0) -> TextBlock:
    return TextBlock(type="text", bullet={}, list_level=level)


PARAGRAPH = TextBlock(type="text")
ROW = TableRowBlock(type="row")
PAGE_BREAK = PageBreakBlock(type="page_break")


def test_normalize_blocks_plain_blocks_pass_through() -> None:
    assert normalize_blocks([PARAGRAPH, PAGE_BREAK]) == [PARAGRAPH, PAGE_BREAK]


def test_normalize_blocks_consecutive_rows_become_one_table() -> None:
    assert normalize_blocks([ROW, ROW, PARAGRAPH, ROW]) == [
        TableBlock((ROW, ROW)),
        PARAGRAPH,
        TableBlock((ROW,)),
    ]


def test_normalize_blocks_consecutive_bullets_become_one_list() -> None:
    first, second = bullet(), bullet()
    assert normalize_blocks([PARAGRAPH, first, second]) == [
        PARAGRAPH,
        ListBlock(0, (first, second)),
    ]


def test_normalize_blocks_list_next_to_table_keeps_document_order() -> None:
    before, after = bullet(), bullet()
    assert normalize_blocks([before, ROW, after]) == [
        ListBlock(0, (before,)),
        TableBlock((ROW,)),
        ListBlock(0, (after,)),
    ]


def test_group_list_items_deeper_bullets_nest() -> None:
    top, nested, deepest, back = bullet(0), bullet(1), bullet(2), bullet(0)
    assert group_list_items([top, nested, deepest, back]) == ListBlock(
        0, (top, ListBlock(1, (nested, ListBlock(2, (deepest,)))), back)
    )


def test_group_list_items_bullet_shallower_than_first_stays_in_outer_list() -> None:
    deep, shallow = bullet(2), bullet(0)
    assert group_list_items([deep, shallow]) == ListBlock(2, (deep, shallow))


def test_group_list_items_without_bullets_returns_none() -> None:
    assert group_list_items([]) is None
