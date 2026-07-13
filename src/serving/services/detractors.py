from __future__ import annotations

import pandas as pd


def build_elo3_explain_row(
    row_df: pd.DataFrame,
    feature_names: list[str],
) -> pd.DataFrame:
    frame = row_df.copy()
    if "Volume" in frame.columns and "Volume_m3" not in frame.columns:
        frame["Volume_m3"] = frame["Volume"]
    missing = [c for c in feature_names if c not in frame.columns]
    for col in missing:
        frame[col] = float("nan")
    return frame[feature_names]
