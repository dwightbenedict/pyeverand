from functools import wraps
from typing import Callable, Protocol, TypeVar

from lxml.etree import Element
from lxml.builder import ElementMaker

from everand_books.exceptions import UnsupportedBlockTypeError


E = ElementMaker(
    namespace="http://www.w3.org/1999/xhtml",
    nsmap={None: "http://www.w3.org/1999/xhtml"}
)


class Renderable(Protocol):
    type: str


T = TypeVar("T", bound=Renderable)

RenderFn = Callable[[T], Element]

renderers: dict[str, RenderFn] = {}


def register_renderer(*block_types: str) -> Callable[[RenderFn], RenderFn]:
    def decorator(fn: RenderFn) -> RenderFn:
        @wraps(fn)
        def wrapper(data: Renderable) -> Element:
            return fn(data)

        for block_type in block_types:
            renderers[block_type] = wrapper

        return wrapper

    return decorator


def render(block: Renderable) -> Element:
    renderer = renderers.get(block.type)

    if renderer is None:
        raise UnsupportedBlockTypeError(f"Unsupported data type encountered: {block.type}")

    return renderer(block)

