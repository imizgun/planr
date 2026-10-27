"""Step 2 of the data update: assigning elective courses to programmes.

URL chain: hub page ('?grupa=<id>' links) -> programme page (name + '?zajecia=<faid>' links)
-> '?zajecia=<faid>&format=csv' (elective courses of that set).
"""
import datetime as dt
import logging
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urljoin

from app.config import get_settings
from app.fetcher.pages import (
    PageFormatError,
    parse_faids,
    parse_footer_timestamp,
    parse_program_ids,
    parse_program_name,
)
from app.parsing.csv_reader import ELECTIVES_COLUMNS, read_rows

log = logging.getLogger(__name__)


class TextSource(Protocol):
    def get_text(self, url: str) -> str: ...


@dataclass
class CrawledProgram:
    site_id: str  # e.g. '3P'
    name: str  # e.g. 'informatyka (P): III rok'
    url: str
    faids: list[str] = field(default_factory=list)
    courses: list[str] = field(default_factory=list)  # distinct elective course names


@dataclass
class HubInfo:
    url: str
    html: str
    updated_at: dt.datetime | None


@dataclass
class ElectiveCrawl:
    programs: list[CrawledProgram]

    @property
    def program_ids_by_name(self) -> dict[str, str]:
        return {program.name: program.site_id for program in self.programs}


def fetch_hubs(source: TextSource, urls: list[str] | None = None) -> list[HubInfo]:
    """Download the hub pages; their footers carry the update timestamps used for change detection."""
    settings = get_settings()
    hubs = []
    for url in urls or settings.source_hub_urls:
        html = source.get_text(url)
        hubs.append(HubInfo(url=url, html=html, updated_at=parse_footer_timestamp(html, settings.timezone)))
    return hubs


def crawl_electives(source: TextSource, hubs: list[HubInfo]) -> ElectiveCrawl:
    """Walk the chain for every programme listed on the hubs. Any failure aborts the whole crawl."""
    programs: list[CrawledProgram] = []
    for hub in hubs:
        for site_id in parse_program_ids(hub.html):
            url = urljoin(hub.url, f"?grupa={site_id}")
            html = source.get_text(url)
            program = CrawledProgram(site_id=site_id, name=parse_program_name(html), url=url)
            program.faids = parse_faids(html)
            names: dict[str, None] = {}
            for faid in program.faids:
                csv_text = source.get_text(urljoin(url, f"?zajecia={faid}&format=csv"))
                for row in read_rows(csv_text, columns=ELECTIVES_COLUMNS):
                    names.setdefault(row.course)
            program.courses = list(names)
            programs.append(program)

    ids = [program.site_id for program in programs]
    if len(ids) != len(set(ids)):
        raise PageFormatError(f"Duplicate programme ids across hubs: {sorted(i for i in set(ids) if ids.count(i) > 1)}")
    names_seen = [program.name for program in programs]
    if len(names_seen) != len(set(names_seen)):
        raise PageFormatError("Two programme ids share the same name")
    log.info("Crawled %d programmes", len(programs))
    return ElectiveCrawl(programs=programs)
