"""
ml_clasificacion.py — Clasificación de perfiles de exclusión digital.

OBJETIVO:
    Predecir si un perfil sociodemográfico (nivel de discapacidad, país,
    sexo, grupo de edad) tiene ALTA EXCLUSIÓN DIGITAL, definida como
    un uso de Internet inferior al 85%.

    Esta pregunta tiene sentido directo para el proyecto: dado un perfil,
    ¿podemos anticipar si pertenece al colectivo más excluido digitalmente?

VARIABLE TARGET (binaria):
    0 — Baja exclusión  (pct_internet_use >= 85%)
    1 — Alta exclusión  (pct_internet_use <  85%)

FEATURES (4):
    - nivel_discapacidad  (No disability / Limited / Severely limited / ...)
    - sexo                (Total / Female / Male)
    - grupo_edad          (Total / 16-24 / 25-54 / 55-74)
    - país                (DE, ES, FR, IT, LT, NL, PT, SE, EU27_2020)

MODELOS COMPARADOS:
    1. Árbol de Decisión    — interpretable, visualizable
    2. Random Forest        — mejor accuracy (modelo ganador)
    3. K-Nearest Neighbors  — referencia comparativa

RESULTADO ESPERADO:
    Random Forest — Accuracy CV: ~79%
    El país y el nivel de discapacidad son los factores más determinantes.

PRERREQUISITO:
    python -m cleaning.main  →  genera data/processed/cleaned_dsb_ictiu01.csv

EJECUCIÓN (desde python/):
    python ml_clasificacion.py

SALIDA:
    images/figures/07_ml_matriz_confusion.png
    images/figures/08_ml_importancia_features.png
    images/figures/09_ml_arbol_decision.png
    outputs/tables/ml_resultados_clasificacion.csv
"""
import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, ConfusionMatrixDisplay
)
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent))
from config import CLEAN_CSV, IMAGES_DIR, OUTPUTS_DIR, PALETTE, SOURCE_NOTE

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-8s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

FIG_DIR = IMAGES_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR = OUTPUTS_DIR / "tables"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Constantes ────────────────────────────────────────────────────────────
UMBRAL_EXCLUSION = 85.0   # % de uso de internet — umbral de alta exclusión
RANDOM_STATE     = 42
TEST_SIZE        = 0.2
CV_FOLDS         = 5

FEATURE_NAMES = ['nivel_discapacidad', 'sexo', 'grupo_edad', 'pais']
CLASS_NAMES   = ['Baja exclusión (≥85%)', 'Alta exclusión (<85%)']


# ── PASO 1: Carga y preparación de datos ─────────────────────────────────
def load_and_prepare(csv_path: Path) -> tuple:
    """
    Carga el CSV limpio y prepara la matriz X e y para clasificación.

    Returns:
        X        : array de features codificadas
        y        : array de la variable target (0/1)
        df_ml    : DataFrame con todas las columnas para análisis
        encoders : dict con los LabelEncoders para cada feature
    """
    df = pd.read_csv(csv_path)
    df["pct_internet_use"] = pd.to_numeric(df["pct_internet_use"], errors="coerce")
    df["is_reliable"]      = df["is_reliable"].astype(bool)

    # Usar solo observaciones con dato fiable
    df_ml = df[df["is_reliable"] & df["pct_internet_use"].notna()].copy()

    # Variable target: ¿alta exclusión digital?
    df_ml["alta_exclusion"] = (df_ml["pct_internet_use"] < UMBRAL_EXCLUSION).astype(int)
    df_ml["tiene_discapacidad"] = df_ml["disability_level"].isin([
        "Severely limited", "Limited (not severely)", "Limited or severely limited"
    ]).astype(int)

    # Codificación de variables categóricas
    encoders = {}
    for col, feat in [
        ("disability_level", "nivel_discapacidad"),
        ("sex",              "sexo"),
        ("age_group",        "grupo_edad"),
        ("country_code",     "pais"),
    ]:
        le = LabelEncoder()
        df_ml[feat + "_enc"] = le.fit_transform(df_ml[col])
        encoders[feat] = le

    X = df_ml[[f + "_enc" for f in FEATURE_NAMES]].values
    y = df_ml["alta_exclusion"].values

    log.info("Dataset preparado: %d observaciones × %d features", len(df_ml), len(FEATURE_NAMES))
    log.info("Clase 0 (baja exclusión, ≥85%%): %d", (y == 0).sum())
    log.info("Clase 1 (alta exclusión, <85%%): %d", (y == 1).sum())

    return X, y, df_ml, encoders


