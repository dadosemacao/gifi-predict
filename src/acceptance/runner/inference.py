from __future__ import annotations

from sklearn.pipeline import Pipeline

from acceptance.scenarios.features import prepare_scenario_frame
from simulation.cascade.inference import infer_dataframe


def predict_tsa(
    inputs: dict,
    *,
    mode: str,
    pipes: dict[str, Pipeline],
    feature_cols: dict[str, list[str]],
    db_proxy_factor: float,
) -> float:
    frame = prepare_scenario_frame(
        inputs, mode=mode, db_proxy_factor=db_proxy_factor
    )
    preds = infer_dataframe(
        frame,
        mode,
        pipes,
        feature_cols,
        db_proxy_factor=db_proxy_factor,
    )
    return float(preds.iloc[0]["TSA_dia"])


def predict_tsa_sequence(
    anchor_inputs: dict,
    *,
    mode: str,
    variable: str,
    sequence: list[float],
    pipes: dict[str, Pipeline],
    feature_cols: dict[str, list[str]],
    db_proxy_factor: float,
) -> list[float]:
    values: list[float] = []
    for val in sequence:
        row = dict(anchor_inputs)
        row[variable] = val
        values.append(
            predict_tsa(
                row,
                mode=mode,
                pipes=pipes,
                feature_cols=feature_cols,
                db_proxy_factor=db_proxy_factor,
            )
        )
    return values
