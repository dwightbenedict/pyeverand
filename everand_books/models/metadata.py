from pydantic import BaseModel, field_validator


class BookMetadata(BaseModel):
    everand_id: str
    title: str
    authors: list[str]
    publisher: str
    date_published: str
    description: str | None = None
    isbn: str | None = None
    subjects: list[str]
    language: str
    cover_url: str | None = None

