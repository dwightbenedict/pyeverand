from lxml.etree import Element

from everand_books.models.chapter_block import TextBlock
from everand_books.models.word import Word
from everand_books.renderers.renderer import E, register_renderer, render
from everand_books.renderers.utils import build_style


def _resolve_text_tag(text_size: str | None = None, text_size_class: int | None = None) -> str:
    if text_size != "heading":
        return "p"

    heading_level = max(1, 5 - (text_size_class or 1))
    return f"h{heading_level}"


def _render_words(words: list[Word]) -> list[Element]:
    content = []

    for word in words:
        span = render(word)
        span.tail = " "
        content.append(span)

    return content


@register_renderer("text")
def render_text(block: TextBlock) -> Element:
    styles = []

    if block.align:
        styles.append(f"text-align: {block.align}")

    if block.block_indent is not None:
        styles.append(f"margin-left: {block.block_indent}em")

    if block.text_indent is not None:
        styles.append(f"text-indent: {block.text_indent}em")

    if block.bg_color is not None:
        r, g, b = block.bg_color
        styles.append(f"background-color: rgb({r}, {g}, {b})")

    word_spans = _render_words(block.words)
    text_tag = _resolve_text_tag(block.size, block.size_class)
    return E(text_tag, *word_spans, style=build_style(styles))