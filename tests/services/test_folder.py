import asyncio
from pathlib import Path

import pytest

from everand_books.errors import FolderPickerError
from everand_books.services import ChooseFolderService


class FakePicker:
    def __init__(self, chosen: Path | None) -> None:
        self.chosen = chosen
        self.opened_at: list[Path] = []
        self.release = asyncio.Event()
        self.release.set()
        self.fails = False

    async def pick(self, initial: Path) -> Path | None:
        self.opened_at.append(initial)
        await self.release.wait()

        if self.fails:
            raise FolderPickerError

        return self.chosen


@pytest.mark.parametrize(("chosen", "result"), [(Path("new"), "new"), (None, "old")])
async def test_choose_folder_returns_the_choice_or_keeps_the_current_one(
    chosen: Path | None, result: str
) -> None:
    picker = FakePicker(chosen)

    assert await ChooseFolderService(picker).choose_folder("old") == result
    assert picker.opened_at == [Path("old")]


async def test_choose_folder_while_open_does_not_open_a_second_dialog() -> None:
    picker = FakePicker(Path("new"))
    picker.release.clear()
    service = ChooseFolderService(picker)
    first = asyncio.create_task(service.choose_folder("old"))
    await asyncio.sleep(0)

    assert await service.choose_folder("old") == "old"

    picker.release.set()
    assert await first == "new"
    assert len(picker.opened_at) == 1


async def test_choose_folder_after_a_failure_can_open_again() -> None:
    picker = FakePicker(Path("new"))
    picker.fails = True
    service = ChooseFolderService(picker)

    with pytest.raises(FolderPickerError):
        await service.choose_folder("old")

    picker.fails = False
    assert await service.choose_folder("old") == "new"
