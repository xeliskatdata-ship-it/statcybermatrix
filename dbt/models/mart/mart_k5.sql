-- CyberPulse -- mart K5
-- Alertes par semaine et categorie
-- Utilise la classification enrichie de stg_articles.category

{{ config(materialized='table') }}

WITH weekly_counts AS (
    SELECT
        DATE_TRUNC('week', published_date::timestamp)::date AS semaine,
        category,
        COUNT(*) AS nb_alertes
    FROM {{ ref('stg_articles') }}
    WHERE published_date IS NOT NULL
    GROUP BY 1, 2
)

SELECT
    semaine,
    category,
    nb_alertes
FROM weekly_counts
ORDER BY semaine DESC, nb_alertes DESC
