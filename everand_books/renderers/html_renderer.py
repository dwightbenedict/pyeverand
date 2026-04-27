from lxml.etree import Element, _Element
from lxml import html

from everand_books.models.chapter_block import HTMLBlock
from everand_books.renderers.renderer import E, register_renderer


@register_renderer("raw")
def render_raw_html(block: HTMLBlock) -> Element:
    nodes = html.fragments_fromstring(block.data)

    section = E.section()
    last_node: _Element | None = None

    for node in nodes:
        if isinstance(node, _Element):
            section.append(node)
            last_node = node
        else:
            if last_node is None:
                section.text = (section.text or "") + node
            else:
                last_node.tail = (last_node.tail or "") + node

    return section