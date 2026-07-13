"""Exporta imputer de Extrativo_AT para o serving (Tier B).

Autor: Emerson Antônio
Data: 2026-07-13

Treina RandomForest em base/primeira_base.csv com features disponíveis na API
(pct_AB, pct_C, pct_DMG, Idade) para estimar Extrativo_AT ausente em requests.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

FEATURES = ["pct_AB", "pct_C", "pct_DMG", "Idade"]
TARGET = "Extrativo_AT"
RANDOM_STATE = 42


def main() -> None:
    csv_path = REPO / "base" / "primeira_base.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"base não encontrada: {csv_path}")

    df = pd.read_csv(csv_path)
    x = df[FEATURES].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(df[TARGET], errors="coerce")
    mask = y.notna() & x.notna().all(axis=1)
    if int(mask.sum()) < 50:
        raise RuntimeError("amostra insuficiente para treinar imputer serving")

    model = RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=5,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    model.fit(x.loc[mask, FEATURES], y.loc[mask])

    meta = {
        "features": FEATURES,
        "target": TARGET,
        "n_train_rows": int(mask.sum()),
        "y_min": float(y.loc[mask].min()),
        "y_max": float(y.loc[mask].max()),
        "range_min": 1.0,
        "range_max": 3.5,
        "source": str(csv_path),
    }
    out_dir = REPO / "models" / "ingest"
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / "extrativo_serving_imputer.joblib"
    joblib.dump({"model": model, "meta": meta}, artifact_path)

    pointer = {
        "artifact_path": "models/ingest/extrativo_serving_imputer.joblib",
        "features": FEATURES,
        "product": "extrativo_serving_imputer",
        "updated_at": "2026-07-13T120000Z",
    }
    (out_dir / "current_extr_imputer.json").write_text(
        json.dumps(pointer, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Imputer serving salvo: {artifact_path} ({meta['n_train_rows']} linhas)")


if __name__ == "__main__":
    main()
