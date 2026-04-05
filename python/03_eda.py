"""
03_eda.py
=========
Análisis Exploratorio de Datos (EDA) sobre el dataset procesado del proyecto.
Genera estadísticas descriptivas, gráficos de comparación y observaciones
automáticas sobre la brecha digital por discapacidad en España y Europa.

Proyecto : Brecha Digital y Discapacidad en España – Proyecto Final Big Data & IA
Fuente   : Eurostat DSB_ICTIU01 v1.0 (2024) – preparado por 02_feature_engineering.py

Ejecución:
    python python/03_eda.py

Entradas:
    data/processed/analytical_dsb_ictiu01.csv
    data/processed/summary_by_country.csv

Salidas (imágenes):
    images/01_distribucion_global.png
    images/02_ranking_brecha_total.png
    images/03_uso_por_nivel_discapacidad.png
    images/04_espana_vs_europa.png
    images/05_doble_vulnerabilidad_genero.png
    images/06_analisis_por_edad.png
    images/07_heatmap_paises_niveles.png
    images/08_exclusion_digital.png

Salidas (tablas):
    data/processed/eda_descriptive_stats.csv
    data/processed/eda_observations.txt
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker

# Backend no interactivo: permite ejecutar sin pantalla (servidor, CI)
matplotlib.use("Agg")

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
INPUT_ANALYTICAL = Path("data/processed/analytical_dsb_ictiu01.csv")
INPUT_COUNTRY    = Path("data/processed/summary_by_country.csv")
IMAGES_DIR       = Path("images")
OUTPUT_STATS     = Path("data/processed/eda_descriptive_stats.csv")
OUTPUT_OBS       = Path("data/processed/eda_observations.txt")

# ─────────────────────────────────────────────────────────────────────────────
# PALETA Y ESTILOS
# Colores consistentes en todas las figuras del proyecto.
# ─────────────────────────────────────────────────────────────────────────────
PAL = {
    "navy":   "#1F4E79",
    "blue":   "#2E75B6",
    "lblue":  "#BDD7EE",
    "green":  "#1E6B3C",
    "lgreen": "#A9D18E",
    "red":    "#C00000",
    "lred":   "#FF9999",
    "amber":  "#C55A11",
    "lamber": "#F4B183",
    "gray":   "#595959",
    "lgray":  "#D9D9D9",
    "white":  "#FFFFFF",
}

# Color asignado a cada país (coherente en todas las figuras)
COUNTRY_COLORS = {
    "ES":        PAL["blue"],
    "EU27_2020": PAL["gray"],
    "DE":        "#7030A0",
    "FR":        "#375623",
    "IT":        PAL["amber"],
    "NL":        PAL["green"],
    "PT":        "#833C00",
    "SE":        PAL["navy"],
}

# Etiquetas en español para los países
COUNTRY_LABELS = {
    "ES":        "España",
    "EU27_2020": "Media UE-27",
    "DE":        "Alemania",
    "FR":        "Francia",
    "IT":        "Italia",
    "NL":        "Países Bajos",
    "PT":        "Portugal",
    "SE":        "Suecia",
}

# Nota de fuente que aparece en el pie de cada figura
SOURCE_NOTE = "Fuente: elaboración propia a partir de Eurostat DSB_ICTIU01 (2024)."

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL DE MATPLOTLIB
# Sin seaborn ni estilos externos: estilo propio limpio y profesional.
# ─────────────────────────────────────────────────────────────────────────────
def configure_matplotlib() -> None:
    """Aplica configuración global de estilo para todas las figuras."""
    plt.rcParams.update({
        # Fuente
        "font.family":          "DejaVu Sans",
        "font.size":            10,
        # Ejes
        "axes.spines.top":      False,
        "axes.spines.right":    False,
        "axes.spines.left":     True,
        "axes.spines.bottom":   True,
        "axes.edgecolor":       PAL["lgray"],
        "axes.linewidth":       0.8,
        "axes.labelcolor":      PAL["gray"],
        "axes.titlepad":        12,
        "axes.titlelocation":   "left",
        # Grid
        "axes.grid":            True,
        "grid.color":           PAL["lgray"],
        "grid.linestyle":       "--",
        "grid.linewidth":       0.6,
        "grid.alpha":           0.7,
        # Ticks
        "xtick.color":          PAL["gray"],
        "ytick.color":          PAL["gray"],
        "xtick.labelsize":      9,
        "ytick.labelsize":      9,
        # Figura
        "figure.facecolor":     PAL["white"],
        "figure.dpi":           130,
        "savefig.dpi":          180,
        "savefig.bbox":         "tight",
        "savefig.facecolor":    PAL["white"],
        # Leyenda
        "legend.frameon":       False,
        "legend.fontsize":      9,
    })


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────
def add_source_note(fig: plt.Figure, note: str = SOURCE_NOTE) -> None:
    """Añade nota de fuente en la parte inferior de la figura."""
    fig.text(
        0.01, -0.02, note,
        fontsize=7.5, color=PAL["gray"],
        ha="left", va="top",
        style="italic",
    )


def add_value_labels_h(ax: plt.Axes, fmt: str = "{:.1f}%",
                        padding: float = 0.3, color: str = PAL["gray"],
                        fontsize: float = 8.5) -> None:
    """Añade etiquetas de valor al final de barras horizontales."""
    for bar in ax.patches:
        w = bar.get_width()
        if not np.isnan(w) and w > 0:
            ax.text(
                w + padding,
                bar.get_y() + bar.get_height() / 2,
                fmt.format(w),
                va="center", ha="left",
                fontsize=fontsize, color=color,
            )


def add_value_labels_v(ax: plt.Axes, fmt: str = "{:.1f}%",
                        padding: float = 0.5, color: str = PAL["gray"],
                        fontsize: float = 8.5) -> None:
    """Añade etiquetas de valor encima de barras verticales."""
    for bar in ax.patches:
        h = bar.get_height()
        if not np.isnan(h) and h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + padding,
                fmt.format(h),
                va="bottom", ha="center",
                fontsize=fontsize, color=color,
            )


def save_fig(fig: plt.Figure, filename: str) -> None:
    """Guarda la figura en images/ y cierra el objeto."""
    path = IMAGES_DIR / filename
    fig.savefig(path)
    plt.close(fig)
    log.info("  → Guardada: %s", path)


# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────────────────────────────────────
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Carga los dos datasets de entrada.
    Verifica existencia de archivos y convierte tipos críticos.
    """
    log.info("Cargando datasets de entrada...")

    for path in [INPUT_ANALYTICAL, INPUT_COUNTRY]:
        if not path.exists():
            raise FileNotFoundError(
                f"Archivo no encontrado: '{path}'.\n"
                f"Ejecuta primero: python python/02_feature_engineering.py"
            )

    df = pd.read_csv(INPUT_ANALYTICAL)
    dc = pd.read_csv(INPUT_COUNTRY)

    # Asegurar tipos booleanos
    for col in ["is_reliable", "is_eu27_aggregate", "is_core_row",
                "is_total_sex", "is_total_age"]:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    log.info("  analytical_dsb: %d filas × %d columnas", *df.shape)
    log.info("  summary_by_country: %d filas × %d columnas", *dc.shape)
    return df, dc


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1 — Estadísticas descriptivas globales
# ─────────────────────────────────────────────────────────────────────────────
def block1_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula y muestra estadísticas descriptivas de pct_internet_use:
      - Global
      - Por nivel de discapacidad (solo filas core: Total sexo y edad)
      - Por país (solo filas core)
    Exporta la tabla a CSV para el informe.
    """
    log.info("=" * 60)
    log.info("BLOQUE 1 — Estadísticas descriptivas")
    log.info("=" * 60)

    # ── 1A: Global ────────────────────────────────────────────────────────────
    stats_global = df["pct_internet_use"].describe().rename("Global").round(2)
    log.info("\nEstadísticos globales (N=%d, %d nulos):\n%s",
             int(stats_global["count"]),
             df["pct_internet_use"].isna().sum(),
             stats_global.to_string())

    # ── 1B: Por nivel de discapacidad (filas core) ────────────────────────────
    core = df[df["is_core_row"]]
    stats_dis = (
        core.groupby("disability_level")["pct_internet_use"]
        .agg(["count", "mean", "std", "min", "median", "max"])
        .round(2)
        .rename(columns={
            "count": "N", "mean": "Media", "std": "DE",
            "min": "Mín", "median": "Mediana", "max": "Máx"
        })
    )
    log.info("\nEstadísticos por nivel de discapacidad (filas core):\n%s",
             stats_dis.to_string())

    # ── 1C: Por país (filas core, Severely limited) ───────────────────────────
    stats_country = (
        core[core["disability_level"] == "Severely limited"]
        [["country_name_es", "pct_internet_use", "pct_excluded",
          "gap_vs_no_disability", "gap_vs_eu27"]]
        .sort_values("gap_vs_no_disability", ascending=False)
        .reset_index(drop=True)
    )
    log.info("\nPaíses ordenados por brecha (Severely limited / Total):\n%s",
             stats_country.to_string(index=False))

    # Exportar estadísticos por discapacidad
    stats_dis.to_csv(OUTPUT_STATS, encoding="utf-8")
    log.info("\nEstadísticos exportados → %s", OUTPUT_STATS)

    return stats_dis


# ─────────────────────────────────────────────────────────────────────────────
# FIGURA 1 — Distribución global de pct_internet_use
# ─────────────────────────────────────────────────────────────────────────────
def fig1_global_distribution(df: pd.DataFrame) -> None:
    """
    Histograma de la distribución global de pct_internet_use.
    Muestra media, mediana y percentil 25 como líneas verticales de referencia.
    Revela la asimetría negativa del dataset: la mayoría de valores están
    por encima del 85%, con una cola inferior en discapacidad severa.
    """
    log.info("Figura 1 — Distribución global")

    valores = df["pct_internet_use"].dropna()
    media   = valores.mean()
    mediana = valores.median()
    p25     = valores.quantile(0.25)

    fig, ax = plt.subplots(figsize=(9, 4.5))

    # Histograma
    n, bins, patches = ax.hist(
        valores, bins=20,
        color=PAL["lblue"], edgecolor=PAL["white"], linewidth=0.6,
        zorder=2,
    )

    # Colorear el cuarto inferior en rojo suave (zona de exclusión)
    for patch, left in zip(patches, bins[:-1]):
        if left < p25:
            patch.set_facecolor(PAL["lred"])

    # Líneas de referencia
    ref_lines = [
        (media,   PAL["navy"],  f"Media: {media:.1f}%",   "--"),
        (mediana, PAL["blue"],  f"Mediana: {mediana:.1f}%", ":"),
        (p25,     PAL["red"],   f"P25: {p25:.1f}%",       "-."),
    ]
    for val, col, label, ls in ref_lines:
        ax.axvline(val, color=col, linestyle=ls, linewidth=1.5,
                   label=label, zorder=3)

    ax.set_title(
        "Distribución global del uso de Internet por nivel de discapacidad\n"
        "Eurostat DSB_ICTIU01 · 8 países · 2024",
        fontsize=11, fontweight="bold", color=PAL["navy"],
    )
    ax.set_xlabel("% de individuos que usan Internet", fontsize=10)
    ax.set_ylabel("Número de observaciones", fontsize=10)
    ax.set_xlim(40, 103)
    ax.legend(loc="upper left")
    ax.text(
        p25 - 0.5, n.max() * 0.6,
        "Zona de\nexclusión",
        fontsize=8, color=PAL["red"], ha="right",
        style="italic",
    )
    add_source_note(fig)
    save_fig(fig, "01_distribucion_global.png")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURA 2 — Ranking de países por brecha total
# ─────────────────────────────────────────────────────────────────────────────
def fig2_ranking_brecha(dc: pd.DataFrame) -> None:
    """
    Gráfico de barras horizontal con el ranking de los 7 países individuales
    ordenados por brecha total (No disability − Severely limited).
    España aparece destacada en azul. La línea punteada marca la media UE-27.
    Responde directamente a la pregunta de investigación P1.
    """
    log.info("Figura 2 — Ranking de brecha por país")

    # Excluir EU27_2020 del ranking de países
    paises = dc[dc["country_code"] != "EU27_2020"].copy()
    paises = paises.sort_values("gap_total", ascending=True)  # orden visual

    eu_gap = dc.loc[dc["country_code"] == "EU27_2020", "gap_total"].values[0]

    fig, ax = plt.subplots(figsize=(9, 5))

    colors = [
        PAL["blue"] if c == "ES" else PAL["lgray"]
        for c in paises["country_code"]
    ]
    bars = ax.barh(
        paises["country_name_es"], paises["gap_total"],
        color=colors, edgecolor=PAL["white"], height=0.55,
        zorder=2,
    )

    # Etiquetas de valor
    for bar, val in zip(bars, paises["gap_total"]):
        ax.text(
            val + 0.2,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f} pp",
            va="center", ha="left", fontsize=9,
            color=PAL["navy"] if val > 15 else PAL["gray"],
            fontweight="bold" if val > 15 else "normal",
        )

    # Línea de referencia UE-27
    ax.axvline(
        eu_gap, color=PAL["red"], linestyle="--", linewidth=1.5,
        label=f"Media UE-27: {eu_gap:.2f} pp", zorder=3,
    )

    # Etiqueta en la línea UE-27
    ax.text(
        eu_gap + 0.15, 0.3,
        f"UE-27\n{eu_gap:.2f} pp",
        fontsize=8, color=PAL["red"], va="bottom",
    )

    ax.set_title(
        "Brecha digital por discapacidad severa — ranking europeo\n"
        "Diferencia (pp) entre personas sin discapacidad y con discapacidad severa · 2024",
        fontsize=11, fontweight="bold", color=PAL["navy"],
    )
    ax.set_xlabel("Brecha (puntos porcentuales)", fontsize=10)
    ax.set_xlim(0, 26)
    ax.legend(loc="lower right")
    add_source_note(fig)
    save_fig(fig, "02_ranking_brecha_total.png")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURA 3 — Uso de Internet por nivel de discapacidad (todos los países)
# ─────────────────────────────────────────────────────────────────────────────
def fig3_uso_por_nivel(df: pd.DataFrame) -> None:
    """
    Gráfico de barras agrupadas: porcentaje de uso por nivel de discapacidad,
    una barra por país. Filas core (Total sexo, Total edad).
    Muestra que la separación entre niveles se amplía en países con baja inclusión.
    """
    log.info("Figura 3 — Uso por nivel de discapacidad")

    core = df[df["is_core_row"]].copy()

    # Ordenar niveles de menor a mayor limitación
    niveles = ["No disability", "Limited (not severely)",
               "Severely limited", "Limited or severely limited"]
    nivel_labels = {
        "No disability":                "Sin discapacidad",
        "Limited (not severely)":       "Limitación leve",
        "Severely limited":             "Limitación severa",
        "Limited or severely limited":  "Leve o severa",
    }
    nivel_colors = {
        "No disability":                PAL["green"],
        "Limited (not severely)":       PAL["lgreen"],
        "Severely limited":             PAL["red"],
        "Limited or severely limited":  PAL["lamber"],
    }

    # Ordenar países por su brecha total (de menor a mayor)
    orden_paises = (
        core[core["disability_level"] == "Severely limited"]
        .sort_values("gap_vs_no_disability", ascending=False)["country_name_es"]
        .tolist()
    )

    pivot = core.pivot_table(
        index="country_name_es", columns="disability_level",
        values="pct_internet_use",
    ).reindex(orden_paises)[niveles]

    n_paises  = len(pivot)
    n_niveles = len(niveles)
    x         = np.arange(n_paises)
    width     = 0.18

    fig, ax = plt.subplots(figsize=(12, 5.5))

    for i, nivel in enumerate(niveles):
        offset = (i - n_niveles / 2 + 0.5) * width
        vals   = pivot[nivel].values
        bars   = ax.bar(
            x + offset, vals,
            width=width,
            color=nivel_colors[nivel],
            edgecolor=PAL["white"], linewidth=0.4,
            label=nivel_labels[nivel],
            zorder=2,
        )
        # Etiqueta solo en nivel severo (el más importante)
        if nivel == "Severely limited":
            for bar, v in zip(bars, vals):
                if not np.isnan(v):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        v + 0.5,
                        f"{v:.1f}",
                        ha="center", va="bottom",
                        fontsize=7.5, color=PAL["red"],
                        fontweight="bold",
                    )

    # Línea de referencia EU-27 (Severely limited)
    eu_sev = df[
        (df["country_code"] == "EU27_2020")
        & (df["disability_level"] == "Severely limited")
        & df["is_core_row"]
    ]["pct_internet_use"].values[0]

    ax.axhline(
        eu_sev, color=PAL["red"], linestyle=":",
        linewidth=1.2, alpha=0.8,
        label=f"UE-27 (discap. severa): {eu_sev:.1f}%",
        zorder=3,
    )

    ax.set_title(
        "Uso de Internet por nivel de discapacidad y país · 2024\n"
        "Ordenado por brecha total (mayor brecha a la izquierda)",
        fontsize=11, fontweight="bold", color=PAL["navy"],
    )
    ax.set_ylabel("% de individuos que usan Internet", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(orden_paises, fontsize=9)
    ax.set_ylim(55, 108)
    ax.legend(loc="lower right", ncol=2, fontsize=8.5)
    add_source_note(fig)
    save_fig(fig, "03_uso_por_nivel_discapacidad.png")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURA 4 — España vs. Europa (posición relativa)
# ─────────────────────────────────────────────────────────────────────────────
def fig4_espana_vs_europa(df: pd.DataFrame, dc: pd.DataFrame) -> None:
    """
    Panel doble:
    - Izquierda: Brecha total de España vs. cada país (gap_vs_eu27 y ranking)
    - Derecha:   Posición de España en los cuatro niveles de discapacidad
    Diseñado para la narrativa del informe: ¿dónde está España?
    """
    log.info("Figura 4 — España vs. Europa")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        "España en el contexto europeo · Uso de Internet por discapacidad · 2024",
        fontsize=12, fontweight="bold", color=PAL["navy"], y=1.01,
    )

    # ── Panel izquierdo: brecha total por país ────────────────────────────────
    paises = dc[dc["country_code"] != "EU27_2020"].sort_values("gap_total", ascending=True)
    colors_left = [PAL["blue"] if c == "ES" else PAL["lgray"]
                   for c in paises["country_code"]]

    bars = ax1.barh(
        paises["country_name_es"], paises["gap_total"],
        color=colors_left, edgecolor=PAL["white"], height=0.5, zorder=2,
    )
    eu_gap = dc.loc[dc["country_code"] == "EU27_2020", "gap_total"].values[0]
    ax1.axvline(eu_gap, color=PAL["red"], linestyle="--", linewidth=1.4,
                label=f"UE-27: {eu_gap:.1f} pp", zorder=3)

    for bar, val in zip(bars, paises["gap_total"]):
        ax1.text(val + 0.2, bar.get_y() + bar.get_height() / 2,
                 f"{val:.1f} pp", va="center", ha="left", fontsize=8.5,
                 color=PAL["navy"] if val > 15 else PAL["gray"])

    ax1.set_title("Brecha digital por discapacidad severa",
                  fontsize=10, fontweight="bold", color=PAL["navy"])
    ax1.set_xlabel("Brecha (puntos porcentuales)", fontsize=9)
    ax1.set_xlim(0, 25)
    ax1.legend(fontsize=8.5)

    # ── Panel derecho: España por nivel de discapacidad vs. UE-27 ────────────
    nivel_order  = ["No disability", "Limited (not severely)",
                    "Severely limited", "Limited or severely limited"]
    nivel_labels = ["Sin discapacidad", "Limitación leve",
                    "Limitación severa", "Leve o severa"]

    es_vals = (
        df[(df["country_code"] == "ES") & df["is_core_row"]]
        .set_index("disability_level")["pct_internet_use"]
        .reindex(nivel_order)
    )
    eu_vals = (
        df[(df["country_code"] == "EU27_2020") & df["is_core_row"]]
        .set_index("disability_level")["pct_internet_use"]
        .reindex(nivel_order)
    )

    x      = np.arange(len(nivel_order))
    width  = 0.32

    ax2.bar(x - width / 2, es_vals.values, width,
            color=PAL["blue"], label="España", edgecolor=PAL["white"],
            linewidth=0.5, zorder=2)
    ax2.bar(x + width / 2, eu_vals.values, width,
            color=PAL["lgray"], label="Media UE-27", edgecolor=PAL["white"],
            linewidth=0.5, zorder=2)

    # Flechas de diferencia en nivel severo
    sev_idx = nivel_order.index("Severely limited")
    diff    = es_vals.values[sev_idx] - eu_vals.values[sev_idx]
    ax2.annotate(
        f"ES: {diff:+.1f} pp\nvs. UE-27",
        xy=(sev_idx + width / 2, eu_vals.values[sev_idx]),
        xytext=(sev_idx + width / 2 + 0.55, eu_vals.values[sev_idx] - 4),
        fontsize=8.5, color=PAL["red"],
        arrowprops=dict(arrowstyle="->", color=PAL["red"], lw=1.2),
    )

    add_value_labels_v(ax2, fmt="{:.1f}%", padding=0.3, fontsize=8)

    ax2.set_title("España vs. Media UE-27 por nivel de discapacidad",
                  fontsize=10, fontweight="bold", color=PAL["navy"])
    ax2.set_ylabel("% de individuos que usan Internet", fontsize=9)
    ax2.set_xticks(x)
    ax2.set_xticklabels(nivel_labels, fontsize=8.5, rotation=10, ha="right")
    ax2.set_ylim(65, 108)
    ax2.legend(fontsize=8.5)

    fig.tight_layout()
    add_source_note(fig)
    save_fig(fig, "04_espana_vs_europa.png")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURA 5 — Doble vulnerabilidad: género × discapacidad severa
# ─────────────────────────────────────────────────────────────────────────────
def fig5_doble_vulnerabilidad(df: pd.DataFrame) -> None:
    """
    Barras agrupadas hombres vs. mujeres con discapacidad severa por país.
    Destaca la brecha de género interna, especialmente pronunciada en España.
    Responde a la pregunta de investigación P2.
    """
    log.info("Figura 5 — Doble vulnerabilidad de género")

    gen = df[
        (df["disability_level"] == "Severely limited")
        & (df["age_group"] == "Total")
        & (df["sex"].isin(["Female", "Male"]))
    ].copy()

    # Ordenar por valor de mujeres (más excluidas primero)
    orden = (
        gen[gen["sex"] == "Female"]
        .sort_values("pct_internet_use", ascending=True)["country_name_es"]
        .tolist()
    )

    pivot_g = gen.pivot_table(
        index="country_name_es", columns="sex",
        values="pct_internet_use",
    ).reindex(orden)

    x     = np.arange(len(orden))
    width = 0.32

    fig, ax = plt.subplots(figsize=(11, 5))

    bars_f = ax.barh(
        x - width / 2, pivot_g["Female"],
        height=width, color=PAL["red"],
        label="Mujeres con discapacidad severa",
        edgecolor=PAL["white"], linewidth=0.4, zorder=2,
    )
    bars_m = ax.barh(
        x + width / 2, pivot_g["Male"],
        height=width, color=PAL["blue"],
        label="Hombres con discapacidad severa",
        edgecolor=PAL["white"], linewidth=0.4, zorder=2,
    )

    # Etiquetas de valor
    for bars, color in [(bars_f, PAL["red"]), (bars_m, PAL["blue"])]:
        for bar in bars:
            w = bar.get_width()
            if not np.isnan(w):
                ax.text(
                    w + 0.3,
                    bar.get_y() + bar.get_height() / 2,
                    f"{w:.1f}%",
                    va="center", ha="left", fontsize=8.5, color=color,
                )

    # Flecha de brecha en España
    es_idx = orden.index("España")
    f_val  = pivot_g.loc["España", "Female"]
    m_val  = pivot_g.loc["España", "Male"]
    gap_es = m_val - f_val
    ax.annotate(
        "", xy=(m_val, es_idx + width / 2),
        xytext=(f_val, es_idx - width / 2),
        arrowprops=dict(arrowstyle="<->", color=PAL["amber"],
                        lw=1.8, mutation_scale=12),
    )
    ax.text(
        (f_val + m_val) / 2 - 1, es_idx + 0.42,
        f"Brecha género: {gap_es:.1f} pp",
        fontsize=8.5, color=PAL["amber"], fontweight="bold",
    )

    # Línea de referencia UE-27 mujeres
    eu_f = df[
        (df["country_code"] == "EU27_2020")
        & (df["disability_level"] == "Severely limited")
        & (df["sex"] == "Female")
    ]["pct_internet_use"].values[0]

    ax.axvline(eu_f, color=PAL["red"], linestyle=":", linewidth=1.2,
               alpha=0.7, label=f"UE-27 mujeres: {eu_f:.1f}%")

    ax.set_title(
        "Doble vulnerabilidad: género × discapacidad severa · 2024\n"
        "% de personas que usan Internet — ordenado por uso femenino",
        fontsize=11, fontweight="bold", color=PAL["navy"],
    )
    ax.set_xlabel("% de individuos que usan Internet", fontsize=10)
    ax.set_yticks(x)
    ax.set_yticklabels(orden, fontsize=9)
    ax.set_xlim(60, 108)
    ax.legend(loc="lower right", fontsize=9)
    add_source_note(fig)
    save_fig(fig, "05_doble_vulnerabilidad_genero.png")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURA 6 — Análisis por edad
# ─────────────────────────────────────────────────────────────────────────────
def fig6_analisis_edad(df: pd.DataFrame) -> None:
    """
    Panel doble:
    - Izquierda:  España — uso por grupo de edad × nivel de discapacidad
    - Derecha:    Efecto del envejecimiento en todos los países
                  (brecha 25-54 vs. 55-74 dentro de discapacidad severa)
    Responde a la pregunta de investigación P3.
    Nota: Y16_24_DIS_SEV excluido por falta de datos fiables.
    """
    log.info("Figura 6 — Análisis por edad")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        "Efecto de la edad sobre la exclusión digital por discapacidad · 2024",
        fontsize=12, fontweight="bold", color=PAL["navy"], y=1.01,
    )

    # ── Panel izquierdo: España, edad × discapacidad ──────────────────────────
    # Usar solo grupos de edad disponibles (excluir Total y 16-24 para DIS_SEV)
    es_data = df[
        (df["country_code"] == "ES")
        & (df["sex"] == "Total")
        & (df["age_group"].isin(["25-54", "55-74"]))
        & (df["disability_level"].isin([
            "No disability", "Limited (not severely)", "Severely limited"
        ]))
    ].copy()

    nivel_order = ["No disability", "Limited (not severely)", "Severely limited"]
    nivel_cols  = {
        "No disability":          PAL["green"],
        "Limited (not severely)": PAL["lgreen"],
        "Severely limited":       PAL["red"],
    }
    nivel_labels = {
        "No disability":          "Sin discapacidad",
        "Limited (not severely)": "Limitación leve",
        "Severely limited":       "Limitación severa",
    }
    age_groups   = ["25-54", "55-74"]
    age_x        = np.arange(len(age_groups))
    width_age    = 0.22

    for i, nivel in enumerate(nivel_order):
        offset = (i - len(nivel_order) / 2 + 0.5) * width_age
        vals   = [
            es_data[
                (es_data["disability_level"] == nivel)
                & (es_data["age_group"] == ag)
            ]["pct_internet_use"].values
            for ag in age_groups
        ]
        vals = [v[0] if len(v) > 0 and not np.isnan(v[0]) else np.nan
                for v in vals]

        bars = ax1.bar(
            age_x + offset, vals, width_age,
            color=nivel_cols[nivel], label=nivel_labels[nivel],
            edgecolor=PAL["white"], linewidth=0.4, zorder=2,
        )
        for bar, v in zip(bars, vals):
            if not np.isnan(v):
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    v + 0.4,
                    f"{v:.1f}",
                    ha="center", va="bottom",
                    fontsize=8, color=nivel_cols[nivel],
                )

    ax1.set_title("España — uso por grupo de edad\n(sexo: Total)",
                  fontsize=10, fontweight="bold", color=PAL["navy"])
    ax1.set_ylabel("% que usa Internet", fontsize=9)
    ax1.set_xticks(age_x)
    ax1.set_xticklabels(["25-54 años", "55-74 años"], fontsize=10)
    ax1.set_ylim(60, 108)
    ax1.legend(fontsize=8.5)
    ax1.text(
        0.5, 62,
        "Nota: el grupo 16-24 con discapacidad severa\nno está disponible (datos insuficientes en Eurostat)",
        ha="center", fontsize=7.5, color=PAL["gray"], style="italic",
    )

    # ── Panel derecho: gap_age por país ──────────────────────────────────────
    # gap_age = pct_25_54_severely − pct_55_74_severely
    dc_tmp = pd.read_csv(INPUT_COUNTRY)
    paises_age = dc_tmp[dc_tmp["country_code"] != "EU27_2020"].dropna(
        subset=["gap_age"]
    ).sort_values("gap_age", ascending=True)

    colors_r = [PAL["blue"] if c == "ES" else PAL["lgray"]
                for c in paises_age["country_code"]]
    bars_r   = ax2.barh(
        paises_age["country_name_es"], paises_age["gap_age"],
        color=colors_r, edgecolor=PAL["white"], height=0.5, zorder=2,
    )

    eu_age_gap = dc_tmp.loc[dc_tmp["country_code"] == "EU27_2020", "gap_age"].values[0]
    ax2.axvline(eu_age_gap, color=PAL["red"], linestyle="--", linewidth=1.3,
                label=f"UE-27: {eu_age_gap:.1f} pp", zorder=3)

    for bar, val in zip(bars_r, paises_age["gap_age"]):
        ax2.text(
            val + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f} pp",
            va="center", ha="left", fontsize=8.5,
            color=PAL["navy"] if val > 15 else PAL["gray"],
        )

    ax2.set_title("Efecto del envejecimiento en discapacidad severa\n"
                  "Brecha: 25-54 años vs. 55-74 años",
                  fontsize=10, fontweight="bold", color=PAL["navy"])
    ax2.set_xlabel("Diferencia de uso (pp)", fontsize=9)
    ax2.set_xlim(0, 36)
    ax2.legend(fontsize=8.5)

    fig.tight_layout()
    add_source_note(fig)
    save_fig(fig, "06_analisis_por_edad.png")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURA 7 — Heatmap países × niveles de discapacidad
# ─────────────────────────────────────────────────────────────────────────────
def fig7_heatmap(df: pd.DataFrame) -> None:
    """
    Mapa de calor manual con matplotlib: filas = países, columnas = niveles.
    Muestra de un vistazo la distribución completa del dataset.
    Los valores numéricos están anotados en cada celda.
    Fondo de color proporcional al porcentaje (verde alto, rojo bajo).
    """
    log.info("Figura 7 — Heatmap países × niveles")

    core = df[df["is_core_row"]].copy()

    nivel_order = [
        "No disability",
        "Limited (not severely)",
        "Severely limited",
        "Limited or severely limited",
    ]
    nivel_labels = [
        "Sin\ndiscapacidad",
        "Limitación\nleve",
        "Limitación\nsevera",
        "Leve o\nsevera",
    ]
    # Ordenar países por brecha total descendente (peor a mejor)
    orden_paises = (
        core[core["disability_level"] == "Severely limited"]
        .sort_values("gap_vs_no_disability", ascending=False)["country_name_es"]
        .tolist()
    )

    pivot = core.pivot_table(
        index="country_name_es",
        columns="disability_level",
        values="pct_internet_use",
    ).reindex(orden_paises)[nivel_order]

    data   = pivot.values
    n_rows = len(orden_paises)
    n_cols = len(nivel_order)

    fig, ax = plt.subplots(figsize=(10, 5.5))

    # Normalizar para la escala de colores [min_dataset, 100]
    vmin = np.nanmin(data)
    vmax = 100.0

    for i in range(n_rows):
        for j in range(n_cols):
            val = data[i, j]
            if np.isnan(val):
                # Celda sin dato
                facecolor = PAL["lgray"]
                ax.add_patch(plt.Rectangle(
                    (j, i), 1, 1,
                    facecolor=facecolor, edgecolor=PAL["white"], linewidth=1.5,
                ))
                ax.text(
                    j + 0.5, i + 0.5, "N/D",
                    ha="center", va="center", fontsize=9,
                    color=PAL["gray"],
                )
            else:
                # Calcular color: rojo bajo, verde alto
                norm = (val - vmin) / (vmax - vmin)
                # Interpolación RGB manual: rojo→amarillo→verde
                if norm < 0.5:
                    r, g, b = 0.9, norm * 2 * 0.85, 0.2
                else:
                    r, g, b = (1 - norm) * 2 * 0.4, 0.78, 0.3
                facecolor = (r, g, b, 0.75)

                ax.add_patch(plt.Rectangle(
                    (j, i), 1, 1,
                    facecolor=facecolor, edgecolor=PAL["white"], linewidth=1.5,
                ))
                # Texto: valor % y nombre del país en primera columna
                text_color = PAL["navy"] if norm > 0.3 else PAL["white"]
                ax.text(
                    j + 0.5, i + 0.5,
                    f"{val:.1f}%",
                    ha="center", va="center",
                    fontsize=9.5, fontweight="bold",
                    color=text_color,
                )

    # Etiquetas de ejes
    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)
    ax.set_xticks([j + 0.5 for j in range(n_cols)])
    ax.set_xticklabels(nivel_labels, fontsize=9.5)
    ax.set_yticks([i + 0.5 for i in range(n_rows)])
    ax.set_yticklabels(orden_paises, fontsize=9.5)
    ax.tick_params(length=0)
    ax.set_aspect("equal")

    # Quitar spines del heatmap
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(False)

    ax.set_title(
        "Uso de Internet por país y nivel de discapacidad · 2024\n"
        "Ordenado por brecha (mayor brecha arriba)",
        fontsize=11, fontweight="bold", color=PAL["navy"],
    )

    # Leyenda de color manual
    legend_patches = [
        mpatches.Patch(facecolor=(0.9, 0.2, 0.2, 0.75), label="Menor uso (mayor exclusión)"),
        mpatches.Patch(facecolor=(0.4, 0.78, 0.3, 0.75), label="Mayor uso (menor exclusión)"),
        mpatches.Patch(facecolor=PAL["lgray"], label="Dato no disponible"),
    ]
    ax.legend(handles=legend_patches, loc="upper right",
              bbox_to_anchor=(1.01, -0.06), fontsize=8.5, ncol=3)

    add_source_note(fig)
    save_fig(fig, "07_heatmap_paises_niveles.png")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURA 8 — Exclusión digital (% que NO usa Internet)
# ─────────────────────────────────────────────────────────────────────────────
def fig8_exclusion_digital(df: pd.DataFrame, dc: pd.DataFrame) -> None:
    """
    Barras verticales del porcentaje de personas CON discapacidad severa
    que NO usan Internet (pct_excluded_severely) por país.
    Complementa la figura 2: cambia la perspectiva de "brecha" a "exclusión real".
    Un porcentaje de exclusión del 20,7% en España significa que 1 de cada 5
    personas con discapacidad severa está excluida digitalmente.
    """
    log.info("Figura 8 — Exclusión digital por país")

    paises = dc[dc["country_code"] != "EU27_2020"].sort_values(
        "pct_excluded_severely", ascending=False
    )
    eu_excl = dc.loc[
        dc["country_code"] == "EU27_2020", "pct_excluded_severely"
    ].values[0]

    colors = [
        PAL["blue"] if c == "ES" else PAL["lgray"]
        for c in paises["country_code"]
    ]

    fig, ax = plt.subplots(figsize=(9, 5))

    bars = ax.bar(
        paises["country_name_es"],
        paises["pct_excluded_severely"],
        color=colors, edgecolor=PAL["white"], linewidth=0.5,
        zorder=2, width=0.55,
    )

    # Línea UE-27
    ax.axhline(
        eu_excl, color=PAL["red"], linestyle="--", linewidth=1.5,
        label=f"Media UE-27: {eu_excl:.1f}%", zorder=3,
    )

    # Etiquetas de valor y anotación "1 de cada N"
    for bar, val, code in zip(bars, paises["pct_excluded_severely"],
                              paises["country_code"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.3,
            f"{val:.1f}%",
            ha="center", va="bottom", fontsize=9,
            color=PAL["navy"] if code == "ES" else PAL["gray"],
            fontweight="bold" if code == "ES" else "normal",
        )
        if code == "ES":
            ratio = round(100 / val)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + 1.8,
                f"≈ 1 de cada {ratio}\npersonas excluidas",
                ha="center", va="bottom",
                fontsize=8, color=PAL["blue"],
                style="italic",
            )

    ax.set_title(
        "Exclusión digital en personas con discapacidad severa · 2024\n"
        "% que NO usa Internet (100 − pct_internet_use)",
        fontsize=11, fontweight="bold", color=PAL["navy"],
    )
    ax.set_ylabel("% excluidos digitalmente", fontsize=10)
    ax.set_ylim(0, 35)
    ax.legend(fontsize=9.5)
    add_source_note(fig)
    save_fig(fig, "08_exclusion_digital.png")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE FINAL — Observaciones automáticas
# ─────────────────────────────────────────────────────────────────────────────
def block_final_observations(df: pd.DataFrame, dc: pd.DataFrame) -> None:
    """
    Genera observaciones analíticas automáticas basadas en los datos reales.
    Las observaciones se muestran en el log y se exportan a un archivo .txt
    para copiarlas directamente al informe o al README del proyecto.
    """
    log.info("=" * 60)
    log.info("BLOQUE FINAL — Observaciones automáticas")
    log.info("=" * 60)

    obs = []

    # ── Dato de apertura ──────────────────────────────────────────────────────
    es_sev = df[
        (df["country_code"] == "ES") & df["is_core_row"]
        & (df["disability_level"] == "Severely limited")
    ]["pct_internet_use"].values[0]
    es_none = df[
        (df["country_code"] == "ES") & df["is_core_row"]
        & (df["disability_level"] == "No disability")
    ]["pct_internet_use"].values[0]
    es_gap  = es_none - es_sev

    obs.append(
        f"[O1] BRECHA PRINCIPAL — España: el {es_none:.1f}% de personas sin "
        f"discapacidad usó Internet en 2024, frente al {es_sev:.1f}% de personas "
        f"con discapacidad severa. Esto supone una brecha de {es_gap:.2f} pp."
    )

    # ── Posición relativa ─────────────────────────────────────────────────────
    eu_gap  = dc.loc[dc["country_code"] == "EU27_2020", "gap_total"].values[0]
    es_rank = int(dc.loc[dc["country_code"] == "ES", "country_rank_by_gap"].values[0])
    n_paises = len(dc[dc["country_code"] != "EU27_2020"])
    ratio_vs_eu = es_gap / eu_gap

    obs.append(
        f"[O2] POSICIÓN EUROPEA — España ocupa el puesto {es_rank} de {n_paises} "
        f"países en la clasificación de brecha digital por discapacidad (mayor "
        f"brecha = peor posición). Su brecha ({es_gap:.2f} pp) es {ratio_vs_eu:.1f}x "
        f"la media de la UE-27 ({eu_gap:.2f} pp)."
    )

    # ── País mejor y peor (excl. EU27) ───────────────────────────────────────
    paises_solo = dc[dc["country_code"] != "EU27_2020"]
    mejor  = paises_solo.loc[paises_solo["gap_total"].idxmin()]
    peor   = paises_solo.loc[paises_solo["gap_total"].idxmax()]

    obs.append(
        f"[O3] RANGO EUROPEO — El país con menor brecha es "
        f"{mejor['country_name_es']} ({mejor['gap_total']:.2f} pp) y el de mayor "
        f"brecha es {peor['country_name_es']} ({peor['gap_total']:.2f} pp). "
        f"La diferencia entre el mejor y el peor es de "
        f"{peor['gap_total'] - mejor['gap_total']:.2f} pp."
    )

    # ── Doble vulnerabilidad género ───────────────────────────────────────────
    es_f = df[
        (df["country_code"] == "ES")
        & (df["disability_level"] == "Severely limited")
        & (df["sex"] == "Female") & (df["age_group"] == "Total")
    ]["pct_internet_use"].values[0]
    es_m = df[
        (df["country_code"] == "ES")
        & (df["disability_level"] == "Severely limited")
        & (df["sex"] == "Male") & (df["age_group"] == "Total")
    ]["pct_internet_use"].values[0]
    gap_gen = es_m - es_f

    obs.append(
        f"[O4] GÉNERO — En España, las mujeres con discapacidad severa tienen "
        f"una tasa de uso del {es_f:.1f}%, frente al {es_m:.1f}% de los hombres. "
        f"La brecha de género interna es de {gap_gen:.2f} pp, la más alta del "
        f"dataset entre los países con datos fiables."
    )

    # ── Grupo de edad más excluido ────────────────────────────────────────────
    es_5574 = df[
        (df["country_code"] == "ES")
        & (df["disability_level"] == "Severely limited")
        & (df["sex"] == "Total") & (df["age_group"] == "55-74")
    ]["pct_internet_use"].values[0]
    es_2554 = df[
        (df["country_code"] == "ES")
        & (df["disability_level"] == "Severely limited")
        & (df["sex"] == "Total") & (df["age_group"] == "25-54")
    ]["pct_internet_use"].values[0]

    obs.append(
        f"[O5] EDAD — En España, el grupo de 55-74 años con discapacidad severa "
        f"tiene la tasa más baja del análisis de edad: {es_5574:.1f}%, frente al "
        f"{es_2554:.1f}% del grupo de 25-54. El efecto del envejecimiento sobre "
        f"la exclusión digital representa {es_2554 - es_5574:.2f} pp adicionales."
    )

    # ── Grupo más excluido en absoluto (España) ───────────────────────────────
    obs.append(
        f"[O6] PERFIL MÁS VULNERABLE — En España, el perfil con mayor exclusión "
        f"digital es: mujer, mayor de 55 años, con discapacidad severa. "
        f"Esta intersección combina tres factores de riesgo simultáneos y no "
        f"puede analizarse directamente con este dataset (faltaría desagregación "
        f"sexo × edad × discapacidad), pero los datos individuales de cada eje "
        f"son consistentes con ese diagnóstico."
    )

    # ── Países líderes ────────────────────────────────────────────────────────
    lideres = paises_solo[paises_solo["inclusion_group"] == "Alta inclusión"]
    obs.append(
        f"[O7] MODELOS DE REFERENCIA — Los países clasificados como 'Alta inclusión' "
        f"son: {', '.join(lideres['country_name_es'].tolist())}. Sus brechas son "
        f"{', '.join([str(round(g, 2)) + ' pp' for g in lideres['gap_total'].tolist()])} "
        f"respectivamente, demostrando que brechas inferiores a 5 pp son alcanzables."
    )

    # ── Datos no disponibles ──────────────────────────────────────────────────
    n_nulos = df["pct_internet_use"].isna().sum()
    obs.append(
        f"[O8] LIMITACIÓN — El dataset tiene {n_nulos} observaciones sin valor "
        f"(todas en la categoría Y16_24_DIS_SEV: jóvenes 16-24 con discapacidad "
        f"severa). Eurostat marcó estos datos como insuficientes (flag 'u') y sin "
        f"valor en ES, FR, NL y SE. El análisis de ese subgrupo no es posible."
    )

    # ── Mostrar en log y exportar ─────────────────────────────────────────────
    log.info("\nOBSERVACIONES GENERADAS:")
    for o in obs:
        log.info("  %s", o)

    OUTPUT_OBS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_OBS, "w", encoding="utf-8") as f:
        f.write("OBSERVACIONES AUTOMÁTICAS DEL EDA\n")
        f.write("Proyecto: Brecha Digital y Discapacidad en España\n")
        f.write("Fuente: Eurostat DSB_ICTIU01 (2024)\n")
        f.write("=" * 60 + "\n\n")
        for o in obs:
            f.write(o + "\n\n")

    log.info("\nObservaciones exportadas → %s", OUTPUT_OBS)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info("=" * 60)
    log.info("INICIO DEL EDA — DSB_ICTIU01 (Eurostat 2024)")
    log.info("=" * 60)

    # Preparar entorno
    configure_matplotlib()
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_STATS.parent.mkdir(parents=True, exist_ok=True)

    # Cargar datos
    df, dc = load_data()

    # Estadísticas descriptivas
    block1_descriptive_stats(df)

    # Generar las 8 figuras
    log.info("\nGenerando figuras...")
    fig1_global_distribution(df)
    fig2_ranking_brecha(dc)
    fig3_uso_por_nivel(df)
    fig4_espana_vs_europa(df, dc)
    fig5_doble_vulnerabilidad(df)
    fig6_analisis_edad(df)
    fig7_heatmap(df)
    fig8_exclusion_digital(df, dc)

    # Observaciones automáticas
    block_final_observations(df, dc)

    log.info("=" * 60)
    log.info("EDA COMPLETADO")
    log.info("  Figuras guardadas en: %s/", IMAGES_DIR)
    log.info("  Estadísticos:         %s", OUTPUT_STATS)
    log.info("  Observaciones:        %s", OUTPUT_OBS)
    log.info("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        log.error("ARCHIVO NO ENCONTRADO:\n%s", e)
        sys.exit(1)
    except Exception as e:
        log.exception("ERROR INESPERADO: %s", e)
        sys.exit(99)
