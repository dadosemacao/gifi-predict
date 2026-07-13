from __future__ import annotations

import dataclasses
import sqlite3
from pathlib import Path

from serving.observability.schema import ApiCallRecord


class AuditRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def insert(self, record: ApiCallRecord) -> None:
        cols = [f.name for f in dataclasses.fields(ApiCallRecord)]
        placeholders = ",".join("?" * len(cols))
        sql = f"INSERT INTO api_calls ({','.join(cols)}) VALUES ({placeholders})"
        values = tuple(getattr(record, col) for col in cols)
        with self._connect() as conn:
            conn.execute(sql, values)
            conn.commit()

    def fetch_last(self, limit: int = 10) -> list[sqlite3.Row]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id, ts_utc, method, path, endpoint, status_code, duration_ms "
                "FROM api_calls ORDER BY ts_utc DESC LIMIT ?",
                (limit,),
            )
            return list(cur.fetchall())

    def fetch_errors(self, limit: int = 20) -> list[sqlite3.Row]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id, ts_utc, endpoint, status_code, error_detail "
                "FROM api_calls WHERE status_code >= 400 "
                "ORDER BY ts_utc DESC LIMIT ?",
                (limit,),
            )
            return list(cur.fetchall())

    def count_since_hours(self, hours: int = 24) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) AS n FROM api_calls "
                "WHERE ts_utc >= datetime('now', ?)",
                (f"-{hours} hours",),
            )
            row = cur.fetchone()
            return int(row["n"]) if row else 0
