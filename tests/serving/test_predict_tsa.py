from __future__ import annotations

import pytest

from serving.services.predict_tsa import run_predict_tsa


def test_predict_tsa_service_returns_prediction(
    repo_root,
    sample_process_payload: dict,
    tsa_pointer: dict,
) -> None:
    result = run_predict_tsa(
        sample_process_payload,
        repo_root=repo_root,
    )
    holdout = tsa_pointer["holdout_metrics"]
    assert result.product == "what_if_direct"
    assert result.family == tsa_pointer["family"]
    assert result.tsa_dia > 0
    assert result.metrics.mae_holdout == pytest.approx(holdout["mae"], rel=0.01)
    assert result.metrics.r2_holdout == pytest.approx(holdout["r2"], rel=0.01)
    assert result.metrics.interval_80_coverage == 0.0


def test_predict_tsa_api(client, sample_process_payload: dict) -> None:
    response = client.post("/api/predict-tsa", json=sample_process_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "what_if_direct"
    assert body["tsa_dia"] > 0


def test_predict_tsa_status_api(client, tsa_pointer: dict) -> None:
    response = client.get("/api/predict-tsa/status")
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "what_if_direct"
    assert body["family"] == tsa_pointer["family"]
    assert len(body["features"]) == 13
