-- ============================================================
-- analysis_queries.sql
-- ============================================================
-- Consultas analíticas para el proyecto:
--   "Brecha Digital y Discapacidad en España"
-- Fuente: Eurostat DSB_ICTIU01 v1.0 (2024)
--
-- Modelo de datos: schema.sql (modelo estrella normalizado)
-- Tablas principales:
--   fact_internet_use       → medidas por país × categoría
--   mart_country_metrics    → resumen precalculado por país
--   dim_country             → dimensión geográfica
--   dim_individual_type     → 24 categorías (discapacidad × sexo × edad)
--   dim_disability_level    → 4 niveles de discapacidad
--   dim_sex                 → Total / Female / Male
--   dim_age_group           → Total / 16-24 / 25-54 / 55-74
--
-- Vistas disponibles (creadas en schema.sql):
--   v_full_dataset          → tabla plana completa con todos los JOINs
--   v_ranking_brecha        → ranking por brecha principal (P1)
--   v_doble_vulnerabilidad  → brecha de género × discapacidad (P2)
--   v_analisis_edad         → efecto del envejecimiento (P3)
--   v_kpis_espana           → KPIs de España vs. UE-27
--
-- Ejecución: sqlite3 proyecto.db < sql/analysis_queries.sql
-- ============================================================


-- ============================================================
-- CONSULTA 01
-- Perfil completo de España: uso de Internet por nivel de
-- discapacidad (Total sexo, Total edad)
-- ============================================================
-- Para qué sirve:
--   Punto de partida narrativo del proyecto. Muestra de un vistazo
--   los cuatro indicadores de España ordenados de menor a mayor
--   limitación, incluyendo la brecha respecto al grupo de referencia
--   y el porcentaje de personas excluidas digitalmente.
--   Se usa en la Sección 7 (Resultados) del informe y como tarjeta
--   de contexto en la página principal del dashboard de Power BI.
-- ============================================================

SELECT
    dl.sort_order                                   AS orden,
    dl.description_es                               AS nivel_discapacidad,
    ROUND(f.pct_internet_use, 2)                    AS pct_usa_internet,
    ROUND(f.pct_excluded, 2)                        AS pct_excluidos,
    ROUND(f.gap_vs_no_disability, 2)                AS brecha_vs_sin_discapacidad_pp,
    CASE f.is_reliable
        WHEN 1 THEN 'Fiable'
        ELSE    '⚠ Baja fiabilidad'
    END                                             AS calidad_dato
FROM fact_internet_use      f
JOIN dim_individual_type    t  ON f.category_code      = t.category_code
JOIN dim_disability_level   dl ON t.disability_level   = dl.disability_level
WHERE f.country_code  = 'ES'
  AND t.sex           = 'Total'
  AND t.age_group     = 'Total'
ORDER BY dl.sort_order;

-- Resultado esperado:
-- Sin discapacidad → 97.56% uso, 2.44% excluidos, brecha 0.00 pp
-- Limitación leve  → 92.62%, 7.38%, brecha 4.94 pp
-- Limitación severa→ 79.30%, 20.70%, brecha 18.26 pp  ← indicador central
-- Leve o severa    → 90.69%, 9.31%, brecha 6.87 pp


-- ============================================================
-- CONSULTA 02
-- España vs. Media UE-27: comparación directa por nivel de
-- discapacidad
-- ============================================================
-- Para qué sirve:
--   Responde a la pregunta central P1. Sitúa a España en el contexto
--   europeo mostrando en cuántos puntos porcentuales su tasa de uso
--   supera o está por debajo de la media de la UE-27 para cada nivel
--   de discapacidad. Una diferencia negativa en discapacidad severa
--   significa que España está por debajo de la media europea.
--   Input directo para la gráfica comparativa de la página 1 del dashboard.
-- ============================================================

SELECT
    dl.description_es                               AS nivel_discapacidad,
    ROUND(es.pct_internet_use, 2)                   AS espana_pct,
    ROUND(eu.pct_internet_use, 2)                   AS eu27_pct,
    ROUND(es.pct_internet_use - eu.pct_internet_use, 2)
                                                    AS diferencia_pp,
    CASE
        WHEN es.pct_internet_use > eu.pct_internet_use
            THEN 'España por encima de UE-27'
        WHEN es.pct_internet_use < eu.pct_internet_use
            THEN 'España por debajo de UE-27'
        ELSE 'Igual a UE-27'
    END                                             AS posicion_relativa
FROM fact_internet_use      es
JOIN fact_internet_use      eu  ON eu.category_code    = es.category_code
JOIN dim_individual_type    t   ON es.category_code    = t.category_code
JOIN dim_disability_level   dl  ON t.disability_level  = dl.disability_level
WHERE es.country_code = 'ES'
  AND eu.country_code = 'EU27_2020'
  AND t.sex           = 'Total'
  AND t.age_group     = 'Total'
