"""
02_feature_engineering.py
=========================
Feature engineering sobre el dataset limpio del proyecto.
Construye variables analíticas derivadas para responder a las cuatro preguntas
de investigación y preparar los datos para SQL y Power BI.

Proyecto : Brecha Digital y Discapacidad en España – Proyecto Final Big Data & IA
Fuente   : Eurostat DSB_ICTIU01 v1.0 (2024) – limpiado por 01_data_cleaning.py

Ejecución:
    python python/02_feature_engineering.py

Entradas:
    data/processed/cleaned_dsb_ictiu01.csv

Salidas:
    data/processed/analytical_dsb_ictiu01.csv   ← dataset fila a fila enriquecido
    data/processed/summary_by_country.csv        ← una fila por país (para clustering/PBI)
    data/processed/summary_spain.csv             ← perfil completo de España
    data/processed/summary_europe_comparison.csv ← tabla comparativa Europa
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# LOGGER
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# RUTAS
# ─────────────────────────────────────────────────────────────────────────────
INPUT_FILE   = Path("data/processed/cleaned_dsb_ictiu01.csv")
OUTPUT_DIR   = Path("data/processed")

# Archivos de salida
OUT_ANALYTICAL  = OUTPUT_DIR / "analytical_dsb_ictiu01.csv"
OUT_BY_COUNTRY  = OUTPUT_DIR / "summary_by_country.csv"
OUT_SPAIN       = OUTPUT_DIR / "summary_spain.csv"
OUT_EUROPE      = OUTPUT_DIR / "summary_europe_comparison.csv"

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES ANALÍTICAS
# ─────────────────────────────────────────────────────────────────────────────

# EU27_2020 es un agregado estadístico, no un país.
# Se usa como referencia en variables de posición relativa, pero se excluye
# del clustering y de los rankings de países individuales.
EU27_CODE = "EU27_2020"

# Valores fijos de la media UE-27 extraídos del dataset limpio
# (Total sexo, Total edad, Eurostat 2024).
# Se definen como constantes para que las fórmulas de posición relativa
# no dependan de que EU27_2020 esté presente en cada subconjunto.
EU27_NO_DISABILITY    = 95.22   # DIS_NONE
EU27_SEVERELY_LIMITED = 82.29   # DIS_SEV
EU27_GAP_TOTAL        = EU27_NO_DISABILITY - EU27_SEVERELY_LIMITED  # 12.93 pp

# Orden lógico de los niveles de discapacidad (de menor a mayor limitación)
DISABILITY_ORDER = [
    "No disability",
    "Limited (not severely)",
    "Severely limited",
    "Limited or severely limited",  # categoría agrupada (DIS_LTD_SEV)
]

# Orden lógico de grupos de edad
AGE_ORDER = ["16-24", "25-54", "55-74", "Total"]


# ─────────────────────────────────────────────────────────────────────────────
# PASO 1 — Carga del dataset limpio
# ─────────────────────────────────────────────────────────────────────────────
def load_clean_data(path: Path) -> pd.DataFrame:
    """
    Carga el CSV producido por 01_data_cleaning.py.
    Verifica que las columnas esperadas estén presentes y que los tipos
    sean correctos antes de empezar el feature engineering.
    """
    log.info("PASO 1 ─ Cargando dataset limpio: %s", path)

    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo '{path}'.\n"
            f"Ejecuta primero: python python/01_data_cleaning.py"
        )

    df = pd.read_csv(path)

    # Columnas esperadas del paso de limpieza
    required_cols = [
        "year", "country_code", "country_name_es", "country_name_en",
        "category_code", "disability_level", "sex", "age_group",
        "pct_internet_use", "quality_flag", "is_reliable",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Columnas faltantes en el input: {missing}")

    # Asegurar tipos correctos tras la carga CSV
    df["is_reliable"] = df["is_reliable"].astype(bool)
    df["pct_internet_use"] = pd.to_numeric(df["pct_internet_use"], errors="coerce")

    log.info("         Dimensiones: %d filas × %d columnas", *df.shape)
    log.info("         Países: %s", sorted(df["country_code"].unique().tolist()))
    log.info("         Observaciones fiables: %d / %d",
             df["is_reliable"].sum(), len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 2 — Variables de contexto y clasificación
# ─────────────────────────────────────────────────────────────────────────────
def add_context_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    NUEVAS VARIABLES:
    ─────────────────
    is_eu27_aggregate  bool
        True si el registro pertenece al agregado EU27_2020.
        Permite excluirlo fácilmente en clustering y rankings de países.

    is_total_sex  bool
        True si sex == 'Total' (sin desagregación por sexo).
        Filtra rápidamente el análisis principal sin desagregación.

    is_total_age  bool
        True si age_group == 'Total' (sin desagregación por edad).
        Combinado con is_total_sex da la fila de referencia por país y
        nivel de discapacidad.

    is_core_row  bool
        True cuando sex == 'Total' AND age_group == 'Total'.
        Estas 4 filas por país (una por nivel de discapacidad) son el núcleo
        del análisis comparativo europeo.

    disability_rank  int
        Ordenación numérica del nivel de discapacidad:
          0 = No disability (máximo uso esperado)
          1 = Limited (not severely)
          2 = Severely limited  (foco del análisis)
          3 = Limited or severely limited (categoría agrupada)
        Permite ordenar gráficos y tablas sin depender de orden alfabético.

    pct_excluded  float
        100 − pct_internet_use: porcentaje de personas que NO usan Internet.
        Variable de exclusión digital directamente interpretable.
        Solo se calcula cuando pct_internet_use no es nulo.
    """
    log.info("PASO 2 ─ Añadiendo variables de contexto y clasificación")

    # Identificadores de subconjuntos
    df["is_eu27_aggregate"] = df["country_code"] == EU27_CODE
    df["is_total_sex"]      = df["sex"] == "Total"
    df["is_total_age"]      = df["age_group"] == "Total"
    df["is_core_row"]       = df["is_total_sex"] & df["is_total_age"]

    # Rango ordinal del nivel de discapacidad
    rank_map = {level: i for i, level in enumerate(DISABILITY_ORDER)}
    df["disability_rank"] = df["disability_level"].map(rank_map)

    # Porcentaje excluido digitalmente
    df["pct_excluded"] = (100 - df["pct_internet_use"]).round(4)

    log.info("         is_core_row=True:   %d filas (4 niveles × 8 países)",
             df["is_core_row"].sum())
    log.info("         is_eu27_aggregate:  %d filas", df["is_eu27_aggregate"].sum())
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 3 — Brecha digital por país (gap_vs_no_disability)
# ─────────────────────────────────────────────────────────────────────────────
def add_gap_vs_no_disability(df: pd.DataFrame) -> pd.DataFrame:
    """
    NUEVA VARIABLE:
    ───────────────
    gap_vs_no_disability  float
        Para cada combinación (país, sexo, edad), diferencia entre el porcentaje
        de personas SIN discapacidad y el porcentaje de personas con el nivel de
        discapacidad de esa fila.

        Fórmula:
            gap = pct_internet_use[disability=No disability, mismo sexo, misma edad]
                − pct_internet_use[fila actual]

        Interpretación:
          - Para filas con disability_level = "No disability": gap = 0 (referencia)
          - Para disability_level = "Severely limited": gap es la brecha principal
          - Positivo → las personas sin discapacidad usan más Internet que este grupo
          - Valores grandes indican mayor exclusión relativa

        LIMITACIÓN: Si el valor de referencia (No disability) o el valor de la fila
        son NaN (baja fiabilidad), el gap también será NaN. Esto ocurre solo en
        Y16_24_DIS_SEV para ES, FR, NL, SE.
    """
    log.info("PASO 3 ─ Calculando brecha vs. 'No disability' por combinación país/sexo/edad")

    # Extraer los valores de referencia: No disability por (country, sex, age_group)
    ref = (
        df[df["disability_level"] == "No disability"]
        [["country_code", "sex", "age_group", "pct_internet_use"]]
        .rename(columns={"pct_internet_use": "pct_no_disability"})
    )

    # Merge con el dataset completo
    df = df.merge(ref, on=["country_code", "sex", "age_group"], how="left")

    # Calcular la brecha
    df["gap_vs_no_disability"] = (
        df["pct_no_disability"] - df["pct_internet_use"]
    ).round(4)

    # La variable solo tiene sentido para filas que no son "No disability" misma
    # (donde sería 0 por definición); se deja el 0 para coherencia estructural.

    n_calculable = df["gap_vs_no_disability"].notna().sum()
    log.info("         gap_vs_no_disability calculado en %d / %d filas",
             n_calculable, len(df))
    log.info("         Rango: [%.2f, %.2f]",
             df["gap_vs_no_disability"].min(),
             df["gap_vs_no_disability"].max())
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 4 — Posición relativa respecto a la media UE-27
# ─────────────────────────────────────────────────────────────────────────────
def add_eu27_relative_position(df: pd.DataFrame) -> pd.DataFrame:
    """
    NUEVAS VARIABLES:
    ─────────────────
    pct_vs_eu27  float
        Diferencia entre el porcentaje de uso de Internet de la fila y
        el valor equivalente de la media UE-27 (mismo disability_level,
        mismo sex, mismo age_group).

        Fórmula:  pct_vs_eu27 = pct_internet_use − pct_eu27_equivalent

        Interpretación:
          - Positivo → el país usa más Internet que la media UE-27 en esa categoría
          - Negativo → el país está por debajo de la media UE-27
          - Para EU27_2020 mismo: siempre 0 (se compara consigo mismo)

    gap_vs_eu27  float
        Diferencia entre la brecha digital total del país (No disability −
        Severely limited, Total sexo/edad) y la brecha media de la UE-27.
        Esta variable solo tiene valor en las filas is_core_row=True.

        Fórmula:
            gap_vs_eu27 = gap_vs_no_disability[fila] − EU27_GAP_TOTAL

        Interpretación:
          - Positivo → el país tiene MÁS brecha que la media europea
          - España: +5.33 pp (brecha mucho peor que la media UE)
          - Países Bajos: −11.88 pp (brecha mucho mejor que la media UE)
    """
    log.info("PASO 4 ─ Calculando posición relativa vs. media UE-27")

    # Extraer todos los valores UE-27 como tabla de referencia
    eu27_ref = (
        df[df["country_code"] == EU27_CODE]
        [["disability_level", "sex", "age_group", "pct_internet_use"]]
        .rename(columns={"pct_internet_use": "pct_eu27_equivalent"})
    )

    # Merge para añadir el valor UE-27 equivalente a cada fila
    df = df.merge(
        eu27_ref,
        on=["disability_level", "sex", "age_group"],
        how="left",
    )

    # Variable 1: diferencia del porcentaje de uso vs. UE-27
    df["pct_vs_eu27"] = (
        df["pct_internet_use"] - df["pct_eu27_equivalent"]
    ).round(4)

    # Variable 2: diferencia de brecha vs. brecha media UE-27
    # Solo aplicable en filas core (Total sex, Total age, Severely limited)
    # donde gap_vs_no_disability representa la brecha principal del país.
    # Para el resto de filas se deja NaN — no tiene interpretación comparable.
    mask_sev_core = (
        (df["disability_level"] == "Severely limited")
        & df["is_core_row"]
    )
    df["gap_vs_eu27"] = np.where(
        mask_sev_core,
        (df["gap_vs_no_disability"] - EU27_GAP_TOTAL).round(4),
        np.nan,
    )

    n_pct = df["pct_vs_eu27"].notna().sum()
    n_gap = df["gap_vs_eu27"].notna().sum()
    log.info("         pct_vs_eu27 calculado en %d filas", n_pct)
    log.info("         gap_vs_eu27 calculado en %d filas (solo Severely limited core)",
             n_gap)

    # Vista rápida para verificar España
    es_sev_core = df[
        (df["country_code"] == "ES")
        & mask_sev_core
    ][["country_code", "pct_internet_use", "gap_vs_no_disability",
       "gap_vs_eu27"]]
    log.info("         España (Severely limited / Total / Total):\n%s",
             es_sev_core.to_string(index=False))

    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 5 — Intensidad de exclusión (severity_score)
