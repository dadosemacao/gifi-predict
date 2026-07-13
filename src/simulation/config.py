from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from simulation.models.grid_search import TuningConfig


def _find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "docs" / "kb" / "_index.yaml").exists():
            return candidate
    return current


class SimulationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GIFI_", extra="ignore")

    repo_root: Path = Field(default_factory=_find_repo_root)
    l2_root: Path = Path("data/l2")
    models_root: Path = Path("models")
    logs_root: Path = Path("logs/simulation")
    expected_schema_version: str = "1.0.0"
    random_state: int = 42
    families: list[str] = Field(
        default_factory=lambda: ["baseline", "elasticnet", "randomforest"]
    )
    holdout_start: str = "2025-05-01"
    holdout_end: str = "2025-10-30"
    mae_limit_report: float = 56.0
    db_proxy_factor: float = 0.985
    min_train_rows: int = 50
    read_timeout_s: int = 120
    lock_timeout_s: int = 30
    max_retries: int = 3
    elo_specs: dict[str, Any] = Field(default_factory=dict)
    tuning_enabled: bool = True
    tuning_cv_folds: int = 5
    tuning_elo3_families: list[str] = Field(
        default_factory=lambda: [
            "elasticnet",
            "ridge",
            "lasso",
            "randomforest",
            "extratrees",
            "histgradientboosting",
            "xgboost",
            "lightgbm",
            "catboost",
        ]
    )
    tuning_grid_search_pool: str = "train"
    tuning_training_pool: str = "combined"
    tuning_train_fraction: float = 0.8
    tuning_fast: bool = False
    tuning_elo3_cascade_fill: bool = False
    tuning_elo3_oof_stack: bool = True
    tuning_n_jobs: int = -1
    tuning_select_by_cascade: bool = True
    training_mode: str = "cascade"
    mae_metric: str = "cascade"

    def tuning_config(self) -> TuningConfig:
        return TuningConfig(
            enabled=self.tuning_enabled,
            cv_folds=self.tuning_cv_folds,
            elo3_families=tuple(self.tuning_elo3_families),
            grid_search_pool=self.tuning_grid_search_pool,
            training_pool=self.tuning_training_pool,
            train_fraction=self.tuning_train_fraction,
            fast=self.tuning_fast,
            elo3_cascade_fill=self.tuning_elo3_cascade_fill,
            elo3_oof_stack=self.tuning_elo3_oof_stack,
            n_jobs=self.tuning_n_jobs,
            select_by_cascade=self.tuning_select_by_cascade,
        )

    @classmethod
    def from_yaml(cls, repo_root: Path | None = None) -> SimulationSettings:
        root = repo_root or _find_repo_root()
        config_path = root / "config" / "simulation.yaml"
        data: dict[str, Any] = {}
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            holdout = raw.pop("holdout", {}) or {}
            io_cfg = raw.pop("io", {}) or {}
            tuning_cfg = raw.pop("tuning", {}) or {}
            repo = raw.get("repo_root", ".")
            resolved_root = root if repo == "." else Path(repo)
            if not resolved_root.is_absolute():
                resolved_root = (root / resolved_root).resolve()
            data = {
                "repo_root": resolved_root,
                "l2_root": Path(raw.get("l2_root", "data/l2")),
                "models_root": Path(raw.get("models_root", "models")),
                "logs_root": Path(raw.get("logs_root", "logs/simulation")),
                "expected_schema_version": raw.get("expected_schema_version", "1.0.0"),
                "random_state": raw.get("random_state", 42),
                "families": raw.get(
                    "families", ["baseline", "elasticnet", "randomforest"]
                ),
                "holdout_start": holdout.get("start", "2025-05-01"),
                "holdout_end": holdout.get("end", "2025-10-30"),
                "mae_limit_report": raw.get("mae_limit_report", 56.0),
                "db_proxy_factor": raw.get("db_proxy_factor", 0.985),
                "min_train_rows": raw.get("min_train_rows", 50),
                "read_timeout_s": io_cfg.get("read_timeout_s", 120),
                "lock_timeout_s": io_cfg.get("lock_timeout_s", 30),
                "max_retries": io_cfg.get("max_retries", 3),
                "elo_specs": raw.get("elo_specs", {}),
                "tuning_enabled": tuning_cfg.get("enabled", True),
                "tuning_cv_folds": tuning_cfg.get("cv_folds", 5),
                "tuning_elo3_families": tuning_cfg.get(
                    "elo3_families",
                    [
                        "elasticnet",
                        "ridge",
                        "lasso",
                        "randomforest",
                        "extratrees",
                        "histgradientboosting",
                        "xgboost",
                        "lightgbm",
                        "catboost",
                    ],
                ),
                "tuning_grid_search_pool": tuning_cfg.get("grid_search_pool", "train"),
                "tuning_training_pool": tuning_cfg.get("training_pool", "train"),
                "tuning_train_fraction": tuning_cfg.get("train_fraction", 0.8),
                "tuning_fast": tuning_cfg.get("fast", False),
                "tuning_elo3_cascade_fill": tuning_cfg.get("elo3_cascade_fill", False),
                "tuning_elo3_oof_stack": tuning_cfg.get("elo3_oof_stack", True),
                "tuning_n_jobs": tuning_cfg.get("n_jobs", -1),
                "tuning_select_by_cascade": tuning_cfg.get("select_by_cascade", True),
                "training_mode": raw.get("training_mode", "cascade"),
                "mae_metric": raw.get("mae_metric", "cascade"),
            }
        else:
            data["repo_root"] = root
        return cls(**data)

    @property
    def l2_path(self) -> Path:
        return (self.repo_root / self.l2_root).resolve()

    @property
    def models_path(self) -> Path:
        return (self.repo_root / self.models_root).resolve()

    @property
    def logs_path(self) -> Path:
        return (self.repo_root / self.logs_root).resolve()


@lru_cache
def get_settings() -> SimulationSettings:
    return SimulationSettings.from_yaml()