ORDER BY dl.sort_order;


-- ============================================================
-- CONSULTA 03
-- Ranking de países por brecha digital total
-- (No disability − Severely limited, Total sexo, Total edad)
-- ============================================================
-- Para qué sirve:
--   Responde a P1. Ordena los 7 países individuales (excluye EU27_2020
--   del ranking) de mayor a menor brecha. Muestra también cuántos
--   puntos porcentuales de brecha tiene cada país por encima o por
--   debajo de la media europea. España aparece en posición 2 de 7.
--   Base del gráfico de barras horizontal del dashboard y de la tabla
--   de ranking del informe.
-- ============================================================

WITH brecha_paises AS (
    SELECT
        c.country_code,
        c.country_name_es,
        c.is_aggregate,
        ROUND(f_none.pct_internet_use, 2)                   AS pct_sin_discapacidad,
        ROUND(f_sev.pct_internet_use, 2)                    AS pct_discap_severa,
        ROUND(f_none.pct_internet_use - f_sev.pct_internet_use, 2)
                                                            AS brecha_pp,
        ROUND(100.0 - f_sev.pct_internet_use, 2)           AS pct_excluidos
    FROM dim_country c
    JOIN fact_internet_use f_none
        ON  f_none.country_code  = c.country_code
        AND f_none.category_code = 'DIS_NONE'
    JOIN fact_internet_use f_sev
        ON  f_sev.country_code   = c.country_code
        AND f_sev.category_code  = 'DIS_SEV'
    WHERE f_sev.is_reliable = 1
),
brecha_eu27 AS (
    SELECT brecha_pp AS eu27_brecha
    FROM brecha_paises
    WHERE country_code = 'EU27_2020'
)
SELECT
    CASE WHEN bp.is_aggregate = 0
         THEN RANK() OVER (
                  PARTITION BY bp.is_aggregate = 0
                  ORDER BY bp.brecha_pp DESC
              )
         ELSE NULL
    END                                                     AS posicion,
    bp.country_name_es                                      AS pais,
    bp.pct_sin_discapacidad,
    bp.pct_discap_severa,
    bp.brecha_pp                                            AS brecha_total_pp,
    ROUND(bp.brecha_pp - eu27_brecha, 2)                   AS diferencia_vs_eu27,
    bp.pct_excluidos,
    CASE
        WHEN bp.country_code = 'EU27_2020' THEN '— referencia europea —'
        WHEN bp.brecha_pp < 5             THEN 'Alta inclusión'
        WHEN bp.brecha_pp < 12            THEN 'Inclusión media'
        ELSE                                   'Baja inclusión'
    END                                                     AS grupo_inclusion
FROM brecha_paises bp
CROSS JOIN brecha_eu27
ORDER BY bp.is_aggregate, bp.brecha_pp DESC;

-- Resultado esperado (países individuales):
-- Pos 1 Italia      18.27 pp | Pos 2 España  18.26 pp
-- Pos 3 Alemania    11.05 pp | Pos 4 Francia  9.36 pp
-- Pos 5 Portugal     7.26 pp | Pos 6 Suecia   4.72 pp
-- Pos 7 Países Bajos  1.05 pp


-- ============================================================
-- CONSULTA 04
-- Comparación de niveles de discapacidad entre todos los países
-- (tabla pivot: país × nivel de discapacidad)
-- ============================================================
-- Para qué sirve:
--   Visión panorámica de la distribución completa del dataset.
--   Cada fila es un país; cada columna es un nivel de discapacidad.
--   Permite ver de un vistazo qué países tienen valores bajos en
--   discapacidad severa y qué países mantienen alta uniformidad
--   entre niveles (indicativo de buenas políticas de inclusión).
--   Fuente de datos para el heatmap del dashboard y del informe.
-- ============================================================

SELECT
    c.country_name_es                               AS pais,
    ROUND(MAX(CASE WHEN f.category_code = 'DIS_NONE'
                   THEN f.pct_internet_use END), 2) AS sin_discapacidad,
    ROUND(MAX(CASE WHEN f.category_code = 'DIS_LTD'
                   THEN f.pct_internet_use END), 2) AS limitacion_leve,
    ROUND(MAX(CASE WHEN f.category_code = 'DIS_SEV'
                   THEN f.pct_internet_use END), 2) AS limitacion_severa,
    ROUND(MAX(CASE WHEN f.category_code = 'DIS_LTD_SEV'
                   THEN f.pct_internet_use END), 2) AS leve_o_severa,
    ROUND(
        MAX(CASE WHEN f.category_code = 'DIS_NONE' THEN f.pct_internet_use END) -
        MAX(CASE WHEN f.category_code = 'DIS_SEV'  THEN f.pct_internet_use END),
    2)                                              AS brecha_none_vs_sev
