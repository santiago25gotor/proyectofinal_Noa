-- ============================================================
-- 01_schema.sql — Definición de tablas e índices
-- Proyecto: Brecha Digital y Discapacidad en España
-- Fuente  : Eurostat DSB_ICTIU01 v1.0 (2024)
--
-- Ejecución (SQLite):
--   sqlite3 proyecto.db < sql/01_schema.sql
--
-- IMPORTANTE: ejecutar en orden:
--   01_schema.sql → 02_seed.sql → python sql_loader.py → analysis_queries.sql
-- ============================================================

-- Limpieza previa (orden inverso de dependencias)
DROP TABLE IF EXISTS fact_internet_use;
DROP TABLE IF EXISTS mart_country_metrics;
DROP TABLE IF EXISTS dim_individual_type;
DROP TABLE IF EXISTS dim_disability_level;
DROP TABLE IF EXISTS dim_sex;
DROP TABLE IF EXISTS dim_age_group;
DROP TABLE IF EXISTS dim_indicator;
DROP TABLE IF EXISTS dim_country;
DROP VIEW  IF EXISTS v_full_dataset;
DROP VIEW  IF EXISTS v_ranking_brecha;
DROP VIEW  IF EXISTS v_doble_vulnerabilidad;
DROP VIEW  IF EXISTS v_analisis_edad;
DROP VIEW  IF EXISTS v_kpis_espana;

-- ── dim_country ───────────────────────────────────────────────────────────
CREATE TABLE dim_country (
    country_code    TEXT    NOT NULL,
    country_name_es TEXT    NOT NULL,
    country_name_en TEXT    NOT NULL,
    is_aggregate    INTEGER NOT NULL DEFAULT 0 CHECK (is_aggregate IN (0,1)),
    iso2_code       TEXT,
    region          TEXT,
    CONSTRAINT pk_country PRIMARY KEY (country_code)
);

-- ── dim_disability_level ─────────────────────────────────────────────────
CREATE TABLE dim_disability_level (
    disability_level TEXT    NOT NULL,
    eurostat_code    TEXT    NOT NULL,
    description_en   TEXT    NOT NULL,
    description_es   TEXT    NOT NULL,
    sort_order       INTEGER NOT NULL CHECK (sort_order BETWEEN 1 AND 4),
    is_aggregate     INTEGER NOT NULL DEFAULT 0 CHECK (is_aggregate IN (0,1)),
    CONSTRAINT pk_disability_level PRIMARY KEY (disability_level)
);

-- ── dim_sex ───────────────────────────────────────────────────────────────
CREATE TABLE dim_sex (
    sex            TEXT    NOT NULL,
    description_es TEXT    NOT NULL,
    sort_order     INTEGER NOT NULL,
    is_total       INTEGER NOT NULL DEFAULT 0 CHECK (is_total IN (0,1)),
    CONSTRAINT pk_sex PRIMARY KEY (sex)
);

-- ── dim_age_group ─────────────────────────────────────────────────────────
CREATE TABLE dim_age_group (
    age_group       TEXT    NOT NULL,
    label_es        TEXT    NOT NULL,
    age_min         INTEGER,
    age_max         INTEGER,
    is_total        INTEGER NOT NULL DEFAULT 0 CHECK (is_total IN (0,1)),
    sort_order      INTEGER NOT NULL,
    has_data_issues INTEGER NOT NULL DEFAULT 0 CHECK (has_data_issues IN (0,1)),
    CONSTRAINT pk_age_group PRIMARY KEY (age_group)
);

-- ── dim_individual_type (24 categorías) ───────────────────────────────────
CREATE TABLE dim_individual_type (
    category_code         TEXT NOT NULL,
    category_desc_en      TEXT NOT NULL,
    disability_level      TEXT NOT NULL,
    sex                   TEXT NOT NULL,
    age_group             TEXT NOT NULL,
    is_core_category      INTEGER NOT NULL DEFAULT 0 CHECK (is_core_category IN (0,1)),
    has_known_data_issues INTEGER NOT NULL DEFAULT 0 CHECK (has_known_data_issues IN (0,1)),
    CONSTRAINT pk_individual_type  PRIMARY KEY (category_code),
    CONSTRAINT fk_disability_level FOREIGN KEY (disability_level)
        REFERENCES dim_disability_level (disability_level),
    CONSTRAINT fk_sex              FOREIGN KEY (sex) REFERENCES dim_sex (sex),
    CONSTRAINT fk_age_group        FOREIGN KEY (age_group) REFERENCES dim_age_group (age_group)
);

