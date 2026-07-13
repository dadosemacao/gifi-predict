from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from serving.services.predict_tsa import run_predict_tsa


def _sample_process(repo_root: Path) -> dict:
    row = pd.read_csv(repo_root / "base" / "primeira_base.csv").iloc[0]
    return {
        "carga_alcalina": float(row["Carga_Alcalina"]),
        "kappa": float(row["Kappa"]),
        "db_sgf": float(row["DB_SGF"]),
        "db_lab": float(row["DB_LAB"]),
        "secura_pct": float(row["Secura_pct"]),
        "casca_pct": float(row["Casca_pct"]),
        "extrativo_total": float(row["Extrativo_Total"]),
        "extrativo_at": float(row["Extrativo_AT"]),
        "extrativo_sgf": float(row["Extrativo_SGF"]),
        "tpc": float(row["TPC"]),
        "idade": float(row["Idade"]),
        "vmi_le_021": float(row["vmi_le_021"]),
        "vmi_021_025": float(row["vmi_021_025"]),
        "vmi_gt_025": float(row["vmi_gt_025"]),
        "pct_ab": float(row["pct_AB"]),
        "pct_c": float(row["pct_C"]),
        "pct_dmg": float(row["pct_DMG"]),
    }


def test_predict_tsa_service_returns_prediction(repo_root: Path) -> None:
    payload = _sample_process(repo_root)
    result = run_predict_tsa(
        payload,
        repo_root=repo_root,
        run_id="2026-07-13T102553Z",
    )
    assert result.product == "what_if_direct"
    assert result.family == "catboost"
    assert result.tsa_dia > 0
    assert result.metrics.mae_holdout == pytest.approx(103.7, rel=0.01)
    assert result.metrics.r2_holdout == pytest.approx(-0.092, rel=0.01)
    assert result.metrics.interval_80_coverage == 0.0


def test_predict_tsa_api(client) -> None:
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    payload = _sample_process(repo_root)
    response = client.post("/api/predict-tsa", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "what_if_direct"
    assert body["tsa_dia"] > 0


def test_predict_tsa_status_api(client) -> None:
    response = client.get("/api/predict-tsa/status")
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "what_if_direct"
    assert body["family"] == "catboost"
    assert len(body["features"]) == 17