# ─────────────────────────────────────────────────────────────────────────────
def add_severity_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    NUEVA VARIABLE:
    ───────────────
    severity_score  float  [0 – 100]
        Índice de severidad de la exclusión digital para cada fila.
        Se calcula como el porcentaje de personas excluidas (pct_excluded)
        normalizado sobre el máximo teórico de exclusión del nivel de
        discapacidad en el dataset (valor máximo de pct_excluded observado
        en ese nivel, entre todos los países fiables).

        Fórmula:
            severity_score = (pct_excluded / max_pct_excluded_en_nivel) × 100

        Interpretación:
          - 100 → el grupo/país con la mayor exclusión observada en ese nivel
          - 0   → ninguna exclusión (pct_internet_use = 100 %)
          - Permite comparar la severidad relativa entre grupos con distintos
            niveles de discapacidad sin que la escala absoluta distorsione.

        NOTA: Se calcula solo sobre filas is_reliable=True para evitar que
        valores con baja fiabilidad estadística actúen como máximo de referencia.
    """
    log.info("PASO 5 ─ Calculando severity_score (índice de exclusión relativa)")

    # Máximo de pct_excluded por nivel de discapacidad (solo filas fiables)
    max_excluded = (
        df[df["is_reliable"]]
        .groupby("disability_level")["pct_excluded"]
        .max()
        .rename("max_pct_excluded")
    )

    df = df.merge(max_excluded, on="disability_level", how="left")

    # Calcular el score (evitar división por cero con replace)
    df["severity_score"] = (
        df["pct_excluded"] / df["max_pct_excluded"].replace(0, np.nan) * 100
    ).round(2)

    # Limpiar columna auxiliar
    df.drop(columns=["max_pct_excluded"], inplace=True)

    log.info("         severity_score — rango: [%.2f, %.2f]",
             df["severity_score"].min(),
             df["severity_score"].max())
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 6 — Etiqueta de posición relativa entre países
# ─────────────────────────────────────────────────────────────────────────────
def add_country_position_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    NUEVAS VARIABLES:
    ─────────────────
    country_rank_by_gap  Int64  (solo en filas is_core_row + Severely limited)
        Ranking de países ordenados por brecha total descendente (mayor brecha
        = peor posición = rank 1). EU27_2020 queda excluido del ranking.

        Permite que Power BI muestre directamente "España está en posición X
        de Y países" sin necesidad de calcular el ranking en DAX.

    inclusion_group  str  (solo en filas is_core_row + Severely limited)
        Categorización cualitativa del nivel de inclusión digital basada en
        el gap_vs_no_disability:
          "Alta inclusión"       → gap < 5 pp   (NL: 1.05, SE: 4.72)
          "Inclusión media"      → gap 5–12 pp  (FR: 9.36, PT: 7.26, DE: 11.05)
          "Baja inclusión"       → gap 12–20 pp (ES: 18.26, IT: 18.27, EU27: 12.93)
          "Muy baja inclusión"   → gap > 20 pp  (ningún país en este dataset)

        Los umbrales están definidos sobre los datos observados para maximizar
        la separación entre grupos. Son descriptivos, no normativos.
    """
    log.info("PASO 6 ─ Añadiendo ranking y etiqueta de inclusión por país")

    # Subconjunto: filas core + Severely limited + excluir EU27
    mask = (
        (df["disability_level"] == "Severely limited")
        & df["is_core_row"]
        & ~df["is_eu27_aggregate"]
    )

    # Ranking por brecha (mayor gap = peor posición = rank más alto numéricamente)
    gap_series = df.loc[mask, "gap_vs_no_disability"].rank(
        ascending=False, method="min"
    ).astype("Int64")
    df["country_rank_by_gap"] = pd.NA
    df.loc[mask, "country_rank_by_gap"] = gap_series

    # Etiqueta de grupo de inclusión
    def inclusion_label(gap: float) -> str:
        if pd.isna(gap):
            return pd.NA
        if gap < 5:
            return "Alta inclusión"
        elif gap < 12:
            return "Inclusión media"
        elif gap <= 20:
            return "Baja inclusión"
        else:
            return "Muy baja inclusión"

    df["inclusion_group"] = pd.NA
    df.loc[mask, "inclusion_group"] = df.loc[mask, "gap_vs_no_disability"].apply(
        inclusion_label
    )

    # Vista de verificación
    check = df[mask][
        ["country_code", "country_name_es", "gap_vs_no_disability",
         "country_rank_by_gap", "inclusion_group"]
    ].sort_values("country_rank_by_gap")
    log.info("         Ranking de países por brecha:\n%s", check.to_string(index=False))

    return df


