from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from serving.app import create_app
from serving.config import ServingSettings
from ingest.config import IngestSettings
from simulation.config import SimulationSettings


@pytest.fixture
def sample_process_payload(repo_root: Path) -> dict:
    row = pd.read_csv(repo_root / "base" / "primeira_base.csv").iloc[0]
    return {
        "carga_alcalina": float(row["Carga_Alcalina"]),
        "kappa": float(row["Kappa"]),
        "prod_alcali_class": float(row["Prod_alcali_class"]),
        "db_sgf": float(row["DB_SGF"]),
        "casca_pct": float(row["Casca_pct"]),
        "extrativo_at": float(row["Extrativo_AT"]),
        "tpc": float(row["TPC"]),
        "idade": float(row["Idade"]),
        "vmi_le_021": float(row["vmi_le_021"]),
        "vmi_021_025": float(row["vmi_021_025"]),
        "vmi_gt_025": float(row["vmi_gt_025"]),
        "pct_ab": float(row["pct_AB"]),
        "pct_c": float(row["pct_C"]),
        "pct_dmg": float(row["pct_DMG"]),
    }


@pytest.fixture
def tsa_pointer(repo_root: Path) -> dict:
    path = repo_root / "models" / "primeira_base" / "current_tsa.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def forecast_pointer(repo_root: Path) -> dict:
    path = repo_root / "models" / "primeira_base" / "current_forecast.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def default_run_id(repo_root: Path) -> str:
    cfg = ServingSettings.from_yaml(repo_root)
    return cfg.default_run_id


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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
