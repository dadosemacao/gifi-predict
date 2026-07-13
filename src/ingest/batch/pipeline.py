from __future__ import annotations

import json
import time
from pathlib import Path

from ingest.config import IngestSettings
from ingest.connectors.excel_qm import read_qm_processo
from ingest.contracts.loader import ContractLoader
from ingest.observability.logging import log_ingest_end, log_ingest_start
from ingest.observability.quarantine import quarantine_batch
from ingest.observability.remediation import record_remediation
from ingest.observability.signals import Severity, SignalCollector
from ingest.publish.holdout import split_holdout
from ingest.publish.manifest import build_manifest, dataset_version_now
from ingest.publish.publisher import publish_batch_artifacts
from ingest.transform.pipeline import transform_historical
from ingest.validation.schema import SchemaValidator
from ingest.validation.warnings import WarningMatrixEvaluator


def run_batch_pipeline(source: Path, settings: IngestSettings | None = None) -> dict:
    settings = settings or IngestSettings.from_yaml()
    loader = ContractLoader(settings.repo_root)
    schema = SchemaValidator(loader)
    signals = SignalCollector()
    warnings = WarningMatrixEvaluator(loader)

    t0 = time.perf_counter()
    df, identity = read_qm_processo(source, schema)
    log_ingest_start(
        path="historical_batch",
        batch_id=identity.batch_id,
        component="I1",
        source_hash=identity.source_hash,
    )

    missing = schema.missing_source_required(df)
    if missing:
        signals.emit(
            "INGEST_SCHEMA_FAIL",
            Severity.BLOCKING,
            f"missing columns: {missing}",
        )

    transformed = df
    exclusions: dict[str, int] = {}
    if not signals.has_blocking:
        transformed, exclusions = transform_historical(df, settings, signals)

    if not signals.has_blocking:
        post_missing = schema.missing_required(transformed)
        if post_missing:
            signals.emit(
                "INGEST_SCHEMA_FAIL",
                Severity.BLOCKING,
                f"missing columns after transform: {post_missing}",
            )
    train_df, holdout_df = split_holdout(transformed, settings)

    warning_codes = signals.codes()
    warnings.apply_unknown_guard(warning_codes, signals)

    holdout_ok, holdout_blocked = warnings.evaluate_context(
        warning_codes, "holdout", holdout_df
    )

    publish_status = "quarantined"
    version = dataset_version_now()
    result: dict = {"batch_id": identity.batch_id, "publish_status": publish_status}

    if signals.has_blocking:
        quarantine_batch(
            settings.l2_path,
            identity.batch_id,
            source,
            signals,
        )
    else:
        publish_status = (
            "published_with_warnings" if signals.codes() else "published_ok"
        )
        if any(s.severity == Severity.WARNING for s in signals.signals):
            publish_status = "published_with_warnings"
        manifest = build_manifest(
            schema_version=settings.schema_version,
            dataset_version=version,
            identity=identity,
            signals=signals,
            row_counts={
                "read": len(df),
                "train": len(train_df),
                "holdout": len(holdout_df),
            },
            rules_applied=[
                "TSA_filter",
                "DB_proxy",
                "mix_features",
                "extr_impute",
                "holdout_split",
            ],
            exclusions=exclusions,
            publish_status=publish_status,
            holdout_eligible=holdout_ok,
        )
        if not holdout_ok:
            manifest["publish_status"] = "published_with_warnings"
            manifest["holdout_blocked_warnings"] = holdout_blocked
        publish_batch_artifacts(
            settings.l2_path,
            version,
            {"train_features": train_df, "holdout_features": holdout_df},
            manifest,
            signals,
            settings.schema_version,
        )
        result["published_path"] = str(settings.l2_path / "published" / version)

    result["publish_status"] = publish_status
    duration_ms = int((time.perf_counter() - t0) * 1000)
    log_ingest_end(
        path="historical_batch",
        batch_id=identity.batch_id,
        component="I4",
        duration_ms=duration_ms,
        source_hash=identity.source_hash,
        rows_read=len(df),
        rows_written=len(train_df) + len(holdout_df),
        rows_excluded=int(len(df) - len(transformed)),
        publish_status=publish_status,
        signals=signals.codes(),
        schema_version=settings.schema_version,
    )
    return result


def run_reprocess_from_trigger(settings: IngestSettings | None = None) -> dict:
    settings = settings or IngestSettings.from_yaml()
    trigger_path = settings.l2_path / "triggers" / "accept_data_reject.json"
    if not trigger_path.exists():
        raise FileNotFoundError(f"no trigger file: {trigger_path}")
    payload = json.loads(trigger_path.read_text(encoding="utf-8"))
    source = Path(payload["source_path"])
    before_hash = payload.get("source_hash", "")
    result = run_batch_pipeline(source, settings)
    record_remediation(
        settings.l2_path,
        {
            "trigger_signal": "ACCEPT_DATA_REJECT",
            "trigger_severity": "blocking",
            "source_hash_before": before_hash,
            "source_hash_after": result.get("source_hash", ""),
            "responsible": payload.get("responsible", "CD"),
            "reason": payload.get("reason", ""),
            "action_taken": "reprocess via CLI",
            "publish_status_after": result.get("publish_status", ""),
        },
    )
    processed = settings.l2_path / "triggers" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    trigger_path.replace(processed / trigger_path.name)
    return result
