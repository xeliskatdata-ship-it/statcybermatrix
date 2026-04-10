-- CyberPulse -- mart K1
-- Articles collectes par jour et par source

{{ config(materialized='table') }}

WITH daily_counts AS (
    SELECT
        published_date,
        source,
        COUNT(*) AS nb_articles
    FROM {{ ref('stg_articles') }}
    WHERE published_date IS NOT NULL
    GROUP BY published_date, source
)

SELECT
    published_date,
    source,
    nb_articles
FROM daily_counts
ORDER BY published_date DESC, nb_articles DESC
