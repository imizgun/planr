from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceSite(BaseModel):
    """A subsite of the plan system: its hub page (programme links, update timestamp) and its plan dump."""

    hub_url: str
    plan_url: str


class Settings(BaseSettings):
    """Runtime configuration. Every value can be overridden with a PLANR_* environment variable."""

    model_config = SettingsConfigDict(env_prefix="PLANR_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://planr:planr@localhost:5432/planr"
    # Each subsite has its own data and its own update timestamp. Override with a JSON list.
    source_sites: list[SourceSite] = [
        SourceSite(
            hub_url="https://inf.ug.edu.pl/plan/?dialog=grupa",
            plan_url="https://inf.ug.edu.pl/plan/?student=.*&seminarium=.&fakultet=.&format=csv",
        ),
        SourceSite(
            hub_url="https://inf.ug.edu.pl/plan/fiz/",
            plan_url="https://inf.ug.edu.pl/plan/fiz/?student=.*&seminarium=.&fakultet=.&format=csv",
        ),
    ]
    source_timeout_seconds: float = 30.0
    timezone: str = "Europe/Warsaw"
    schema_version: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
