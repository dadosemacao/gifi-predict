from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from simulation.pipeline.infer import run_infer_pipeline
from simulation.pipeline.train import run_train_pipeline


def _holdout_path(l2_root: Path) -> Path:
    pointer = json.loads((l2_root / "current.json").read_text(encoding="utf-8"))
    return Path(pointer["paths"]["holdout_features"])


def _publish_mode_a_scenario(l2_root: Path, cenario_id: str, *, n_rows: int = 5) -> None:
    holdout = pd.read_parquet(_holdout_path(l2_root)).head(n_rows)
    infer_df = holdout.drop(
        columns=["Extrativo_AT", "Carga_Alcalina", "TSA_dia"],
        errors="ignore",
    )
    scenario_dir = l2_root / "scenarios" / cenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)
    infer_df.to_parquet(scenario_dir / "infer_features.parquet", index=False)


def test_infer_pipeline_with_run_id(settings, tmp_path):
    train = run_train_pipeline(settings)
    run_id = train["run_id"]

    pointer = settings.models_path / "current_candidate.json"
    if pointer.exists():
        pointer.unlink()

    cenario_id = "AT-006-mini"
    _publish_mode_a_scenario(settings.l2_path, cenario_id)

    result = run_infer_pipeline(
        settings,
        cenario_id=cenario_id,
        mode="A",
        run_id=run_id,
        output=tmp_path / "preds.parquet",
    )

    assert result["run_id"] == run_id
    assert result["mode"] == "A"
    assert result["rows"] == 5

    preds = pd.read_parquet(result["output"])
    assert {"Extrativo_AT", "Carga_Alcalina", "TSA_dia", "mode"}.issubset(preds.columns)
    assert preds["mode"].eq("A").all()
    assert preds["TSA_dia"].notna().all()


def test_infer_pipeline_mode_b_with_run_id(settings, tmp_path):
    train = run_train_pipeline(settings)
    run_id = train["run_id"]

    holdout = pd.read_parquet(_holdout_path(settings.l2_path)).head(3)
    cenario_id = "AT-007-mini"
    scenario_dir = settings.l2_path / "scenarios" / cenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)
    holdout.to_parquet(scenario_dir / "infer_features.parquet", index=False)

    result = run_infer_pipeline(
        settings,
        cenario_id=cenario_id,
        mode="B",
        run_id=run_id,
        output=tmp_path / "preds_b.parquet",
    )

    preds = pd.read_parquet(result["output"])
    injected = holdout[["Extrativo_AT", "Carga_Alcalina"]].reset_index(drop=True)
    actual = preds[["Extrativo_AT", "Carga_Alcalina"]].reset_index(drop=True)
    pd.testing.assert_series_equal(
        injected["Extrativo_AT"],
        actual["Extrativo_AT"],
        check_names=False,
    )
    pd.testing.assert_series_equal(
        injected["Carga_Alcalina"],
        actual["Carga_Alcalina"],
        check_names=False,
    )
