from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env(name: str, legacy_name: str) -> AliasChoices:
    # The second name is the variable the project read before it adopted the EVERAND_BOOKS_ prefix.
    return AliasChoices(f"EVERAND_BOOKS_{name}", legacy_name)


ENV_FILE = ".env"


class AppOptions(BaseSettings):
    """The settings that need no Everand cookies, so the GUI can start before they exist."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        validation_alias=AliasChoices("EVERAND_BOOKS_LOG_LEVEL"),
    )
    # json: one object per line for log collectors
    log_format: Literal["text", "json"] = Field(
        default="text",
        validation_alias=AliasChoices("EVERAND_BOOKS_LOG_FORMAT"),
    )
    gui_port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        validation_alias=AliasChoices("EVERAND_BOOKS_GUI_PORT"),
    )
    # For development; works only with: python -m everand_books.interfaces.nicegui_app
    gui_reload: bool = Field(
        default=False,
        validation_alias=AliasChoices("EVERAND_BOOKS_GUI_RELOAD"),
    )


class Settings(AppOptions):
    session_token: str = Field(validation_alias=_env("SESSION_TOKEN", "EVERAND__SESSION_TOKEN"))
    user_id: str = Field(validation_alias=_env("USER_ID", "EVERAND__USER_ID"))
    base_url: str = Field(
        default="https://www.everand.com",
        validation_alias=_env("BASE_URL", "EVERAND__BASE_URL"),
    )
    # Everand access tokens last 10 minutes; refresh a minute early.
    access_token_ttl_seconds: float = Field(
        default=540,
        gt=0,
        validation_alias=_env("ACCESS_TOKEN_TTL_SECONDS", "EVERAND__ACCESS_TOKEN_TTLS"),
    )
    http_timeout_seconds: float = Field(
        default=30,
        gt=0,
        validation_alias=_env("HTTP_TIMEOUT_SECONDS", "HTTP__TIMEOUT"),
    )
    http_max_attempts: int = Field(
        default=3,
        ge=1,
        validation_alias=_env("HTTP_MAX_ATTEMPTS", "HTTP__MAX_RETRIES"),
    )
    http_max_retry_delay_seconds: float = Field(
        default=10,
        ge=0,
        validation_alias=_env("HTTP_MAX_RETRY_DELAY_SECONDS", "HTTP__MAX_RETRY_DELAY"),
    )
    http_max_concurrency: int = Field(
        default=8,
        ge=1,
        validation_alias=AliasChoices("EVERAND_BOOKS_HTTP_MAX_CONCURRENCY"),
    )


def load_app_options() -> AppOptions:
    return AppOptions()


def load_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]  required values come from the environment
