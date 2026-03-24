-- K1 -- Articles collectes par jour et par source

{
{ config
(materialized='table') }}

SELECT
    published_date,
    source,
    COUNT(*) AS nb_articles
FROM {{ ref
('stg_articles') }}
WHERE published_date IS NOT NULL
GROUP BY published_date, source
ORDER BY published_date DESC, nb_articles DESC
