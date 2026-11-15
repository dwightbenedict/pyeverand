import json
import logging

import pytest

from everand_books.config import Settings, load_settings
from everand_books.logging_config import configure_logging


def _settings(monkeypatch: pytest.MonkeyPatch, **env: str) -> Settings:
    credentials = {"SESSION_TOKEN": "token", "USER_ID": "7"}

    for key, value in (credentials | env).items():
        monkeypatch.setenv(f"EVERAND_BOOKS_{key}", value)

    return load_settings()


def test_configure_logging_writes_text_lines_to_stderr(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging(_settings(monkeypatch))
    logging.getLogger("demo").info("started %s", "ok")
    assert capsys.readouterr().err.endswith("INFO demo: started ok\n")


def test_configure_logging_drops_records_below_the_level(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging(_settings(monkeypatch, LOG_LEVEL="WARNING"))
    logging.getLogger("demo").info("quiet")
    logging.getLogger("demo").warning("loud")
    assert capsys.readouterr().err.endswith("WARNING demo: loud\n")


def test_configure_logging_replaces_earlier_handlers(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging(_settings(monkeypatch))
    configure_logging(_settings(monkeypatch))
    logging.getLogger("demo").info("once")
    assert capsys.readouterr().err.count("once") == 1


def test_json_format_writes_one_object_per_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging(_settings(monkeypatch, LOG_FORMAT="json"))
    logging.getLogger("demo").info("started %s", "ok")
    entry = json.loads(capsys.readouterr().err)
    assert entry["level"] == "INFO"
    assert entry["logger"] == "demo"
    assert entry["message"] == "started ok"
    assert entry["time"].endswith("+00:00")
    assert "exception" not in entry


def test_json_format_includes_the_traceback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging(_settings(monkeypatch, LOG_FORMAT="json"))

    try:
        raise ValueError("boom")  # noqa: TRY301, EM101
    except ValueError:
        logging.getLogger("demo").exception("failed")

    entry = json.loads(capsys.readouterr().err)
    assert "ValueError: boom" in entry["exception"]
