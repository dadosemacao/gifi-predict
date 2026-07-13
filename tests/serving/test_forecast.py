from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from serving.services.forecast import run_forecast


def _sample_payload(repo_root: Path) -> dict:
    row = pd.read_csv(repo_root / "base" / "primeira_base.csv").iloc[0]
    history = [float(row["TSA_dia"])] * 7
    return {
        "tsa_history": history,
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


def test_forecast_service_returns_prediction(repo_root: Path) -> None:
    payload = _sample_payload(repo_root)
    result = run_forecast(
        payload,
        repo_root=repo_root,
        run_id="2026-07-13T104544Z",
    )
    assert result.product == "forecast_operacional"
    assert result.family == "extratrees"
    assert result.tsa_dia > 0
    assert result.tsa_dia_lo <= result.tsa_dia <= result.tsa_dia_hi
    assert result.baselines["roll3"] == pytest.approx(payload["tsa_history"][-1], rel=0.01)
    assert result.metrics.mae_holdout == pytest.approx(67.6, rel=0.01)
    assert result.metrics.r2_holdout == pytest.approx(0.252, rel=0.01)
    assert result.metrics.interval_80_coverage == pytest.approx(0.71, rel=0.01)


def test_forecast_api(client) -> None:
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    payload = _sample_payload(repo_root)
    response = client.post("/api/forecast", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "forecast_operacional"
    assert body["tsa_dia"] > 0


def test_forecast_status_api(client) -> None:
    response = client.get("/api/forecast/status")
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "forecast_operacional"
    assert body["family"] == "extratrees"
    assert body["holdout_mae"] is not None


def test_forecast_requires_history(repo_root: Path) -> None:
    payload = _sample_payload(repo_root)
    payload["tsa_history"] = payload["tsa_history"][:3]
    with pytest.raises(ValueError, match="tsa_history"):
        run_forecast(payload, repo_root=repo_root, run_id="2026-07-13T104544Z")
