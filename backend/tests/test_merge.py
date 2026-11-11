import datetime as dt

from app.parsing.csv_reader import RawRow
from app.parsing.merge import merge_sources


def row(group: str, **overrides) -> RawRow:
    values = dict(
        line_no=2, day="Piątek", start_hour=14, hour_count=2, course="Filozofia nauki", group=group,
        teacher="dr Jan Kowalski", room="D003", type="wykład", remark="",
        date_from=dt.date(2026, 10, 2), date_to=dt.date(2027, 1, 29),
    )
    values.update(overrides)
    return RawRow(**values)


def test_same_class_in_two_dumps_is_merged_into_the_union_of_groups():
    rows, merges = merge_sources([[row("a: I rok+b: I rok")], [row("c: I rok+a: I rok")]])
    assert merges == 1 and len(rows) == 1
    assert rows[0].group == "a: I rok+b: I rok+c: I rok"  # sorted, no duplicates


def test_identical_group_text_is_left_untouched():
    rows, merges = merge_sources([[row("b: I rok/a: I rok")], [row("b: I rok/a: I rok")]])
    assert merges == 1 and rows[0].group == "b: I rok/a: I rok"


def test_rows_differing_in_any_other_column_are_not_merged():
    for change in (dict(room="D004"), dict(teacher="dr Anna Nowak"), dict(start_hour=16), dict(remark="zajęcia zdalne"),
                   dict(date_to=dt.date(2027, 1, 30)), dict(type="ćwiczenia"), dict(hour_count=1)):
        rows, merges = merge_sources([[row("a: I rok")], [row("b: I rok", **change)]])
        assert merges == 0 and len(rows) == 2, change


def test_duplicates_within_one_dump_are_preserved():
    rows, merges = merge_sources([[row("a: I rok"), row("a: I rok")], [row("b: I rok")]])
    assert merges == 1 and len(rows) == 2  # the second dump matches only one of the two
    assert sorted(r.group for r in rows) == ["a: I rok", "a: I rok+b: I rok"]


def test_unmatched_rows_keep_their_order_and_a_single_dump_is_unchanged():
    first = [row("a: I rok", course="X"), row("a: I rok", course="Y")]
    second = [row("b: I rok", course="Z")]
    rows, merges = merge_sources([first, second])
    assert [r.course for r in rows] == ["X", "Y", "Z"] and merges == 0
    assert merge_sources([first]) == (first, 0)
    assert merge_sources([]) == ([], 0)


def test_remark_whitespace_does_not_prevent_a_merge():
    rows, merges = merge_sources([[row("a: I rok", remark=" 8.30-10.00")], [row("b: I rok", remark="8.30-10.00")]])
    assert merges == 1
