from __future__ import annotations

import time
from pathlib import Path

from ingest.config import IngestSettings
from ingest.connectors.scenario_upload import read_scenario_upload
from ingest.contracts.loader import ContractLoader
from ingest.observability.logging import log_ingest_end, log_ingest_start
from ingest.validation.scenario import ScenarioValidator


def validate_scenario_file(
    path: Path,
    cenario_id: str,
    settings: IngestSettings | None = None,
) -> dict:
    settings = settings or IngestSettings.from_yaml()
    loader = ContractLoader(settings.repo_root)
    template = loader.scenario_template()
    validator = ScenarioValidator(template, settings)

    t0 = time.perf_counter()
    batch_id = f"scenario-{cenario_id}"
    log_ingest_start(
        path="scenario_online",
        batch_id=batch_id,
        component="I2",
        cenario_id=cenario_id,
    )

    df = read_scenario_upload(path)
    errors = validator.validate_dataframe(df)
    duration_ms = int((time.perf_counter() - t0) * 1000)

    if errors:
        log_ingest_end(
            path="scenario_online",
            batch_id=batch_id,
            component="I2",
            duration_ms=duration_ms,
            sla_ms=duration_ms,
            cenario_id=cenario_id,
            publish_status="rejected",
            signals=["INGEST_SCENARIO_REJECT"],
            reject_reason="; ".join(errors),
        )
        return {
            "ok": False,
            "signal": "INGEST_SCENARIO_REJECT",
            "errors": errors,
            "sla_ms": duration_ms,
        }

    log_ingest_end(
        path="scenario_online",
        batch_id=batch_id,
        component="I2",
        duration_ms=duration_ms,
        sla_ms=duration_ms,
        cenario_id=cenario_id,
        publish_status="accepted",
        row_count=len(df),
    )
    return {"ok": True, "row_count": len(df), "sla_ms": duration_ms, "frame": df}
