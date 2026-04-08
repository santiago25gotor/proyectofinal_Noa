"""
03_eda.py — Análisis exploratorio y generación de figuras.
Genera 5 figuras clave en images/figures/

Ejecución (desde python/):
    python 03_eda.py
"""
import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from config import CLEAN_CSV, IMAGES_DIR, PALETTE, SOURCE_NOTE, COUNTRY_COLORS

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-8s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

FIG_DIR = IMAGES_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.3, "grid.linestyle": "--",
    "figure.facecolor": "white", "savefig.dpi": 180,
    "savefig.bbox": "tight", "savefig.facecolor": "white",
})

PAIS_ES = {
    "ES": "España", "EU27_2020": "Media UE-27", "DE": "Alemania",
    "FR": "Francia", "IT": "Italia", "NL": "Países Bajos",
    "PT": "Portugal", "SE": "Suecia", "LT": "Lituania",
}


def save(fig, name):
    path = FIG_DIR / name
    fig.savefig(path)
    plt.close(fig)
    log.info("Figura guardada: %s", path)


def load_data():
    if not CLEAN_CSV.exists():
        raise FileNotFoundError(
            f"CSV no encontrado: {CLEAN_CSV}\n"
            f"Ejecuta primero: python -m cleaning.main"
        )
    df = pd.read_csv(CLEAN_CSV)
    df["pct_internet_use"] = pd.to_numeric(df["pct_internet_use"], errors="coerce")
    df["is_reliable"] = df["is_reliable"].astype(bool)
    df["pais_es"] = df["country_code"].map(PAIS_ES)
    return df


# ── Figura 1: Ranking de países por brecha total ──────────────────────────
def fig_ranking(df):
    """
    Ranking europeo por brecha digital.
    Valores verificados con el CSV real de Eurostat 2024:
      1º LT: 35,86 pp | 2º IT: 18,27 pp | 3º ES: 18,26 pp
    Italia y España forman el bloque mediterráneo (diferencia de 0,01 pp).
    """
    core  = df[(df["sex"] == "Total") & (df["age_group"] == "Total")]
    none_ = core[core["disability_level"] == "No disability"].set_index("country_code")["pct_internet_use"]
    sev_  = core[core["disability_level"] == "Severely limited"].set_index("country_code")["pct_internet_use"]
    gap   = (none_ - sev_).dropna().sort_values(ascending=True)

    paises  = [c for c in gap.index if c != "EU27_2020"]
    valores = [gap[c] for c in paises]
    nombres = [PAIS_ES[c] for c in paises]

    # LT rojo; IT y ES azul (bloque mediterráneo); resto gris
    colores = [
        PALETTE["red"]  if c == "LT" else
        PALETTE["blue"] if c in ("IT", "ES") else
        PALETTE["lgray"]
        for c in paises
    ]
    eu_gap = gap.get("EU27_2020", 12.93)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(nombres, valores, color=colores, edgecolor="white", height=0.6)
    ax.axvline(eu_gap, color=PALETTE["red"], linestyle="--", linewidth=1.5,
               label=f"Media UE-27: {eu_gap:.2f} pp")
    for bar, val in zip(bars, valores):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f} pp", va="center", ha="left", fontsize=9)
    ax.set_xlabel("Brecha (puntos porcentuales)")
    ax.set_title(
        "Brecha digital por discapacidad severa — Ranking europeo 2024\n"
        "Italia (18,27 pp) y España (18,26 pp): bloque mediterráneo de alta brecha",
        fontweight="bold", color=PALETTE["navy"]
    )
    ax.legend()
    ax.set_xlim(0, 42)
    fig.text(0.01, -0.03, SOURCE_NOTE, fontsize=8, color=PALETTE["gray"], style="italic")
    save(fig, "01_ranking_brecha_total.png")


