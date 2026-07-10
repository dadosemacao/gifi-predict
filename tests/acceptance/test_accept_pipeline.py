from __future__ import annotations

import json
from pathlib import Path

from build_l3_fixture import build_monotonic_candidate  # noqa: E402

from acceptance.pipeline.accept import run_accept_pipeline
from acceptance.pipeline.report import run_report_pipeline
from simulation.config import SimulationSettings
from simulation.pipeline.train import run_train_pipeline


def test_accept_pipeline_produces_report(acceptance_settings, l2_mini):
    sim_settings = SimulationSettings(
        repo_root=acceptance_settings.repo_root,
        l2_root=l2_mini,
        models_root=acceptance_settings.models_path,
        logs_root=acceptance_settings.logs_root / "simulation",
        tuning_enabled=False,
        min_train_rows=50,
    )
    train = run_train_pipeline(sim_settings)
    run_id = train["run_id"]

    result = run_accept_pipeline(acceptance_settings, run_id=run_id)
    assert "matriz_a" in result
    assert "matriz_b" in result
    assert "matriz_c" in result
    report_path = Path(result["report_dir"]) / "acceptance_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert "release_ok" in report
    assert "demo_mode" in report


def test_accept_pipeline_deterministic(acceptance_settings):
    run_id = build_monotonic_candidate(
        acceptance_settings.models_path,
        run_id="test-deterministic-run",
        mae_tsa_cascade=95.0,
    )
    first = run_accept_pipeline(acceptance_settings, run_id=run_id)
    second = run_accept_pipeline(acceptance_settings, run_id=run_id)
    r1 = json.loads(
        (Path(first["report_dir"]) / "acceptance_report.json").read_text(encoding="utf-8")
    )
    r2 = json.loads(
        (Path(second["report_dir"]) / "acceptance_report.json").read_text(encoding="utf-8")
    )
    for key in ("matriz_a", "matriz_b", "matriz_c", "release_ok"):
        assert r1[key] == r2[key]


def test_accept_report_readonly(acceptance_settings, monotonic_run_id):
    run_accept_pipeline(acceptance_settings, run_id=monotonic_run_id)
    out = run_report_pipeline(acceptance_settings, run_id=monotonic_run_id)
    assert out["run_id"] == monotonic_run_id
    assert "summary" in out
