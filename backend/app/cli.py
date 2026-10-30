"""Command line entry point: python -m app.cli <command>."""
import argparse
import logging
import sys
from pathlib import Path

from app.db import get_sessionmaker
from app.fetcher.client import SourceClient
from app.services.ingest import IngestReport, ingest
from app.services.refresh import refresh


def _print(report: IngestReport) -> None:
    print(
        f"{report.status}: version={report.version} rows={report.rows} "
        f"active={report.slots_active} deactivated={report.slots_deactivated} needs_review={report.needs_review}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="planr")
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch", help="Update everything from the source website (main plan + electives)")
    fetch.add_argument("--force", action="store_true", help="Update even if the source reports no changes")
    local = sub.add_parser(
        "ingest-file", help="Ingest a local CSV dump (offline development; programme ids are slugs)"
    )
    local.add_argument("path", type=Path)
    local.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    with get_sessionmaker()() as session:
        if args.command == "fetch":
            with SourceClient() as source:
                result = refresh(session, source, force=args.force)
            if result.status == "unchanged":
                print("unchanged: source reports no updates since the last fetch")
            else:
                _print(result.ingest)
                e = result.electives
                print(
                    f"electives: programs={e.programs_linked} links={e.links} "
                    f"unknown_programs={len(e.unknown_programs)} unknown_courses={len(e.unknown_courses)}"
                )
        else:
            _print(ingest(session, args.path.read_bytes(), force=args.force))
    return 0


if __name__ == "__main__":
    sys.exit(main())
