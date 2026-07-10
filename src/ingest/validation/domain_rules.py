from __future__ import annotations

import pandas as pd

from ingest.config import IngestSettings
from ingest.observability.signals import Severity, SignalCollector


MIX_COLS = ["pct_A", "pct_B", "pct_C", "pct_D", "pct_MG"]
DB_RANGE = (350.0, 650.0)


def validate_mix(df: pd.DataFrame, settings: IngestSettings, signals: SignalCollector) -> None:
    if not all(c in df.columns for c in MIX_COLS):
        signals.emit(
            "INGEST_SCHEMA_FAIL",
            Severity.BLOCKING,
            f"missing mix columns: {[c for c in MIX_COLS if c not in df.columns]}",
        )
        return
    mix_sum = df[MIX_COLS].sum(axis=1)
    bad = (mix_sum - 1.0).abs() > settings.mix_tolerance
    if bad.any():
        signals.emit(
            "INGEST_MIX_FAIL",
            Severity.BLOCKING,
            f"mix sum outside tolerance ±{settings.mix_tolerance}",
            row_ref=str(int(bad.idxmax())) if hasattr(bad, "idxmax") else None,
        )


def validate_db_units(df: pd.DataFrame, signals: SignalCollector) -> None:
    for col in ("DB_SGF", "DB_LAB"):
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        if series.dropna().empty:
            continue
        if series.max() > 1000 or series.min() < 50:
            signals.emit(
                "INGEST_UNIT_FAIL",
                Severity.BLOCKING,
                f"{col} likely wrong unit (expected kg/m3)",
            )
            return
        out_of_range = series[(series < DB_RANGE[0]) | (series > DB_RANGE[1])]
        if len(out_of_range) > len(series) * 0.5:
            signals.emit(
                "INGEST_UNIT_FAIL",
                Severity.BLOCKING,
                f"{col} majority outside [{DB_RANGE[0]}, {DB_RANGE[1]}]",
            )


def validate_db_ranges(df: pd.DataFrame, signals: SignalCollector) -> None:
    for col in ("DB_SGF", "DB_LAB"):
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        invalid = series[(series < DB_RANGE[0]) | (series > DB_RANGE[1])]
        if not invalid.dropna().empty:
            signals.emit(
                "INGEST_SCHEMA_FAIL",
                Severity.BLOCKING,
                f"{col} outside schema range {DB_RANGE}",
            )


def validate_historical_frame(
    df: pd.DataFrame, settings: IngestSettings, signals: SignalCollector
) -> pd.DataFrame:
    out = df.copy()
    if all(c in out.columns for c in MIX_COLS):
        has_mix = out[MIX_COLS].notna().any(axis=1)
        missing_mix = int((~has_mix).sum())
        if missing_mix:
            signals.emit(
                "INGEST_FILTER_INFO",
                Severity.INFO,
                f"excluding {missing_mix} rows without mix data",
            )
            out = out[has_mix].copy()

    validate_mix(out, settings, signals)
    validate_db_units(out, signals)
    if not signals.has_blocking:
        validate_db_ranges(out, signals)
    return out
