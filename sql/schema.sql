-- ============================================================
-- schema.sql
-- ============================================================
-- Modelo relacional para el proyecto:
--   "Brecha Digital y Discapacidad en España"
--
-- Fuente de datos : Eurostat DSB_ICTIU01 v1.0 (2024)
-- Indicador       : I_ILT12 — uso de Internet en los últimos 12 meses
-- Unidad          : PC_IND  — porcentaje de individuos
-- Compatibilidad  : SQL estándar (SQLite · PostgreSQL · BigQuery*)
--
-- * En BigQuery, sustituir AUTOINCREMENT por omitirlo, y REAL por FLOAT64.
--   Las instrucciones de variante están señaladas en comentarios.
--
-- Ejecución (SQLite):
--   sqlite3 proyecto.db < sql/schema.sql
--
-- Ejecución (PostgreSQL):
--   psql -d nombre_bd -f sql/schema.sql
-- ============================================================


-- ============================================================
-- 0. LIMPIEZA PREVIA
-- Eliminar tablas en orden inverso de dependencia para evitar
-- errores de clave foránea al re-ejecutar el script.
-- ============================================================

DROP TABLE IF EXISTS fact_internet_use;
DROP TABLE IF EXISTS dim_individual_type;
DROP TABLE IF EXISTS dim_disability_level;
DROP TABLE IF EXISTS dim_sex;
DROP TABLE IF EXISTS dim_age_group;
DROP TABLE IF EXISTS dim_indicator;
DROP TABLE IF EXISTS dim_country;
DROP TABLE IF EXISTS mart_country_metrics;


-- ============================================================
-- 1. dim_country
-- ============================================================
-- Dimensión geográfica. Contiene los 8 países del proyecto
-- más el agregado EU27_2020.
-- La columna is_aggregate distingue el promedio europeo de los
-- países individuales, lo que es necesario para excluir EU27_2020
-- en análisis de clustering y rankings de países reales.
-- ============================================================

CREATE TABLE dim_country (
    -- Clave primaria: código ISO de Eurostat
    -- ES, DE, FR, IT, NL, PT, SE, EU27_2020
    country_code        TEXT        NOT NULL,

    -- Nombre oficial del país en español (para visualizaciones)
    country_name_es     TEXT        NOT NULL,

    -- Nombre oficial del país en inglés (código original Eurostat)
    country_name_en     TEXT        NOT NULL,

    -- TRUE si es el agregado EU27_2020 (no un país individual)
    -- Usar: WHERE is_aggregate = FALSE en clustering y rankings
    is_aggregate        INTEGER     NOT NULL DEFAULT 0
                            CHECK (is_aggregate IN (0, 1)),

    -- Código ISO 3166-1 alpha-2 estándar (NULL para EU27_2020)
    -- Útil para mapas coropléticos en Power BI
    iso2_code           TEXT,

    -- Región geopolítica (para agrupaciones alternativas)
    region              TEXT,

    CONSTRAINT pk_country PRIMARY KEY (country_code)
);

-- Índice para búsquedas por nombre
CREATE INDEX IF NOT EXISTS idx_country_name_es ON dim_country (country_name_es);


-- ============================================================
-- 2. dim_disability_level
-- ============================================================
-- Dimensión del nivel de limitación de actividad.
-- Descompone el eje de discapacidad del código ind_type de Eurostat.
-- Incluye un campo de ordenación (sort_order) para que los gráficos
-- puedan ordenar los niveles de menor a mayor limitación sin
-- depender del orden alfabético.
-- ============================================================

CREATE TABLE dim_disability_level (
    -- Clave primaria: nombre del nivel tal como aparece en el dataset limpio
    disability_level    TEXT        NOT NULL,

    -- Código Eurostat correspondiente (para trazabilidad al dataset original)
    -- DIS_NONE | DIS_LTD | DIS_SEV | DIS_LTD_SEV
    eurostat_code       TEXT        NOT NULL,

    -- Descripción oficial de Eurostat en inglés
    description_en      TEXT        NOT NULL,

    -- Descripción en español para informes y dashboards
    description_es      TEXT        NOT NULL,

    -- Orden lógico de menor a mayor limitación:
    --   1 = No disability (referencia)
    --   2 = Limited (not severely)
    --   3 = Severely limited  ← foco del análisis
    --   4 = Limited or severely limited (agrupado)
    sort_order          INTEGER     NOT NULL
                            CHECK (sort_order BETWEEN 1 AND 4),

    -- TRUE si es la categoría que agrupa leve + severa (DIS_LTD_SEV)
    -- Estas filas son redundantes con las filas individuales:
    -- usarlas solo cuando se necesite el indicador oficial agrupado
    is_aggregate        INTEGER     NOT NULL DEFAULT 0
                            CHECK (is_aggregate IN (0, 1)),

    CONSTRAINT pk_disability_level PRIMARY KEY (disability_level)
);


