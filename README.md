# Planr (working name)

Alternative frontend for the MFI faculty schedule. This repository currently contains the **minimal backend**: source fetcher / parser, database and REST API. The `frontend/` directory is intentionally empty.

## Structure

- `backend/` – Python / FastAPI / PostgreSQL (SQLAlchemy 2, Alembic)
- `frontend/` – Angular

### Backend layout

- `app/fetcher/` – HTTP access (`SourceClient`), HTML page parsers (`pages.py`), programme / elective crawl (`electives.py`)
- `app/parsing/` – CSV reader, `grupa` column parser, hierarchical remark analysis (`remarks/`)
- `app/services/` – refresh orchestration, ingestion (snapshots, upsert), elective linking, effective-value computation, catalog and schedule queries
- `app/api/v1/` – REST endpoints
- `alembic/` – database migrations
- `tests/` – pytest suite (uses a real PostgreSQL database; fixture: `tests/fixtures/main_plan.csv`)

## Running

Prerequisites: Python 3.11+, PostgreSQL 14+ [FONTEND DEPS TBA].

### Native start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # adjust PLANR_DATABASE_URL

alembic upgrade head            # create db schema
python -m app.cli fetch         # download schedule and ingest it (first run / update)
uvicorn app.main:app --reload   # API on http://localhost:8000

cd ../frontend
ng serve
```

### Docker start

```bash
docker compose up -d
docker compose --profile tools up -d # download schedule and ingest it (first run / update)
```

TODO:

- Current time marker
- Facultatives support
- Timeline
- Mobile view
