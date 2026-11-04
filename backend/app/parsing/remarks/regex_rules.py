"""Stage 1 of the remark analysis: static regular expressions for known templates.

To support a new template add a Rule to RULES. Rules are matched against whole segments
(the remark split on ';'), case-insensitively.
"""
import re
from collections.abc import Callable
from dataclasses import dataclass

from app.parsing.remarks.types import AnalysisPart

_MONTHS = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
    "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12,
}
_MONTH_RE = "(?:" + "|".join(sorted(_MONTHS, key=len, reverse=True)) + ")"


def _md(day: str, month: str) -> list[int] | None:
    """(day, roman month) -> [day, month]; None when out of range."""
    d, m = int(day), _MONTHS[month.upper()]
    return [d, m] if 1 <= d <= 31 else None


Handler = Callable[[re.Match[str]], AnalysisPart | None]


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    handler: Handler


def _time_range(m: re.Match[str]) -> AnalysisPart | None:
    h1, m1, h2, m2 = (int(m[k]) for k in ("h1", "m1", "h2", "m2"))
    if not (0 <= h1 < 24 and 0 <= h2 < 24 and m1 < 60 and m2 < 60):
        return None
    if (h2, m2) <= (h1, m1):
        return None
    return AnalysisPart(patch={"start_time": f"{h1:02d}:{m1:02d}", "end_time": f"{h2:02d}:{m2:02d}"})


def _date_range(m: re.Match[str]) -> AnalysisPart | None:
    start = _md(m["d1"], m["m1"])
    end = _md(m["d2"], m["m2"]) if m["d2"] else None
    if start is None or (m["d2"] and end is None):
        return None
    extras: dict = {"date_from_md": start}
    if end:
        extras["date_to_md"] = end
    return AnalysisPart(extras=extras)


def _date_to(m: re.Match[str]) -> AnalysisPart | None:
    end = _md(m["d"], m["m"])
    return AnalysisPart(extras={"date_to_md": end}) if end else None


def _excluded_date(m: re.Match[str]) -> AnalysisPart | None:
    day = _md(m["d"], m["m"])
    return AnalysisPart(extras={"excluded_dates_md": [day]}) if day else None


RULES: tuple[Rule, ...] = (
    Rule(
        "time_range",
        re.compile(r"(?P<h1>\d{1,2})[.:](?P<m1>\d{2})\s*-\s*(?P<h2>\d{1,2})[.:](?P<m2>\d{2})", re.I),
        _time_range,
    ),
    Rule("remote", re.compile(r"zajęcia zdalne", re.I), lambda m: AnalysisPart(patch={"mode": "remote"})),
    Rule(
        "elective_group",
        re.compile(r"gr\.\s*(?P<n>\d+)", re.I),
        lambda m: AnalysisPart(extras={"elective_group": f"gr. {int(m['n'])}"}),
    ),
    Rule(
        "biweekly",
        re.compile(r"zajęcia co dwa tygodnie", re.I),
        lambda m: AnalysisPart(extras={"week_interval": 2}),
    ),
    Rule(
        "alternating_groups",
        re.compile(r"grupy na zmianę co (?P<n>\d+) tygodnie", re.I),
        lambda m: AnalysisPart(extras={"alternating_groups_weeks": int(m["n"])}),
    ),
    Rule(
        "date_range",
        re.compile(
            rf"zajęcia od (?P<d1>\d{{1,2}}) (?P<m1>{_MONTH_RE})(?: do (?P<d2>\d{{1,2}}) (?P<m2>{_MONTH_RE}))?",
            re.I,
        ),
        _date_range,
    ),
    Rule(
        "date_to",
        re.compile(rf"zajęcia do (?P<d>\d{{1,2}}) (?P<m>{_MONTH_RE})", re.I),
        _date_to,
    ),
    Rule(
        "excluded_date",
        re.compile(rf"(?P<d>\d{{1,2}}) (?P<m>{_MONTH_RE}) nie będzie \w+", re.I),
        _excluded_date,
    ),
    Rule(
        "link",
        re.compile(
            r"(?P<label>szczegółowy plan|dni wykładów na stronie) <a href=['\"]?(?P<url>[^\s>'\"]+)['\"]?>.*?</a>",
            re.I,
        ),
        lambda m: AnalysisPart(extras={"link": {"label": m["label"], "url": m["url"]}}),
    ),
    Rule(
        "building",
        re.compile(r"zajęcia w budynku (?P<building>.+)", re.I),
        lambda m: AnalysisPart(extras={"location_note": m["building"].strip()}),
    ),
)


class RegexAnalyzer:
    name = "regex"

    def __init__(self, rules: tuple[Rule, ...] = RULES) -> None:
        self._rules = rules

    def _match(self, segment: str) -> AnalysisPart | None:
        for rule in self._rules:
            match = rule.pattern.fullmatch(segment)
            if match:
                part = rule.handler(match)
                if part is not None:
                    return part
        return None

    def analyze(self, segments: list[str]) -> tuple[AnalysisPart, list[str]]:
        result = AnalysisPart()
        leftover: list[str] = []
        for segment in segments:
            part = self._match(segment)
            # A segment contradicting an already recognised one is left for later stages / review.
            if part is None or result.conflicts_with(part):
                leftover.append(segment)
                continue
            result.merge(part)
        return result, leftover
