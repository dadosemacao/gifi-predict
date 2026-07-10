from __future__ import annotations

import pandas as pd

from ingest.config import IngestSettings
from ingest.observability.signals import SignalCollector
from ingest.transform.imputation import impute_db_lab
from ingest.transform.mix_features import derive_mix_features
from ingest.transform.pipeline import transform_historical
from ingest.validation.domain_rules import validate_mix


def test_proxy_db_imputation(settings: IngestSettings) -> None:
    df = pd.DataFrame({"DB_SGF": [500.0], "DB_LAB": [pd.NA]})
    signals = SignalCollector()
    out = impute_db_lab(df, settings, signals)
    assert abs(out.loc[0, "DB_LAB"] - 492.5) < 0.01
    assert out.loc[0, "db_origin"] == "proxy"
    assert "INGEST_PROXY_DB" in signals.codes()


def test_mix_features_entropy_and_dom() -> None:
    concentrated = pd.DataFrame(
        {"pct_A": [0.8], "pct_B": [0.05], "pct_C": [0.05], "pct_D": [0.05], "pct_MG": [0.05]}
    )
    balanced = pd.DataFrame(
        {"pct_A": [0.2], "pct_B": [0.2], "pct_C": [0.2], "pct_D": [0.2], "pct_MG": [0.2]}
    )
    c = derive_mix_features(concentrated).iloc[0]
    b = derive_mix_features(balanced).iloc[0]
    assert c["dom_A"] == 1
    assert c["mix_hhi"] > b["mix_hhi"]
    assert b["mix_entropy"] > c["mix_entropy"]


def test_tsa_filter(settings: IngestSettings, fixtures_dir) -> None:
    df = pd.read_csv(fixtures_dir / "synthetic_historical.csv")
    signals = SignalCollector()
    out, exclusions = transform_historical(df, settings, signals)
    assert (out["TSA_dia"] >= settings.tsa_train_min).all()
    assert "INGEST_FILTER_INFO" in signals.codes()
    assert exclusions.get("tsa_below_min", 0) >= 1


def test_mix_fail(settings: IngestSettings) -> None:
    df = pd.DataFrame(
        {
            "pct_A": [0.5],
            "pct_B": [0.2],
            "pct_C": [0.1],
            "pct_D": [0.1],
            "pct_MG": [0.05],
        }
    )
    signals = SignalCollector()
    validate_mix(df, settings, signals)
    assert "INGEST_MIX_FAIL" in signals.codes()
