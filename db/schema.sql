-- ============================================================
-- CyberPulse -- Schema PostgreSQL
-- Seule la couche raw est geree ici (init Docker)
-- Les couches stg + mart sont gerees par dbt (views + tables)
-- ============================================================

DROP TABLE IF EXISTS raw_articles CASCADE;

-- ============================================================
-- COUCHE RAW — raw_articles
-- Donnees brutes telles que produites par acquisition.py
-- 6 colonnes : source, title, description, url, published_at, collected_at
-- ============================================================
CREATE TABLE raw_articles (
    id           SERIAL PRIMARY KEY,
    source       TEXT,
    title        TEXT,
    description  TEXT,
    url          TEXT,
    published_at TEXT,                          -- date brute, non normalisee
    collected_at TEXT,                          -- date brute de collecte
    inserted_at  TIMESTAMP DEFAULT NOW()
);

-- Index pour le scan dbt sur la table source
CREATE INDEX idx_raw_source    ON raw_articles(source);
CREATE INDEX idx_raw_title     ON raw_articles(title);

-- ============================================================
-- Verification au demarrage
-- ============================================================
SELECT 'raw_articles' AS table_name, COUNT(*) AS nb_lignes
FROM raw_articles;