-- ============================================================
-- 3. dim_sex
-- ============================================================
-- Dimensión de sexo. Tres valores posibles:
--   Total  → sin desagregación por sexo
--   Female → mujeres
--   Male   → hombres
-- La fila Total agrupa a ambos sexos y es la referencia para
-- análisis comparativos entre países.
-- ============================================================

CREATE TABLE dim_sex (
    sex                 TEXT        NOT NULL,

    -- Descripción en español
    description_es      TEXT        NOT NULL,

    -- Orden para visualizaciones (Total primero)
    sort_order          INTEGER     NOT NULL,

    -- TRUE para la fila Total (sin desagregación)
    is_total            INTEGER     NOT NULL DEFAULT 0
                            CHECK (is_total IN (0, 1)),

    CONSTRAINT pk_sex PRIMARY KEY (sex)
);


-- ============================================================
-- 4. dim_age_group
-- ============================================================
-- Dimensión del grupo de edad.
-- Cuatro valores: Total (sin desagregación), 16-24, 25-54, 55-74.
-- La franja 16-24 con discapacidad severa tiene datos no disponibles
-- en varios países (flag u / NULL). El campo has_data_issues lo
-- señala para que las queries puedan advertir al usuario.
-- ============================================================

CREATE TABLE dim_age_group (
    age_group           TEXT        NOT NULL,

    -- Etiqueta para visualizaciones en español
    label_es            TEXT        NOT NULL,

    -- Límite inferior del rango de edad (NULL para Total)
    age_min             INTEGER,

    -- Límite superior del rango de edad (NULL para Total)
    age_max             INTEGER,

    -- TRUE para la fila Total (sin desagregación por edad)
    is_total            INTEGER     NOT NULL DEFAULT 0
                            CHECK (is_total IN (0, 1)),

    -- Orden para ejes de gráficos (Total al final o al principio)
    sort_order          INTEGER     NOT NULL,

    -- TRUE si este grupo tiene problemas de disponibilidad de datos
    -- conocidos en el dataset (16-24 × DIS_SEV tiene 4 nulos en 8 países)
    has_data_issues     INTEGER     NOT NULL DEFAULT 0
                            CHECK (has_data_issues IN (0, 1)),

    CONSTRAINT pk_age_group PRIMARY KEY (age_group)
);


-- ============================================================
-- 5. dim_individual_type
-- ============================================================
-- Dimensión de tipo de individuo. Corresponde a la columna ind_type
-- del CSV original de Eurostat (24 categorías únicas).
-- Esta tabla es el resultado de normalizar el código compuesto de
-- Eurostat: cada fila descompone el código en sus tres dimensiones
-- (disability_level, sex, age_group) y las conecta mediante FK.
-- ============================================================

CREATE TABLE dim_individual_type (
    -- Clave primaria: código original de Eurostat
    -- Ejemplos: DIS_SEV, F_DIS_SEV, Y55_74_DIS_SEV
    category_code       TEXT        NOT NULL,

    -- Descripción oficial completa en inglés (tal como la publica Eurostat)
    category_desc_en    TEXT        NOT NULL,

    -- ── Claves foráneas a las tres dimensiones descodificadas ──
    -- Permiten filtrar sin parsear el código en cada query.

    disability_level    TEXT        NOT NULL,
    sex                 TEXT        NOT NULL,
    age_group           TEXT        NOT NULL,

    -- TRUE si este tipo de individuo combina Total sex Y Total age
    -- (filas de referencia para el análisis comparativo principal)
    is_core_category    INTEGER     NOT NULL DEFAULT 0
                            CHECK (is_core_category IN (0, 1)),

    -- TRUE si datos de esta categoría tienen problemas conocidos de
    -- fiabilidad en el dataset (Y16_24_DIS_SEV tiene 4 nulos)
    has_known_data_issues INTEGER   NOT NULL DEFAULT 0
                            CHECK (has_known_data_issues IN (0, 1)),

    CONSTRAINT pk_individual_type  PRIMARY KEY (category_code),
    CONSTRAINT fk_disability_level FOREIGN KEY (disability_level)
        REFERENCES dim_disability_level (disability_level),
    CONSTRAINT fk_sex              FOREIGN KEY (sex)
        REFERENCES dim_sex (sex),
    CONSTRAINT fk_age_group        FOREIGN KEY (age_group)
        REFERENCES dim_age_group (age_group)
);

