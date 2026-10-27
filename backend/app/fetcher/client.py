"""HTTP access to the source website."""
from types import TracebackType

import httpx

from app.config import get_settings


class SourceClient:
    """Synchronous client for the source plan website (one connection pool per instance)."""

    def __init__(self, timeout: float | None = None) -> None:
        self._settings = get_settings()
        self._http = httpx.Client(
            timeout=timeout or self._settings.source_timeout_seconds, follow_redirects=True
        )

    def __enter__(self) -> "SourceClient":
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def get_bytes(self, url: str) -> bytes:
        response = self._http.get(url)
        response.raise_for_status()
        return response.content

    def get_text(self, url: str) -> str:
        return self.get_bytes(url).decode("utf-8-sig")

    def fetch_main_plan(self) -> bytes:
        return self.get_bytes(self._settings.source_main_plan_url)