# ─────────────────────────────────────────────────────────────────────────────
# PASO 7 — Tabla resumen por país (una fila por país)
# ─────────────────────────────────────────────────────────────────────────────
def build_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye una tabla con UNA FILA POR PAÍS con todas las métricas clave.
    Esta tabla es el input directo para:
      - El clustering K-Means (python/05_clustering_paises.ipynb)
      - Las tarjetas KPI y el mapa coroplético de Power BI
      - Las queries de ranking en SQL

    COLUMNAS DE LA TABLA RESUMEN:
    ──────────────────────────────
    country_code, country_name_es, country_name_en
        Identificadores del país.

    pct_no_disability
        % uso Internet — sin discapacidad (Total sexo, Total edad).
        Denominador de la brecha.

    pct_severely_limited
        % uso Internet — discapacidad severa (Total sexo, Total edad).
        Numerador central del análisis.

    pct_limited_not_severely
        % uso Internet — limitación leve (Total sexo, Total edad).
        Brecha intermedia.

    pct_limited_or_severely
        % uso Internet — leve o severa agrupada (Total sexo, Total edad).
        Indicador oficial agrupado de Eurostat.

    gap_total
        Brecha digital principal: pct_no_disability − pct_severely_limited.
        Variable dependiente central del proyecto.

    pct_excluded_severely
        % personas con discapacidad severa excluidas digitalmente (100 − pct_severely_limited).

    pct_female_severely
        % uso Internet — mujeres con discapacidad severa (Total edad).
        Indicador de doble vulnerabilidad.

    pct_male_severely
        % uso Internet — hombres con discapacidad severa (Total edad).

    gap_gender
        Brecha de género dentro de discapacidad severa: pct_male − pct_female.
        Positivo → hombres usan más. Negativo → mujeres usan más.

    pct_25_54_severely
        % uso Internet — adultos 25-54 con discapacidad severa.

    pct_55_74_severely
        % uso Internet — mayores 55-74 con discapacidad severa.
        Intersección crítica: envejecimiento + discapacidad.

    gap_age
        Brecha generacional: pct_25_54_severely − pct_55_74_severely.
        Mayor valor = mayor efecto del envejecimiento sobre la exclusión digital.

    gap_vs_eu27
        Diferencia entre la brecha del país y la media UE-27 (12.93 pp).
        Positivo → peor que la media europea.

    inclusion_group
        Categoría cualitativa de inclusión digital.

    country_rank_by_gap
        Posición en el ranking de brecha (1 = mayor brecha = peor posición).

    is_eu27_aggregate
        Flag para excluir EU27_2020 del clustering.
    """
    log.info("PASO 7 ─ Construyendo tabla resumen por país")

    records = []

    for country in df["country_code"].unique():
        sub = df[df["country_code"] == country]

        # ── Helpers para extraer un valor específico ──────────────────────
        def get_val(disability: str, sex: str = "Total",
                    age: str = "Total") -> float:
            """Extrae pct_internet_use para una combinación exacta."""
            row = sub[
                (sub["disability_level"] == disability)
                & (sub["sex"] == sex)
                & (sub["age_group"] == age)
            ]["pct_internet_use"]
            return float(row.iloc[0]) if len(row) > 0 and not row.isna().all() else np.nan

        def get_reliable(disability: str, sex: str = "Total",
                         age: str = "Total") -> bool:
            """Retorna True si la observación es fiable."""
            row = sub[
                (sub["disability_level"] == disability)
                & (sub["sex"] == sex)
                & (sub["age_group"] == age)
            ]["is_reliable"]
            return bool(row.iloc[0]) if len(row) > 0 else False

        # ── Valores base ──────────────────────────────────────────────────
        pct_none   = get_val("No disability")
        pct_sev    = get_val("Severely limited")
        pct_ltd    = get_val("Limited (not severely)")
        pct_ltd_s  = get_val("Limited or severely limited")
        pct_f_sev  = get_val("Severely limited", sex="Female")
        pct_m_sev  = get_val("Severely limited", sex="Male")
        pct_2554   = get_val("Severely limited", age="25-54")
        pct_5574   = get_val("Severely limited", age="55-74")

        # ── Métricas derivadas ────────────────────────────────────────────
        gap_total   = round(pct_none - pct_sev, 4) if not (np.isnan(pct_none) or np.isnan(pct_sev)) else np.nan
        gap_gender  = round(pct_m_sev - pct_f_sev, 4) if not (np.isnan(pct_m_sev) or np.isnan(pct_f_sev)) else np.nan
        gap_age     = round(pct_2554 - pct_5574, 4) if not (np.isnan(pct_2554) or np.isnan(pct_5574)) else np.nan
        gap_eu27    = round(gap_total - EU27_GAP_TOTAL, 4) if not np.isnan(gap_total) else np.nan
        pct_excl    = round(100 - pct_sev, 4) if not np.isnan(pct_sev) else np.nan

        # ── Metadatos del país ────────────────────────────────────────────
        country_name_es = sub["country_name_es"].iloc[0]
        country_name_en = sub["country_name_en"].iloc[0]
        is_eu27 = country == EU27_CODE

        # ── Ranking e inclusion_group (desde columnas ya calculadas) ──────
        # Tomar de la fila core Severely limited si existe
        core_sev = sub[
            (sub["disability_level"] == "Severely limited")
            & sub["is_core_row"]
        ]
        rank = core_sev["country_rank_by_gap"].iloc[0] if len(core_sev) > 0 else pd.NA
        incl = core_sev["inclusion_group"].iloc[0] if len(core_sev) > 0 else pd.NA

        records.append({
            "country_code":             country,
            "country_name_es":          country_name_es,
            "country_name_en":          country_name_en,
            "is_eu27_aggregate":        is_eu27,
            # Porcentajes base (Total sexo, Total edad)
            "pct_no_disability":        pct_none,
            "pct_severely_limited":     pct_sev,
            "pct_limited_not_severely": pct_ltd,
            "pct_limited_or_severely":  pct_ltd_s,
            # Porcentajes por sexo (dentro de discapacidad severa)
            "pct_female_severely":      pct_f_sev,
            "pct_male_severely":        pct_m_sev,
            # Porcentajes por edad (dentro de discapacidad severa)
            "pct_25_54_severely":       pct_2554,
            "pct_55_74_severely":       pct_5574,
            # Métricas de brecha
            "gap_total":                gap_total,
            "gap_gender":               gap_gender,
            "gap_age":                  gap_age,
            "gap_vs_eu27":              gap_eu27,
            "pct_excluded_severely":    pct_excl,
            # Clasificación
            "inclusion_group":          incl,
            "country_rank_by_gap":      rank,
        })

    summary = (
        pd.DataFrame(records)
        .sort_values("gap_total", ascending=False, na_position="last")
        .reset_index(drop=True)
    )

    log.info("         Tabla resumen: %d países × %d variables",
             len(summary), len(summary.columns))
    log.info("         Variables creadas:\n%s", summary.columns.tolist())

    # Vista de verificación de las métricas clave
    check_cols = ["country_code","gap_total","gap_gender","gap_age","gap_vs_eu27","inclusion_group"]
    log.info("         Resumen de métricas:\n%s",
             summary[check_cols].to_string(index=False))

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# PASO 8 — Tabla resumen de España
# ─────────────────────────────────────────────────────────────────────────────
def build_spain_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perfil analítico completo de España con todas las categorías disponibles.
    Esta tabla alimenta directamente la página de España en Power BI y la
    Sección 7 (Resultados) del informe.

    Incluye las variables del dataset analítico para los 23 registros
    válidos de España (el nulo en Y16_24_DIS_SEV se conserva marcado).
    """
    log.info("PASO 8 ─ Construyendo perfil completo de España")

    spain = (
        df[df["country_code"] == "ES"]
        [[
            "disability_level", "sex", "age_group",
            "pct_internet_use", "pct_excluded",
            "gap_vs_no_disability", "pct_vs_eu27",
            "severity_score", "is_reliable", "quality_flag",
        ]]
        .sort_values(["disability_level", "sex", "age_group"])
        .reset_index(drop=True)
    )

    log.info("         Perfil España: %d filas × %d columnas", *spain.shape)
    log.info("         Nulos: %d (Y16_24_DIS_SEV)", spain["pct_internet_use"].isna().sum())
    return spain


