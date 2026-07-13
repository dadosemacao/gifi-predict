from __future__ import annotations

from serving.schemas import FieldOriginsResponse


def build_field_origins(origins: dict[str, str]) -> FieldOriginsResponse:
    payload = {key: origins.get(key) for key in origins}
    return FieldOriginsResponse(**payload)
