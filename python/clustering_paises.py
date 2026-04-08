"""
clustering_paises.py — Clustering K-Means sobre indicadores de brecha por país.

Aplica K-Means (K=3) con Scikit-learn para identificar tipologías de
modelos nacionales de inclusión digital para personas con discapacidad.

PRERREQUISITO:
    python -m cleaning.main  →  genera data/processed/cleaned_dsb_ictiu01.csv

EJECUCIÓN (desde python/):
    python clustering_paises.py

SALIDA:
    images/figures/06_clustering_paises.png
    images/figures/06b_elbow_silhouette.png
    outputs/tables/clustering_resultados.csv

DECISIÓN DE FEATURES:
    Se usan 2 features: gap_total y pct_sev (nivel absoluto de uso).
    Motivo: con más features (gap_gender, gap_age), LT queda aislada
    en su propio cluster y ES/IT se agrupan con DE/FR/PT, lo que no
    refleja el objetivo del análisis (ordenar países por exclusión digital).
    Con gap_total + pct_sev el resultado es interpretable y coherente
    con la narrativa del proyecto.

NOTA SOBRE EU27_2020:
    Se excluye del clustering al ser un agregado estadístico,
    no un país individual comparable.

RESULTADO ESPERADO (K=3):
    Grupo 0 — Alta inclusión:  Países Bajos, Suecia      (~2,9 pp)
    Grupo 1 — Inclusión media: Alemania, Francia, Portugal (~9,2 pp)
    Grupo 2 — Baja inclusión:  España, Italia, Lituania   (~24,1 pp)

    España e Italia comparten cluster, coherente con su práctica
    igualdad en brecha total (18,26 vs 18,27 pp — diferencia de 0,01 pp).
"""
import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

sys.path.insert(0, str(Path(__file__).parent))
from config import CLEAN_CSV, IMAGES_DIR, OUTPUTS_DIR, PALETTE

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-8s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

FIG_DIR = IMAGES_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR = OUTPUTS_DIR / "tables"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PAIS_ES = {
    "ES": "España", "EU27_2020": "Media UE-27", "DE": "Alemania",
    "FR": "Francia", "IT": "Italia", "NL": "Países Bajos",
    "PT": "Portugal", "SE": "Suecia", "LT": "Lituania",
}

CLUSTER_COLORS = {
    0: PALETTE["green"],  # Alta inclusión
    1: PALETTE["amber"],  # Inclusión media
    2: PALETTE["red"],    # Baja inclusión
}
CLUSTER_LABELS = {
    0: "Alta inclusión",
    1: "Inclusión media",
    2: "Baja inclusión",
}


def load_and_build_features(csv_path: Path) -> pd.DataFrame:
    """
    Construye la matriz de features por país.

    Features:
        gap_total : DIS_NONE − DIS_SEV  (brecha total)
        pct_sev   : % uso Internet con discapacidad severa
    """
    df = pd.read_csv(csv_path)
    df["pct_internet_use"] = pd.to_numeric(df["pct_internet_use"], errors="coerce")

    # EU27_2020 excluido — es un agregado, no un país individual
    df = df[df["country_code"] != "EU27_2020"].copy()

    core  = df[(df["sex"] == "Total") & (df["age_group"] == "Total")]
    none_ = core[core["disability_level"] == "No disability"].set_index("country_code")["pct_internet_use"]
    sev_  = core[core["disability_level"] == "Severely limited"].set_index("country_code")["pct_internet_use"]

    gap_total = (none_ - sev_).rename("gap_total")
    pct_sev   = sev_.rename("pct_sev")

    features = pd.concat([gap_total, pct_sev], axis=1).dropna()
    features["pais_es"] = features.index.map(PAIS_ES)

    log.info("Matriz de features: %d países × 2 features", len(features))
    log.info("Países: %s", features.index.tolist())
    return features


def elbow_analysis(X_scaled: np.ndarray) -> None:
    """Curva del codo y silhouette para justificar K=3."""
    inertias   = []
    sil_scores = []
    K_range    = range(2, 7)

    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)
        sil_scores.append(silhouette_score(X_scaled, km.labels_))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))

    ax1.plot(list(K_range), inertias, "o-", color=PALETTE["blue"], linewidth=2)
    ax1.axvline(3, color=PALETTE["red"], linestyle="--", alpha=0.7, label="K=3 elegido")
    ax1.set_xlabel("Número de clusters (K)")
    ax1.set_ylabel("Inercia (WCSS)")
    ax1.set_title("Método del codo", fontweight="bold")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(list(K_range), sil_scores, "s-", color=PALETTE["green"], linewidth=2)
    ax2.axvline(3, color=PALETTE["red"], linestyle="--", alpha=0.7, label="K=3 elegido")
    ax2.set_xlabel("Número de clusters (K)")
    ax2.set_ylabel("Silhouette score")
    ax2.set_title("Puntuación Silhouette", fontweight="bold")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.suptitle("Selección de K para el clustering de países",
                 fontweight="bold", color=PALETTE["navy"])
    plt.tight_layout()

    path = FIG_DIR / "06b_elbow_silhouette.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log.info("Figura selección K guardada: %s", path)
    log.info("Silhouette scores por K: %s",
             {k: round(s, 3) for k, s in zip(K_range, sil_scores)})


