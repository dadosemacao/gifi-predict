"""Analytics opt-in para /api/predict-tsa — sweep + ablação local.

Autor: Emerson Antônio
Data: 2026-07-13
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from simulation.process_specs import PROCESS_API_TO_COLUMN

SENSITIVITY_RANGES: dict[str, tuple[float, float]] = {
    "db_sgf": (465.0, 515.0),
    "carga_alcalina": (17.5, 21.0),
    "kappa": (15.0, 18.5),
    "casca_pct": (0.0, 1.5),
    "tpc": (45.0, 90.0),
    "extrativo_at": (1.0, 3.5),
    "idade": (4.0, 10.0),
}

ABLATION_POOL: tuple[str, ...] = tuple(SENSITIVITY_RANGES.keys())
SENSITIVITY_WHITELIST = frozenset(SENSITIVITY_RANGES)

DISCLAIMER_ANALYTICS_SUFFIX = (
    " Explicabilidade assistida (sensitivity/detractors por ablação local) "
    "— não é Matriz C e não libera o gate de release."
)


@dataclass(frozen=True)
class AnalyticsResult:
    sensitivity: list[dict[str, float]]
    detractors: list[dict[str, float | str]]
    sensitivity_variable: str
    sensitivity_steps: int


def _predict_rows(
    pipe: Pipeline,
    features: list[str],
    base_cols: dict[str, float],
    overrides: list[dict[str, float]],
) -> list[float]:
    rows: list[dict[str, float]] = []
    for ov in overrides:
        row = dict(base_cols)
        for api_key, value in ov.items():
            row[PROCESS_API_TO_COLUMN[api_key]] = float(value)
        rows.append(row)
    frame = pd.DataFrame(rows)
    return [float(x) for x in pipe.predict(frame[features])]


def build_analytics(
    *,
    pipe: Pipeline,
    features: list[str],
    resolved_api: dict[str, float],
    tsa_dia: float,
    sensitivity_variable: str,
    sensitivity_steps: int,
) -> AnalyticsResult:
    if sensitivity_variable not in SENSITIVITY_WHITELIST:
        raise ValueError(
            f"sensitivity_variable inválida: {sensitivity_variable!r}; "
            f"use uma de {sorted(SENSITIVITY_WHITELIST)}"
        )
    if not 5 <= sensitivity_steps <= 31:
        raise ValueError("sensitivity_steps deve estar em [5, 31]")

    low, high = SENSITIVITY_RANGES[sensitivity_variable]
    grid = np.linspace(low, high, num=sensitivity_steps)
    base_cols = {
        PROCESS_API_TO_COLUMN[k]: float(resolved_api[k]) for k in PROCESS_API_TO_COLUMN
    }
    sweep_preds = _predict_rows(
        pipe,
        features,
        base_cols,
        [{sensitivity_variable: float(v)} for v in grid],
    )
    sensitivity = [
        {"value": float(v), "tsa_dia": float(p)}
        for v, p in zip(grid, sweep_preds, strict=True)
    ]

    abl_overrides: list[dict[str, float]] = []
    abl_features: list[str] = []
    for feat in ABLATION_POOL:
        lo, hi = SENSITIVITY_RANGES[feat]
        abl_features.append(feat)
        abl_overrides.append({feat: (lo + hi) / 2.0})
    abl_preds = _predict_rows(pipe, features, base_cols, abl_overrides)
    ranked = sorted(
        (
            {
                "feature": f,
                "delta_tsa": float(p - tsa_dia),
                "method": "local_ablation",
            }
            for f, p in zip(abl_features, abl_preds, strict=True)
        ),
        key=lambda d: (-abs(float(d["delta_tsa"])), str(d["feature"])),
    )
    return AnalyticsResult(
        sensitivity=sensitivity,
        detractors=ranked[:3],
        sensitivity_variable=sensitivity_variable,
        sensitivity_steps=sensitivity_steps,
    )
