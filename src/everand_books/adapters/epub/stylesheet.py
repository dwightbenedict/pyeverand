from collections.abc import Mapping


def render_stylesheet(styles: Mapping[str, str]) -> str:
    rules: list[str] = []
    for class_name, declarations in styles.items():
        lines = [
            f"  {declaration.strip()};\n"
            for declaration in declarations.split(";")
            if declaration.strip()
        ]
        rules.append(f".{class_name} {{\n{''.join(lines)}}}\n")
    return "\n".join(rules)
