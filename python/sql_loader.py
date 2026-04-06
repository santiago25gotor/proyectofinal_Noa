"""
sql_loader.py — Carga el dataset limpio en la base de datos SQLite del proyecto.

PRERREQUISITO:
    python -m cleaning.main  →  genera data/processed/cleaned_dsb_ictiu01.csv

EJECUCIÓN:
    cd python/
    python sql_loader.py

QUÉ HACE:
    1. Ejecuta sql/01_schema.sql + sql/02_seed.sql  → crea tablas y dimensiones
    2. Lee cleaned_dsb_ictiu01.csv
    3. Calcula métricas derivadas (gap, pct_vs_eu27, pct_excluded)
    4. Carga fact_internet_use  (216 filas)
    5. Calcula y carga mart_country_metrics  (9 filas, una por país)
    6. Verifica la carga con queries de control

SALIDA:
    proyecto.db  (SQLite) → listo para sql/analysis_queries.sql y Power BI
"""
import sys
import logging
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from config import CLEAN_CSV, DB_PATH, SQL_DIR, EU27_CODE

INDICATOR_CODE = "I_ILT12"
EU27_GAP       = 12.93   # brecha media UE-27 (referencia fija)

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)


# ── Helpers ───────────────────────────────────────────────────────────────
def _run_sql(conn, path):
    if not path.exists():
        raise FileNotFoundError(f"SQL no encontrado: {path}")
    conn.executescript(path.read_text(encoding="utf-8"))
    log.info("SQL ejecutado: %s", path.name)


def _f(val):
    """float seguro para SQLite (None si NaN)."""
    return None if pd.isna(val) else float(round(val, 4))


def _get(df_pivot, code):
    """Obtiene valor de un pivot o None si no existe."""
    try:
        v = df_pivot.loc[code]
        return None if pd.isna(v) else float(v)
    except KeyError:
        return None


# ── PASO 1: Esquema ───────────────────────────────────────────────────────
def create_schema(conn):
    _run_sql(conn, SQL_DIR / "01_schema.sql")
    _run_sql(conn, SQL_DIR / "02_seed.sql")
    conn.commit()
    log.info("Esquema y dimensiones creados")


# ── PASO 2: Métricas derivadas ────────────────────────────────────────────
def compute_derived(df):
    """Añade pct_excluded, gap_vs_no_disability, pct_vs_eu27."""
    df = df.copy()
    df["pct_excluded"] = (100 - df["pct_internet_use"]).round(4)

    # gap_vs_no_disability: referencia sin discapacidad del mismo país/sexo/edad
    ref = (
        df[df["disability_level"] == "No disability"]
        [["country_code", "sex", "age_group", "pct_internet_use"]]
        .rename(columns={"pct_internet_use": "_ref"})
    )
    df = df.merge(ref, on=["country_code", "sex", "age_group"], how="left")
    df["gap_vs_no_disability"] = (df["_ref"] - df["pct_internet_use"]).round(4)
    df.drop(columns=["_ref"], inplace=True)

    # pct_vs_eu27: diferencia vs valor equivalente EU27_2020
    eu27 = (
        df[df["country_code"] == EU27_CODE]
        [["disability_level", "sex", "age_group", "pct_internet_use"]]
        .rename(columns={"pct_internet_use": "_eu27"})
    )
    df = df.merge(eu27, on=["disability_level", "sex", "age_group"], how="left")
    df["pct_vs_eu27"] = (df["pct_internet_use"] - df["_eu27"]).round(4)
    df.drop(columns=["_eu27"], inplace=True)

    df["is_reliable_int"] = df["is_reliable"].astype(int)
    return df


