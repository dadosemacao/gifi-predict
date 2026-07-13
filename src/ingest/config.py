from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "docs" / "kb" / "_index.yaml").exists():
            return candidate
    return current


class IngestSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GIFI_", extra="ignore")

    repo_root: Path = Field(default_factory=_find_repo_root)
    l2_root: Path = Path("data/l2")
    logs_root: Path = Path("logs/ingest")
    schema_version: str = "1.0.0"
    holdout_start: str = "2025-05-01"
    holdout_end: str = "2025-10-30"
    train_cutoff: str = "2025-04-30"
    online_max_rows: int = 500
    online_sla_p95_ms: int = 3000
    db_proxy_factor: float = 0.985
    tsa_train_min: float = 1000.0
    mix_tolerance: float = 0.02
    extr_impute_enabled: bool = True
    extr_impute_min_train_rows: int = 200
    extr_impute_random_state: int = 42
    extr_range_min: float = 1.0
    extr_range_max: float = 3.5
    read_timeout_s: int = 120
    lock_timeout_s: int = 30
    max_retries: int = 3

    @classmethod
    def from_yaml(cls, repo_root: Path | None = None) -> IngestSettings:
        root = repo_root or _find_repo_root()
        config_path = root / "config" / "ingest.yaml"
        data: dict = {}
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            holdout = raw.pop("holdout", {}) or {}
            online = raw.pop("online", {}) or {}
            io_cfg = raw.pop("io", {}) or {}
            data = {
                "repo_root": Path(raw.get("repo_root", ".")).resolve()
                if not Path(raw.get("repo_root", ".")).is_absolute()
                else Path(raw.get("repo_root", ".")),
                "l2_root": Path(raw.get("l2_root", "data/l2")),
                "logs_root": Path(raw.get("logs_root", "logs/ingest")),
                "schema_version": raw.get("schema_version", "1.0.0"),
                "holdout_start": holdout.get("start", "2025-05-01"),
                "holdout_end": holdout.get("end", "2025-10-30"),
                "train_cutoff": raw.get("train_cutoff", "2025-04-30"),
                "online_max_rows": online.get("max_rows", 500),
                "online_sla_p95_ms": online.get("sla_p95_ms", 3000),
                "db_proxy_factor": raw.get("db_proxy_factor", 0.985),
                "tsa_train_min": raw.get("tsa_train_min", 1000),
                "mix_tolerance": raw.get("mix_tolerance", 0.02),
                "extr_impute_enabled": raw.get("extr_impute", {}).get("enabled", True),
                "extr_impute_min_train_rows": raw.get("extr_impute", {}).get(
                    "min_train_rows", 200
                ),
                "extr_impute_random_state": raw.get("extr_impute", {}).get(
                    "random_state", 42
                ),
                "extr_range_min": raw.get("extr_impute", {}).get("range_min", 1.0),
                "extr_range_max": raw.get("extr_impute", {}).get("range_max", 3.5),
                "read_timeout_s": io_cfg.get("read_timeout_s", 120),
                "lock_timeout_s": io_cfg.get("lock_timeout_s", 30),
                "max_retries": io_cfg.get("max_retries", 3),
            }
            if data["repo_root"] == Path("."):
                data["repo_root"] = root
        else:
            data["repo_root"] = root
        return cls(**data)

    @property
    def l2_path(self) -> Path:
        return (self.repo_root / self.l2_root).resolve()

    @property
    def logs_path(self) -> Path:
        return (self.repo_root / self.logs_root).resolve()


@lru_cache
def get_settings() -> IngestSettings:
    return IngestSettings.from_yaml()