-- Índices para los filtros más frecuentes en el proyecto
CREATE INDEX IF NOT EXISTS idx_indtype_disability ON dim_individual_type (disability_level);
CREATE INDEX IF NOT EXISTS idx_indtype_sex        ON dim_individual_type (sex);
CREATE INDEX IF NOT EXISTS idx_indtype_age        ON dim_individual_type (age_group);
CREATE INDEX IF NOT EXISTS idx_indtype_core       ON dim_individual_type (is_core_category);


-- ============================================================
-- 6. dim_indicator
-- ============================================================
-- Dimensión del indicador estadístico.
-- En este proyecto existe un único indicador (I_ILT12), pero la
-- tabla permite escalar el modelo si en el futuro se añaden otros
-- indicadores del mismo dataset Eurostat (p. ej. frecuencia de uso,
-- tipo de actividad, etc.) sin modificar la tabla de hechos.
-- ============================================================

CREATE TABLE dim_indicator (
    -- Clave primaria: código Eurostat del indicador
    indicator_code      TEXT        NOT NULL,

    -- Nombre descriptivo del indicador en inglés
    indicator_name_en   TEXT        NOT NULL,

    -- Nombre en español para visualizaciones
    indicator_name_es   TEXT        NOT NULL,

    -- Código del dataset Eurostat al que pertenece el indicador
    dataset_code        TEXT        NOT NULL,

    -- Unidad de medida (código Eurostat)
    unit_code           TEXT        NOT NULL,

    -- Descripción de la unidad en español
    unit_desc_es        TEXT        NOT NULL,

    -- Frecuencia de publicación (A = Annual)
    frequency           TEXT        NOT NULL DEFAULT 'A',

    -- Año de publicación del snapshot cargado en la base de datos
    reference_year      INTEGER     NOT NULL,

    -- URL de la fuente oficial
    source_url          TEXT,

    CONSTRAINT pk_indicator PRIMARY KEY (indicator_code)
);


-- ============================================================
-- 7. fact_internet_use  ← TABLA DE HECHOS PRINCIPAL
-- ============================================================
-- Una fila por combinación (indicador × país × tipo_individuo).
-- Con un único indicador y 8 países × 24 categorías → 192 filas.
-- Cada fila representa el porcentaje de individuos de ese perfil
-- (país + tipo) que usaron Internet en los últimos 12 meses.
--
-- Modelo estrella: esta tabla apunta a todas las dimensiones.
-- Las consultas analíticas se construyen con JOINs a las dim_*.
-- ============================================================

