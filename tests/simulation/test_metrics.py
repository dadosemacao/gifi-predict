from __future__ import annotations

import numpy as np
import pytest

from simulation.metrics.stage import mae, rmse, wape


def test_mae_rmse_wape():
    y = np.array([10.0, 20.0, 30.0])
    pred = np.array([12.0, 18.0, 33.0])
    assert mae(y, pred) == pytest.approx(7 / 3)
    assert rmse(y, pred) == pytest.approx(np.sqrt((4 + 4 + 9) / 3))
    assert wape(y, pred) == pytest.approx(7 / 60)
