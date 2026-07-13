from __future__ import annotations

from simulation.process_specs import PROCESS_COLUMNS, TARGET

DEFAULT_ANCHOR = "TSA_roll3"
PROCESS_FEATURES = list(PROCESS_COLUMNS)
LAG_FEATURES = ["TSA_lag1", "TSA_roll3", "TSA_roll7"]
MIN_TSA_HISTORY = 7
