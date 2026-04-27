from lxml.etree import Element

from everand_books.models.chapter_block import PageBreakBlock
from everand_books.renderers.renderer import E, register_renderer


@register_renderer("page_break")
def render_page_break(_: PageBreakBlock) -> Element:
    div = E.div(
        style="break-before: page; page-break-before: always;"
    )
    div.set("{http://www.idpf.org/2007/ops}type", "pagebreak")
    return div