from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_validate_mode_a_rejects_injection(
    client: TestClient, fixtures_dir: Path
) -> None:
    path = fixtures_dir / "scenario_mode_a_bad.csv"
    with path.open("rb") as fh:
        response = client.post(
            "/api/scenario/validate",
            files={"file": ("scenario_mode_a_bad.csv", fh, "text/csv")},
            data={"mode": "A"},
        )
    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_validate_mix_invalid(client: TestClient, tmp_path: Path) -> None:
    bad = tmp_path / "bad_mix.csv"
    bad.write_text(
        "cenario_id,linha,modo,Idade,TPC,Volume,DB_SGF,Kappa,"
        "pct_A,pct_B,pct_C,pct_D,pct_MG\n"
        "X,1,A,8,60,1000,480,17,0.5,0.2,0.2,0.2,0.2\n",
        encoding="utf-8",
    )
    with bad.open("rb") as fh:
        response = client.post(
            "/api/scenario/validate",
            files={"file": ("bad_mix.csv", fh, "text/csv")},
            data={"mode": "A"},
        )
    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_validate_mode_b_ok(client: TestClient, fixtures_dir: Path) -> None:
    path = fixtures_dir / "scenario_mode_b_ok.csv"
    with path.open("rb") as fh:
        response = client.post(
            "/api/scenario/validate",
            files={"file": ("scenario_mode_b_ok.csv", fh, "text/csv")},
            data={"mode": "B"},
        )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_unsupported_file(client: TestClient, tmp_path: Path) -> None:
    bad = tmp_path / "notes.txt"
    bad.write_text("not a spreadsheet", encoding="utf-8")
    with bad.open("rb") as fh:
        response = client.post(
            "/api/scenario/validate",
            files={"file": ("notes.txt", fh, "text/plain")},
            data={"mode": "A"},
        )
    assert response.status_code == 415
