-- ============================================================
-- NJ Pharma Supply Chain ESG — Risk & Opportunity Analytics
-- SQL Schema · Lunarix Technologies LLC · Yiduo Xiao
-- Compatible with: PostgreSQL, SQLite
-- ============================================================

-- 1. COMPANY MASTER (6 NJ-HQ pharma manufacturers)
CREATE TABLE company (
    ticker          TEXT PRIMARY KEY,           -- 'JNJ', 'MRK', 'BMY', 'BAYN', 'SNY', 'BDX'
    name            TEXT NOT NULL,
    hq_city         TEXT,
    hq_state        TEXT,
    naics_code      TEXT,                        -- 3254 pharma preparation
    sbti_validated  INTEGER DEFAULT 0,           -- 1 = SBTi 1.5°C target validated
    revenue_usd_bn  REAL,                        -- most recent annual
    employees       INTEGER,
    public_listed   INTEGER DEFAULT 1
);

-- 2. ANNUAL ESG PILLAR SCORES (E/S/G + composite)
CREATE TABLE pillar_score (
    score_id        INTEGER PRIMARY KEY,
    ticker          TEXT REFERENCES company(ticker),
    reporting_year  INTEGER NOT NULL,
    pillar_e        REAL,                        -- environment (0-100)
    pillar_s        REAL,                        -- social
    pillar_g        REAL,                        -- governance
    composite       REAL,                        -- SASB pharma weighted: 0.40·E + 0.35·S + 0.25·G
    source          TEXT,                        -- 'MSCI ESG' | 'CDP' | 'Synthesized'
    assurance       TEXT                         -- 'Third-party' | 'Management estimate' | 'Synthesized'
);

-- 3. SCOPE 1/2/3 EMISSIONS (5-year trajectory)
CREATE TABLE scope_emissions (
    em_id           INTEGER PRIMARY KEY,
    ticker          TEXT REFERENCES company(ticker),
    reporting_year  INTEGER NOT NULL,
    scope           INTEGER NOT NULL,            -- 1, 2, or 3
    co2e_mt_million REAL NOT NULL,               -- million metric tons CO2e
    source_disclosure TEXT,
    third_party_verified INTEGER DEFAULT 0
);

-- 4. SUPPLIER COMPLIANCE (PSCI audit pass rate trend)
CREATE TABLE supplier_audit (
    audit_id        INTEGER PRIMARY KEY,
    ticker          TEXT REFERENCES company(ticker),
    reporting_year  INTEGER NOT NULL,
    pass_rate_pct   REAL,                        -- PSCI audit pass rate %
    suppliers_total INTEGER,
    suppliers_flagged_high_risk INTEGER,
    suppliers_remediated INTEGER
);

-- 5. RISK MATRIX (TCFD-aligned 5×5 likelihood × impact)
-- One row per (stage, risk_type) tuple per company per year
CREATE TABLE risk_matrix (
    risk_id         INTEGER PRIMARY KEY,
    ticker          TEXT REFERENCES company(ticker),
    reporting_year  INTEGER NOT NULL,
    stage           TEXT NOT NULL,               -- 'Raw Material Sourcing' | 'API Manufacturing' | ...
    risk_type       TEXT NOT NULL,               -- 'env' | 'carbon' | 'social' | 'gov' | 'op'
    likelihood      INTEGER,                     -- 1-5
    impact          INTEGER,                     -- 1-5
    inherent_score  INTEGER GENERATED ALWAYS AS (likelihood * impact) STORED,
    residual_score  INTEGER,                     -- after controls
    narrative       TEXT
);

-- 6. TCFD-ALIGNED OPPORTUNITY REGISTER (paired with material risks)
CREATE TABLE opportunity (
    opp_id          INTEGER PRIMARY KEY,
    ticker          TEXT REFERENCES company(ticker),
    risk_id         INTEGER REFERENCES risk_matrix(risk_id),
    opp_name        TEXT NOT NULL,
    impact_class    TEXT,                        -- 'High' | 'Medium' | 'Low'
    quantified_value_usd_m REAL,                 -- if quantifiable
    quantified_pct_reduction REAL,
    framework_alignment TEXT,                    -- 'TCFD' | 'SASB' | 'SBTi'
    recommended_action TEXT,
    owner_function  TEXT
);

-- 7. SASB PHARMA MATERIALITY WEIGHTS (reference table)
CREATE TABLE sasb_weights (
    pillar          TEXT PRIMARY KEY,
    weight          REAL NOT NULL,
    rationale       TEXT
);
INSERT INTO sasb_weights VALUES
    ('E', 0.40, 'Environmental — high materiality for pharma due to API energy intensity'),
    ('S', 0.35, 'Social — drug safety, access to medicines, employee health & safety'),
    ('G', 0.25, 'Governance — clinical trial ethics, anti-corruption, supply chain controls');

-- ============================================================
-- ANALYTICAL VIEWS
-- ============================================================

CREATE VIEW v_latest_composite AS
SELECT c.name, c.hq_city, ps.composite, ps.reporting_year
FROM company c
JOIN pillar_score ps ON c.ticker = ps.ticker
WHERE ps.reporting_year = (SELECT MAX(reporting_year) FROM pillar_score);

CREATE VIEW v_scope3_share AS
SELECT
    ticker,
    reporting_year,
    SUM(CASE WHEN scope = 3 THEN co2e_mt_million ELSE 0 END) AS scope3,
    SUM(co2e_mt_million) AS total,
    SUM(CASE WHEN scope = 3 THEN co2e_mt_million ELSE 0 END) / SUM(co2e_mt_million) * 100 AS scope3_pct
FROM scope_emissions
GROUP BY ticker, reporting_year;

CREATE VIEW v_top_hotspots AS
SELECT ticker, stage, risk_type, inherent_score, narrative
FROM risk_matrix
WHERE inherent_score >= 18
ORDER BY inherent_score DESC;
