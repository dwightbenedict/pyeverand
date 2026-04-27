from pathlib import Path

from lxml.etree import Element, ElementTree


def write_epub_resource(resource: Element, save_path: Path, **kwargs) -> None:
    tree = ElementTree(resource)
    tree.write(save_path,
        encoding="utf-8",
        pretty_print=True,
        **kwargs
    )