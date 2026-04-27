from lxml.etree import Element

from everand_books.models.word import SimpleWord, CompositeWord, InlineImage
from everand_books.renderers.renderer import E, register_renderer
from everand_books.renderers.utils import build_style
from everand_books.epub.layout import IMAGES_HREF


@register_renderer("simple")
def render_simple_word(word: SimpleWord) -> Element:
    span = E.span(word.text)
    span.set("class", word.style_class)
    return span


@register_renderer("composite")
def render_composite_word(word: CompositeWord) -> Element:
    words = [render_simple_word(word_part) for word_part in word.words]
    return E.span(*words)


@register_renderer("inline_image")
def render_inline_image(word: InlineImage) -> Element:
    styles = [
        "display: inline-block",
        "vertical-align: middle",
    ]

    if word.width is not None and word.width > 0:
        styles.append(f"width: {word.width}px")
    else:
        styles.append("max-width: 100%")

    if word.height is not None and word.height > 0:
        styles.append(f"height: {word.height}px")
    else:
        styles.append("height: auto")

    image = E.img(src=f"../{IMAGES_HREF}/{word.filename}", alt=word.alt, style=build_style(styles))
    return E.span(image)

