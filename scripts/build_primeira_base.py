"""Regenera base/primeira_base.csv com 13 preditores + pct_C auxiliar.

Autor: Emerson Antônio
Data: 2026-07-13

Fonte: L2 (train + holdout) via pointer data/l2_excel_validation/current.json.previous
Saída: base/primeira_base.csv — colunas modelo + TSA_dia + pct_C (imputer only)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from simulation.process_specs import (  # noqa: E402
    IMPUTER_AUX_COLUMN,
    PROCESS_COLUMNS,
    TARGET,
    encode_prod_alcali_class,
)


def _load_l2_ordered() -> pd.DataFrame:
    pointer_path = REPO / "data" / "l2_excel_validation" / "current.json.previous"
    if not pointer_path.exists():
        raise FileNotFoundError(f"pointer L2 ausente: {pointer_path}")
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    train = pd.read_parquet(pointer["paths"]["train_features"])
    holdout = pd.read_parquet(pointer["paths"]["holdout_features"])
    l2 = pd.concat([train, holdout], ignore_index=True)
    return l2.sort_values(["data_processo", "turno"]).reset_index(drop=True)


def build_primeira_base() -> pd.DataFrame:
    l2 = _load_l2_ordered()
    if "Prod alcali_class" not in l2.columns:
        raise ValueError("L2 não contém coluna 'Prod alcali_class'")

    frame = l2.copy()
    frame["Prod_alcali_class"] = frame["Prod alcali_class"].map(encode_prod_alcali_class)

    out_cols = list(PROCESS_COLUMNS) + [TARGET, IMPUTER_AUX_COLUMN]
    missing = [c for c in out_cols if c not in frame.columns]
    if missing:
        raise ValueError(f"colunas ausentes no L2: {missing}")

    complete = frame.loc[frame[out_cols].notna().all(axis=1), out_cols].reset_index(drop=True)
    return complete


def main() -> None:
    out = build_primeira_base()
    out_path = REPO / "base" / "primeira_base.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"Escrito {len(out)} linhas em {out_path}")
    print(f"Colunas: {list(out.columns)}")


if __name__ == "__main__":
    main()
