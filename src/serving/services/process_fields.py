from __future__ import annotations

PROCESS_API_TO_COLUMN: dict[str, str] = {
    "carga_alcalina": "Carga_Alcalina",
    "kappa": "Kappa",
    "db_sgf": "DB_SGF",
    "db_lab": "DB_LAB",
    "secura_pct": "Secura_pct",
    "casca_pct": "Casca_pct",
    "extrativo_total": "Extrativo_Total",
    "extrativo_at": "Extrativo_AT",
    "extrativo_sgf": "Extrativo_SGF",
    "tpc": "TPC",
    "idade": "Idade",
    "vmi_le_021": "vmi_le_021",
    "vmi_021_025": "vmi_021_025",
    "vmi_gt_025": "vmi_gt_025",
    "pct_ab": "pct_AB",
    "pct_c": "pct_C",
    "pct_dmg": "pct_DMG",
}


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
