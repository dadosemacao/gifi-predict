from __future__ import annotations

import pytest

from serving.services.forecast import run_forecast


def _forecast_payload(sample_process_payload: dict) -> dict:
    history = [sample_process_payload.get("tsa_dia", 3289.0)] * 7
    return {"tsa_history": history, **sample_process_payload}


def test_forecast_service_returns_prediction(
    repo_root,
    sample_process_payload: dict,
    forecast_pointer: dict,
) -> None:
    payload = _forecast_payload(sample_process_payload)
    result = run_forecast(
        payload,
        repo_root=repo_root,
    )
    holdout = forecast_pointer["holdout_metrics"]
    coverage = forecast_pointer.get("interval_80_coverage", 0.0)
    assert result.product == "forecast_operacional"
    assert result.family == forecast_pointer["family"]
    assert result.tsa_dia > 0
    assert result.tsa_dia_lo <= result.tsa_dia <= result.tsa_dia_hi
    assert result.baselines["roll3"] == pytest.approx(payload["tsa_history"][-1], rel=0.01)
    assert result.metrics.mae_holdout == pytest.approx(holdout["mae"], rel=0.01)
    assert result.metrics.r2_holdout == pytest.approx(holdout["r2"], rel=0.01)
    assert result.metrics.interval_80_coverage == pytest.approx(coverage, rel=0.01)


def test_forecast_api(client, sample_process_payload: dict) -> None:
    payload = _forecast_payload(sample_process_payload)
    response = client.post("/api/forecast", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "forecast_operacional"
    assert body["tsa_dia"] > 0


def test_forecast_status_api(client, forecast_pointer: dict) -> None:
    response = client.get("/api/forecast/status")
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "forecast_operacional"
    assert body["family"] == forecast_pointer["family"]
    assert body["holdout_mae"] is not None


def test_forecast_requires_history(repo_root, sample_process_payload: dict) -> None:
    payload = _forecast_payload(sample_process_payload)
    payload["tsa_history"] = payload["tsa_history"][:3]
    with pytest.raises(ValueError, match="tsa_history"):
        run_forecast(payload, repo_root=repo_root)
