from pydantic import BaseModel, Field

from .chapter_block import ChapterBlock


class Chapter(BaseModel):
    title: str
    blocks: list[ChapterBlock] = Field(default_factory=list)