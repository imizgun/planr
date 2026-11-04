from pathlib import Path

from sqlalchemy import func, select

from app.models import Slot, SlotTeacher, Teacher
from app.parsing.teachers import split_teachers
from app.services.ingest import ingest

FIZYKA = Path(__file__).parent / "fixtures" / "fizyka_I_rok.csv"
PAIR = ["dr inż. Krzysztof Dorywalski", "dr Sławomir Werbowy"]


def test_split_teachers():
    assert split_teachers("") == []
    assert split_teachers("dr Jan Kowalski") == ["dr Jan Kowalski"]
    assert split_teachers("dr A + dr B+ ") == ["dr A", "dr B"]
    assert split_teachers("dr A+dr A") == ["dr A"]
    assert split_teachers("dr Jakub Neumann, prof. UG") == ["dr Jakub Neumann, prof. UG"]  # comma is not a separator


def test_multi_teacher_slot_is_stored_in_order(session):
    ingest(session, FIZYKA.read_bytes())
    slot = session.scalars(select(Slot).join(SlotTeacher).group_by(Slot.id).having(func.count() == 2)).one()
    names = [link.teacher.name for link in slot.teacher_links]
    assert names == PAIR
    assert session.scalar(select(func.count()).select_from(Teacher).where(Teacher.name.contains("+"))) == 0


def test_schedule_returns_teacher_list(client, session):
    ingest(session, FIZYKA.read_bytes())
    items = client.get("/api/v1/schedule", params={"program": "fizyka-1"}).json()["items"]
    pair = next(i for i in items if len(i["teachers"]) == 2)
    assert [t["name"] for t in pair["teachers"]] == PAIR
    assert len({t["id"] for t in pair["teachers"]}) == 2 and all(t["id"].startswith("t_") for t in pair["teachers"])
    assert all(isinstance(i["teachers"], list) for i in items)


def test_teachers_follow_the_latest_dump(session):
    text = FIZYKA.read_text(encoding="utf-8")
    ingest(session, text.encode())
    swapped = text.replace("dr inż. Krzysztof Dorywalski+dr Sławomir Werbowy", "dr Sławomir Werbowy")
    report = ingest(session, swapped.encode())
    assert report.status == "ingested"
    counts = [len(s.teacher_links) for s in session.scalars(select(Slot).where(Slot.is_active))]
    assert max(counts) == 1
