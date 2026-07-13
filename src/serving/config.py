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


class ServingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GIFI_SERVING_", extra="ignore")

    repo_root: Path = Field(default_factory=_find_repo_root)
    host: str = "127.0.0.1"
    port: int = 8000
    default_run_id: str = ""
    default_forecast_run_id: str = ""
    default_tsa_run_id: str = ""
    forecast_models_root: Path = Path("models/primeira_base")
    reports_root: Path = Path("reports/acceptance")
    static_dir: Path = Path("web/dist")
    template_path: Path = Path("docs/kb/gifi-domain/specs/template_cenario_v0.yaml")
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )
    demo_default: bool = True
    ephemeral_prefix: str = "ui-"
    audit_enabled: bool = True
    audit_db_path: Path = Path("logs/serving_audit.db")
    audit_max_body_bytes: int = 65536

    @classmethod
    def from_yaml(cls, repo_root: Path | None = None) -> ServingSettings:
        root = repo_root or _find_repo_root()
        config_path = root / "config" / "serving.yaml"
        data: dict = {"repo_root": root}
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            data.update(
                {
                    "host": raw.get("host", "127.0.0.1"),
                    "port": raw.get("port", 8000),
                    "default_run_id": raw.get("default_run_id", ""),
                    "default_forecast_run_id": raw.get("default_forecast_run_id", ""),
                    "default_tsa_run_id": raw.get("default_tsa_run_id", ""),
                    "forecast_models_root": Path(
                        raw.get("forecast_models_root", "models/primeira_base")
                    ),
                    "reports_root": Path(raw.get("reports_root", "reports/acceptance")),
                    "static_dir": Path(raw.get("static_dir", "web/dist")),
                    "template_path": Path(
                        raw.get(
                            "template_path",
                            "docs/kb/gifi-domain/specs/template_cenario_v0.yaml",
                        )
                    ),
                    "cors_origins": raw.get("cors_origins", data.get("cors_origins", [])),
                    "demo_default": raw.get("demo_default", True),
                    "ephemeral_prefix": raw.get("ephemeral_prefix", "ui-"),
                    "audit_enabled": raw.get("audit_enabled", True),
                    "audit_db_path": Path(
                        raw.get("audit_db_path", "logs/serving_audit.db")
                    ),
                    "audit_max_body_bytes": raw.get("audit_max_body_bytes", 65536),
                }
            )
        return cls(**data)

    @property
    def audit_db_path_resolved(self) -> Path:
        return (self.repo_root / self.audit_db_path).resolve()

    @property
    def reports_path(self) -> Path:
        return (self.repo_root / self.reports_root).resolve()

    @property
    def static_path(self) -> Path:
        return (self.repo_root / self.static_dir).resolve()

    @property
    def template_file(self) -> Path:
        return (self.repo_root / self.template_path).resolve()


@lru_cache
def get_settings() -> ServingSettings:
    return ServingSettings.from_yaml()
