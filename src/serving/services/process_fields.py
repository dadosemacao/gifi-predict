from __future__ import annotations

from simulation.process_specs import PROCESS_API_TO_COLUMN


def process_dict(body: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for api_key, col in PROCESS_API_TO_COLUMN.items():
        if api_key not in body:
            raise ValueError(f"campo ausente: {api_key}")
        out[col] = float(body[api_key])
    return out


def process_dict_from_resolved(values: dict[str, float]) -> dict[str, float]:
    """Converte dict snake_case resolvido para nomes de coluna do modelo."""
    return {PROCESS_API_TO_COLUMN[k]: float(values[k]) for k in PROCESS_API_TO_COLUMN}
