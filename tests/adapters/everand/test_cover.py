from io import BytesIO

import pytest
from PIL import Image

from pyeverand.adapters.everand.cover import cover_as_jpeg
from pyeverand.errors import InvalidCoverImageError


def png() -> bytes:
    buffer = BytesIO()
    Image.new("RGBA", (2, 2)).save(buffer, "PNG")
    return buffer.getvalue()


def test_cover_as_jpeg_jpeg_content_is_kept_as_is() -> None:
    assert cover_as_jpeg(b"jpeg-bytes", "image/JPEG; charset=binary") == b"jpeg-bytes"


def test_cover_as_jpeg_other_image_is_converted() -> None:
    converted = cover_as_jpeg(png(), "image/png")

    with Image.open(BytesIO(converted)) as image:
        assert image.format == "JPEG"


def test_cover_as_jpeg_non_image_content_type_raises() -> None:
    with pytest.raises(InvalidCoverImageError, match="text/html"):
        cover_as_jpeg(b"<html>", "text/html")


def test_cover_as_jpeg_unreadable_image_raises() -> None:
    with pytest.raises(InvalidCoverImageError, match="not convertible"):
        cover_as_jpeg(b"not an image", "image/png")
