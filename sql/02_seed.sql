-- ============================================================
-- 02_seed.sql — Datos de las dimensiones
-- Proyecto: Brecha Digital y Discapacidad en España
-- Fuente  : Eurostat DSB_ICTIU01 v1.0 (2024)
--
-- EJECUTAR DESPUÉS de 01_schema.sql
-- ============================================================

-- ── dim_country (9 entidades: 8 países + agregado EU27) ──────────────────
-- CORRECCIÓN: Lituania (LT) incluida. Tiene la mayor brecha del dataset
-- (35,86 pp). España es la 2ª con mayor brecha (18,26 pp).
INSERT INTO dim_country (country_code, country_name_es, country_name_en, is_aggregate, iso2_code, region) VALUES
    ('ES',        'España',       'Spain',                                    0, 'ES', 'Sur de Europa'),
    ('EU27_2020', 'Media UE-27',  'European Union - 27 countries (2020)',     1, NULL, 'Agregado europeo'),
    ('DE',        'Alemania',     'Germany',                                  0, 'DE', 'Europa central'),
    ('FR',        'Francia',      'France',                                   0, 'FR', 'Europa occidental'),
    ('IT',        'Italia',       'Italy',                                    0, 'IT', 'Sur de Europa'),
    ('NL',        'Países Bajos', 'Netherlands',                              0, 'NL', 'Europa occidental'),
    ('PT',        'Portugal',     'Portugal',                                 0, 'PT', 'Sur de Europa'),
    ('SE',        'Suecia',       'Sweden',                                   0, 'SE', 'Europa del Norte'),
    ('LT',        'Lituania',     'Lithuania',                                0, 'LT', 'Europa del Este');

-- ── dim_disability_level ─────────────────────────────────────────────────
INSERT INTO dim_disability_level (disability_level, eurostat_code, description_en, description_es, sort_order, is_aggregate) VALUES
    ('No disability',               'DIS_NONE',    'Not limited at all',              'Sin discapacidad',             1, 0),
    ('Limited (not severely)',       'DIS_LTD',     'Limited, but not severely',       'Limitación leve',              2, 0),
    ('Severely limited',             'DIS_SEV',     'Severely limited',                'Limitación severa',            3, 0),
    ('Limited or severely limited',  'DIS_LTD_SEV', 'Limited or severely limited',     'Leve o severa (agrupada)',     4, 1);

-- ── dim_sex ───────────────────────────────────────────────────────────────
INSERT INTO dim_sex (sex, description_es, sort_order, is_total) VALUES
    ('Total',  'Total (ambos sexos)', 1, 1),
    ('Female', 'Mujeres',             2, 0),
    ('Male',   'Hombres',             3, 0);

-- ── dim_age_group ─────────────────────────────────────────────────────────
-- Nota: Y16_24_DIS_SEV tiene datos no disponibles en varios países (flag u)
INSERT INTO dim_age_group (age_group, label_es, age_min, age_max, is_total, sort_order, has_data_issues) VALUES
    ('Total', 'Total (todas las edades)', NULL, NULL, 1, 1, 0),
    ('16-24', '16 a 24 años',            16,   24,   0, 2, 1),
    ('25-54', '25 a 54 años',            25,   54,   0, 3, 0),
    ('55-74', '55 a 74 años',            55,   74,   0, 4, 0);

-- ── dim_indicator ─────────────────────────────────────────────────────────
INSERT INTO dim_indicator (indicator_code, indicator_name_en, indicator_name_es, dataset_code,
    unit_code, unit_desc_es, frequency, reference_year, source_url) VALUES (
    'I_ILT12',
    'Last internet use: in the last 12 months',
    'Último uso de Internet: en los últimos 12 meses',
    'DSB_ICTIU01',
    'PC_IND',
    'Porcentaje de individuos',
    'A', 2024,
    'https://ec.europa.eu/eurostat/databrowser/view/DSB_ICTIU01'
);

