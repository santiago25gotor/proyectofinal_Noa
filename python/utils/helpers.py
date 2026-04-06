"""
utils/helpers.py — Funciones auxiliares para notebooks y scripts del proyecto.
Usadas principalmente desde los notebooks .ipynb.

Proyecto: Brecha Digital y Discapacidad en España
Fuente:   Eurostat DSB_ICTIU01 v1.0 (2024)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ── Paleta del proyecto ───────────────────────────────────────────────────
PALETTE: dict[str, str] = {
    "navy":   "#1F4E79",
    "blue":   "#2E75B6",
    "lblue":  "#D6E4F0",
    "green":  "#1E6B3C",
    "lgreen": "#E2EFDA",
    "red":    "#C00000",
    "lred":   "#FCE4D6",
    "amber":  "#7F3F00",
    "lamber": "#FFF2CC",
    "gray":   "#595959",
    "lgray":  "#F5F5F5",
}

# ── Nombres en español ────────────────────────────────────────────────────
# CORRECCIÓN: Lituania (LT) incluida — presenta la mayor brecha del dataset
COUNTRY_NAMES_ES: dict[str, str] = {
    "DE":        "Alemania",
    "ES":        "España",
    "EU27_2020": "Media UE-27",
    "FR":        "Francia",
    "IT":        "Italia",
    "LT":        "Lituania",      # ← CORRECCIÓN: faltaba en versión anterior
    "NL":        "Países Bajos",
    "PT":        "Portugal",
    "SE":        "Suecia",
}

COUNTRY_COLORS: dict[str, str] = {
    "ES":        PALETTE["blue"],
    "EU27_2020": PALETTE["gray"],
    "NL":        PALETTE["green"],
    "SE":        "#4CAF50",
    "DE":        "#795548",
    "FR":        "#9C27B0",
    "IT":        "#FF9800",
    "PT":        "#009688",
    "LT":        PALETTE["red"],   # ← CORRECCIÓN: faltaba
}

# ── Rutas del proyecto ─────────────────────────────────────────────────────
def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def get_figures_path(filename: str) -> Path:
    path = get_project_root() / "images" / "figures"
    path.mkdir(parents=True, exist_ok=True)
    return path / filename


def get_outputs_path(filename: str) -> Path:
    path = get_project_root() / "outputs" / "tables"
    path.mkdir(parents=True, exist_ok=True)
    return path / filename


# ── Mapeos de columnas del CSV raw (para notebooks) ──────────────────────
_COLS_KEEP = {
    "TIME_PERIOD":                      "anio",
    "geo":                              "pais_cod",
    "Geopolitical entity (reporting)":  "pais_nombre",
    "ind_type":                         "categoria_cod",
    "Individual type":                  "categoria_desc",
    "OBS_VALUE":                        "pct_uso_internet",
    "OBS_FLAG":                         "flag_calidad",
}

_SEX_MAP   = {"F_": "Femenino", "M_": "Masculino"}
_AGE_MAP   = {"Y16_24_": "16-24", "Y25_54_": "25-54", "Y55_74_": "55-74"}
_DIS_MAP   = {
    "DIS_NONE":    "Sin discapacidad",
    "DIS_LTD":     "Limitación leve",
    "DIS_SEV":     "Limitación severa",
    "DIS_LTD_SEV": "Leve o severa (agrupada)",
}


def decode_ind_type(code: str) -> dict:
    """Descompone un código ind_type en sexo, grupo_edad y dis_nivel."""
    remaining = code
    sexo = "Total"
    for prefix, label in _SEX_MAP.items():
        if remaining.startswith(prefix):
            sexo, remaining = label, remaining[len(prefix):]
            break
    edad = "Total"
    for prefix, label in _AGE_MAP.items():
        if remaining.startswith(prefix):
            edad, remaining = label, remaining[len(prefix):]
            break
    return {"sexo": sexo, "grupo_edad": edad, "dis_nivel": _DIS_MAP.get(remaining, remaining)}


def load_and_clean(filepath=None) -> pd.DataFrame:
    """
    Carga el CSV raw de Eurostat y devuelve un DataFrame limpio con nombres en español.
    Incluye todos los países: ES, DE, FR, IT, NL, PT, SE, LT, EU27_2020.
    """
    if filepath is None:
        filepath = get_project_root() / "data" / "raw" / "dsb_ictiu01_eurostat_2024.csv"

    df = pd.read_csv(filepath)
    df = df[list(_COLS_KEEP.keys())].rename(columns=_COLS_KEEP)
    df["fiable"]         = ~((df["flag_calidad"] == "u") | df["pct_uso_internet"].isna())
    decoded              = df["categoria_cod"].apply(decode_ind_type).apply(pd.Series)
    df                   = pd.concat([df, decoded], axis=1)
    df["pais_nombre_es"] = df["pais_cod"].map(COUNTRY_NAMES_ES)
    return df


def compute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula métricas derivadas por país. Devuelve una fila por país."""
    core = df[df["sexo"] == "Total"][df["grupo_edad"] == "Total"]
    pivot = core[core["dis_nivel"].isin(["Sin discapacidad", "Limitación severa"])].pivot_table(
        index="pais_cod", columns="dis_nivel", values="pct_uso_internet"
    )
    metrics = pd.DataFrame(index=pivot.index)
    metrics["dis_none"] = pivot.get("Sin discapacidad")
    metrics["dis_sev"]  = pivot.get("Limitación severa")
    metrics["gap_total"] = (metrics["dis_none"] - metrics["dis_sev"]).round(2)

    gen = df[df["dis_nivel"] == "Limitación severa"].pivot_table(
        index="pais_cod", columns="sexo", values="pct_uso_internet"
    )
    metrics["m_dis_sev"]  = gen.get("Masculino")
    metrics["f_dis_sev"]  = gen.get("Femenino")
    metrics["gap_genero"] = (metrics["m_dis_sev"] - metrics["f_dis_sev"]).round(2)

    age = df[df["dis_nivel"] == "Limitación severa"].pivot_table(
        index="pais_cod", columns="grupo_edad", values="pct_uso_internet"
    )
    metrics["y25_54_dis_sev"] = age.get("25-54")
    metrics["y55_74_dis_sev"] = age.get("55-74")
    metrics["gap_edad"]       = (metrics["y25_54_dis_sev"] - metrics["y55_74_dis_sev"]).round(2)

    eu27_gap = metrics.loc["EU27_2020", "gap_total"] if "EU27_2020" in metrics.index else None
    if eu27_gap is not None:
        metrics["pos_relativa_eu"] = (metrics["gap_total"] - eu27_gap).round(2)

    return metrics.reset_index().assign(
        pais_nombre_es=lambda x: x["pais_cod"].map(COUNTRY_NAMES_ES)
    )


