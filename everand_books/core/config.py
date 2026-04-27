from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class EverandConfig(BaseModel):
    base_url: str = "https://www.everand.com"
    session_token: str
    user_id: str
    access_token_ttls: int = 540  # 10 minutes - 1 minute buffer


class HTTPConfig(BaseModel):
    timeout: int
    max_retries: int
    max_retry_delay: int


class Config(BaseSettings):
    everand: EverandConfig
    http: HTTPConfig

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__"
    )


config = Config()