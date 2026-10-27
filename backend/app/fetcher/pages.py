"""Pure parsers for the source website's HTML pages (no I/O)."""
import datetime as dt
import re
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

_MONTHS = {
    "stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4, "maja": 5, "czerwca": 6,
    "lipca": 7, "sierpnia": 8, "września": 9, "października": 10, "listopada": 11, "grudnia": 12,
}
_FOOTER = re.compile(r"Aktualizacja danych:\s*(\d{1,2})\s+(\w+)\s+(\d{4})\s+o\s+(\d{1,2})[.:](\d{2})")
_HEADER_TITLE = "Plan zajęć"


class PageFormatError(ValueError):
    """Raised when a page does not have the expected structure."""


class _PageScanner(HTMLParser):
    """Collects hyperlinks and <h1> texts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.headings: list[str] = []
        self._in_h1 = False
        self._h1_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)
        elif tag == "h1":
            self._in_h1, self._h1_parts = True, []

    def handle_data(self, data: str) -> None:
        if self._in_h1:
            self._h1_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self._in_h1:
            self._in_h1 = False
            self.headings.append(" ".join("".join(self._h1_parts).split()))


def _scan(html: str) -> _PageScanner:
    scanner = _PageScanner()
    scanner.feed(html)
    return scanner


def _query_value(href: str, key: str) -> str | None:
    values = parse_qs(urlsplit(href).query).get(key)
    return values[0] if values else None


def parse_program_ids(hub_html: str) -> list[str]:
    """Programme ids ('?grupa=<id>' links) listed on a hub page, in page order."""
    ids: list[str] = []
    for href in _scan(hub_html).hrefs:
        query = parse_qs(urlsplit(href).query)
        if set(query) == {"grupa"} and query["grupa"][0] not in ids:
            ids.append(query["grupa"][0])
    return ids


def parse_program_name(program_html: str) -> str:
    """Programme name, e.g. 'informatyka (P): III rok' (the <h1> that follows the page header)."""
    titles = [h for h in _scan(program_html).headings if h and h != _HEADER_TITLE]
    if not titles:
        raise PageFormatError("Programme page has no programme heading")
    return titles[-1]


def parse_faids(program_html: str) -> list[str]:
    """Elective set ids ('?zajecia=<faid>' links) of a programme page, in page order."""
    faids: list[str] = []
    for href in _scan(program_html).hrefs:
        faid = _query_value(href, "zajecia")
        if faid and faid not in faids:
            faids.append(faid)
    return faids


def parse_footer_timestamp(html: str, timezone: str) -> dt.datetime | None:
    """'Aktualizacja danych: 23 października 2026 o 16.18' -> timezone-aware datetime."""
    match = _FOOTER.search(html)
    if not match:
        return None
    day, month_name, year, hour, minute = match.groups()
    month = _MONTHS.get(month_name.lower())
    if month is None:
        return None
    return dt.datetime(int(year), month, int(day), int(hour), int(minute), tzinfo=ZoneInfo(timezone))
