from __future__ import annotations

TARGET = "TSA_dia"
DEFAULT_ANCHOR = "TSA_roll3"

PROCESS_FEATURES = [
    "Carga_Alcalina",
    "Kappa",
    "DB_SGF",
    "DB_LAB",
    "Secura_pct",
    "Casca_pct",
    "Extrativo_Total",
    "Extrativo_AT",
    "Extrativo_SGF",
    "TPC",
    "Idade",
    "vmi_le_021",
    "vmi_021_025",
    "vmi_gt_025",
    "pct_AB",
    "pct_C",
    "pct_DMG",
]

LAG_FEATURES = ["TSA_lag1", "TSA_roll3", "TSA_roll7"]

MIN_TSA_HISTORY = 7
