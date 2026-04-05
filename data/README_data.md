# 📁 data/ — Documentación de los Datos

## Estructura

```
data/
├── raw/                              ← Datos originales. NUNCA modificar.
│   └── dsb_ictiu01_eurostat_2024.csv
└── processed/                        ← Generados por python/01_limpieza_pipeline.ipynb
    ├── dsb_clean.csv                 ← Dataset limpio (sin columnas redundantes, flags gestionados)
    └── dsb_derived_metrics.csv       ← Dataset con métricas derivadas por país
```

## Fuente de los datos

| Campo | Valor |
|---|---|
| Nombre | Persons using the internet in the past 12 months by level of disability (activity limitation) |
| Código Eurostat | DSB_ICTIU01 v1.0 |
| URL de descarga | https://ec.europa.eu/eurostat/databrowser/view/DSB_ICTIU01 |
| Fecha de acceso | 2025 |
| Licencia | Reutilización libre con atribución a Eurostat |
| Formato | CSV lineal (page_linear) |

## Descripción del archivo raw

- **Filas:** 216 (una por combinación país × categoría)
- **Columnas:** 21 (5 útiles para análisis, 16 son metadatos redundantes o vacíos)
- **Año:** 2024 (corte transversal único)
- **Países:** DE, ES, EU27_2020, FR, IT, LT, NL, PT, SE
- **Indicador:** I_ILT12 — uso de Internet en los últimos 12 meses
- **Unidad:** PC_IND — porcentaje de individuos

## Columnas clave

| Columna original | Nombre de trabajo | Descripción |
|---|---|---|
| `geo` | `pais_cod` | Código ISO del país |
| `ind_type` | `categoria_cod` | Código de categoría (discapacidad × sexo × edad) |
| `OBS_VALUE` | `pct_uso_internet` | % de personas que usaron Internet (variable central) |
| `OBS_FLAG` | `flag_calidad` | `u` = baja fiabilidad estadística (Eurostat) |
| `TIME_PERIOD` | `anio` | Año de referencia (2024) |

## Valores faltantes

- **5 observaciones nulas:** todas en la categoría `Y16_24_DIS_SEV` (jóvenes 16-24 con discapacidad severa). Irrecuperables. → Se excluyen del análisis.
- **19 observaciones con flag `u`:** baja fiabilidad. → Se conservan con columna `fiable=False`.

## Métricas derivadas (en dsb_derived_metrics.csv)

| Variable | Cálculo | Descripción |
|---|---|---|
| `gap_total` | `DIS_NONE − DIS_SEV` | Brecha digital entre sin discapacidad y con discapacidad severa |
| `gap_genero` | `M_DIS_SEV − F_DIS_SEV` | Diferencia de uso entre hombres y mujeres con discapacidad severa |
| `gap_edad` | `Y25_54_DIS_SEV − Y55_74_DIS_SEV` | Efecto del envejecimiento sobre la exclusión digital |
| `pos_relativa_eu` | `gap_pais − gap_EU27` | Posición relativa respecto a la media europea |

## Aviso de uso

> Los datos de la carpeta `raw/` son los datos originales descargados de Eurostat.
> **No modificar ningún archivo de `raw/`.**
> Toda transformación debe realizarse en Python y los resultados guardarse en `processed/`.
