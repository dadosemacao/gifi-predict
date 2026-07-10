from __future__ import annotations

import pandas as pd

from ingest.config import IngestSettings
from ingest.observability.signals import Severity, SignalCollector
from ingest.transform.aggregation import add_daily_meta_columns
from ingest.transform.imputation import impute_db_lab
from ingest.transform.mix_features import derive_mix_features, derive_vmi_flags
from ingest.validation.domain_rules import validate_historical_frame


def transform_historical(
    df: pd.DataFrame,
    settings: IngestSettings,
    signals: SignalCollector,
) -> tuple[pd.DataFrame, dict[str, int]]:
    exclusions: dict[str, int] = {}
    rows_in = len(df)
    frame = validate_historical_frame(df, settings, signals)
    mix_excluded = rows_in - len(frame)
    if mix_excluded:
        exclusions["mix_missing"] = mix_excluded
    if signals.has_blocking:
        return frame, exclusions

    out = impute_db_lab(frame, settings, signals)
    out = derive_mix_features(out)
    out = derive_vmi_flags(out)
    out = add_daily_meta_columns(out)

    if "TSA_dia" in out.columns:
        excluded = int((out["TSA_dia"] < settings.tsa_train_min).sum())
        if excluded:
            signals.emit(
                "INGEST_FILTER_INFO",
                Severity.INFO,
                f"excluding {excluded} rows with TSA_dia < {settings.tsa_train_min}",
            )
            exclusions["tsa_below_min"] = excluded
            out = out[out["TSA_dia"] >= settings.tsa_train_min].copy()

    return out, exclusions


def transform_scenario(df: pd.DataFrame, settings: IngestSettings) -> pd.DataFrame:
    out = derive_mix_features(df.copy())
    out = derive_vmi_flags(out)
    if "DB_SGF" in out.columns and "DB_LAB" not in out.columns:
        signals = SignalCollector()
        out = impute_db_lab(out, settings, signals)
    return out
