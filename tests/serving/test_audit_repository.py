from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from serving.observability.migrate import run_migrations
from serving.observability.repository import AuditRepository
from serving.observability.schema import ApiCallRecord


@pytest.fixture
def audit_repo(tmp_path: Path) -> AuditRepository:
    db_path = tmp_path / "audit.db"
    repo = AuditRepository(db_path)
    run_migrations(Path(__file__).resolve().parents[2], db_path)
    return repo


def _fetch_last(db_path: Path) -> dict | None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM api_calls ORDER BY ts_utc DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def test_insert_and_select(audit_repo: AuditRepository) -> None:
    record = ApiCallRecord(
        method="POST",
        path="/api/forecast",
        endpoint="forecast",
        status_code=200,
        duration_ms=12.5,
        product="forecast_operacional",
        request_json='{"tsa_history":[1,2,3,4,5,6,7]}',
    )
    audit_repo.insert(record)
    rows = audit_repo.fetch_last(1)
    assert len(rows) == 1
    assert rows[0]["endpoint"] == "forecast"
    assert rows[0]["status_code"] == 200


def test_fetch_errors(audit_repo: AuditRepository) -> None:
    audit_repo.insert(
        ApiCallRecord(
            method="POST",
            path="/api/forecast",
            endpoint="forecast",
            status_code=422,
            duration_ms=1.0,
            error_detail='["missing field"]',
        )
    )
    audit_repo.insert(
        ApiCallRecord(
            method="GET",
            path="/api/forecast/status",
            endpoint="forecast_status",
            status_code=200,
            duration_ms=1.0,
        )
    )
    errors = audit_repo.fetch_errors(10)
    assert len(errors) == 1
    assert errors[0]["status_code"] == 422


def test_migrations_idempotent(repo_root: Path, tmp_path: Path) -> None:
    db_path = tmp_path / "migrate.db"
    run_migrations(repo_root, db_path)
    run_migrations(repo_root, db_path)
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    conn.close()
    assert count == 1


def test_count_since_hours(audit_repo: AuditRepository) -> None:
    audit_repo.insert(
        ApiCallRecord(
            method="GET",
            path="/api/release-status",
            endpoint="release_status",
            status_code=200,
            duration_ms=2.0,
        )
    )
    assert audit_repo.count_since_hours(24) >= 1
