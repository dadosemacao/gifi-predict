from __future__ import annotations

from typing import Literal

import pandas as pd

from ingest.contracts.loader import ContractLoader
from ingest.observability.signals import Severity, SignalCollector

Context = Literal["train", "holdout", "inference"]


class WarningMatrixEvaluator:
    def __init__(self, loader: ContractLoader) -> None:
        self._matrix = loader.warning_matrix().get("matrix", {})
        self._default = loader.warning_matrix().get("default_unknown_warning", "block")

    def is_admitted(self, code: str, context: Context, df: pd.DataFrame | None = None) -> bool:
        rule = self._matrix.get(code)
        if rule is None:
            return self._default != "block"

        ctx_rule = rule.get(context)
        if ctx_rule == "admit":
            return True
        if ctx_rule == "not_applicable":
            return True
        if ctx_rule == "block":
            return False
        if isinstance(ctx_rule, dict):
            if "admit_if" in ctx_rule:
                return self._eval_admit_if(code, ctx_rule["admit_if"], df)
            if "block_if" in ctx_rule:
                return not self._eval_block_if(ctx_rule["block_if"], df)
        return False

    def _eval_admit_if(self, code: str, cond: dict, df: pd.DataFrame | None) -> bool:
        if code == "INGEST_PROXY_DB" and df is not None and "db_origin" in df.columns:
            ratio = (df["db_origin"] == "proxy").mean()
            return ratio <= cond.get("max_proxy_row_ratio", 1.0)
        if code == "INGEST_PROXY_EXTR" and df is not None and "extr_origin" in df.columns:
            ratio = (df["extr_origin"] == "estimado").mean()
            return ratio <= cond.get("max_estimated_row_ratio", 1.0)
        return True

    def _eval_block_if(self, condition: str, df: pd.DataFrame | None) -> bool:
        if condition == "critical_target_or_feature_missing_in_window" and df is not None:
            if "Extrativo_AT" in df.columns:
                return df["Extrativo_AT"].isna().all()
            return False
        return False

    def evaluate_context(
        self, codes: list[str], context: Context, df: pd.DataFrame | None = None
    ) -> tuple[bool, list[str]]:
        blocked: list[str] = []
        for code in codes:
            if not self.is_admitted(code, context, df):
                blocked.append(code)
        return len(blocked) == 0, blocked

    def apply_unknown_guard(self, codes: list[str], signals: SignalCollector) -> None:
        known = set(self._matrix.keys())
        for code in codes:
            if code not in known and code not in {"INGEST_FILTER_INFO"}:
                signals.emit(
                    code,
                    Severity.BLOCKING,
                    "unknown warning — default block per warning matrix",
                )
