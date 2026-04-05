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
echo " Proyecto Final Big Data & IA — IFP 2025-2026"
echo "============================================================"
echo ""

# ── 1. Crear estructura de carpetas ───────────────────────────
echo "[1/4] Verificando estructura de carpetas..."

DIRS=(
    "data/raw"
    "data/processed"
    "sql"
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
echo "[4/4] Verificando archivos clave..."

FILES=(
    "data/raw/dsb_ictiu01_eurostat_2024.csv"
    "requirements.txt"
    "README.md"
    ".gitignore"
    "sql/01_create_schema.sql"
    "python/01_limpieza_pipeline.ipynb"
    "python/utils/helpers.py"
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

# ── Resumen ───────────────────────────────────────────────────
echo ""
echo "============================================================"
if [ "$ALL_OK" = true ]; then
    echo " ✓ Proyecto inicializado correctamente."
    echo ""
    echo " PRÓXIMOS PASOS:"
    echo "   1. Activar el entorno:  source .venv/bin/activate"
    echo "   2. Abrir Jupyter:       jupyter notebook python/"
    echo "   3. Ejecutar en orden:   01 → 02 → 03 → 04 → 05"
    echo "   4. Ejecutar SQL:        sqlite3 proyecto.db < sql/01_create_schema.sql"
else
    echo " ⚠ Algunos archivos no se encontraron. Revisar lista."
fi
echo "============================================================"
echo ""
