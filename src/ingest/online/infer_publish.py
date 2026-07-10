from __future__ import annotations

import json
from pathlib import Path

from ingest.config import IngestSettings
from ingest.online.validator import validate_scenario_file
from ingest.publish.parquet_writer import write_parquet
from ingest.transform.pipeline import transform_scenario


def publish_infer_features(
    path: Path,
    cenario_id: str,
    settings: IngestSettings | None = None,
) -> Path:
    settings = settings or IngestSettings.from_yaml()
    result = validate_scenario_file(path, cenario_id, settings)
    if not result.get("ok"):
        raise ValueError(result.get("errors", ["validation failed"]))

    df = result["frame"]
    if "cenario_id" not in df.columns:
        df = df.copy()
        df["cenario_id"] = cenario_id
    if "linha" not in df.columns:
        df = df.copy()
        df["linha"] = range(1, len(df) + 1)

    out = transform_scenario(df, settings)
    dest_dir = settings.l2_path / "scenarios" / cenario_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = dest_dir / "infer_features.parquet"
    write_parquet(out, parquet_path, settings.schema_version)

    manifest = {
        "cenario_id": cenario_id,
        "schema_version": settings.schema_version,
        "row_count": len(out),
        "source_upload": str(path),
    }
    (dest_dir / "scenario_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return parquet_path
