"""Migration tests: a blank database upgrades, and existing data survives."""

from __future__ import annotations

import os
import uuid

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command
from app.config import get_settings

MIGRATION_DB = "quantum_migration_test"


@pytest.fixture
def migration_url() -> str:
    settings = get_settings()
    base = settings.database_url.rsplit("/", 1)[0]
    admin = create_engine(f"{base}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{MIGRATION_DB}"'))
        connection.execute(text(f'CREATE DATABASE "{MIGRATION_DB}"'))
    admin.dispose()
    yield f"{base}/{MIGRATION_DB}"
    admin = create_engine(f"{base}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{MIGRATION_DB}"'))
    admin.dispose()


def alembic_config(url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    return config


def test_blank_database_upgrades_to_head(migration_url):
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = migration_url
    try:
        command.upgrade(alembic_config(migration_url), "head")
    finally:
        if previous is not None:
            os.environ["DATABASE_URL"] = previous
    engine = create_engine(migration_url)
    with engine.connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
        }
    engine.dispose()
    expected = {
        "principals",
        "guest_sessions",
        "topic_progress",
        "workspaces",
        "revisions",
        "runs",
        "task_attempts",
        "assessment_attempts",
        "evaluations",
        "skill_evidence",
        "preview_encounters",
        "conversations",
        "tutor_turns",
        "delivered_hints",
        "quota_counters",
        "alembic_version",
    }
    assert expected <= tables


def test_a_seeded_guest_and_evaluation_survive_a_migration_cycle(migration_url):
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = migration_url
    try:
        config = alembic_config(migration_url)
        command.upgrade(config, "head")

        engine = create_engine(migration_url)
        principal_id = uuid.uuid4()
        attempt_id = uuid.uuid4()
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO principals (id, kind, created_at) VALUES (:id, 'guest', now())"),
                {"id": principal_id},
            )
            connection.execute(
                text(
                    "INSERT INTO assessment_attempts "
                    "(id, principal_id, assessment_id, form, mode, status, "
                    " content_version, answers, created_at, updated_at) "
                    "VALUES (:id, :principal, 'chapter-1-assessment', 'A', 'test', "
                    "'submitted', 1, '{}'::jsonb, now(), now())"
                ),
                {"id": attempt_id, "principal": principal_id},
            )
            connection.execute(
                text(
                    "INSERT INTO evaluations "
                    "(id, principal_id, attempt_id, score, max_score, passed, detail, "
                    " rubric_version, created_at) "
                    "VALUES (:id, :principal, :attempt, 9, 10, true, "
                    "'{\"score\": 9}'::jsonb, 1, now())"
                ),
                {"id": uuid.uuid4(), "principal": principal_id, "attempt": attempt_id},
            )

        # Re-running the upgrade must not disturb the stored evidence.
        command.upgrade(config, "head")
        with engine.connect() as connection:
            row = connection.execute(
                text("SELECT score, passed FROM evaluations WHERE principal_id = :id"),
                {"id": principal_id},
            ).one()
        engine.dispose()
        assert row[0] == 9
        assert row[1] is True
    finally:
        if previous is not None:
            os.environ["DATABASE_URL"] = previous
