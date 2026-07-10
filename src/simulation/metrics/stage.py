from __future__ import annotations

import numpy as np


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    diff = np.asarray(y_true) - np.asarray(y_pred)
    return float(np.sqrt(np.mean(diff**2)))


def wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    true = np.asarray(y_true)
    denom = np.sum(np.abs(true))
    if denom == 0:
        return 0.0
    return float(np.sum(np.abs(true - np.asarray(y_pred))) / denom)
