from __future__ import annotations

import pandas as pd

from simulation.forecast.specs import LAG_FEATURES, PROCESS_FEATURES


def compute_lags(tsa_history: list[float]) -> dict[str, float]:
    """Calcula lags a partir do histórico cronológico de TSA (último = mais recente)."""
    if len(tsa_history) < 3:
        raise ValueError("tsa_history requer ao menos 3 valores para TSA_roll3")
    series = pd.Series(tsa_history, dtype=float)
    return {
        "TSA_lag1": float(series.iloc[-1]),
        "TSA_roll3": float(series.iloc[-3:].mean()),
        "TSA_roll7": float(series.iloc[-7:].mean()) if len(series) >= 7 else float(series.mean()),
    }


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame[PROCESS_FEATURES + LAG_FEATURES].copy()
    out["DB_c"] = frame["DB_LAB"] - 490.0
    out["DB_c2"] = out["DB_c"] ** 2
    out["TPC_crit"] = (frame["TPC"] < 45).astype(float)
    out["TPC_opt"] = ((frame["TPC"] >= 60) & (frame["TPC"] <= 90)).astype(float)
    out["Carga_crit"] = (frame["Carga_Alcalina"] > 21).astype(float)
    out["Carga_opt"] = (
        (frame["Carga_Alcalina"] >= 18.5) & (frame["Carga_Alcalina"] <= 20.5)
    ).astype(float)
    out["Extr_crit"] = (frame["Extrativo_AT"] > 2.45).astype(float)
    out["Extr_x_Carga"] = frame["Extrativo_AT"] * frame["Carga_Alcalina"]
    out["DB_x_Extr"] = out["DB_c"] * frame["Extrativo_AT"]
    out["TPC_x_VMIgt"] = frame["TPC"] * frame["vmi_gt_025"]
    return out


def build_process_row(process: dict[str, float], lags: dict[str, float]) -> pd.DataFrame:
    row = {**process, **lags}
    missing = [c for c in PROCESS_FEATURES + LAG_FEATURES if c not in row]
    if missing:
        raise ValueError(f"campos ausentes: {missing}")
    return pd.DataFrame([row])
