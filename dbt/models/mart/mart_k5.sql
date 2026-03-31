-- K5 -- Alertes critiques par semaine et categorie
-- Meme logique de categorisation regex que mart_k3 et mart_k4

{{ config(materialized='table') }}

WITH
    categorized
    AS
    (
        SELECT
            DATE_TRUNC('week', published_date::timestamp)
    ::date AS semaine,
        CASE
            WHEN LOWER
(COALESCE
(title, '') || ' ' || COALESCE
(description, ''))
                ~ 'ransomware'
                THEN 'ransomware'
            WHEN LOWER
(COALESCE
(title, '') || ' ' || COALESCE
(description, ''))
                ~ 'phish'
                THEN 'phishing'
            WHEN LOWER
(COALESCE
(title, '') || ' ' || COALESCE
(description, ''))
                ~ 'cve|vulnerabilit|zero.day|exploit|rce|privilege escalation'
                THEN 'vulnerability'
            WHEN LOWER
(COALESCE
(title, '') || ' ' || COALESCE
(description, ''))
                ~ 'apt|nation.state|state.sponsored|apt2[0-9]|volt typhoon|lazarus|fancy bear'
                THEN 'apt'
            WHEN LOWER
(COALESCE
(title, '') || ' ' || COALESCE
(description, ''))
                ~ 'ddos|denial.of.service|distributed denial'
                THEN 'ddos'
            WHEN LOWER
(COALESCE
(title, '') || ' ' || COALESCE
(description, ''))
                ~ 'data.breach|data.leak|leaked|exfiltrat|database dump'
                THEN 'data_breach'
            WHEN LOWER
(COALESCE
(title, '') || ' ' || COALESCE
(description, ''))
                ~ 'supply.chain|third.party|vendor compromise|dependency'
                THEN 'supply_chain'
            WHEN LOWER
(COALESCE
(title, '') || ' ' || COALESCE
(description, ''))
                ~ 'malware|trojan|backdoor|spyware|worm|botnet|infostealer|wiper'
                THEN 'malware'
            ELSE 'general'
END AS category
    FROM {{ ref('stg_articles') }}
    WHERE published_date IS NOT NULL
)

SELECT
    semaine,
    category,
    COUNT(*) AS nb_alertes
FROM categorized
GROUP BY semaine, category
ORDER BY semaine DESC, nb_alertes DESC