CREATE TABLE fact_internet_use (
    -- Clave primaria surrogate (entero autoincremental)
    -- En PostgreSQL: usar SERIAL o GENERATED ALWAYS AS IDENTITY
    -- En BigQuery: omitir esta columna y usar una clave compuesta
    fact_id             INTEGER     PRIMARY KEY AUTOINCREMENT,

    -- ── Claves foráneas a las dimensiones ─────────────────────
    indicator_code      TEXT        NOT NULL,
    country_code        TEXT        NOT NULL,
    category_code       TEXT        NOT NULL,

    -- ── Medida principal ──────────────────────────────────────
    -- Porcentaje de individuos del perfil que usaron Internet
    -- en los últimos 12 meses. Escala: 0.00 – 100.00.
    -- NULL en 4 observaciones (Y16_24_DIS_SEV: ES, FR, NL, SE)
    pct_internet_use    REAL        CHECK (
                            pct_internet_use IS NULL
                            OR (pct_internet_use >= 0.0 AND pct_internet_use <= 100.0)
                        ),

    -- ── Medidas derivadas ─────────────────────────────────────
    -- Se almacenan desnormalizadas aquí para eficiencia de lectura
    -- desde Power BI y queries SQL complejas sin subqueries.

    -- Porcentaje de personas que NO usan Internet (exclusión digital)
    -- 100 - pct_internet_use. NULL si pct_internet_use es NULL.
    pct_excluded        REAL        CHECK (
                            pct_excluded IS NULL
                            OR (pct_excluded >= 0.0 AND pct_excluded <= 100.0)
                        ),

    -- Brecha respecto al grupo sin discapacidad del mismo país/sexo/edad.
    -- pct_no_disability[mismo país/sexo/edad] - pct_internet_use.
    -- 0.0 para filas de No disability. NULL si faltan datos de referencia.
    gap_vs_no_disability REAL,

    -- Diferencia respecto al valor equivalente de la media EU27_2020.
    -- pct_internet_use - pct_eu27_equivalent[mismo disability/sexo/edad].
    -- 0.0 para las filas de EU27_2020.
    pct_vs_eu27         REAL,

    -- ── Metadatos de calidad estadística ─────────────────────
    -- Flag original de Eurostat: NULL = sin problema, 'u' = baja fiabilidad
    quality_flag        TEXT        CHECK (quality_flag IS NULL OR quality_flag = 'u'),

    -- Indicador booleano de fiabilidad (0/1)
    -- 0 si quality_flag = 'u' O si pct_internet_use es NULL
    -- 1 en todos los demás casos
    is_reliable         INTEGER     NOT NULL DEFAULT 1
                            CHECK (is_reliable IN (0, 1)),

    -- ── Claves foráneas ───────────────────────────────────────
    CONSTRAINT fk_fact_indicator FOREIGN KEY (indicator_code)
        REFERENCES dim_indicator    (indicator_code),
    CONSTRAINT fk_fact_country   FOREIGN KEY (country_code)
        REFERENCES dim_country      (country_code),
    CONSTRAINT fk_fact_category  FOREIGN KEY (category_code)
        REFERENCES dim_individual_type (category_code),

    -- Unicidad: no puede haber dos filas con la misma combinación
    CONSTRAINT uq_fact_observation UNIQUE (indicator_code, country_code, category_code)
);

-- Índices para las queries analíticas más frecuentes del proyecto
CREATE INDEX IF NOT EXISTS idx_fact_country   ON fact_internet_use (country_code);
CREATE INDEX IF NOT EXISTS idx_fact_category  ON fact_internet_use (category_code);
CREATE INDEX IF NOT EXISTS idx_fact_reliable  ON fact_internet_use (is_reliable);


-- ============================================================
-- 8. mart_country_metrics  ← DATA MART DE PAÍS
-- ============================================================
-- Tabla resumen con una fila por país. No es una tabla de hechos
-- transaccional, sino un mart precalculado con las métricas
-- derivadas necesarias para Power BI y el análisis de clustering.
-- Equivale al archivo summary_by_country.csv generado por Python.
--
-- Ventaja: Power BI puede conectarse directamente a esta tabla
-- sin necesidad de medidas DAX complejas para las KPI cards.
-- ============================================================

CREATE TABLE mart_country_metrics (
    -- Un registro por país (clave foránea a dim_country)
    country_code                TEXT        NOT NULL,

    -- ── Porcentajes base (Total sexo, Total edad) ──────────────
    pct_no_disability           REAL,   -- % uso, sin discapacidad
    pct_severely_limited        REAL,   -- % uso, discapacidad severa ← central
    pct_limited_not_severely    REAL,   -- % uso, limitación leve
    pct_limited_or_severely     REAL,   -- % uso, leve o severa (agrupado)

    -- ── Desagregación por sexo (Total edad, discapacidad severa) ─
    pct_female_severely         REAL,   -- % uso, mujeres, discapacidad severa
    pct_male_severely           REAL,   -- % uso, hombres, discapacidad severa

    -- ── Desagregación por edad (Total sexo, discapacidad severa) ─
    pct_25_54_severely          REAL,   -- % uso, 25-54 años, discapacidad severa
    pct_55_74_severely          REAL,   -- % uso, 55-74 años (intersección crítica)

    -- ── Métricas de brecha ─────────────────────────────────────
    -- Brecha principal: No disability - Severely limited (Total/Total)
    gap_total                   REAL,

    -- Brecha de género dentro de discapacidad severa: Male - Female
    -- Positivo → hombres usan más. Negativo → mujeres usan más.
    gap_gender                  REAL,

    -- Efecto del envejecimiento: pct_25_54 - pct_55_74 (discapacidad severa)
    gap_age                     REAL,

    -- Diferencia de brecha vs. media UE-27: gap_total - 12.93
    -- Positivo → mayor brecha que la media europea
    gap_vs_eu27                 REAL,

    -- Porcentaje de personas con discapacidad severa excluidas digitalmente
    pct_excluded_severely       REAL,

    -- ── Clasificación analítica ────────────────────────────────
    -- Grupo de inclusión basado en gap_total:
    --   Alta inclusión    → gap < 5 pp   (NL, SE)
    --   Inclusión media   → gap 5-12 pp  (DE, FR, PT)
    --   Baja inclusión    → gap 12-20 pp (ES, IT)
    --   Muy baja inclusión → gap > 20 pp
    inclusion_group             TEXT,

    -- Posición en el ranking de brecha (1 = mayor brecha = peor posición)
    -- NULL para EU27_2020 (agregado, no compite en el ranking)
    country_rank_by_gap         INTEGER,

    -- TRUE si es el agregado EU27_2020
    is_eu27_aggregate           INTEGER     NOT NULL DEFAULT 0
                                    CHECK (is_eu27_aggregate IN (0, 1)),

    CONSTRAINT pk_mart_country  PRIMARY KEY (country_code),
    CONSTRAINT fk_mart_country  FOREIGN KEY (country_code)
        REFERENCES dim_country (country_code)
);


