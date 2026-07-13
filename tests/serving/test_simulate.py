from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ingest.config import IngestSettings
from serving.config import ServingSettings
from serving.policy.release import load_release_context
from serving.services.simulate import run_simulate_upload
from simulation.config import SimulationSettings


@pytest.fixture
def mode_b_fixture(fixtures_dir: Path) -> Path:
    return fixtures_dir / "scenario_mode_b_ok.csv"


def test_simulate_mode_b_returns_curves_and_detractors(
    repo_root: Path,
    ingest_settings: IngestSettings,
    sim_settings: SimulationSettings,
    mode_b_fixture: Path,
    default_run_id: str,
) -> None:
    ctx = load_release_context(
        default_run_id, ServingSettings.from_yaml(repo_root)
    )
    result = run_simulate_upload(
        mode_b_fixture,
        cenario_id="ui-test-b",
        mode="B",
        release_ctx=ctx,
        demo=True,
        ingest_settings=ingest_settings,
        sim_settings=sim_settings,
    )
    assert result.mode == "B"
    assert result.demo is True
    assert len(result.curves) >= 1
    assert len(result.detractors) <= 3
    assert result.curves[0].tsa_dia > 0


def test_simulate_api_mode_a(
    client: TestClient,
    fixtures_dir: Path,
) -> None:
    path = fixtures_dir / "scenario_mode_b_ok.csv"
    with path.open("rb") as fh:
        response = client.post(
            "/api/simulate",
            files={"file": ("scenario_mode_b_ok.csv", fh, "text/csv")},
            data={"mode": "B", "demo": "true"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["curves"]
    assert body["demo"] is True
    assert len(body["detractors"]) <= 3
