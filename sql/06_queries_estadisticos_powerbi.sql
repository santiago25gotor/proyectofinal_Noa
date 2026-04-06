-- ============================================================
-- 06_queries_estadisticos_powerbi.sql
-- Estadísticos descriptivos + vistas específicas para Power BI
-- Prerrequisito: python sql_loader.py
-- ============================================================

-- ── Q1: Estadísticos descriptivos por nivel de discapacidad ──────────────
-- Para qué: Sección 3 del informe (selección e integración de datasets)
SELECT
    dl.description_es                                  AS nivel_discapacidad,
    COUNT(f.pct_internet_use)                          AS n_observaciones,
    ROUND(AVG(f.pct_internet_use), 2)                  AS media,
    ROUND(MIN(f.pct_internet_use), 2)                  AS minimo,
    ROUND(MAX(f.pct_internet_use), 2)                  AS maximo,
    ROUND(MAX(f.pct_internet_use) - MIN(f.pct_internet_use), 2) AS rango,
    SUM(CASE WHEN f.is_reliable=0 THEN 1 ELSE 0 END)  AS obs_baja_fiabilidad,
    SUM(CASE WHEN f.pct_internet_use IS NULL THEN 1 ELSE 0 END) AS obs_nulas
FROM fact_internet_use      f
JOIN dim_individual_type    t  ON f.category_code    = t.category_code
JOIN dim_disability_level   dl ON t.disability_level = dl.disability_level
WHERE t.sex='Total' AND t.age_group='Total'
GROUP BY dl.disability_level, dl.description_es, dl.sort_order
ORDER BY dl.sort_order;

