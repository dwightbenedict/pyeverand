class AppError(Exception):
    pass


class ConfigurationError(AppError):
    pass


class BookNotFoundError(AppError):
    pass


class BookNotAccessibleError(AppError):
    pass


class EverandRequestError(AppError):
    pass


class UnexpectedResponseError(AppError):
    pass


class InvalidCoverImageError(AppError):
    pass


class UnsupportedBlockTypeError(AppError):
    pass


class UnsupportedImageFormatError(AppError):
    pass
