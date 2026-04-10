-- CyberPulse -- mart K3
-- Repartition par type de menace x source
-- Utilise la classification enrichie de stg_articles.category

{{ config(materialized='table') }}

WITH counts AS (
    SELECT
        category,
        source,
        COUNT(*) AS nb_articles
    FROM {{ ref('stg_articles') }}
    WHERE published_date IS NOT NULL
    GROUP BY category, source
)

SELECT
    category,
    source,
    nb_articles
FROM counts
ORDER BY category, nb_articles DESC
