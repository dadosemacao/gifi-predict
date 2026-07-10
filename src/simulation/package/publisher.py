from __future__ import annotations

import json
import os
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

from simulation.package.atomic_io import atomic_write_json, file_lock


def load_pipeline(path: Path, models_root: Path) -> Pipeline:
    resolved = path.resolve()
    root = models_root.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"joblib path outside models_root: {resolved}")
    return joblib.load(resolved)


def _retry_joblib_dump(pipe: Pipeline, dest: Path, *, max_retries: int) -> None:
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            joblib.dump(pipe, dest)
            return
        except OSError as exc:
            last_exc = exc
            time.sleep(0.1 * (attempt + 1))
    assert last_exc is not None
    raise last_exc


def publish_candidate(
    models_root: Path,
    run_id: str,
    champion_pipes: dict[str, Pipeline],
    champions: dict[str, str],
    manifest_base: dict[str, Any],
    metrics: dict[str, Any],
    explainability: dict[str, Any],
    *,
    release_ok: bool,
    lock_timeout_s: float = 30.0,
    max_retries: int = 3,
) -> Path:
    candidates_root = models_root / "candidates"
    staging = candidates_root / f".staging_{run_id}"
    final = candidates_root / run_id
    lock_path = models_root / ".train.lock"

    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)

    artifact_paths: dict[str, Path] = {}
    try:
        for elo, family in champions.items():
            dest = staging / f"{elo}_{family}.joblib"
            _retry_joblib_dump(champion_pipes[elo], dest, max_retries=max_retries)
            artifact_paths[elo] = dest

        manifest_payload = dict(manifest_base)
        manifest_payload["release_ok"] = release_ok
        atomic_write_json(staging / "candidate_manifest.json", manifest_payload)
        atomic_write_json(staging / "metrics_holdout.json", metrics)
        atomic_write_json(staging / "explainability.json", explainability)

        with file_lock(lock_path, timeout_s=lock_timeout_s):
            if final.exists():
                raise FileExistsError(f"candidate run already exists: {run_id}")
            os.replace(staging, final)

            if release_ok:
                pointer_path = models_root / "current_candidate.json"
                if pointer_path.exists():
                    atomic_write_json(
                        models_root / "current_candidate.json.previous",
                        json.loads(pointer_path.read_text(encoding="utf-8")),
                    )
                pointer = {
                    "run_id": run_id,
                    "candidate_dir": str(final),
                    "updated_at": datetime.now(UTC).isoformat(),
                    "release_ok": release_ok,
                    "l2_dataset_version": manifest_base["l2"]["dataset_version"],
                    "champions": champions,
                    "artifacts": {
                        elo: str(final / f"{elo}_{family}.joblib")
                        for elo, family in champions.items()
                    },
                }
                atomic_write_json(pointer_path, pointer)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise

    return final


def load_current_candidate(models_root: Path) -> dict[str, Any]:
    pointer_path = models_root / "current_candidate.json"
    if not pointer_path.exists():
        raise FileNotFoundError(f"current_candidate.json not found under {models_root}")
    return json.loads(pointer_path.read_text(encoding="utf-8"))


def load_champion_pipes(
    models_root: Path,
    pointer: dict[str, Any] | None = None,
) -> tuple[dict[str, Pipeline], dict[str, list[str]], dict[str, Any]]:
    ptr = pointer or load_current_candidate(models_root)
    pipes: dict[str, Pipeline] = {}
    champions = ptr.get("champions", {})
    candidate_dir = Path(ptr.get("candidate_dir", models_root / "candidates" / ptr["run_id"]))
    manifest_path = candidate_dir / "candidate_manifest.json"
    feature_cols: dict[str, list[str]] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        feature_cols = manifest.get("feature_cols", {})
    for elo, _family in champions.items():
        rel = ptr["artifacts"][elo]
        path = Path(rel)
        if not path.is_absolute():
            path = candidate_dir / path.name
        pipes[elo] = load_pipeline(path, models_root)
    return pipes, feature_cols, ptr
