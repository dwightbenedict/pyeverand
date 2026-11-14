from collections.abc import Callable

import httpx
import pytest

from everand_books.adapters.everand import AccessTokenProvider, EverandBookSource, EverandSession
from everand_books.domain import Chapter, NavChapter, PageBreakBlock, SectionKind
from everand_books.errors import (
    BookNotAccessibleError,
    BookNotFoundError,
    EverandRequestError,
    UnexpectedResponseError,
)

type SessionFactory = Callable[[Callable[[httpx.Request], httpx.Response]], EverandSession]
type SourceFactory = Callable[[dict[str, httpx.Response]], EverandBookSource]

AUTH = {
    "/csrf_token": httpx.Response(200, json={"csrf_token": "csrf"}),
    "/read2/1/access_token": httpx.Response(200, json={"response": "tok", "error": None}),
}


@pytest.fixture
def make_source(make_session: SessionFactory) -> SourceFactory:
    def build(routes: dict[str, httpx.Response]) -> EverandBookSource:
        def handler(request: httpx.Request) -> httpx.Response:
            return (AUTH | routes).get(request.url.raw_path.decode(), httpx.Response(418))

        session = make_session(handler)
        return EverandBookSource(session, AccessTokenProvider(session, 540))

    return build


async def test_fetch_metadata_missing_book_raises_not_found(make_source: SourceFactory) -> None:
    source = make_source({"/book/1": httpx.Response(404)})
    with pytest.raises(BookNotFoundError, match="Book with ID 1 not found"):
        await source.fetch_metadata("1")


async def test_fetch_metadata_server_refusal_raises_request_error(
    make_source: SourceFactory,
) -> None:
    source = make_source({"/book/1": httpx.Response(403)})
    with pytest.raises(EverandRequestError, match="GET /book/1 returned HTTP 403"):
        await source.fetch_metadata("1")


async def test_fetch_metadata_parses_the_book_page(make_source: SourceFactory) -> None:
    source = make_source({"/book/1": httpx.Response(200, text="<html></html>")})
    with pytest.raises(BookNotAccessibleError):
        await source.fetch_metadata("1")


async def test_fetch_toc_maps_section_types(make_source: SourceFactory) -> None:
    toc = [
        {"title": "Intro", "type": "frontmatter", "anchor": 0, "extra": 1},
        {"title": "One", "type": "content", "anchor": 1},
        {"title": "Notes", "type": "backmatter", "anchor": 2},
        {"title": "Odd", "type": "interlude", "anchor": 3},
    ]
    source = make_source({"/scepub/1/toc.json?token=tok": httpx.Response(200, json=toc)})

    assert await source.fetch_toc("1") == [
        NavChapter("Intro", SectionKind.FRONTMATTER, 0),
        NavChapter("One", SectionKind.BODYMATTER, 1),
        NavChapter("Notes", SectionKind.BACKMATTER, 2),
        NavChapter("Odd", SectionKind.BODYMATTER, 3),
    ]


async def test_fetch_toc_unexpected_shape_raises(make_source: SourceFactory) -> None:
    source = make_source({"/scepub/1/toc.json?token=tok": httpx.Response(200, json={"toc": []})})
    with pytest.raises(UnexpectedResponseError):
        await source.fetch_toc("1")


async def test_fetch_stylesheet_keeps_only_class_declarations(make_source: SourceFactory) -> None:
    styles = {"s1": "color: red", "styles": "ignored", "meta": {"version": 2}}
    source = make_source({"/scepub/1/styles.json?token=tok": httpx.Response(200, json=styles)})

    assert await source.fetch_stylesheet("1") == {"s1": "color: red"}


async def test_fetch_chapter_returns_blocks_and_referenced_images(
    make_source: SourceFactory,
) -> None:
    body = (
        b'{"title": "One", "blocks": [{"type": "page_break"},'
        b' {"type": "image", "src": "images\\/b.png"},'
        b' {"type": "raw", "data": "<img src=\\"images/a.jpg\\"><img src=\\"images/b.png\\">"}]}'
    )
    path = "/scepub/1/chapters/3/contents.json?token=tok"
    source = make_source({path: httpx.Response(200, content=body)})

    chapter = await source.fetch_chapter("1", 3)

    assert isinstance(chapter, Chapter)
    assert chapter.title == "One"
    assert chapter.blocks[0] == PageBreakBlock(type="page_break")
    assert chapter.image_filenames == ("a.jpg", "b.png")


async def test_fetch_chapter_image_returns_image_bytes(make_source: SourceFactory) -> None:
    path = "/scepub/1/chapters/3/images/a.jpg?token=tok"
    source = make_source({path: httpx.Response(200, content=b"image")})

    assert await source.fetch_chapter_image("1", 3, "a.jpg") == b"image"


async def test_fetch_chapter_image_missing_raises_request_error(make_source: SourceFactory) -> None:
    with pytest.raises(EverandRequestError, match="HTTP 418"):
        await make_source({}).fetch_chapter_image("1", 3, "a.jpg")


async def test_fetch_cover_returns_jpeg_bytes(make_source: SourceFactory) -> None:
    cover = httpx.Response(200, content=b"jpeg", headers={"Content-Type": "image/jpeg"})
    source = make_source({"/covers/1.jpg": cover})

    assert await source.fetch_cover("https://everand.test/covers/1.jpg") == b"jpeg"
