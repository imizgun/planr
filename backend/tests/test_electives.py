import datetime as dt
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from sqlalchemy import func, select

from app.fetcher.electives import crawl_electives, fetch_hubs
from app.fetcher.pages import (
    PageFormatError,
    parse_faids,
    parse_footer_timestamp,
    parse_program_ids,
    parse_program_name,
)
from app.models import Program, ProgramElective, SourceStamp
from app.services.ingest import ingest
from app.services.refresh import refresh

SITE = Path(__file__).parent / "fixtures" / "site"
ROOT_HUB = "https://inf.ug.edu.pl/plan/?dialog=grupa"
FIZ_HUB = "https://inf.ug.edu.pl/plan/fiz/"
CSV_HEADER = "przedmiot,nauczyciel,dzien,godz,czas,sala,typ,uwagi,dataod,datado\n"


def _read(name: str) -> str:
    return (SITE / name).read_text(encoding="utf-8")


def test_page_parsers_on_real_pages():
    root, fiz, program = _read("dialog.html"), _read("fiz.html"), _read("grupa_3P.html")
    assert parse_program_ids(root)[:3] == ["1I", "2I", "3I"] and len(parse_program_ids(root)) == 18
    assert parse_program_ids(fiz)[-2:] == ["4Q", "5Q"]
    assert parse_program_ids(program) == []  # format links carry two parameters and are not programmes
    assert parse_program_name(program) == "informatyka (P): III rok"
    assert parse_faids(program) == ["Fa3p"]
    assert parse_footer_timestamp(root, "Europe/Warsaw") == dt.datetime(
        2026, 10, 23, 16, 18, tzinfo=dt.timezone(dt.timedelta(hours=2))
    )
    assert parse_footer_timestamp(fiz, "Europe/Warsaw").day == 22  # subsites have their own timestamp
    assert parse_footer_timestamp("no footer", "Europe/Warsaw") is None


def test_program_name_requires_a_heading():
    with pytest.raises(PageFormatError):
        parse_program_name("<html><h1>Plan zajęć</h1></html>")


class FakeSite:
    """Serves the real hub pages and the real '3P' page; everything else is synthesised."""

    def __init__(self, main_csv: bytes, *, fiz_stamp: str | None = None):
        self.main_csv = main_csv
        self.requests: list[str] = []
        self.fiz_html = _read("fiz.html")
        if fiz_stamp:
            self.fiz_html = self.fiz_html.replace("22 października 2026 o 10.26", fiz_stamp)
        self.elective_csv = CSV_HEADER + (
            'Programowanie funkcyjne,dr Jan Kowalski,Poniedziałek,10,2,1.15,wykład,,2026-10-05,2027-01-25\n'
            'Kurs spoza planu,dr Anna Nowak,Poniedziałek,10,2,1.15,wykład,,2026-10-05,2027-01-25\n'
        )

    def get_text(self, url: str) -> str:
        self.requests.append(url)
        parts = urlsplit(url)
        path, query = parts.path, parts.query
        if url == ROOT_HUB:
            return _read("dialog.html")
        if url == FIZ_HUB:
            return self.fiz_html
        if query == "grupa=3P":
            return _read("grupa_3P.html")
        if query.startswith("grupa="):
            site_id = query.split("=")[1]
            names = {"2P": "informatyka (P): II rok", "1F": "fizyka: I rok"}
            return f"<html><h1>Plan zajęć</h1><h1>{names.get(site_id, 'program ' + site_id)}</h1></html>"
        if query == "zajecia=Fa3p&format=csv":
            assert path == "/plan/"
            return self.elective_csv
        raise AssertionError(f"unexpected request {url}")

    def fetch_main_plan(self) -> bytes:
        self.requests.append("MAIN")
        return self.main_csv


def test_crawl_collects_programs_faids_and_courses(csv_bytes):
    site = FakeSite(csv_bytes)
    crawl = crawl_electives(site, fetch_hubs(site))
    assert len(crawl.programs) == 36
    third = next(p for p in crawl.programs if p.site_id == "3P")
    assert (third.name, third.faids, third.courses) == (
        "informatyka (P): III rok", ["Fa3p"], ["Programowanie funkcyjne", "Kurs spoza planu"],
    )
    fiz = next(p for p in crawl.programs if p.site_id == "1F")
    assert fiz.url == "https://inf.ug.edu.pl/plan/fiz/?grupa=1F"  # relative links resolve against the hub