FROM fact_internet_use  f
JOIN dim_country         c ON f.country_code = c.country_code
WHERE f.category_code IN ('DIS_NONE', 'DIS_LTD', 'DIS_SEV', 'DIS_LTD_SEV')
GROUP BY c.country_code, c.country_name_es
ORDER BY brecha_none_vs_sev DESC;


-- ============================================================
-- CONSULTA 05
-- Brecha digital específica de España: cada categoría frente
-- al grupo de referencia (Total sexo, Total edad, sin discapacidad)
-- ============================================================
-- Para qué sirve:
--   Descompone la brecha de España en todos sus ejes: no solo por
--   nivel de discapacidad, sino también por sexo y edad. Permite
--   identificar qué subgrupo tiene la mayor exclusión relativa.
--   Útil para el storytelling del informe: el grupo con brecha
--   más alta es el más vulnerable.
--   Se usa en la narrativa de la Sección 8 (Discusión) del informe.
-- ============================================================

SELECT
    f.category_code,
    t.disability_level                              AS nivel_discapacidad,
    t.sex                                           AS sexo,
    t.age_group                                     AS grupo_edad,
    ROUND(f.pct_internet_use, 2)                    AS pct_usa_internet,
    ROUND(f.gap_vs_no_disability, 2)                AS brecha_vs_referencia_pp,
    ROUND(f.pct_excluded, 2)                        AS pct_no_usa_internet,
    CASE f.is_reliable
        WHEN 1 THEN 'Fiable'
        ELSE    '⚠ Baja fiabilidad / sin dato'
    END                                             AS calidad
FROM fact_internet_use      f
JOIN dim_individual_type    t ON f.category_code = t.category_code
WHERE f.country_code  = 'ES'
  AND f.category_code != 'DIS_NONE'        -- excluir la referencia (brecha = 0)
ORDER BY f.gap_vs_no_disability DESC NULLS LAST;

-- El resultado ordena de mayor a menor brecha.
-- Encabeza la lista: F_DIS_SEV (mujeres con discapacidad severa)
-- → brecha de 24.07 pp respecto al grupo de referencia.


-- ============================================================
-- CONSULTA 06
-- Los 5 perfiles más excluidos digitalmente en el dataset
-- (sin restricción de país)
-- ============================================================
-- Para qué sirve:
--   Identifica los casos extremos de exclusión digital en el
--   conjunto de datos. Responde a la pregunta: ¿dónde se concentra
--   la mayor exclusión absoluta? Muestra el porcentaje de personas
--   que NO usan Internet (pct_excluded) de forma directa.
--   Útil para el párrafo de apertura del informe: "el caso más grave
--   del dataset es..."
-- ============================================================

SELECT
    c.country_name_es                               AS pais,
    t.disability_level                              AS nivel_discapacidad,
    t.sex                                           AS sexo,
    t.age_group                                     AS grupo_edad,
    ROUND(f.pct_internet_use, 2)                    AS pct_usa_internet,
    ROUND(f.pct_excluded, 2)                        AS pct_excluidos_digitalmente
FROM fact_internet_use      f
JOIN dim_country            c ON f.country_code  = c.country_code
JOIN dim_individual_type    t ON f.category_code = t.category_code
WHERE f.pct_internet_use IS NOT NULL
  AND f.is_reliable = 1
ORDER BY f.pct_internet_use ASC
LIMIT 5;


-- ============================================================
-- CONSULTA 07
-- Doble vulnerabilidad: brecha de género dentro de la
-- discapacidad severa en todos los países
-- ============================================================
-- Para qué sirve:
--   Responde a P2. Cuantifica la desventaja adicional que experimentan
--   las mujeres con discapacidad severa respecto a los hombres con
--   el mismo nivel de limitación. Un valor positivo en brecha_genero
--   indica que los hombres usan más Internet que las mujeres dentro
--   del mismo colectivo (España: +9.92 pp, el más alto del dataset).
--   Fuente de datos para la Figura 5 del EDA y la página 2 del dashboard.
-- ============================================================

SELECT
    c.country_name_es                               AS pais,
    ROUND(f_f.pct_internet_use, 2)                  AS pct_mujeres,
    ROUND(f_m.pct_internet_use, 2)                  AS pct_hombres,
    ROUND(f_m.pct_internet_use - f_f.pct_internet_use, 2)
                                                    AS brecha_genero_pp,
    ROUND(100.0 - f_f.pct_internet_use, 2)         AS pct_mujeres_excluidas,
    ROUND(100.0 - f_m.pct_internet_use, 2)         AS pct_hombres_excluidos,
    CASE
        WHEN (f_m.pct_internet_use - f_f.pct_internet_use) > 5
            THEN 'Brecha de género alta (hombres usan más)'
        WHEN (f_m.pct_internet_use - f_f.pct_internet_use) < -5
            THEN 'Brecha de género alta (mujeres usan más)'
        WHEN ABS(f_m.pct_internet_use - f_f.pct_internet_use) <= 2
            THEN 'Brecha de género baja (práctica paridad)'
        ELSE 'Brecha de género moderada'
    END                                             AS interpretacion,
    CASE
        WHEN f_f.is_reliable = 0 OR f_m.is_reliable = 0
             THEN '⚠ Algún dato con baja fiabilidad'
        ELSE 'Ambos fiables'
    END                                             AS calidad
