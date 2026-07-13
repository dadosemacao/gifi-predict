from __future__ import annotations

from pathlib import Path

import yaml

from serving.config import ServingSettings


def load_db_proxy_factor(repo_root: Path | None = None) -> float:
    root = repo_root or ServingSettings.from_yaml().repo_root
    ingest_cfg = root / "config" / "ingest.yaml"
    if ingest_cfg.exists():
        raw = yaml.safe_load(ingest_cfg.read_text(encoding="utf-8")) or {}
        return float(raw.get("db_proxy_factor", 0.985))
    serving = ServingSettings.from_yaml(root)
    return float(getattr(serving, "db_proxy_factor", 0.985))
