"""
sql_loader.py — Carga el dataset limpio en la base de datos SQLite del proyecto.

PRERREQUISITO:
    python -m cleaning.main       →  genera data/processed/cleaned_dsb_ictiu01.csv

EJECUCIÓN:
    cd python/
    python sql_loader.py

QUÉ HACE:
    1. Ejecuta sql/schema.sql   → crea tablas y dimensiones
    2. Lee cleaned_dsb_ictiu01.csv
    3. Calcula métricas derivadas (gap, pct_vs_eu27)
    4. Carga fact_internet_use con todos los datos
    5. Verifica la carga con queries de control

SALIDA:
    proyecto.db  (SQLite — listo para sql/analysis_queries.sql y Power BI)
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

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)


# ── Helpers ───────────────────────────────────────────────────────────────
def _run_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    """Ejecuta un archivo SQL completo. Usa executescript para múltiples sentencias."""
    if not path.exists():
        raise FileNotFoundError(f"Archivo SQL no encontrado: {path}")
    conn.executescript(path.read_text(encoding="utf-8"))
    log.info("SQL ejecutado: %s", path.name)


def _safe_float(val) -> float | None:
    """Convierte a float; devuelve None si NaN (compatibilidad SQLite)."""
    return None if pd.isna(val) else float(val)


# ── Paso 1: Crear esquema ─────────────────────────────────────────────────
def create_schema(conn: sqlite3.Connection) -> None:
    """
    Ejecuta los scripts SQL que crean tablas y cargan dimensiones.
    Intenta primero los archivos divididos (01_schema.sql + 02_seed.sql);
    si no existen, usa el schema.sql original completo.
    """
    split_files = [SQL_DIR / "01_schema.sql", SQL_DIR / "02_seed.sql"]
    if all(f.exists() for f in split_files):
        for f in split_files:
            _run_sql_file(conn, f)
    else:
        _run_sql_file(conn, SQL_DIR / "schema.sql")

    # Añadir Lituania a dim_country si no existe
    conn.execute("""
        INSERT OR IGNORE INTO dim_country
            (country_code, country_name_es, country_name_en, is_aggregate, iso2_code, region)
        VALUES ('LT', 'Lituania', 'Lithuania', 0, 'LT', 'Europa del Este')
    """)
    conn.commit()
    log.info("Esquema y dimensiones creados (con Lituania incluida)")


# ── Paso 2: Métricas derivadas ────────────────────────────────────────────
def compute_derived(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade al DataFrame:
    - pct_excluded           : 100 − pct_internet_use
    - gap_vs_no_disability   : referencia (sin discapacidad) − valor fila
    - pct_vs_eu27            : valor fila − valor equivalente EU27_2020
    - is_reliable_int        : int(is_reliable) para SQLite
    """
    df = df.copy()
    df["pct_excluded"] = (100 - df["pct_internet_use"]).round(4)

    # gap_vs_no_disability — mismo país/sexo/edad
    ref = (
        df[df["disability_level"] == "No disability"]
        [["country_code", "sex", "age_group", "pct_internet_use"]]
        .rename(columns={"pct_internet_use": "_ref"})
    )
    df = df.merge(ref, on=["country_code", "sex", "age_group"], how="left")
    df["gap_vs_no_disability"] = (df["_ref"] - df["pct_internet_use"]).round(4)
    df.drop(columns=["_ref"], inplace=True)

    # pct_vs_eu27 — mismo disability/sexo/edad
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


# ── Paso 3: Carga de la tabla de hechos ───────────────────────────────────
def load_fact_table(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """Vacía e inserta todas las filas en fact_internet_use. Devuelve nº de filas."""
    cur = conn.cursor()
    cur.execute("DELETE FROM fact_internet_use")

    sql_insert = """
        INSERT INTO fact_internet_use
            (indicator_code, country_code, category_code,
             pct_internet_use, pct_excluded, gap_vs_no_disability,
             pct_vs_eu27, quality_flag, is_reliable)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    rows = [
        (
            INDICATOR_CODE,
            row.country_code,
            row.category_code,
            _safe_float(row.pct_internet_use),
            _safe_float(row.pct_excluded),
            _safe_float(row.gap_vs_no_disability),
            _safe_float(row.pct_vs_eu27),
            None if pd.isna(row.quality_flag) else str(row.quality_flag),
            int(row.is_reliable_int),
        )
        for row in df.itertuples(index=False)
    ]
    cur.executemany(sql_insert, rows)
    conn.commit()
    log.info("fact_internet_use: %d filas insertadas", len(rows))
    return len(rows)


# ── Paso 4: Verificación post-carga ──────────────────────────────────────
def verify(conn: sqlite3.Connection) -> None:
    """Ejecuta queries de control para confirmar que la carga es correcta."""
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM fact_internet_use").fetchone()[0]
    log.info("Total filas en fact_internet_use: %d", total)

    # Brecha España (debe ser 18,26 pp)
    es_gap = cur.execute("""
        SELECT ROUND(f_none.pct_internet_use - f_sev.pct_internet_use, 2)
        FROM fact_internet_use f_none, fact_internet_use f_sev
        WHERE f_none.country_code='ES' AND f_none.category_code='DIS_NONE'
          AND f_sev.country_code='ES'  AND f_sev.category_code='DIS_SEV'
    """).fetchone()[0]
    log.info("Verificación brecha España: %.2f pp (esperado: 18.26 pp)", es_gap)

    # Top 3 países por brecha (LT debe ser el primero)
    top3 = cur.execute("""
        SELECT f_n.country_code,
               ROUND(f_n.pct_internet_use - f_s.pct_internet_use, 2) AS gap
        FROM fact_internet_use f_n
        JOIN fact_internet_use f_s ON f_n.country_code = f_s.country_code
        WHERE f_n.category_code='DIS_NONE' AND f_s.category_code='DIS_SEV'
          AND f_s.is_reliable=1 AND f_n.country_code != 'EU27_2020'
        ORDER BY gap DESC LIMIT 3
    """).fetchall()
    log.info("Top 3 brechas: %s (LT debe ser el primero con ~35.86 pp)", top3)


# ── Main ──────────────────────────────────────────────────────────────────
def main() -> None:
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
    log.info("CSV limpio cargado: %d filas × %d columnas", *df.shape)

    df = compute_derived(df)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        create_schema(conn)
        n = load_fact_table(conn, df)
        verify(conn)
    finally:
        conn.close()

    size_kb = DB_PATH.stat().st_size / 1024
    log.info("Base de datos: %s (%.0f KB)", DB_PATH, size_kb)
    log.info("=" * 60)
    log.info("CARGA COMPLETADA. Ahora puedes ejecutar:")
    log.info("  sqlite3 proyecto.db < sql/analysis_queries.sql")
    log.info("  O conectar Power BI directamente a proyecto.db")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
