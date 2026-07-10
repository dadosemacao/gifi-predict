from __future__ import annotations

import pytest
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline

from simulation.cascade.inference import infer_cascade_row
from simulation.exceptions import ScenarioRejectError


def _dummy_pipes() -> dict[str, Pipeline]:
    cols1 = ["pct_A", "Idade"]
    cols2 = ["Extrativo_AT", "TPC", "DB_SGF"]
    cols3 = ["Extrativo_AT", "Carga_Alcalina", "TPC"]
    pipes = {
        "elo1": Pipeline([("model", DummyRegressor(strategy="constant", constant=9.0))]),
        "elo2": Pipeline([("model", DummyRegressor(strategy="constant", constant=80.0))]),
        "elo3": Pipeline([("model", DummyRegressor(strategy="constant", constant=1200.0))]),
    }
    import numpy as np

    pipes["elo1"].fit(np.zeros((1, len(cols1))), [9.0])
    pipes["elo2"].fit(np.zeros((1, len(cols2))), [80.0])
    pipes["elo3"].fit(np.zeros((1, len(cols3))), [1200.0])
    return pipes


def _feature_cols() -> dict[str, list[str]]:
    return {
        "elo1": ["pct_A", "Idade"],
        "elo2": ["Extrativo_AT", "TPC", "DB_SGF"],
        "elo3": ["Extrativo_AT", "Carga_Alcalina", "TPC"],
    }


def test_mode_a_cascade():
    row = {"pct_A": 0.2, "Idade": 3, "TPC": 1.0, "DB_SGF": 1.2}
    out = infer_cascade_row(row, "A", _dummy_pipes(), _feature_cols())
    assert out["Extrativo_AT"] == 9.0
    assert out["Carga_Alcalina"] == 80.0
    assert out["TSA_dia"] == 1200.0


def test_mode_b_injection():
    row = {
        "pct_A": 0.2,
        "Idade": 3,
        "TPC": 1.0,
        "DB_SGF": 1.2,
        "Extrativo_AT": 7.5,
        "Carga_Alcalina": 75.0,
    }
    out = infer_cascade_row(row, "B", _dummy_pipes(), _feature_cols())
    assert out["Extrativo_AT"] == 7.5
    assert out["Carga_Alcalina"] == 75.0


def test_mode_a_rejects_injection():
    row = {"Carga_Alcalina": 75.0, "TPC": 1.0}
    with pytest.raises(ScenarioRejectError, match="INGEST_SCENARIO_REJECT"):
        infer_cascade_row(row, "A", _dummy_pipes(), _feature_cols())