CREATE INDEX IF NOT EXISTS idx_indtype_disability ON dim_individual_type (disability_level);
CREATE INDEX IF NOT EXISTS idx_indtype_sex        ON dim_individual_type (sex);
CREATE INDEX IF NOT EXISTS idx_indtype_age        ON dim_individual_type (age_group);
CREATE INDEX IF NOT EXISTS idx_indtype_core       ON dim_individual_type (is_core_category);

-- ── dim_indicator ─────────────────────────────────────────────────────────
CREATE TABLE dim_indicator (
    indicator_code    TEXT    NOT NULL,
    indicator_name_en TEXT    NOT NULL,
    indicator_name_es TEXT    NOT NULL,
    dataset_code      TEXT    NOT NULL,
    unit_code         TEXT    NOT NULL,
    unit_desc_es      TEXT    NOT NULL,
    frequency         TEXT    NOT NULL DEFAULT 'A',
    reference_year    INTEGER NOT NULL,
    source_url        TEXT,
    CONSTRAINT pk_indicator PRIMARY KEY (indicator_code)
);

-- ── fact_internet_use (tabla de hechos) ───────────────────────────────────
CREATE TABLE fact_internet_use (
    fact_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_code       TEXT    NOT NULL,
    country_code         TEXT    NOT NULL,
    category_code        TEXT    NOT NULL,
    pct_internet_use     REAL    CHECK (pct_internet_use IS NULL
                                 OR (pct_internet_use >= 0 AND pct_internet_use <= 100)),
    pct_excluded         REAL,
    gap_vs_no_disability REAL,
    pct_vs_eu27          REAL,
    quality_flag         TEXT    CHECK (quality_flag IS NULL OR quality_flag = 'u'),
    is_reliable          INTEGER NOT NULL DEFAULT 1 CHECK (is_reliable IN (0,1)),
    CONSTRAINT fk_fact_indicator FOREIGN KEY (indicator_code)
        REFERENCES dim_indicator (indicator_code),
    CONSTRAINT fk_fact_country   FOREIGN KEY (country_code)
        REFERENCES dim_country (country_code),
    CONSTRAINT fk_fact_category  FOREIGN KEY (category_code)
        REFERENCES dim_individual_type (category_code),
    CONSTRAINT uq_fact_observation UNIQUE (indicator_code, country_code, category_code)
);

CREATE INDEX IF NOT EXISTS idx_fact_country  ON fact_internet_use (country_code);
CREATE INDEX IF NOT EXISTS idx_fact_category ON fact_internet_use (category_code);
CREATE INDEX IF NOT EXISTS idx_fact_reliable ON fact_internet_use (is_reliable);

-- ── mart_country_metrics (data mart por país) ─────────────────────────────
CREATE TABLE mart_country_metrics (
    country_code             TEXT    NOT NULL,
    pct_no_disability        REAL,
    pct_severely_limited     REAL,
    pct_limited_not_severely REAL,
    pct_limited_or_severely  REAL,
    pct_female_severely      REAL,
    pct_male_severely        REAL,
    pct_25_54_severely       REAL,
    pct_55_74_severely       REAL,
    gap_total                REAL,
    gap_gender               REAL,
    gap_age                  REAL,
    gap_vs_eu27              REAL,
    pct_excluded_severely    REAL,
    inclusion_group          TEXT,
    country_rank_by_gap      INTEGER,
    is_eu27_aggregate        INTEGER NOT NULL DEFAULT 0 CHECK (is_eu27_aggregate IN (0,1)),
    CONSTRAINT pk_mart_country  PRIMARY KEY (country_code),
    CONSTRAINT fk_mart_country  FOREIGN KEY (country_code)
        REFERENCES dim_country (country_code)
);

SELECT 'Tablas creadas correctamente.' AS status;
