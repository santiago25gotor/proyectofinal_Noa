"""
01_data_cleaning.py
===================
Pipeline completo de limpieza del dataset de Eurostat sobre uso de Internet
por nivel de discapacidad (DSB_ICTIU01, año 2024).

Fuente   : Eurostat – https://ec.europa.eu/eurostat
Indicador: DSB_ICTIU01 v1.0 – "Persons using the internet in the past 12 months
           by level of disability (activity limitation)"
Proyecto : Brecha Digital y Discapacidad en España – Proyecto Final Big Data & IA

Ejecución:
    python 01_data_cleaning.py

Salida:
    data/processed/cleaned_dsb_ictiu01.csv
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import sys
import os
import logging
from pathlib import Path

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DEL LOGGER
# Muestra mensajes con nivel, timestamp y descripción clara en cada paso.
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES Y CONFIGURACIÓN DEL PROYECTO
# Centralizar aquí facilita adaptar el script a nuevos archivos o países.
# ─────────────────────────────────────────────────────────────────────────────

# --- Rutas ---
RAW_FILE    = Path("data/raw/dsb_ictiu01_eurostat_2024.csv")
OUTPUT_DIR  = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "cleaned_dsb_ictiu01.csv"

# Permite ejecutar el script desde cualquier directorio: busca el CSV adjunto
# si la ruta canónica no existe (útil durante el desarrollo).
FALLBACK_RAW = Path("dsb_ictiu01_page_linear_2_0.csv")

# --- Países de interés (códigos ISO Eurostat) ---
# Lithuania (LT) queda excluida según la especificación del proyecto.
TARGET_COUNTRIES: dict[str, str] = {
    "ES":        "España",
    "EU27_2020": "Media UE-27",
    "DE":        "Alemania",
    "FR":        "Francia",
    "IT":        "Italia",
    "PT":        "Portugal",
    "NL":        "Países Bajos",
    "SE":        "Suecia",
}

# --- Categorías de ind_type a conservar ---
# Se mantienen las 24 categorías originales pero se documenta cuáles tienen
# problemas de fiabilidad estadística para que los análisis posteriores puedan
# filtrarlas si es necesario.  La columna 'is_reliable' hace ese trabajo.
# La categoría Y16_24_DIS_SEV se conserva con flag de baja fiabilidad porque
# tiene 4 nulos en los 8 países objetivo; eliminarla aquí ocultaría el problema
# en análisis posteriores.
CATEGORIES_TO_KEEP: list[str] = [
    # --- Totales por nivel de discapacidad (sin desagregación de sexo/edad) ---
    "DIS_NONE",         # Sin discapacidad
    "DIS_LTD",          # Limitación leve
    "DIS_SEV",          # Limitación severa  ← indicador central del proyecto
    "DIS_LTD_SEV",      # Leve o severa (categoría agrupada Eurostat)
    # --- Desagregación por sexo ---
    "F_DIS_NONE",       # Mujeres sin discapacidad
    "F_DIS_LTD",        # Mujeres con limitación leve
    "F_DIS_SEV",        # Mujeres con limitación severa  ← doble vulnerabilidad
    "F_DIS_LTD_SEV",    # Mujeres, leve o severa
    "M_DIS_NONE",       # Hombres sin discapacidad
    "M_DIS_LTD",        # Hombres con limitación leve
    "M_DIS_SEV",        # Hombres con limitación severa
    "M_DIS_LTD_SEV",    # Hombres, leve o severa
    # --- Desagregación por grupo de edad ---
    "Y16_24_DIS_NONE",      # 16-24, sin discapacidad
    "Y16_24_DIS_LTD",       # 16-24, limitación leve
    "Y16_24_DIS_SEV",       # 16-24, limitación severa  ← 4 nulos, baja fiabilidad
    "Y16_24_DIS_LTD_SEV",   # 16-24, leve o severa
    "Y25_54_DIS_NONE",      # 25-54, sin discapacidad
    "Y25_54_DIS_LTD",       # 25-54, limitación leve
    "Y25_54_DIS_SEV",       # 25-54, limitación severa
    "Y25_54_DIS_LTD_SEV",   # 25-54, leve o severa
    "Y55_74_DIS_NONE",      # 55-74, sin discapacidad
    "Y55_74_DIS_LTD",       # 55-74, limitación leve
    "Y55_74_DIS_SEV",       # 55-74, limitación severa  ← intersección crítica
    "Y55_74_DIS_LTD_SEV",   # 55-74, leve o severa
]

# --- Columnas del CSV original que se conservan antes de renombrar ---
# Las 16 columnas restantes son: constantes de metadatos (9), completamente
# nulas (4), o duplicados descriptivos de otras columnas (3).  Todas se descartan.
COLUMNS_TO_KEEP_RAW: list[str] = [
    "TIME_PERIOD",                      # Año de referencia
    "geo",                              # Código ISO del país
    "Geopolitical entity (reporting)",  # Nombre completo del país
    "ind_type",                         # Código de categoría (eje analítico)
    "Individual type",                  # Descripción larga de la categoría
    "OBS_VALUE",                        # Variable central: % de uso de Internet
    "OBS_FLAG",                         # Flag de calidad estadística de Eurostat
]

# --- Mapeo de renombrado: nombre_original → nombre_de_trabajo ---
RENAME_MAP: dict[str, str] = {
    "TIME_PERIOD":                      "year",
    "geo":                              "country_code",
    "Geopolitical entity (reporting)":  "country_name_en",
    "ind_type":                         "category_code",
    "Individual type":                  "category_desc_en",
    "OBS_VALUE":                        "pct_internet_use",
    "OBS_FLAG":                         "quality_flag",
}

# --- Descodificación del eje de discapacidad (extraído de category_code) ---
DISABILITY_LEVEL_MAP: dict[str, str] = {
    "DIS_NONE":    "No disability",
    "DIS_LTD":     "Limited (not severely)",
    "DIS_SEV":     "Severely limited",
    "DIS_LTD_SEV": "Limited or severely limited",
}

# --- Descodificación del eje de sexo ---
SEX_MAP: dict[str, str] = {
    "F_": "Female",
    "M_": "Male",
    "":   "Total",
}

# --- Descodificación del eje de grupo de edad ---
AGE_GROUP_MAP: dict[str, str] = {
    "Y16_24_": "16-24",
    "Y25_54_": "25-54",
    "Y55_74_": "55-74",
    "":        "Total",
}

# --- Nombres de países en español para el análisis ---
COUNTRY_NAMES_ES: dict[str, str] = {
    "ES":        "España",
    "EU27_2020": "Media UE-27",
    "DE":        "Alemania",
    "FR":        "Francia",
    "IT":        "Italia",
    "PT":        "Portugal",
    "NL":        "Países Bajos",
    "SE":        "Suecia",
}


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────

def resolve_input_path() -> Path:
    """
    Devuelve la ruta al archivo CSV raw.
    Busca primero en la ruta canónica del proyecto (data/raw/); si no existe,
    busca el archivo original descargado de Eurostat en el directorio actual.
    Lanza FileNotFoundError si no encuentra ninguno de los dos.
    """
    if RAW_FILE.exists():
        return RAW_FILE
    if FALLBACK_RAW.exists():
        log.warning(
            "Archivo canónico no encontrado en '%s'. "
            "Usando fallback: '%s'.",
            RAW_FILE, FALLBACK_RAW,
        )
        return FALLBACK_RAW
    raise FileNotFoundError(
        f"No se encontró el archivo CSV.\n"
        f"  Ruta esperada : {RAW_FILE.resolve()}\n"
        f"  Ruta fallback : {FALLBACK_RAW.resolve()}\n"
        f"Coloca el archivo descargado de Eurostat en 'data/raw/' y vuelve a ejecutar."
    )


def decode_ind_type(code: str) -> dict[str, str]:
    """
    Decodifica un código ind_type de Eurostat en sus tres ejes analíticos.

    La estructura del código es:   [SEXO_][EDAD_]NIVEL_DISCAPACIDAD
    Ejemplos:
        "DIS_SEV"         → sex=Total,    age=Total, disability=Severely limited
        "F_DIS_SEV"       → sex=Female,   age=Total, disability=Severely limited
        "Y55_74_DIS_SEV"  → sex=Total,    age=55-74, disability=Severely limited
        "M_Y25_54_DIS_LTD"→ No existe; la edad nunca lleva prefijo de sexo en este dataset.

    Parámetros
    ----------
    code : str
        Valor de la columna 'category_code' (ind_type original de Eurostat).

    Retorna
    -------
    dict con claves 'sex', 'age_group', 'disability_level'.
    """
    remaining = code

    # --- Extraer sexo (prefijo F_ o M_) ---
    sex = "Total"
    for prefix, label in [("F_", "Female"), ("M_", "Male")]:
        if remaining.startswith(prefix):
            sex = label
            remaining = remaining[len(prefix):]
            break

    # --- Extraer grupo de edad (prefijo Y16_24_, Y25_54_, Y55_74_) ---
    age_group = "Total"
    for prefix, label in [("Y16_24_", "16-24"), ("Y25_54_", "25-54"), ("Y55_74_", "55-74")]:
        if remaining.startswith(prefix):
            age_group = label
            remaining = remaining[len(prefix):]
            break

    # --- El resto es el código de nivel de discapacidad ---
    disability_level = DISABILITY_LEVEL_MAP.get(remaining, remaining)

    return {
        "sex":               sex,
        "age_group":         age_group,
        "disability_level":  disability_level,
    }


def audit_dataframe(df: pd.DataFrame, label: str) -> None:
    """
    Imprime un resumen de auditoría del DataFrame en el punto actual del pipeline.
    Útil para detectar pérdida inesperada de filas entre transformaciones.
    """
    n_rows, n_cols = df.shape
    n_nulls = int(df["pct_internet_use"].isna().sum()) if "pct_internet_use" in df.columns else -1
    n_flags = int((df.get("quality_flag", pd.Series(dtype=str)) == "u").sum())
    log.info(
        "[%s]  filas=%d  columnas=%d  nulos_valor=%-3s  flags_u=%d",
        label.ljust(28), n_rows, n_cols,
        str(n_nulls) if n_nulls >= 0 else "n/a",
        n_flags,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE DE LIMPIEZA
# Cada función corresponde a un paso numerado del proceso.
# ─────────────────────────────────────────────────────────────────────────────

def step1_load(path: Path) -> pd.DataFrame:
    """
    PASO 1 — Carga del CSV raw.

    Carga el archivo tal como lo exporta Eurostat: 216 filas × 21 columnas.
    No se aplica ninguna transformación en este paso para preservar la
    trazabilidad respecto al archivo original.
    """
    log.info("PASO 1 ─ Cargando archivo: %s", path)
    try:
        df = pd.read_csv(path, dtype=str)   # dtype=str preserva todos los valores
    except Exception as exc:               # captura errores de ruta o formato
        log.error("Error al leer el CSV: %s", exc)
        raise

    log.info("         Dimensiones originales: %d filas × %d columnas", *df.shape)
    log.info("         Columnas: %s", df.columns.tolist())
    return df


def step2_inspect(df: pd.DataFrame) -> None:
    """
    PASO 2 — Inspección y diagnóstico.

    No modifica el DataFrame; solo registra información diagnóstica que queda
    en el log para documentar el estado de los datos originales.
    Esta información debe incorporarse a la Sección 2 del informe final.
    """
    log.info("PASO 2 ─ Inspección del dataset original")

    # Columnas completamente nulas
    all_null = [c for c in df.columns if df[c].isna().all()]
    log.info("         Columnas 100%% nulas (%d): %s", len(all_null), all_null)

    # Columnas constantes (un solo valor único)
    constant = [c for c in df.columns if df[c].nunique(dropna=False) == 1]
    log.info("         Columnas constantes (%d): %s", len(constant), constant)

    # Valores únicos de las dimensiones clave
    log.info("         Países (geo):    %s", sorted(df["geo"].dropna().unique().tolist()))
    log.info("         Indicador:       %s", df["indic_is"].iloc[0])
    log.info("         Unidad:          %s", df["unit"].iloc[0])
    log.info("         Año:             %s", df["TIME_PERIOD"].iloc[0])

    # Valores de OBS_FLAG
    flag_counts = df["OBS_FLAG"].value_counts(dropna=False)
    log.info("         OBS_FLAG:\n%s", flag_counts.to_string())

    # Nulos en OBS_VALUE (ya como float64)
    n_nulls = pd.to_numeric(df["OBS_VALUE"], errors="coerce").isna().sum()
    log.info("         Nulos en OBS_VALUE: %d", n_nulls)


def step3_select_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    PASO 3 — Selección y renombrado de columnas.

    De las 21 columnas originales se conservan 7:
      - 4 completamente nulas  → eliminadas
      - 9 constantes/metadatos → eliminadas (aportan cero variación analítica)
      - 1 duplicado descriptivo de OBS_VALUE → eliminado
      - 1 duplicado descriptivo de OBS_FLAG  → eliminado
    Las 7 conservadas se renombran a nombres de trabajo en snake_case inglés
    para coherencia con convenciones de Python y con los scripts SQL.
    """
    log.info("PASO 3 ─ Selección de columnas útiles y renombrado")

    # Verificar que todas las columnas esperadas existen en el CSV
    missing = [c for c in COLUMNS_TO_KEEP_RAW if c not in df.columns]
    if missing:
        raise KeyError(
            f"Las siguientes columnas esperadas no existen en el CSV: {missing}\n"
            f"Columnas disponibles: {df.columns.tolist()}"
        )

    df = df[COLUMNS_TO_KEEP_RAW].rename(columns=RENAME_MAP)

    log.info("         Columnas conservadas: %s", df.columns.tolist())
    return df


