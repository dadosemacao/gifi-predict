from __future__ import annotations

from pathlib import Path

import pytest

from ingest.config import IngestSettings
from serving.app import create_app
from serving.config import ServingSettings
from simulation.config import SimulationSettings


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def default_run_id(repo_root: Path) -> str:
    cfg = ServingSettings.from_yaml(repo_root)
    return cfg.default_run_id


@pytest.fixture
def serving_settings(repo_root: Path, tmp_path: Path) -> ServingSettings:
    return ServingSettings(
        repo_root=repo_root,
        default_run_id=ServingSettings.from_yaml(repo_root).default_run_id,
        default_forecast_run_id=ServingSettings.from_yaml(repo_root).default_forecast_run_id,
        default_tsa_run_id=ServingSettings.from_yaml(repo_root).default_tsa_run_id,
        reports_root=Path("reports/acceptance"),
        static_dir=tmp_path / "static",
        audit_enabled=True,
        audit_db_path=tmp_path / "serving_audit.db",
    )


@pytest.fixture
def audit_db(serving_settings: ServingSettings) -> Path:
    return serving_settings.audit_db_path_resolved


@pytest.fixture
def ingest_settings(repo_root: Path, tmp_path: Path) -> IngestSettings:
    return IngestSettings(
        repo_root=repo_root,
        l2_root=tmp_path / "l2",
        logs_root=tmp_path / "logs",
    )


@pytest.fixture
def sim_settings(repo_root: Path, ingest_settings: IngestSettings) -> SimulationSettings:
    return SimulationSettings(
        repo_root=repo_root,
        l2_root=ingest_settings.l2_root,
        models_root=Path("models"),
        logs_root=Path("logs/simulation"),
        tuning_enabled=False,
        families=["baseline", "elasticnet", "randomforest"],
    )


@pytest.fixture
def client(serving_settings: ServingSettings):
    from fastapi.testclient import TestClient

    with TestClient(create_app(serving_settings)) as test_client:
        yield test_client


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "ingest" / "fixtures"
