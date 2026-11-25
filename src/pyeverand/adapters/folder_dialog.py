import asyncio
import logging
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from pyeverand.errors import FolderPickerError


logger = logging.getLogger(__name__)

WINDOW_COMMAND = (sys.executable, "-m", "pyeverand.adapters.folder_window")


class SystemFolderDialog:
    def __init__(self, command: Sequence[str] = WINDOW_COMMAND) -> None:
        self._command = command

    async def pick(self, initial: Path) -> Path | None:
        try:
            # Not asyncio's subprocesses: the Windows event loop used with reload lacks them.
            finished = await asyncio.to_thread(
                subprocess.run, [*self._command, str(initial)], capture_output=True, check=True
            )

        except (OSError, subprocess.CalledProcessError) as err:
            logger.warning("folder dialog failed", exc_info=True)
            msg = "Could not open the folder dialog. See the terminal for details."
            raise FolderPickerError(msg) from err

        chosen = finished.stdout.decode()
        return Path(chosen) if chosen else None
