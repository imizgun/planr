"""Reader for the main plan CSV dump (source columns are Polish; internal names are English)."""
import csv
import datetime as dt
import io
from dataclasses import dataclass

# Column sets of the source's CSV exports (matched by name, order does not matter).
MAIN_PLAN_COLUMNS = frozenset(
    {"dzien", "godz", "czas", "przedmiot", "grupa", "nauczyciel", "sala", "typ", "uwagi", "dataod", "datado"}
)
ELECTIVES_COLUMNS = MAIN_PLAN_COLUMNS - {"grupa"}  # '?zajecia=<faid>&format=csv' has no group column

_ZERO_DATE = "0000-00-00"


class SourceFormatError(ValueError):
    """Raised when the downloaded content is not the expected CSV dump."""


@dataclass(frozen=True)
class RawRow:
    line_no: int
    day: str
    start_hour: int
    hour_count: int
    course: str
    group: str  # raw 'grupa' column, may hold several '/'- or '+'-separated entries
    teacher: str
    room: str
    type: str
    remark: str  # raw 'uwagi' column, kept unstripped
    date_from: dt.date | None
    date_to: dt.date | None


def _parse_date(value: str, line_no: int) -> dt.date | None:
    value = value.strip()
    if not value or value == _ZERO_DATE:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise SourceFormatError(f"Line {line_no}: invalid date {value!r}") from exc


def read_rows(text: str, *, columns: frozenset[str] = MAIN_PLAN_COLUMNS) -> list[RawRow]:
    """Read a CSV export. 'columns' is the exact set of columns the export must have."""
    reader = csv.DictReader(io.StringIO(text))
    if set(reader.fieldnames or ()) != columns or len(reader.fieldnames or ()) != len(columns):
        raise SourceFormatError(f"Unexpected CSV header: {reader.fieldnames!r}")

    rows: list[RawRow] = []
    for record in reader:
        line_no = reader.line_num
        try:
            start_hour = int(record["godz"])
            hour_count = int(record["czas"])
        except (TypeError, ValueError) as exc:
            raise SourceFormatError(f"Line {line_no}: non-integer godz/czas") from exc
        rows.append(
            RawRow(
                line_no=line_no,
                day=record["dzien"].strip(),
                start_hour=start_hour,
                hour_count=hour_count,
                course=record["przedmiot"].strip(),
                group=record.get("grupa", "").strip(),
                teacher=record["nauczyciel"].strip(),
                room=record["sala"].strip(),
                type=record["typ"].strip(),
                remark=record["uwagi"],
                date_from=_parse_date(record["dataod"], line_no),
                date_to=_parse_date(record["datado"], line_no),
            )
        )
    return rows
