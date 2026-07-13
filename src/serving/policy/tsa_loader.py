from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from serving.policy.holdout_metrics import HoldoutMetrics, load_json_pointer, resolve_holdout_metrics
from simulation.tsa_direct.specs import PROCESS_FEATURES

TSA_DIRECT_REPORT = Path("reports/TSA_PRIMEIRA_BASE_MODELING.json")


@dataclass(frozen=True)
class TsaDirectContext:
    run_id: str
    family: str
    artifact_path: Path
    holdout_mae: float
    holdout_r2: float
    features: list[str]
    metrics: HoldoutMetrics


def _resolve(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def load_tsa_direct_context(
    repo_root: Path,
    *,
    models_root: Path | None = None,
    run_id: str | None = None,
) -> tuple[Pipeline, TsaDirectContext]:
    root = (repo_root / (models_root or Path("models/primeira_base"))).resolve()
    pointer = load_json_pointer(root / "current_tsa.json")
    effective_run_id = run_id or pointer.get("run_id")
    if not effective_run_id:
        raise FileNotFoundError(
            f"current_tsa.json não encontrado em {root}; informe run_id"
        )

    if run_id:
        model_dir = root / run_id
        artifact_path = _pick_artifact(model_dir)
        family = artifact_path.stem.replace("tsa_", "")
    elif pointer.get("artifact_path"):
        artifact_path = _resolve(repo_root, str(pointer["artifact_path"]))
        family = str(pointer.get("family", artifact_path.stem.replace("tsa_", "")))
    else:
        model_dir = root / effective_run_id
        artifact_path = _pick_artifact(model_dir)
        family = artifact_path.stem.replace("tsa_", "")

    if not artifact_path.exists():
        raise FileNotFoundError(f"artefato what-if direto não encontrado: {artifact_path}")

    holdout = resolve_holdout_metrics(
        repo_root,
        run_id=str(effective_run_id),
        pointer=pointer,
        report_path=TSA_DIRECT_REPORT,
        default_interval=0.0,
    )
    pipe = joblib.load(artifact_path)
    if not isinstance(pipe, Pipeline):
        raise ValueError(f"artefato inválido (esperado Pipeline): {artifact_path}")

    features = list(pointer.get("features", PROCESS_FEATURES)) if pointer else PROCESS_FEATURES
    ctx = TsaDirectContext(
        run_id=str(effective_run_id),
        family=family,
        artifact_path=artifact_path,
        holdout_mae=holdout.mae_holdout,
        holdout_r2=holdout.r2_holdout,
        features=features,
        metrics=holdout,
    )
    return pipe, ctx


def _pick_artifact(model_dir: Path) -> Path:
    if not model_dir.is_dir():
        raise FileNotFoundError(f"diretório de modelo TSA não encontrado: {model_dir}")
    matches = sorted(model_dir.glob("tsa_*.joblib"))
    if not matches:
        raise FileNotFoundError(f"nenhum tsa_*.joblib em {model_dir}")
    return matches[0]
