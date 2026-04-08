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

---

## 📋 Resumen (Abstract)

Este proyecto analiza y caracteriza la **brecha digital por discapacidad en España** comparada con ocho países europeos y la media UE-27, utilizando datos oficiales de Eurostat (indicador DSB_ICTIU01, año 2024).

España presenta una brecha de **18,26 puntos porcentuales** entre personas sin discapacidad (97,56% de uso de Internet) y personas con discapacidad severa (79,30%). Esta cifra es prácticamente idéntica a la de Italia (18,27 pp, diferencia de solo 0,01 pp), situando a ambos países como el **bloque mediterráneo de mayor brecha digital**, superados únicamente por Lituania (35,86 pp) y muy por encima de la media europea (12,93 pp). El análisis identifica además una **doble vulnerabilidad** en mujeres con discapacidad severa (73,91%) y en el grupo de 55-74 años (76,85%).

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
<summary><h2>🗄️ 2. Dataset y fuente de datos</h2></summary>

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
| **Archivo local** | `data/raw/dsb_ictiu01_eurostat_2024.csv` |

### 2.2 Estructura del dataset

- **Dimensiones:** 216 filas × 21 columnas (7 columnas útiles + 14 metadatos redundantes)
- **Eje principal:** `ind_type` — 24 categorías que combinan nivel de discapacidad × sexo × edad

| Eje | Valores |
|---|---|
| Nivel de discapacidad | `DIS_NONE` / `DIS_LTD` / `DIS_SEV` / `DIS_LTD_SEV` |
| Sexo | `Total` / `Female (F_)` / `Male (M_)` |
| Grupo de edad | `Total` / `Y16_24` / `Y25_54` / `Y55_74` |

### 2.3 Calidad de los datos

El dataset contiene **19 observaciones con flag `u`** (low reliability estadística según Eurostat):

- **5 observaciones nulas** (flag `u` sin valor): todas en `Y16_24_DIS_SEV` para ES, FR, LT, NL y SE. Muestra subyacente insuficiente → excluidas del análisis.
- **14 observaciones con flag `u` y valor disponible**: conservadas con `is_reliable=False` y usadas con advertencia en análisis descriptivos, excluidas del clustering.

| País | Categorías con flag u | Decisión |
|---|---|---|
| LT | F_DIS_SEV, M_DIS_SEV, Y16_24_DIS_LTD, Y16_24_DIS_LTD_SEV, Y16_24_DIS_SEV (nulo), Y25_54_DIS_SEV, Y55_74_DIS_SEV | Conservar con advertencia (nulo: excluir) |
| SE | M_DIS_SEV, Y16_24_DIS_SEV (nulo), Y25_54_DIS_SEV, Y55_74_DIS_SEV | Conservar con advertencia (nulo: excluir) |
| FR | Y16_24_DIS_LTD, Y16_24_DIS_SEV (nulo) | Conservar con advertencia (nulo: excluir) |
| ES, NL | Y16_24_DIS_SEV (nulo) | Excluir |
| DE, IT, PT | Y16_24_DIS_SEV (con valor) | Conservar con advertencia |

