from __future__ import annotations

import math
from typing import Any

import pandas as pd

from ingest.config import IngestSettings


def _is_filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    return str(value).strip() != ""


class ScenarioValidator:
    def __init__(self, template: dict, settings: IngestSettings) -> None:
        self._template = template
        self._settings = settings

    def validate_dataframe(self, df: pd.DataFrame) -> list[str]:
        errors: list[str] = []
        if len(df) > self._settings.online_max_rows:
            errors.append(
                f"row count {len(df)} exceeds max {self._settings.online_max_rows}"
            )
            return errors

        required_cols = [
            c["name"] for c in self._template.get("columns", []) if c.get("required")
        ]
        for col in required_cols:
            if col not in df.columns:
                errors.append(f"missing required column: {col}")

        mix_cols = self._template.get("mix_rules", {}).get("columns", [])
        if all(c in df.columns for c in mix_cols):
            tol = self._template.get("mix_rules", {}).get("tolerance", 0.02)
            bad = (df[mix_cols].sum(axis=1) - 1.0).abs() > tol
            if bad.any():
                errors.append("mix sum outside tolerance")

        if "modo" in df.columns:
            for idx, row in df.iterrows():
                mode = str(row.get("modo", "")).upper()
                if mode == "A":
                    for col in self._template.get("mode_rules", {}).get("mode_A", {}).get(
                        "forbidden_non_empty", []
                    ):
                        if col in df.columns and _is_filled(row.get(col)):
                            errors.append(
                                f"row {idx}: Modo A forbids non-empty {col}"
                            )
        return errors