-- ============================================================
-- 9. DATOS DE LAS DIMENSIONES
-- ============================================================


-- ── 9.1  dim_country ─────────────────────────────────────────
INSERT INTO dim_country (country_code, country_name_es, country_name_en, is_aggregate, iso2_code, region) VALUES
    ('ES',        'España',        'Spain',                                          0, 'ES', 'Sur de Europa'),
    ('EU27_2020', 'Media UE-27',   'European Union - 27 countries (from 2020)',      1,  NULL, 'Agregado europeo'),
    ('DE',        'Alemania',      'Germany',                                        0, 'DE', 'Europa central'),
    ('FR',        'Francia',       'France',                                         0, 'FR', 'Europa occidental'),
    ('IT',        'Italia',        'Italy',                                          0, 'IT', 'Sur de Europa'),
    ('NL',        'Países Bajos',  'Netherlands',                                    0, 'NL', 'Europa occidental'),
    ('PT',        'Portugal',      'Portugal',                                       0, 'PT', 'Sur de Europa'),
    ('SE',        'Suecia',        'Sweden',                                         0, 'SE', 'Europa del Norte');


-- ── 9.2  dim_disability_level ────────────────────────────────
INSERT INTO dim_disability_level
    (disability_level, eurostat_code, description_en, description_es, sort_order, is_aggregate)
VALUES
    ('No disability',
     'DIS_NONE',
     'Disability (activity limitation) - not limited at all',
     'Sin discapacidad (sin limitación de actividad)',
     1, 0),

    ('Limited (not severely)',
     'DIS_LTD',
     'Disability (activity limitation) - limited, but not severely',
     'Limitación leve (limitada, pero no severamente)',
     2, 0),

    ('Severely limited',
     'DIS_SEV',
     'Disability (activity limitation) - severely limited',
     'Limitación severa (severamente limitada)',
     3, 0),

    ('Limited or severely limited',
     'DIS_LTD_SEV',
     'Disability (activity limitation) - limited or severely limited',
     'Limitación leve o severa (categoría agrupada)',
     4, 1);


-- ── 9.3  dim_sex ─────────────────────────────────────────────
INSERT INTO dim_sex (sex, description_es, sort_order, is_total) VALUES
    ('Total',  'Total (ambos sexos)',  1, 1),
    ('Female', 'Mujeres',             2, 0),
    ('Male',   'Hombres',             3, 0);


-- ── 9.4  dim_age_group ───────────────────────────────────────
INSERT INTO dim_age_group
    (age_group, label_es, age_min, age_max, is_total, sort_order, has_data_issues)
VALUES
    ('Total', 'Total (todas las edades)', NULL, NULL, 1, 1, 0),
    ('16-24', '16 a 24 años',            16,   24,   0, 2, 1),  -- has_data_issues: Y16_24_DIS_SEV tiene 4 nulos
    ('25-54', '25 a 54 años',            25,   54,   0, 3, 0),
    ('55-74', '55 a 74 años',            55,   74,   0, 4, 0);


-- ── 9.5  dim_individual_type (24 categorías) ─────────────────
INSERT INTO dim_individual_type
    (category_code, category_desc_en, disability_level, sex, age_group,
     is_core_category, has_known_data_issues)
