from __future__ import annotations

import numpy as np
import pytest

from simulation.models.families import make_family
from simulation.package.manifest import extract_explainability


@pytest.fixture
def tiny_xy():
    rng = np.random.default_rng(42)
    x = rng.normal(size=(30, 4))
    y = x @ np.array([0.5, -0.2, 0.1, 0.0]) + rng.normal(scale=0.05, size=30)
    cols = ["feat_a", "feat_b", "feat_c", "feat_d"]
    return x, y, cols


@pytest.mark.parametrize(
    "family",
    ["elasticnet", "ridge", "lasso", "randomforest", "extratrees", "xgboost", "lightgbm", "catboost"],
)
def test_explainability_exports_contributions(family, tiny_xy):
    x, y, cols = tiny_xy
    pipe = make_family(family, random_state=42)
    pipe.fit(x, y)

    fitted = {"elo3": {family: pipe}}
    champions = {"elo3": family}
    feature_cols = {"elo3": cols}
    out = extract_explainability(fitted, champions, feature_cols)

    entry = out["elo3"]
    assert entry["family"] == family
    assert entry["elo"] == "elo3"
    linear_families = {"elasticnet", "ridge", "lasso"}
    if family in linear_families:
        assert "coefficients" in entry
        assert set(entry["coefficients"]) == set(cols)
    else:
        assert "feature_importances" in entry
        assert set(entry["feature_importances"]) == set(cols)
        assert all(val >= 0 for val in entry["feature_importances"].values())


def test_explainability_baseline_has_no_contributions(tiny_xy):
    x, y, cols = tiny_xy
    pipe = make_family("baseline", random_state=42)
    pipe.fit(x, y)

    out = extract_explainability(
        {"elo1": {"baseline": pipe}},
        {"elo1": "baseline"},
        {"elo1": cols},
    )
    entry = out["elo1"]
    assert "coefficients" not in entry
    assert "feature_importances" not in entry
