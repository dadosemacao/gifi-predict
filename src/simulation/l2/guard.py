from __future__ import annotations

import pandas as pd

from ingest.contracts.models import SchemaVersionError
from ingest.publish.parquet_writer import parse_major
from simulation.exceptions import HoldoutIneligibleError


def guard_schema(manifest: dict, expected_schema_version: str) -> None:
    actual = manifest.get("schema_version", "")
    if parse_major(actual) != parse_major(expected_schema_version):
        raise SchemaVersionError(
            f"schema major mismatch: L2={actual} expected={expected_schema_version}"
        )


def guard_holdout_eligible(manifest: dict) -> None:
    if not manifest.get("holdout_eligible", True):
        raise HoldoutIneligibleError(
            "holdout_eligible=false in L2 manifest; training blocked (Matriz A invalid)"
        )


def validate_holdout_window(
    holdout: pd.DataFrame,
    *,
    start: str,
    end: str,
    date_col: str = "data_processo",
) -> None:
    if date_col not in holdout.columns:
        return
    dates = pd.to_datetime(holdout[date_col], errors="coerce")
    if dates.isna().all():
        return
    min_date = dates.min()
    max_date = dates.max()
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if min_date < start_ts or max_date > end_ts:
        raise ValueError(
            f"holdout dates [{min_date.date()}, {max_date.date()}] "
            f"outside expected window [{start}, {end}]"
        )
