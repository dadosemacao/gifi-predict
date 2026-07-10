from __future__ import annotations

import sys
from pathlib import Path

import pytest

from acceptance.config import AcceptanceSettings

sys.path.insert(0, str(Path(__file__).parent))
from build_l3_fixture import build_monotonic_candidate  # noqa: E402


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def l2_mini(repo_root: Path) -> Path:
    fixture = repo_root / "tests" / "simulation" / "fixtures" / "l2_mini"
    if not (fixture / "current.json").exists():
        sys.path.insert(0, str(repo_root / "tests" / "simulation"))
        from build_fixture import build_l2_mini  # noqa: E402

        build_l2_mini(fixture)
    return fixture


@pytest.fixture
def acceptance_settings(
    repo_root: Path, tmp_path: Path, l2_mini: Path
) -> AcceptanceSettings:
    return AcceptanceSettings(
        repo_root=repo_root,
        l2_root=Path("tests/simulation/fixtures/l2_mini"),
        models_root=tmp_path / "models",
        reports_root=tmp_path / "reports",
        logs_root=tmp_path / "logs",
        scenarios_dir=repo_root / "config" / "acceptance_scenarios",
        recompute_matriz_a=False,
    )


@pytest.fixture
def monotonic_run_id(acceptance_settings: AcceptanceSettings) -> str:
    return build_monotonic_candidate(
        acceptance_settings.models_path,
        run_id="test-monotonic-run",
        mae_tsa_cascade=30.0,
    )
