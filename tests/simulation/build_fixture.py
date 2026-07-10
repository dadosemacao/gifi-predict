from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def _synthetic_rows(n: int, start: date) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n):
        pct_a, pct_b, pct_c, pct_d, pct_mg = rng.dirichlet([2, 2, 2, 2, 1])
        extr = 8.0 + rng.normal(0, 0.5)
        carga = 80.0 + rng.normal(0, 5)
        tsa = 1200.0 + rng.normal(0, 40)
        rows.append(
            {
                "data_processo": str(start + timedelta(days=i)),
                "pct_A": pct_a,
                "pct_B": pct_b,
                "pct_C": pct_c,
                "pct_D": pct_d,
                "pct_MG": pct_mg,
                "pct_ABC": pct_a + pct_b + pct_c,
                "pct_CDMG": pct_c + pct_d + pct_mg,
                "mix_entropy": float(rng.uniform(1.0, 2.0)),
                "mix_hhi": float(rng.uniform(0.2, 0.4)),
                "dom_A": pct_a,
                "dom_B": pct_b,
                "dom_C": pct_c,
                "dom_D": pct_d,
                "dom_MG": pct_mg,
                "Idade": float(rng.integers(1, 10)),
                "Extrativo_AT": extr,
                "TPC": 1.0 + rng.normal(0, 0.05),
                "DB_SGF": 1.2 + rng.normal(0, 0.05),
                "DB_LAB": 1.18 + rng.normal(0, 0.05),
                "Carga_Alcalina": carga,
                "VMI": 0.2 + rng.uniform(0, 0.1),
                "Volume_m3": 3000 + rng.normal(0, 100),
                "Kappa": 15 + rng.normal(0, 1),
                "TSA_dia": tsa,
                "Casca_pct": float(rng.uniform(5, 15)),
                "db_origin": "lab",
            }
        )
    return pd.DataFrame(rows)


def build_l2_mini(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    published = target_dir / "published" / "2026-07-10T12:00:00Z"
    published.mkdir(parents=True, exist_ok=True)

    train = _synthetic_rows(65, date(2024, 1, 1))
    holdout = _synthetic_rows(10, date(2025, 5, 1))
    train_path = published / "train_features.parquet"
    holdout_path = published / "holdout_features.parquet"
    train.to_parquet(train_path, index=False)
    holdout.to_parquet(holdout_path, index=False)

    manifest = {
        "schema_version": "1.0.0",
        "dataset_version": "2026-07-10T12:00:00Z",
        "source_hash": "sha256:mini",
        "holdout_eligible": True,
        "publish_status": "published_ok",
    }
    manifest_path = published / "batch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    pointer = {
        "dataset_version": "2026-07-10T12:00:00Z",
        "schema_version": "1.0.0",
        "paths": {
            "train_features": str(train_path),
            "holdout_features": str(holdout_path),
        },
        "manifest": str(manifest_path),
        "updated_at": "2026-07-10T12:00:00Z",
    }
    (target_dir / "current.json").write_text(json.dumps(pointer, indent=2), encoding="utf-8")
    return target_dir


if __name__ == "__main__":
    root = Path(__file__).resolve().parent / "fixtures" / "l2_mini"
    build_l2_mini(root)
    print(f"built {root}")
