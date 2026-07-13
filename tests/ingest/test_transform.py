from __future__ import annotations

import pandas as pd

from ingest.config import IngestSettings
from ingest.observability.signals import SignalCollector
from ingest.transform.imputation import (
    EXTR_IMPUTE_FEATURES,
    impute_db_lab,
    impute_extrativo_at,
)
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


def _extr_frame(n_measured: int, n_missing: int) -> pd.DataFrame:
    rows = []
    for i in range(n_measured + n_missing):
        measured = i < n_measured
        a = 0.2 + (i % 5) * 0.05
        feats = {
            "pct_A": a,
            "pct_B": 0.2,
            "pct_C": 0.2,
            "pct_D": 0.2,
            "pct_MG": max(0.0, 1.0 - a - 0.6),
            "pct_ABC": a + 0.4,
            "pct_CDMG": 0.6 - a + 0.4,
            "mix_entropy": 1.4 + (i % 3) * 0.05,
            "mix_hhi": 0.30 + (i % 4) * 0.01,
            "dom_A": 1.0 if a > 0.3 else 0.0,
            "dom_B": 0.0,
            "dom_C": 0.0,
            "dom_D": 0.0,
            "dom_MG": 0.0,
            "Idade": 3 + (i % 4),
        }
        feats["Extrativo_AT"] = 1.6 + a if measured else pd.NA
        feats["data_processo"] = pd.Timestamp("2024-01-01") + pd.Timedelta(days=i)
        rows.append(feats)
    return pd.DataFrame(rows)


def test_extrativo_imputation_fills_missing(settings: IngestSettings) -> None:
    assert "Extrativo_AT" not in EXTR_IMPUTE_FEATURES
    df = _extr_frame(n_measured=260, n_missing=40)
    signals = SignalCollector()
    out = impute_extrativo_at(df, settings, signals)

    assert out["Extrativo_AT"].isna().sum() == 0
    assert (out["extr_origin"] == "medido").sum() == 260
    assert (out["extr_origin"] == "estimado").sum() == 40
    assert "INGEST_PROXY_EXTR" in signals.codes()
    estimated = out.loc[out["extr_origin"] == "estimado", "Extrativo_AT"]
    assert estimated.between(settings.extr_range_min, settings.extr_range_max).all()


def test_extrativo_imputation_sparse_skips(settings: IngestSettings) -> None:
    df = _extr_frame(n_measured=10, n_missing=5)
    signals = SignalCollector()
    out = impute_extrativo_at(df, settings, signals)

    assert out["Extrativo_AT"].isna().sum() == 5
    assert (out["extr_origin"] == "medido").sum() == 10
    assert "INGEST_SPARSE_LAB" in signals.codes()
    assert "INGEST_PROXY_EXTR" not in signals.codes()


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
