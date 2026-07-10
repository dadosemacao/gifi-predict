from __future__ import annotations

import pandas as pd

from ingest.batch.pipeline import run_batch_pipeline
from ingest.observability.signals import SignalCollector
from ingest.validation.domain_rules import validate_mix


def test_batch_pipeline_publishes(settings, fixtures_dir) -> None:
    source = fixtures_dir / "synthetic_historical.csv"
    result = run_batch_pipeline(source, settings)
    assert result["publish_status"] in ("published_ok", "published_with_warnings")
    current = settings.l2_path / "current.json"
    assert current.exists()


def test_mix_invalid_blocks_publish(settings) -> None:
    df = pd.DataFrame(
        {
            "data_processo": ["2024-01-01"],
            "turno": [1],
            "TSA_dia": [1200],
            "DB_SGF": [480],
            "pct_A": [0.5],
            "pct_B": [0.2],
            "pct_C": [0.1],
            "pct_D": [0.05],
            "pct_MG": [0.05],
            "TPC": [60],
            "Idade": [8],
            "VMI": [0.24],
            "Volume": [1000],
            "Kappa": [17],
        }
    )
    path = settings.l2_path / "bad.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    signals = SignalCollector()
    validate_mix(df, settings, signals)
    assert signals.has_blocking
