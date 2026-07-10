from __future__ import annotations


class IntegrityError(Exception):
    """L3 artifact hash mismatch or corrupt manifest."""


class GateError(Exception):
    """Acceptance gate blocked before report generation."""
