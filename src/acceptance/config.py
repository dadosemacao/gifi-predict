from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from simulation.config import _find_repo_root


class AcceptanceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GIFI_", extra="ignore")

    repo_root: Path = Field(default_factory=_find_repo_root)
    l2_root: Path = Path("data/l2")
    models_root: Path = Path("models")
    reports_root: Path = Path("reports/acceptance")
    logs_root: Path = Path("logs/acceptance")
    scenarios_dir: Path = Path("config/acceptance_scenarios")
    mae_limit: float = 56.0
    recompute_matriz_a: bool = True
    db_proxy_factor: float = 0.985
    holdout_start: str = "2025-05-01"
    holdout_end: str = "2025-10-30"
    matriz_c_required: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "TC-09": ["TPC"],
            "TC-10": ["Extrativo_AT", "Carga_Alcalina"],
        }
    )
    lock_timeout_s: int = 30
    max_retries: int = 3

    @classmethod
    def from_yaml(cls, repo_root: Path | None = None) -> AcceptanceSettings:
        root = repo_root or _find_repo_root()
        config_path = root / "config" / "acceptance.yaml"
        data: dict[str, Any] = {}
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            holdout = raw.pop("holdout", {}) or {}
            io_cfg = raw.pop("io", {}) or {}
            matriz_c = raw.pop("matriz_c", {}) or {}
            repo = raw.get("repo_root", ".")
            resolved_root = root if repo == "." else Path(repo)
            if not resolved_root.is_absolute():
                resolved_root = (root / resolved_root).resolve()
            data = {
                "repo_root": resolved_root,
                "l2_root": Path(raw.get("l2_root", "data/l2")),
                "models_root": Path(raw.get("models_root", "models")),
                "reports_root": Path(raw.get("reports_root", "reports/acceptance")),
                "logs_root": Path(raw.get("logs_root", "logs/acceptance")),
                "scenarios_dir": Path(
                    raw.get("scenarios_dir", "config/acceptance_scenarios")
                ),
                "mae_limit": raw.get("mae_limit", 56.0),
                "recompute_matriz_a": raw.get("recompute_matriz_a", True),
                "db_proxy_factor": raw.get("db_proxy_factor", 0.985),
                "holdout_start": holdout.get("start", "2025-05-01"),
                "holdout_end": holdout.get("end", "2025-10-30"),
                "matriz_c_required": matriz_c.get(
                    "required_in_top3",
                    {
                        "TC-09": ["TPC"],
                        "TC-10": ["Extrativo_AT", "Carga_Alcalina"],
                    },
                ),
                "lock_timeout_s": io_cfg.get("lock_timeout_s", 30),
                "max_retries": io_cfg.get("max_retries", 3),
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
    def reports_path(self) -> Path:
        return (self.repo_root / self.reports_root).resolve()

    @property
    def logs_path(self) -> Path:
        return (self.repo_root / self.logs_root).resolve()

    @property
    def scenarios_path(self) -> Path:
        path = self.scenarios_dir
        if path.is_absolute():
            return path
        return (self.repo_root / path).resolve()


@lru_cache
def get_settings() -> AcceptanceSettings:
    return AcceptanceSettings.from_yaml()
