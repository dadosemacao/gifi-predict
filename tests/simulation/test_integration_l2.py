from __future__ import annotations

from pathlib import Path

import pytest

from simulation.config import SimulationSettings
from simulation.l2.guard import validate_holdout_window
from simulation.l2.loader import load_l2_bundle
from simulation.pipeline.train import run_train_pipeline


@pytest.mark.slow
def test_integration_l2_excel(repo_root: Path, tmp_path: Path):
    l2_path = repo_root / "data" / "l2_excel_validation"
    if not (l2_path / "current.json").exists():
        pytest.skip("Excel L2 validation data not available")

    settings = SimulationSettings(
        repo_root=repo_root,
        l2_root=l2_path,
        models_root=tmp_path / "models",
        logs_root=tmp_path / "logs",
        min_train_rows=50,
    )
    bundle = load_l2_bundle(l2_path)
    validate_holdout_window(
        bundle.holdout,
        start=settings.holdout_start,
        end=settings.holdout_end,
    )
    result = run_train_pipeline(settings)
    assert result["metrics"]["holdout_rows"] == 500
    assert (Path(result["candidate_dir"]) / "metrics_holdout.json").exists()
