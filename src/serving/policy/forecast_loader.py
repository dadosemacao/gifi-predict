from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from serving.policy.holdout_metrics import HoldoutMetrics, load_json_pointer, resolve_holdout_metrics
from simulation.forecast.predictor import ForecastArtifact, load_forecast_artifact
from simulation.forecast.specs import DEFAULT_ANCHOR

FORECAST_REPORT = Path("reports/TSA_FORECAST_OPERACIONAL.json")


@dataclass(frozen=True)
class ForecastContext:
    run_id: str
    family: str
    anchor: str
    artifact_path: Path
    holdout_mae: float
    holdout_r2: float
    interval_coverage: float
    metrics: HoldoutMetrics


def _resolve(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def load_forecast_context(
    repo_root: Path,
    *,
    models_root: Path | None = None,
    run_id: str | None = None,
) -> tuple[ForecastArtifact, ForecastContext]:
    root = (repo_root / (models_root or Path("models/primeira_base"))).resolve()
    pointer = load_json_pointer(root / "current_forecast.json")
    effective_run_id = run_id or pointer.get("run_id")
    if not effective_run_id:
        raise FileNotFoundError(
            f"current_forecast.json não encontrado em {root}; informe run_id"
        )

    if run_id:
        model_dir = root / f"forecast_{run_id}"
        artifact_path = _pick_artifact(model_dir)
        family = artifact_path.stem.replace("forecast_", "")
        anchor = pointer.get("anchor", DEFAULT_ANCHOR) if pointer.get("run_id") == run_id else DEFAULT_ANCHOR
    elif pointer.get("artifact_path"):
        artifact_path = _resolve(repo_root, str(pointer["artifact_path"]))
        family = str(pointer.get("family", artifact_path.stem.replace("forecast_", "")))
        anchor = str(pointer.get("anchor", DEFAULT_ANCHOR))
    else:
        model_dir = root / f"forecast_{effective_run_id}"
        artifact_path = _pick_artifact(model_dir)
        family = artifact_path.stem.replace("forecast_", "")
        anchor = DEFAULT_ANCHOR

    if not artifact_path.exists():
        raise FileNotFoundError(f"artefato de forecast não encontrado: {artifact_path}")

    holdout = resolve_holdout_metrics(
        repo_root,
        run_id=str(effective_run_id),
        pointer=pointer,
        report_path=FORECAST_REPORT,
    )
    artifact = load_forecast_artifact(artifact_path)
    ctx = ForecastContext(
        run_id=str(effective_run_id),
        family=family,
        anchor=anchor,
        artifact_path=artifact_path,
        holdout_mae=holdout.mae_holdout,
        holdout_r2=holdout.r2_holdout,
        interval_coverage=holdout.interval_80_coverage,
        metrics=holdout,
    )
    enriched = ForecastArtifact(
        pipe=artifact.pipe,
        anchor=artifact.anchor,
        feature_columns=artifact.feature_columns,
        interval_quantiles=artifact.interval_quantiles,
        family=ctx.family,
        run_id=ctx.run_id,
    )
    return enriched, ctx


def _pick_artifact(model_dir: Path) -> Path:
    if not model_dir.is_dir():
        raise FileNotFoundError(f"diretório de forecast não encontrado: {model_dir}")
    matches = sorted(model_dir.glob("forecast_*.joblib"))
    if not matches:
        raise FileNotFoundError(f"nenhum forecast_*.joblib em {model_dir}")
    return matches[0]