# ── Funciones de visualización ─────────────────────────────────────────────
def setup_style() -> None:
    """Aplica el estilo global de matplotlib para todos los notebooks."""
    plt.rcParams.update({
        "font.family":       "DejaVu Sans",
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.grid":         True,
        "grid.alpha":        0.3,
        "grid.linestyle":    "--",
        "figure.dpi":        130,
        "savefig.dpi":       300,
        "savefig.bbox":      "tight",
        "savefig.facecolor": "white",
    })


def bar_chart_brecha(df_metrics: pd.DataFrame,
                     save: bool = True,
                     filename: str = "fig_ranking_brecha.png"):
    """Ranking horizontal de países por brecha total. España en azul, LT en rojo."""
    setup_style()
    data    = df_metrics[df_metrics["pais_cod"] != "EU27_2020"].sort_values("gap_total")
    eu_gap  = df_metrics.loc[df_metrics["pais_cod"] == "EU27_2020", "gap_total"].values[0]
    colors  = [
        PALETTE["red"] if p == "LT"
        else PALETTE["blue"] if p == "ES"
        else PALETTE["lgray"]
        for p in data["pais_cod"]
    ]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars    = ax.barh(data["pais_nombre_es"], data["gap_total"],
                      color=colors, edgecolor="white", height=0.6)
    ax.axvline(eu_gap, color=PALETTE["red"], linestyle="--", linewidth=1.5,
               label=f"Media UE-27: {eu_gap:.2f} pp")
    ax.bar_label(bars, fmt="%.2f pp", padding=4, fontsize=9, color=PALETTE["gray"])
    ax.set_xlabel("Brecha (puntos porcentuales)", fontsize=10)
    ax.set_title("Brecha digital por discapacidad severa\nEspaña y pares europeos "
                 "(Eurostat 2024)", fontsize=12, fontweight="bold", color=PALETTE["navy"])
    ax.legend(fontsize=9)
    fig.text(0.01, -0.02,
             "Fuente: elaboración propia a partir de Eurostat DSB_ICTIU01 (2024). "
             "Brecha = % sin discapacidad − % con discapacidad severa.",
             fontsize=7, color=PALETTE["gray"])
    plt.tight_layout()
    if save:
        fig.savefig(get_figures_path(filename))
    return fig, ax


def save_figure(fig, filename: str) -> None:
    """Guarda una figura en images/figures/ con DPI 300."""
    fig.savefig(get_figures_path(filename), dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Figura guardada: images/figures/{filename}")