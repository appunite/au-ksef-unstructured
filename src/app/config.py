from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_token: str
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    log_level: str = "INFO"
    # auto | fast | ocr_only | hi_res
    default_strategy: str = "auto"
    default_languages: list[str] = ["eng", "pol"]
    default_pdf_infer_table_structure: bool = True

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
