from everand_books import __main__ as entry_point
from everand_books.interfaces.cli import app


def test_entry_point_delegates_to_cli_app() -> None:
    assert entry_point.app is app
