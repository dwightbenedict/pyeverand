from lxml.etree import Element

from everand_books.models.chapter_block import BorderBlock
from everand_books.renderers.renderer import E, register_renderer
from everand_books.renderers.utils import build_style


@register_renderer("border", "hr")
def render_border(block: BorderBlock) -> Element:
    styles = [
        f"border-top: {block.width_em}em {block.style} {block.color}",
        "border-left: 0",
        "border-right: 0",
        "border-bottom: 0",
        "margin: 0.5em 0",
    ]

    return E.hr(style=build_style(styles))