def step4_filter_countries(df: pd.DataFrame) -> pd.DataFrame:
    """
    PASO 4 — Filtrado de países de interés.

    Se conservan 8 entidades geográficas (7 países + el agregado EU27_2020).
    Lithuania (LT) queda excluida del análisis según la especificación del proyecto.
    Se añade la columna 'country_name_es' con los nombres en español para las
    visualizaciones de Python y Power BI.
    """
    log.info("PASO 4 ─ Filtrando países de interés")
    log.info("         Países seleccionados: %s", list(TARGET_COUNTRIES.keys()))

    n_before = len(df)
    df = df[df["country_code"].isin(TARGET_COUNTRIES.keys())].copy()
    n_after = len(df)

    log.info("         Filas eliminadas: %d (Lithuania + cualquier otro país)", n_before - n_after)
    log.info("         Filas restantes:  %d", n_after)

    # Añadir nombre del país en español
    df["country_name_es"] = df["country_code"].map(COUNTRY_NAMES_ES)

    return df


def step5_filter_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    PASO 5 — Filtrado de categorías de ind_type.

    Se conservan las 24 categorías definidas en CATEGORIES_TO_KEEP.
    En este dataset todos los codes del CSV son útiles y están incluidos,
    por lo que este paso actúa como guardia: si en el futuro Eurostat añade
    categorías nuevas no deseadas, este filtro las excluiría automáticamente.
    """
    log.info("PASO 5 ─ Filtrando categorías ind_type")

    n_before = len(df)
    df = df[df["category_code"].isin(CATEGORIES_TO_KEEP)].copy()
    n_after = len(df)

    categories_found = sorted(df["category_code"].unique().tolist())
    log.info("         Categorías conservadas (%d): %s", len(categories_found), categories_found)
    log.info("         Filas eliminadas: %d", n_before - n_after)

    return df


def step6_handle_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    PASO 6 — Tratamiento de flags de calidad de Eurostat.

    El flag 'u' (low reliability) indica que el tamaño muestral subyacente
    es insuficiente para garantizar la fiabilidad estadística del estimador.
    Eurostat lo documenta en: https://ec.europa.eu/eurostat/data/database

    Decisión metodológica:
    - Las observaciones con flag 'u' Y valor disponible se CONSERVAN pero se
      marcan con is_reliable=False. Los análisis posteriores pueden filtrarlas
      o incluirlas con advertencia según el contexto.
    - Las observaciones con flag 'u' Y valor nulo se CONSERVAN igualmente con
      is_reliable=False. No se imputan; la ausencia del dato es información.
    - Esta estrategia preserva la trazabilidad y documenta el problema de forma
      explícita en el dataset limpio.

    Resumen de flags en los 8 países objetivo (sin Lithuania):
      - 12 observaciones con flag 'u'
      - 4 con flag 'u' Y valor nulo (todas en Y16_24_DIS_SEV: ES, FR, NL, SE)
      - 8 con flag 'u' Y valor disponible (usar con precaución)
    """
    log.info("PASO 6 ─ Tratamiento de flags de calidad Eurostat")

    # Estandarizar: NaN → cadena vacía para facilitar comparaciones
    df["quality_flag"] = df["quality_flag"].fillna("").str.strip()

    # Columna booleana de fiabilidad
    # is_reliable=False si: flag=='u' O valor es nulo
    df["is_reliable"] = ~(
        (df["quality_flag"] == "u") | df["pct_internet_use"].isna()
    )

    # Log detallado de observaciones problemáticas
    unreliable = df[~df["is_reliable"]][
        ["country_code", "category_code", "pct_internet_use", "quality_flag"]
    ].sort_values(["category_code", "country_code"])

    log.info(
        "         Observaciones con is_reliable=False (%d):\n%s",
        len(unreliable),
        unreliable.to_string(index=False),
    )

    # Restaurar NaN donde quality_flag quedó como cadena vacía (más limpio)
    df["quality_flag"] = df["quality_flag"].replace("", pd.NA)

    return df


