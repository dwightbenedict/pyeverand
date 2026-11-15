from typing import get_args

import pytest
from lxml import etree

from everand_books.adapters.epub.element import XmlElement
from everand_books.adapters.epub.rendering import render, render_chapter
from everand_books.domain import (
    BookChapter,
    BorderBlock,
    Chapter,
    CompositeWord,
    HTMLBlock,
    ImageBlock,
    InlineImage,
    ListBlock,
    NavChapter,
    NormalizedBlock,
    PageBreakBlock,
    SectionKind,
    SimpleWord,
    SpacerBlock,
    TableBlock,
    TableCell,
    TableRowBlock,
    TextBlock,
    Word,
)
from everand_books.errors import UnsupportedBlockTypeError


EPUB_TYPE = "{http://www.idpf.org/2007/ops}type"
RENDERABLE_TYPES = [*get_args(NormalizedBlock), *get_args(get_args(Word)[0])]


def tag(element: XmlElement) -> str:
    return etree.QName(element).localname


def tags(element: XmlElement) -> list[str]:
    return [tag(child) for child in element]


def word(text: str = "hi") -> SimpleWord:
    return SimpleWord(type="simple", text=text, style="s1")


@pytest.mark.parametrize("block_type", RENDERABLE_TYPES)
def test_render_every_block_and_word_type_has_a_renderer(block_type: type) -> None:
    assert render.dispatch(block_type) is not render.dispatch(object)


def test_render_unregistered_type_raises_unsupported_block() -> None:
    with pytest.raises(UnsupportedBlockTypeError, match="int"):
        render(1)


@pytest.mark.parametrize(("size", "margin"), [(0.5, "0.5rem"), (3, "1.2rem")])
def test_render_spacer_caps_height(size: float, margin: str) -> None:
    rendered = render(SpacerBlock(type="spacer", size=size))
    assert (tag(rendered), rendered.get("style")) == ("div", f"margin: {margin} 0")


def test_render_border_draws_top_rule() -> None:
    rendered = render(BorderBlock(type="border", color="#f00", width=0.1))
    assert tag(rendered) == "hr"
    assert str(rendered.get("style")).startswith("border-top: 0.1em solid #f00; border-left: 0")


def test_render_page_break_is_marked_for_reading_systems() -> None:
    rendered = render(PageBreakBlock(type="page_break"))
    assert rendered.get(EPUB_TYPE) == "pagebreak"


@pytest.mark.parametrize(
    ("center", "style"),
    [
        (None, "max-width: 100%; height: auto"),
        (
            True,
            "max-width: 100%; height: auto; display: block; margin-left: auto; margin-right: auto",
        ),
    ],
)
def test_render_image_links_into_images_folder(center: bool | None, style: str) -> None:
    rendered = render(ImageBlock(type="image", src="images/fig.jpg", alt="Fig", center=center))
    image = rendered[0]
    assert (tag(rendered), tag(image)) == ("div", "img")
    assert dict(image.attrib) == {"src": "../Images/fig.jpg", "alt": "Fig", "style": style}


def test_render_raw_html_keeps_text_and_moves_elements_into_xhtml() -> None:
    rendered = render(
        HTMLBlock(type="raw", data='lead <p class="x">para<br>line</p> tail <b>bold</b>')
    )

    assert etree.tostring(rendered, encoding="unicode") == (
        '<section xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">'
        'lead <p class="x">para<br/>line</p> tail <b>bold</b></section>'
    )
    assert all(
        etree.QName(element).namespace == "http://www.w3.org/1999/xhtml"
        for element in rendered.iter("*")
    )


def test_render_raw_html_without_leading_text_has_no_section_text() -> None:
    rendered = render(HTMLBlock(type="raw", data="<p>only</p>"))
    assert rendered.text is None
    assert tags(rendered) == ["p"]


def test_render_text_plain_paragraph_has_no_style_and_spaces_words() -> None:
    rendered = render(TextBlock(type="text", words=(word("a"), word("b"))))
    assert (tag(rendered), rendered.get("style")) == ("p", None)
    assert [(span.text, span.get("class"), span.tail) for span in rendered] == [
        ("a", "s1", " "),
        ("b", "s1", " "),
    ]


