import datetime as dt

from sqlalchemy import and_, or_, select, true
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.ids import course_public_id, group_public_id, parse_course_id, parse_group_id, teacher_public_id
from app.models import Course, Group, Program, Slot, SlotTarget, SlotTeacher
from app.schemas import (
    Block,
    CourseRef,
    Effective,
    ItemGroup,
    ProgramRef,
    Remark,
    ScheduleItem,
    ScheduleResponse,
    ScheduleSource,
    TeacherRef,
)
from app.services.common import current_snapshot, iso_utc
from app.services.effective import compute_effective


class UnknownProgramError(Exception):
    pass


class InvalidQueryError(Exception):
    pass


def _load_groups(session: Session, raw_ids: list[str], *, program_id: str) -> dict[int, Group]:
    ids: list[int] = []
    for raw in raw_ids:
        try:
            ids.append(parse_group_id(raw))
        except ValueError as exc:
            raise InvalidQueryError(str(exc)) from exc
    groups = {g.id: g for g in session.scalars(select(Group).where(Group.id.in_(ids)))}
    for raw, group_id in zip(raw_ids, ids):
        group = groups.get(group_id)
        if group is None or group.program_id != program_id:
            raise InvalidQueryError(f"Group {raw!r} does not belong to program {program_id!r}")
    return groups


def _parse_electives(session: Session, raw_values: list[str]) -> list[tuple[int, int | None]]:
    """Accepts <courseId>:<groupId>, or a bare <courseId> for courses that have no groups."""
    pairs: list[tuple[int, int | None]] = []
    for raw in raw_values:
        course_part, sep, group_part = raw.partition(":")
        try:
            pairs.append((parse_course_id(course_part), parse_group_id(group_part) if sep else None))
        except ValueError as exc:
            raise InvalidQueryError(str(exc)) from exc

    wanted = [g for _, g in pairs if g is not None]
    groups = {g.id: g for g in session.scalars(select(Group).where(Group.id.in_(wanted)))}
    for raw, (course_id, group_id) in zip(raw_values, pairs):
        if group_id is None:
            has_groups = session.scalar(select(Group.id).where(Group.course_id == course_id).limit(1))
            if has_groups is not None:
                raise InvalidQueryError(f"Elective {raw!r} has groups; use <courseId>:<groupId>")
            if session.get(Course, course_id) is None:
                raise InvalidQueryError(f"Unknown course {raw!r}")
        else:
            group = groups.get(group_id)
            if group is None or group.course_id != course_id:
                raise InvalidQueryError(f"Group of elective {raw!r} does not belong to the course")
    return pairs


def _item(slot: Slot, group: ItemGroup | None) -> ScheduleItem:
    remark = slot.remark
    patch = remark.patch if remark else {}
    effective, patched = compute_effective(
        weekday=slot.weekday,
        start_hour=slot.start_hour,
        hour_count=slot.hour_count,
        date_from=slot.date_from,
        date_to=slot.date_to,
        patch=patch,
    )
    return ScheduleItem(
        id=slot.id,
        course=CourseRef(id=course_public_id(slot.course.id), name=slot.course.name),
        type=slot.type,
        group=group,
        teachers=[
            TeacherRef(id=teacher_public_id(link.teacher.id), name=link.teacher.name) for link in slot.teacher_links
        ],
        room=slot.room,
        block=Block(weekday=slot.weekday, start_hour=slot.start_hour, count=slot.hour_count),
        effective=Effective(**effective),
        patched_fields=patched,
        remark=Remark(
            raw=(remark.raw or None) if remark else None,
            parse_status=remark.parse_status if remark else "ok",
            unparsed=remark.unparsed if remark else None,
            needs_review=remark.needs_review if remark else False,
        ),
        proposals=[],
    )


def build_schedule(
    session: Session,
    *,
    program_id: str,
    group_ids: list[str],
    electives: list[str],
    date_from: dt.date | None,
    date_to: dt.date | None,
) -> ScheduleResponse:
    snapshot = current_snapshot(session)
    program = session.get(Program, program_id)
    if program is None:
        raise UnknownProgramError(program_id)
    if date_from and date_to and date_from > date_to:
        raise InvalidQueryError("'from' must not be later than 'to'")

    groups = _load_groups(session, group_ids, program_id=program_id)
    elective_pairs = _parse_electives(session, electives)

    conditions = [Slot.is_active.is_(True), Slot.weekday.is_not(None)]
    if date_from:
        conditions.append(or_(Slot.date_to.is_(None), Slot.date_to >= date_from))
    if date_to:
        conditions.append(or_(Slot.date_from.is_(None), Slot.date_from <= date_to))

    loaders = (
        selectinload(Slot.course),
        selectinload(Slot.teacher_links).selectinload(SlotTeacher.teacher),
        selectinload(Slot.remark),
        selectinload(Slot.elective_group),
        selectinload(Slot.targets).selectinload(SlotTarget.group),
    )

    items: dict[str, ScheduleItem] = {}

    program_slots = session.scalars(
        select(Slot)
        .join(SlotTarget)
        .where(
            *conditions,
            SlotTarget.program_id == program_id,
            or_(SlotTarget.group_id.is_(None), SlotTarget.group_id.in_(list(groups))),
        )
        .options(*loaders)
    ).unique()
    for slot in program_slots:
        matching = [
            t for t in slot.targets
            if t.program_id == program_id and (t.group_id is None or t.group_id in groups)
        ]
        specific = next((t for t in matching if t.group_id is not None), None)
        group = (
            ItemGroup(id=group_public_id(specific.group.id, None), label=specific.group.label, program_wide=False)
            if specific
            else ItemGroup(id=None, label=None, program_wide=True)
        )
        items[slot.id] = _item(slot, group)

    if elective_pairs:
        elective_slots = session.scalars(
            select(Slot)
            .where(
                *conditions,
                Slot.is_elective.is_(True),
                or_(
                    *(
                        and_(
                            Slot.course_id == course_id,
                            or_(Slot.elective_group_id.is_(None), Slot.elective_group_id == group_id)
                            if group_id is not None
                            else true(),
                        )
                        for course_id, group_id in elective_pairs
                    )
                ),
            )
            .options(*loaders)
        )
        for slot in elective_slots:
            eg = slot.elective_group
            group = (
                ItemGroup(id=group_public_id(eg.id, eg.course_id), label=eg.label, program_wide=False) if eg else None
            )
            items.setdefault(slot.id, _item(slot, group))

    ordered = sorted(
        items.values(),
        key=lambda i: (i.effective.weekday, i.effective.start_time, i.course.name, i.id),
    )
    settings = get_settings()
    return ScheduleResponse(
        schema_version=settings.schema_version,
        program=ProgramRef(id=program.id, name=program.name),
        source=ScheduleSource(
            version=snapshot.version, fetched_at=iso_utc(snapshot.fetched_at), timezone=settings.timezone
        ),
        items=ordered,
    )
