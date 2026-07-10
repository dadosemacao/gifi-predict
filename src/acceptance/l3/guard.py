from __future__ import annotations

import hashlib
from pathlib import Path

from acceptance.exceptions import IntegrityError
from acceptance.l3.loader import L3CandidateBundle
from simulation.l2.guard import guard_holdout_eligible


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def guard_l3_integrity(bundle: L3CandidateBundle) -> None:
    champions = bundle.champions
    artifacts = bundle.manifest.get("artifacts", {})
    for elo, family in champions.items():
        key = f"{elo}_{family}"
        artifact_meta = artifacts.get(key, {})
        expected = artifact_meta.get("sha256")
        joblib_path = bundle.candidate_dir / f"{elo}_{family}.joblib"
        if not joblib_path.exists():
            raise IntegrityError(f"missing joblib: {joblib_path}")
        actual = _file_sha256(joblib_path)
        if expected and actual != expected:
            raise IntegrityError(
                f"hash mismatch for {key}: expected={expected} actual={actual}"
            )


def guard_l2_for_acceptance(l2_manifest: dict) -> None:
    guard_holdout_eligible(l2_manifest)
