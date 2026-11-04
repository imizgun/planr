import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Snapshot


class NoDataError(Exception):
    """No plan has been ingested yet."""


def current_snapshot(session: Session) -> Snapshot:
    snapshot = session.scalar(select(Snapshot).where(Snapshot.is_current))
    if snapshot is None:
        raise NoDataError("No plan data has been ingested yet")
    return snapshot


def iso_utc(value: dt.datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
