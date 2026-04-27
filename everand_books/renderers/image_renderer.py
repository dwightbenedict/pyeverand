from lxml.etree import Element

from everand_books.models.chapter_block import ImageBlock
from everand_books.renderers.renderer import E, register_renderer
from everand_books.renderers.utils import build_style
from everand_books.epub.layout import IMAGES_HREF


@register_renderer("image")
def render_image(block: ImageBlock) -> Element:
    styles = [
        "max-width: 100%",
        "height: auto",
    ]

    if block.center:
        styles.append("display: block")
        styles.append("margin-left: auto")
        styles.append("margin-right: auto")

    image = E.img(src=f"../{IMAGES_HREF}/{block.filename}", alt=block.alt, style=build_style(styles))
    return E.div(image)