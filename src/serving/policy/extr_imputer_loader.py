from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

SERVING_EXTR_FEATURES = ["pct_AB", "pct_C", "pct_DMG", "Idade"]


@lru_cache(maxsize=4)
def load_extr_serving_imputer(repo_root: str) -> tuple[Any, dict[str, Any]]:
    root = Path(repo_root)
    pointer_path = root / "models" / "ingest" / "current_extr_imputer.json"
    artifact_path = root / "models" / "ingest" / "extrativo_serving_imputer.joblib"
    if pointer_path.exists():
        ptr = json.loads(pointer_path.read_text(encoding="utf-8"))
        rel = ptr.get("artifact_path", "models/ingest/extrativo_serving_imputer.joblib")
        artifact_path = root / rel

    if artifact_path.exists():
        payload = joblib.load(artifact_path)
        if isinstance(payload, dict) and "model" in payload:
            return payload["model"], dict(payload["meta"])
        return payload, {"features": SERVING_EXTR_FEATURES}

    return _fit_from_primeira_base(root)


def _fit_from_primeira_base(repo_root: Path) -> tuple[Any, dict[str, Any]]:
    csv_path = repo_root / "base" / "primeira_base.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            "extrativo_serving_imputer.joblib ausente; execute "
            "scripts/export_extrativo_serving_imputer.py"
        )
    df = pd.read_csv(csv_path)
    x = df[SERVING_EXTR_FEATURES].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(df["Extrativo_AT"], errors="coerce")
    mask = y.notna() & x.notna().all(axis=1)
    model = RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=1,
    )
    model.fit(x.loc[mask, SERVING_EXTR_FEATURES], y.loc[mask])
    meta = {
        "features": SERVING_EXTR_FEATURES,
        "n_train_rows": int(mask.sum()),
        "y_min": float(y.loc[mask].min()),
        "y_max": float(y.loc[mask].max()),
        "range_min": 1.0,
        "range_max": 3.5,
    }
    return model, meta
