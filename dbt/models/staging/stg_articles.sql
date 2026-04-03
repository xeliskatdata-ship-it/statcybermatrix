-- CyberPulse -- modele staging
-- Source : raw_articles (chargee par load_to_db.py)
-- Gere deux formats de date :
--   ISO     : 2026-03-22T10:00:00Z  ou  2026-03-22 10:00:00
--   RFC2822 : Tue, 09 Dec 2025 10:00:00 +0000

{{ config(materialized='view') }}

SELECT
    id,
    source,
    title,
    description,
    url,
    published_at,
    collected_at,
    inserted_at,
    CASE
        WHEN published_at ~ '^\d{4}-\d{2}-\d{2}'
            THEN LEFT(published_at, 10)::date
        WHEN published_at ~ '\d{1,2} \w{3} \d{4}'
            THEN TO_DATE(
                (regexp_match(published_at, '(\d{1,2} \w{3} \d{4})'))[1],
    'DD Mon YYYY'
)
        ELSE NULL
END                                          AS published_date,
    LENGTH
(description)                          AS content_length,
    NULL::text                                   AS category,
    CASE
        WHEN LOWER
(title || ' ' || COALESCE
(description, ''))
             ~ 'ransomware|zero.day|apt|malware|vulnerability|data.breach'
        THEN TRUE
        ELSE FALSE
END                                          AS is_critical
FROM {{ source
('public', 'raw_articles') }}
WHERE title IS NOT NULL
  AND title != ''
  AND
(
    -- Exclure les dates futures (flux RSS avec dates erronees ou articles programmes)
    published_at IS NULL
    OR NOT
(
        CASE
            WHEN published_at ~ '^\d{4}-\d{2}-\d{2}' THEN LEFT
(published_at,10)::date
            WHEN published_at ~ '\d{1,2} \w{3} \d{4}'
            THEN TO_DATE
((regexp_match
(published_at,'\d{1,2} \w{3} \d{4}'))[1],'DD Mon YYYY')
            ELSE NULL
END > CURRENT_DATE
    )
  )