# ─────────────────────────────────────────────────────────────────────────────
# PASO 9 — Tabla comparativa Europa (para Power BI y SQL)
# ─────────────────────────────────────────────────────────────────────────────
def build_europe_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla pivotada pensada para visualizaciones de comparación europea.
    Una fila por (país × nivel de discapacidad), Total sexo y Total edad.
    Incluye la brecha y las variables de posición relativa.
    Esta estructura es directamente importable en Power BI como tabla base
    del mapa coroplético y del gráfico de barras de ranking.
    """
    log.info("PASO 9 ─ Construyendo tabla comparativa Europa")

    europe = (
        df[df["is_core_row"]]
        [[
            "country_code", "country_name_es", "country_name_en",
            "disability_level", "disability_rank",
            "pct_internet_use", "pct_excluded",
            "gap_vs_no_disability", "pct_vs_eu27",
            "severity_score", "gap_vs_eu27",
            "inclusion_group", "country_rank_by_gap",
            "is_eu27_aggregate", "is_reliable",
        ]]
        .sort_values(["disability_rank", "country_code"])
        .reset_index(drop=True)
    )

    log.info("         Tabla comparativa: %d filas × %d columnas", *europe.shape)
    return europe


# ─────────────────────────────────────────────────────────────────────────────
# PASO 10 — Validación del dataset analítico
# ─────────────────────────────────────────────────────────────────────────────
def validate_analytical(df: pd.DataFrame) -> None:
    """
    Comprueba que las variables derivadas son coherentes con las expectativas
    conocidas del dataset (valores reales de España verificados manualmente).
    Lanza AssertionError con mensaje claro si algo no cuadra.
    """
    log.info("PASO 10 ─ Validando variables derivadas")

    # Dimensiones
    assert len(df) == 192, f"Filas inesperadas: {len(df)} (esperadas 192)"

    # Todas las columnas de contexto existen
    for col in ["is_core_row", "pct_excluded", "gap_vs_no_disability",
                "pct_vs_eu27", "severity_score", "gap_vs_eu27",
                "country_rank_by_gap", "inclusion_group"]:
        assert col in df.columns, f"Columna faltante: {col}"

    # pct_excluded = 100 - pct_internet_use (donde ambos son válidos)
    valid = df[df["pct_internet_use"].notna() & df["pct_excluded"].notna()]
    check = (valid["pct_excluded"] - (100 - valid["pct_internet_use"])).abs().max()
    assert check < 1e-6, f"pct_excluded inconsistente: desviación máxima = {check}"

    # España: brecha total conocida = 18.26 pp
    es_gap = df[
        (df["country_code"] == "ES")
        & (df["disability_level"] == "Severely limited")
        & df["is_core_row"]
    ]["gap_vs_no_disability"].iloc[0]
    assert abs(es_gap - 18.26) < 0.01, f"Brecha España incorrecta: {es_gap}"

    # España: gap_vs_eu27 conocido = +5.33 pp
    es_gap_eu = df[
        (df["country_code"] == "ES")
        & (df["disability_level"] == "Severely limited")
        & df["is_core_row"]
    ]["gap_vs_eu27"].iloc[0]
    assert abs(es_gap_eu - 5.33) < 0.01, f"gap_vs_eu27 España incorrecto: {es_gap_eu}"

    # España: inclusion_group debe ser "Baja inclusión"
    es_incl = df[
        (df["country_code"] == "ES")
        & (df["disability_level"] == "Severely limited")
        & df["is_core_row"]
    ]["inclusion_group"].iloc[0]
    assert es_incl == "Baja inclusión", f"inclusion_group España incorrecto: {es_incl}"

    # Países Bajos: mayor brecha más baja → rank 7 (de 7 países sin EU27)
    nl_rank = df[
        (df["country_code"] == "NL")
        & (df["disability_level"] == "Severely limited")
        & df["is_core_row"]
    ]["country_rank_by_gap"].iloc[0]
    assert nl_rank == 7, f"Ranking NL incorrecto: {nl_rank} (esperado 7)"

    log.info("         ✓ Todas las validaciones superadas.")


# ─────────────────────────────────────────────────────────────────────────────
# PASO 11 — Guardado de todos los archivos de salida
# ─────────────────────────────────────────────────────────────────────────────
def save_outputs(
    df_analytical: pd.DataFrame,
    df_country: pd.DataFrame,
    df_spain: pd.DataFrame,
    df_europe: pd.DataFrame,
) -> None:
    """
    Guarda los cuatro archivos de salida en data/processed/.
    Registra en el log la ruta, dimensiones y tamaño de cada archivo.
    """
    log.info("PASO 11 ─ Guardando archivos de salida")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    outputs = [
        (df_analytical, OUT_ANALYTICAL,  "Dataset analítico completo"),
        (df_country,    OUT_BY_COUNTRY,  "Resumen por país"),
        (df_spain,      OUT_SPAIN,        "Perfil España"),
        (df_europe,     OUT_EUROPE,       "Comparativa Europa"),
    ]

    for df_out, path, label in outputs:
        df_out.to_csv(path, index=False, encoding="utf-8")
        size_kb = path.stat().st_size / 1024
        log.info("         [%s]  %s  (%d × %d, %.1f KB)",
                 label, path, len(df_out), len(df_out.columns), size_kb)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def main() -> pd.DataFrame:
    """Ejecuta el pipeline completo de feature engineering."""
    log.info("=" * 70)
    log.info("INICIO DEL PIPELINE DE FEATURE ENGINEERING — DSB_ICTIU01 (2024)")
    log.info("=" * 70)

    # ── Pipeline ─────────────────────────────────────────────────────────────
    df = load_clean_data(INPUT_FILE)
    df = add_context_variables(df)
    df = add_gap_vs_no_disability(df)
    df = add_eu27_relative_position(df)
    df = add_severity_score(df)
    df = add_country_position_label(df)

    # ── Tablas derivadas ──────────────────────────────────────────────────────
    df_country = build_country_summary(df)
    df_spain   = build_spain_summary(df)
    df_europe  = build_europe_comparison(df)

    # ── Validación y guardado ─────────────────────────────────────────────────
    validate_analytical(df)
    save_outputs(df, df_country, df_spain, df_europe)

    # ── Resumen final ─────────────────────────────────────────────────────────
    new_cols = [
        "is_eu27_aggregate", "is_total_sex", "is_total_age", "is_core_row",
        "disability_rank", "pct_excluded",
        "pct_no_disability",
        "gap_vs_no_disability",
        "pct_eu27_equivalent", "pct_vs_eu27", "gap_vs_eu27",
        "severity_score",
        "country_rank_by_gap", "inclusion_group",
    ]
    log.info("=" * 70)
    log.info("PIPELINE COMPLETADO CON ÉXITO")
    log.info("  Variables nuevas añadidas (%d):", len(new_cols))
    for v in new_cols:
        log.info("    %-30s  %s", v, str(df[v].dtype))
    log.info("  Archivos generados:")
    log.info("    %s", OUT_ANALYTICAL)
    log.info("    %s", OUT_BY_COUNTRY)
    log.info("    %s", OUT_SPAIN)
    log.info("    %s", OUT_EUROPE)
    log.info("=" * 70)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        df_result = main()
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
# RESUMEN DE VARIABLES CREADAS
# ─────────────────────────────────────────────────────────────────────────────
"""
VARIABLES NUEVAS EN analytical_dsb_ictiu01.csv
═══════════════════════════════════════════════