FROM dim_country        c
JOIN fact_internet_use  f_f
    ON  f_f.country_code  = c.country_code
    AND f_f.category_code = 'F_DIS_SEV'
JOIN fact_internet_use  f_m
    ON  f_m.country_code  = c.country_code
    AND f_m.category_code = 'M_DIS_SEV'
ORDER BY ABS(f_m.pct_internet_use - f_f.pct_internet_use) DESC;

-- Resultado esperado:
-- España: mujeres 73.91%, hombres 83.83%, brecha +9.92 pp (mayor del dataset)
-- Francia: mujeres 89.28%, hombres 83.30%, brecha -5.98 pp (mujeres usan más)


-- ============================================================
-- CONSULTA 08
-- Efecto del envejecimiento: uso de Internet por grupo de edad
-- dentro de la discapacidad severa (todos los países)
-- ============================================================
-- Para qué sirve:
--   Responde a P3. Mide cómo el envejecimiento amplifica la exclusión
--   digital ya presente por discapacidad. Un gap_edad alto indica que
--   los mayores con discapacidad están mucho más excluidos que los
--   adultos de mediana edad con la misma discapacidad.
--   Portugal presenta el mayor efecto (28.81 pp): sus mayores con
--   discapacidad severa son el grupo con peor acceso proporcional.
--   NOTA: Grupo 16-24 excluido por datos no disponibles (4 nulos).
-- ============================================================

SELECT
    c.country_name_es                               AS pais,
    ROUND(f_25.pct_internet_use, 2)                 AS pct_25_54_anos,
    ROUND(f_55.pct_internet_use, 2)                 AS pct_55_74_anos,
    ROUND(f_25.pct_internet_use - f_55.pct_internet_use, 2)
                                                    AS efecto_envejecimiento_pp,
    CASE
        WHEN (f_25.pct_internet_use - f_55.pct_internet_use) > 20
            THEN 'Efecto muy alto (>20 pp)'
        WHEN (f_25.pct_internet_use - f_55.pct_internet_use) > 10
            THEN 'Efecto alto (10-20 pp)'
        WHEN (f_25.pct_internet_use - f_55.pct_internet_use) > 5
            THEN 'Efecto moderado (5-10 pp)'
        ELSE 'Efecto bajo (<5 pp)'
    END                                             AS clasificacion,
    CASE
        WHEN f_25.is_reliable = 0 OR f_55.is_reliable = 0
             THEN '⚠ Algún dato con baja fiabilidad'
        ELSE 'Ambos fiables'
    END                                             AS calidad
FROM dim_country        c
JOIN fact_internet_use  f_25
    ON  f_25.country_code  = c.country_code
    AND f_25.category_code = 'Y25_54_DIS_SEV'
JOIN fact_internet_use  f_55
    ON  f_55.country_code  = c.country_code
    AND f_55.category_code = 'Y55_74_DIS_SEV'
ORDER BY efecto_envejecimiento_pp DESC;

-- Resultado esperado:
-- Portugal: 28.81 pp | Italia: 14.96 pp | Francia: 13.94 pp
-- España:   5.46 pp  | Países Bajos: 2.61 pp | Suecia: 1.76 pp


-- ============================================================
-- CONSULTA 09
-- España por grupo de edad × nivel de discapacidad
-- (análisis interno de perfiles de edad en España)
-- ============================================================
-- Para qué sirve:
--   Análisis interno de España que combina edad y nivel de discapacidad.
--   Muestra cómo la brecha se intensifica con la edad para cada nivel
--   de limitación. La fila más crítica es: 55-74 años + discapacidad
--   severa → 76.85%, la tasa más baja de España con dato fiable.
--   Fuente del panel izquierdo de la Figura 6 del EDA y de la página
--   3 del dashboard.
-- ============================================================

SELECT
    ag.label_es                                     AS grupo_edad,
    dl.description_es                               AS nivel_discapacidad,
    ROUND(f.pct_internet_use, 2)                    AS pct_usa_internet,
    ROUND(f.pct_excluded, 2)                        AS pct_excluidos,
    ROUND(f.gap_vs_no_disability, 2)                AS brecha_vs_sin_discapacidad,
    CASE f.is_reliable
        WHEN 1 THEN 'Fiable'
        ELSE    '⚠ Sin dato (Y16_24 × DIS_SEV)'
    END                                             AS calidad
