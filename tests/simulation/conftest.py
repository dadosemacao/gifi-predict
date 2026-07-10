from __future__ import annotations

import sys
from pathlib import Path

import pytest

from simulation.config import SimulationSettings

sys.path.insert(0, str(Path(__file__).parent))
from build_fixture import build_l2_mini  # noqa: E402


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def l2_mini(repo_root: Path) -> Path:
    fixture = repo_root / "tests" / "simulation" / "fixtures" / "l2_mini"
    if not (fixture / "current.json").exists():
        build_l2_mini(fixture)
    return fixture


@pytest.fixture
def settings(repo_root: Path, tmp_path: Path, l2_mini: Path) -> SimulationSettings:
    return SimulationSettings(
        repo_root=repo_root,
        l2_root=l2_mini,
        models_root=tmp_path / "models",
        logs_root=tmp_path / "logs",
        min_train_rows=50,
        families=["baseline", "elasticnet", "randomforest"],
        tuning_enabled=False,
    )