def step7_handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    PASO 7 — Tratamiento de valores faltantes en pct_internet_use.

    Todos los nulos en este dataset corresponden a la categoría Y16_24_DIS_SEV
    (jóvenes 16-24 con discapacidad severa) en 4 países: ES, FR, NL, SE.
    Eurostat no publicó el dato porque la muestra subyacente era demasiado
    pequeña para ser estadísticamente significativa.

    Decisión metodológica:
    - Los nulos NO se imputan. Imputar estimadores no fiables introduciría
      sesgos en el análisis comparativo, que es el objetivo central del proyecto.
    - Los nulos se dejan como NaN y quedan marcados con is_reliable=False
      (paso anterior). Los análisis que usen Y16_24_DIS_SEV deben excluir o
      advertir sobre estas observaciones.
    """
    log.info("PASO 7 ─ Diagnóstico de valores faltantes")

    null_rows = df[df["pct_internet_use"].isna()][
        ["country_code", "category_code", "pct_internet_use", "quality_flag"]
    ]
    log.info(
        "         Filas con pct_internet_use=NaN (%d) — NO se imputan:\n%s",
        len(null_rows),
        null_rows.to_string(index=False),
    )
    log.info(
        "         Todas corresponden a Y16_24_DIS_SEV (muestra insuficiente en Eurostat)."
    )

    return df


def step8_convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    PASO 8 — Conversión de tipos de datos.

    Al cargar con dtype=str todos los campos llegaron como objeto/string.
    Aquí se asignan los tipos correctos:
      - year               : int   (solo existe 2024, pero se tipifica correctamente)
      - pct_internet_use   : float (porcentaje 0-100, permite NaN)
      - is_reliable        : bool  (ya es bool tras el paso 6)
      - Resto              : str   (ya son str, no requieren conversión)
    """
    log.info("PASO 8 ─ Conversión de tipos de datos")

    # year: entero
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # pct_internet_use: float (pd.to_numeric gestiona NaN automáticamente)
    df["pct_internet_use"] = pd.to_numeric(df["pct_internet_use"], errors="coerce")

    # Verificar rango lógico: los porcentajes deben estar entre 0 y 100
    out_of_range = df[
        df["pct_internet_use"].notna()
        & ~df["pct_internet_use"].between(0, 100)
    ]
    if not out_of_range.empty:
        log.warning(
            "         ¡ALERTA! %d valores fuera del rango [0, 100]:\n%s",
            len(out_of_range),
            out_of_range[["country_code", "category_code", "pct_internet_use"]].to_string(index=False),
        )
    else:
        log.info(
            "         Rango de pct_internet_use: [%.2f, %.2f] — todos dentro de [0, 100].",
            df["pct_internet_use"].min(),
            df["pct_internet_use"].max(),
        )

    log.info("         Tipos finales:\n%s", df.dtypes.to_string())

    return df


