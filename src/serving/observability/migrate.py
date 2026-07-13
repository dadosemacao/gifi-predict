from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from serving.observability.repository import AuditRepository

MIGRATION_VERSION = "001_init"


def run_migrations(repo_root: Path, db_path: Path) -> None:
    repo = AuditRepository(db_path)
    sql_path = repo_root / "database" / "serving_audit" / "001_init.sql"
    if not sql_path.exists():
        raise FileNotFoundError(f"migration não encontrada: {sql_path}")

    script = sql_path.read_text(encoding="utf-8")
    with repo._connect() as conn:
        conn.executescript(script)
        cur = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE version = ?",
            (MIGRATION_VERSION,),
        )
        if cur.fetchone() is None:
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (MIGRATION_VERSION, datetime.now(UTC).isoformat()),
            )
        conn.commit()