-- ── dim_individual_type (24 categorías = 4 niveles × 3 sexos × 4 edades aplanado)
INSERT INTO dim_individual_type (category_code, category_desc_en, disability_level, sex, age_group, is_core_category, has_known_data_issues) VALUES
-- Totales core (Total sexo, Total edad)
    ('DIS_NONE',    'Not limited at all',               'No disability',              'Total',  'Total', 1, 0),
    ('DIS_LTD',     'Limited, but not severely',        'Limited (not severely)',      'Total',  'Total', 1, 0),
    ('DIS_SEV',     'Severely limited',                 'Severely limited',            'Total',  'Total', 1, 0),
    ('DIS_LTD_SEV', 'Limited or severely limited',      'Limited or severely limited', 'Total',  'Total', 1, 0),
-- Por sexo (Total edad)
    ('F_DIS_NONE',    'Females - not limited',          'No disability',              'Female', 'Total', 0, 0),
    ('F_DIS_LTD',     'Females - limited not severely', 'Limited (not severely)',      'Female', 'Total', 0, 0),
    ('F_DIS_SEV',     'Females - severely limited',     'Severely limited',            'Female', 'Total', 0, 0),
    ('F_DIS_LTD_SEV', 'Females - limited or severely',  'Limited or severely limited', 'Female', 'Total', 0, 0),
    ('M_DIS_NONE',    'Males - not limited',            'No disability',              'Male',   'Total', 0, 0),
    ('M_DIS_LTD',     'Males - limited not severely',   'Limited (not severely)',      'Male',   'Total', 0, 0),
    ('M_DIS_SEV',     'Males - severely limited',       'Severely limited',            'Male',   'Total', 0, 0),
    ('M_DIS_LTD_SEV', 'Males - limited or severely',    'Limited or severely limited', 'Male',   'Total', 0, 0),
-- Por edad 16-24 (Y16_24_DIS_SEV tiene datos insuficientes)
    ('Y16_24_DIS_NONE',    'Age 16-24 - not limited',           'No disability',              'Total', '16-24', 0, 0),
    ('Y16_24_DIS_LTD',     'Age 16-24 - limited not severely',  'Limited (not severely)',      'Total', '16-24', 0, 0),
    ('Y16_24_DIS_SEV',     'Age 16-24 - severely limited',      'Severely limited',            'Total', '16-24', 0, 1),
    ('Y16_24_DIS_LTD_SEV', 'Age 16-24 - limited or severely',   'Limited or severely limited', 'Total', '16-24', 0, 0),
-- Por edad 25-54
    ('Y25_54_DIS_NONE',    'Age 25-54 - not limited',           'No disability',              'Total', '25-54', 0, 0),
    ('Y25_54_DIS_LTD',     'Age 25-54 - limited not severely',  'Limited (not severely)',      'Total', '25-54', 0, 0),
    ('Y25_54_DIS_SEV',     'Age 25-54 - severely limited',      'Severely limited',            'Total', '25-54', 0, 0),
    ('Y25_54_DIS_LTD_SEV', 'Age 25-54 - limited or severely',   'Limited or severely limited', 'Total', '25-54', 0, 0),
-- Por edad 55-74 (intersección crítica: envejecimiento + discapacidad)
    ('Y55_74_DIS_NONE',    'Age 55-74 - not limited',           'No disability',              'Total', '55-74', 0, 0),
    ('Y55_74_DIS_LTD',     'Age 55-74 - limited not severely',  'Limited (not severely)',      'Total', '55-74', 0, 0),
    ('Y55_74_DIS_SEV',     'Age 55-74 - severely limited',      'Severely limited',            'Total', '55-74', 0, 0),
    ('Y55_74_DIS_LTD_SEV', 'Age 55-74 - limited or severely',   'Limited or severely limited', 'Total', '55-74', 0, 0);