def step9_decode_ind_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    PASO 9 — Decodificación de ind_type en tres columnas analíticas.

    El código ind_type de Eurostat combina tres ejes en una sola cadena:
    [SEXO_][EDAD_]NIVEL_DISCAPACIDAD

    Este paso lo descompone en columnas independientes:
      - sex              : Total / Female / Male
      - age_group        : Total / 16-24 / 25-54 / 55-74
      - disability_level : No disability / Limited (not severely) /
                           Severely limited / Limited or severely limited

    Las columnas category_code y category_desc_en se conservan como referencia
    al código original de Eurostat para trazabilidad.
    """
    log.info("PASO 9 ─ Decodificando ind_type en columnas analíticas")

    decoded = df["category_code"].apply(decode_ind_type).apply(pd.Series)
    df = pd.concat([df, decoded], axis=1)

    # Verificar que todos los códigos se decodificaron correctamente
    unknown_levels = df[
        df["disability_level"].isin(DISABILITY_LEVEL_MAP.values()) == False
    ]["disability_level"].unique()
    if len(unknown_levels) > 0:
        log.warning("         Niveles de discapacidad no reconocidos: %s", unknown_levels)
    else:
        log.info("         Todos los códigos decodificados correctamente.")

    # Distribución de la decodificación
    log.info(
        "         Distribución sex:\n%s",
        df["sex"].value_counts().to_string(),
    )
    log.info(
        "         Distribución age_group:\n%s",
        df["age_group"].value_counts().to_string(),
    )
    log.info(
        "         Distribución disability_level:\n%s",
        df["disability_level"].value_counts().to_string(),
    )

    return df


def step10_reorder_and_sort(df: pd.DataFrame) -> pd.DataFrame:
    """
    PASO 10 — Reordenación de columnas y ordenación de filas.

    Columnas ordenadas de más general a más específico:
    1. Metadatos de identificación (año, país)
    2. Código de categoría + decodificación analítica
    3. Variable central (porcentaje de uso)
    4. Metadatos de calidad

    Filas ordenadas por: país → nivel de discapacidad → sexo → edad.
    Este orden facilita la lectura directa del CSV y las consultas SQL.
    """
    log.info("PASO 10 ─ Reordenación de columnas y filas")

    # Orden final de columnas
    column_order = [
        # Identificación
        "year",
        "country_code",
        "country_name_es",
        "country_name_en",
        # Categoría analítica
        "category_code",        # Código Eurostat original (referencia)
        "disability_level",     # Eje 1: nivel de discapacidad
        "sex",                  # Eje 2: sexo
        "age_group",            # Eje 3: grupo de edad
        "category_desc_en",     # Descripción completa en inglés (Eurostat)
        # Variable central
        "pct_internet_use",     # % individuos que usaron Internet (variable dependiente)
        # Calidad
        "quality_flag",         # Flag original de Eurostat ('u' = baja fiabilidad)
        "is_reliable",          # Indicador booleano de fiabilidad (True/False)
    ]

    # Verificar que no falta ninguna columna esperada
    missing_cols = [c for c in column_order if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columnas esperadas no encontradas tras el pipeline: {missing_cols}")

    df = df[column_order]

    # Ordenar filas
    sort_order = ["country_code", "disability_level", "sex", "age_group"]
    df = df.sort_values(sort_order).reset_index(drop=True)

    return df


def step11_validate_output(df: pd.DataFrame) -> None:
    """
    PASO 11 — Validación del dataset limpio.

    Comprueba que el output cumple las expectativas antes de guardarlo.
    Lanza AssertionError con mensaje descriptivo si algo no cuadra.
    """
    log.info("PASO 11 ─ Validación del dataset limpio")

    # Dimensiones esperadas: 8 países × 24 categorías = 192 filas
    expected_rows = len(TARGET_COUNTRIES) * len(CATEGORIES_TO_KEEP)
    assert len(df) == expected_rows, (
        f"Número de filas incorrecto: esperado {expected_rows}, obtenido {len(df)}"
    )

    # Número de países
    assert df["country_code"].nunique() == len(TARGET_COUNTRIES), (
        f"Número de países incorrecto: {df['country_code'].unique()}"
    )

    # Número de categorías
    assert df["category_code"].nunique() == len(CATEGORIES_TO_KEEP), (
        f"Número de categorías incorrecto: {df['category_code'].unique()}"
    )

    # Lithuania no debe estar presente
    assert "LT" not in df["country_code"].values, "Lithuania no debe estar en el dataset limpio."

    # Rango de pct_internet_use (solo valores no nulos)
    valid = df["pct_internet_use"].dropna()
    assert valid.between(0, 100).all(), "Valores fuera de rango [0, 100] en pct_internet_use."

    # is_reliable es booleano
    assert df["is_reliable"].dtype == bool, "La columna is_reliable debe ser de tipo bool."

    # Nulos restantes solo en Y16_24_DIS_SEV
    null_categories = df[df["pct_internet_use"].isna()]["category_code"].unique()
    assert set(null_categories) <= {"Y16_24_DIS_SEV"}, (
        f"Nulos inesperados en categorías distintas de Y16_24_DIS_SEV: {null_categories}"
    )

    log.info(
        "         ✓ Todas las validaciones superadas. "
        "Dataset listo: %d filas × %d columnas.",
        *df.shape,
    )


def step12_save(df: pd.DataFrame) -> None:
    """
    PASO 12 — Guardado del dataset limpio.

    Crea el directorio de salida si no existe y guarda el CSV sin índice.
    El archivo resultante es la fuente de datos para todos los análisis
    posteriores: notebooks de Python, queries SQL y conexión con Power BI.
    """
    log.info("PASO 12 ─ Guardando dataset limpio")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    file_size_kb = OUTPUT_FILE.stat().st_size / 1024
    log.info("         Archivo guardado: %s", OUTPUT_FILE.resolve())
    log.info("         Tamaño: %.1f KB", file_size_kb)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def main() -> pd.DataFrame:
    """
    Ejecuta el pipeline completo de limpieza en orden secuencial.
    Retorna el DataFrame limpio para uso interactivo (p. ej. en un notebook).
    """
    log.info("=" * 70)
    log.info("INICIO DEL PIPELINE DE LIMPIEZA — DSB_ICTIU01 (Eurostat 2024)")
    log.info("=" * 70)

    # Resolver ruta del archivo de entrada
    input_path = resolve_input_path()

    # ── Pipeline ─────────────────────────────────────────────────────────────
    df = step1_load(input_path)
    step2_inspect(df)

    df = step3_select_rename_columns(df)
    df = step4_filter_countries(df)
    df = step5_filter_categories(df)
    df = step6_handle_quality_flags(df)
    df = step7_handle_missing_values(df)
    df = step8_convert_types(df)
    df = step9_decode_ind_type(df)
    df = step10_reorder_and_sort(df)

    # Auditoría del estado final antes de validar
    audit_dataframe(df, "Dataset limpio final")

    step11_validate_output(df)
    step12_save(df)

    log.info("=" * 70)
    log.info("PIPELINE COMPLETADO CON ÉXITO")
    log.info("  Output : %s", OUTPUT_FILE.resolve())
    log.info("  Filas  : %d", len(df))
    log.info("  Columnas: %d  →  %s", len(df.columns), df.columns.tolist())
    log.info("  Nulos en pct_internet_use: %d (solo Y16_24_DIS_SEV)", df["pct_internet_use"].isna().sum())
    log.info("  Observaciones con is_reliable=False: %d", (~df["is_reliable"]).sum())
    log.info("=" * 70)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        df_clean = main()
    except FileNotFoundError as e:
        log.error("ARCHIVO NO ENCONTRADO:\n%s", e)
        sys.exit(1)
    except AssertionError as e:
        log.error("VALIDACIÓN FALLIDA: %s", e)
        sys.exit(2)
    except Exception as e:
        log.exception("ERROR INESPERADO: %s", e)
        sys.exit(99)


# ─────────────────────────────────────────────────────────────────────────────
# RESUMEN DEL SCRIPT
# ─────────────────────────────────────────────────────────────────────────────
"""
QUÉ HACE ESTE SCRIPT
════════════════════

