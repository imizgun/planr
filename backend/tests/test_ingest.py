import pytest
from sqlalchemy import func, select

from app.models import Slot, SlotRemark, Snapshot
from app.parsing.csv_reader import SourceFormatError
from app.services.ingest import ingest


def test_first_ingest(session, loaded):
    assert loaded.status == "ingested"
    assert loaded.rows == 400 and loaded.slots_active == 400
    assert loaded.needs_review == 2  # only genuinely unrecognised remarks remain
    assert session.scalar(select(func.count()).select_from(Slot).where(Slot.is_active)) == 400
    assert session.scalar(select(func.count()).select_from(Slot).where(Slot.weekday.is_(None))) == 6  # 'TPP' rows
    assert len(loaded.version) == 6


def test_identical_content_is_a_noop(session, loaded, csv_bytes):
    report = ingest(session, csv_bytes)
    assert report.status == "unchanged"
    assert session.scalar(select(func.count()).select_from(Snapshot)) == 1


def test_force_creates_new_snapshot_without_deactivation(session, loaded, csv_bytes):
    report = ingest(session, csv_bytes, force=True)
    assert report.status == "ingested" and report.slots_deactivated == 0
    assert session.scalar(select(func.count()).select_from(Snapshot).where(Snapshot.is_current)) == 1
    assert session.scalar(select(func.count()).select_from(Slot)) == 400


def test_slot_ids_survive_room_changes_and_removed_rows_are_deactivated(session, loaded, csv_bytes):
    before = {slot.id: slot.room for slot in session.scalars(select(Slot))}
    lines = csv_bytes.decode().splitlines()
    lines.pop(10)  # drop one row
    index = next(i for i, line in enumerate(lines) if ",1.14," in line)
    lines[index] = lines[index].replace(",1.14,", ",9.99,", 1)  # move one row to another room

    report = ingest(session, "\n".join(lines).encode())

    assert report.status == "ingested" and report.slots_deactivated == 1
    after = {slot.id: slot for slot in session.scalars(select(Slot))}
    assert set(after) == set(before)  # no new ids: the room change did not alter identity
    assert sum(1 for slot in after.values() if not slot.is_active) == 1
    assert [s for s in after.values() if s.room == "9.99" and before[s.id] == "1.14"]


def test_remark_results_are_stored(session, loaded):
    patched = session.scalars(select(SlotRemark).where(SlotRemark.raw == "14.30-16.00")).first()
    assert patched.patch == {"start_time": "14:30", "end_time": "16:00"}
    assert patched.parse_status == "ok" and not patched.needs_review
    assert not any("conflicts" in r.extras for r in session.scalars(select(SlotRemark)))


def test_invalid_header_is_rejected_before_any_write(session):
    with pytest.raises(SourceFormatError):
        ingest(session, b"<html>not a csv</html>")
    assert session.scalar(select(func.count()).select_from(Snapshot)) == 0


def test_two_dumps_are_ingested_as_one_snapshot(session, csv_bytes, fiz_bytes):
    report = ingest(session, [csv_bytes, fiz_bytes])
    assert report.status == "ingested"
    assert report.merged_rows == 7 and report.rows == 400 + 268 - 7
    assert session.scalar(select(func.count()).select_from(Snapshot)) == 1
    assert report.version != ingest(session, csv_bytes, force=True).version  # version covers all sources


def test_merged_class_targets_the_union_of_programs(session, csv_bytes, fiz_bytes):
    from app.models import Course, Program, SlotTarget

    ingest(session, [csv_bytes, fiz_bytes])
    course = session.scalar(select(Course).where(Course.name == "Filozofia nauki"))
    slot = session.scalars(select(Slot).where(Slot.course_id == course.id)).one()
    names = {session.get(Program, t.program_id).name for t in session.scalars(select(SlotTarget).where(SlotTarget.slot_id == slot.id))}
    assert names == {
        "fizyka II st.: I rok", "informatyka 2 st.: I rok", "matematyka 2 st.: I rok", "fizyka medyczna II st.: II rok",
    }


def test_physics_programmes_get_their_classes(client, session, csv_bytes, fiz_bytes):
    ingest(session, [csv_bytes, fiz_bytes])
    catalog = client.get("/api/v1/catalog").json()
    names = {p["name"] for p in catalog["programs"]}
    assert {"bioinformatyka: I rok", "bezpieczeństwo jądrowe: I rok", "fizyka medyczna: I rok"} <= names
    program = next(p for p in catalog["programs"] if p["name"] == "bioinformatyka: I rok")
    params = [("program", program["id"])] + [("group", g["id"]) for g in program["groups"]]
    assert len(client.get("/api/v1/schedule", params=params).json()["items"]) > 0


def test_dump_order_does_not_change_the_slot_ids(session, csv_bytes, fiz_bytes):
    ingest(session, [csv_bytes, fiz_bytes])
    first = set(session.scalars(select(Slot.id)))
    ingest(session, [fiz_bytes, csv_bytes])
    assert set(session.scalars(select(Slot.id).where(Slot.is_active))) == first


def test_invalid_second_dump_is_rejected_before_any_write(session, csv_bytes):
    with pytest.raises(SourceFormatError):
        ingest(session, [csv_bytes, b"<html>error page</html>"])
    assert session.scalar(select(func.count()).select_from(Snapshot)) == 0


def test_fizyka_first_year_matches_the_programme_export(client, session, csv_bytes, fiz_bytes):
    """The physics dump must contain everything the programme's own export (?grupa=1F&format=csv) lists."""
    import csv
    import io
    from pathlib import Path

    ingest(session, [csv_bytes, fiz_bytes])
    catalog = client.get("/api/v1/catalog").json()
    program = next(p for p in catalog["programs"] if p["name"] == "fizyka: I rok")
    params = [("program", program["id"])] + [("group", g["id"]) for g in program["groups"]]
    items = client.get("/api/v1/schedule", params=params).json()["items"]
    api = sorted((i["course"]["name"], i["type"], i["block"]["weekday"], i["block"]["start_hour"]) for i in items)

    export = (Path(__file__).parent / "fixtures" / "fizyka_I_rok.csv").read_text(encoding="utf-8")
    days = {"Poniedziałek": 1, "Wtorek": 2, "Środa": 3, "Czwartek": 4, "Piątek": 5}
    expected = sorted(
        (r["przedmiot"].strip(), r["typ"].strip(), days[r["dzien"]], int(r["godz"]))
        for r in csv.DictReader(io.StringIO(export))
    )
    assert len(expected) == 13 and api == expected
