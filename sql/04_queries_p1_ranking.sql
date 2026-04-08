-- ============================================================
-- 04_queries_p1_ranking.sql
-- Consultas para P1: posición de España en el ranking europeo
-- Prerrequisito: python sql_loader.py (pobla fact_internet_use)
--
-- RANKING VERIFICADO CON EL CSV REAL (Eurostat 2024):
--   1º Lituania    93,31 - 57,45 = 35,86 pp
--   2º Italia      92,88 - 74,61 = 18,27 pp
--   3º España      97,56 - 79,30 = 18,26 pp  ← diferencia de 0,01 pp con Italia
--   ref UE-27      95,22 - 82,29 = 12,93 pp
--   4º Alemania    95,58 - 84,53 = 11,05 pp
--   5º Francia     96,24 - 86,88 =  9,36 pp
--   6º Portugal    91,73 - 84,47 =  7,26 pp
--   7º Suecia      99,15 - 94,43 =  4,72 pp
--   8º Países Bajos 99,72 - 98,67 = 1,05 pp
--
-- España e Italia forman el bloque mediterráneo de mayor brecha.
-- ============================================================

-- ── Q1: Perfil completo de España ────────────────────────────────────────
-- Resultado esperado:
--   Sin discapacidad: 97,56% | Severa: 79,30% | Brecha: 18,26 pp
SELECT
    dl.sort_order                              AS orden,
    dl.description_es                          AS nivel_discapacidad,
    ROUND(f.pct_internet_use, 2)               AS pct_usa_internet,
    ROUND(f.pct_excluded, 2)                   AS pct_excluidos,
    ROUND(f.gap_vs_no_disability, 2)           AS brecha_vs_sin_discapacidad_pp,
    CASE f.is_reliable WHEN 1 THEN 'Fiable' ELSE '⚠ Baja fiabilidad' END AS calidad
FROM fact_internet_use      f
JOIN dim_individual_type    t  ON f.category_code    = t.category_code
JOIN dim_disability_level   dl ON t.disability_level = dl.disability_level
WHERE f.country_code='ES' AND t.sex='Total' AND t.age_group='Total'
ORDER BY dl.sort_order;

-- ── Q2: España vs. Media UE-27 por nivel de discapacidad ─────────────────
SELECT
    dl.description_es                                          AS nivel_discapacidad,
    ROUND(es.pct_internet_use, 2)                              AS espana_pct,
    ROUND(eu.pct_internet_use, 2)                              AS eu27_pct,
    ROUND(es.pct_internet_use - eu.pct_internet_use, 2)        AS diferencia_pp,
    CASE
        WHEN es.pct_internet_use > eu.pct_internet_use THEN '↑ España por encima'
        WHEN es.pct_internet_use < eu.pct_internet_use THEN '↓ España por debajo'
        ELSE '= Igual'
    END                                                         AS posicion_relativa
FROM fact_internet_use      es
JOIN fact_internet_use      eu ON eu.category_code  = es.category_code
JOIN dim_individual_type    t  ON es.category_code  = t.category_code
JOIN dim_disability_level   dl ON t.disability_level = dl.disability_level
WHERE es.country_code='ES' AND eu.country_code='EU27_2020'
  AND t.sex='Total' AND t.age_group='Total'
ORDER BY dl.sort_order;