Carga el CSV original de Eurostat (DSB_ICTIU01, 2024) con 216 filas y 21
columnas y produce un dataset limpio con 192 filas y 12 columnas, listo para
el análisis comparativo de la brecha digital por discapacidad en España.

PASOS DEL PIPELINE
──────────────────
  1. Carga          Importa el CSV con dtype=str para no perder ningún valor.
  2. Inspección     Registra columnas nulas, constantes y distribución de flags.
  3. Columnas       De 21 columnas conserva 7 y las renombra a snake_case.
                    Eliminadas: 4 completamente nulas + 9 constantes de
                    metadatos + 1 duplicado de OBS_VALUE + 0 de OBS_FLAG.
  4. Países         Filtra a 8 entidades: ES, EU27_2020, DE, FR, IT, PT, NL, SE.
                    Lithuania queda excluida.
  5. Categorías     Verifica que las 24 categorías de ind_type están presentes.
  6. Flags          Procesa el flag 'u' de Eurostat (low reliability).
                    Crea columna booleana is_reliable para filtrado posterior.
  7. Nulos          Documenta 4 nulos en Y16_24_DIS_SEV. No se imputan.
  8. Tipos          Convierte year→Int64, pct_internet_use→float64.
                    Verifica el rango [0, 100].
  9. Decodificación Descompone ind_type en 3 columnas: disability_level,
                    sex, age_group. Facilita GROUP BY y filtros analíticos.
 10. Orden          Reordena columnas (identificación → análisis → calidad)
                    y filas (country_code → disability_level → sex → age_group).
 11. Validación     Assertions automáticas: dimensiones, rango, tipos,
                    ausencia de Lithuania, nulos solo en Y16_24_DIS_SEV.
 12. Guardado       Exporta a data/processed/cleaned_dsb_ictiu01.csv.

