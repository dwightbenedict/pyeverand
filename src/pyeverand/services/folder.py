from pathlib import Path

from pyeverand.services.ports import FolderPicker


class ChooseFolderService:
    def __init__(self, picker: FolderPicker) -> None:
        self._picker = picker
        self._is_open = False

    async def choose_folder(self, current: str) -> str:
        """Return the folder the person picks, or ``current`` if they pick none."""

        # A second press while the dialog is open must not stack another one.
        if self._is_open:
            return current

        self._is_open = True

        try:
            chosen = await self._picker.pick(Path(current))

        finally:
            self._is_open = False

        return current if chosen is None else str(chosen)
