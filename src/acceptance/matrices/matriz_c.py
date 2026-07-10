from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline

from acceptance.l3.loader import L3CandidateBundle
from acceptance.scenarios.features import prepare_scenario_frame
from acceptance.scenarios.loader import ScenarioSpec, matriz_c_scenarios
from simulation.features.elo_specs import default_elo_specs
from simulation.features.matrix import build_matrix

LINEAR_FAMILIES = frozenset({"elasticnet", "ridge", "lasso"})
TREE_FAMILIES = frozenset(
    {"randomforest", "extratrees", "xgboost", "lightgbm", "catboost"}
)


def _elo3_model(pipe: Pipeline):
    return pipe.named_steps.get("model")


def _top3_from_pairs(pairs: list[tuple[str, float]], method: str) -> list[dict[str, Any]]:
    ranked = sorted(pairs, key=lambda p: abs(p[1]), reverse=True)[:3]
    return [
        {"feature": name, "delta_tsa": float(val), "method": method}
        for name, val in ranked
    ]


def top3_detractors(
    pipe: Pipeline,
    family: str,
    x_row: pd.DataFrame,
    feature_names: list[str],
    *,
    holdout: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    model = _elo3_model(pipe)
    if family in LINEAR_FAMILIES and hasattr(model, "coef_"):
        coef = np.asarray(model.coef_, dtype=float).ravel()
        x = x_row.to_numpy(dtype=float).ravel()
        pairs = list(zip(feature_names, coef * x, strict=False))
        return _top3_from_pairs(pairs, "coef")

    if family in TREE_FAMILIES:
        try:
            import shap

            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(x_row)
            if isinstance(sv, list):
                sv = sv[0]
            values = np.asarray(sv, dtype=float).ravel()
            pairs = list(zip(feature_names, values, strict=False))
            return _top3_from_pairs(pairs, "shap")
        except Exception:
            pass

    if holdout is not None and holdout.shape[0] >= 5:
        specs = default_elo_specs()
        X, y, _, _ = build_matrix(holdout, "elo3", specs, enforce_min_rows=False)
        if len(y) >= 5:
            result = permutation_importance(
                pipe,
                X,
                y,
                n_repeats=5,
                random_state=0,
                scoring="neg_mean_absolute_error",
            )
            pairs = list(
                zip(feature_names, result.importances_mean, strict=False)
            )
            return _top3_from_pairs(pairs, "permutation")

    return []


def _coverage_ok(
    top3: list[dict[str, Any]],
    required_any: list[str],
) -> bool:
    names = {d["feature"] for d in top3}
    return any(req in names for req in required_any)


@dataclass(frozen=True)
class MatrizCScenarioResult:
    id: str
    passed: bool
    detractors: list[dict[str, Any]]
    required_any: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "passed": self.passed,
            "required_any": self.required_any,
            "detractors": self.detractors,
        }


@dataclass(frozen=True)
class MatrizCResult:
    ok: bool
    scenarios: list[MatrizCScenarioResult]
    failures: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "failures": self.failures,
            "scenarios": {s.id: s.to_dict() for s in self.scenarios},
        }


def run_matriz_c(
    bundle: L3CandidateBundle,
    specs: dict[str, ScenarioSpec],
    *,
    required_in_top3: dict[str, list[str]],
    db_proxy_factor: float,
    holdout: pd.DataFrame | None = None,
) -> MatrizCResult:
    elo3_family = bundle.champions["elo3"]
    pipe = bundle.pipes["elo3"]
    feature_names = bundle.feature_cols.get("elo3", [])
    scenario_results: list[MatrizCScenarioResult] = []
    failures: list[str] = []

    for spec in matriz_c_scenarios(specs):
        frame = prepare_scenario_frame(
            spec.inputs, mode=spec.mode, db_proxy_factor=db_proxy_factor
        )
        elo_specs = default_elo_specs()
        cols = bundle.feature_cols.get("elo3", elo_specs["elo3"]["features"])
        x_row = frame.reindex(columns=cols)
        detractors = top3_detractors(
            pipe,
            elo3_family,
            x_row,
            feature_names,
            holdout=holdout,
        )
        required = required_in_top3.get(spec.id, spec.expect.get("required_any", []))
        passed = _coverage_ok(detractors, required) if required else len(detractors) == 3
        if not passed:
            failures.append(spec.id)
        scenario_results.append(
            MatrizCScenarioResult(
                id=spec.id,
                passed=passed,
                detractors=detractors,
                required_any=list(required),
            )
        )

    return MatrizCResult(
        ok=len(failures) == 0,
        scenarios=scenario_results,
        failures=failures,
    )
