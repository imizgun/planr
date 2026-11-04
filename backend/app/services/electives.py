"""Persisting the programme -> elective course assignment produced by the crawl."""
import logging
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.fetcher.electives import ElectiveCrawl
from app.models import Course, Program, ProgramElective

log = logging.getLogger(__name__)


@dataclass
class LinkReport:
    programs_linked: int = 0
    links: int = 0
    unknown_programs: list[str] = field(default_factory=list)  # in the crawl, absent from the main dump
    unknown_courses: list[str] = field(default_factory=list)  # in elective CSVs, absent from the main dump


def link_electives(session: Session, crawl: ElectiveCrawl) -> LinkReport:
    """Replace the elective assignment of every crawled programme (matching by programme / course name)."""
    programs = {p.name: p for p in session.scalars(select(Program))}
    courses = {c.name: c for c in session.scalars(select(Course))}
    report = LinkReport()
    unknown_courses: dict[str, None] = {}

    for crawled in crawl.programs:
        program = programs.get(crawled.name)
        if program is None:
            report.unknown_programs.append(crawled.name)
            continue
        session.execute(delete(ProgramElective).where(ProgramElective.program_id == program.id))
        linked = set()
        for name in crawled.courses:
            course = courses.get(name)
            if course is None:
                unknown_courses.setdefault(name)
                continue
            linked.add(course.id)
        session.add_all(ProgramElective(program_id=program.id, course_id=course_id) for course_id in sorted(linked))
        report.programs_linked += 1
        report.links += len(linked)

    report.unknown_courses = list(unknown_courses)
    if report.unknown_courses:
        log.warning("Elective courses missing from the main dump: %s", report.unknown_courses)
    session.commit()
    return report
