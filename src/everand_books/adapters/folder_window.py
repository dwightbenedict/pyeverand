"""The program `folder_dialog` runs: show the system's folder dialog and print the choice.

It is a process of its own because Tk wants the main thread, which the web server occupies.
"""

import ctypes
import sys
import tkinter as tk
from tkinter import filedialog


def _ask_folder(initial: str) -> str:
    if sys.platform == "win32":
        # Without this, Windows scales the dialog as a bitmap and it looks blurred.
        ctypes.windll.shcore.SetProcessDpiAwareness(1)

    root = tk.Tk()
    root.withdraw()
    # The browser has the focus, so the dialog would otherwise open behind it. The ignores are for
    # Tk's own signature: it takes the value by position and its type stub leaves it unknown.
    root.attributes("-topmost", True)  # noqa: FBT003  # pyright: ignore[reportUnknownMemberType]

    try:
        return filedialog.askdirectory(
            parent=root, initialdir=initial, title="Save Books To", mustexist=False
        )

    finally:
        root.destroy()


def main(arguments: list[str]) -> None:
    # Bytes, so that the console's code page cannot damage the path. Cancel gives an empty value.
    sys.stdout.buffer.write(str(_ask_folder(arguments[0]) or "").encode())


if __name__ == "__main__":
    main(sys.argv[1:])
