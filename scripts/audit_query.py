#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from serving.config import _find_repo_root
from serving.observability.repository import AuditRepository


def _default_db_path() -> Path:
    root = _find_repo_root()
    return root / "logs" / "serving_audit.db"


def _print_rows(rows: list) -> None:
    for row in rows:
        print(json.dumps(dict(row), ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consultas operacionais ao SQLite de auditoria")
    parser.add_argument(
        "--db",
        type=Path,
        default=_default_db_path(),
        help="Caminho do arquivo SQLite (default: logs/serving_audit.db)",
    )
    parser.add_argument("--last", type=int, default=10, help="Últimas N chamadas")
    parser.add_argument(
        "--errors",
        action="store_true",
        help="Listar apenas respostas 4xx/5xx",
    )
    parser.add_argument(
        "--count-24h",
        action="store_true",
        help="Contagem de chamadas nas últimas 24 horas",
    )
    args = parser.parse_args(argv)

    if not args.db.exists():
        print(f"Arquivo não encontrado: {args.db}", file=sys.stderr)
        return 1

    repo = AuditRepository(args.db)
    if args.count_24h:
        print(repo.count_since_hours(24))
        return 0
    if args.errors:
        _print_rows(repo.fetch_errors(args.last))
        return 0
    _print_rows(repo.fetch_last(args.last))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
