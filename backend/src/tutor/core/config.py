"""Konfiguration aus Umgebungsvariablen (Zwölf-Faktoren-Prinzip)."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_MIN_SECRET_LENGTH = 16


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    environment: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"

    database_url: str

    llm_base_url: str
    llm_api_key: SecretStr
    llm_model: str = "tutor"
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2

    api_token: SecretStr
    # Origins, die das Backend aus dem Browser aufrufen dürfen (Allowlist, nie "*").
    # Format in der Umgebung als JSON-Liste: CORS_ORIGINS='["http://localhost:5173"]'
    cors_origins: list[str] = []
    default_user_id: str = "default"

    max_turns_per_session: int = 60
    history_window: int = 20

    @field_validator("api_token")
    @classmethod
    def _api_token_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < _MIN_SECRET_LENGTH:
            raise ValueError(f"API_TOKEN muss mindestens {_MIN_SECRET_LENGTH} Zeichen haben")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # Pflichtfelder kommen aus der Umgebung