-- ── Vistas analíticas ─────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS v_full_dataset AS
SELECT f.fact_id, i.reference_year AS year,
       c.country_code, c.country_name_es, c.is_aggregate AS is_eu27_aggregate,
       f.category_code, dl.disability_level, dl.sort_order AS disability_rank,
       s.sex, ag.age_group, t.category_desc_en,
       f.pct_internet_use, f.pct_excluded,
       f.gap_vs_no_disability, f.pct_vs_eu27,
       f.quality_flag, f.is_reliable,
       t.is_core_category AS is_core_row
FROM fact_internet_use f
JOIN dim_indicator       i  ON f.indicator_code = i.indicator_code
JOIN dim_country         c  ON f.country_code   = c.country_code
JOIN dim_individual_type t  ON f.category_code  = t.category_code
JOIN dim_disability_level dl ON t.disability_level = dl.disability_level
JOIN dim_sex             s  ON t.sex = s.sex
JOIN dim_age_group       ag ON t.age_group = ag.age_group;

CREATE VIEW IF NOT EXISTS v_ranking_brecha AS
SELECT c.country_code, c.country_name_es, c.is_aggregate,
    ROUND(f_none.pct_internet_use, 2)                           AS pct_no_disability,
    ROUND(f_sev.pct_internet_use, 2)                            AS pct_severely_limited,
    ROUND(f_none.pct_internet_use - f_sev.pct_internet_use, 2) AS gap_total_pp,
    ROUND(100.0 - f_sev.pct_internet_use, 2)                   AS pct_excluded_severely,
    RANK() OVER (ORDER BY (f_none.pct_internet_use - f_sev.pct_internet_use) DESC)
                                                                AS rank_by_gap
FROM dim_country c
JOIN fact_internet_use f_none ON f_none.country_code=c.country_code AND f_none.category_code='DIS_NONE'
JOIN fact_internet_use f_sev  ON f_sev.country_code=c.country_code  AND f_sev.category_code='DIS_SEV'
WHERE f_sev.is_reliable = 1
ORDER BY gap_total_pp DESC;

CREATE VIEW IF NOT EXISTS v_doble_vulnerabilidad AS
SELECT c.country_code, c.country_name_es,
    ROUND(f_f.pct_internet_use, 2)                             AS pct_mujeres_dis_sev,
    ROUND(f_m.pct_internet_use, 2)                             AS pct_hombres_dis_sev,
    ROUND(f_m.pct_internet_use - f_f.pct_internet_use, 2)     AS brecha_genero_pp
FROM dim_country c
JOIN fact_internet_use f_f ON f_f.country_code=c.country_code AND f_f.category_code='F_DIS_SEV'
JOIN fact_internet_use f_m ON f_m.country_code=c.country_code AND f_m.category_code='M_DIS_SEV'
ORDER BY ABS(f_m.pct_internet_use - f_f.pct_internet_use) DESC;

CREATE VIEW IF NOT EXISTS v_analisis_edad AS
SELECT c.country_code, c.country_name_es,
    ROUND(f_25.pct_internet_use, 2)                            AS pct_25_54_dis_sev,
    ROUND(f_55.pct_internet_use, 2)                            AS pct_55_74_dis_sev,
    ROUND(f_25.pct_internet_use - f_55.pct_internet_use, 2)   AS efecto_envejecimiento_pp
FROM dim_country c
JOIN fact_internet_use f_25 ON f_25.country_code=c.country_code AND f_25.category_code='Y25_54_DIS_SEV'
JOIN fact_internet_use f_55 ON f_55.country_code=c.country_code AND f_55.category_code='Y55_74_DIS_SEV'
ORDER BY efecto_envejecimiento_pp DESC;

SELECT 'Dimensiones y vistas cargadas correctamente.' AS status;
SELECT 'Países disponibles: ' || GROUP_CONCAT(country_code, ', ') AS paises
FROM dim_country ORDER BY is_aggregate, country_code;
