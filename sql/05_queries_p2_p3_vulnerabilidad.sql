-- ============================================================
-- 05_queries_p2_p3_vulnerabilidad.sql
-- P2: Doble vulnerabilidad género × discapacidad
-- P3: Intersección edad × discapacidad
-- Prerrequisito: python sql_loader.py
-- ============================================================

-- ── P2-Q1: Brecha de género dentro de discapacidad severa ────────────────
-- Para qué: responde P2; España tiene la mayor brecha de género (9.92 pp)
-- Uso: gráfico barras agrupadas, página 2 del dashboard
SELECT
    c.country_name_es                                              AS pais,
    ROUND(f_f.pct_internet_use, 2)                                 AS pct_mujeres,
    ROUND(f_m.pct_internet_use, 2)                                 AS pct_hombres,
    ROUND(f_m.pct_internet_use - f_f.pct_internet_use, 2)         AS brecha_genero_pp,
    ROUND(100.0 - f_f.pct_internet_use, 2)                        AS pct_mujeres_excluidas,
    CASE
        WHEN (f_m.pct_internet_use - f_f.pct_internet_use) > 5    THEN 'Hombres usan más (+5 pp)'
        WHEN (f_m.pct_internet_use - f_f.pct_internet_use) < -5   THEN 'Mujeres usan más (-5 pp)'
        ELSE 'Brecha moderada (<5 pp)'
    END                                                            AS interpretacion,
    CASE WHEN f_f.is_reliable=0 OR f_m.is_reliable=0 THEN '⚠ Dato poco fiable' ELSE 'OK' END AS calidad
FROM dim_country c
JOIN fact_internet_use f_f ON f_f.country_code=c.country_code AND f_f.category_code='F_DIS_SEV'
JOIN fact_internet_use f_m ON f_m.country_code=c.country_code AND f_m.category_code='M_DIS_SEV'
ORDER BY ABS(f_m.pct_internet_use - f_f.pct_internet_use) DESC;

-- ── P2-Q2: España — brecha género por nivel de discapacidad ──────────────
SELECT
    dl.description_es                                AS nivel_discapacidad,
    ROUND(f_t.pct_internet_use, 2)                   AS pct_total,
    ROUND(f_f.pct_internet_use, 2)                   AS pct_mujeres,
    ROUND(f_m.pct_internet_use, 2)                   AS pct_hombres,
    ROUND(f_m.pct_internet_use - f_f.pct_internet_use, 2) AS brecha_genero_pp
FROM dim_disability_level dl
JOIN dim_individual_type  t_t ON t_t.disability_level=dl.disability_level AND t_t.sex='Total' AND t_t.age_group='Total'
JOIN dim_individual_type  t_f ON t_f.disability_level=dl.disability_level AND t_f.sex='Female' AND t_f.age_group='Total'
JOIN dim_individual_type  t_m ON t_m.disability_level=dl.disability_level AND t_m.sex='Male'   AND t_m.age_group='Total'
JOIN fact_internet_use f_t ON f_t.category_code=t_t.category_code AND f_t.country_code='ES'
JOIN fact_internet_use f_f ON f_f.category_code=t_f.category_code AND f_f.country_code='ES'
JOIN fact_internet_use f_m ON f_m.category_code=t_m.category_code AND f_m.country_code='ES'
ORDER BY dl.sort_order;

