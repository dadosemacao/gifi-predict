from __future__ import annotations

from typing import Any

import pandas as pd

from ingest.contracts.loader import ContractLoader


def _iter_column_specs(contract: dict) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for section in (
        "process",
        "wood_quality",
        "supply_and_mix",
        "supply_and_mix_derived",
        "keys_and_scale",
    ):
        for item in contract.get(section, []) or []:
            if isinstance(item, dict) and "name" in item:
                specs.append(item)
    diversity = contract.get("mix_diversity_prd", []) or []
    for item in diversity:
        if isinstance(item, dict) and "name" in item:
            specs.append(item)
    return specs


def build_alias_map(contract: dict) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for spec in _iter_column_specs(contract):
        name = spec["name"]
        mapping[name.lower()] = name
        for alias in spec.get("aliases", []) or []:
            mapping[str(alias).lower()] = name
    for key, value in (contract.get("column_aliases_map") or {}).items():
        mapping[str(key).lower()] = value
    for key, value in (contract.get("business_label_map") or {}).items():
        mapping[str(key).lower()] = str(value)
    return mapping


def normalize_columns(df: pd.DataFrame, contract: dict) -> pd.DataFrame:
    alias_map = build_alias_map(contract)
    rename = {
        col: alias_map[col.lower()]
        for col in df.columns
        if col.lower() in alias_map
    }
    return df.rename(columns=rename)


def required_train_columns(contract: dict) -> list[str]:
    cols: list[str] = []
    for spec in _iter_column_specs(contract):
        if spec.get("required_train"):
            cols.append(spec["name"])
    grain = contract.get("grain", {}).get("historical", [])
    return list(dict.fromkeys([*grain, *cols]))


def required_source_columns(contract: dict) -> list[str]:
    cols: list[str] = []
    for spec in _iter_column_specs(contract):
        if spec.get("required_train") and spec.get("required_source", True):
            cols.append(spec["name"])
    grain = contract.get("grain", {}).get("historical", [])
    return list(dict.fromkeys([*grain, *cols]))


class SchemaValidator:
    def __init__(self, loader: ContractLoader) -> None:
        self._contract = loader.feature_columns()

    @property
    def contract(self) -> dict:
        return self._contract

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        return normalize_columns(df, self._contract)

    def missing_required(self, df: pd.DataFrame) -> list[str]:
        required = required_train_columns(self._contract)
        return [c for c in required if c not in df.columns]

    def missing_source_required(self, df: pd.DataFrame) -> list[str]:
        required = required_source_columns(self._contract)
        return [c for c in required if c not in df.columns]
