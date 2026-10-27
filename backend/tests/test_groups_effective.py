import datetime as dt

from app.parsing.groups import GroupRef, parse_group_field, slugify
from app.services.crosscheck import cross_check
from app.services.effective import compute_effective, default_times


def test_slugify_polish_characters():
    assert slugify("Wydział Łączności (P)") == "wydzial-lacznosci-p"


def test_single_group():
    assert parse_group_field("informatyka (P): I rok gr. 4") == [
        GroupRef("informatyka-p-1", "informatyka (P): I rok", "gr. 4")
    ]


def test_program_wide():
    assert parse_group_field("informatyka (P): II rok") == [GroupRef("informatyka-p-2", "informatyka (P): II rok", None)]


def test_multiple_groups_slash_and_plus():
    refs = parse_group_field(
        "matematyka 2 st.: II rok sp. nauczycielska+matematyka 2 st.: II rok sp. teoretyczna"
        "/informatyka (P): II rok gr. 1"
    )
    assert [(r.program_id, r.label) for r in refs] == [
        ("matematyka-2-st-2", "sp. nauczycielska"),
        ("matematyka-2-st-2", "sp. teoretyczna"),
        ("informatyka-p-2", "gr. 1"),
    ]


def test_numbered_external_entry_is_a_group_of_its_program():
    assert parse_group_field("Biotech 2") == [GroupRef("biotech", "Biotech", "Biotech 2")]
    assert parse_group_field("Biotech") == [GroupRef("biotech", "Biotech", None)]


def test_external_entry_without_number_is_a_program():
    assert parse_group_field("OCEAN") == [GroupRef("ocean", "OCEAN", None)]


def test_empty_group_field():
    assert parse_group_field("") == []


def test_default_times_use_academic_hours():
    assert default_times(8, 2) == ("08:00", "09:30")
    assert default_times(12, 3) == ("12:00", "14:15")
    assert default_times(19, 1) == ("19:00", "19:45")


def test_effective_patched_fields_only_when_value_differs():
    base = dict(weekday=2, start_hour=17, hour_count=2, date_from=dt.date(2026, 10, 6), date_to=None)
    same, patched = compute_effective(**base, patch={"start_time": "17:00", "end_time": "18:30"})
    assert patched == []
    effective, patched = compute_effective(**base, patch={"start_time": "17:30", "end_time": "19:00", "mode": "remote"})
    assert patched == ["start_time", "end_time", "mode"]
    assert effective["mode"] == "remote" and effective["date_to"] is None


def test_cross_check_dates_and_exclusions():
    start, end = dt.date(2026, 10, 2), dt.date(2026, 11, 27)
    additions, conflicts = cross_check(
        {"date_to_md": [27, 11], "excluded_dates_md": [[9, 10]]}, date_from=start, date_to=end, has_program_groups=True
    )
    assert additions == {"excluded_dates": ["2026-10-09"]} and conflicts == []
    _, conflicts = cross_check({"date_to_md": [26, 11]}, date_from=start, date_to=end, has_program_groups=True)
    assert len(conflicts) == 1
    _, conflicts = cross_check({"elective_group": "gr. 1"}, date_from=start, date_to=end, has_program_groups=True)
    assert len(conflicts) == 1
