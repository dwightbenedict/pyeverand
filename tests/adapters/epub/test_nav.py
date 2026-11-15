from everand_books.adapters.epub.nav import build_nav_document
from everand_books.domain import NavChapter, SectionKind


XHTML = {"x": "http://www.w3.org/1999/xhtml"}


def test_build_nav_document_links_every_chapter_in_order() -> None:
    toc = [
        NavChapter("Intro", SectionKind.FRONTMATTER, 0),
        NavChapter("One", SectionKind.BODYMATTER, 1),
    ]

    document = build_nav_document(toc, "fr")

    nav = document.find("x:body/x:nav", XHTML)
    assert nav is not None
    assert nav.get("{http://www.idpf.org/2007/ops}type") == "toc"
    assert [(link.get("href"), link.text) for link in nav.iterfind("x:ol/x:li/x:a", XHTML)] == [
        ("Text/chapter_1.xhtml", "Intro"),
        ("Text/chapter_2.xhtml", "One"),
    ]
    assert document.get("lang") == "fr"
    assert document.get("{http://www.w3.org/XML/1998/namespace}lang") == "fr"
