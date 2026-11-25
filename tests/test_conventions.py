"""Mechanical checks for the UI rules in docs/design.md, so they need no one to remember them."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI_DIRS = [
    ROOT / "src" / "pyeverand" / "interfaces",
]
SUFFIXES = {".css", ".ts", ".html", ".py"}
RAW_COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")
INLINE_STYLE = re.compile(r"\bstyle\s*=|\.style\b")
TOKEN_DECLARATION = re.compile(r"^\s*--[\w-]+\s*:")


def _violations() -> list[str]:
    found: list[str] = []

    for directory in UI_DIRS:
        for path in sorted(directory.rglob("*")):
            if path.suffix not in SUFFIXES:
                continue

            lines = path.read_text(encoding="utf-8").splitlines()

            for number, line in enumerate(lines, start=1):
                if TOKEN_DECLARATION.match(line):
                    continue

                if RAW_COLOUR.search(line) or INLINE_STYLE.search(line):
                    found.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")

    return found


def test_ui_code_uses_design_tokens_only() -> None:
    assert _violations() == [], "raw colour or inline style: use the tokens from docs/design.md"
