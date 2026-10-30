from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Every value can be overridden with a PLANR_* environment variable."""

    model_config = SettingsConfigDict(env_prefix="PLANR_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://planr:planr@localhost:5432/planr"
    source_main_plan_url: str = "https://inf.ug.edu.pl/plan/?student=.*&seminarium=.&fakultet=.&format=csv"
    # Pages listing programmes ('?grupa=<id>' links); each subsite has its own update timestamp.
    source_hub_urls: list[str] = [
        "https://inf.ug.edu.pl/plan/?dialog=grupa",
        "https://inf.ug.edu.pl/plan/fiz/",
    ]
    source_timeout_seconds: float = 30.0
    timezone: str = "Europe/Warsaw"
    schema_version: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
