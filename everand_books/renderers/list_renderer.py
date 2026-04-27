from lxml.etree import Element

from everand_books.normalization.lists import ListBlock
from everand_books.renderers.renderer import E, register_renderer, render


@register_renderer("list")
def render_list(block: ListBlock) -> Element:
    tag = "ol" if block.level == 0 else "ul"

    items = []
    for item in block.items:
        rendered = render(item)
        items.append(E.li(rendered))

    return E(tag, *items)