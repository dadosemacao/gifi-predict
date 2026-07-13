from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_prod_blocked_when_not_released(client: TestClient) -> None:
    from pathlib import Path

    from serving.policy.release import ReleaseContext

    fake = ReleaseContext(
        run_id="2026-07-10T10:54:42.849161Z",
        release_ok=False,
        demo_mode=True,
        l2_dataset_version="2026-07-10T07:35:10Z",
        mae_tsa_holdout=96.7,
        champions={"elo3": "catboost"},
        report_path=Path("reports/acceptance/fake/acceptance_report.json"),
    )
    with patch("serving.routes.scenario.load_release_context", return_value=fake):
        response = client.post(
            "/api/simulate",
            files={"file": ("x.csv", b"cenario_id,linha\n", "text/csv")},
            data={"mode": "A", "demo": "false"},
        )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "production_bind_blocked"


def test_release_status(client: TestClient, default_run_id: str) -> None:
    response = client.get("/api/release-status")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == default_run_id
    assert "demo_mode" in body
    assert "mae_tsa_holdout" in body


def test_template_download(client: TestClient) -> None:
    response = client.get("/api/template")
    assert response.status_code == 200
    assert "cenario_id" in response.text
    assert response.headers["content-type"].startswith("text/csv")
