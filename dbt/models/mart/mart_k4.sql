-- CyberPulse -- mart K4
-- Evolution des mentions par categorie dans le temps
-- Utilise la classification enrichie de stg_articles.category

{{ config(materialized='table') }}

WITH daily_counts AS (
    SELECT
        published_date,
        category,
        COUNT(*) AS nb_mentions
    FROM {{ ref('stg_articles') }}
    WHERE published_date IS NOT NULL
    GROUP BY published_date, category
)

SELECT
    published_date,
    category,
    nb_mentions
FROM daily_counts
ORDER BY published_date DESC, nb_mentions DESC
