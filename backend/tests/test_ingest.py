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
