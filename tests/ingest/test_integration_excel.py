from __future__ import annotations

import pytest

from ingest.batch.pipeline import run_batch_pipeline
from ingest.config import IngestSettings


@pytest.mark.slow
def test_smoke_excel_sample(repo_root, tmp_path) -> None:
    excel = repo_root / "excels" / "Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx"
    if not excel.exists():
        pytest.skip("Excel reference not available")
    settings = IngestSettings(repo_root=repo_root, l2_root=tmp_path / "l2")
    result = run_batch_pipeline(excel, settings)
    assert result["publish_status"] in ("published_ok", "published_with_warnings")
    assert "published_path" in result
