# 📊 Power BI — Dashboard Brecha Digital por Discapacidad

## Archivo principal

`dashboard_brecha_digital.pbix`

> **Nota:** El archivo `.pbix` se genera directamente en Power BI Desktop.
> Este README documenta su estructura y configuración para reproducibilidad.

---

## Fuente de datos en Power BI

### Opción A — Importar CSV directamente
1. Abrir Power BI Desktop
2. `Obtener datos` → `Texto/CSV`
3. Seleccionar `data/processed/dsb_clean.csv`
4. Seleccionar `data/processed/dsb_derived_metrics.csv`

### Opción B — Conectar a SQLite (recomendado)
1. `Obtener datos` → `Base de datos ODBC`
2. Conectar a la base de datos generada por los scripts SQL
3. Seleccionar las vistas: `vw_ranking_paises`, `vw_genero_dis_sev`, `vw_edad_espana`, `vw_kpis_espana`, `vw_mapa_europeo`

---

## Estructura del Dashboard (páginas)

### Página 1: Resumen — España en Europa
**Visuals:**
- Mapa coroplético de Europa con intensidad de brecha por país
- 3 tarjetas KPI:
  - Brecha España: **18,26 pp**
  - Media UE-27: **12,93 pp**
  - Posición: **2ª mayor brecha**
- Gráfico de barras horizontal: ranking de 8 países por brecha total
- Segmentador: selector de país para comparación directa

### Página 2: Doble Vulnerabilidad — Género
**Visuals:**
- Gráfico de barras agrupadas: hombres vs. mujeres con DIS_SEV, por país
- Callout highlight: España — mujeres 73,91% vs. hombres 83,83%
- Tabla: brecha de género por país ordenada descendentemente
- Filtro: selección de país

### Página 3: Análisis por Edad
**Visuals:**
- Gráfico de líneas: % de uso por grupo de edad × nivel de discapacidad (España)
- Gráfico de barras: grupo 55-74 con DIS_SEV — comparación europea
- Tabla: efecto del envejecimiento (gap_edad) por país

### Página 4: Clustering de Países
**Visuals:**
- Scatter plot: gap_total vs. f_dis_sev, puntos coloreados por cluster
- Tabla de clusters con descripción interpretativa
- Mapa de Europa con países coloreados por grupo de inclusión

---

## Medidas DAX recomendadas

```dax
-- Brecha España
Brecha_Espana =
CALCULATE(
    MAX(dsb_derived_metrics[gap_total]),
    dsb_derived_metrics[pais_cod] = "ES"
)

-- Diferencia España vs. UE-27
Diff_vs_EU27 =
CALCULATE(MAX(dsb_derived_metrics[gap_total]), dsb_derived_metrics[pais_cod]="ES") -
CALCULATE(MAX(dsb_derived_metrics[gap_total]), dsb_derived_metrics[pais_cod]="EU27_2020")

-- % excluidos digitalmente (personas con DIS_SEV que NO usan Internet)
Pct_Excluidos =
DIVIDE(100 - MAX(dsb_internet[pct_uso_internet]), 100)
```

---

## Paleta de colores (coherencia con Python)

| Elemento | Color HEX |
|---|---|
| España (destacado) | `#2E75B6` |
| Media UE-27 (referencia) | `#595959` |
| Alta inclusión (NL, SE) | `#1E6B3C` |
| Baja inclusión (ES, IT, LT) | `#C00000` |
| Fondo de tarjetas | `#D6E4F0` |

---

## Capturas del dashboard

Guardar en: `images/capturas/`
- `captura_pagina1_resumen.png`
- `captura_pagina2_genero.png`
- `captura_pagina3_edad.png`
- `captura_pagina4_clustering.png`
