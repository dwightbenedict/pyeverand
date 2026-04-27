from typing import Literal, Annotated

from pydantic import Field

from everand_books.models.base import BaseSchema


class SimpleWord(BaseSchema):
    type: Literal["simple"]
    text: str
    style_class: str = Field(alias="style")


class CompositeWord(BaseSchema):
    type: Literal["composite"]
    words: list[SimpleWord] = Field(default_factory=list)


class InlineImage(BaseSchema):
    type: Literal["inline_image"]
    src: str
    alt: str = ""
    width: int | None = None
    height: int | None = None

    @property
    def filename(self) -> str:
        return self.src.split("/")[-1]


Word = Annotated[
    SimpleWord | CompositeWord | InlineImage,
    Field(discriminator="type"),
]