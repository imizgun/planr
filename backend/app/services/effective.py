"""Computation of the 'effective' block of a schedule item (source data + remark patch)."""
import datetime as dt
from typing import Any

ACADEMIC_HOUR_MINUTES = 45  # 'czas' counts academic hours; block starts at the full hour 'godz'
DEFAULT_MODE = "stationary"
PATCHABLE_FIELDS = ("start_time", "end_time", "mode")


def _format(minutes: int) -> str:
    minutes = min(minutes, 24 * 60 - 1)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def default_times(start_hour: int, hour_count: int) -> tuple[str, str]:
    start = start_hour * 60
    return _format(start), _format(start + hour_count * ACADEMIC_HOUR_MINUTES)


def compute_effective(
    *,
    weekday: int | None,
    start_hour: int,
    hour_count: int,
    date_from: dt.date | None,
    date_to: dt.date | None,
    patch: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Returns (effective, patched_fields). A field is 'patched' only if the patch changes its default."""
    start, end = default_times(start_hour, hour_count)
    defaults = {"start_time": start, "end_time": end, "mode": DEFAULT_MODE}
    values = {field: patch.get(field, default) for field, default in defaults.items()}
    effective = {
        "weekday": weekday,
        **values,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }
    patched = [field for field in PATCHABLE_FIELDS if values[field] != defaults[field]]
    return effective, patched
