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
                "pct_ABC",
                "pct_CDMG",
                "mix_entropy",
                "mix_hhi",
                "DB_LAB",
                "Extrativo_AT",
                "Carga_Alcalina",
                "TPC",
                "VMI",
                "Volume_m3",
                "Kappa",
            ],
            "optional_features": ["Casca_pct"],
        },
    }