FROM fact_internet_use      f
JOIN dim_individual_type    t  ON f.category_code      = t.category_code
JOIN dim_disability_level   dl ON t.disability_level   = dl.disability_level
JOIN dim_age_group          ag ON t.age_group          = ag.age_group
WHERE f.country_code  = 'ES'
  AND t.sex           = 'Total'
  AND t.age_group    != 'Total'
  AND dl.is_aggregate = 0             -- excluir categoría agrupada DIS_LTD_SEV
ORDER BY ag.sort_order, dl.sort_order;


-- ============================================================
-- CONSULTA 10
-- Estadísticos descriptivos globales del dataset
-- ============================================================
-- Para qué sirve:
--   Produce la tabla de estadísticos descriptivos para la Sección 3
--   del informe (Selección e integración de datasets). Muestra media,
--   mediana, desviación, mínimo y máximo de pct_internet_use
--   desglosados por nivel de discapacidad. Confirma que la mayor
--   dispersión está en "Severely limited" (std más alta), lo que
--   refleja la heterogeneidad de políticas entre países.
-- ============================================================

SELECT
    dl.description_es                               AS nivel_discapacidad,
    COUNT(f.pct_internet_use)                       AS n_observaciones,
    ROUND(AVG(f.pct_internet_use), 2)               AS media,
    ROUND(MIN(f.pct_internet_use), 2)               AS minimo,
    ROUND(MAX(f.pct_internet_use), 2)               AS maximo,
    ROUND(MAX(f.pct_internet_use)
        - MIN(f.pct_internet_use), 2)               AS rango,
    SUM(CASE WHEN f.is_reliable = 0 THEN 1 ELSE 0 END)
                                                    AS obs_baja_fiabilidad,
    SUM(CASE WHEN f.pct_internet_use IS NULL THEN 1 ELSE 0 END)
                                                    AS obs_nulas
FROM fact_internet_use      f
JOIN dim_individual_type    t  ON f.category_code    = t.category_code
JOIN dim_disability_level   dl ON t.disability_level = dl.disability_level
WHERE t.sex       = 'Total'
  AND t.age_group = 'Total'
GROUP BY dl.disability_level, dl.description_es, dl.sort_order
ORDER BY dl.sort_order;

-- La desviación típica no es función nativa en SQLite, pero se puede
-- aproximar manualmente. En PostgreSQL o BigQuery usar STDDEV().
-- En Power BI calcular con DAX: STDEV.P([pct_internet_use]).


-- ============================================================
-- CONSULTA 11
-- Tabla de calidad de datos: inventario de observaciones
-- problemáticas (flags u y nulos)
-- ============================================================
-- Para qué sirve:
--   Documenta todas las observaciones con baja fiabilidad estadística
--   (flag 'u' de Eurostat) o sin valor disponible. Esta tabla debe
--   aparecer en los Anexos del informe como evidencia de transparencia
--   metodológica. También es la base para la nota de advertencia en
--   los visuals de Power BI que incluyan datos de baja fiabilidad.
-- ============================================================

SELECT
    c.country_name_es                               AS pais,
    f.category_code,
    t.disability_level                              AS nivel_discapacidad,
    t.sex                                           AS sexo,
    t.age_group                                     AS grupo_edad,
    COALESCE(CAST(ROUND(f.pct_internet_use, 2) AS TEXT), 'SIN DATO')
                                                    AS valor,
    COALESCE(f.quality_flag, '—')                  AS flag_eurostat,
    CASE
        WHEN f.pct_internet_use IS NULL AND f.quality_flag = 'u'
            THEN 'Nulo con flag u — excluir del análisis'
        WHEN f.pct_internet_use IS NOT NULL AND f.quality_flag = 'u'
            THEN 'Valor disponible con flag u — usar con precaución'
        ELSE 'Sin problemas'
    END                                             AS diagnostico,
    CASE
        WHEN f.pct_internet_use IS NULL AND f.quality_flag = 'u'
            THEN 'EXCLUIR'
        WHEN f.pct_internet_use IS NOT NULL AND f.quality_flag = 'u'
            THEN 'CONSERVAR CON MARCA'
        ELSE 'OK'
    END                                             AS decision_pipeline
FROM fact_internet_use      f
JOIN dim_country            c ON f.country_code  = c.country_code
JOIN dim_individual_type    t ON f.category_code = t.category_code
WHERE f.is_reliable = 0
ORDER BY f.pct_internet_use IS NULL DESC, c.country_code, f.category_code;

-- Resultado: 12 observaciones con is_reliable = 0
-- De ellas, 4 son nulos (ES, FR, NL, SE en Y16_24_DIS_SEV)


