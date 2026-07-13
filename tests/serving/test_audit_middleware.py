from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from serving.app import create_app
from serving.config import ServingSettings


def _fetch_last(db_path: Path) -> dict | None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM api_calls ORDER BY ts_utc DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _forecast_payload(sample_process_payload: dict) -> dict:
    history = [3289.0] * 7
    return {"tsa_history": history, **sample_process_payload}


def _predict_payload(sample_process_payload: dict, *, drop_extrativo_at: bool = False) -> dict:
    payload = dict(sample_process_payload)
    if drop_extrativo_at:
        payload.pop("extrativo_at", None)
    return payload


def test_audit_forecast_persists_row(
    serving_settings: ServingSettings,
    audit_db: Path,
    sample_process_payload: dict,
) -> None:
    with TestClient(create_app(serving_settings)) as client:
        payload = _forecast_payload(sample_process_payload)
        response = client.post("/api/forecast", json=payload)
        assert response.status_code == 200

    row = _fetch_last(audit_db)
    assert row is not None
    assert row["endpoint"] == "forecast"
    assert row["status_code"] == 200
    assert row["product"] == "forecast_operacional"
    assert row["model_id"]
    assert row["metrics_json"]
    assert row["duration_ms"] >= 0


def test_audit_predict_tsa_estimated_origins(
    serving_settings: ServingSettings,
    audit_db: Path,
    sample_process_payload: dict,
) -> None:
    with TestClient(create_app(serving_settings)) as client:
        payload = _predict_payload(sample_process_payload, drop_extrativo_at=True)
        response = client.post("/api/predict-tsa", json=payload)
        assert response.status_code == 200

    row = _fetch_last(audit_db)
    assert row is not None
    assert row["endpoint"] == "predict_tsa"
    origins = json.loads(row["field_origins_json"])
    assert origins["extrativo_at"] == "estimado"


def test_audit_validation_error_422(
    serving_settings: ServingSettings,
    audit_db: Path,
) -> None:
    with TestClient(create_app(serving_settings)) as client:
        response = client.post("/api/forecast", json={"carga_alcalina": 1.0})
        assert response.status_code == 422

    row = _fetch_last(audit_db)
    assert row is not None
    assert row["endpoint"] == "forecast"
    assert row["status_code"] == 422
    assert row["error_detail"]


def test_audit_simulate_multipart_hash(
    repo_root: Path,
    serving_settings: ServingSettings,
    audit_db: Path,
    fixtures_dir: Path,
) -> None:
    path = fixtures_dir / "scenario_mode_b_ok.csv"
    file_bytes = path.read_bytes()
    expected_hash = hashlib.sha256(file_bytes).hexdigest()

    with TestClient(create_app(serving_settings)) as client:
        with path.open("rb") as fh:
            response = client.post(
                "/api/simulate",
                files={"file": ("scenario_mode_b_ok.csv", fh, "text/csv")},
                data={"mode": "B", "demo": "true"},
            )
        assert response.status_code == 200

    row = _fetch_last(audit_db)
    assert row is not None
    assert row["endpoint"] == "simulate"
    assert row["file_sha256"] == expected_hash
    assert row["file_name"] == "scenario_mode_b_ok.csv"
    req = json.loads(row["request_json"])
    assert req["mode"] == "B"


def test_audit_status_get(
    serving_settings: ServingSettings,
    audit_db: Path,
) -> None:
    with TestClient(create_app(serving_settings)) as client:
        response = client.get("/api/forecast/status")
        assert response.status_code == 200

    row = _fetch_last(audit_db)
    assert row is not None
    assert row["endpoint"] == "forecast_status"
    assert row["status_code"] == 200


def test_audit_query_cli_last_n(
    repo_root: Path,
    serving_settings: ServingSettings,
    audit_db: Path,
) -> None:
    with TestClient(create_app(serving_settings)) as client:
        client.get("/api/release-status")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    proc = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "audit_query.py"),
            "--db",
            str(audit_db),
            "--last",
            "1",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(repo_root),
        env=env,
    )
    lines = [line for line in proc.stdout.strip().splitlines() if line]
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["endpoint"] == "release_status"


def test_audit_sequential_inserts_no_loss(
    repo_root: Path,
    serving_settings: ServingSettings,
    audit_db: Path,
) -> None:
    with TestClient(create_app(serving_settings)) as client:
        for _ in range(20):
            client.get("/api/forecast/status")

    conn = sqlite3.connect(audit_db)
    count = conn.execute("SELECT COUNT(*) FROM api_calls").fetchone()[0]
    conn.close()
    assert count == 20
