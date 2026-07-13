from __future__ import annotations

from typing import Any


def default_elo_specs() -> dict[str, Any]:
    return {
        "elo1": {
            "target": "Extrativo_AT",
            "features": [
                "pct_A",
                "pct_B",
                "pct_C",
                "pct_D",
                "pct_MG",
                "pct_ABC",
                "pct_CDMG",
                "mix_entropy",
                "mix_hhi",
                "dom_A",
                "dom_B",
                "dom_C",
                "dom_D",
                "dom_MG",
                "Idade",
            ],
        },
        "elo2": {
            "target": "Carga_Alcalina",
            "features": ["Extrativo_AT", "TPC", "DB_SGF"],
        },
        "elo3": {
            "target": "TSA_dia",
            "features": [
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
            ],
            "column_aliases": {"Prod_alcali_class": "Prod alcali_class"},
            "categorical_features": ["Prod_alcali_class"],
            "optional_features": ["Extrativo_AT", "Casca_pct"],
        },
    }
