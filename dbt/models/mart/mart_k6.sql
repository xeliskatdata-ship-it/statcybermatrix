-- K6 -- CVE les plus mentionnees dans les articles

{{ config(materialized='table') }}

WITH
    cve_extraites
    AS
    (
        SELECT
            t.cve[1]
     AS cve,
        id
    FROM {{ ref('stg_articles') }},
    LATERAL regexp_matches
(
        COALESCE
(title, '') || ' ' || COALESCE
(description, ''),
        'CVE-[0-9]{4}-[0-9]{4,7}',
        'g'
    ) AS t
(cve)
)

SELECT
    cve,
    COUNT(DISTINCT id) AS nb_mentions
FROM cve_extraites
GROUP BY cve
ORDER BY nb_mentions DESC
LIMIT 20
