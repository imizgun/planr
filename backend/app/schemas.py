"""Response models of the public API (see project documentation, section 'Dokumentacja endpointów')."""
from pydantic import BaseModel


class SourceInfo(BaseModel):
    version: str
    fetched_at: str  # ISO 8601, UTC


class ScheduleSource(SourceInfo):
    timezone: str


# --- GET /api/v1/catalog ---------------------------------------------------------------------


class CatalogGroup(BaseModel):
    id: str
    label: str


class CatalogElective(BaseModel):
    id: str
    name: str
    groups: list[CatalogGroup]
    # 'teachers' and 'summary' are planned for a later phase (see documentation) and not served yet.


class CatalogProgram(BaseModel):
    id: str
    name: str
    groups: list[CatalogGroup]
    electives: list[CatalogElective]


class CatalogResponse(BaseModel):
    schema_version: int
    source: SourceInfo
    programs: list[CatalogProgram]


# --- GET /api/v1/schedule --------------------------------------------------------------------


class ProgramRef(BaseModel):
    id: str
    name: str


class CourseRef(BaseModel):
    id: str
    name: str


class ItemGroup(BaseModel):
    id: str | None
    label: str | None
    program_wide: bool


class TeacherRef(BaseModel):
    id: str
    name: str


class Block(BaseModel):
    weekday: int
    start_hour: int
    count: int


class Effective(BaseModel):
    weekday: int
    start_time: str
    end_time: str
    mode: str
    date_from: str | None
    date_to: str | None


class Remark(BaseModel):
    raw: str | None
    parse_status: str
    unparsed: str | None
    needs_review: bool


class ScheduleItem(BaseModel):
    id: str
    course: CourseRef
    type: str | None
    group: ItemGroup | None
    teachers: list[TeacherRef]
    room: str | None
    block: Block
    effective: Effective
    patched_fields: list[str]
    remark: Remark
    proposals: list[dict]


class ScheduleResponse(BaseModel):
    schema_version: int
    program: ProgramRef
    source: ScheduleSource
    items: list[ScheduleItem]
