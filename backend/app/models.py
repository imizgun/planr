from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

JsonType = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Snapshot(Base):
    """One ingested version of the main plan dump."""

    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(16))  # short content hash
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    row_count: Mapped[int] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)


class Program(Base):
    """A study programme in a given year, e.g. 'informatyka (P): III rok'."""

    __tablename__ = "programs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # slug
    name: Mapped[str] = mapped_column(String(256), unique=True)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(512), unique=True)


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), unique=True)


class Group(Base):
    """A group of a programme (program_id set) or of an elective course (course_id set)."""

    __tablename__ = "groups"
    __table_args__ = (
        CheckConstraint("(program_id IS NULL) <> (course_id IS NULL)", name="exactly_one_parent"),
        UniqueConstraint("program_id", "label"),
        UniqueConstraint("course_id", "label"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[str | None] = mapped_column(ForeignKey("programs.id"), nullable=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True)
    label: Mapped[str] = mapped_column(String(128))


class ProgramElective(Base):
    """Assignment of elective courses to programmes (populated by the elective chain, see docs)."""

    __tablename__ = "program_electives"

    program_id: Mapped[str] = mapped_column(ForeignKey("programs.id"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), primary_key=True)


class Slot(Base):
    """A single timetable row from the source dump."""

    __tablename__ = "slots"
    __table_args__ = (Index("ix_slots_active_elective", "is_active", "is_elective"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # slot_<hash>
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    elective_group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    is_elective: Mapped[bool] = mapped_column(Boolean)
    type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    room: Mapped[str | None] = mapped_column(Text, nullable=True)  # raw; may hold an HTML link
    weekday: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = not on the weekly grid
    start_hour: Mapped[int] = mapped_column(Integer)
    hour_count: Mapped[int] = mapped_column(Integer)
    date_from: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    date_to: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    source_group: Mapped[str] = mapped_column(String(1024), default="")  # raw 'grupa' column
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_snapshot_id: Mapped[int] = mapped_column(ForeignKey("snapshots.id"))
    last_seen_snapshot_id: Mapped[int] = mapped_column(ForeignKey("snapshots.id"))

    course: Mapped[Course] = relationship()
    teacher_links: Mapped[list[SlotTeacher]] = relationship(order_by="SlotTeacher.position")
    elective_group: Mapped[Group | None] = relationship()
    remark: Mapped[SlotRemark | None] = relationship(back_populates="slot", uselist=False)
    targets: Mapped[list[SlotTarget]] = relationship(back_populates="slot")


class SlotTeacher(Base):
    """Teachers of a slot, in the order given by the source."""

    __tablename__ = "slot_teachers"

    slot_id: Mapped[str] = mapped_column(ForeignKey("slots.id"), primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer)

    teacher: Mapped[Teacher] = relationship()


class SlotTarget(Base):
    """Programme (and optionally group) a slot applies to. group_id NULL = whole programme."""

    __tablename__ = "slot_targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    slot_id: Mapped[str] = mapped_column(ForeignKey("slots.id"), index=True)
    program_id: Mapped[str] = mapped_column(ForeignKey("programs.id"), index=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)

    slot: Mapped[Slot] = relationship(back_populates="targets")
    group: Mapped[Group | None] = relationship()


class SlotRemark(Base):
    """Result of the hierarchical remark ('uwagi') analysis for a slot."""

    __tablename__ = "slot_remarks"

    slot_id: Mapped[str] = mapped_column(ForeignKey("slots.id"), primary_key=True)
    raw: Mapped[str] = mapped_column(String(2048), default="")
    parse_status: Mapped[str] = mapped_column(String(16))  # ok | partial | unparsed
    unparsed: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    patch: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)  # fields overriding 'effective'
    extras: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)  # recognised, not yet exposed
    stage: Mapped[str] = mapped_column(String(16), default="regex")  # regex | llm | manual

    slot: Mapped[Slot] = relationship(back_populates="remark")


class SourceStamp(Base):
    """'Aktualizacja danych' footer timestamp last seen per source page (change detection)."""

    __tablename__ = "source_stamps"

    key: Mapped[str] = mapped_column(String(512), primary_key=True)  # page URL
    source_updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