-- ── Q2: Tabla de calidad por país ─────────────────────────────────────────
-- Para qué: Anexos del informe — transparencia metodológica
SELECT
    c.country_name_es                          AS pais,
    COUNT(*)                                   AS total_obs,
    SUM(CASE WHEN f.is_reliable=1 THEN 1 ELSE 0 END) AS fiables,
    SUM(CASE WHEN f.quality_flag='u' AND f.pct_internet_use IS NOT NULL THEN 1 ELSE 0 END) AS flag_u_con_valor,
    SUM(CASE WHEN f.pct_internet_use IS NULL THEN 1 ELSE 0 END) AS nulos,
    ROUND(100.0 * SUM(CASE WHEN f.is_reliable=1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_fiabilidad
FROM fact_internet_use f
JOIN dim_country c ON f.country_code=c.country_code
GROUP BY c.country_code, c.country_name_es
ORDER BY pct_fiabilidad ASC;

-- ── Q3: Tabla comparativa completa por país ───────────────────────────────
-- Para qué: tabla resumen del informe y Power BI overview
SELECT
    COALESCE(CAST(m.country_rank_by_gap AS TEXT), '—')  AS posicion,
    c.country_name_es                                    AS pais,
    ROUND(m.pct_no_disability, 2)                        AS pct_sin_discapacidad,
    ROUND(m.pct_severely_limited, 2)                     AS pct_discap_severa,
    ROUND(m.gap_total, 2)                                AS brecha_total_pp,
    ROUND(m.gap_gender, 2)                               AS brecha_genero_pp,
    ROUND(m.gap_age, 2)                                  AS efecto_envejecimiento_pp,
    ROUND(m.gap_vs_eu27, 2)                              AS vs_media_eu27_pp,
    ROUND(m.pct_excluded_severely, 2)                    AS pct_excluidos_severa,
    COALESCE(m.inclusion_group, '— referencia —')        AS grupo_inclusion
FROM mart_country_metrics m
JOIN dim_country c ON m.country_code=c.country_code
ORDER BY m.is_eu27_aggregate, m.gap_total DESC NULLS LAST;

-- ════════════════════════════════════════════════════════════
-- VISTAS PARA POWER BI (cada vista alimenta una página/visual)
-- ════════════════════════════════════════════════════════════

-- ── Vista A: Mapa coroplético europeo (página 1 dashboard) ───────────────
DROP VIEW IF EXISTS vw_pbi_mapa_europeo;
CREATE VIEW vw_pbi_mapa_europeo AS
SELECT c.country_code, c.country_name_es AS pais, c.iso2_code, c.region,
    ROUND(m.pct_severely_limited, 2)  AS pct_discap_severa,
    ROUND(m.gap_total, 2)             AS brecha_total_pp,
    ROUND(m.pct_excluded_severely, 2) AS pct_excluidos,
    ROUND(m.gap_vs_eu27, 2)           AS vs_media_eu27,
    COALESCE(m.inclusion_group, 'Referencia UE') AS grupo_inclusion,
    m.country_rank_by_gap             AS posicion_ranking
FROM mart_country_metrics m
JOIN dim_country c ON m.country_code=c.country_code;

-- ── Vista B: Ranking de barras (página 1 dashboard) ──────────────────────
DROP VIEW IF EXISTS vw_pbi_ranking;
CREATE VIEW vw_pbi_ranking AS
SELECT c.country_name_es AS pais, c.country_code,
    ROUND(m.pct_no_disability, 2)    AS pct_sin_discapacidad,
    ROUND(m.pct_severely_limited, 2) AS pct_discap_severa,
    ROUND(m.gap_total, 2)            AS brecha_pp,
    CASE c.country_code WHEN 'ES' THEN '#2E75B6'  -- azul España
                        WHEN 'LT' THEN '#C00000'  -- rojo Lituania
                        ELSE '#D9D9D9' END         AS color_barra
FROM mart_country_metrics m
JOIN dim_country c ON m.country_code=c.country_code
ORDER BY m.gap_total DESC NULLS LAST;

-- ── Vista C: Género en discapacidad severa (página 2 dashboard) ──────────
DROP VIEW IF EXISTS vw_pbi_genero;
CREATE VIEW vw_pbi_genero AS
SELECT c.country_name_es AS pais, c.country_code,
    ROUND(m.pct_female_severely, 2) AS pct_mujeres,
    ROUND(m.pct_male_severely, 2)   AS pct_hombres,
    ROUND(m.gap_gender, 2)          AS brecha_genero_pp,
    ROUND(100 - m.pct_female_severely, 2) AS pct_mujeres_excluidas,
    CASE c.country_code WHEN 'ES' THEN 1 ELSE 0 END AS es_espana
FROM mart_country_metrics m
JOIN dim_country c ON m.country_code=c.country_code
ORDER BY ABS(m.gap_gender) DESC;

-- ── Vista D: Edad en España (página 3 dashboard) ──────────────────────────
DROP VIEW IF EXISTS vw_pbi_edad_espana;
CREATE VIEW vw_pbi_edad_espana AS
SELECT ag.label_es AS grupo_edad, ag.sort_order AS orden_edad,
    dl.description_es AS nivel_discapacidad, dl.sort_order AS orden_discapacidad,
    ROUND(f.pct_internet_use, 2) AS pct_uso,
    ROUND(f.pct_excluded, 2)     AS pct_excluidos,
    f.is_reliable                AS dato_fiable
FROM fact_internet_use f
JOIN dim_individual_type  t  ON f.category_code    = t.category_code
JOIN dim_age_group        ag ON t.age_group        = ag.age_group
JOIN dim_disability_level dl ON t.disability_level = dl.disability_level
WHERE f.country_code='ES' AND t.sex='Total' AND t.age_group != 'Total'
  AND dl.is_aggregate=0
ORDER BY ag.sort_order, dl.sort_order;

-- ── Vista E: KPIs de España para tarjetas del dashboard ──────────────────
DROP VIEW IF EXISTS vw_pbi_kpis_espana;
CREATE VIEW vw_pbi_kpis_espana AS
SELECT 1 AS orden, 'Brecha total España (pp)' AS kpi,
    ROUND((SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='DIS_NONE') -
          (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='DIS_SEV'), 2) AS valor_es,
    12.93 AS referencia_eu27, 'pp' AS unidad
UNION ALL SELECT 2, '% mujeres con discapacidad severa',
    (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='F_DIS_SEV'),
    82.93, '%'
UNION ALL SELECT 3, '% grupo 55-74 con discapacidad severa',
    (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='Y55_74_DIS_SEV'),
    76.21, '%'
UNION ALL SELECT 4, '% excluidos digitalmente (discap. severa)',
    ROUND(100.0 - (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='DIS_SEV'), 2),
    17.71, '%'
ORDER BY orden;

SELECT 'Vistas Power BI creadas correctamente.' AS status;
