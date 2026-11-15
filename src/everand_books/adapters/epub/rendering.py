from collections.abc import Mapping
from functools import singledispatch

from lxml import html as lxml_html
from lxml.builder import ElementMaker

from everand_books.adapters.epub.element import XmlElement
from everand_books.adapters.epub.layout import (
    STYLESHEET_HREF_FROM_CHAPTER,
    image_href_from_chapter,
)
from everand_books.domain import (
    BookChapter,
    BorderBlock,
    CompositeWord,
    HTMLBlock,
    ImageBlock,
    InlineImage,
    ListBlock,
    PageBreakBlock,
    SimpleWord,
    SpacerBlock,
    TableBlock,
    TextBlock,
    normalize_blocks,
)
from everand_books.errors import UnsupportedBlockTypeError


XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
EPUB_NAMESPACE = "http://www.idpf.org/2007/ops"
EPUB_TYPE = f"{{{EPUB_NAMESPACE}}}type"

MAX_SPACER_HEIGHT_REM = 1.2
SMALLEST_HEADING_LEVEL = 6

E = ElementMaker(
    namespace=XHTML_NAMESPACE,
    nsmap={None: XHTML_NAMESPACE, "epub": EPUB_NAMESPACE},
)


def _styled(element: XmlElement, *declarations: str) -> XmlElement:
    if declarations:
        element.set("style", "; ".join(declarations))
    return element


@singledispatch
def render(block: object) -> XmlElement:
    msg = f"No renderer is registered for {type(block).__name__}"
    raise UnsupportedBlockTypeError(msg)


@render.register
def render_spacer(block: SpacerBlock) -> XmlElement:
    height = min(block.height_em, MAX_SPACER_HEIGHT_REM)
    return _styled(E.div(), f"margin: {height}rem 0")


@render.register
def render_border(block: BorderBlock) -> XmlElement:
    return _styled(
        E.hr(),
        f"border-top: {block.width_em}em {block.style} {block.color}",
        "border-left: 0",
        "border-right: 0",
        "border-bottom: 0",
        "margin: 0.5em 0",
    )


@render.register
def render_page_break(_block: PageBreakBlock) -> XmlElement:
    page_break = E.div(style="break-before: page; page-break-before: always;")
    page_break.set(EPUB_TYPE, "pagebreak")
    return page_break


@render.register
def render_image(block: ImageBlock) -> XmlElement:
    declarations = ["max-width: 100%", "height: auto"]
    if block.center:
        declarations += ["display: block", "margin-left: auto", "margin-right: auto"]
    image = E.img(src=image_href_from_chapter(block.filename), alt=block.alt)
    return E.div(_styled(image, *declarations))


@render.register
def render_raw_html(block: HTMLBlock) -> XmlElement:
    section = E.section()
    for fragment in lxml_html.fragments_fromstring(block.data):
        # lxml returns text that precedes the first element as a leading string.
        if isinstance(fragment, str):
            section.text = fragment
            continue
        for element in fragment.iter("*"):
            element.tag = f"{{{XHTML_NAMESPACE}}}{element.tag}"
        section.append(fragment)
    return section


def _text_tag(block: TextBlock) -> str:
    if block.size != "heading":
        return "p"
    level = 5 - (block.size_class or 1)
    return f"h{min(max(level, 1), SMALLEST_HEADING_LEVEL)}"


def _text_declarations(block: TextBlock) -> list[str]:
    declarations: list[str] = []
    if block.align:
        declarations.append(f"text-align: {block.align}")
    if block.block_indent is not None:
        declarations.append(f"margin-left: {block.block_indent}em")
    if block.text_indent is not None:
        declarations.append(f"text-indent: {block.text_indent}em")
    if block.bg_color is not None:
        red, green, blue = block.bg_color
        declarations.append(f"background-color: rgb({red}, {green}, {blue})")
    return declarations


@render.register
def render_text(block: TextBlock) -> XmlElement:
    text = E(_text_tag(block))
    for word in block.words:
        rendered = render(word)
        rendered.tail = " "
        text.append(rendered)
    return _styled(text, *_text_declarations(block))


@render.register
def render_list(block: ListBlock) -> XmlElement:
    tag = "ol" if block.level == 0 else "ul"
    return E(tag, *(E.li(render(item)) for item in block.items))


@render.register
def render_table(block: TableBlock) -> XmlElement:
    table = E.table()
    for row in block.rows:
        table_row = E.tr()
        for cell in row.cells:
            table_row.append(E.td(*(render(node) for node in cell.nodes), style=cell.style))
        table.append(table_row)
    return E.div(table)


@render.register
def render_simple_word(word: SimpleWord) -> XmlElement:
    span = E.span(word.text)
    span.set("class", word.style_class)
    return span


@render.register
def render_composite_word(word: CompositeWord) -> XmlElement:
    return E.span(*(render_simple_word(part) for part in word.words))


def _dimension(name: str, pixels: int | None, fallback: str) -> str:
    return f"{name}: {pixels}px" if pixels is not None and pixels > 0 else fallback


@render.register
def render_inline_image(word: InlineImage) -> XmlElement:
    image = E.img(src=image_href_from_chapter(word.filename), alt=word.alt)
    return E.span(
        _styled(
            image,
            "display: inline-block",
            "vertical-align: middle",
            _dimension("width", word.width, "max-width: 100%"),
            _dimension("height", word.height, "height: auto"),
        )
    )


def _link_images(body: XmlElement, image_names: Mapping[str, str]) -> None:
    # Covers images inside raw HTML blocks too, whose links still point at Everand's own paths.
    for image in body.iter(f"{{{XHTML_NAMESPACE}}}img"):
        filename = str(image.get("src", "")).rsplit("/", 1)[-1]
        if filename in image_names:
            image.set("src", image_href_from_chapter(image_names[filename]))


def render_chapter(chapter: BookChapter, image_names: Mapping[str, str]) -> XmlElement:
    body = E.body(*(render(block) for block in normalize_blocks(chapter.chapter.blocks)))
    body.set(EPUB_TYPE, chapter.nav.kind.value)
    _link_images(body, image_names)
    return E.html(
        E.head(
            E.title(chapter.chapter.title),
            E.link(rel="stylesheet", href=STYLESHEET_HREF_FROM_CHAPTER, type="text/css"),
        ),
        body,
    )
