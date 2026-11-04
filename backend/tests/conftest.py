import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.db import get_session
from app.main import app
from app.models import Base
from app.services.ingest import ingest

TEST_DATABASE_URL = os.environ.get(
    "PLANR_TEST_DATABASE_URL", "postgresql+psycopg://planr:planr@localhost:5432/planr_test"
)
FIXTURE = Path(__file__).parent / "fixtures" / "main_plan.csv"


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine) -> Iterator[Session]:
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
def csv_bytes() -> bytes:
    return FIXTURE.read_bytes()


@pytest.fixture
def loaded(session, csv_bytes):
    """Database with the fixture dump ingested."""
    return ingest(session, csv_bytes)


@pytest.fixture
def client(engine, session) -> Iterator[TestClient]:
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override() -> Iterator[Session]:
        with factory() as request_session:
            yield request_session

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
