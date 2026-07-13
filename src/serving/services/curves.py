from __future__ import annotations

import pandas as pd

from serving.schemas import CurvePoint


def build_curves(df: pd.DataFrame) -> list[CurvePoint]:
    curves: list[CurvePoint] = []
    ordered = df.sort_values("linha") if "linha" in df.columns else df
    for idx, row in ordered.iterrows():
        linha = row.get("linha", idx)
        label = f"linha-{int(linha)}"
        curves.append(
            CurvePoint(
                label=label,
                tsa_dia=float(row["TSA_dia"]),
                carga_alcalina=float(row["Carga_Alcalina"]),
                extrativo_at=float(row["Extrativo_AT"]),
            )
        )
    return curves