- **Legalidad:** datos abiertos de Eurostat. Reutilización libre con atribución. [Política de datos de Eurostat](https://ec.europa.eu/eurostat/web/main/about/about-eurostat/legal-notices-and-privacy-policy).

</details>

---

<details>
<summary><h2>🔬 3. Metodología CRISP-DM</h2></summary>

Se aplica el modelo **CRISP-DM** (Cross-Industry Standard Process for Data Mining) porque estructura un proceso analítico completo sobre datos observacionales agregados, desde la definición del problema hasta la presentación interpretable de resultados.

| Fase | Aplicación al proyecto | Sección informe | Herramienta |
|---|---|---|---|
| **1. Comprensión del negocio** | Definir brecha digital por discapacidad; formular P1–P4 | Introducción | — |
| **2. Comprensión de los datos** | Explorar DSB_ICTIU01: estructura, flags, nulos, cobertura | Sección 2-3 | Python |
| **3. Preparación de los datos** | Pipeline de limpieza, métricas derivadas (gap, pct_vs_eu27) | Sección 6 | Python |
| **4. Modelado** | EDA, ranking, clustering K-Means (K=3), análisis género/edad | Sección 6 | SQL + Python |
| **5. Evaluación** | Validar coherencia, contrastar con literatura, limitaciones | Sección 7-8 | — |
| **6. Despliegue** | Dashboard interactivo Power BI con filtros y storytelling | Sección 6 | Power BI |

> **Nota metodológica:** los datos son observacionales y agregados. El análisis es **descriptivo-comparativo**, no causal. No se puede afirmar que la discapacidad *causa* menor uso de Internet; sí que *se asocia* con él en el contexto europeo de 2024.

</details>

---

<details>
<summary><h2>🛠️ 4. Herramientas y tecnologías</h2></summary>

### 4.1 Herramientas implementadas

| Herramienta | Versión | Uso en el proyecto |
|---|---|---|
| **Python** | 3.11+ | Pipeline de limpieza, EDA, clustering, carga SQL |
| **Pandas** | 2.x | Manipulación y transformación del dataset |
| **Matplotlib** | latest | Generación de las 5 figuras analíticas |
| **Scikit-learn** | 1.x | K-Means clustering (K=3) sobre métricas de brecha |
| **SQL (SQLite)** | built-in | Modelo estrella, consultas analíticas, vistas Power BI |
| **Power BI Desktop** | latest | Dashboard interactivo con 4 páginas de análisis |

### 4.2 Justificación de la selección de herramientas

El profesor propone un abanico amplio de herramientas. Para este proyecto concreto (216 observaciones, análisis descriptivo-comparativo, un único año de datos) se han seleccionado las tres que mejor se adaptan al tipo de análisis:

- **SQL en lugar de BigQuery:** el dataset tiene 216 filas y ~50 KB. La infraestructura distribuida de BigQuery no aporta valor operativo para este volumen. SQLite utiliza el mismo lenguaje SQL estándar y las queries son 100% compatibles con BigQuery si se quisiera escalar.
- **Python en lugar de R/Tidyverse:** Python con Pandas ofrece las mismas capacidades de manipulación y análisis estadístico, con la ventaja adicional de integrarse de forma nativa con Scikit-learn para el clustering.
- **Power BI en lugar de Tableau:** Power BI Desktop es gratuito y tiene integración nativa con SQLite via ODBC. La elección es de ecosistema, no de capacidad analítica.
- **Python en lugar de Orange Data Mining:** el clustering K-Means se implementa con Scikit-learn, que produce código reproducible, versionable en GitHub y auditable línea a línea.
- **No se usa Hadoop/HDFS ni Apache NiFi:** con 216 filas en un CSV de 50 KB, la infraestructura distribuida no aporta valor. El pipeline ETL en Python cubre íntegramente las fases de ingesta y transformación con mayor trazabilidad.
- **No se usa Cassandra:** los datos son porcentajes agregados con estructura relacional clara. Un modelo estrella SQLite es más apropiado que una base de datos NoSQL orientada a escrituras masivas distribuidas.

### 4.3 SQL — Modelo estrella

La base de datos `proyecto.db` implementa un modelo estrella con 7 tablas:

```
fact_internet_use   ← tabla de hechos principal
├── dim_country     ← 9 países + EU27
├── dim_disability_level
├── dim_sex
├── dim_age_group
├── dim_individual_type  ← 24 categorías
└── dim_indicator
```

### 4.4 Power BI — Conexión a la base de datos

1. Ejecutar `python python/sql_loader.py` → genera `proyecto.db`
2. Abrir Power BI Desktop → **Obtener datos** → **Base de datos ODBC**
3. Navegar hasta `proyecto.db` en la raíz del proyecto
4. Seleccionar las vistas `vw_pbi_*` creadas por el script 06
5. Construir los 4 paneles del dashboard (ver `powerbi/README_powerbi.md`)

</details>

---

<details>
<summary><h2>⚙️ 5. Implementación práctica</h2></summary>

### 5.1 Estructura del proyecto

```
brecha_digital_discapacidad_es/
│
├── README.md
├── requirements.txt
├── setup.sh
├── proyecto.db                  ← generado por sql_loader.py
│
├── data/
│   ├── raw/                     ← CSV original de Eurostat (NO modificar)
│   └── processed/               ← generado por cleaning/main.py
│
├── python/
│   ├── config.py                ← constantes centrales del proyecto
│   ├── cleaning/
│   │   ├── steps.py             ← 9 funciones de limpieza
│   │   └── main.py              ← orquestador del pipeline
│   ├── sql_loader.py            ← carga CSV limpio → SQLite
│   ├── clustering_paises.py     ← K-Means K=3 con Scikit-learn
│   ├── 03_eda.py                ← genera 5 figuras analíticas
│   └── utils/helpers.py         ← funciones para notebooks
│
├── sql/
│   ├── 01_schema.sql            ← CREATE TABLE e índices
│   ├── 02_seed.sql              ← INSERT dimensiones + vistas base
│   ├── 04_queries_p1_ranking.sql
│   ├── 05_queries_p2_p3_vulnerabilidad.sql
│   └── 06_queries_estadisticos_powerbi.sql
│
├── powerbi/
│   ├── dashboard_brecha_digital.pbix
│   └── README_powerbi.md
│
├── images/
│   ├── figures/                 ← figuras generadas por 03_eda.py
│   └── capturas/                ← capturas del dashboard Power BI
│
├── outputs/
│   ├── tables/                  ← tablas exportadas desde notebooks
│   └── reports/                 ← informe final en PDF
│
└── docs/
    ├── informe_final.pdf
    └── bibliografia.md
```

### 5.2 Orden de ejecución

```bash
# PASO 1 — Instalar dependencias
bash setup.sh

# PASO 2 — Limpiar datos
cd python/
python -m cleaning.main

# PASO 3 — Cargar en SQLite
python sql_loader.py

# PASO 4 — Ejecutar consultas SQL
cd ..
sqlite3 proyecto.db < sql/04_queries_p1_ranking.sql
sqlite3 proyecto.db < sql/05_queries_p2_p3_vulnerabilidad.sql
sqlite3 proyecto.db < sql/06_queries_estadisticos_powerbi.sql

# PASO 5 — Clustering K-Means K=3
cd python/
python clustering_paises.py

# PASO 6 — Figuras del EDA
python 03_eda.py

# PASO 7 — Power BI
# Conectar Power BI Desktop a proyecto.db (ver powerbi/README_powerbi.md)
```

</details>

---

<details>
<summary><h2>📊 6. Resultados principales</h2></summary>

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

> **Italia (18,27 pp) y España (18,26 pp) presentan brechas prácticamente idénticas**, con una diferencia de solo 0,01 pp. Ambos países forman el bloque mediterráneo de mayor brecha digital, superando en más de 5 pp la media de la UE-27.

### 6.2 Doble vulnerabilidad de género (P2)

| Grupo | España | UE-27 |
|---|:---:|:---:|
| Hombres con discapacidad severa | 83,83% | 81,54% |
| Mujeres con discapacidad severa | **73,91%** | 82,93% |
| **Brecha de género** | **9,92 pp** | −1,39 pp |

España presenta la mayor brecha de género del dataset entre países con datos estadísticamente fiables. Las mujeres con discapacidad severa están 23,65 pp por debajo de las mujeres sin discapacidad.

### 6.3 Intersección edad × discapacidad (P3)

| Grupo de edad | % uso Internet (discap. severa, España) |
|---|:---:|
| 25-54 años | 82,31% |
| 55-74 años | **76,85%** ← perfil más vulnerable |
| 16-24 años | *No disponible — muestra insuficiente* |

El efecto del envejecimiento añade 5,46 pp de exclusión adicional dentro del colectivo con discapacidad severa en España.

### 6.4 Clustering K-Means K=3 (P4)

| Grupo | Países | Brecha media |
|---|---|:---:|
| **Alta inclusión** | Países Bajos, Suecia | ~2,9 pp |
| **Inclusión media** | Alemania, Francia, Portugal | ~9,2 pp |
| **Baja inclusión** | España, Italia, Lituania | ~24,1 pp |

España e Italia comparten cluster, coherente con su práctica igualdad en brecha total (18,26 vs 18,27 pp).

</details>

---

<details>
<summary><h2>🏁 7. Conclusiones</h2></summary>

**P1 — Posición europea:** España e Italia presentan brechas digitales por discapacidad prácticamente idénticas (18,26 y 18,27 pp respectivamente), formando el bloque mediterráneo de mayor exclusión digital dentro del dataset. Ambos países superan en más de 5 pp la media europea (12,93 pp) y solo son superados por Lituania (35,86 pp). La brecha no es un problema de conectividad sino de inclusión diferencial.

**P2 — Doble vulnerabilidad (género):** Las mujeres con discapacidad severa en España usan Internet casi 10 pp menos que los hombres en la misma situación (73,91% vs 83,83%). Esta es la mayor brecha de género del dataset entre países con datos estadísticamente fiables.

**P3 — Intersección edad:** El grupo de 55-74 años con discapacidad severa en España presenta la menor tasa de uso de Internet (76,85%), combinando dos factores de exclusión. El envejecimiento añade 5,46 pp de exclusión adicional respecto al grupo de 25-54 años.

**P4 — Tipología de países:** El clustering K-Means con K=3 identifica tres perfiles claros. Los países de alta inclusión (Países Bajos, Suecia) comparten brechas bajas en todos los ejes. España e Italia comparten cluster, coherente con su proximidad en todos los indicadores.

**Limitaciones:** los datos son un corte transversal de 2024, son porcentajes agregados (no microdatos individuales), hay 5 valores no disponibles en `Y16_24_DIS_SEV`, y la cobertura de 8 países no es representativa del conjunto de la UE. Las correlaciones observadas son descriptivas, no causales.

</details>

---

<details>
<summary><h2>📚 8. Bibliografía</h2></summary>

Ver archivo completo en [`docs/bibliografia.md`](docs/bibliografia.md).

**Fuente de datos principal:**
Eurostat (2024). *Persons using the internet in the past 12 months by level of disability (activity limitation)* [DSB_ICTIU01 v1.0]. Statistical Office of the European Union. https://ec.europa.eu/eurostat/databrowser/view/DSB_ICTIU01

**Metodología:**
Chapman, P., Clinton, J., Kerber, R., Khabaza, T., Reinartz, T., Shearer, C., & Wirth, R. (2000). *CRISP-DM 1.0: Step-by-step data mining guide*. SPSS Inc.

**Literatura académica clave:**
- Dobransky, K., & Hargittai, E. (2006). The disability divide in Internet access and use. *Information, Communication & Society*, *9*(3), 313–334.
- Scheerder, A. J., van Deursen, A. J. A. M., & van Dijk, J. A. G. M. (2017). Determinants of Internet skills, uses and outcomes. *Telematics and Informatics*, *34*(8), 1607–1624.

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
| Valor nulo + flag u | ES, FR, LT, NL, SE (Y16_24_DIS_SEV) | 5 | Excluir del análisis |
| Valor disponible + flag u | DE, IT, PT (Y16_24_DIS_SEV) | 3 | Conservar con advertencia |
| Valor disponible + flag u | LT (F/M_DIS_SEV, Y25_54, Y55_74), SE (M_DIS_SEV, Y25_54, Y55_74), FR (Y16_24_DIS_LTD), PT (Y16_24_DIS_LTD) | 11 | Conservar con advertencia |

### Anexo C — Herramientas de IA utilizadas

Se utilizó Claude (Anthropic, modelo Sonnet 4) como apoyo en la estructuración del pipeline de Python, la redacción de consultas SQL y la revisión de coherencia del código. Todo el contenido analítico, la interpretación de resultados y las conclusiones son responsabilidad del autor.

</details>

---

## 📈 Entregables del Proyecto

- [ ] `docs/informe_final.pdf` — Informe completo (11 secciones)
- [ ] `powerbi/dashboard_brecha_digital.pbix` — Dashboard interactivo (4 páginas)
- [x] `python/` — Pipeline Python documentado y modular
- [x] `sql/` — Modelo relacional + consultas analíticas
- [x] Repositorio GitHub con estructura navegable
- [ ] Presentación oral de 15 minutos

---

## 🚀 Inicio rápido

```bash
git clone <repo-url>
cd brecha_digital_discapacidad_es
bash setup.sh
cd python && python -m cleaning.main && python sql_loader.py
python clustering_paises.py   # K-Means K=3
python 03_eda.py              # genera 5 figuras en images/figures/
```

---

*Proyecto desarrollado con Python 3.11, SQL (SQLite) y Power BI. Dataset: Eurostat DSB_ICTIU01 (2024). Metodología: CRISP-DM.*