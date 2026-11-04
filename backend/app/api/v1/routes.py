import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import CatalogResponse, ScheduleResponse
from app.services.catalog import build_catalog
from app.services.common import NoDataError
from app.services.schedule import InvalidQueryError, UnknownProgramError, build_schedule

router = APIRouter(prefix="/api/v1")


@router.get("/catalog", response_model=CatalogResponse)
def get_catalog(session: Session = Depends(get_session)) -> CatalogResponse:
    """List of programs, groups and electives used to build the schedule selection form."""
    try:
        return build_catalog(session)
    except NoDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/schedule", response_model=ScheduleResponse)
def get_schedule(
    program: str = Query(..., description="Program id"),
    group: list[str] = Query(default=[], description="Program group id (repeatable)"),
    elective: list[str] = Query(default=[], description="<courseId>:<groupId> (repeatable)"),
    date_from: dt.date | None = Query(default=None, alias="from"),
    date_to: dt.date | None = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
) -> ScheduleResponse:
    try:
        return build_schedule(
            session,
            program_id=program,
            group_ids=group,
            electives=elective,
            date_from=date_from,
            date_to=date_to,
        )
    except NoDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UnknownProgramError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown program: {exc}") from exc
    except InvalidQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