VARIABLES DE CONTEXTO (Paso 2)
────────────────────────────────
is_eu27_aggregate   bool    True si el registro es del agregado EU27_2020.
                            Excluir en clustering; usar solo como referencia.

is_total_sex        bool    True si sex == 'Total'.

is_total_age        bool    True si age_group == 'Total'.

is_core_row         bool    True si sex == 'Total' Y age_group == 'Total'.
                            Estas filas son el núcleo del análisis comparativo.

disability_rank     int     Orden numérico del nivel de discapacidad:
                            0=No disability, 1=Limited not severely,
                            2=Severely limited, 3=Limited or severely.
                            Útil para ORDER BY en SQL y ejes de gráficos.

pct_excluded        float   100 − pct_internet_use. % de personas que NO
                            usan Internet. Interpretación directa de exclusión.

BRECHA VS. SIN DISCAPACIDAD (Paso 3)
─────────────────────────────────────
pct_no_disability       float   % uso Internet del grupo sin discapacidad con
                                el mismo sexo y grupo de edad. Valor de referencia.

gap_vs_no_disability    float   pct_no_disability − pct_internet_use.
                                0 para filas de No disability.
                                18.26 pp para España (Severely limited / Total).
                                Pregunta P1 y P2.

POSICIÓN RELATIVA UE-27 (Paso 4)
──────────────────────────────────
pct_eu27_equivalent     float   % uso Internet de EU27_2020 para el mismo
                                disability_level, sex y age_group. Referencia europea.

