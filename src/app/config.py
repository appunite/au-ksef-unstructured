from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_VALID_STRATEGIES = {"auto", "fast", "ocr_only"}
_DEPRECATED_STRATEGIES = {"hi_res": "auto"}


class Settings(BaseSettings):
    api_token: str
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    log_level: str = "INFO"
    default_strategy: Literal["auto", "fast", "ocr_only"] = "fast"
    default_languages: list[str] = ["eng", "pol"]
    max_upload_size_mb: int = 10
    anthropic_timeout: int = 120

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def normalize_strategy(cls, values: dict) -> dict:
        strategy = values.get("default_strategy")
        if strategy and strategy not in _VALID_STRATEGIES:
            replacement = _DEPRECATED_STRATEGIES.get(strategy)
            if replacement:
                values["default_strategy"] = replacement
            else:
                raise ValueError(
                    f"Unknown default_strategy '{strategy}'. "
                    f"Must be one of: {', '.join(sorted(_VALID_STRATEGIES))}"
                )
        return values


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