-- ============================================================
-- CONSULTA 12
-- Tabla comparativa completa Europa: todas las métricas por país
-- (fuente directa para Power BI y el informe)
-- ============================================================
-- Para qué sirve:
--   Consolida las métricas más relevantes del mart_country_metrics
--   en una tabla lista para copiar al informe o conectar en Power BI.
--   Incluye las cuatro métricas de brecha (total, género, edad, vs EU27),
--   el grupo de inclusión y el ranking. Ordenada de mayor a menor brecha
--   para facilitar la lectura comparativa.
-- ============================================================

SELECT
    CASE WHEN m.country_rank_by_gap IS NOT NULL
         THEN CAST(m.country_rank_by_gap AS TEXT)
         ELSE '—'
    END                                             AS posicion,
    c.country_name_es                               AS pais,
    ROUND(m.pct_no_disability, 2)                   AS pct_sin_discapacidad,
    ROUND(m.pct_severely_limited, 2)                AS pct_discap_severa,
    ROUND(m.gap_total, 2)                           AS brecha_total_pp,
    ROUND(m.gap_gender, 2)                          AS brecha_genero_pp,
    ROUND(m.gap_age, 2)                             AS brecha_envejecimiento_pp,
    ROUND(m.gap_vs_eu27, 2)                         AS diferencia_vs_eu27_pp,
    ROUND(m.pct_excluded_severely, 2)               AS pct_excluidos_discap_severa,
    COALESCE(m.inclusion_group, '— referencia —')  AS grupo_inclusion,
    CASE
        WHEN m.is_eu27_aggregate = 1 THEN 'Agregado europeo (referencia)'
        ELSE c.region
    END                                             AS region
FROM mart_country_metrics   m
JOIN dim_country            c ON m.country_code = c.country_code
ORDER BY m.is_eu27_aggregate, m.gap_total DESC NULLS LAST;


-- ============================================================
-- CONSULTA 13
-- España en perspectiva: ¿cuánto tendría que mejorar para
-- alcanzar a los países líderes?
-- ============================================================
-- Para qué sirve:
--   Pregunta práctica con impacto narrativo para la presentación.
--   Calcula la distancia entre España y los países de "Alta inclusión"
--   (Países Bajos y Suecia) en puntos porcentuales. Responde a:
--   "¿Cuánto le falta a España para llegar al nivel de los mejores?"
--   Útil para las conclusiones del informe y como slide de cierre
--   en la presentación oral.
-- ============================================================

WITH espana AS (
    SELECT
        pct_severely_limited    AS es_pct,
        gap_total               AS es_brecha
    FROM mart_country_metrics
    WHERE country_code = 'ES'
),
eu27 AS (
    SELECT gap_total AS eu_brecha
    FROM mart_country_metrics
    WHERE country_code = 'EU27_2020'
)
SELECT
    c.country_name_es                               AS pais_referencia,
    ROUND(m.pct_severely_limited, 2)                AS pct_discap_severa_referencia,
    ROUND(espana.es_pct, 2)                         AS pct_discap_severa_espana,
    ROUND(m.pct_severely_limited - espana.es_pct, 2)
                                                    AS mejora_necesaria_pp,
    ROUND(m.gap_total, 2)                           AS brecha_pais_referencia,
    ROUND(espana.es_brecha, 2)                      AS brecha_espana,
    ROUND(espana.es_brecha - m.gap_total, 2)        AS reduccion_brecha_necesaria_pp
FROM mart_country_metrics   m
JOIN dim_country            c ON m.country_code = c.country_code
CROSS JOIN espana
CROSS JOIN eu27
WHERE m.inclusion_group IN ('Alta inclusión', 'Inclusión media')
  AND m.country_code != 'ES'
ORDER BY m.gap_total;

-- Resultado interpretativo:
-- Para llegar al nivel de Países Bajos (1.05 pp de brecha),
-- España necesitaría reducir su brecha en 17.21 pp.
-- Para alcanzar la media UE-27 (12.93 pp), la reducción necesaria
-- sería de 5.33 pp, un objetivo más realista a corto plazo.


-- ============================================================
-- CONSULTA 14
-- Clasificación de países por grupo de inclusión con detalle
-- de todas las métricas de brecha
-- ============================================================
-- Para qué sirve:
--   Responde a P4 (tipología de países). Agrupa los países en sus
--   categorías de inclusión digital y muestra qué tienen en común
--   los países de cada grupo. Los países de "Alta inclusión" tienen
--   brechas bajas en todos los ejes (total, género y edad), lo que
--   sugiere políticas de inclusión más integrales.
--   Base para la interpretación del clustering en el informe.
-- ============================================================