VALUES
-- Totales (Total sexo, Total edad) — 4 filas — categorías core
    ('DIS_NONE',    'Disability (activity limitation) - not limited at all',           'No disability',                  'Total',  'Total', 1, 0),
    ('DIS_LTD',     'Disability (activity limitation) - limited, but not severely',    'Limited (not severely)',          'Total',  'Total', 1, 0),
    ('DIS_SEV',     'Disability (activity limitation) - severely limited',              'Severely limited',               'Total',  'Total', 1, 0),
    ('DIS_LTD_SEV', 'Disability (activity limitation) - limited or severely limited',  'Limited or severely limited',    'Total',  'Total', 1, 0),
-- Desagregación por sexo femenino — 4 filas
    ('F_DIS_NONE',    'Females with disability (activity limitation) - not limited at all',          'No disability',               'Female', 'Total', 0, 0),
    ('F_DIS_LTD',     'Females with disability (activity limitation) - limited, but not severely',   'Limited (not severely)',       'Female', 'Total', 0, 0),
    ('F_DIS_SEV',     'Females with disability (activity limitation) - severely limited',             'Severely limited',            'Female', 'Total', 0, 0),
    ('F_DIS_LTD_SEV', 'Females with disability (activity limitation) - limited or severely limited', 'Limited or severely limited', 'Female', 'Total', 0, 0),
-- Desagregación por sexo masculino — 4 filas
    ('M_DIS_NONE',    'Males with disability (activity limitation) - not limited at all',          'No disability',               'Male',   'Total', 0, 0),
    ('M_DIS_LTD',     'Males with disability (activity limitation) - limited, but not severely',   'Limited (not severely)',       'Male',   'Total', 0, 0),
    ('M_DIS_SEV',     'Males with disability (activity limitation) - severely limited',             'Severely limited',            'Male',   'Total', 0, 0),
    ('M_DIS_LTD_SEV', 'Males with disability (activity limitation) - limited or severely limited', 'Limited or severely limited', 'Male',   'Total', 0, 0),
-- Desagregación por edad 16-24 — 4 filas (Y16_24_DIS_SEV con datos insuficientes)
    ('Y16_24_DIS_NONE',    'Individuals aged 16 to 24 with disability (activity limitation) - not limited at all',          'No disability',               'Total', '16-24', 0, 0),
    ('Y16_24_DIS_LTD',     'Individuals aged 16 to 24 with disability (activity limitation) - limited, but not severely',   'Limited (not severely)',       'Total', '16-24', 0, 0),
    ('Y16_24_DIS_SEV',     'Individuals aged 16 to 24 with disability (activity limitation) - severely limited',             'Severely limited',            'Total', '16-24', 0, 1),
    ('Y16_24_DIS_LTD_SEV', 'Individuals aged 16 to 24 with disability (activity limitation) - limited or severely limited', 'Limited or severely limited', 'Total', '16-24', 0, 0),
-- Desagregación por edad 25-54 — 4 filas
    ('Y25_54_DIS_NONE',    'Individuals aged 25 to 54 with disability (activity limitation) - not limited at all',          'No disability',               'Total', '25-54', 0, 0),
    ('Y25_54_DIS_LTD',     'Individuals aged 25 to 54 with disability (activity limitation) - limited, but not severely',   'Limited (not severely)',       'Total', '25-54', 0, 0),
    ('Y25_54_DIS_SEV',     'Individuals aged 25 to 54 with disability (activity limitation) - severely limited',             'Severely limited',            'Total', '25-54', 0, 0),
    ('Y25_54_DIS_LTD_SEV', 'Individuals aged 25 to 54 with disability (activity limitation) - limited or severely limited', 'Limited or severely limited', 'Total', '25-54', 0, 0),
-- Desagregación por edad 55-74 — 4 filas
    ('Y55_74_DIS_NONE',    'Individuals aged 55 to 74 with disability (activity limitation) - not limited at all',          'No disability',               'Total', '55-74', 0, 0),
    ('Y55_74_DIS_LTD',     'Individuals aged 55 to 74 with disability (activity limitation) - limited, but not severely',   'Limited (not severely)',       'Total', '55-74', 0, 0),
    ('Y55_74_DIS_SEV',     'Individuals aged 55 to 74 with disability (activity limitation) - severely limited',             'Severely limited',            'Total', '55-74', 0, 0),
    ('Y55_74_DIS_LTD_SEV', 'Individuals aged 55 to 74 with disability (activity limitation) - limited or severely limited', 'Limited or severely limited', 'Total', '55-74', 0, 0);