COLUMNAS DEL DATASET LIMPIO
────────────────────────────
  year              int    Año de referencia (2024)
  country_code      str    Código ISO (ES, DE, FR, …)
  country_name_es   str    Nombre en español
  country_name_en   str    Nombre en inglés (Eurostat)
  category_code     str    Código ind_type original (trazabilidad)
  disability_level  str    Nivel de discapacidad decodificado
  sex               str    Sexo decodificado (Total / Female / Male)
  age_group         str    Grupo de edad decodificado (Total / 16-24 / …)
  category_desc_en  str    Descripción larga en inglés (Eurostat)
  pct_internet_use  float  % que usó Internet en últimos 12 meses (0-100)
  quality_flag      str    Flag Eurostat ('u' = baja fiabilidad, NaN = OK)
  is_reliable       bool   True si el dato es estadísticamente fiable

DECISIONES METODOLÓGICAS DOCUMENTADAS
──────────────────────────────────────
  • Los 4 nulos en Y16_24_DIS_SEV NO se imputan: representan ausencia real
    de dato fiable, no errores del pipeline.
  • Las 8 observaciones con flag 'u' y valor disponible SE CONSERVAN marcadas
    con is_reliable=False para que el analista decida caso a caso.
  • Lithuania se excluye desde el filtrado de países (paso 4).
  • EU27_2020 se trata como entidad de referencia, no como país en clustering.
"""