-- ── P3-Q1: Efecto del envejecimiento en discapacidad severa ──────────────
-- Para qué: responde P3; efecto_envejecimiento = uso_25-54 - uso_55-74
-- Nota: grupo 16-24 excluido — datos no disponibles en varios países
SELECT
    c.country_name_es                                                      AS pais,
    ROUND(f_25.pct_internet_use, 2)                                        AS pct_25_54_dis_sev,
    ROUND(f_55.pct_internet_use, 2)                                        AS pct_55_74_dis_sev,
    ROUND(f_25.pct_internet_use - f_55.pct_internet_use, 2)               AS efecto_envejecimiento_pp,
    CASE
        WHEN (f_25.pct_internet_use - f_55.pct_internet_use) > 20         THEN 'Muy alto (>20 pp)'
        WHEN (f_25.pct_internet_use - f_55.pct_internet_use) > 10         THEN 'Alto (10-20 pp)'
        WHEN (f_25.pct_internet_use - f_55.pct_internet_use) > 5          THEN 'Moderado (5-10 pp)'
        ELSE                                                                    'Bajo (<5 pp)'
    END                                                                    AS clasificacion,
    CASE WHEN f_25.is_reliable=0 OR f_55.is_reliable=0 THEN '⚠ Dato poco fiable' ELSE 'OK' END AS calidad
FROM dim_country c
JOIN fact_internet_use f_25 ON f_25.country_code=c.country_code AND f_25.category_code='Y25_54_DIS_SEV'
JOIN fact_internet_use f_55 ON f_55.country_code=c.country_code AND f_55.category_code='Y55_74_DIS_SEV'
ORDER BY efecto_envejecimiento_pp DESC;

-- ── P3-Q2: España por grupo de edad × nivel de discapacidad ──────────────
-- Para qué: perfil interno de España; el grupo 55-74 + severa = más vulnerable
SELECT
    ag.label_es                            AS grupo_edad,
    dl.description_es                      AS nivel_discapacidad,
    ROUND(f.pct_internet_use, 2)           AS pct_usa_internet,
    ROUND(f.pct_excluded, 2)              AS pct_excluidos,
    ROUND(f.gap_vs_no_disability, 2)      AS brecha_vs_sin_discapacidad,
    CASE f.is_reliable WHEN 1 THEN 'Fiable' ELSE '⚠ Sin dato (muestra insuficiente)' END AS calidad
FROM fact_internet_use      f
JOIN dim_individual_type    t  ON f.category_code    = t.category_code
JOIN dim_disability_level   dl ON t.disability_level = dl.disability_level
JOIN dim_age_group          ag ON t.age_group        = ag.age_group
WHERE f.country_code='ES' AND t.sex='Total' AND t.age_group != 'Total'
  AND dl.is_aggregate=0
ORDER BY ag.sort_order, dl.sort_order;

-- ── P2+P3: Los 5 perfiles más excluidos del dataset completo ─────────────
-- Para qué: apertura narrativa del informe ("el caso más grave es...")
SELECT
    c.country_name_es   AS pais,
    t.disability_level  AS nivel_discapacidad,
    t.sex               AS sexo,
    t.age_group         AS grupo_edad,
    ROUND(f.pct_internet_use, 2) AS pct_usa_internet,
    ROUND(f.pct_excluded, 2)     AS pct_excluidos
FROM fact_internet_use f
JOIN dim_country         c ON f.country_code  = c.country_code
JOIN dim_individual_type t ON f.category_code = t.category_code
WHERE f.pct_internet_use IS NOT NULL AND f.is_reliable=1
ORDER BY f.pct_internet_use ASC
LIMIT 5;

-- ── Tabla de calidad: inventario de datos problemáticos ──────────────────
-- Para qué: incluir en los Anexos del informe (transparencia metodológica)
SELECT
    c.country_name_es                                             AS pais,
    f.category_code,
    t.sex AS sexo, t.age_group AS grupo_edad, t.disability_level AS discapacidad,
    COALESCE(CAST(ROUND(f.pct_internet_use,2) AS TEXT), 'SIN DATO') AS valor,
    COALESCE(f.quality_flag, '—')                                AS flag_eurostat,
    CASE
        WHEN f.pct_internet_use IS NULL THEN 'Nulo — excluir del análisis'
        ELSE 'Valor disponible — usar con precaución'
    END                                                          AS decision
FROM fact_internet_use      f
JOIN dim_country            c ON f.country_code  = c.country_code
JOIN dim_individual_type    t ON f.category_code = t.category_code
WHERE f.is_reliable=0
ORDER BY f.pct_internet_use IS NULL DESC, c.country_code;
