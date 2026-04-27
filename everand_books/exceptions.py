

class EverandBooksException(Exception):
    """Base exception for Everand Books downloader."""


class BookNotFoundError(EverandBooksException):
    """Raised when a book is not found."""


class InvalidCoverImageError(EverandBooksException):
    """Raised when a book cover is not a valid image format."""


class BookNotAccessibleError(EverandBooksException):
    """Raised when a book is not accessible (e.g., private or removed)."""


class UnsupportedBlockTypeError(EverandBooksException):
    """Raised when an unsupported block type is encountered in chapter content."""


class UnsupportedWordTypeError(EverandBooksException):
    """Raised when an unsupported word type is encountered in text block."""


class InvalidEPUBChapterFormatError(EverandBooksException):
    """Raised when a chapter is not in a valid format by EPUB specs."""

class UnsupportedEPUBImageFormatError(EverandBooksException):
    """Raised when an unsupported image format is encountered in packaging the EPUB."""

