from __future__ import annotations

import pandas as pd


def merge_train_holdout(
    train: pd.DataFrame,
    holdout: pd.DataFrame,
    *,
    date_col: str = "data_processo",
) -> pd.DataFrame:
    combined = pd.concat([train, holdout], ignore_index=True)
    if date_col in combined.columns:
        combined = combined.sort_values(date_col).reset_index(drop=True)
    return combined


def temporal_train_test_split(
    df: pd.DataFrame,
    *,
    train_fraction: float = 0.8,
    date_col: str = "data_processo",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = df.sort_values(date_col).reset_index(drop=True) if date_col in df.columns else df
    cut = max(1, int(len(ordered) * train_fraction))
    if cut >= len(ordered):
        cut = len(ordered) - 1
    return ordered.iloc[:cut].copy(), ordered.iloc[cut:].copy()
