class AppError(Exception):
    pass


class ConfigurationError(AppError):
    pass


class InvalidCredentialsError(AppError):
    pass


class CredentialsRequiredError(AppError):
    pass


class FolderPickerError(AppError):
    pass


class OutputDeleteError(AppError):
    pass


class InvalidBookReferenceError(AppError):
    pass


class InvalidOutputFolderError(AppError):
    pass


class OutputWriteError(AppError):
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