def test_crawl_failure_aborts_before_any_ingest(session, csv_bytes):
    site = FakeSite(csv_bytes)
    site.get_text_orig = site.get_text
    site.get_text = lambda url: (_ for _ in ()).throw(RuntimeError("boom")) if "grupa=2P" in url else site.get_text_orig(url)
    with pytest.raises(RuntimeError):
        refresh(session, site)
    assert "MAIN" not in site.requests
    assert session.scalar(select(func.count()).select_from(Program)) == 0
    assert session.scalar(select(func.count()).select_from(SourceStamp)) == 0


def test_refresh_uses_site_ids_and_links_electives(session, client, csv_bytes):
    report = refresh(session, FakeSite(csv_bytes))
    assert report.status == "refreshed"
    assert report.electives.unknown_courses == ["Kurs spoza planu"]
    assert "informatyka (P): III rok" not in report.electives.unknown_programs

    program = session.scalar(select(Program).where(Program.name == "informatyka (P): III rok"))
    assert program.id == "3P"
    assert session.scalar(select(func.count()).select_from(ProgramElective)) == 1

    catalog = client.get("/api/v1/catalog").json()
    entry = next(p for p in catalog["programs"] if p["id"] == "3P")
    assert [e["name"] for e in entry["electives"]] == ["Programowanie funkcyjne"]
    assert [g["label"] for g in entry["electives"][0]["groups"]] == ["gr. 1", "gr. 2"]
    assert client.get("/api/v1/schedule", params={"program": "3P"}).status_code == 200
    # programmes outside the site's hubs keep generated ids
    assert any(p["id"] == "biotech" for p in catalog["programs"])


def test_unchanged_footer_stops_after_the_hub_requests(session, csv_bytes):
    refresh(session, FakeSite(csv_bytes))
    site = FakeSite(csv_bytes)
    report = refresh(session, site)
    assert report.status == "unchanged"
    assert site.requests == [ROOT_HUB, FIZ_HUB]


def test_changed_footer_of_one_hub_triggers_update(session, csv_bytes):
    refresh(session, FakeSite(csv_bytes))
    site = FakeSite(csv_bytes, fiz_stamp="24 października 2026 o 08.00")
    report = refresh(session, site)
    assert report.status == "refreshed" and report.ingest.status == "unchanged"  # same dump content
    assert "MAIN" in site.requests


def test_force_refreshes_despite_unchanged_footer(session, csv_bytes):
    refresh(session, FakeSite(csv_bytes))
    assert refresh(session, FakeSite(csv_bytes), force=True).status == "refreshed"


def test_existing_program_keeps_its_id_and_warns_once(session, loaded, csv_bytes, caplog):
    # data ingested offline (slug ids) is not re-keyed by a later refresh
    with caplog.at_level("WARNING", logger="app.services.ingest"):
        refresh(session, FakeSite(csv_bytes), force=True)
    program = session.scalar(select(Program).where(Program.name == "informatyka (P): III rok"))
    assert program.id == "informatyka-p-3"
    mismatches = [r.getMessage() for r in caplog.records if "keeps id" in r.getMessage()]
    assert len([m for m in mismatches if "informatyka (P): III rok" in m]) == 1  # not once per CSV row
    assert len(mismatches) == len(set(mismatches))


def test_offline_ingest_over_site_ids_is_silent(session, csv_bytes, caplog):
    refresh(session, FakeSite(csv_bytes))  # programmes now carry site ids
    with caplog.at_level("WARNING", logger="app.services.ingest"):
        report = ingest(session, csv_bytes, force=True)  # no site mapping supplied
    assert report.status == "ingested"
    assert not [r for r in caplog.records if "keeps id" in r.getMessage()]
    assert session.scalar(select(Program.id).where(Program.name == "informatyka (P): III rok")) == "3P"


def test_elective_and_main_exports_are_not_interchangeable(csv_bytes):
    from app.parsing.csv_reader import ELECTIVES_COLUMNS, SourceFormatError, read_rows

    elective_csv = FakeSite(csv_bytes).elective_csv
    rows = read_rows(elective_csv, columns=ELECTIVES_COLUMNS)
    assert [r.course for r in rows] == ["Programowanie funkcyjne", "Kurs spoza planu"]
    assert rows[0].group == "" and rows[0].teacher == "dr Jan Kowalski" and rows[0].start_hour == 10
    with pytest.raises(SourceFormatError):
        read_rows(elective_csv)  # main-plan reader rejects the elective header
    with pytest.raises(SourceFormatError):
        read_rows(csv_bytes.decode(), columns=ELECTIVES_COLUMNS)  # and vice versa
