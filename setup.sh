#!/usr/bin/env bash
# ============================================================
# setup.sh — Inicialización del entorno del proyecto
# Proyecto: Brecha Digital y Discapacidad en España
# Uso: bash setup.sh
# ============================================================

set -e

echo ""
echo "============================================================"
echo " BRECHA DIGITAL Y DISCAPACIDAD EN ESPAÑA"
echo " Proyecto Final Big Data & IA · IFP 2025-2026"
echo "============================================================"
echo ""

# ── 1. Crear estructura de carpetas ───────────────────────────
echo "[1/4] Verificando estructura de carpetas..."

DIRS=(
    "data/raw"
    "data/processed"
    "sql"
    "python/cleaning"
    "python/utils"
    "powerbi"
    "docs"
    "images/figures"
    "images/capturas"
    "outputs/tables"
    "outputs/reports"
)

for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
    echo "  ✓ $dir"
done

# ── 2. Crear entorno virtual Python ──────────────────────────
echo ""
echo "[2/4] Creando entorno virtual Python..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  ✓ Entorno virtual creado en .venv/"
else
    echo "  ℹ Entorno virtual ya existe"
fi

# ── 3. Instalar dependencias ──────────────────────────────────
echo ""
echo "[3/4] Instalando dependencias Python..."

source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "  ✓ Dependencias instaladas"

# ── 4. Verificar archivos clave ───────────────────────────────
echo ""
echo "[4/4] Verificando archivos clave del proyecto..."

FILES=(
    "data/raw/dsb_ictiu01_eurostat_2024.csv"
    "requirements.txt"
    "README.md"
    ".gitignore"
    "python/config.py"
    "python/cleaning/steps.py"
    "python/cleaning/main.py"
    "python/sql_loader.py"
    "python/utils/helpers.py"
    "python/03_eda.py"
    "sql/01_schema.sql"
    "sql/02_seed.sql"
    "sql/04_queries_p1_ranking.sql"
    "sql/05_queries_p2_p3_vulnerabilidad.sql"
    "sql/06_queries_estadisticos_powerbi.sql"
    "powerbi/README_powerbi.md"
    "docs/bibliografia.md"
)

ALL_OK=true
for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
        echo "  ✓ $f"
    else
        echo "  ✗ FALTA: $f"
        ALL_OK=false
    fi
done

# ── Verificar imports Python ──────────────────────────────────
echo ""
echo "  Verificando imports de Python..."
cd python/
if python3 -c "
import sys
from config import TARGET_COUNTRIES, CLEAN_CSV, DB_PATH
from cleaning.steps import load, validate
from utils.helpers import COUNTRY_NAMES_ES
assert 'LT' in TARGET_COUNTRIES, 'Lituania no está en TARGET_COUNTRIES'
assert 'LT' in COUNTRY_NAMES_ES, 'Lituania no está en COUNTRY_NAMES_ES'
print(f'  ✓ Módulos OK — {len(TARGET_COUNTRIES)} países (incluida Lituania)')
" 2>&1; then
    echo "  ✓ Imports verificados"
else
    echo "  ✗ Error en imports — revisar config.py"
    ALL_OK=false
fi
cd ..

# ── Resumen ───────────────────────────────────────────────────
echo ""
echo "============================================================"
if [ "$ALL_OK" = true ]; then
    echo " ✓ Entorno inicializado correctamente."
    echo ""
    echo " FLUJO DE EJECUCIÓN (copiar y pegar en orden):"
    echo ""
    echo "   cd python"
    echo "   python -m cleaning.main          # limpia datos"
    echo "   python sql_loader.py             # crea proyecto.db"
    echo "   python 03_eda.py                 # genera figuras"
    echo "   cd .."
    echo "   ./sqlite3.exe proyecto.db < sql/04_queries_p1_ranking.sql"
    echo "   ./sqlite3.exe proyecto.db < sql/05_queries_p2_p3_vulnerabilidad.sql"
    echo "   ./sqlite3.exe proyecto.db < sql/06_queries_estadisticos_powerbi.sql"
    echo ""
    echo "   # Power BI: conectar a proyecto.db y usar vistas vw_pbi_*"
else
    echo " ⚠ Algunos archivos no encontrados. Revisa los ✗ arriba."
fi
echo "============================================================"
echo ""