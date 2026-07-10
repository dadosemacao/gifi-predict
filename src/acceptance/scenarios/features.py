from __future__ import annotations

import pandas as pd

from ingest.transform.mix_features import derive_mix_features


def prepare_scenario_row(
    inputs: dict,
    *,
    mode: str,
    db_proxy_factor: float = 0.985,
) -> dict:
    row = dict(inputs)
    if "Volume_m3" not in row and "Volume" in row:
        row["Volume_m3"] = row["Volume"]
    if "VMI" not in row:
        row["VMI"] = 0.25
    if (row.get("DB_LAB") is None or pd.isna(row.get("DB_LAB"))) and row.get(
        "DB_SGF"
    ) is not None:
        row["DB_LAB"] = db_proxy_factor * float(row["DB_SGF"])
    if mode.upper() == "A":
        row.pop("Extrativo_AT", None)
        row.pop("Carga_Alcalina", None)
    df = pd.DataFrame([row])
    df = derive_mix_features(df)
    return df.to_dict(orient="records")[0]


def prepare_scenario_frame(
    inputs: dict,
    *,
    mode: str,
    db_proxy_factor: float = 0.985,
) -> pd.DataFrame:
    return pd.DataFrame(
        [prepare_scenario_row(inputs, mode=mode, db_proxy_factor=db_proxy_factor)]
    )
