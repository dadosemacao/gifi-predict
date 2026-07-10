from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pandas as pd

from ingest.contracts.models import BatchIdentity
from ingest.validation.schema import SchemaValidator


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


_TURNO_FROM_HOUR = {0: "1", 8: "2", 16: "3"}


def _derive_grain_from_process_date(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "data_processo" not in out.columns:
        return out
    ts = pd.to_datetime(out["data_processo"], errors="coerce")
    if "turno" not in out.columns:
        out["turno"] = ts.dt.hour.map(_TURNO_FROM_HOUR)
        unknown = out["turno"].isna() & ts.notna()
        if unknown.any():
            out.loc[unknown, "turno"] = ts.loc[unknown].dt.hour.astype(str)
    out["data_processo"] = ts.dt.strftime("%Y-%m-%d")
    return out


def read_qm_processo(path: Path, schema: SchemaValidator) -> tuple[pd.DataFrame, BatchIdentity]:
    if not path.exists():
        raise FileNotFoundError(f"source missing: {path}")

    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path, engine="openpyxl")
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"unsupported format: {path.suffix}")

    df = schema.normalize(df)
    df = _derive_grain_from_process_date(df)

    period_start = period_end = None
    if "data_processo" in df.columns and not df.empty:
        period_start = str(df["data_processo"].min())
        period_end = str(df["data_processo"].max())

    identity = BatchIdentity(
        batch_id=str(uuid.uuid4()),
        source_path=str(path),
        source_hash=_file_hash(path),
        period_start=period_start,
        period_end=period_end,
    )
    return df, identity