@pytest.mark.parametrize(
    ("size_class", "expected"), [(None, "h4"), (2, "h3"), (9, "h1"), (-5, "h6")]
)
def test_render_text_heading_level_stays_between_h1_and_h6(
    size_class: int | None, expected: str
) -> None:
    rendered = render(TextBlock(type="text", size="heading", size_class=size_class))
    assert tag(rendered) == expected


def test_render_text_applies_alignment_indents_and_background() -> None:
    block = TextBlock(
        type="text", align="center", block_indent=1.5, text_indent=2, bg_color=(1, 2, 3)
    )
    assert render(block).get("style") == (
        "text-align: center; margin-left: 1.5em; text-indent: 2.0em; background-color: rgb(1, 2, 3)"
    )


def test_render_list_top_level_is_ordered_and_nested_is_unordered() -> None:
    item = TextBlock(type="text", bullet={})
    rendered = render(ListBlock(0, (item, ListBlock(1, (item,)))))

    assert (tag(rendered), tags(rendered)) == ("ol", ["li", "li"])
    assert [tag(entry[0]) for entry in rendered] == ["p", "ul"]


def test_render_table_renders_rows_cells_and_cell_nodes() -> None:
    cells = (
        TableCell(style="width: 50%", nodes=(SpacerBlock(type="spacer"),)),
        TableCell(style=""),
    )
    rendered = render(TableBlock((TableRowBlock(type="row", cells=cells),)))

    row = rendered[0][0]
    assert (tag(rendered), tag(rendered[0]), tag(row)) == ("div", "table", "tr")
    assert [(tag(cell), cell.get("style"), tags(cell)) for cell in row] == [
        ("td", "width: 50%", ["div"]),
        ("td", "", []),
    ]


def test_render_composite_word_wraps_its_parts() -> None:
    rendered = render(CompositeWord(type="composite", words=(word("wor"), word("ld"))))
    assert (tag(rendered), [part.text for part in rendered]) == ("span", ["wor", "ld"])


@pytest.mark.parametrize(
    ("width", "height", "size_style"),
    [(10, 12, "width: 10px; height: 12px"), (None, 0, "max-width: 100%; height: auto")],
)
def test_render_inline_image_uses_given_size_or_scales(
    width: int | None, height: int | None, size_style: str
) -> None:
    rendered = render(InlineImage(type="image", src="images/i.png", width=width, height=height))
    image = rendered[0]
    assert (tag(rendered), image.get("src")) == ("span", "../Images/i.png")
    assert image.get("style") == f"display: inline-block; vertical-align: middle; {size_style}"


def test_render_chapter_builds_document_with_grouped_blocks() -> None:
    bullet = TextBlock(type="text", bullet={})
    chapter = BookChapter(
        NavChapter("One", SectionKind.BACKMATTER, 0),
        Chapter("One & Only", (bullet, bullet)),
    )

    document = render_chapter(chapter, {})

    head, body = document
    assert (tag(document), tags(head), tags(body)) == ("html", ["title", "link"], ["ol"])
    assert head[0].text == "One & Only"
    assert head[1].get("href") == "../Styles/styles.css"
    assert body.get(EPUB_TYPE) == "backmatter"


def test_render_chapter_points_images_at_their_archive_names() -> None:
    blocks = (
        ImageBlock(type="image", src="images/fig.jpg"),
        HTMLBlock(type="raw", data='<img src="images/raw.png"><img src="https://cdn/other.gif">'),
    )
    chapter = BookChapter(NavChapter("One", SectionKind.BODYMATTER, 0), Chapter("One", blocks))

    document = render_chapter(chapter, {"fig.jpg": "chapter_1-fig.jpg", "raw.png": "raw.png"})

    sources = [image.get("src") for image in document.iter("{http://www.w3.org/1999/xhtml}img")]
    assert sources == ["../Images/chapter_1-fig.jpg", "../Images/raw.png", "https://cdn/other.gif"]
