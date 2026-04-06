"""
cleaning/main.py — Orquestador del pipeline de limpieza.

Ejecución:
    cd python/
    python -m cleaning.main

Salida:
    data/processed/cleaned_dsb_ictiu01.csv  (9 países × 24 categorías = 216 filas)

Nota: este script sustituye a 01_data_cleaning.py (que era demasiado largo).
La lógica de limpieza vive en cleaning/steps.py.
"""
import sys
import logging
from pathlib import Path

# Añadir python/ al path para encontrar config.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import RAW_CSV, CLEAN_CSV, DATA_PROC
from cleaning import steps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def run() -> "pd.DataFrame":
    """Ejecuta el pipeline completo y devuelve el DataFrame limpio."""
    log.info("=" * 60)
    log.info("PIPELINE DE LIMPIEZA — Eurostat DSB_ICTIU01 (2024)")
    log.info("Países: 9 (ES, EU27, DE, FR, IT, NL, PT, SE, LT)")
    log.info("=" * 60)

    df = steps.load(RAW_CSV)
    steps.inspect(df)
    df = steps.select_rename(df)
    df = steps.filter_countries(df)
    df = steps.filter_categories(df)
    df = steps.handle_flags(df)
    df = steps.convert_types(df)
    df = steps.decode_ind_type(df)
    df = steps.reorder_sort(df)
    steps.validate(df)

    DATA_PROC.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_CSV, index=False, encoding="utf-8")
    size_kb = CLEAN_CSV.stat().st_size / 1024
    log.info("✓ Output guardado: %s (%d filas, %.1f KB)", CLEAN_CSV, len(df), size_kb)
    log.info("=" * 60)
    return df


if __name__ == "__main__":
    try:
        df_clean = run()
    except FileNotFoundError as e:
        log.error("ARCHIVO NO ENCONTRADO: %s", e)
        sys.exit(1)
    except AssertionError as e:
        log.error("VALIDACIÓN FALLIDA: %s", e)
        sys.exit(2)
    except Exception as e:
        log.exception("ERROR INESPERADO: %s", e)
        sys.exit(99)
