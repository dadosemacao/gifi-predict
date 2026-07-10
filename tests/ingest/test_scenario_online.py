from __future__ import annotations

from ingest.online.infer_publish import publish_infer_features
from ingest.online.validator import validate_scenario_file


def test_scenario_mode_a_rejected(settings, fixtures_dir) -> None:
    result = validate_scenario_file(
        fixtures_dir / "scenario_mode_a_bad.csv", "C-AT09", settings
    )
    assert result["ok"] is False
    assert result["signal"] == "INGEST_SCENARIO_REJECT"


def test_scenario_mode_b_accepted_and_publish(settings, fixtures_dir) -> None:
    path = fixtures_dir / "scenario_mode_b_ok.csv"
    result = validate_scenario_file(path, "C-AT10", settings)
    assert result["ok"] is True
    out = publish_infer_features(path, "C-AT10", settings)
    assert out.exists()
