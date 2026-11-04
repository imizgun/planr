"""Consistency checks between remark-derived information and the structured source columns."""
import datetime as dt
from typing import Any


def _resolve(day: int, month: int, start: dt.date | None, end: dt.date | None) -> dt.date | None:
    """Resolve a year-less date against the slot's date range."""
    if start is None or end is None:
        return None
    for year in range(start.year, end.year + 1):
        try:
            candidate = dt.date(year, month, day)
        except ValueError:
            continue
        if start <= candidate <= end:
            return candidate
    return None


def cross_check(
    extras: dict[str, Any],
    *,
    date_from: dt.date | None,
    date_to: dt.date | None,
    has_program_groups: bool,
) -> tuple[dict[str, Any], list[str]]:
    """Returns (extra values to store, conflict messages).

    The 'dataod'/'datado' columns are authoritative; remark dates are validated against them.
    """
    additions: dict[str, Any] = {}
    conflicts: list[str] = []

    for key, column, label in (("date_from_md", date_from, "dataod"), ("date_to_md", date_to, "datado")):
        if key in extras and (column is None or [column.day, column.month] != extras[key]):
            conflicts.append(f"{key} {extras[key]} does not match source column {label} ({column})")

    if "excluded_dates_md" in extras:
        resolved = [_resolve(d, m, date_from, date_to) for d, m in extras["excluded_dates_md"]]
        if all(resolved):
            additions["excluded_dates"] = [d.isoformat() for d in resolved if d]
        else:
            conflicts.append(f"excluded_dates_md {extras['excluded_dates_md']} outside the slot date range")

    if "elective_group" in extras and has_program_groups:
        conflicts.append("group remark on a row that already targets programme groups")

    return additions, conflicts
