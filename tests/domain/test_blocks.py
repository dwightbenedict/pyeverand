import pytest
from pydantic import TypeAdapter, ValidationError

from everand_books.domain import (
    ChapterBlock,
    CompositeWord,
    ImageBlock,
    InlineImage,
    SimpleWord,
    SpacerBlock,
    TableRowBlock,
    TextBlock,
)


BLOCK: TypeAdapter[ChapterBlock] = TypeAdapter(ChapterBlock)


def test_spacer_without_size_uses_default_height() -> None:
    block = BLOCK.validate_python({"type": "spacer", "ignored": True})
    assert isinstance(block, SpacerBlock)
    assert block.height_em == 0.3125


def test_spacer_negative_size_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BLOCK.validate_python({"type": "spacer", "size": -1})


def test_block_unknown_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BLOCK.validate_python({"type": "video"})


def test_text_block_parses_every_word_kind() -> None:
    block = BLOCK.validate_python(
        {
            "type": "text",
            "bg_color": [1, 2, 3],
            "words": [
                {"type": "simple", "text": "a", "style": "s1"},
                {"type": "composite", "words": [{"type": "simple", "text": "b", "style": "s2"}]},
                {"type": "image", "src": "images/inline.png"},
            ],
        }
    )

    assert isinstance(block, TextBlock)
    simple, composite, image = block.words
    assert isinstance(simple, SimpleWord)
    assert simple.style_class == "s1"
    assert isinstance(composite, CompositeWord)
    assert isinstance(image, InlineImage)
    assert image.filename == "inline.png"
    assert block.bg_color == (1, 2, 3)
    assert not block.is_bullet


def test_text_block_without_words_is_empty() -> None:
    block = BLOCK.validate_python({"type": "text", "bullet": {"type": "disc"}})
    assert isinstance(block, TextBlock)
    assert block.words == ()
    assert block.is_bullet


def test_text_block_out_of_range_colour_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BLOCK.validate_python({"type": "text", "bg_color": [1, 2, 256]})


def test_image_block_filename_is_last_path_segment() -> None:
    block = BLOCK.validate_python({"type": "image", "src": "chapters/1/images/fig.jpg"})
    assert isinstance(block, ImageBlock)
    assert block.filename == "fig.jpg"


def test_row_block_parses_cell_nodes() -> None:
    block = BLOCK.validate_python(
        {"type": "row", "cells": [{"style": "width: 50%", "nodes": [{"type": "spacer"}]}]}
    )
    assert isinstance(block, TableRowBlock)
    assert isinstance(block.cells[0].nodes[0], SpacerBlock)
