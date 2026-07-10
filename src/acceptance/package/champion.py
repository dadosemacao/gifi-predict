from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from acceptance.package.atomic_io import atomic_write_json, file_lock


def _report_sha256(report: dict[str, Any]) -> str:
    payload = json.dumps(report, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def promote_champion(
    models_root: Path,
    run_id: str,
    report: dict[str, Any],
    *,
    lock_timeout_s: float = 30.0,
) -> Path:
    candidate_dir = models_root / "candidates" / run_id
    champion_dir = models_root / "champion" / run_id
    lock_path = models_root / ".champion.lock"

    if not candidate_dir.is_dir():
        raise FileNotFoundError(f"candidate not found: {run_id}")

    champions = report.get("l3_champions", {})
    with file_lock(lock_path, timeout_s=lock_timeout_s):
        if champion_dir.exists():
            raise FileExistsError(f"champion run already exists: {run_id}")
        champion_dir.mkdir(parents=True, exist_ok=True)

        for elo, family in champions.items():
            src = candidate_dir / f"{elo}_{family}.joblib"
            dst = champion_dir / f"{elo}_{family}.joblib"
            shutil.copy2(src, dst)

        manifest = {
            "run_id": run_id,
            "promoted_at": datetime.now(UTC).isoformat(),
            "champions": champions,
            "acceptance_report_sha256": _report_sha256(report),
            "l2_dataset_version": report.get("l2_dataset_version"),
            "l3_candidate_dir": str(candidate_dir),
        }
        atomic_write_json(champion_dir / "champion_manifest.json", manifest)
        atomic_write_json(champion_dir / "acceptance_report.json", report)

        pointer_path = models_root / "current_champion.json"
        if pointer_path.exists():
            atomic_write_json(
                models_root / "current_champion.json.previous",
                json.loads(pointer_path.read_text(encoding="utf-8")),
            )
        pointer = {
            "run_id": run_id,
            "champion_dir": str(champion_dir),
            "updated_at": datetime.now(UTC).isoformat(),
            "release_ok": True,
            "l2_dataset_version": report.get("l2_dataset_version"),
            "champions": champions,
            "artifacts": {
                elo: str(champion_dir / f"{elo}_{family}.joblib")
                for elo, family in champions.items()
            },
        }
        atomic_write_json(pointer_path, pointer)

    return champion_dir
