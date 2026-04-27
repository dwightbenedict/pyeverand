from typing import Any
from pathlib import Path


def write_styles_css(styles: dict[str, Any], save_path: Path) -> None:
    css_lines = []

    for k, v in styles.items():
        if k == "styles":
            continue

        props = [prop.strip() for prop in v.split(";") if prop.strip()]
        formatted = "\n".join(f"  {prop};" for prop in props)

        if props:
            block = f".{k} {{\n{formatted}\n}}\n"
        else:
            block = f".{k} {{\n}}\n"

        css_lines.append(block)

    save_path.write_text("\n".join(css_lines), encoding="utf-8")