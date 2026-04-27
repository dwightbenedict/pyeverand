from typing import Literal, Annotated, Any

from pydantic import Field, model_validator, confloat, conint

from everand_books.models.base import BaseSchema
from everand_books.models.word import Word


class SpacerBlock(BaseSchema):
    type: Literal["spacer"]
    height_em: confloat(ge=0) = Field(alias="size", default= 0.3125)


class BorderBlock(BaseSchema):
    type: Literal["border"]
    color: str = "#000000"
    style: str = "solid"
    width_em: confloat(ge=0) = Field(alias="width", default=0.0625)


class PageBreakBlock(BaseSchema):
    type: Literal["page_break"]


RGB = Annotated[list[conint(ge=0, le=255)], Field(min_length=3, max_length=3)]


class TextBlock(BaseSchema):
    type: Literal["text"]
    size: str | None = None
    size_class: int | None = None
    align: str | None = None
    block_indent: float | None = None
    text_indent: float | None = None
    bg_color: RGB | None = None
    bullet: dict[str, Any] | None = None
    list_level: int = 0
    words: list[Word] = Field(default_factory=list)

    def is_bullet(self) -> bool:
        return self.bullet is not None

    @model_validator(mode="before")
    @classmethod
    def normalize_inline_images(cls, data: dict[str, Any]) -> dict[str, Any]:
        for word in data["words"]:
            if word["type"] == "image":
                word["type"] = "inline_image"
        return data


class ImageBlock(BaseSchema):
    type: Literal["image"]
    src: str
    alt: str = ""
    center: bool | None = None

    @property
    def filename(self) -> str:
        return self.src.split("/")[-1]


class HTMLBlock(BaseSchema):
    type: Literal["raw"]
    data: str


ChapterBlockTabular = Annotated[
    SpacerBlock | TextBlock | ImageBlock | HTMLBlock,
    Field(discriminator="type"),
]


class TableCell(BaseSchema):
    style: str
    nodes: list[ChapterBlockTabular] = Field(default_factory=list)


class TableRowBlock(BaseSchema):
    type: Literal["row"]
    cells: list[TableCell] = Field(default_factory=list)


ChapterBlock = Annotated[
    SpacerBlock
    | BorderBlock
    | PageBreakBlock
    | TextBlock
    | ImageBlock
    | HTMLBlock
    | TableRowBlock,
    Field(discriminator="type"),
]

