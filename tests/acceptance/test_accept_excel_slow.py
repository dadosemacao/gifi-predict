from __future__ import annotations

from pathlib import Path

import pytest

from acceptance.config import AcceptanceSettings
from acceptance.pipeline.accept import run_accept_pipeline


@pytest.mark.slow
def test_excel_candidate_matriz_a_fails(repo_root: Path):
    models_root = repo_root / "models"
    candidates = sorted((models_root / "candidates").glob("*/candidate_manifest.json"))
    if not candidates:
        pytest.skip("no local L3 candidates")
    run_id = candidates[-1].parent.name
    l2 = repo_root / "data" / "l2_excel_validation"
    if not (l2 / "current.json").exists():
        pytest.skip("Excel L2 validation path missing")

    settings = AcceptanceSettings(
        repo_root=repo_root,
        l2_root=l2,
        models_root=models_root,
        reports_root=repo_root / "reports" / "acceptance",
        logs_root=repo_root / "logs" / "acceptance",
        scenarios_dir=repo_root / "config" / "acceptance_scenarios",
        recompute_matriz_a=True,
    )
    result = run_accept_pipeline(settings, run_id=run_id)
    assert result["matriz_a"] is False
    assert result["release_ok"] is False
    assert result["demo_mode"] is True