-- ── 9.6  dim_indicator ───────────────────────────────────────
INSERT INTO dim_indicator
    (indicator_code, indicator_name_en, indicator_name_es, dataset_code,
     unit_code, unit_desc_es, frequency, reference_year, source_url)
VALUES (
    'I_ILT12',
    'Last internet use: in the last 12 months',
    'Último uso de Internet: en los últimos 12 meses',
    'DSB_ICTIU01',
    'PC_IND',
    'Porcentaje de individuos',
    'A',
    2024,
    'https://ec.europa.eu/eurostat/databrowser/view/DSB_ICTIU01'
);


-- ============================================================
-- 10. VISTAS ANALÍTICAS
-- ============================================================
-- Las vistas traducen el modelo relacional normalizado a formatos
-- planos listos para queries de análisis y conexión con Power BI.
-- No almacenan datos: son consultas predefinidas reutilizables.
-- ============================================================


-- ── Vista 1: Tabla plana completa (equivalente al CSV analítico) ──
CREATE VIEW IF NOT EXISTS v_full_dataset AS
SELECT
    f.fact_id,
    -- Dimensión indicador
    i.indicator_code,
    i.reference_year                            AS year,
    -- Dimensión país
    c.country_code,
    c.country_name_es,
    c.country_name_en,
    c.is_aggregate                              AS is_eu27_aggregate,
    -- Dimensión tipo de individuo
    f.category_code,
    dl.disability_level,
    dl.sort_order                               AS disability_rank,
    s.sex,
    ag.age_group,
    t.category_desc_en,
    -- Medidas principales
    f.pct_internet_use,
    f.pct_excluded,
    f.gap_vs_no_disability,
    f.pct_vs_eu27,
    -- Calidad
    f.quality_flag,
    f.is_reliable,
    -- Flags de contexto
    t.is_core_category                          AS is_core_row
FROM fact_internet_use      f
JOIN dim_indicator          i  ON f.indicator_code = i.indicator_code
JOIN dim_country            c  ON f.country_code   = c.country_code
JOIN dim_individual_type    t  ON f.category_code  = t.category_code
JOIN dim_disability_level   dl ON t.disability_level = dl.disability_level
JOIN dim_sex                s  ON t.sex            = s.sex
JOIN dim_age_group          ag ON t.age_group      = ag.age_group;


-- ── Vista 2: Ranking de países por brecha (responde a P1) ────────
CREATE VIEW IF NOT EXISTS v_ranking_brecha AS
SELECT
    c.country_code,
    c.country_name_es,
    c.is_aggregate                          AS is_eu27_aggregate,
    ROUND(f_none.pct_internet_use, 2)       AS pct_no_disability,
    ROUND(f_sev.pct_internet_use, 2)        AS pct_severely_limited,
    ROUND(
        f_none.pct_internet_use - f_sev.pct_internet_use,
    2)                                      AS gap_total_pp,
    ROUND(
        100.0 - f_sev.pct_internet_use,
    2)                                      AS pct_excluded_severely,
    RANK() OVER (
        ORDER BY (f_none.pct_internet_use - f_sev.pct_internet_use) DESC
    )                                       AS rank_by_gap
FROM dim_country c
-- Sin discapacidad (referencia)
JOIN fact_internet_use f_none
    ON  f_none.country_code   = c.country_code
    AND f_none.category_code  = 'DIS_NONE'
-- Discapacidad severa (indicador clave)
JOIN fact_internet_use f_sev
    ON  f_sev.country_code    = c.country_code
    AND f_sev.category_code   = 'DIS_SEV'
WHERE f_sev.is_reliable = 1
ORDER BY gap_total_pp DESC;


-- ── Vista 3: Doble vulnerabilidad género × discapacidad (P2) ─────
CREATE VIEW IF NOT EXISTS v_doble_vulnerabilidad AS
SELECT
    c.country_code,
    c.country_name_es,
    ROUND(f_f.pct_internet_use, 2)          AS pct_mujeres_dis_sev,
    ROUND(f_m.pct_internet_use, 2)          AS pct_hombres_dis_sev,
    ROUND(f_m.pct_internet_use - f_f.pct_internet_use, 2) AS brecha_genero_pp,
    CASE
        WHEN (f_m.pct_internet_use - f_f.pct_internet_use) > 0
        THEN 'Hombres usan más'
        WHEN (f_m.pct_internet_use - f_f.pct_internet_use) < 0
        THEN 'Mujeres usan más'
        ELSE 'Sin diferencia'
    END                                     AS direccion_brecha
