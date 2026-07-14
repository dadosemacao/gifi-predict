"""Testes do empacotador de release serving.

Autor: Emerson Antônio
Data: 2026-07-14
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml


def _load_pack_module():
    root = Path(__file__).resolve().parents[2]
    path = root / "scripts" / "pack_serving_release.py"
    spec = importlib.util.spec_from_file_location("pack_serving_release", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


pack_mod = _load_pack_module()
pack = pack_mod.pack


def _write(path: Path, content: str | bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)


@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    run_id = "run-test-001"
    (root / "docs" / "kb").mkdir(parents=True)
    _write(root / "docs" / "kb" / "_index.yaml", "version: 1\n")

    manifest = {
        "must_paths": [
            "models/candidates/{run_id}",
            "reports/acceptance/{run_id}/acceptance_report.json",
            "models/primeira_base/current_forecast.json",
            "models/primeira_base/current_tsa.json",
            "models/ingest/extrativo_serving_imputer.joblib",
            "models/ingest/current_extr_imputer.json",
            "reports/TSA_FORECAST_OPERACIONAL.json",
            "reports/TSA_PRIMEIRA_BASE_MODELING.json",
        ],
        "optional_paths": ["models/candidates/current_champion.json"],
        "pointer_rules": [
            {
                "pointer": "models/primeira_base/current_forecast.json",
                "artifact_key": "artifact_path",
            },
            {
                "pointer": "models/primeira_base/current_tsa.json",
                "artifact_key": "artifact_path",
            },
            {
                "pointer": "models/ingest/current_extr_imputer.json",
                "artifact_key": "artifact_path",
            },
        ],
    }
    _write(
        root / "config" / "serving_release_manifest.yaml",
        yaml.safe_dump(manifest, allow_unicode=True),
    )

    _write(root / f"models/candidates/{run_id}/elo1_randomforest.joblib")
    _write(
        root / f"reports/acceptance/{run_id}/acceptance_report.json",
        json.dumps({"release_ok": True}),
    )
    _write(
        root / "models/primeira_base/current_forecast.json",
        json.dumps(
            {
                "run_id": "fc1",
                "artifact_path": "models/primeira_base/forecast_fc1/forecast_x.joblib",
            }
        ),
    )
    _write(root / "models/primeira_base/forecast_fc1/forecast_x.joblib")
    _write(
        root / "models/primeira_base/current_tsa.json",
        json.dumps(
            {
                "run_id": "tsa1",
                "artifact_path": "models/primeira_base/tsa1/tsa_lasso.joblib",
            }
        ),
    )
    _write(root / "models/primeira_base/tsa1/tsa_lasso.joblib")
    _write(root / "models/ingest/extrativo_serving_imputer.joblib")
    _write(
        root / "models/ingest/current_extr_imputer.json",
        json.dumps(
            {"artifact_path": "models/ingest/extrativo_serving_imputer.joblib"}
        ),
    )
    _write(root / "reports/TSA_FORECAST_OPERACIONAL.json", "{}")
    _write(root / "reports/TSA_PRIMEIRA_BASE_MODELING.json", "{}")
    return root


def test_pack_happy_path(mini_repo: Path) -> None:
    manifest = mini_repo / "config" / "serving_release_manifest.yaml"
    dest = pack(mini_repo, "run-test-001", manifest)
    assert dest.exists()
    assert (dest / "MANIFEST.json").exists()
    assert (
        dest / "reports/acceptance/run-test-001/acceptance_report.json"
    ).exists()
    assert (
        dest / "models/primeira_base/forecast_fc1/forecast_x.joblib"
    ).exists()
    payload = json.loads((dest / "MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-test-001"
    assert "models/candidates/run-test-001" in payload["paths"]


def test_pack_missing_path_exits_2(mini_repo: Path) -> None:
    shutil.rmtree(mini_repo / "reports/acceptance/run-test-001")
    manifest = mini_repo / "config" / "serving_release_manifest.yaml"
    with pytest.raises(SystemExit) as exc:
        pack(mini_repo, "run-test-001", manifest)
    assert exc.value.code == 2
