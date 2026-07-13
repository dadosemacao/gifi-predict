from __future__ import annotations

TARGET = "TSA_dia"

# Camada 3 — 13 preditores oficiais para TSA_dia (reestruturação 2026-07-13).
PROCESS_COLUMNS: tuple[str, ...] = (
    "Carga_Alcalina",
    "Kappa",
    "Prod_alcali_class",
    "DB_SGF",
    "Idade",
    "TPC",
    "pct_AB",
    "pct_DMG",
    "vmi_le_021",
    "vmi_021_025",
    "vmi_gt_025",
    "Extrativo_AT",
    "Casca_pct",
)

PROCESS_API_TO_COLUMN: dict[str, str] = {
    "carga_alcalina": "Carga_Alcalina",
    "kappa": "Kappa",
    "prod_alcali_class": "Prod_alcali_class",
    "db_sgf": "DB_SGF",
    "idade": "Idade",
    "tpc": "TPC",
    "pct_ab": "pct_AB",
    "pct_dmg": "pct_DMG",
    "vmi_le_021": "vmi_le_021",
    "vmi_021_025": "vmi_021_025",
    "vmi_gt_025": "vmi_gt_025",
    "extrativo_at": "Extrativo_AT",
    "casca_pct": "Casca_pct",
}

# Auxiliares: não entram no modelo; imputação Tier A/B.
AUX_API_FIELDS: tuple[str, ...] = (
    "vmi",
    "pct_a",
    "pct_b",
    "pct_d",
    "pct_mg",
    "pct_c",
)

MANDATORY_API_FIELDS: tuple[str, ...] = (
    "carga_alcalina",
    "kappa",
    "prod_alcali_class",
    "db_sgf",
    "casca_pct",
    "tpc",
    "idade",
)

PROD_ALCALI_CLASS_MAP: dict[str, float] = {
    "baixo": 0.0,
    "normal": 1.0,
}

# Coluna auxiliar no CSV de treino do imputer (não é preditor do modelo TSA).
IMPUTER_AUX_COLUMN = "pct_C"


def encode_prod_alcali_class(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("prod_alcali_class deve ser 0/1 ou 'baixo'/'normal'")
    if isinstance(value, (int, float)):
        numeric = float(value)
        if numeric in (0.0, 1.0):
            return numeric
        raise ValueError("prod_alcali_class ordinal deve ser 0 (baixo) ou 1 (normal)")
    key = str(value).strip().lower()
    if key not in PROD_ALCALI_CLASS_MAP:
        raise ValueError(
            "prod_alcali_class inválido: use 0/1 ou 'baixo'/'normal'; "
            f"recebido {value!r}"
        )
    return PROD_ALCALI_CLASS_MAP[key]