-- ── Q3: Ranking europeo completo por brecha total ────────────────────────
-- Resultado esperado: LT 1º (35,86), IT 2º (18,27), ES 3º (18,26)
-- Italia y España presentan brechas prácticamente idénticas (0,01 pp)
WITH brecha AS (
    SELECT c.country_code, c.country_name_es, c.is_aggregate,
           ROUND(fn.pct_internet_use, 2) AS pct_sin_discap,
           ROUND(fs.pct_internet_use, 2) AS pct_severa,
           ROUND(fn.pct_internet_use - fs.pct_internet_use, 2) AS gap_pp,
           ROUND(100.0 - fs.pct_internet_use, 2) AS pct_excluidos
    FROM dim_country c
    JOIN fact_internet_use fn ON fn.country_code = c.country_code AND fn.category_code = 'DIS_NONE'
    JOIN fact_internet_use fs ON fs.country_code = c.country_code AND fs.category_code = 'DIS_SEV'
    WHERE fs.is_reliable = 1
),
ref_eu27 AS (SELECT gap_pp AS eu27_gap FROM brecha WHERE country_code = 'EU27_2020')
SELECT
    CASE WHEN b.is_aggregate = 0
         THEN RANK() OVER (PARTITION BY b.is_aggregate = 0 ORDER BY b.gap_pp DESC)
         ELSE NULL END              AS posicion,
    b.country_name_es               AS pais,
    b.pct_sin_discap,
    b.pct_severa,
    b.gap_pp                        AS brecha_total_pp,
    ROUND(b.gap_pp - r.eu27_gap, 2) AS vs_media_eu27_pp,
    b.pct_excluidos,
    CASE
        WHEN b.country_code = 'EU27_2020' THEN '— referencia —'
        WHEN b.gap_pp < 5               THEN 'Alta inclusión'
        WHEN b.gap_pp < 12              THEN 'Inclusión media'
        ELSE                                 'Baja inclusión'
    END                             AS grupo_inclusion
FROM brecha b CROSS JOIN ref_eu27 r
ORDER BY b.is_aggregate, b.gap_pp DESC;

-- ── Q4: Tabla pivot países × niveles de discapacidad ─────────────────────
SELECT
    c.country_name_es                                        AS pais,
    ROUND(MAX(CASE WHEN f.category_code='DIS_NONE' THEN f.pct_internet_use END), 2) AS sin_discapacidad,
    ROUND(MAX(CASE WHEN f.category_code='DIS_LTD'  THEN f.pct_internet_use END), 2) AS limit_leve,
    ROUND(MAX(CASE WHEN f.category_code='DIS_SEV'  THEN f.pct_internet_use END), 2) AS limit_severa,
    ROUND(MAX(CASE WHEN f.category_code='DIS_NONE' THEN f.pct_internet_use END) -
          MAX(CASE WHEN f.category_code='DIS_SEV'  THEN f.pct_internet_use END), 2) AS brecha_total
FROM fact_internet_use f
JOIN dim_country c ON f.country_code = c.country_code
WHERE f.category_code IN ('DIS_NONE','DIS_LTD','DIS_SEV','DIS_LTD_SEV')
GROUP BY c.country_code, c.country_name_es
ORDER BY brecha_total DESC;

-- ── Q5: ¿Cuánto le falta a España para alcanzar a los países líderes? ────
-- Nota: con España en 3ª posición (18,26 pp), la comparación relevante
-- es contra NL (1,05 pp), SE (4,72 pp) y la media UE-27 (12,93 pp).
SELECT
    c.country_name_es                                    AS pais_referencia,
    ROUND(fn.pct_internet_use, 2)                        AS pct_sin_discap_ref,
    ROUND(fs.pct_internet_use, 2)                        AS pct_severa_ref,
    ROUND(
        fs.pct_internet_use -
        (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='DIS_SEV'),
    2)                                                   AS mejora_necesaria_pp,
    ROUND(
        (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='DIS_NONE') -
        (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='DIS_SEV') -
        (fn.pct_internet_use - fs.pct_internet_use),
    2)                                                   AS reduccion_brecha_necesaria_pp
FROM dim_country c
JOIN fact_internet_use fn ON fn.country_code = c.country_code AND fn.category_code = 'DIS_NONE'
JOIN fact_internet_use fs ON fs.country_code = c.country_code AND fs.category_code = 'DIS_SEV'
WHERE c.country_code IN ('NL','SE','EU27_2020')
ORDER BY fs.pct_internet_use DESC;
-- NL → España necesita +19,37 pp | SE → +15,13 pp | EU27 → +3,01 pp