SELECT
    COALESCE(m.inclusion_group, '— Agregado UE (sin grupo) —')
                                                    AS grupo_inclusion,
    GROUP_CONCAT(c.country_name_es, ' · ')          AS paises,
    COUNT(CASE WHEN m.is_eu27_aggregate = 0 THEN 1 END)
                                                    AS n_paises,
    ROUND(AVG(CASE WHEN m.is_eu27_aggregate = 0 THEN m.gap_total END), 2)
                                                    AS brecha_media_grupo,
    ROUND(MIN(CASE WHEN m.is_eu27_aggregate = 0 THEN m.gap_total END), 2)
                                                    AS brecha_minima,
    ROUND(MAX(CASE WHEN m.is_eu27_aggregate = 0 THEN m.gap_total END), 2)
                                                    AS brecha_maxima,
    ROUND(AVG(CASE WHEN m.is_eu27_aggregate = 0 THEN ABS(m.gap_gender) END), 2)
                                                    AS brecha_genero_media_abs,
    ROUND(AVG(CASE WHEN m.is_eu27_aggregate = 0 THEN m.gap_age END), 2)
                                                    AS efecto_envejecimiento_medio
FROM mart_country_metrics   m
JOIN dim_country            c ON m.country_code = c.country_code
GROUP BY m.inclusion_group
ORDER BY brecha_media_grupo DESC NULLS LAST;

-- Grupos esperados:
-- Baja inclusión (IT, ES):    brecha media ~18 pp, brecha_género alta
-- Inclusión media (DE,FR,PT): brecha media ~9 pp
-- Alta inclusión (SE, NL):    brecha media ~3 pp, género y edad bajos


-- ============================================================
-- CONSULTA 15
-- Tabla resumen de datos de calidad para los Anexos del informe
-- ============================================================
-- Para qué sirve:
--   Produce la tabla de inventario de datos del informe: cuántas
--   observaciones hay en total, cuántas son fiables, cuántas tienen
--   flag de baja fiabilidad y cuántas son nulas. Desglosado por país
--   para identificar cuáles tienen más problemas de cobertura.
--   Debe incluirse en los Anexos o en la sección de Metodología.
-- ============================================================

SELECT
    c.country_name_es                               AS pais,
    COUNT(*)                                        AS total_obs,
    SUM(CASE WHEN f.is_reliable = 1 THEN 1 ELSE 0 END)
                                                    AS obs_fiables,
    SUM(CASE WHEN f.quality_flag = 'u'
                  AND f.pct_internet_use IS NOT NULL
             THEN 1 ELSE 0 END)                     AS obs_flag_u_con_valor,
    SUM(CASE WHEN f.pct_internet_use IS NULL THEN 1 ELSE 0 END)
                                                    AS obs_nulas,
    ROUND(
        100.0 * SUM(CASE WHEN f.is_reliable = 1 THEN 1 ELSE 0 END)
        / COUNT(*),
    1)                                              AS pct_fiabilidad
FROM fact_internet_use  f
JOIN dim_country        c ON f.country_code = c.country_code
GROUP BY c.country_code, c.country_name_es
ORDER BY pct_fiabilidad ASC;


-- ============================================================
-- VISTAS ADICIONALES PARA POWER BI
-- ============================================================
-- Las siguientes vistas están diseñadas específicamente para ser
-- importadas como tablas en Power BI Desktop.
-- Cada vista corresponde a un visual o página del dashboard.
-- ============================================================


-- ── Vista A: Datos para el mapa coroplético europeo ───────────────
-- Alimenta el mapa de calor de la página 1 del dashboard.
-- Una fila por país con la brecha total y el grupo de inclusión.
-- Power BI usa country_code (código ISO) para geolocalizar.
-- ─────────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS vw_pbi_mapa_europeo;
CREATE VIEW vw_pbi_mapa_europeo AS
SELECT
    c.country_code,
    c.country_name_es                           AS pais,
    c.iso2_code,
    c.region,
    c.is_aggregate                              AS es_agregado_eu27,
    ROUND(m.pct_severely_limited, 2)            AS pct_discap_severa,
    ROUND(m.gap_total, 2)                       AS brecha_total_pp,
    ROUND(m.pct_excluded_severely, 2)           AS pct_excluidos,
    ROUND(m.gap_vs_eu27, 2)                     AS diferencia_vs_eu27,
    COALESCE(m.inclusion_group, 'Referencia UE')AS grupo_inclusion,
    m.country_rank_by_gap                       AS posicion_ranking
FROM mart_country_metrics   m
JOIN dim_country            c ON m.country_code = c.country_code;


-- ── Vista B: Datos para el gráfico de ranking de barras ──────────
-- Alimenta el gráfico de barras horizontal de la página 1.
-- Incluye colores sugeridos para España (destacada en azul).
-- ─────────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS vw_pbi_ranking_barras;
CREATE VIEW vw_pbi_ranking_barras AS
SELECT
    c.country_name_es                           AS pais,
    c.country_code,
    ROUND(m.pct_no_disability, 2)               AS pct_sin_discapacidad,
    ROUND(m.pct_severely_limited, 2)            AS pct_discap_severa,
    ROUND(m.gap_total, 2)                       AS brecha_pp,
    ROUND(m.gap_vs_eu27, 2)                     AS vs_media_europea,
    CASE c.country_code
        WHEN 'ES' THEN '#2E75B6'                -- azul España (destacado)
        ELSE            '#D9D9D9'               -- gris otros países
    END                                         AS color_barra,
    CASE c.is_aggregate
        WHEN 1 THEN 1 ELSE 0
    END                                         AS es_referencia
