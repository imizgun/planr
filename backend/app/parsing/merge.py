"""Merging of several plan dumps (one per source subsite) into a single list of rows."""
import dataclasses
import re
from collections import defaultdict
from collections.abc import Sequence

from app.parsing.csv_reader import RawRow

_SEPARATOR = re.compile(r"\s*[/+]\s*")


def _key(row: RawRow) -> tuple:
    """Everything that identifies a class except the 'grupa' column (which differs between dumps)."""
    return (
        row.day, row.start_hour, row.hour_count, row.course, row.teacher,
        row.room, row.type, row.remark.strip(), row.date_from, row.date_to,
    )


def _combine(first: RawRow, second: RawRow) -> RawRow:
    """One row targeting the union of both group lists."""
    if first.group == second.group:
        return first
    entries = {e for g in (first.group, second.group) for e in _SEPARATOR.split(g.strip()) if e}
    return dataclasses.replace(first, group="+".join(sorted(entries)))


def merge_sources(sources: Sequence[Sequence[RawRow]]) -> tuple[list[RawRow], int]:
    """Merge dumps; returns (rows, number of merges).

    A row of a later dump is merged into a row of an earlier dump when all columns except 'grupa' are
    equal. Matching is one-to-one per dump, so identical rows repeated *within* one dump stay separate
    (the source does contain such duplicates). Unmatched rows are kept unchanged.
    """
    merged: list[RawRow] = []
    index: dict[tuple, list[int]] = defaultdict(list)  # rows of earlier dumps, by key
    merges = 0
    for source in sources:
        taken: set[int] = set()
        added: list[tuple[tuple, int]] = []
        for row in source:
            key = _key(row)
            position = next((i for i in index.get(key, ()) if i not in taken), None)
            if position is None:
                merged.append(row)
                added.append((key, len(merged) - 1))
            else:
                taken.add(position)
                merged[position] = _combine(merged[position], row)
                merges += 1
        for key, position in added:
            index[key].append(position)
    return merged, merges
