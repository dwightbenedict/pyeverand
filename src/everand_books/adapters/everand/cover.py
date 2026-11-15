from io import BytesIO

from PIL import Image, UnidentifiedImageError

from everand_books.errors import InvalidCoverImageError


JPEG_MEDIA_TYPES = frozenset({"image/jpeg", "image/jpg", "image/pjpeg"})
JPEG_QUALITY = 95


def _convert_to_jpeg(content: bytes) -> bytes:
    converted = BytesIO()
    try:
        with Image.open(BytesIO(content)) as image:
            image.convert("RGB").save(converted, "JPEG", quality=JPEG_QUALITY)
    except UnidentifiedImageError as err:
        msg = "Cover image type is not convertible to JPEG."
        raise InvalidCoverImageError(msg) from err
    return converted.getvalue()


def cover_as_jpeg(content: bytes, content_type: str) -> bytes:
    media_type = content_type.split(";", 1)[0].strip().lower()
    if not media_type.startswith("image/"):
        msg = f"Invalid content type for cover image: {content_type}"
        raise InvalidCoverImageError(msg)
    return content if media_type in JPEG_MEDIA_TYPES else _convert_to_jpeg(content)