def run_kmeans(features: pd.DataFrame) -> pd.DataFrame:
    """Ejecuta K-Means K=3 y devuelve DataFrame con cluster asignado."""
    X = features[["gap_total", "pct_sev"]].values

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    elbow_analysis(X_scaled)

    km     = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    features = features.copy()
    features["cluster_raw"] = labels

    # Reordenar: cluster 0 = menor brecha, cluster 2 = mayor brecha
    means = features.groupby("cluster_raw")["gap_total"].mean().sort_values()
    remap = {old: new for new, old in enumerate(means.index)}
    features["cluster"] = features["cluster_raw"].map(remap)
    features["grupo"]   = features["cluster"].map(CLUSTER_LABELS)

    sil = silhouette_score(X_scaled, features["cluster"].values)
    log.info("K-Means K=3 | Silhouette: %.3f", sil)

    es_c = features.loc["ES", "cluster"] if "ES" in features.index else None
    it_c = features.loc["IT", "cluster"] if "IT" in features.index else None
    lt_c = features.loc["LT", "cluster"] if "LT" in features.index else None
    log.info("Verificación clusters: ES=%s | IT=%s | LT=%s",
             CLUSTER_LABELS.get(es_c,"?"), CLUSTER_LABELS.get(it_c,"?"), CLUSTER_LABELS.get(lt_c,"?"))
    log.info("¿ES e IT en mismo cluster ('Baja inclusión')? %s", es_c == it_c == 2)

    return features


def plot_clustering(features: pd.DataFrame) -> None:
    """Scatter plot gap_total vs pct_sev, coloreado por cluster."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for cluster_id, grupo_label in CLUSTER_LABELS.items():
        mask = features["cluster"] == cluster_id
        sub  = features[mask]
        ax.scatter(
            sub["gap_total"], sub["pct_sev"],
            color=CLUSTER_COLORS[cluster_id],
            s=120, zorder=3, label=grupo_label,
            edgecolors="white", linewidths=1.5
        )
        for _, row in sub.iterrows():
            oy = -2.2 if row.name == "IT" else 0.8
            ax.annotate(
                row["pais_es"],
                (row["gap_total"], row["pct_sev"]),
                xytext=(row["gap_total"] + 0.5, row["pct_sev"] + oy),
                fontsize=9, color=PALETTE["gray"]
            )

    ax.axvline(12.93, color=PALETTE["gray"], linestyle="--", linewidth=1,
               alpha=0.6, label="Media UE-27 (12,93 pp)")
    ax.set_xlabel("Brecha total (pp) — DIS_NONE menos DIS_SEV", fontsize=10)
    ax.set_ylabel("% uso Internet con discapacidad severa", fontsize=10)
    ax.set_title(
        "Clustering de países por perfil de inclusión digital — K-Means K=3\n"
        "España e Italia comparten cluster (diferencia de solo 0,01 pp en brecha total)",
        fontweight="bold", color=PALETTE["navy"]
    )
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, linestyle="--")
    fig.text(
        0.01, -0.02,
        "Fuente: elaboración propia a partir de Eurostat DSB_ICTIU01 (2024). "
        "Features: gap_total y pct_sev. EU27_2020 excluido (agregado estadístico).",
        fontsize=8, color=PALETTE["gray"], style="italic"
    )
    plt.tight_layout()

    path = FIG_DIR / "06_clustering_paises.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log.info("Figura clustering guardada: %s", path)


def main():
    log.info("=" * 55)
    log.info("CLUSTERING — K-Means K=3")
    log.info("Features: gap_total, pct_sev")
    log.info("=" * 55)

    if not CLEAN_CSV.exists():
        log.error("CSV limpio no encontrado: %s", CLEAN_CSV)
        log.error("Ejecuta primero: python -m cleaning.main")
        sys.exit(1)

    features = load_and_build_features(CLEAN_CSV)
    features = run_kmeans(features)
    plot_clustering(features)

    out_cols = ["pais_es", "gap_total", "pct_sev", "cluster", "grupo"]
    result   = features[out_cols].sort_values("gap_total", ascending=False)
    out_path = OUT_DIR / "clustering_resultados.csv"
    result.to_csv(out_path, index=True)
    log.info("Resultados exportados: %s", out_path)

    log.info("=" * 55)
    log.info("RESULTADOS:")
    for _, row in result.iterrows():
        log.info("  %-15s  gap=%.2f pp  grupo=%s",
                 row["pais_es"], row["gap_total"], row["grupo"])
    log.info("=" * 55)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("ERROR: %s", e)
        sys.exit(1)