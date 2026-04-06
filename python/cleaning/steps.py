"""
cleaning/steps.py — Funciones de limpieza del pipeline.
Cada función es un paso puro (recibe y devuelve DataFrame).
La orquestación está en cleaning/main.py.
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Importar desde config.py (un nivel arriba)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    TARGET_COUNTRIES, CATEGORIES_TO_KEEP,
    COLUMNS_TO_KEEP_RAW, RENAME_MAP, DISABILITY_LEVEL_MAP,
)

log = logging.getLogger(__name__)


# ── Paso 1: Carga ─────────────────────────────────────────────────────────
def load(path: Path) -> pd.DataFrame:
    """Carga el CSV raw sin transformaciones (dtype=str para preservar valores)."""
    if not path.exists():
        raise FileNotFoundError(f"CSV no encontrado: {path}")
    df = pd.read_csv(path, dtype=str)
    log.info("CSV cargado: %d filas × %d columnas desde %s", *df.shape, path.name)
    return df


# ── Paso 2: Inspección ────────────────────────────────────────────────────
def inspect(df: pd.DataFrame) -> None:
    """Diagnóstico del dataset original (solo log, no modifica datos)."""
    n_null_obs = pd.to_numeric(df.get("OBS_VALUE", pd.Series()), errors="coerce").isna().sum()
    flag_vals  = df.get("OBS_FLAG", pd.Series()).value_counts(dropna=False)
    log.info("Nulos en OBS_VALUE: %d | Países únicos: %s",
             n_null_obs,
             sorted(df.get("geo", pd.Series()).dropna().unique().tolist()))
    log.info("OBS_FLAG distribución:\n%s", flag_vals.to_string())


# ── Paso 3: Selección y renombrado ────────────────────────────────────────
def select_rename(df: pd.DataFrame) -> pd.DataFrame:
    """Selecciona las 7 columnas útiles (de 21) y las renombra a snake_case."""
    missing = [c for c in COLUMNS_TO_KEEP_RAW if c not in df.columns]
    if missing:
        raise KeyError(f"Columnas esperadas no encontradas: {missing}")
    return df[COLUMNS_TO_KEEP_RAW].rename(columns=RENAME_MAP)


# ── Paso 4: Filtrado de países ────────────────────────────────────────────
def filter_countries(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra a los 9 países/agregados de interés. Incluye Lituania (LT)."""
    n_before = len(df)
    out = df[df["country_code"].isin(TARGET_COUNTRIES)].copy()
    out["country_name_es"] = out["country_code"].map(TARGET_COUNTRIES)
    log.info("Filtro países: %d → %d filas | países: %s",
             n_before, len(out), sorted(out["country_code"].unique().tolist()))
    return out


# ── Paso 5: Filtrado de categorías ────────────────────────────────────────
def filter_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Mantiene únicamente las 24 categorías de ind_type definidas en config."""
    out = df[df["category_code"].isin(CATEGORIES_TO_KEEP)].copy()
    log.info("Categorías conservadas: %d", out["category_code"].nunique())
    return out


# ── Paso 6: Tratamiento de flags de calidad ───────────────────────────────
def handle_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Procesa OBS_FLAG='u' (baja fiabilidad estadística de Eurostat).
    Crea columna is_reliable (bool): False si flag='u' O valor es nulo.
    Los datos con flag 'u' se CONSERVAN marcados para que el analista
    decida su inclusión según el contexto.
    """
    df["quality_flag"] = df["quality_flag"].fillna("").str.strip()
    df["is_reliable"]  = ~((df["quality_flag"] == "u") | df["pct_internet_use"].isna())

    unreliable = df[~df["is_reliable"]][["country_code", "category_code", "quality_flag"]]
    log.info("Observaciones con is_reliable=False: %d\n%s",
             len(unreliable), unreliable.to_string(index=False))

    df["quality_flag"] = df["quality_flag"].replace("", pd.NA)
    return df


# ── Paso 7: Conversión de tipos ───────────────────────────────────────────
def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte year → Int64, pct_internet_use → float64. Valida rango [0,100]."""
    df["year"]             = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["pct_internet_use"] = pd.to_numeric(df["pct_internet_use"], errors="coerce")

    out_of_range = df[
        df["pct_internet_use"].notna() & ~df["pct_internet_use"].between(0, 100)
    ]
    if not out_of_range.empty:
        log.warning("⚠ Valores fuera de [0,100]: %d observaciones", len(out_of_range))
    else:
        log.info("Rango pct_internet_use: [%.2f, %.2f] ✓",
                 df["pct_internet_use"].min(), df["pct_internet_use"].max())
    return df


# ── Paso 8: Decodificación de ind_type ───────────────────────────────────
def _decode_code(code: str) -> dict:
    """Descompone un código ind_type en sus tres ejes analíticos."""
    remaining = code
    sex = "Total"
    for prefix, label in [("F_", "Female"), ("M_", "Male")]:
        if remaining.startswith(prefix):
            sex, remaining = label, remaining[len(prefix):]
            break
    age_group = "Total"
    for prefix, label in [("Y16_24_", "16-24"), ("Y25_54_", "25-54"), ("Y55_74_", "55-74")]:
        if remaining.startswith(prefix):
            age_group, remaining = label, remaining[len(prefix):]
            break
    return {
        "disability_level": DISABILITY_LEVEL_MAP.get(remaining, remaining),
        "sex":              sex,
        "age_group":        age_group,
    }


def decode_ind_type(df: pd.DataFrame) -> pd.DataFrame:
    """Descompone category_code en columnas: disability_level, sex, age_group."""
    decoded = df["category_code"].apply(_decode_code).apply(pd.Series)
    return pd.concat([df, decoded], axis=1)


# ── Paso 9: Orden final ───────────────────────────────────────────────────
def reorder_sort(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena columnas (identificación → análisis → calidad) y filas."""
    cols = [
        "year", "country_code", "country_name_es", "country_name_en",
        "category_code", "disability_level", "sex", "age_group",
        "category_desc_en", "pct_internet_use",
        "quality_flag", "is_reliable",
    ]
    return (
        df[cols]
        .sort_values(["country_code", "disability_level", "sex", "age_group"])
        .reset_index(drop=True)
    )


# ── Validación del output ─────────────────────────────────────────────────
def validate(df: pd.DataFrame) -> None:
    """Comprueba dimensiones, tipos y coherencia. Lanza AssertionError si falla."""
    n_countries  = len(TARGET_COUNTRIES)
    n_categories = len(CATEGORIES_TO_KEEP)
    expected     = n_countries * n_categories

    assert len(df) == expected, (
        f"Filas: esperadas {expected} ({n_countries} países × {n_categories} "
        f"categorías), obtenidas {len(df)}"
    )
    assert df["country_code"].nunique() == n_countries, \
        f"Número de países incorrecto: {df['country_code'].unique()}"
    assert df["is_reliable"].dtype == bool, "is_reliable debe ser tipo bool"

    valid = df["pct_internet_use"].dropna()
    assert valid.between(0, 100).all(), "Valores fuera de [0,100] en pct_internet_use"

    null_cats = set(df[df["pct_internet_use"].isna()]["category_code"].unique())
    assert null_cats <= {"Y16_24_DIS_SEV"}, \
        f"Nulos inesperados en categorías distintas de Y16_24_DIS_SEV: {null_cats}"

    log.info("✓ Validación superada: %d filas × %d columnas", *df.shape)
