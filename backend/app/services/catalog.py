import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.ids import course_public_id, group_public_id
from app.models import Course, Group, Program, ProgramElective, Slot, SlotTarget
from app.schemas import CatalogElective, CatalogGroup, CatalogProgram, CatalogResponse, SourceInfo
from app.services.common import current_snapshot, iso_utc


def _label_key(label: str) -> list:
    """Natural ordering: 'gr. 2' < 'gr. 10'."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", label)]


def build_catalog(session: Session) -> CatalogResponse:
    snapshot = current_snapshot(session)

    active = (Slot.is_active.is_(True), Slot.weekday.is_not(None))
    program_ids = set(session.scalars(select(SlotTarget.program_id).join(Slot).where(*active)))
    target_group_ids = set(session.scalars(select(SlotTarget.group_id).join(Slot).where(*active)))
    elective_group_ids = set(session.scalars(select(Slot.elective_group_id).where(*active)))
    elective_course_ids = set(session.scalars(select(Slot.course_id).where(*active, Slot.is_elective.is_(True))))

    programs = session.scalars(select(Program).where(Program.id.in_(program_ids)).order_by(Program.name)).all()

    groups_by_program: dict[str, list[Group]] = {}
    for group in session.scalars(select(Group).where(Group.id.in_(target_group_ids))):
        groups_by_program.setdefault(group.program_id, []).append(group)

    course_groups: dict[int, list[Group]] = {}
    for group in session.scalars(select(Group).where(Group.id.in_(elective_group_ids))):
        course_groups.setdefault(group.course_id, []).append(group)

    courses = {c.id: c for c in session.scalars(select(Course).where(Course.id.in_(elective_course_ids)))}
    electives_by_program: dict[str, list[int]] = {}
    for link in session.scalars(select(ProgramElective)):
        if link.course_id in courses:
            electives_by_program.setdefault(link.program_id, []).append(link.course_id)

    def groups_out(groups: list[Group]) -> list[CatalogGroup]:
        ordered = sorted(groups, key=lambda g: _label_key(g.label))
        return [CatalogGroup(id=group_public_id(g.id, g.course_id), label=g.label) for g in ordered]

    result = [
        CatalogProgram(
            id=program.id,
            name=program.name,
            groups=groups_out(groups_by_program.get(program.id, [])),
            electives=[
                CatalogElective(
                    id=course_public_id(course_id),
                    name=courses[course_id].name,
                    groups=groups_out(course_groups.get(course_id, [])),
                )
                for course_id in sorted(electives_by_program.get(program.id, []), key=lambda c: courses[c].name)
            ],
        )
        for program in programs
    ]
    return CatalogResponse(
        schema_version=get_settings().schema_version,
        source=SourceInfo(version=snapshot.version, fetched_at=iso_utc(snapshot.fetched_at)),
        programs=result,
    )
