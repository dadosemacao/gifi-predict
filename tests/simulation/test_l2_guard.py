from __future__ import annotations

import pytest

from ingest.contracts.models import SchemaVersionError
from simulation.exceptions import HoldoutIneligibleError
from simulation.l2.guard import guard_holdout_eligible, guard_schema
from simulation.l2.loader import load_l2_bundle


def test_load_l2_bundle(l2_mini):
    bundle = load_l2_bundle(l2_mini)
    assert len(bundle.train) >= 50
    assert len(bundle.holdout) >= 5
    assert bundle.schema_version == "1.0.0"


def test_guard_schema_mismatch():
    with pytest.raises(SchemaVersionError):
        guard_schema({"schema_version": "2.0.0"}, "1.0.0")


def test_guard_holdout_ineligible():
    with pytest.raises(HoldoutIneligibleError):
        guard_holdout_eligible({"holdout_eligible": False})
