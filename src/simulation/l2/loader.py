from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import pandas as pd

T = TypeVar("T")


def retry_io(
    fn: Callable[[], T],
    *,
    max_retries: int = 3,
    base_delay_s: float = 0.1,
) -> T:
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except OSError as exc:
            last_exc = exc
            if attempt + 1 >= max_retries:
                break
            time.sleep(base_delay_s * (attempt + 1))
    assert last_exc is not None
    raise last_exc


@dataclass(frozen=True)
class L2Bundle:
    train: pd.DataFrame
    holdout: pd.DataFrame
    manifest: dict
    dataset_version: str
    schema_version: str
    source_hash: str
    paths: dict[str, Path]


def load_l2_bundle(l2_root: Path, *, max_retries: int = 3) -> L2Bundle:
    current_path = l2_root / "current.json"
    if not current_path.exists():
        raise FileNotFoundError(f"current.json not found under {l2_root}")

    def _load() -> L2Bundle:
        pointer = json.loads(current_path.read_text(encoding="utf-8"))
        manifest_path = Path(pointer["manifest"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        train = pd.read_parquet(pointer["paths"]["train_features"])
        holdout = pd.read_parquet(pointer["paths"]["holdout_features"])
        return L2Bundle(
            train=train,
            holdout=holdout,
            manifest=manifest,
            dataset_version=pointer["dataset_version"],
            schema_version=pointer["schema_version"],
            source_hash=manifest.get("source_hash", ""),
            paths={k: Path(v) for k, v in pointer["paths"].items()},
        )

    return retry_io(_load, max_retries=max_retries)
