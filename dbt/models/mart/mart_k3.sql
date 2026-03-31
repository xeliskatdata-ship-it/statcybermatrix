-- K3 -- Répartition par type de menace × source
-- La catégorisation est calculée ici par regex sur titre+description
-- car stg_articles.category est NULL (enrichi en amont uniquement si le pipeline NLP tourne)

{{ config(materialized='table') }}

WITH
    categorized
    AS
    (
        SELECT
            source,
            CASE
            WHEN LOWER(COALESCE(title, '') || ' ' || COALESCE(description, ''))
                ~ 'ransomware'
                THEN 'ransomware'
            WHEN LOWER(COALESCE(title, '') || ' ' || COALESCE(description, ''))
                ~ 'phish'
                THEN 'phishing'
            WHEN LOWER(COALESCE(title, '') || ' ' || COALESCE(description, ''))
                ~ 'cve|vulnerabilit|zero.day|exploit|rce|privilege escalation'
                THEN 'vulnerability'
            WHEN LOWER(COALESCE(title, '') || ' ' || COALESCE(description, ''))
                ~ 'apt|nation.state|state.sponsored|apt2[0-9]|volt typhoon|lazarus|fancy bear'
                THEN 'apt'
            WHEN LOWER(COALESCE(title, '') || ' ' || COALESCE(description, ''))
                ~ 'ddos|denial.of.service|distributed denial'
                THEN 'ddos'
            WHEN LOWER(COALESCE(title, '') || ' ' || COALESCE(description, ''))
                ~ 'data.breach|data.leak|leaked|exfiltrat|database dump'
                THEN 'data_breach'
            WHEN LOWER(COALESCE(title, '') || ' ' || COALESCE(description, ''))
                ~ 'supply.chain|third.party|vendor compromise|dependency'
                THEN 'supply_chain'
            WHEN LOWER(COALESCE(title, '') || ' ' || COALESCE(description, ''))
                ~ 'malware|trojan|backdoor|spyware|worm|botnet|infostealer|wiper'
                THEN 'malware'
            ELSE 'general'
        END AS category
        FROM {{ ref('stg_articles') }}
    WHERE published_date IS NOT NULL
)

SELECT
    category,
    source,
    COUNT(*) AS nb_articles
FROM categorized
GROUP BY category, source
ORDER BY category, nb_articles DESC
