from lxml.etree import Element

from everand_books.models.chapter_block import SpacerBlock
from everand_books.renderers.renderer import E, register_renderer


@register_renderer("spacer")
def render_spacer(block: SpacerBlock) -> Element:
    height = min(block.height_em, 1.2)
    return E.div(
        style=f"margin: {height}rem 0"
    )