pct_vs_eu27             float   pct_internet_use − pct_eu27_equivalent.
                                Positivo → por encima de la media UE.

gap_vs_eu27             float   gap_vs_no_disability − 12.93 (brecha media EU27).
                                Solo tiene valor en filas is_core_row + Severely limited.
                                España: +5.33 pp (la brecha española supera a la europea).

SEVERIDAD DE EXCLUSIÓN (Paso 5)
─────────────────────────────────
severity_score          float   Índice [0–100] de exclusión relativa dentro del nivel
                                de discapacidad. 100 = mayor exclusión observada en ese
                                nivel. Calculado solo sobre datos fiables.

CLASIFICACIÓN Y RANKING (Paso 6)
──────────────────────────────────
country_rank_by_gap     Int64   Ranking de países por brecha total (1 = mayor brecha).
                                Solo en filas is_core_row + Severely limited.
                                España: rank 2 de 7 países (excl. EU27).

inclusion_group         str     Categoría cualitativa:
                                "Alta inclusión"     gap < 5 pp   → NL, SE
                                "Inclusión media"    gap 5-12 pp  → FR, PT, DE
                                "Baja inclusión"     gap 12-20 pp → ES, IT, EU27
                                "Muy baja inclusión" gap > 20 pp  → (ninguno aquí)

ARCHIVOS DE SALIDA
══════════════════
analytical_dsb_ictiu01.csv    Dataset fila a fila con todas las variables nuevas.
                               192 filas × 26 columnas. Input para notebooks de análisis.

summary_by_country.csv         Una fila por país. 8 filas × 19 columnas.
                               Input para clustering y KPIs de Power BI.

summary_spain.csv               Perfil de España. 24 filas × 10 columnas.
                               Para página España en Power BI e informe §7.

summary_europe_comparison.csv   Tabla comparativa. 32 filas (8 × 4 niveles) × 16 columnas.
                               Para mapa coroplético y gráficos de ranking.
"""
