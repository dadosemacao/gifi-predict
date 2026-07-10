from __future__ import annotations

import json
from pathlib import Path

import pytest

from simulation.pipeline.evaluate import run_evaluate_pipeline
from simulation.pipeline.train import run_train_pipeline


def test_train_pipeline(settings):
    result = run_train_pipeline(settings)
    assert result["run_id"]
    assert (Path(result["candidate_dir"]) / "candidate_manifest.json").exists()
    manifest = json.loads(
        (Path(result["candidate_dir"]) / "candidate_manifest.json").read_text()
    )
    assert manifest["l2"]["dataset_version"]
    assert "elo1" in manifest["champions"]
    assert "mae_tsa_cascade" in result["metrics"]


def test_evaluate_pipeline(settings):
    train = run_train_pipeline(settings)
    eval_result = run_evaluate_pipeline(settings)
    assert eval_result["run_id"] == train["run_id"]
    assert "mae_extrativos" in eval_result["metrics"]
    assert "mae_carga" in eval_result["metrics"]
    assert "mae_tsa_cascade" in eval_result["metrics"]


def test_reproducibility(settings):
    first = run_train_pipeline(settings)
    second = run_train_pipeline(settings)
    assert first["metrics"]["mae_tsa_cascade"] == pytest.approx(
        second["metrics"]["mae_tsa_cascade"]
    )
