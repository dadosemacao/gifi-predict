"""Backfill de Extrativo_AT no L2 publicado.

Autor: Emerson Antônio
Data: 2026-07-13

Treina o imputer do Elo 1 (mix + idade) apenas com as linhas de treino que
possuem Extrativo_AT medido e aplica a estimativa às linhas ausentes de
`train_features` e `holdout_features`, marcando `extr_origin`
(medido/estimado). Publica uma nova versão de dataset e atualiza `current.json`.

Uso:
    python scripts/backfill_extrativo_l2.py --l2-root data/l2_excel_validation
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from ingest.config import IngestSettings
from ingest.transform.imputation import (
    apply_extrativo_imputer,
    fit_extrativo_imputer,
)


def _load_pointer(l2_root: Path) -> dict:
    pointer_path = l2_root / "current.json"
    if not pointer_path.exists():
        raise FileNotFoundError(f"current.json não encontrado em {l2_root}")
    return json.loads(pointer_path.read_text(encoding="utf-8"))


def _coverage(df: pd.DataFrame) -> str:
    total = len(df)
    notna = int(df["Extrativo_AT"].notna().sum())
    return f"{notna}/{total} ({notna / total:.1%})" if total else "0/0"


def run(l2_root: Path, settings: IngestSettings) -> dict:
    pointer = _load_pointer(l2_root)
    train_path = Path(pointer["paths"]["train_features"])
    holdout_path = Path(pointer["paths"]["holdout_features"])
    schema_version = pointer["schema_version"]

    train = pd.read_parquet(train_path)
    holdout = pd.read_parquet(holdout_path)

    print("Cobertura Extrativo_AT ANTES:")
    print(f"  train:   {_coverage(train)}")
    print(f"  holdout: {_coverage(holdout)}")

    fitted = fit_extrativo_imputer(
        train,
        random_state=settings.extr_impute_random_state,
        min_train_rows=settings.extr_impute_min_train_rows,
    )
    if fitted is None:
        raise RuntimeError("cobertura insuficiente para treinar o imputer do Elo 1")
    model, meta = fitted
    print(f"\nImputer treinado em {meta['n_train_rows']} linhas medidas (train).")

    train_out, n_train = apply_extrativo_imputer(
        train, model, meta, range_min=settings.extr_range_min, range_max=settings.extr_range_max
    )
    holdout_out, n_holdout = apply_extrativo_imputer(
        holdout, model, meta, range_min=settings.extr_range_min, range_max=settings.extr_range_max
    )

    print(f"\nLinhas estimadas: train={n_train} | holdout={n_holdout}")
    print("Cobertura Extrativo_AT DEPOIS:")
    print(f"  train:   {_coverage(train_out)}")
    print(f"  holdout: {_coverage(holdout_out)}")

    version = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    dest = l2_root / "published" / version
    staging = l2_root / "published" / f".staging_{version}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    train_out.to_parquet(staging / "train_features.parquet", index=False, engine="pyarrow")
    holdout_out.to_parquet(staging / "holdout_features.parquet", index=False, engine="pyarrow")

    manifest_text = (train_path.parent / "batch_manifest.json").read_text(encoding="utf-8")
    src_manifest = json.loads(manifest_text)
    src_manifest["dataset_version"] = version
    rules = src_manifest.get("rules_applied", [])
    if "extr_impute" not in rules:
        rules.append("extr_impute")
    src_manifest["rules_applied"] = rules
    codes = src_manifest.get("warning_codes", [])
    if n_train or n_holdout:
        if "INGEST_PROXY_EXTR" not in codes:
            codes.append("INGEST_PROXY_EXTR")
    src_manifest["warning_codes"] = codes
    src_manifest["extr_impute"] = {
        "n_train_estimated": n_train,
        "n_holdout_estimated": n_holdout,
        "imputer_train_rows": meta["n_train_rows"],
        "features": meta["features"],
        "backfilled_from": pointer["dataset_version"],
    }
    (staging / "batch_manifest.json").write_text(
        json.dumps(src_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if dest.exists():
        raise FileExistsError(f"versão já existe: {dest}")
    staging.replace(dest)

    if (l2_root / "current.json").exists():
        (l2_root / "current.json.previous").write_text(
            json.dumps(pointer, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    new_pointer = {
        "dataset_version": version,
        "schema_version": schema_version,
        "paths": {
            "train_features": str(dest / "train_features.parquet"),
            "holdout_features": str(dest / "holdout_features.parquet"),
        },
        "manifest": str(dest / "batch_manifest.json"),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    (l2_root / "current.json").write_text(
        json.dumps(new_pointer, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nPublicado: {dest}")
    return {"version": version, "n_train": n_train, "n_holdout": n_holdout}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill de Extrativo_AT no L2")
    parser.add_argument("--l2-root", default="data/l2_excel_validation", type=Path)
    args = parser.parse_args()
    settings = IngestSettings.from_yaml()
    run(args.l2_root.resolve(), settings)


if __name__ == "__main__":
    main()
