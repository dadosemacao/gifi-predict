from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_scenario_upload(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, engine="openpyxl")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"unsupported scenario format: {path.suffix}")
