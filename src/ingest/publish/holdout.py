from __future__ import annotations

import pandas as pd

from ingest.config import IngestSettings


def split_holdout(
    df: pd.DataFrame, settings: IngestSettings
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if "data_processo" not in df.columns:
        return df.copy(), df.iloc[0:0].copy()
    dates = pd.to_datetime(df["data_processo"])
    holdout_mask = (dates >= settings.holdout_start) & (dates <= settings.holdout_end)
    holdout = df[holdout_mask].copy()
    train = df[~holdout_mask].copy()
    return train, holdout
