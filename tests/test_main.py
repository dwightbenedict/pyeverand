from everand_books import __main__ as entry_point
from everand_books.interfaces import cli


def test_entry_point_delegates_to_cli_main() -> None:
    assert entry_point.main is cli.main
