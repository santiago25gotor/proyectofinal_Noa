"""
config.py — Configuración central del proyecto.
Todos los scripts importan de aquí. Editar solo este archivo para cambiar
rutas, países o constantes globales.

Proyecto : Brecha Digital y Discapacidad en España
Fuente   : Eurostat DSB_ICTIU01 v1.0 (2024)
"""
from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent
DATA_RAW    = ROOT / "data" / "raw"
DATA_PROC   = ROOT / "data" / "processed"
IMAGES_DIR  = ROOT / "images"
SQL_DIR     = ROOT / "sql"
OUTPUTS_DIR = ROOT / "outputs"

RAW_CSV     = DATA_RAW  / "dsb_ictiu01_eurostat_2024.csv"
CLEAN_CSV   = DATA_PROC / "cleaned_dsb_ictiu01.csv"
ANAL_CSV    = DATA_PROC / "analytical_dsb_ictiu01.csv"
COUNTRY_CSV = DATA_PROC / "summary_by_country.csv"
SPAIN_CSV   = DATA_PROC / "summary_spain.csv"
EUROPE_CSV  = DATA_PROC / "summary_europe_comparison.csv"
DB_PATH     = ROOT / "proyecto.db"

# ── Países de interés (9 entidades) ───────────────────────────────────────
# IMPORTANTE: Lituania (LT) incluida — presenta la mayor brecha del dataset
# (35,86 pp). España es la 2ª con mayor brecha (18,26 pp).
TARGET_COUNTRIES: dict[str, str] = {
    "ES":        "España",
    "EU27_2020": "Media UE-27",
    "DE":        "Alemania",
    "FR":        "Francia",
    "IT":        "Italia",
    "NL":        "Países Bajos",
    "PT":        "Portugal",
    "SE":        "Suecia",
    "LT":        "Lituania",      # ← CORREGIDO: excluida por error en versión anterior
}

EU27_CODE = "EU27_2020"

# ── Valores de referencia UE-27 (Total sexo, Total edad, 2024) ─────────────
EU27_NO_DISABILITY    = 95.22
EU27_SEVERELY_LIMITED = 82.29
EU27_GAP_TOTAL        = EU27_NO_DISABILITY - EU27_SEVERELY_LIMITED  # 12,93 pp

# ── 24 categorías de ind_type a conservar ─────────────────────────────────
CATEGORIES_TO_KEEP: list[str] = [
    # Total (sin desagregación)
    "DIS_NONE", "DIS_LTD", "DIS_SEV", "DIS_LTD_SEV",
    # Por sexo
    "F_DIS_NONE", "F_DIS_LTD", "F_DIS_SEV", "F_DIS_LTD_SEV",
    "M_DIS_NONE", "M_DIS_LTD", "M_DIS_SEV", "M_DIS_LTD_SEV",
    # Por edad — 16-24
    "Y16_24_DIS_NONE", "Y16_24_DIS_LTD", "Y16_24_DIS_SEV", "Y16_24_DIS_LTD_SEV",
    # Por edad — 25-54
    "Y25_54_DIS_NONE", "Y25_54_DIS_LTD", "Y25_54_DIS_SEV", "Y25_54_DIS_LTD_SEV",
    # Por edad — 55-74
    "Y55_74_DIS_NONE", "Y55_74_DIS_LTD", "Y55_74_DIS_SEV", "Y55_74_DIS_LTD_SEV",
]

# ── Columnas del CSV raw → renombrado de trabajo ───────────────────────────
COLUMNS_TO_KEEP_RAW: list[str] = [
    "TIME_PERIOD",
    "geo",
    "Geopolitical entity (reporting)",
    "ind_type",
    "Individual type",
    "OBS_VALUE",
    "OBS_FLAG",
]

RENAME_MAP: dict[str, str] = {
    "TIME_PERIOD":                      "year",
    "geo":                              "country_code",
    "Geopolitical entity (reporting)":  "country_name_en",
    "ind_type":                         "category_code",
    "Individual type":                  "category_desc_en",
    "OBS_VALUE":                        "pct_internet_use",
    "OBS_FLAG":                         "quality_flag",
}

# ── Decodificación del eje de discapacidad ────────────────────────────────
DISABILITY_LEVEL_MAP: dict[str, str] = {
    "DIS_NONE":    "No disability",
    "DIS_LTD":     "Limited (not severely)",
    "DIS_SEV":     "Severely limited",
    "DIS_LTD_SEV": "Limited or severely limited",
}

DISABILITY_ORDER: list[str] = [
    "No disability",
    "Limited (not severely)",
    "Severely limited",
    "Limited or severely limited",
]

# ── Paleta y colores por país ─────────────────────────────────────────────
PALETTE: dict[str, str] = {
    "navy":   "#1F4E79",
    "blue":   "#2E75B6",
    "lblue":  "#BDD7EE",
    "green":  "#1E6B3C",
    "lgreen": "#A9D18E",
    "red":    "#C00000",
    "lred":   "#FF9999",
    "amber":  "#C55A11",
    "gray":   "#595959",
    "lgray":  "#D9D9D9",
}

COUNTRY_COLORS: dict[str, str] = {
    "ES":        PALETTE["blue"],
    "EU27_2020": PALETTE["gray"],
    "DE":        "#7030A0",
    "FR":        "#375623",
    "IT":        PALETTE["amber"],
    "NL":        PALETTE["green"],
    "PT":        "#833C00",
    "SE":        PALETTE["navy"],
    "LT":        PALETTE["red"],   # ← Lituania en rojo (mayor brecha)
}

SOURCE_NOTE = "Fuente: elaboración propia a partir de Eurostat DSB_ICTIU01 (2024)."