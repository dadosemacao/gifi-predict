from __future__ import annotations

import pandas as pd

from ingest.config import IngestSettings
from ingest.contracts.loader import ContractLoader
from ingest.observability.signals import Severity, SignalCollector
from ingest.validation.domain_rules import validate_db_units
from ingest.validation.scenario import ScenarioValidator


def test_scenario_mode_a_rejects_carga(settings: IngestSettings, repo_root, fixtures_dir) -> None:
    loader = ContractLoader(repo_root)
    template = loader.scenario_template()
    df = pd.read_csv(fixtures_dir / "scenario_mode_a_bad.csv")
    errors = ScenarioValidator(template, settings).validate_dataframe(df)
    assert any("Modo A" in e for e in errors)


def test_unit_fail_g_per_cm3() -> None:
    df = pd.DataFrame({"DB_SGF": [1.2]})
    signals = SignalCollector()
    validate_db_units(df, signals)
    assert signals.signals[0].code == "INGEST_UNIT_FAIL"
    assert signals.signals[0].severity == Severity.BLOCKING