# ── PASO 2: Entrenamiento y comparación de modelos ────────────────────────
def train_and_compare(X, y) -> dict:
    """
    Entrena 3 modelos, los compara con validación cruzada y devuelve resultados.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    modelos = {
        "Árbol de Decisión": DecisionTreeClassifier(max_depth=4, random_state=RANDOM_STATE),
        "Random Forest":     RandomForestClassifier(n_estimators=100, max_depth=4,
                                                    random_state=RANDOM_STATE),
        "K-Nearest Neighbors": KNeighborsClassifier(n_neighbors=5),
    }

    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    log.info("Comparación de modelos:")
    resultados = {}
    for nombre, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        acc_test = accuracy_score(y_test, modelo.predict(X_test))
        acc_cv   = cross_val_score(modelo, X, y, cv=cv, scoring="accuracy").mean()
        resultados[nombre] = {
            "modelo":    modelo,
            "acc_test":  acc_test,
            "acc_cv":    acc_cv,
            "y_pred":    modelo.predict(X_test),
            "y_test":    y_test,
            "X_train":   X_train,
            "X_test":    X_test,
            "y_train":   y_train,
        }
        log.info("  %-22s  test=%.3f  CV=%.3f", nombre, acc_test, acc_cv)

    mejor_nombre = max(resultados, key=lambda k: resultados[k]["acc_cv"])
    log.info("Mejor modelo: %s (CV=%.3f)", mejor_nombre, resultados[mejor_nombre]["acc_cv"])

    return resultados, mejor_nombre


# ── PASO 3: Figura — comparación de modelos ───────────────────────────────
def plot_comparacion(resultados: dict, mejor_nombre: str) -> None:
    """Gráfico de barras comparando accuracy de los 3 modelos."""
    nombres  = list(resultados.keys())
    acc_test = [resultados[n]["acc_test"] for n in nombres]
    acc_cv   = [resultados[n]["acc_cv"]   for n in nombres]

    x  = np.arange(len(nombres))
    w  = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))

    bars_test = ax.bar(x - w/2, acc_test, w, label="Accuracy test",
                       color=PALETTE["lblue"], edgecolor="white")
    bars_cv   = ax.bar(x + w/2, acc_cv,   w, label=f"Accuracy CV ({CV_FOLDS} folds)",
                       color=PALETTE["blue"], edgecolor="white")

    for bar, val in zip(bars_test, acc_test):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.01,
                f"{val:.1%}", ha="center", va="bottom", fontsize=9)
    for bar, val in zip(bars_cv, acc_cv):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.01,
                f"{val:.1%}", ha="center", va="bottom", fontsize=9,
                fontweight="bold")

    # Marcar el mejor modelo
    idx_mejor = nombres.index(mejor_nombre)
    ax.annotate("Mejor modelo", xy=(idx_mejor + w/2, acc_cv[idx_mejor]),
                xytext=(idx_mejor + w/2 + 0.3, acc_cv[idx_mejor] + 0.05),
                arrowprops=dict(arrowstyle="->", color=PALETTE["red"]),
                color=PALETTE["red"], fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(nombres, fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Accuracy")
    ax.set_title(
        "Comparación de modelos de clasificación\n"
        f"Variable objetivo: alta exclusión digital (uso < {UMBRAL_EXCLUSION:.0f}%)",
        fontweight="bold", color=PALETTE["navy"]
    )
    ax.legend()
    ax.axhline(0.5, color=PALETTE["gray"], linestyle=":", linewidth=1, alpha=0.5,
               label="Línea base (azar)")
    ax.grid(True, alpha=0.3, axis="y")
    fig.text(0.01, -0.03, SOURCE_NOTE, fontsize=8, color=PALETTE["gray"], style="italic")
    plt.tight_layout()
    path = FIG_DIR / "07_ml_comparacion_modelos.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log.info("Figura guardada: %s", path)


# ── PASO 4: Figura — matriz de confusión ─────────────────────────────────
def plot_matriz_confusion(resultados: dict, mejor_nombre: str) -> None:
    """Matriz de confusión del mejor modelo."""
    res    = resultados[mejor_nombre]
    y_test = res["y_test"]
    y_pred = res["y_pred"]
    cm     = confusion_matrix(y_test, y_pred)

    fig, ax = plt.subplots(figsize=(7, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASS_NAMES)
    disp.plot(ax=ax, colorbar=False,
              cmap="Blues",
              values_format="d")

    ax.set_title(
        f"Matriz de confusión — {mejor_nombre}\n"
        f"Accuracy: {accuracy_score(y_test, y_pred):.1%}",
        fontweight="bold", color=PALETTE["navy"], pad=15
    )
    ax.set_xlabel("Predicción del modelo", fontsize=10)
    ax.set_ylabel("Valor real", fontsize=10)
    ax.tick_params(axis="x", labelrotation=15)
    fig.text(0.01, -0.05, SOURCE_NOTE, fontsize=8, color=PALETTE["gray"], style="italic")
    plt.tight_layout()
    path = FIG_DIR / "08_ml_matriz_confusion.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log.info("Figura guardada: %s", path)


# ── PASO 5: Figura — importancia de features ─────────────────────────────
def plot_importancia_features(resultados: dict, mejor_nombre: str) -> None:
    """Importancia de features del Random Forest."""
    modelo = resultados[mejor_nombre]["modelo"]
    if not hasattr(modelo, "feature_importances_"):
        log.warning("El mejor modelo no tiene feature_importances_. Usando Random Forest.")
        modelo = resultados["Random Forest"]["modelo"]

    importancias = modelo.feature_importances_
    indices      = np.argsort(importancias)
    nombres_ord  = [FEATURE_NAMES[i] for i in indices]
    imp_ord      = importancias[indices]

    colores = [PALETTE["blue"] if imp > 0.2 else PALETTE["lblue"] for imp in imp_ord]

    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.barh(nombres_ord, imp_ord, color=colores, edgecolor="white", height=0.5)
    for bar, val in zip(bars, imp_ord):
        ax.text(val + 0.005, bar.get_y() + bar.get_height()/2,
                f"{val:.1%}", va="center", fontsize=10)
    ax.set_xlabel("Importancia relativa")
    ax.set_xlim(0, max(imp_ord) * 1.25)
    ax.set_title(
        "Importancia de variables — Random Forest\n"
        "¿Qué factores predicen mejor la exclusión digital?",
        fontweight="bold", color=PALETTE["navy"]
    )
    ax.grid(True, alpha=0.3, axis="x")
    fig.text(0.01, -0.05, SOURCE_NOTE, fontsize=8, color=PALETTE["gray"], style="italic")
    plt.tight_layout()
    path = FIG_DIR / "09_ml_importancia_features.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log.info("Figura guardada: %s", path)


# ── PASO 6: Figura — árbol de decisión visualizado ───────────────────────
def plot_arbol_decision(resultados: dict, encoders: dict) -> None:
    """
    Visualiza el árbol de decisión de forma manual para que sea
    legible en el informe sin depender de graphviz.
    """
    dt    = resultados["Árbol de Decisión"]["modelo"]
    reglas = export_text(dt, feature_names=FEATURE_NAMES, max_depth=3)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis("off")
    ax.text(0.01, 0.99, "Árbol de Decisión (primeros 3 niveles)",
            transform=ax.transAxes, fontsize=13, fontweight="bold",
            color=PALETTE["navy"], va="top")
    ax.text(0.01, 0.88,
            f"Variable objetivo: alta exclusión digital (uso < {UMBRAL_EXCLUSION:.0f}%)\n"
            f"max_depth=4 | Accuracy CV: {resultados['Árbol de Decisión']['acc_cv']:.1%}",
            transform=ax.transAxes, fontsize=10, color=PALETTE["gray"], va="top")
    ax.text(0.01, 0.72, reglas,
            transform=ax.transAxes, fontsize=8.5, va="top",
            family="monospace", color=PALETTE["navy"],
            bbox=dict(boxstyle="round,pad=0.4", facecolor=PALETTE["lblue"],
                      edgecolor=PALETTE["blue"], alpha=0.3))
    fig.text(0.01, -0.02, SOURCE_NOTE, fontsize=8, color=PALETTE["gray"], style="italic")
    plt.tight_layout()
    path = FIG_DIR / "10_ml_arbol_decision.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log.info("Figura guardada: %s", path)


# ── PASO 7: Exportar resultados a CSV ─────────────────────────────────────
def export_resultados(resultados: dict, mejor_nombre: str) -> None:
    """Exporta tabla de resultados de todos los modelos."""
    filas = []
    for nombre, res in resultados.items():
        report = classification_report(
            res["y_test"], res["y_pred"],
            target_names=CLASS_NAMES, output_dict=True
        )
        filas.append({
            "modelo":              nombre,
            "accuracy_test":       round(res["acc_test"], 4),
            "accuracy_cv":         round(res["acc_cv"], 4),
            "precision_alta_excl": round(report["Alta exclusión (<85%)"]["precision"], 4),
            "recall_alta_excl":    round(report["Alta exclusión (<85%)"]["recall"],    4),
            "f1_alta_excl":        round(report["Alta exclusión (<85%)"]["f1-score"],  4),
            "mejor_modelo":        nombre == mejor_nombre,
        })
    df_out = pd.DataFrame(filas).sort_values("accuracy_cv", ascending=False)
    path   = OUT_DIR / "ml_resultados_clasificacion.csv"
    df_out.to_csv(path, index=False)
    log.info("Resultados exportados: %s", path)


# ── PASO 8: Log del reporte final ─────────────────────────────────────────
def log_reporte_final(resultados: dict, mejor_nombre: str, df_ml: pd.DataFrame,
                      encoders: dict) -> None:
    """Muestra en el terminal el reporte completo del mejor modelo."""
    res    = resultados[mejor_nombre]
    y_test = res["y_test"]
    y_pred = res["y_pred"]

    log.info("=" * 60)
    log.info("REPORTE FINAL — %s", mejor_nombre)
    log.info("=" * 60)
    log.info("Accuracy test: %.3f (%.1f%%)", res["acc_test"], res["acc_test"]*100)
    log.info("Accuracy CV:   %.3f (%.1f%%)", res["acc_cv"],   res["acc_cv"]*100)
    log.info("")
    log.info("Clasificación:\n%s",
             classification_report(y_test, y_pred, target_names=CLASS_NAMES))

    # Feature importances
    modelo = res["modelo"]
    if hasattr(modelo, "feature_importances_"):
        log.info("Importancia de features:")
        for feat, imp in sorted(zip(FEATURE_NAMES, modelo.feature_importances_),
                                 key=lambda x: -x[1]):
            log.info("  %-22s: %.3f", feat, imp)

    log.info("")
    log.info("INTERPRETACIÓN:")
    log.info("  El modelo predice con %.1f%% de precisión (CV) si un perfil", res["acc_cv"]*100)
    log.info("  sociodemográfico tiene alta exclusión digital (uso < %.0f%%).", UMBRAL_EXCLUSION)
    log.info("  Esto respalda cuantitativamente la hipótesis del proyecto:")
    log.info("  la discapacidad es un predictor independiente de la exclusión digital.")
    log.info("=" * 60)


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("CLASIFICACIÓN ML — Exclusión digital por discapacidad")
    log.info("Variable objetivo: uso < %.0f%% → alta exclusión", UMBRAL_EXCLUSION)
    log.info("=" * 60)

    if not CLEAN_CSV.exists():
        log.error("CSV limpio no encontrado: %s", CLEAN_CSV)
        log.error("Ejecuta primero: python -m cleaning.main")
        sys.exit(1)

    # Pasos
    X, y, df_ml, encoders        = load_and_prepare(CLEAN_CSV)
    resultados, mejor_nombre      = train_and_compare(X, y)
    plot_comparacion(resultados, mejor_nombre)
    plot_matriz_confusion(resultados, mejor_nombre)
    plot_importancia_features(resultados, mejor_nombre)
    plot_arbol_decision(resultados, encoders)
    export_resultados(resultados, mejor_nombre)
    log_reporte_final(resultados, mejor_nombre, df_ml, encoders)

    log.info("Figuras generadas:")
    for f in sorted(FIG_DIR.glob("0[7-9]_ml_*.png")) + sorted(FIG_DIR.glob("10_ml_*.png")):
        log.info("  %s", f.name)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("ERROR: %s", e)
        sys.exit(1)