FROM mart_country_metrics   m
JOIN dim_country            c ON m.country_code = c.country_code
ORDER BY m.gap_total DESC NULLS LAST;


-- ── Vista C: Datos para el gráfico de género ─────────────────────
-- Alimenta el gráfico de barras agrupadas hombres vs. mujeres
-- en la página 2 del dashboard.
-- ─────────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS vw_pbi_genero;
CREATE VIEW vw_pbi_genero AS
SELECT
    c.country_name_es                           AS pais,
    c.country_code,
    ROUND(m.pct_female_severely, 2)             AS pct_mujeres,
    ROUND(m.pct_male_severely, 2)               AS pct_hombres,
    ROUND(m.gap_gender, 2)                      AS brecha_genero_pp,
    ROUND(100.0 - m.pct_female_severely, 2)    AS pct_mujeres_excluidas,
    ROUND(100.0 - m.pct_male_severely, 2)      AS pct_hombres_excluidos,
    CASE c.country_code
        WHEN 'ES' THEN 1 ELSE 0
    END                                         AS es_espana
FROM mart_country_metrics   m
JOIN dim_country            c ON m.country_code = c.country_code
ORDER BY ABS(m.gap_gender) DESC;


-- ── Vista D: Datos para el gráfico de edad (España) ──────────────
-- Alimenta el gráfico de barras agrupadas por edad y nivel de
-- discapacidad de la página 3 del dashboard.
-- Solo incluye datos de España con grupos de edad disponibles.
-- ─────────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS vw_pbi_edad_espana;
CREATE VIEW vw_pbi_edad_espana AS
SELECT
    ag.label_es                                 AS grupo_edad,
    ag.sort_order                               AS orden_edad,
    dl.description_es                           AS nivel_discapacidad,
    dl.sort_order                               AS orden_discapacidad,
    ROUND(f.pct_internet_use, 2)                AS pct_uso,
    ROUND(f.pct_excluded, 2)                    AS pct_excluidos,
    f.is_reliable                               AS dato_fiable
FROM fact_internet_use      f
JOIN dim_individual_type    t  ON f.category_code    = t.category_code
JOIN dim_age_group          ag ON t.age_group        = ag.age_group
JOIN dim_disability_level   dl ON t.disability_level = dl.disability_level
WHERE f.country_code  = 'ES'
  AND t.sex           = 'Total'
  AND t.age_group    != 'Total'
  AND dl.is_aggregate = 0
ORDER BY ag.sort_order, dl.sort_order;


-- ── Vista E: KPIs de España para tarjetas del dashboard ──────────
-- Alimenta las cuatro tarjetas KPI de la página principal.
-- Formato vertical (una KPI por fila) para flexibilidad en Power BI.
-- ─────────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS vw_pbi_kpis_espana;
CREATE VIEW vw_pbi_kpis_espana AS
SELECT 1 AS orden, 'Brecha total España'                AS kpi,
    ROUND(m.gap_total, 2)                               AS valor_espana,
    12.93                                               AS referencia_eu27,
    ROUND(m.gap_total - 12.93, 2)                       AS diferencia,
    'pp'                                                AS unidad
FROM mart_country_metrics m WHERE m.country_code = 'ES'
UNION ALL
SELECT 2, '% mujeres con discapacidad severa',
    ROUND(m.pct_female_severely, 2), 82.93,
    ROUND(m.pct_female_severely - 82.93, 2), '%'
FROM mart_country_metrics m WHERE m.country_code = 'ES'
UNION ALL
SELECT 3, '% grupo 55-74 con discapacidad severa',
    ROUND(m.pct_55_74_severely, 2), 76.21,
    ROUND(m.pct_55_74_severely - 76.21, 2), '%'
FROM mart_country_metrics m WHERE m.country_code = 'ES'
UNION ALL
SELECT 4, '% excluidos digitalmente (discap. severa)',
    ROUND(m.pct_excluded_severely, 2), 17.71,
    ROUND(m.pct_excluded_severely - 17.71, 2), '%'
FROM mart_country_metrics m WHERE m.country_code = 'ES'
ORDER BY orden;

-- ============================================================
-- FIN DEL ARCHIVO
-- ============================================================
-- Resumen de objetos creados:
--   15 consultas SELECT comentadas con su propósito analítico
--    5 vistas para Power BI (vw_pbi_*)
--
-- Vistas previas de schema.sql que siguen disponibles:
--   v_full_dataset          · v_ranking_brecha
--   v_doble_vulnerabilidad  · v_analisis_edad · v_kpis_espana
-- ============================================================