FROM dim_country c
JOIN fact_internet_use f_f
    ON  f_f.country_code  = c.country_code
    AND f_f.category_code = 'F_DIS_SEV'
JOIN fact_internet_use f_m
    ON  f_m.country_code  = c.country_code
    AND f_m.category_code = 'M_DIS_SEV'
ORDER BY ABS(f_m.pct_internet_use - f_f.pct_internet_use) DESC;


-- ── Vista 4: Análisis por edad — efecto del envejecimiento (P3) ──
CREATE VIEW IF NOT EXISTS v_analisis_edad AS
SELECT
    c.country_code,
    c.country_name_es,
    ROUND(f_25.pct_internet_use, 2)         AS pct_25_54_dis_sev,
    ROUND(f_55.pct_internet_use, 2)         AS pct_55_74_dis_sev,
    ROUND(f_25.pct_internet_use - f_55.pct_internet_use, 2) AS efecto_envejecimiento_pp,
    f_25.is_reliable                        AS fiable_25_54,
    f_55.is_reliable                        AS fiable_55_74
FROM dim_country c
JOIN fact_internet_use f_25
    ON  f_25.country_code  = c.country_code
    AND f_25.category_code = 'Y25_54_DIS_SEV'
JOIN fact_internet_use f_55
    ON  f_55.country_code  = c.country_code
    AND f_55.category_code = 'Y55_74_DIS_SEV'
ORDER BY efecto_envejecimiento_pp DESC;


-- ── Vista 5: KPIs de España vs. UE-27 (para tarjetas Power BI) ───
CREATE VIEW IF NOT EXISTS v_kpis_espana AS
SELECT
    'Brecha total España (pp)'              AS kpi,
    ROUND(
        (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES'        AND category_code='DIS_NONE') -
        (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES'        AND category_code='DIS_SEV'),
    2)                                      AS valor_espana,
    ROUND(
        (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='EU27_2020' AND category_code='DIS_NONE') -
        (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='EU27_2020' AND category_code='DIS_SEV'),
    2)                                      AS referencia_eu27
UNION ALL
SELECT
    '% mujeres con discapacidad severa',
    (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='F_DIS_SEV'),
    (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='EU27_2020' AND category_code='F_DIS_SEV')
UNION ALL
SELECT
    '% grupo 55-74 con discapacidad severa',
    (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='Y55_74_DIS_SEV'),
    (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='EU27_2020' AND category_code='Y55_74_DIS_SEV')
UNION ALL
SELECT
    '% excluidos digitalmente (discap. severa)',
    ROUND(100.0 - (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='ES' AND category_code='DIS_SEV'), 2),
    ROUND(100.0 - (SELECT pct_internet_use FROM fact_internet_use WHERE country_code='EU27_2020' AND category_code='DIS_SEV'), 2);


-- ============================================================
-- 11. VERIFICACIÓN DEL SCHEMA
-- ============================================================

SELECT '=== TABLAS CREADAS ===' AS info;
SELECT name AS tabla FROM sqlite_master WHERE type='table' ORDER BY name;

SELECT '=== VISTAS CREADAS ===' AS info;
SELECT name AS vista FROM sqlite_master WHERE type='view'  ORDER BY name;

SELECT '=== DIMENSIONES CARGADAS ===' AS info;
SELECT 'dim_country'          AS tabla, COUNT(*) AS filas FROM dim_country
UNION ALL
SELECT 'dim_disability_level',          COUNT(*) FROM dim_disability_level
UNION ALL
SELECT 'dim_sex',                        COUNT(*) FROM dim_sex
UNION ALL
SELECT 'dim_age_group',                  COUNT(*) FROM dim_age_group
UNION ALL
SELECT 'dim_individual_type',            COUNT(*) FROM dim_individual_type
UNION ALL
SELECT 'dim_indicator',                  COUNT(*) FROM dim_indicator;

SELECT '=== SCHEMA COMPLETADO ===' AS info;
SELECT 'fact_internet_use (vacía, pendiente de carga con load_data.sql)' AS siguiente_paso;
