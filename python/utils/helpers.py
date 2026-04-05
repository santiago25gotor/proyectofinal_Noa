"""
helpers.py
==========
Funciones auxiliares reutilizables para los notebooks del proyecto.
Proyecto: Brecha Digital y Discapacidad en España
Fuente:   Eurostat DSB_ICTIU01 (2024)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

# ── Paleta de colores del proyecto ────────────────────────────────────────
PALETTE = {
    "navy":    "#1F4E79",
    "blue":    "#2E75B6",
    "lblue":   "#D6E4F0",
    "green":   "#1E6B3C",
    "lgreen":  "#E2EFDA",
    "red":     "#C00000",
    "lred":    "#FCE4D6",
    "amber":   "#7F3F00",
    "lamber":  "#FFF2CC",
    "gray":    "#595959",
    "lgray":   "#F5F5F5",
    "spain":   "#2E75B6",   # Color específico para España
    "eu27":    "#595959",   # Color para la media UE-27
}

# Mapa de colores para países
COUNTRY_COLORS = {
    "ES": PALETTE["spain"],
    "EU27_2020": PALETTE["eu27"],
    "NL": PALETTE["green"],
    "SE": "#4CAF50",
    "DE": "#795548",
    "FR": "#9C27B0",
    "IT": "#FF9800",
    "PT": "#009688",
    "LT": PALETTE["red"],
}

# ── Rutas del proyecto ─────────────────────────────────────────────────────
def get_project_root() -> Path:
    """Retorna la raíz del proyecto."""
    return Path(__file__).parent.parent

def get_data_path(filename: str, folder: str = "raw") -> Path:
    """Retorna la ruta a un archivo de datos."""
    return get_project_root() / "data" / folder / filename

def get_figures_path(filename: str) -> Path:
    """Retorna la ruta para guardar figuras."""
    path = get_project_root() / "images" / "figures"
    path.mkdir(parents=True, exist_ok=True)
    return path / filename

def get_outputs_path(filename: str) -> Path:
    """Retorna la ruta para guardar outputs."""
    path = get_project_root() / "outputs" / "tables"
    path.mkdir(parents=True, exist_ok=True)
    return path / filename

# ── Carga y limpieza del dataset ──────────────────────────────────────────
COLS_KEEP = {
    "TIME_PERIOD": "anio",
    "geo": "pais_cod",
    "Geopolitical entity (reporting)": "pais_nombre",
    "ind_type": "categoria_cod",
    "Individual type": "categoria_desc",
    "OBS_VALUE": "pct_uso_internet",
    "OBS_FLAG": "flag_calidad",
}

COUNTRY_NAMES_ES = {
    "DE": "Alemania", "ES": "España", "EU27_2020": "Media UE-27",
    "FR": "Francia", "IT": "Italia", "LT": "Lituania",
    "NL": "Países Bajos", "PT": "Portugal", "SE": "Suecia",
}

def decode_ind_type(code: str) -> dict:
    """
    Decodifica un código ind_type en sus tres ejes:
    sexo, grupo de edad y nivel de discapacidad.
    """
    sex_map = {"F_": "Femenino", "M_": "Masculino"}
    age_map = {"Y16_24_": "16-24", "Y25_54_": "25-54", "Y55_74_": "55-74"}
    dis_map = {
        "DIS_NONE": "Sin discapacidad",
        "DIS_LTD": "Limitación leve",
        "DIS_SEV": "Limitación severa",
        "DIS_LTD_SEV": "Leve o severa (agrupada)",
    }

    sexo = "Total"
    for prefix, label in sex_map.items():
        if code.startswith(prefix):
            sexo = label
            code = code[len(prefix):]
            break

    edad = "Total"
    for prefix, label in age_map.items():
        if code.startswith(prefix):
            edad = label
            code = code[len(prefix):]
            break

    discapacidad = dis_map.get(code, code)
    return {"sexo": sexo, "grupo_edad": edad, "dis_nivel": discapacidad}


def load_and_clean(filepath: str | Path = None) -> pd.DataFrame:
    """
    Carga el CSV raw de Eurostat y devuelve un DataFrame limpio con:
    - Solo columnas relevantes renombradas
    - Columnas decodificadas (sexo, grupo_edad, dis_nivel)
    - Columna 'fiable' (bool)
    - pais_nombre en español
    """
    if filepath is None:
        filepath = get_data_path("dsb_ictiu01_eurostat_2024.csv", "raw")

    df = pd.read_csv(filepath)

    # Seleccionar y renombrar columnas
    df = df[list(COLS_KEEP.keys())].rename(columns=COLS_KEEP)

    # Crear columna de fiabilidad
    df["fiable"] = ~((df["flag_calidad"] == "u") | df["pct_uso_internet"].isna())

    # Decodificar ind_type en tres columnas
    decoded = df["categoria_cod"].apply(decode_ind_type).apply(pd.Series)
    df = pd.concat([df, decoded], axis=1)

    # Nombres de países en español
    df["pais_nombre_es"] = df["pais_cod"].map(COUNTRY_NAMES_ES)

    return df


def compute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula métricas derivadas por país a partir del dataset limpio.
    Retorna un DataFrame con una fila por país.
    """
    # Pivot para cálculos
    pivot = df[
        df["sexo"].isin(["Total"]) &
        df["grupo_edad"].isin(["Total"]) &
        df["dis_nivel"].isin(["Sin discapacidad", "Limitación severa"])
    ].pivot_table(index="pais_cod", columns="dis_nivel", values="pct_uso_internet")

    metrics = pd.DataFrame(index=pivot.index)

    # Brecha principal
    metrics["dis_none"] = pivot.get("Sin discapacidad")
    metrics["dis_sev"] = pivot.get("Limitación severa")
    metrics["gap_total"] = (metrics["dis_none"] - metrics["dis_sev"]).round(2)

    # Brecha de género dentro de DIS_SEV
    gen = df[
        df["dis_nivel"] == "Limitación severa"
    ].pivot_table(index="pais_cod", columns="sexo", values="pct_uso_internet")
    metrics["m_dis_sev"] = gen.get("Masculino")
    metrics["f_dis_sev"] = gen.get("Femenino")
    metrics["gap_genero"] = (metrics["m_dis_sev"] - metrics["f_dis_sev"]).round(2)

    # Brecha por edad (DIS_SEV)
    age = df[
        df["dis_nivel"] == "Limitación severa"
    ].pivot_table(index="pais_cod", columns="grupo_edad", values="pct_uso_internet")
    metrics["y25_54_dis_sev"] = age.get("25-54")
    metrics["y55_74_dis_sev"] = age.get("55-74")
    metrics["gap_edad"] = (metrics["y25_54_dis_sev"] - metrics["y55_74_dis_sev"]).round(2)

    # Posición relativa vs. EU27
    eu27_gap = metrics.loc["EU27_2020", "gap_total"] if "EU27_2020" in metrics.index else None
    if eu27_gap is not None:
        metrics["pos_relativa_eu"] = (metrics["gap_total"] - eu27_gap).round(2)

    # Reset index y añadir nombre en español
    metrics = metrics.reset_index()
    metrics["pais_nombre_es"] = metrics["pais_cod"].map(COUNTRY_NAMES_ES)

    return metrics


