from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from simulation.cascade.inference import infer_dataframe
from simulation.config import SimulationSettings
from simulation.package.publisher import load_champion_pipes


def run_infer_pipeline(
    settings: SimulationSettings,
    *,
    cenario_id: str,
    mode: str,
    output: Path | None = None,
) -> dict[str, Any]:
    pipes, feature_cols, pointer = load_champion_pipes(settings.models_path)

    infer_path = (
        settings.l2_path / "scenarios" / cenario_id / "infer_features.parquet"
    )
    if not infer_path.exists():
        raise FileNotFoundError(f"infer_features not found: {infer_path}")

    df = pd.read_parquet(infer_path)
    preds = infer_dataframe(
        df,
        mode,
        pipes,
        feature_cols,
        db_proxy_factor=settings.db_proxy_factor,
    )

    out_path = output or (
        settings.models_path / "predictions" / cenario_id / f"predictions_{mode.upper()}.parquet"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    preds.to_parquet(out_path, index=False)

    return {
        "run_id": pointer["run_id"],
        "cenario_id": cenario_id,
        "mode": mode.upper(),
        "rows": len(preds),
        "output": str(out_path),
    }
