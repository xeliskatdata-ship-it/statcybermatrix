-- ============================================================
-- CyberPulse — Schema PostgreSQL
-- Modèle 3 couches : raw → staging → mart
-- Colonnes vérifiées sur les CSV réels — 19/03/2026
-- ============================================================

DROP TABLE IF EXISTS mart_kpis
CASCADE;
DROP TABLE IF EXISTS stg_articles
CASCADE;
DROP TABLE IF EXISTS raw_articles
CASCADE;

-- ============================================================
-- COUCHE 1 — raw_articles
-- Données brutes telles que produites par acquisition.py
-- 6 colonnes : source, title, description, url, published_at, collected_at
-- ============================================================
CREATE TABLE raw_articles
(
    id SERIAL PRIMARY KEY,
    source TEXT,
    title TEXT,
    description TEXT,
    url TEXT,
    published_at TEXT,
    -- date brute, non normalisée
    collected_at TEXT,
    -- date brute de collecte
    inserted_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- COUCHE 2 — stg_articles
-- Données nettoyées par cleaning.py
-- 9 colonnes : + published_date normalisée, content_length, category
-- ============================================================
CREATE TABLE stg_articles
(
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT UNIQUE,
    -- bloque les doublons d'URL
    published_at TEXT,
    -- date brute conservée
    collected_at TEXT,
    published_date DATE,
    -- date normalisée ISO 8601
    content_length INTEGER,
    category TEXT,
    inserted_at TIMESTAMP DEFAULT NOW()
);

-- Index pour les filtres fréquents du dashboard
CREATE INDEX idx_stg_source      ON stg_articles(source);
CREATE INDEX idx_stg_category    ON stg_articles(category);
CREATE INDEX idx_stg_published   ON stg_articles(published_date);

-- ============================================================
-- COUCHE 3 — mart_kpis
-- Agrégations pré-calculées pour les 6 KPIs Streamlit
-- Alimenté par dbt, lu directement par le dashboard
-- ============================================================
CREATE TABLE mart_kpis
(
    id SERIAL PRIMARY KEY,
    kpi_name TEXT NOT NULL,
    -- 'K1_articles_par_jour', etc.
    dimension TEXT,
    -- source, category, keyword…
    period_date DATE,
    value NUMERIC,
    label TEXT,
    computed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mart_kpi_name  ON mart_kpis(kpi_name);
CREATE INDEX idx_mart_period    ON mart_kpis(period_date);

-- ============================================================
-- Vérification au démarrage
-- ============================================================
    SELECT 'raw_articles' AS table_name, COUNT(*) AS nb_lignes
    FROM raw_articles
UNION ALL
    SELECT 'stg_articles', COUNT(*)
    FROM stg_articles
UNION ALL
    SELECT 'mart_kpis', COUNT(*)
    FROM mart_kpis;