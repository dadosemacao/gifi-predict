from __future__ import annotations

from pathlib import Path

import yaml


class ContractLoader:
    def __init__(self, repo_root: Path) -> None:
        self._root = repo_root
        self._kb = repo_root / "docs" / "kb"

    def feature_columns(self) -> dict:
        path = self._kb / "gifi-ingest" / "specs" / "feature-columns.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def warning_matrix(self) -> dict:
        path = self._kb / "gifi-ingest" / "specs" / "warning-matrix.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def signal_catalog(self) -> dict:
        path = self._kb / "gifi-ingest" / "specs" / "signal-catalog.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def artifact_contract(self) -> dict:
        path = self._kb / "gifi-ingest" / "specs" / "artifact-contract.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def scenario_template(self) -> dict:
        path = self._kb / "gifi-domain" / "specs" / "template_cenario_v0.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def remediation_schema(self) -> dict:
        path = self._kb / "gifi-ingest" / "specs" / "remediation-evidence.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))
