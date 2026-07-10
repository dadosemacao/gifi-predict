from __future__ import annotations

from pathlib import Path

import pytest

from ingest.config import IngestSettings


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def settings(repo_root: Path, tmp_path: Path) -> IngestSettings:
    return IngestSettings(
        repo_root=repo_root,
        l2_root=tmp_path / "l2",
        logs_root=tmp_path / "logs",
    )


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
