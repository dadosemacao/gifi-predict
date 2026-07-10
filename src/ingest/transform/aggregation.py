from __future__ import annotations

import pandas as pd


def add_daily_meta_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Attach per-day TSA meta without changing grain (turno PK preserved)."""
    out = df.copy()
    if "data_processo" not in out.columns or "TSA_dia" not in out.columns:
        return out
    daily_tsa = out.groupby("data_processo", as_index=False)["TSA_dia"].sum()
    daily_tsa = daily_tsa.rename(columns={"TSA_dia": "tsa_meta_dia"})
    return out.merge(daily_tsa, on="data_processo", how="left")
