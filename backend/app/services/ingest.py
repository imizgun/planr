"""Ingestion of the main plan dump: snapshot bookkeeping, normalisation and upsert."""
import datetime as dt
import hashlib
import logging
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Course, Group, Program, Slot, SlotRemark, SlotTarget, SlotTeacher, Snapshot, Teacher
from app.parsing.csv_reader import RawRow, read_rows
from app.parsing.groups import GroupRef, parse_group_field
from app.parsing.remarks import analyze_remark
from app.parsing.teachers import split_teachers
from app.services.crosscheck import cross_check

log = logging.getLogger(__name__)

WEEKDAYS = {  # ISO numbering (Monday = 1)
    "Poniedziałek": 1, "Wtorek": 2, "Środa": 3, "Czwartek": 4, "Piątek": 5, "Sobota": 6, "Niedziela": 7,
}
OFF_GRID_DAY = "TPP"  # rows outside the weekly grid


@dataclass
class IngestReport:
    status: str  # ingested | unchanged
    version: str
    rows: int = 0
    slots_active: int = 0
    slots_deactivated: int = 0
    needs_review: int = 0


def content_version(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:6]


def _slot_id(row: RawRow, elective_group: str | None, ordinal: int) -> str:
    """Stable identifier. Excludes room, duration, remark and dates, which are likely to change."""
    parts = [row.day, str(row.start_hour), row.course, row.type, row.group, row.teacher, elective_group or ""]
    if ordinal:
        parts.append(f"#{ordinal}")
    return "slot_" + hashlib.sha1("|".join(parts).encode()).hexdigest()[:8]


class _Lookups:
    """Get-or-create helpers with in-memory caches (the dataset is small)."""

    def __init__(self, session: Session, program_ids: Mapping[str, str]) -> None:
        self.session = session
        self.program_ids = program_ids
        self._warned_programs: set[str] = set()
        self.programs = {p.name: p for p in session.scalars(select(Program))}
        self.courses = {c.name: c for c in session.scalars(select(Course))}
        self.teachers = {t.name: t for t in session.scalars(select(Teacher))}
        self.program_groups = {(g.program_id, g.label): g for g in session.scalars(select(Group)) if g.program_id}
        self.course_groups = {(g.course_id, g.label): g for g in session.scalars(select(Group)) if g.course_id}

    def program(self, ref: GroupRef) -> Program:
        """Programmes are keyed by name. The id is the site id when known, otherwise a slug.

        The id of an existing programme never changes. A warning is logged (once per programme) only
        when a site id was supplied and differs from the stored id; without a mapping (offline ingest)
        the slug is merely a fallback for new programmes, so there is nothing to compare.
        """
        site_id = self.program_ids.get(ref.program_name)
        program = self.programs.get(ref.program_name)
        if program is None:
            program = self.programs[ref.program_name] = Program(id=site_id or ref.program_id, name=ref.program_name)
            self.session.add(program)
            self.session.flush()
        elif site_id and program.id != site_id and ref.program_name not in self._warned_programs:
            self._warned_programs.add(ref.program_name)
            log.warning("Programme %r keeps id %r (site id is %r)", program.name, program.id, site_id)
        return program

    def course(self, name: str) -> Course:
        course = self.courses.get(name)
        if course is None:
            course = self.courses[name] = Course(name=name)
            self.session.add(course)
            self.session.flush()
        return course

    def teacher(self, name: str) -> Teacher:
        teacher = self.teachers.get(name)
        if teacher is None:
            teacher = self.teachers[name] = Teacher(name=name)
            self.session.add(teacher)
            self.session.flush()
        return teacher

    def program_group(self, program_id: str, label: str) -> Group:
        group = self.program_groups.get((program_id, label))
        if group is None:
            group = self.program_groups[(program_id, label)] = Group(program_id=program_id, label=label)
            self.session.add(group)
            self.session.flush()
        return group

    def course_group(self, course_id: int, label: str) -> Group:
        group = self.course_groups.get((course_id, label))
        if group is None:
            group = self.course_groups[(course_id, label)] = Group(course_id=course_id, label=label)
            self.session.add(group)
            self.session.flush()
        return group