# ── PASO 3: Carga fact_internet_use ──────────────────────────────────────
def load_fact(conn, df):
    conn.execute("DELETE FROM fact_internet_use")
    sql = """
        INSERT INTO fact_internet_use
            (indicator_code, country_code, category_code,
             pct_internet_use, pct_excluded, gap_vs_no_disability,
             pct_vs_eu27, quality_flag, is_reliable)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    rows = [
        (
            INDICATOR_CODE,
            r.country_code, r.category_code,
            _f(r.pct_internet_use), _f(r.pct_excluded),
            _f(r.gap_vs_no_disability), _f(r.pct_vs_eu27),
            None if pd.isna(r.quality_flag) else str(r.quality_flag),
            int(r.is_reliable_int),
        )
        for r in df.itertuples(index=False)
    ]
    conn.executemany(sql, rows)
    conn.commit()
    log.info("fact_internet_use: %d filas insertadas", len(rows))


# ── PASO 4: Calcular y cargar mart_country_metrics ────────────────────────
def populate_mart(conn, df):
    """
    Calcula una fila resumen por país y la inserta en mart_country_metrics.
    Esta tabla alimenta las vistas vw_pbi_* de Power BI.
    Sin esta tabla, todas las vistas Power BI devuelven cero filas.
    """
    conn.execute("DELETE FROM mart_country_metrics")

    countries = df["country_code"].unique()
    records   = []

    for cc in countries:
        sub   = df[df["country_code"] == cc].set_index("category_code")["pct_internet_use"]
        is_eu = (cc == EU27_CODE)

        pct_none  = _get(sub, "DIS_NONE")
        pct_sev   = _get(sub, "DIS_SEV")
        pct_ltd   = _get(sub, "DIS_LTD")
        pct_lts   = _get(sub, "DIS_LTD_SEV")
        pct_f_sev = _get(sub, "F_DIS_SEV")
        pct_m_sev = _get(sub, "M_DIS_SEV")
        pct_2554  = _get(sub, "Y25_54_DIS_SEV")
        pct_5574  = _get(sub, "Y55_74_DIS_SEV")

        # Métricas de brecha
        def diff(a, b):
            return round(a - b, 2) if (a is not None and b is not None) else None

        gap_total  = diff(pct_none, pct_sev)
        gap_gender = diff(pct_m_sev, pct_f_sev)
        gap_age    = diff(pct_2554, pct_5574)
        gap_eu27   = diff(gap_total, EU27_GAP) if gap_total is not None else None
        pct_excl   = round(100 - pct_sev, 2) if pct_sev is not None else None

        # Grupo de inclusión
        if gap_total is None or is_eu:
            group = None
        elif gap_total < 5:
            group = "Alta inclusión"
        elif gap_total < 12:
            group = "Inclusión media"
        elif gap_total <= 25:
            group = "Baja inclusión"
        else:
            group = "Muy baja inclusión"

        records.append({
            "country_code":             cc,
            "pct_no_disability":        pct_none,
            "pct_severely_limited":     pct_sev,
            "pct_limited_not_severely": pct_ltd,
            "pct_limited_or_severely":  pct_lts,
            "pct_female_severely":      pct_f_sev,
            "pct_male_severely":        pct_m_sev,
            "pct_25_54_severely":       pct_2554,
            "pct_55_74_severely":       pct_5574,
            "gap_total":                gap_total,
            "gap_gender":               gap_gender,
            "gap_age":                  gap_age,
            "gap_vs_eu27":              gap_eu27,
            "pct_excluded_severely":    pct_excl,
            "inclusion_group":          group,
            "country_rank_by_gap":      None,   # se actualiza abajo
            "is_eu27_aggregate":        1 if is_eu else 0,
        })

    # Calcular ranking (solo países individuales, no EU27)
    paises = [(r["country_code"], r["gap_total"])
              for r in records if not r["is_eu27_aggregate"] and r["gap_total"] is not None]
    paises.sort(key=lambda x: x[1], reverse=True)
    rank_map = {cc: i + 1 for i, (cc, _) in enumerate(paises)}

    for r in records:
        r["country_rank_by_gap"] = rank_map.get(r["country_code"])

    sql = """
        INSERT INTO mart_country_metrics (
            country_code, pct_no_disability, pct_severely_limited,
            pct_limited_not_severely, pct_limited_or_severely,
            pct_female_severely, pct_male_severely,
            pct_25_54_severely, pct_55_74_severely,
            gap_total, gap_gender, gap_age, gap_vs_eu27,
            pct_excluded_severely, inclusion_group,
            country_rank_by_gap, is_eu27_aggregate
        ) VALUES (
            :country_code, :pct_no_disability, :pct_severely_limited,
            :pct_limited_not_severely, :pct_limited_or_severely,
            :pct_female_severely, :pct_male_severely,
            :pct_25_54_severely, :pct_55_74_severely,
            :gap_total, :gap_gender, :gap_age, :gap_vs_eu27,
            :pct_excluded_severely, :inclusion_group,
            :country_rank_by_gap, :is_eu27_aggregate
        )
    """
    conn.executemany(sql, records)
    conn.commit()
    log.info("mart_country_metrics: %d filas insertadas", len(records))

    # Log de verificación
    rows = conn.execute(
        "SELECT country_code, gap_total, inclusion_group, country_rank_by_gap "
        "FROM mart_country_metrics ORDER BY COALESCE(gap_total,0) DESC"
    ).fetchall()
    log.info("Resumen mart_country_metrics:")
    for r in rows:
        log.info("  %s | gap=%-6s | grupo=%-18s | rank=%s",
                 r[0], r[1], r[2] or "—", r[3] or "—")


# ── PASO 5: Verificación ─────────────────────────────────────────────────
def verify(conn):
    total_fact = conn.execute("SELECT COUNT(*) FROM fact_internet_use").fetchone()[0]
    total_mart = conn.execute("SELECT COUNT(*) FROM mart_country_metrics").fetchone()[0]
    log.info("fact_internet_use: %d filas | mart_country_metrics: %d filas",
             total_fact, total_mart)

    # Brecha España (18.26 pp)
    es_gap = conn.execute(
        "SELECT gap_total FROM mart_country_metrics WHERE country_code='ES'"
    ).fetchone()[0]
    log.info("Brecha España: %.2f pp (esperado: 18.26 pp) %s",
             es_gap, "✓" if abs(es_gap - 18.26) < 0.01 else "✗")

    # Verificar que las vistas Power BI devuelven datos
    for vista in ["vw_pbi_ranking", "vw_pbi_mapa_europeo",
                  "vw_pbi_genero", "vw_pbi_kpis_espana"]:
        try:
            n = conn.execute(f"SELECT COUNT(*) FROM {vista}").fetchone()[0]
            log.info("Vista %-28s → %d filas %s", vista, n,
                     "✓" if n > 0 else "✗ VACÍA")
        except Exception as e:
            log.warning("Vista %s no existe aún (se crea en 06_queries): %s", vista, e)

    # Top 3 por brecha
    top3 = conn.execute(
        "SELECT country_code, gap_total, country_rank_by_gap "
        "FROM mart_country_metrics WHERE is_eu27_aggregate=0 "
        "ORDER BY gap_total DESC LIMIT 3"
    ).fetchall()
    log.info("Top 3 brechas: %s (Lituania debe ser 1ª con 35.86 pp)", top3)


# ── Main ─────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("SQL LOADER — DSB_ICTIU01 → proyecto.db")
    log.info("=" * 60)

    if not CLEAN_CSV.exists():
        log.error("CSV limpio no encontrado: %s", CLEAN_CSV)
        log.error("Ejecuta primero: python -m cleaning.main")
        sys.exit(1)

    df = pd.read_csv(CLEAN_CSV)
    df["is_reliable"]      = df["is_reliable"].astype(bool)
    df["pct_internet_use"] = pd.to_numeric(df["pct_internet_use"], errors="coerce")
    log.info("CSV cargado: %d filas × %d columnas", *df.shape)

    df = compute_derived(df)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        create_schema(conn)
        load_fact(conn, df)
        populate_mart(conn, df)    # ← CRÍTICO: rellena mart para Power BI
        verify(conn)
    finally:
        conn.close()

    size_kb = DB_PATH.stat().st_size / 1024
    log.info("=" * 60)
    log.info("Base de datos: %s (%.0f KB)", DB_PATH, size_kb)
    log.info("CARGA COMPLETADA")
    log.info("Siguiente paso:")
    log.info("  ./sqlite3.exe proyecto.db < sql/06_queries_estadisticos_powerbi.sql")
    log.info("  (crea las vistas vw_pbi_* que usa Power BI)")
    log.info("=" * 60)


if __name__ == "__main__":
    main()