from everand_books.adapters.epub.stylesheet import render_stylesheet


def test_render_stylesheet_writes_one_rule_per_class() -> None:
    css = render_stylesheet({"s1": "font-weight: bold; color: red;", "s2": " "})
    assert css == ".s1 {\n  font-weight: bold;\n  color: red;\n}\n\n.s2 {\n}\n"
