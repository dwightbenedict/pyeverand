import pytest

from everand_books.config import load_settings


def test_settings_read_prefixed_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVERAND_BOOKS_SESSION_TOKEN", "token")
    monkeypatch.setenv("EVERAND_BOOKS_USER_ID", "7")
    monkeypatch.setenv("EVERAND_BOOKS_HTTP_MAX_ATTEMPTS", "5")

    settings = load_settings()

    assert (settings.session_token, settings.user_id, settings.http_max_attempts) == (
        "token",
        "7",
        5,
    )
    assert settings.base_url == "https://www.everand.com"


def test_settings_read_legacy_variable_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVERAND__SESSION_TOKEN", "old-token")
    monkeypatch.setenv("EVERAND__USER_ID", "8")
    monkeypatch.setenv("EVERAND__ACCESS_TOKEN_TTLS", "120")
    monkeypatch.setenv("HTTP__TIMEOUT", "12")
    monkeypatch.setenv("HTTP__MAX_RETRIES", "4")
    monkeypatch.setenv("HTTP__MAX_RETRY_DELAY", "6")

    settings = load_settings()

    assert (settings.session_token, settings.user_id) == ("old-token", "8")
    assert settings.access_token_ttl_seconds == 120
    assert settings.http_timeout_seconds == 12
    assert settings.http_max_attempts == 4
    assert settings.http_max_retry_delay_seconds == 6


def test_settings_reject_an_unknown_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVERAND_BOOKS_SESSION_TOKEN", "token")
    monkeypatch.setenv("EVERAND_BOOKS_USER_ID", "7")
    monkeypatch.setenv("EVERAND_BOOKS_LOG_LEVEL", "LOUD")

    with pytest.raises(ValueError, match="EVERAND_BOOKS_LOG_LEVEL"):
        load_settings()
