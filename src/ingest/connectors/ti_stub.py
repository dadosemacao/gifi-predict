from __future__ import annotations

from pathlib import Path

import pandas as pd

from ingest.connectors.excel_qm import read_qm_processo
from ingest.validation.schema import SchemaValidator


class TiInterpolatedConnector:
    def read(self, path: Path, schema: SchemaValidator) -> tuple[pd.DataFrame, object]:
        raise NotImplementedError("TI interpolated source not available — use Excel fallback")


def read_historical_source(path: Path, schema: SchemaValidator) -> tuple[pd.DataFrame, object]:
    return read_qm_processo(path, schema)
