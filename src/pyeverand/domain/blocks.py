from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat


class BlockSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


def _filename(src: str) -> str:
    return src.rsplit("/", 1)[-1]


class SimpleWord(BlockSchema):
    type: Literal["simple"]
    text: str
    style_class: str = Field(alias="style")


class CompositeWord(BlockSchema):
    type: Literal["composite"]
    words: tuple[SimpleWord, ...] = ()


class InlineImage(BlockSchema):
    type: Literal["image"]
    src: str
    alt: str = ""
    width: int | None = None
    height: int | None = None

    @property
    def filename(self) -> str:
        return _filename(self.src)


Word = Annotated[SimpleWord | CompositeWord | InlineImage, Field(discriminator="type")]


class SpacerBlock(BlockSchema):
    type: Literal["spacer"]
    height_em: NonNegativeFloat = Field(alias="size", default=0.3125)


class BorderBlock(BlockSchema):
    type: Literal["border"]
    color: str = "#000000"
    style: str = "solid"
    width_em: NonNegativeFloat = Field(alias="width", default=0.0625)


class PageBreakBlock(BlockSchema):
    type: Literal["page_break"]


RgbChannel = Annotated[int, Field(ge=0, le=255)]


class TextBlock(BlockSchema):
    type: Literal["text"]
    size: str | None = None
    size_class: int | None = None
    align: str | None = None
    block_indent: float | None = None
    text_indent: float | None = None
    bg_color: tuple[RgbChannel, RgbChannel, RgbChannel] | None = None
    bullet: dict[str, object] | None = None
    list_level: int = 0
    words: tuple[Word, ...] = ()

    @property
    def is_bullet(self) -> bool:
        return self.bullet is not None


class ImageBlock(BlockSchema):
    type: Literal["image"]
    src: str
    alt: str = ""
    center: bool | None = None

    @property
    def filename(self) -> str:
        return _filename(self.src)


class HTMLBlock(BlockSchema):
    type: Literal["raw"]
    data: str


TableCellBlock = Annotated[
    SpacerBlock | TextBlock | ImageBlock | HTMLBlock,
    Field(discriminator="type"),
]


class TableCell(BlockSchema):
    style: str
    nodes: tuple[TableCellBlock, ...] = ()


class TableRowBlock(BlockSchema):
    type: Literal["row"]
    cells: tuple[TableCell, ...] = ()


ChapterBlock = Annotated[
    SpacerBlock | BorderBlock | PageBreakBlock | TextBlock | ImageBlock | HTMLBlock | TableRowBlock,
    Field(discriminator="type"),
]
