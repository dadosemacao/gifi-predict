from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.pipeline import Pipeline

from simulation.exceptions import ScenarioRejectError


def _row_frame(row: dict[str, Any], features: list[str]) -> pd.DataFrame:
    values: dict[str, float] = {}
    for col in features:
        val = row.get(col)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            values[col] = float("nan")
        else:
            values[col] = float(val)
    return pd.DataFrame([values], columns=features)


def infer_cascade_row(
    row: dict[str, Any],
    mode: str,
    pipes: dict[str, Pipeline],
    feature_cols: dict[str, list[str]],
    *,
    db_proxy_factor: float = 0.985,
    strict_scenario: bool = True,
) -> dict[str, Any]:
    x = dict(row)
    direct_tsa = "elo1" not in pipes and "elo2" not in pipes

    if not direct_tsa:
        if mode.upper() == "A" and strict_scenario:
            if x.get("Carga_Alcalina") is not None and pd.notna(x.get("Carga_Alcalina")):
                raise ScenarioRejectError(
                    "INGEST_SCENARIO_REJECT: Carga injetada em Modo A"
                )
            if x.get("Extrativo_AT") is not None and pd.notna(x.get("Extrativo_AT")):
                raise ScenarioRejectError(
                    "INGEST_SCENARIO_REJECT: Extrativo injetado em Modo A"
                )
        elif mode.upper() == "A":
            x.pop("Extrativo_AT", None)
            x.pop("Carga_Alcalina", None)

    if direct_tsa:
        if mode.upper() == "A" and strict_scenario:
            if x.get("Carga_Alcalina") is not None and pd.notna(x.get("Carga_Alcalina")):
                raise ScenarioRejectError(
                    "INGEST_SCENARIO_REJECT: Carga injetada em Modo A"
                )
            if x.get("Extrativo_AT") is not None and pd.notna(x.get("Extrativo_AT")):
                raise ScenarioRejectError(
                    "INGEST_SCENARIO_REJECT: Extrativo injetado em Modo A"
                )
        tsa = float(
            pipes["elo3"].predict(_row_frame(x, feature_cols["elo3"]))[0]
        )
        extr = x.get("Extrativo_AT")
        carga = x.get("Carga_Alcalina")
        return {
            "Extrativo_AT": float(extr) if extr is not None and pd.notna(extr) else None,
            "Carga_Alcalina": float(carga) if carga is not None and pd.notna(carga) else None,
            "TSA_dia": tsa,
        }

    if (
        mode.upper() == "B"
        and x.get("Extrativo_AT") is not None
        and pd.notna(x.get("Extrativo_AT"))
    ):
        extr = float(x["Extrativo_AT"])
    else:
        extr = float(
            pipes["elo1"].predict(_row_frame(x, feature_cols["elo1"]))[0]
        )

    x["Extrativo_AT"] = extr

    if (
        mode.upper() == "B"
        and x.get("Carga_Alcalina") is not None
        and pd.notna(x.get("Carga_Alcalina"))
    ):
        carga = float(x["Carga_Alcalina"])
    else:
        carga = float(
            pipes["elo2"].predict(_row_frame(x, feature_cols["elo2"]))[0]
        )

    x["Carga_Alcalina"] = carga

    if (x.get("DB_LAB") is None or pd.isna(x.get("DB_LAB"))) and x.get("DB_SGF") is not None:
        x["DB_LAB"] = db_proxy_factor * float(x["DB_SGF"])

    tsa = float(
        pipes["elo3"].predict(_row_frame(x, feature_cols["elo3"]))[0]
    )
    return {
        "Extrativo_AT": extr,
        "Carga_Alcalina": carga,
        "TSA_dia": tsa,
        "mode": mode.upper(),
    }


def infer_dataframe(
    df: pd.DataFrame,
    mode: str,
    pipes: dict[str, Pipeline],
    feature_cols: dict[str, list[str]],
    *,
    db_proxy_factor: float = 0.985,
    strict_scenario: bool = True,
) -> pd.DataFrame:
    rows = [
        infer_cascade_row(
            record,
            mode,
            pipes,
            feature_cols,
            db_proxy_factor=db_proxy_factor,
            strict_scenario=strict_scenario,
        )
        for record in df.to_dict(orient="records")
    ]
    return pd.DataFrame(rows)
