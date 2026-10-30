"""Full data update: change detection, step 1 (main plan) and step 2 (elective assignment)."""
import datetime as dt
import logging
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fetcher.electives import HubInfo, crawl_electives, fetch_hubs
from app.models import SourceStamp
from app.services.electives import LinkReport, link_electives
from app.services.ingest import IngestReport, ingest

log = logging.getLogger(__name__)


class Source(Protocol):
    def get_text(self, url: str) -> str: ...
    def fetch_main_plan(self) -> bytes: ...


@dataclass
class RefreshReport:
    status: str  # unchanged | refreshed
    ingest: IngestReport | None = None
    electives: LinkReport | None = None


def _unchanged(session: Session, hubs: list[HubInfo]) -> bool:
    stored = {s.key: s.source_updated_at for s in session.scalars(select(SourceStamp))}
    return all(hub.updated_at is not None and stored.get(hub.url) == hub.updated_at for hub in hubs)


def _save_stamps(session: Session, hubs: list[HubInfo], now: dt.datetime) -> None:
    for hub in hubs:
        stamp = session.get(SourceStamp, hub.url) or SourceStamp(key=hub.url)
        stamp.source_updated_at = hub.updated_at
        stamp.checked_at = now
        session.add(stamp)
    session.commit()


def refresh(session: Session, source: Source, *, force: bool = False) -> RefreshReport:
    """Update everything from the source.

    1. Hub pages are fetched; if all footer timestamps match the stored ones nothing else is requested.
    2. The programme crawl runs first (it yields the site programme ids used by the ingestion) and
       aborts the whole update on any failure, so ids never change because of a partial crawl.
    3. The main plan is ingested and the elective assignment is stored.
    Timestamps are saved only after everything succeeded.
    """
    now = dt.datetime.now(dt.timezone.utc)
    hubs = fetch_hubs(source)
    if not force and _unchanged(session, hubs):
        return RefreshReport(status="unchanged")

    crawl = crawl_electives(source, hubs)
    report = ingest(session, source.fetch_main_plan(), fetched_at=now, force=force, program_ids=crawl.program_ids_by_name)
    links = link_electives(session, crawl)
    _save_stamps(session, hubs, now)
    return RefreshReport(status="refreshed", ingest=report, electives=links)
