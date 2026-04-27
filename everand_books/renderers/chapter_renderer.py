from lxml.etree import Element

from everand_books.normalization.normalize import NormalizedBlock
from everand_books.renderers.renderer import E, render


def render_chapter(title: str, blocks: list[NormalizedBlock]) -> Element:
    return E.html(
        E.head(
            E.title(title),
            E.link(
                rel="stylesheet",
                href="../Styles/styles.css",
                type="text/css",
            ),
        ),
        E.body(
            *[render(block) for block in blocks]
        ),
    )