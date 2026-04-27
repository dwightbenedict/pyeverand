from pydantic import BaseModel, ConfigDict


class NavChapter(BaseModel):
    title: str
    type: str
    anchor: int

    model_config = ConfigDict(extra="ignore")

    @property
    def number(self) -> int:
        return self.anchor + 1

    @property
    def id(self) -> str:
        return f"chapter_{self.number}"