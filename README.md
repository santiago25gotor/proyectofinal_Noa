# 🌐 La Brecha Digital por Discapacidad en España
## Análisis Comparativo Europeo mediante técnicas de Big Data

**Proyecto Final de la Especialidad · Big Data e Inteligencia Artificial**  
IFP · Innovación en Formación Profesional · Curso 2025-2026

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?logo=sqlite&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-Dashboard-F2C811?logo=powerbi&logoColor=black)
![Dataset](https://img.shields.io/badge/Dataset-Eurostat_DSB__ICTIU01-003399)
![Metodología](https://img.shields.io/badge/Metodología-CRISP--DM-4CAF50)
![Licencia](https://img.shields.io/badge/Datos-Eurostat_Open_Data-blue)
![Estado](https://img.shields.io/badge/Estado-Completado-success)

---

## 📋 Resumen (Abstract)

Este proyecto analiza y caracteriza la **brecha digital por discapacidad en España** comparada con ocho países europeos y la media UE-27, utilizando datos oficiales de Eurostat (indicador DSB_ICTIU01, año 2024).

España presenta una brecha de **18,26 puntos porcentuales** entre personas sin discapacidad (97,56% de uso de Internet) y personas con discapacidad severa (79,30%). Esta cifra es prácticamente idéntica a la de Italia (18,27 pp), situando a ambos países como el **bloque mediterráneo de mayor brecha digital**, superados únicamente por Lituania (35,86 pp) y muy por encima de la media europea (12,93 pp). El análisis identifica además una **doble vulnerabilidad** en mujeres con discapacidad severa (73,91%) y en el grupo de 55-74 años (76,85%).

El proyecto aplica el modelo **CRISP-DM** utilizando **SQL** (SQLite), **Python** (Pandas, Matplotlib, Scikit-learn) y **Power BI**, sobre un dataset de 216 observaciones en 9 entidades geográficas × 24 categorías de discapacidad, sexo y edad.

---

## 🗺️ Navegación del Proyecto

| Sección | Descripción |
|---|---|
| [📖 Introducción](#-1-introducción) | Problema, preguntas de investigación y objetivos |
| [🗄️ Dataset](#️-2-dataset-y-fuente-de-datos) | Eurostat DSB_ICTIU01 — estructura, cobertura y calidad |
| [🔬 Metodología](#-3-metodología-crisp-dm) | CRISP-DM: 6 fases aplicadas al proyecto |
| [🛠️ Herramientas](#️-4-herramientas-y-tecnologías) | SQL · Python · Power BI — justificación de la selección |
| [⚙️ Implementación](#️-5-implementación-práctica) | Pipeline, código y orden de ejecución |
| [📊 Resultados](#-6-resultados-principales) | Hallazgos clave con valores numéricos |
| [🏁 Conclusiones](#-7-conclusiones) | Respuesta a las preguntas de investigación |
| [📚 Bibliografía](#-8-bibliografía) | Fuentes académicas y normativas en APA 7 |
| [📁 Anexos](#-9-anexos) | Estructura del repositorio y diccionario de datos |

---

<details>
<summary><h2>📖 1. Introducción</h2></summary>

En España, **casi 1 de cada 5 personas con discapacidad severa no utilizó Internet en 2024**. Esta cifra, extraída de los datos oficiales de Eurostat, no refleja un problema de infraestructura — España tiene una de las coberturas de red más completas de Europa — sino una fractura estructural de inclusión digital que afecta de manera desproporcionada a las personas con discapacidad.

### 1.1 Pregunta principal de investigación

> *¿Cuál es la magnitud real de la brecha digital por discapacidad en España en comparación con sus pares europeos, y qué perfiles sociodemográficos concentran la mayor exclusión digital?*

### 1.2 Preguntas secundarias

| ID | Pregunta |
|---|---|
| **P1** | ¿En qué posición relativa se sitúa España respecto a Alemania, Francia, Italia, Países Bajos, Portugal, Suecia, Lituania y la media UE-27? |
| **P2** | ¿Existe una brecha adicional significativa entre hombres y mujeres dentro del colectivo con discapacidad severa en España? |
| **P3** | ¿Qué grupo de edad concentra la mayor exclusión digital entre las personas con discapacidad? |
| **P4** | ¿Es posible identificar tipologías diferenciadas de países europeos según su perfil de inclusión digital? |

### 1.3 Objetivos específicos

- **OE1** — Diseñar un pipeline de limpieza en Python con trazabilidad completa y gestión explícita de valores ausentes y flags de baja fiabilidad.
- **OE2** — Realizar un análisis exploratorio multidimensional que cuantifique la brecha en sus tres ejes: nivel de discapacidad, sexo y grupo de edad.
- **OE3** — Implementar consultas SQL que respondan directamente a las cuatro preguntas de investigación.
- **OE4** — Aplicar clustering K-Means (K=3) para identificar tipologías nacionales de inclusión digital.
- **OE5** — Construir un dashboard Power BI con narrativa visual accesible para usuarios no técnicos.

### 1.4 Marco normativo

El problema se enmarca en tres compromisos legales: la **Agenda Digital Europa 2030** (objetivo del 80% de ciudadanos digitalmente conectados), la **Estrategia Española sobre Discapacidad 2022-2030** y el **Real Decreto Legislativo 1/2013** (LGDPD). La brecha digital por discapacidad incumple directamente el espíritu de estos marcos normativos.

</details>

---

<details>
<summary><h2>🗄️ 2. Dataset y Fuente de Datos</h2></summary>

### 2.1 Ficha técnica

| Campo | Detalle |
|---|---|
| **Fuente** | Eurostat — Statistical Office of the European Union |
| **Indicador** | DSB_ICTIU01 v1.0 |
| **Nombre completo** | *Persons using the internet in the past 12 months by level of disability* |
| **Indicador central** | I_ILT12 — uso de Internet en los últimos 12 meses |
| **Unidad** | PC_IND — porcentaje de individuos |
| **Año** | 2024 (corte transversal) |
| **Países** | DE, ES, EU27_2020, FR, IT, LT, NL, PT, SE |
| **URL** | https://ec.europa.eu/eurostat/databrowser/view/DSB_ICTIU01 |
| **Licencia** | Datos públicos — reutilización libre con atribución a Eurostat |
| **Archivos** | `data/raw/dsb_ictiu01_eurostat_2024.csv` · `data/processed/cleaned_dsb_ictiu01.csv` |

### 2.2 Estructura del dataset

- **Dimensiones:** 216 filas × 21 columnas (7 columnas útiles + 14 metadatos redundantes)
- **Eje principal:** `ind_type` — 24 categorías que combinan nivel de discapacidad × sexo × edad

| Eje | Valores |
|---|---|
| Nivel de discapacidad | `DIS_NONE` / `DIS_LTD` / `DIS_SEV` / `DIS_LTD_SEV` |
| Sexo | `Total` / `Female (F_)` / `Male (M_)` |
| Grupo de edad | `Total` / `Y16_24` / `Y25_54` / `Y55_74` |

### 2.3 Calidad y legalidad de los datos

El dataset contiene **19 observaciones con flag `u`** (low reliability estadística según Eurostat):

- **5 observaciones nulas** (flag `u` sin valor): todas en `Y16_24_DIS_SEV` para ES, FR, LT, NL y SE → excluidas del análisis.
- **14 observaciones con flag `u` y valor disponible**: conservadas con `is_reliable=False`, excluidas del clustering.

| País | Categorías afectadas | Decisión |
|---|---|---|
| LT | F_DIS_SEV, M_DIS_SEV, Y16_24_* (varios), Y25_54_DIS_SEV, Y55_74_DIS_SEV | Conservar con advertencia / nulo: excluir |
| SE | M_DIS_SEV, Y16_24_DIS_SEV (nulo), Y25_54_DIS_SEV, Y55_74_DIS_SEV | Conservar con advertencia / nulo: excluir |
| FR | Y16_24_DIS_LTD, Y16_24_DIS_SEV (nulo) | Conservar con advertencia / nulo: excluir |
| ES, NL | Y16_24_DIS_SEV (nulo) | Excluir |
| DE, IT, PT | Y16_24_DIS_SEV (con valor) | Conservar con advertencia |

**Legalidad:** datos abiertos de Eurostat. Reutilización libre con atribución. [Política de datos de Eurostat](https://ec.europa.eu/eurostat/web/main/about/about-eurostat/legal-notices-and-privacy-policy).

</details>

---

<details>
<summary><h2>🔬 3. Metodología CRISP-DM</h2></summary>

Se aplica el modelo **CRISP-DM** (Cross-Industry Standard Process for Data Mining) porque estructura un proceso analítico completo sobre datos observacionales agregados, desde la definición del problema hasta la presentación interpretable de resultados.

| Fase | Aplicación al proyecto | Sección | Herramienta |
|---|---|---|---|
| **1. Comprensión del negocio** | Definir brecha digital por discapacidad; formular P1–P4 | Introducción | — |
| **2. Comprensión de los datos** | Explorar DSB_ICTIU01: estructura, flags, nulos, cobertura | Sección 2-3 | Python |
| **3. Preparación de los datos** | Pipeline de limpieza, métricas derivadas (gap, pct_vs_eu27) | Sección 5 | Python |
| **4. Modelado** | EDA, ranking, clustering K-Means (K=3), análisis género/edad | Sección 5-6 | SQL + Python |
| **5. Evaluación** | Validar coherencia, contrastar con literatura, limitaciones | Sección 7 | — |
| **6. Despliegue** | Dashboard interactivo Power BI con filtros y storytelling | Sección 6 | Power BI |

> **Nota metodológica:** los datos son observacionales y agregados. El análisis es **descriptivo-comparativo**, no causal. No se puede afirmar que la discapacidad *cause* menor uso de Internet; sí que *se asocia* con él en el contexto europeo de 2024.

</details>

---

<details>
<summary><h2>🛠️ 4. Herramientas y Tecnologías</h2></summary>

### 4.1 Herramientas implementadas

| Herramienta | Versión | Uso en el proyecto |
|---|---|---|
| **Python** | 3.11+ | Pipeline de limpieza, EDA, clustering, carga SQL |
| **Pandas** | 2.x | Manipulación y transformación del dataset |
| **Matplotlib** | latest | Generación de las figuras analíticas |
| **Scikit-learn** | 1.x | K-Means clustering (K=3) sobre métricas de brecha |
| **SQL (SQLite)** | built-in | Modelo estrella, consultas analíticas, vistas Power BI |
| **Power BI Desktop** | latest | Dashboard interactivo con 4 páginas de análisis |

### 4.2 Justificación de la selección

El proyecto propone un abanico amplio de herramientas. Para este proyecto concreto (216 observaciones, análisis descriptivo-comparativo, un único año de datos) se han seleccionado las tres que mejor se adaptan:

- **SQL en lugar de BigQuery:** el dataset tiene 216 filas y ~50 KB. SQLite utiliza el mismo lenguaje SQL estándar y las queries son 100% compatibles con BigQuery si se quisiera escalar.
- **Python en lugar de R/Tidyverse:** integración nativa con Scikit-learn para clustering, permitiendo un pipeline unificado y reproducible.
- **Power BI en lugar de Tableau:** gratuito con integración nativa a SQLite via ODBC.
- **Python en lugar de Orange Data Mining:** código reproducible, versionable en GitHub y auditable línea a línea.
- **Sin Hadoop/HDFS ni NiFi:** con 216 filas, la infraestructura distribuida no aporta valor. El pipeline ETL en Python cubre íntegramente las fases de ingesta y transformación.
- **Sin Cassandra:** los datos tienen estructura relacional clara. Un modelo estrella SQLite es más apropiado que una base de datos NoSQL.

### 4.3 Modelo estrella SQL

La base de datos `proyecto.db` implementa un modelo estrella con 7 tablas:

```
fact_internet_use   ← tabla de hechos principal
├── dim_country
├── dim_disability_level
├── dim_sex
├── dim_age_group
├── dim_individual_type  ← 24 categorías
└── dim_indicator
```

### 4.4 Dashboard Power BI

El dashboard `powerbi/Estado_de_ES_EU_2024.pbix` consta de **4 páginas interactivas**:

1. 🗺️ **Mapa europeo** — distribución geográfica de la brecha digital
2. 🏆 **Ranking** — comparativa de los 9 países por nivel de brecha
3. 👥 **Género** — doble vulnerabilidad mujeres × discapacidad severa
4. 📅 **Edad** — intersección grupo de edad × discapacidad en España

> Ver `powerbi/README_powerbi.md` para instrucciones de conexión ODBC.

</details>

---

<details>
<summary><h2>⚙️ 5. Implementación Práctica</h2></summary>

### 5.1 Estructura del repositorio

```
proyectofinal_Noa-main/
│
├── README.md                        ← Este archivo
├── requirements.txt                 ← Dependencias Python
├── setup.sh                         ← Instalación automática
├── proyecto.db                      ← Base de datos SQLite (generada)
│
├── data/
│   ├── raw/
│   │   └── dsb_ictiu01_eurostat_2024.csv     ← Dataset original (NO modificar)
│   ├── processed/
│   │   └── cleaned_dsb_ictiu01.csv           ← Dataset limpio
│   └── README_data.md
│
├── python/
│   ├── config.py                    ← Constantes centrales del proyecto
│   ├── cleaning/
│   │   ├── steps.py                 ← 9 funciones de limpieza modulares
│   │   └── main.py                  ← Orquestador del pipeline
│   ├── sql_loader.py                ← Carga CSV limpio → SQLite
│   ├── clustering_paises.py         ← K-Means K=3 con Scikit-learn
│   ├── 03_eda.py                    ← Genera figuras analíticas
│   └── utils/helpers.py
│
├── sql/
│   ├── 01_schema.sql                ← CREATE TABLE e índices
│   ├── 02_seed.sql                  ← INSERT dimensiones + vistas base
│   ├── 04_queries_p1_ranking.sql    ← Responde P1
│   ├── 05_queries_p2_p3_vulnerabilidad.sql  ← Responde P2 y P3
│   └── 06_queries_estadisticos_powerbi.sql  ← Vistas para Power BI
│
├── powerbi/
│   ├── Estado_de_ES_EU_2024.pbix    ← Dashboard interactivo (4 páginas)
│   └── README_powerbi.md
│
├── images/
│   ├── figures/                     ← Figuras generadas por 03_eda.py (10 imágenes)
│   └── capturas/                    ← Capturas del dashboard Power BI
│
├── outputs/
│   ├── tables/
│   │   ├── clustering_resultados.csv
│   │   └── ml_resultados_clasificacion.csv
│   └── reports/                     ← Informe final PDF
│
└── docs/
    ├── informe_final.pdf
    └── bibliografia.md
```

### 5.2 Orden de ejecución

```bash
# PASO 1 — Clonar e instalar
git clone <url-repositorio>
cd proyectofinal_Noa-main
bash setup.sh

# PASO 2 — Limpiar datos (genera cleaned_dsb_ictiu01.csv)
cd python/
python -m cleaning.main

# PASO 3 — Cargar en SQLite (genera proyecto.db)
python sql_loader.py

# PASO 4 — Ejecutar consultas SQL analíticas
cd ..
sqlite3 proyecto.db < sql/04_queries_p1_ranking.sql
sqlite3 proyecto.db < sql/05_queries_p2_p3_vulnerabilidad.sql
sqlite3 proyecto.db < sql/06_queries_estadisticos_powerbi.sql

# PASO 5 — Clustering K-Means K=3
cd python/
python clustering_paises.py

# PASO 6 — Figuras del EDA (10 imágenes en images/figures/)
python 03_eda.py

# PASO 7 — Power BI
# Abrir powerbi/Estado_de_ES_EU_2024.pbix
# Conectar via ODBC a proyecto.db (ver powerbi/README_powerbi.md)
```

### 5.3 Figuras analíticas generadas

| Archivo | Contenido |
|---|---|
| `01_ranking_brecha_total.png` | Ranking europeo de brechas por discapacidad |
| `02_espana_vs_eu27.png` | España comparada con la media UE-27 |
| `03_doble_vulnerabilidad_genero.png` | Análisis de género × discapacidad severa |
| `04_analisis_edad_espana.png` | Intersección edad × discapacidad en España |
| `05_exclusion_digital.png` | Mapa visual de exclusión digital |
| `06_clustering_paises.png` | Resultado del clustering K-Means K=3 |
| `06b_elbow_silhouette.png` | Validación del K óptimo (elbow + silhouette) |
| `07_ml_comparacion_modelos.png` | Comparación de modelos de clasificación |
| `08_ml_matriz_confusion.png` | Matriz de confusión del modelo seleccionado |
| `09_ml_importancia_features.png` | Importancia de variables |
| `10_ml_arbol_decision.png` | Árbol de decisión visualizado |

</details>

---

<details>
<summary><h2>📊 6. Resultados Principales</h2></summary>

### 6.1 Ranking europeo por brecha total (P1)

| Posición | País | Sin discapacidad | Discap. severa | Brecha (pp) | vs. UE-27 |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | 🇱🇹 Lituania | 93,31% | 57,45% | **35,86** | +22,93 |
| 2 | 🇮🇹 Italia | 92,88% | 74,61% | **18,27** | +5,34 |
| 3 | 🇪🇸 **España ★** | **97,56%** | **79,30%** | **18,26** | **+5,33** |
| — | 🇪🇺 Media UE-27 | 95,22% | 82,29% | *12,93* | *ref.* |
| 4 | 🇩🇪 Alemania | 95,58% | 84,53% | 11,05 | −1,88 |
| 5 | 🇫🇷 Francia | 96,24% | 86,88% | 9,36 | −3,57 |
| 6 | 🇵🇹 Portugal | 91,73% | 84,47% | 7,26 | −5,67 |
| 7 | 🇸🇪 Suecia | 99,15% | 94,43% | 4,72 | −8,21 |
| 8 | 🇳🇱 Países Bajos | 99,72% | 98,67% | 1,05 | −11,88 |

> **Italia (18,27 pp) y España (18,26 pp) presentan brechas prácticamente idénticas**, formando el bloque mediterráneo de mayor exclusión digital. Ambos superan en más de 5 pp la media europea.

### 6.2 Doble vulnerabilidad de género (P2)

| Grupo | España | UE-27 |
|---|:---:|:---:|
| Hombres con discapacidad severa | 83,83% | 81,54% |
| Mujeres con discapacidad severa | **73,91%** | 82,93% |
| **Brecha de género** | **9,92 pp** | −1,39 pp |

España presenta la **mayor brecha de género del dataset** entre países con datos estadísticamente fiables.

### 6.3 Intersección edad × discapacidad (P3)

| Grupo de edad | % uso Internet (discap. severa, España) |
|---|:---:|
| 25-54 años | 82,31% |
| 55-74 años | **76,85%** ← perfil más vulnerable |
| 16-24 años | *No disponible — muestra insuficiente* |

### 6.4 Clustering K-Means K=3 (P4)

| Grupo | Países | Brecha media |
|---|---|:---:|
| **Alta inclusión** | Países Bajos, Suecia | ~2,9 pp |
| **Inclusión media** | Alemania, Francia, Portugal | ~9,2 pp |
| **Baja inclusión** | España, Italia, Lituania | ~24,1 pp |

</details>

---

<details>
<summary><h2>🏁 7. Conclusiones</h2></summary>

**P1 — Posición europea:** España e Italia forman el bloque mediterráneo de mayor exclusión digital (18,26 y 18,27 pp respectivamente), superando en más de 5 pp la media europea (12,93 pp). La brecha no es de conectividad sino de inclusión diferencial.

**P2 — Doble vulnerabilidad (género):** Las mujeres con discapacidad severa en España usan Internet casi 10 pp menos que los hombres en la misma situación (73,91% vs 83,83%). Es la mayor brecha de género del dataset entre países con datos fiables.

**P3 — Intersección edad:** El grupo de 55-74 años con discapacidad severa (76,85%) concentra la mayor exclusión. El envejecimiento añade 5,46 pp de exclusión adicional respecto al grupo de 25-54 años.

**P4 — Tipología de países:** El clustering K=3 identifica tres perfiles claros y bien diferenciados. España e Italia comparten cluster, coherente con su proximidad en todos los indicadores.

**Limitaciones del estudio:**
- Corte transversal de 2024 — no permite análisis temporal
- Datos agregados, no microdatos individuales
- 5 valores no disponibles en `Y16_24_DIS_SEV`
- Cobertura de 8 países, no representativa del conjunto UE-27
- Correlaciones descriptivas, no causales

</details>

---

<details>
<summary><h2>📚 8. Bibliografía</h2></summary>

**Fuente de datos principal:**

Eurostat (2024). *Persons using the internet in the past 12 months by level of disability (activity limitation)* [DSB_ICTIU01 v1.0]. Statistical Office of the European Union. https://ec.europa.eu/eurostat/databrowser/view/DSB_ICTIU01

**Metodología:**

Chapman, P., Clinton, J., Kerber, R., Khabaza, T., Reinartz, T., Shearer, C., & Wirth, R. (2000). *CRISP-DM 1.0: Step-by-step data mining guide*. SPSS Inc.

**Literatura académica:**

- Dobransky, K., & Hargittai, E. (2006). The disability divide in Internet access and use. *Information, Communication & Society*, *9*(3), 313–334.
- Scheerder, A. J., van Deursen, A. J. A. M., & van Dijk, J. A. G. M. (2017). Determinants of Internet skills, uses and outcomes. *Telematics and Informatics*, *34*(8), 1607–1624.

**Marco normativo:**

- Comisión Europea (2021). Brújula Digital 2030. Comunicación COM/2021/118.
- Gobierno de España (2022). Estrategia Española sobre Discapacidad 2022-2030.
- Real Decreto Legislativo 1/2013 (LGDPD). BOE núm. 289.

**Herramientas:**

- McKinney, W. (2022). *Python for Data Analysis* (3rd ed.). O'Reilly Media.
- Microsoft (2024). Power BI Desktop documentation. https://docs.microsoft.com/power-bi
- SQLite Consortium (2024). SQLite documentation. https://www.sqlite.org/docs.html

**Uso de IA:**

Se utilizó Claude (Anthropic, modelo Sonnet) como apoyo en la estructuración del pipeline Python, redacción de consultas SQL y revisión de coherencia del código. Todo el contenido analítico, la interpretación de resultados y las conclusiones son responsabilidad de la autora.

Ver bibliografía completa en [`docs/bibliografia.md`](docs/bibliografia.md).

</details>

---

<details>
<summary><h2>📁 9. Anexos</h2></summary>

### Anexo A — Diccionario de variables (dataset limpio)

| Variable | Tipo | Descripción |
|---|---|---|
| `year` | Int | Año de referencia (2024) |
| `country_code` | Str | Código ISO del país (ES, DE, ...) |
| `category_code` | Str | Código ind_type original de Eurostat |
| `disability_level` | Str | Nivel de discapacidad decodificado |
| `sex` | Str | Sexo (Total / Female / Male) |
| `age_group` | Str | Grupo de edad (Total / 16-24 / 25-54 / 55-74) |
| `pct_internet_use` | Float | % de individuos que usaron Internet [0-100] |
| `quality_flag` | Str | Flag Eurostat ('u' = baja fiabilidad, vacío = OK) |
| `is_reliable` | Bool | True si el dato es estadísticamente fiable |

### Anexo B — Observaciones con flag de calidad

El dataset contiene **19 observaciones con flag `u`** (low reliability):

| Tipo | Países | N | Decisión |
|---|---|:---:|---|
| Valor nulo + flag u | ES, FR, LT, NL, SE (Y16_24_DIS_SEV) | 5 | Excluir |
| Valor disponible + flag u | DE, IT, PT (Y16_24_DIS_SEV) | 3 | Conservar con advertencia |
| Valor disponible + flag u | LT, SE, FR, PT (otras categorías) | 11 | Conservar con advertencia |

### Anexo C — Herramientas de IA utilizadas

Se utilizó **Claude (Anthropic, modelo Sonnet)** como apoyo en:
- Estructuración del pipeline de Python
- Revisión de coherencia del código SQL
- Corrección de errores de sintaxis
- Redacción técnica del README y documentación

Todo el contenido analítico, la interpretación de resultados y las conclusiones son responsabilidad de la autora del proyecto.

</details>

---

## 📈 Estado de Entregables

| Entregable | Estado | Peso |
|---|:---:|:---:|
| ✅ Práctica en el aula (pipeline funcional) | Completado | 3 pts |
| ✅ Repositorio GitHub con estructura navegable | Completado | 2 pts |
| ✅ Entrega .zip con código y archivos | Completado | 1 pt |
| ✅ Informe final PDF | Completado | 1 pt |
| ✅ Redacción, ortografía y bibliografía | Completado | 1 pt |
| 🔜 Presentación oral (15 minutos) | Pendiente | 2 pts |

---

## 🚀 Inicio Rápido

```bash
git clone <url-repositorio>
cd proyectofinal_Noa-main
bash setup.sh
cd python && python -m cleaning.main && python sql_loader.py
python clustering_paises.py
python 03_eda.py
# Abrir powerbi/Estado_de_ES_EU_2024.pbix en Power BI Desktop
```

**Requisitos:** Python 3.11+, SQLite (incluido en Python), Power BI Desktop (gratuito).

---

*Proyecto desarrollado con Python 3.11, SQL (SQLite) y Power BI Desktop · Dataset: Eurostat DSB_ICTIU01 (2024) · Metodología: CRISP-DM · IFP Big Data e IA 2025-2026*
