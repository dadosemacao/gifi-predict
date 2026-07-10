from __future__ import annotations

import pandas as pd
import pytest

from simulation.exceptions import TrainingDataError
from simulation.features.elo_specs import default_elo_specs
from simulation.features.matrix import build_matrix


def test_matrix_drops_na_target():
    specs = default_elo_specs()
    df = pd.DataFrame(
        {
            "Extrativo_AT": [1.0, None],
            "pct_A": [0.2, 0.2],
            "pct_B": [0.2, 0.2],
            "pct_C": [0.2, 0.2],
            "pct_D": [0.2, 0.2],
            "pct_MG": [0.2, 0.2],
            "pct_ABC": [0.6, 0.6],
            "pct_CDMG": [0.6, 0.6],
            "mix_entropy": [1.5, 1.5],
            "mix_hhi": [0.3, 0.3],
            "dom_A": [0.2, 0.2],
            "dom_B": [0.2, 0.2],
            "dom_C": [0.2, 0.2],
            "dom_D": [0.2, 0.2],
            "dom_MG": [0.2, 0.2],
            "Idade": [3, 3],
        }
    )
    X, y, excl, _ = build_matrix(df, "elo1", specs, min_rows=1, enforce_min_rows=True)
    assert len(X) == 1
    assert excl["na_target"] == 1


def test_matrix_min_rows_enforced():
    specs = default_elo_specs()
    df = pd.DataFrame(
        {
            "Extrativo_AT": [1.0] * 10,
            "pct_A": [0.2] * 10,
            "pct_B": [0.2] * 10,
            "pct_C": [0.2] * 10,
            "pct_D": [0.2] * 10,
            "pct_MG": [0.2] * 10,
            "pct_ABC": [0.6] * 10,
            "pct_CDMG": [0.6] * 10,
            "mix_entropy": [1.5] * 10,
            "mix_hhi": [0.3] * 10,
            "dom_A": [0.2] * 10,
            "dom_B": [0.2] * 10,
            "dom_C": [0.2] * 10,
            "dom_D": [0.2] * 10,
            "dom_MG": [0.2] * 10,
            "Idade": [3] * 10,
        }
    )
    with pytest.raises(TrainingDataError):
        build_matrix(df, "elo1", specs, min_rows=50, enforce_min_rows=True)