# ── Funciones de visualización ────────────────────────────────────────────
def setup_style():
    """Configura el estilo global de matplotlib para el proyecto."""
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    })


def bar_chart_brecha(df_metrics: pd.DataFrame, save: bool = True, filename: str = "fig_ranking_brecha.png"):
    """
    Gráfico de barras horizontal con el ranking de países por brecha total.
    España resaltada en azul.
    """
    setup_style()
    data = df_metrics[df_metrics["pais_cod"] != "EU27_2020"].sort_values("gap_total", ascending=True)
    eu_gap = df_metrics.loc[df_metrics["pais_cod"] == "EU27_2020", "gap_total"].values[0]

    colors = [PALETTE["spain"] if p == "ES" else PALETTE["gray"] for p in data["pais_cod"]]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(data["pais_nombre_es"], data["gap_total"], color=colors, edgecolor="white", height=0.6)
    ax.axvline(eu_gap, color=PALETTE["red"], linestyle="--", linewidth=1.5, label=f"Media UE-27: {eu_gap} pp")
    ax.bar_label(bars, fmt="%.2f pp", padding=4, fontsize=9, color=PALETTE["gray"])
    ax.set_xlabel("Brecha (puntos porcentuales)", fontsize=10)
    ax.set_title("Brecha digital por discapacidad severa\nEspaña y pares europeos (Eurostat 2024)", fontsize=12, fontweight="bold", color=PALETTE["navy"])
    ax.legend(fontsize=9)
    ax.set_xlim(0, max(data["gap_total"]) * 1.15)
    fig.text(0.01, -0.02, "Fuente: elaboración propia a partir de Eurostat DSB_ICTIU01 (2024). Brecha = % sin discapacidad − % con discapacidad severa.", fontsize=7, color=PALETTE["gray"])
    plt.tight_layout()
    if save:
        plt.savefig(get_figures_path(filename))
    return fig, ax


def save_figure(fig, filename: str):
    """Guarda una figura en la carpeta de imágenes del proyecto."""
    fig.savefig(get_figures_path(filename), dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figura guardada: images/figures/{filename}")
