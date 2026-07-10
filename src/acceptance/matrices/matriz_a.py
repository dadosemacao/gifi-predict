from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from acceptance.l3.loader import L3CandidateBundle
from simulation.cascade.evaluator import evaluate_holdout
from simulation.features.elo_specs import default_elo_specs
from simulation.l2.loader import L2Bundle


@dataclass(frozen=True)
class MatrizAResult:
    ok: bool
    mae_tsa_cascade: float
    limit: float
    mae_extrativos: float
    mae_carga: float
    mae_tsa_isolated: float
    source: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mae_tsa_cascade": self.mae_tsa_cascade,
            "limit": self.limit,
            "mae_extrativos": self.mae_extrativos,
            "mae_carga": self.mae_carga,
            "mae_tsa_isolated": self.mae_tsa_isolated,
            "source": self.source,
            "details": self.details,
        }


def run_matriz_a(
    bundle: L3CandidateBundle,
    l2: L2Bundle,
    *,
    mae_limit: float,
    recompute: bool,
    db_proxy_factor: float,
) -> MatrizAResult:
    specs = default_elo_specs()
    if recompute:
        fitted = {
            elo: {bundle.champions[elo]: bundle.pipes[elo]}
            for elo in bundle.champions
        }
        metrics = evaluate_holdout(
            fitted,
            bundle.champions,
            l2.holdout,
            specs,
            bundle.feature_cols,
            db_proxy_factor=db_proxy_factor,
        )
        source = "recomputed"
    else:
        metrics = bundle.metrics
        source = "l3_metrics"
        required = ("mae_tsa_cascade", "mae_extrativos", "mae_carga")
        missing = [k for k in required if k not in metrics]
        if missing:
            raise ValueError(f"metrics_holdout.json missing keys: {missing}")

    mae_cascade = float(metrics["mae_tsa_cascade"])
    return MatrizAResult(
        ok=mae_cascade <= mae_limit,
        mae_tsa_cascade=mae_cascade,
        limit=mae_limit,
        mae_extrativos=float(metrics.get("mae_extrativos", metrics.get("elo1", {}).get("mae", 0))),
        mae_carga=float(metrics.get("mae_carga", metrics.get("elo2", {}).get("mae", 0))),
        mae_tsa_isolated=float(
            metrics.get("mae_tsa_isolated", metrics.get("elo3", {}).get("mae", 0))
        ),
        source=source,
        details=metrics,
    )