def ingest(
    session: Session,
    content: bytes,
    *,
    fetched_at: dt.datetime | None = None,
    force: bool = False,
    program_ids: Mapping[str, str] | None = None,
) -> IngestReport:
    """Ingest a CSV dump. Unchanged content only refreshes fetched_at unless force is set.

    program_ids maps programme names to the source website's ids (see fetcher.electives).
    """
    fetched_at = fetched_at or dt.datetime.now(dt.timezone.utc)
    version = content_version(content)
    rows = read_rows(content.decode("utf-8-sig"))  # validate before touching the database

    current = session.scalar(select(Snapshot).where(Snapshot.is_current))
    if current is not None and current.version == version and not force:
        current.fetched_at = fetched_at
        session.commit()
        return IngestReport(
            status="unchanged", version=version, rows=current.row_count, slots_active=current.row_count
        )

    if current is not None:
        current.is_current = False
    snapshot = Snapshot(version=version, fetched_at=fetched_at, row_count=len(rows), is_current=True)
    session.add(snapshot)
    session.flush()

    lookups = _Lookups(session, program_ids or {})
    existing = {slot.id: slot for slot in session.scalars(select(Slot))}
    existing_remarks = {r.slot_id: r for r in session.scalars(select(SlotRemark))}
    session.execute(delete(SlotTarget))  # rebuilt below from the new dump
    session.execute(delete(SlotTeacher))

    seen_counts: dict[str, int] = {}
    needs_review = 0

    for row in rows:
        refs = parse_group_field(row.group)
        remark = analyze_remark(row.remark)
        is_elective = not refs
        elective_label = remark.extras.get("elective_group") if is_elective else None

        base_id = _slot_id(row, elective_label, 0)
        ordinal = seen_counts.get(base_id, 0)
        seen_counts[base_id] = ordinal + 1
        slot_id = _slot_id(row, elective_label, ordinal)

        course = lookups.course(row.course)
        teachers = [lookups.teacher(name) for name in split_teachers(row.teacher)]
        elective_group = lookups.course_group(course.id, elective_label) if elective_label else None

        if row.day not in WEEKDAYS and row.day != OFF_GRID_DAY:
            log.warning("Line %d: unknown day %r, slot kept off the weekly grid", row.line_no, row.day)

        slot = existing.get(slot_id)
        if slot is None:
            slot = existing[slot_id] = Slot(id=slot_id, first_seen_snapshot_id=snapshot.id)
            session.add(slot)
        slot.course_id = course.id
        slot.elective_group_id = elective_group.id if elective_group else None
        slot.is_elective = is_elective
        slot.type = row.type or None
        slot.room = row.room or None
        slot.weekday = WEEKDAYS.get(row.day)
        slot.start_hour = row.start_hour
        slot.hour_count = row.hour_count
        slot.date_from = row.date_from
        slot.date_to = row.date_to
        slot.source_group = row.group
        slot.is_active = True
        slot.last_seen_snapshot_id = snapshot.id
        session.flush()

        for position, teacher in enumerate(teachers):
            session.add(SlotTeacher(slot_id=slot_id, teacher_id=teacher.id, position=position))

        for ref in refs:
            program = lookups.program(ref)
            group = lookups.program_group(program.id, ref.label) if ref.label else None
            session.add(SlotTarget(slot_id=slot_id, program_id=program.id, group_id=group.id if group else None))

        additions, conflicts = cross_check(
            remark.extras, date_from=row.date_from, date_to=row.date_to, has_program_groups=bool(refs)
        )
        extras = {**remark.extras, **additions}
        if conflicts:
            extras["conflicts"] = conflicts
        review = remark.needs_review or bool(conflicts)
        needs_review += review

        record = existing_remarks.get(slot_id)
        if record is None:
            record = existing_remarks[slot_id] = SlotRemark(slot_id=slot_id)
            session.add(record)
        record.raw = row.remark
        record.parse_status = remark.parse_status
        record.unparsed = "; ".join(remark.unparsed) or None
        record.needs_review = review
        record.patch = remark.patch
        record.extras = extras
        record.stage = remark.stages[0] if remark.stages else "regex"

    deactivated = 0
    for slot in existing.values():
        if slot.last_seen_snapshot_id != snapshot.id and slot.is_active:
            slot.is_active = False
            deactivated += 1

    session.commit()
    return IngestReport(
        status="ingested",
        version=version,
        rows=len(rows),
        slots_active=len(rows),
        slots_deactivated=deactivated,
        needs_review=needs_review,
    )
