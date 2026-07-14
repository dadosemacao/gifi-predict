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
    assert "sensitivity" not in body
    assert "detractors" not in body


def test_predict_tsa_status_api(client, tsa_pointer: dict) -> None:
    response = client.get("/api/predict-tsa/status")
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "what_if_direct"
    assert body["family"] == tsa_pointer["family"]
    assert len(body["features"]) == 13


def test_predict_tsa_analytics_happy_path(client, sample_process_payload: dict) -> None:
    response = client.post(
        "/api/predict-tsa",
        params={"include_analytics": True},
        json=sample_process_payload,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["sensitivity"]) == 15
    assert body["sensitivity"][0]["value"] == pytest.approx(465.0)
    assert body["sensitivity"][-1]["value"] == pytest.approx(515.0)
    assert len(body["detractors"]) == 3
    assert all(d["method"] == "local_ablation" for d in body["detractors"])
    assert body["sensitivity_variable"] == "db_sgf"
    assert body["sensitivity_steps"] == 15
    assert "Matriz C" in body["disclaimer"]


def test_predict_tsa_analytics_custom_variable(client, sample_process_payload: dict) -> None:
    response = client.post(
        "/api/predict-tsa",
        params={
            "include_analytics": True,
            "sensitivity_variable": "carga_alcalina",
            "sensitivity_steps": 11,
        },
        json=sample_process_payload,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["sensitivity"]) == 11
    assert body["sensitivity"][0]["value"] == pytest.approx(17.5)
    assert body["sensitivity"][-1]["value"] == pytest.approx(21.0)


@pytest.mark.parametrize("steps", [4, 32])
def test_predict_tsa_analytics_bad_steps(
    client, sample_process_payload: dict, steps: int
) -> None:
    response = client.post(
        "/api/predict-tsa",
        params={"include_analytics": True, "sensitivity_steps": steps},
        json=sample_process_payload,
    )
    assert response.status_code == 422


def test_predict_tsa_analytics_bad_variable(client, sample_process_payload: dict) -> None:
    response = client.post(
        "/api/predict-tsa",
        params={"include_analytics": True, "sensitivity_variable": "foo"},
        json=sample_process_payload,
    )
    assert response.status_code == 422


def test_predict_tsa_analytics_deterministic(client, sample_process_payload: dict) -> None:
    params = {"include_analytics": True, "sensitivity_steps": 9}
    a = client.post("/api/predict-tsa", params=params, json=sample_process_payload).json()
    b = client.post("/api/predict-tsa", params=params, json=sample_process_payload).json()
    assert a["tsa_dia"] == pytest.approx(b["tsa_dia"], abs=1e-6)
    assert a["sensitivity"] == b["sensitivity"]
    assert a["detractors"] == b["detractors"]
