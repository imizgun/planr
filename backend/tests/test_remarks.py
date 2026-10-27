import pytest

from app.parsing.remarks import analyze_remark


@pytest.mark.parametrize(
    ("raw", "patch", "extras", "unparsed", "status"),
    [
        ("", {}, {}, [], "ok"),
        ("14.30-16.00", {"start_time": "14:30", "end_time": "16:00"}, {}, [], "ok"),
        (" 8.00-9.30; zajęcia od 8 XII do 19 I", {"start_time": "08:00", "end_time": "09:30"},
         {"date_from_md": [8, 12], "date_to_md": [19, 1]}, [], "ok"),
        ("zajęcia zdalne", {"mode": "remote"}, {}, [], "ok"),
        ("18.30-20.00; gr. 2; zajęcia co dwa tygodnie", {"start_time": "18:30", "end_time": "20:00"},
         {"elective_group": "gr. 2", "week_interval": 2}, [], "ok"),
        ("grupy na zmianę co 3 tygodnie", {}, {"alternating_groups_weeks": 3}, [], "ok"),
        ("9 X nie będzie wykładu; zajęcia do 27 XI", {}, {"excluded_dates_md": [[9, 10]], "date_to_md": [27, 11]}, [], "ok"),
        ("8.00-9.30; zajęcia w budynku Wydziału Ekonomii", {"start_time": "08:00", "end_time": "09:30"},
         {"location_note": "Wydziału Ekonomii"}, [], "ok"),
        ("ćwiczenia lub wykład; zajęcia zdalne", {"mode": "remote"}, {}, ["ćwiczenia lub wykład"], "partial"),
        ("dokładne terminy zostaną podane później", {}, {}, ["dokładne terminy zostaną podane później"], "unparsed"),
        # invalid values must not be recognised
        ("20.00-18.00", {}, {}, ["20.00-18.00"], "unparsed"),
        ("zajęcia od 45 X", {}, {}, ["zajęcia od 45 X"], "unparsed"),
    ],
)
def test_regex_stage(raw, patch, extras, unparsed, status):
    result = analyze_remark(raw)
    assert result.patch == patch
    assert result.extras == extras
    assert result.unparsed == unparsed
    assert result.parse_status == status
    assert result.needs_review == bool(unparsed)


def test_link_remark_template():
    raw = "szczegółowy plan <a href=https://inf.ug.edu.pl/plan/NL.html>https://inf.ug.edu.pl/plan/NL.html</a>"
    result = analyze_remark(raw)
    assert result.unparsed == []
    assert result.extras == {"link": {"label": "szczegółowy plan", "url": "https://inf.ug.edu.pl/plan/NL.html"}}
    other = analyze_remark("dni wykładów na stronie <a href=https://lmielewczyk.pl/others/dateOS.php>x</a>")
    assert other.extras["link"]["url"] == "https://lmielewczyk.pl/others/dateOS.php"


def test_conflicting_segments_are_not_merged():
    result = analyze_remark("8.00-9.30; 10.00-11.30")
    assert result.patch == {"start_time": "08:00", "end_time": "09:30"}
    assert result.unparsed == ["10.00-11.30"]


def test_earlier_stage_has_precedence_and_later_stage_sees_leftovers():
    class Stub:
        name = "stub"

        def __init__(self):
            self.seen = None

        def analyze(self, segments):
            from app.parsing.remarks.types import AnalysisPart

            self.seen = list(segments)
            return AnalysisPart(patch={"mode": "stationary", "start_time": "07:00"}), []

    stub = Stub()
    from app.parsing.remarks.regex_rules import RegexAnalyzer

    result = analyze_remark("zajęcia zdalne; coś nieznanego", analyzers=[RegexAnalyzer(), stub])
    assert stub.seen == ["coś nieznanego"]
    assert result.patch["mode"] == "remote"  # regex stage wins
    assert result.patch["start_time"] == "07:00"
    assert result.unparsed == []
    assert result.stages == ["regex", "stub"]
