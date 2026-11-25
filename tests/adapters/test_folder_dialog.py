import sys
from pathlib import Path

import pytest

from pyeverand.adapters import SystemFolderDialog, folder_window
from pyeverand.errors import FolderPickerError


ECHO = "import sys; sys.stdout.buffer.write(sys.argv[1].encode())"


async def test_pick_returns_the_path_the_window_prints(tmp_path: Path) -> None:
    folder = tmp_path / "Bücher 本"

    assert await SystemFolderDialog((sys.executable, "-c", ECHO)).pick(folder) == folder


async def test_pick_cancelled_returns_none(tmp_path: Path) -> None:
    assert await SystemFolderDialog((sys.executable, "-c", "")).pick(tmp_path) is None


async def test_pick_when_the_window_fails_raises_folder_picker_error(tmp_path: Path) -> None:
    dialog = SystemFolderDialog((sys.executable, "-c", "raise SystemExit(1)"))

    with pytest.raises(FolderPickerError, match="Could not open"):
        await dialog.pick(tmp_path)


class FakeRoot:
    destroyed = False

    def withdraw(self) -> None: ...

    def attributes(self, name: str, value: bool) -> None: ...

    def destroy(self) -> None:
        FakeRoot.destroyed = True


@pytest.mark.parametrize(("answer", "printed"), [("C:/Books", "C:/Books"), ((), "")])
def test_folder_window_prints_the_chosen_folder(
    monkeypatch: pytest.MonkeyPatch,
    capsysbinary: pytest.CaptureFixture[bytes],
    answer: object,
    printed: str,
) -> None:
    def ask(**options: object) -> object:
        return answer

    monkeypatch.setattr(folder_window.tk, "Tk", FakeRoot)
    monkeypatch.setattr(folder_window.filedialog, "askdirectory", ask)
    monkeypatch.setattr(folder_window.sys, "platform", "linux")

    folder_window.main(["start"])

    assert capsysbinary.readouterr().out.decode() == printed
    assert FakeRoot.destroyed


class FakeWindowsLibraries:
    def __init__(self) -> None:
        self.awareness: list[int] = []
        self.shcore = self

    def SetProcessDpiAwareness(self, level: int) -> None:  # noqa: N802  the Windows API's name
        self.awareness.append(level)


def test_folder_window_on_windows_asks_for_sharp_scaling(monkeypatch: pytest.MonkeyPatch) -> None:
    libraries = FakeWindowsLibraries()

    def ask(**options: object) -> str:
        return ""

    monkeypatch.setattr(folder_window.ctypes, "windll", libraries, raising=False)
    monkeypatch.setattr(folder_window.tk, "Tk", FakeRoot)
    monkeypatch.setattr(folder_window.filedialog, "askdirectory", ask)
    monkeypatch.setattr(folder_window.sys, "platform", "win32")

    folder_window.main(["start"])

    assert libraries.awareness == [1]
