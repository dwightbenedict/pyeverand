from pyeverand import __main__ as entry_point
from pyeverand.interfaces import cli


def test_entry_point_delegates_to_cli_main() -> None:
    assert entry_point.main is cli.main