# ── Figura 2: España vs UE-27 por nivel de discapacidad ──────────────────
def fig_espana_vs_eu27(df):
    core    = df[(df["sex"] == "Total") & (df["age_group"] == "Total")]
    niveles = ["No disability", "Limited (not severely)", "Severely limited", "Limited or severely limited"]
    labels  = ["Sin discapacidad", "Limitación leve", "Limitación severa", "Leve o severa"]
    es = core[core["country_code"] == "ES"].set_index("disability_level")["pct_internet_use"].reindex(niveles)
    eu = core[core["country_code"] == "EU27_2020"].set_index("disability_level")["pct_internet_use"].reindex(niveles)

    x, w = np.arange(len(niveles)), 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w/2, es.values, w, color=PALETTE["blue"],  label="España",     edgecolor="white")
    ax.bar(x + w/2, eu.values, w, color=PALETTE["lgray"], label="Media UE-27", edgecolor="white")

    for i, (e, u) in enumerate(zip(es.values, eu.values)):
        if not np.isnan(e):
            ax.text(i - w/2, e + 0.5, f"{e:.1f}%", ha="center", va="bottom", fontsize=8, color=PALETTE["blue"])
        if not np.isnan(u):
            ax.text(i + w/2, u + 0.5, f"{u:.1f}%", ha="center", va="bottom", fontsize=8, color=PALETTE["gray"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(55, 108)
    ax.set_ylabel("% que usa Internet")
    ax.set_title("España vs. Media UE-27 por nivel de discapacidad (2024)",
                 fontweight="bold", color=PALETTE["navy"])
    ax.legend()
    fig.text(0.01, -0.03, SOURCE_NOTE, fontsize=8, color=PALETTE["gray"], style="italic")
    save(fig, "02_espana_vs_eu27.png")


# ── Figura 3: Doble vulnerabilidad género ────────────────────────────────
def fig_genero(df):
    gen = df[
        (df["disability_level"] == "Severely limited") &
        (df["age_group"] == "Total") &
        (df["sex"].isin(["Female", "Male"]))
    ].copy()
    pivot = gen.pivot_table(index="pais_es", columns="sex", values="pct_internet_use")
    pivot = pivot.dropna().sort_values("Female", ascending=True)

    x, w = np.arange(len(pivot)), 0.35
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.barh(x - w/2, pivot["Female"], w, color=PALETTE["red"],  label="Mujeres", edgecolor="white")
    ax.barh(x + w/2, pivot["Male"],   w, color=PALETTE["blue"], label="Hombres", edgecolor="white")

    for i, (f, m) in enumerate(zip(pivot["Female"], pivot["Male"])):
        if not np.isnan(f):
            ax.text(f + 0.4, i - w/2, f"{f:.1f}%", va="center", fontsize=8, color=PALETTE["red"])
        if not np.isnan(m):
            ax.text(m + 0.4, i + w/2, f"{m:.1f}%", va="center", fontsize=8, color=PALETTE["blue"])

    ax.set_yticks(x)
    ax.set_yticklabels(pivot.index, fontsize=9)
    ax.set_xlabel("% que usa Internet")
    ax.set_title(
        "Doble vulnerabilidad: género × discapacidad severa (2024)\n"
        "España: mayor brecha de género fiable del dataset (9,92 pp)",
        fontweight="bold", color=PALETTE["navy"]
    )
    ax.legend()
    ax.set_xlim(45, 108)
    fig.text(0.01, -0.03, SOURCE_NOTE, fontsize=8, color=PALETTE["gray"], style="italic")
    save(fig, "03_doble_vulnerabilidad_genero.png")


# ── Figura 4: Análisis por edad (España) ──────────────────────────────────
def fig_edad(df):
    es = df[
        (df["country_code"] == "ES") &
        (df["sex"] == "Total") &
        (df["age_group"].isin(["25-54", "55-74"])) &
        (df["disability_level"].isin(["No disability", "Limited (not severely)", "Severely limited"]))
    ]
    pivot = es.pivot_table(index="age_group", columns="disability_level", values="pct_internet_use")
    pivot = pivot.reindex(["25-54", "55-74"])

    niveles = ["No disability", "Limited (not severely)", "Severely limited"]
    colores = [PALETTE["green"], PALETTE["lgreen"], PALETTE["red"]]
    labels  = ["Sin discapacidad", "Limitación leve", "Limitación severa"]
    x, w    = np.arange(2), 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, (niv, col, lab) in enumerate(zip(niveles, colores, labels)):
        vals = [pivot.loc[ag, niv] if niv in pivot.columns else np.nan for ag in ["25-54", "55-74"]]
        bars = ax.bar(x + (i - 1) * w, vals, w, color=col, label=lab, edgecolor="white")
        for bar, v in zip(bars, vals):
            if not np.isnan(v):
                ax.text(bar.get_x() + bar.get_width() / 2, v + 0.5,
                        f"{v:.1f}%", ha="center", va="bottom", fontsize=8.5)

    ax.set_xticks(x)
    ax.set_xticklabels(["25-54 años", "55-74 años"], fontsize=11)
    ax.set_ylim(60, 108)
    ax.set_ylabel("% que usa Internet")
    ax.set_title(
        "España — Efecto del envejecimiento sobre la exclusión digital (2024)\n"
        "Grupo 55-74 con discapacidad severa: 76,85% (perfil más vulnerable)",
        fontweight="bold", color=PALETTE["navy"]
    )
    ax.legend(fontsize=9)
    ax.text(
        0.5, 63,
        "Nota: datos 16-24 con discapacidad severa no disponibles en Eurostat (muestra insuficiente)",
        ha="center", fontsize=8, color=PALETTE["gray"], style="italic"
    )
    fig.text(0.01, -0.03, SOURCE_NOTE, fontsize=8, color=PALETTE["gray"], style="italic")
    save(fig, "04_analisis_edad_espana.png")


# ── Figura 5: Exclusión digital (% que NO usa Internet) ───────────────────
def fig_exclusion(df):
    core = df[
        (df["disability_level"] == "Severely limited") &
        (df["sex"] == "Total") &
        (df["age_group"] == "Total") &
        (df["is_reliable"]) &
        (df["country_code"] != "EU27_2020")
    ]
    core = core.sort_values("pct_internet_use").copy()
    core["pct_excluidos"] = 100 - core["pct_internet_use"]
    eu_excl = 100 - 82.29

    # LT rojo; IT y ES azul (bloque mediterráneo); resto gris
    colores = [
        PALETTE["red"]  if c == "LT" else
        PALETTE["blue"] if c in ("ES", "IT") else
        PALETTE["lgray"]
        for c in core["country_code"]
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(core["pais_es"], core["pct_excluidos"],
                  color=colores, edgecolor="white", width=0.6)
    ax.axhline(eu_excl, color=PALETTE["red"], linestyle="--", linewidth=1.5,
               label=f"Media UE-27: {eu_excl:.1f}%")
    for bar, val, code in zip(bars, core["pct_excluidos"], core["country_code"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.4, f"{val:.1f}%",
                ha="center", va="bottom", fontsize=9,
                fontweight="bold" if code in ("ES", "IT", "LT") else "normal")
    ax.set_ylabel("% excluidos digitalmente")
    ax.set_ylim(0, 48)
    ax.set_title(
        "Exclusión digital en personas con discapacidad severa (2024)\n"
        "% de personas que NO usan Internet",
        fontweight="bold", color=PALETTE["navy"]
    )
    ax.legend()
    fig.text(0.01, -0.03, SOURCE_NOTE, fontsize=8, color=PALETTE["gray"], style="italic")
    save(fig, "05_exclusion_digital.png")


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("EDA — Generando figuras del proyecto")
    log.info("Destino: %s", FIG_DIR)
    log.info("=" * 55)
    df = load_data()
    log.info("Dataset cargado: %d filas × %d columnas", *df.shape)

    fig_ranking(df)
    fig_espana_vs_eu27(df)
    fig_genero(df)
    fig_edad(df)
    fig_exclusion(df)

    figuras = list(FIG_DIR.glob("*.png"))
    log.info("=" * 55)
    log.info("✓ %d figuras generadas en images/figures/", len(figuras))
    for f in sorted(figuras):
        log.info("  %s", f.name)
    log.info("=" * 55)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("ERROR: %s", e)
        sys.exit(1)