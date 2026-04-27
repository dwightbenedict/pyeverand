from pathlib import Path
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from everand_books.api.session import EverandSession
from everand_books.exceptions import InvalidCoverImageError


JPEG_TYPES = {"image/jpeg", "image/jpg", "image/pjpeg"}
ALLOWED_JPG_EXTENSIONS = {".jpg", ".jpeg"}


def _image_bytes_to_jpeg(content: bytes, save_path: Path) -> None:
    try:
        img = Image.open(BytesIO(content))
    except UnidentifiedImageError:
        raise InvalidCoverImageError("Image type not convertible to JPEG.")

    rgb = img.convert("RGB")
    rgb.save(save_path, "JPEG", quality=95)


async def download_cover_image(session: EverandSession, cover_url: str, save_path: Path) -> None:
    if save_path.suffix not in ALLOWED_JPG_EXTENSIONS:
        raise InvalidCoverImageError("Cover image must be saved as a JPEG file.")

    response = await session.get(cover_url)
    content_type = response.headers.get("Content-Type", "").lower()

    if not content_type.startswith("image/"):
        raise InvalidCoverImageError(f"Invalid content type for cover image: {content_type}")

    if content_type in JPEG_TYPES:
        save_path.write_bytes(response.content)
    else:
        _image_bytes_to_jpeg(response.content, save_path)
