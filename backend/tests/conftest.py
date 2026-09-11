"""Test fixtures. Integration tests run against a real PostgreSQL database."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://quantum:quantum_local_only@127.0.0.1:5432/quantum_test",
)
os.environ.setdefault("SESSION_SECRET", "test-only-secret-0000000000000000")
os.environ.setdefault("PUBLIC_ORIGIN", "http://127.0.0.1:5173")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("TUTOR_PROVIDER", "authored")

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings
from app.identity import sessions as identity_sessions
from app.main import create_app
from app.storage.database import get_engine, get_session_factory
from app.storage.models import Base


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Iterator[None]:
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    yield
    engine = get_engine()
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.exec_driver_sql(f'TRUNCATE TABLE "{table.name}" CASCADE')


@pytest.fixture
def db() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(), base_url="http://127.0.0.1:5173") as test_client:
        yield test_client


class GuestClient:
    """A TestClient carrying one guest's cookies and CSRF token."""

    def __init__(self, client: TestClient) -> None:
        self.client = client
        response = client.post("/api/v1/guest-session", headers={"origin": "http://127.0.0.1:5173"})
        response.raise_for_status()
        payload = response.json()
        self.principal_id = payload["principal_id"]
        self.csrf = payload["csrf_token"]

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "origin": "http://127.0.0.1:5173",
            identity_sessions.CSRF_HEADER_NAME: self.csrf,
        }
        headers.update(extra or {})
        return headers

    def get(self, url: str, **kwargs):
        return self.client.get(url, headers=self._headers(), **kwargs)

    def post(self, url: str, **kwargs):
        return self.client.post(url, headers=self._headers(), **kwargs)

    def patch(self, url: str, **kwargs):
        return self.client.patch(url, headers=self._headers(), **kwargs)


@pytest.fixture
def guest() -> Iterator[GuestClient]:
    with TestClient(create_app(), base_url="http://127.0.0.1:5173") as test_client:
        yield GuestClient(test_client)


@pytest.fixture
def second_guest() -> Iterator[GuestClient]:
    with TestClient(create_app(), base_url="http://127.0.0.1:5173") as test_client:
        yield GuestClient(test_client)


@pytest.fixture
def settings():
    return get_settings()
