from __future__ import annotations

import pandas as pd

from ingest.config import IngestSettings
from ingest.observability.signals import Severity, SignalCollector


def impute_db_lab(
    df: pd.DataFrame, settings: IngestSettings, signals: SignalCollector
) -> pd.DataFrame:
    out = df.copy()
    if "DB_SGF" not in out.columns:
        return out
    if "DB_LAB" not in out.columns:
        out["DB_LAB"] = pd.NA
    if "db_origin" not in out.columns:
        out["db_origin"] = pd.NA

    proxy_mask = out["DB_LAB"].isna() & out["DB_SGF"].notna()
    if proxy_mask.any():
        out.loc[proxy_mask, "DB_LAB"] = out.loc[proxy_mask, "DB_SGF"] * settings.db_proxy_factor
        out.loc[proxy_mask, "db_origin"] = "proxy"
        signals.emit(
            "INGEST_PROXY_DB",
            Severity.WARNING,
            f"DB_LAB imputed for {int(proxy_mask.sum())} rows",
        )

    lab_mask = out["DB_LAB"].notna() & out["db_origin"].isna()
    out.loc[lab_mask, "db_origin"] = "lab"
    return out
