from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from acceptance.matrices.matriz_c import top3_detractors


def test_top3_elasticnet_includes_tpc():
    cols = ["TPC", "Extrativo_AT", "Carga_Alcalina", "DB_LAB"]
    X = np.array([[30.0, 2.0, 19.0, 480.0]])
    y = np.array([1200.0])
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", ElasticNet(alpha=0.01, random_state=42, max_iter=5000)),
        ]
    )
    pipe.fit(X, y)
    row = pd.DataFrame(X, columns=cols)
    top = top3_detractors(pipe, "elasticnet", row, cols)
    assert len(top) == 3
    assert top[0]["method"] == "coef"
    features = {d["feature"] for d in top}
    assert "TPC" in features or "Extrativo_AT" in features
