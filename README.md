# 🌐 Brecha Digital y Discapacidad en España
## Análisis Comparativo Europeo mediante técnicas de Big Data

**Proyecto Final de la Especialidad · Big Data e Inteligencia Artificial**  
IFP · Innovación en Formación Profesional · Curso 2025-2026

---

## 📋 Resumen (Abstract)

Este proyecto analiza y caracteriza la **brecha digital por discapacidad en España** en comparación con ocho países europeos y la media de la UE-27, utilizando datos oficiales de Eurostat (indicador DSB_ICTIU01, año 2024).

España presenta una brecha de **18,26 puntos porcentuales** entre personas sin discapacidad (97,56% de uso de Internet) y personas con discapacidad severa (79,30%), situándose como el segundo país con mayor brecha del dataset, muy por encima de la media europea (12,93 pp). El análisis identifica además una **doble vulnerabilidad** en mujeres con discapacidad severa (73,91%) y en el grupo de 55-74 años (76,85%).

---

## 🎯 Preguntas de Investigación

**Pregunta principal:**  
¿Cuál es la magnitud real de la brecha digital por discapacidad en España en comparación con sus pares europeos, y qué perfiles sociodemográficos concentran la mayor exclusión?

**Preguntas secundarias:**
1. ¿En qué posición se sitúa España respecto a Alemania, Francia, Italia, Países Bajos, Portugal, Suecia, Lituania y la media UE-27?
2. ¿Existe una brecha de género significativa dentro del colectivo con discapacidad severa?
3. ¿Qué grupo de edad concentra la mayor exclusión digital entre personas con discapacidad?
4. ¿Es posible identificar tipologías de países europeos según su perfil de inclusión digital?

---

## 🗂️ Estructura del Proyecto

```
brecha_digital_discapacidad_es/
│
├── README.md                        ← Este archivo
├── requirements.txt                 ← Dependencias Python
├── .gitignore                       ← Exclusiones Git
│
├── data/
│   ├── raw/                         ← Datos originales sin modificar
│   └── processed/                   ← Datos limpios y métricas derivadas
│
├── sql/                             ← Queries y schema de base de datos
├── python/                          ← Notebooks de análisis
├── powerbi/                         ← Dashboard interactivo
├── docs/                            ← Informe final y presentación
├── images/                          ← Figuras y capturas
└── outputs/                         ← Tablas y exportaciones de resultados
```

---

## 🛠️ Herramientas y Tecnologías

| Herramienta | Versión | Uso en el proyecto |
|---|---|---|
| Python | 3.11+ | Pipeline de limpieza, EDA, clustering |
| Pandas | 2.x | Manipulación y transformación de datos |
| Matplotlib / Seaborn | latest | Visualización analítica |
| Scikit-learn | 1.x | K-Means clustering |
| SQL (SQLite / BigQuery) | — | Estructuración y consultas de datos |
| Power BI Desktop | latest | Dashboard interactivo final |

---

## 📊 Fuente de Datos

| Campo | Detalle |
|---|---|
| Fuente | Eurostat — Statistical Office of the European Union |
| Indicador | DSB_ICTIU01 v1.0 |
| Nombre completo | Persons using the internet in the past 12 months by level of disability |
| Año | 2024 |
| Países | DE, ES, EU27, FR, IT, LT, NL, PT, SE |
| URL | https://ec.europa.eu/eurostat |
| Licencia | Datos públicos — reutilización libre con atribución |
| Archivo local | `data/raw/dsb_ictiu01_eurostat_2024.csv` |

---

## 🔬 Metodología

El proyecto sigue el modelo **CRISP-DM** (Cross-Industry Standard Process for Data Mining):

| Fase | Descripción | Herramienta | Archivo |
|---|---|---|---|
| 1. Comprensión del negocio | Definición del problema y preguntas | — | `docs/` |
| 2. Comprensión de los datos | Exploración inicial del dataset | Python | `python/01_limpieza_pipeline.ipynb` |
| 3. Preparación de los datos | Limpieza, transformación, métricas | Python | `python/01_limpieza_pipeline.ipynb` |
| 4. Modelado | EDA, análisis comparativo, clustering | Python + SQL | `python/`, `sql/` |
| 5. Evaluación | Interpretación y contraste | — | `docs/informe_final.pdf` |
| 6. Despliegue | Dashboard interactivo | Power BI | `powerbi/` |

---

## 🚀 Orden de Ejecución

```
PASO 1  →  sql/01_create_schema.sql       (crear tabla en base de datos)
PASO 2  →  sql/02_load_data.sql           (cargar datos limpios)
PASO 3  →  python/01_limpieza_pipeline.ipynb  (limpiar y exportar a processed/)
PASO 4  →  python/02_eda_descriptivo.ipynb    (análisis exploratorio)
PASO 5  →  python/03_analisis_brecha_europa.ipynb  (ranking y brecha)
PASO 6  →  python/04_doble_vulnerabilidad.ipynb    (género y edad)
PASO 7  →  python/05_clustering_paises.ipynb       (K-Means)
PASO 8  →  sql/03_q_ranking_brecha.sql    (queries analíticas)
PASO 9  →  sql/07_views_powerbi.sql       (vistas para Power BI)
PASO 10 →  powerbi/dashboard_brecha_digital.pbix   (dashboard final)
```

---

## 📈 Resultados Principales

| Hallazgo | Valor | Contexto europeo |
|---|---|---|
| Brecha total España (DIS_NONE − DIS_SEV) | **18,26 pp** | 2ª más alta del dataset |
| Media UE-27 | 12,93 pp | España supera en +5,33 pp |
| Mujeres con discapacidad severa (España) | 73,91% | 9,92 pp menos que hombres |
| Grupo 55-74 con discapacidad severa | 76,85% | Perfil de mayor vulnerabilidad |
| Países Bajos (referencia) | 1,05 pp brecha | Mejor resultado europeo |

---

## 📁 Entregables del Proyecto

- [x] `docs/informe_final.pdf` — Informe completo en PDF
- [x] `powerbi/dashboard_brecha_digital.pbix` — Dashboard interactivo
- [x] `python/` — Notebooks documentados con outputs
- [x] `sql/` — Queries completas comentadas
- [ ] Repositorio GitHub con estructura navegable
- [ ] Presentación oral de 15 minutos

---

## 📚 Referencias Principales

- Eurostat (2024). *Persons using the internet in the past 12 months by level of disability*. DSB_ICTIU01. https://ec.europa.eu/eurostat
- Chapman, P. et al. (2000). *CRISP-DM 1.0: Step-by-step data mining guide*. SPSS Inc.
- Comisión Europea (2021). *Década Digital de Europa: objetivos digitales para 2030*. https://commission.europa.eu
- España. *Real Decreto Legislativo 1/2013* — Ley General de Derechos de las Personas con Discapacidad (LGDPD). BOE núm. 289.

---

*Proyecto desarrollado con Python, SQL y Power BI. Dataset: Eurostat DSB_ICTIU01 (2024).*
