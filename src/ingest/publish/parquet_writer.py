from __future__ import annotations

from pathlib import Path

import pandas as pd

from ingest.contracts.models import SchemaVersionError


def parse_major(schema_version: str) -> int:
    return int(schema_version.split(".", 1)[0])


def assert_schema_compatible(expected: str, actual: str) -> None:
    if parse_major(expected) != parse_major(actual):
        raise SchemaVersionError(
            f"schema major mismatch: expected {expected}, got {actual}"
        )


def write_parquet(df: pd.DataFrame, path: Path, schema_version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out.attrs["schema_version"] = schema_version
    out.to_parquet(path, index=False, engine="pyarrow")
