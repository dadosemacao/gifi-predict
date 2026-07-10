from __future__ import annotations

import pandas as pd

from simulation.features.elo_specs import default_elo_specs
from simulation.features.matrix import build_matrix
from simulation.models.families import make_family
from simulation.models.oof_stack import enrich_elo3_oof_features


def test_oof_stack_expands_elo3_rows():
    specs = default_elo_specs()
    rows = []
    for i in range(120):
        rows.append(
            {
                "data_processo": f"2024-01-{(i % 28) + 1:02d}",
                "pct_A": 0.2,
                "pct_B": 0.2,
                "pct_C": 0.2,
                "pct_D": 0.2,
                "pct_MG": 0.2,
                "pct_ABC": 0.6,
                "pct_CDMG": 0.8,
                "mix_entropy": 1.5,
                "mix_hhi": 0.2,
                "dom_A": 0.2,
                "dom_B": 0.2,
                "dom_C": 0.2,
                "dom_D": 0.2,
                "dom_MG": 0.2,
                "Idade": 5.0,
                "Extrativo_AT": 2.0 if i % 3 == 0 else None,
                "Carga_Alcalina": 18.0 + (i % 5) * 0.1,
                "TPC": 70.0,
                "DB_SGF": 480.0,
                "DB_LAB": 470.0,
                "VMI": 0.22,
                "Volume_m3": 1000.0,
                "Kappa": 15.0,
                "TSA_dia": 3400.0 + i,
            }
        )
    df = pd.DataFrame(rows)
    fallback = {
        "elo1": make_family("baseline", 42),
        "elo2": make_family("baseline", 42),
    }
    X1, y1, _, _ = build_matrix(df, "elo1", specs, enforce_min_rows=False)
    fallback["elo1"].fit(X1, y1)
    df2 = df.copy()
    df2["Extrativo_AT"] = df2["Extrativo_AT"].fillna(2.0)
    X2, y2, _, _ = build_matrix(df2, "elo2", specs, enforce_min_rows=False)
    fallback["elo2"].fit(X2, y2)
    X_before, _, _, _ = build_matrix(df, "elo3", specs, enforce_min_rows=False)
    enriched, meta = enrich_elo3_oof_features(
        df,
        specs,
        random_state=42,
        cv_folds=3,
        min_train_rows=20,
        fallback_elo12=fallback,
    )
    X_after, _, _, _ = build_matrix(enriched, "elo3", specs, enforce_min_rows=False)

    assert len(X_after) > len(X_before)
    assert meta["oof_folds"] >= 2
    assert enriched["Extrativo_AT"].notna().sum() > df["Extrativo_AT"].notna().sum()
