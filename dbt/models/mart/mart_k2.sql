-- K2 -- Occurrences des mots-clés cyber par catégorie et période glissante
-- Colonnes produites : keyword, category, sub_category,
--                      period_days (3/7/15/30), occurrences, article_count, source_count

{{ config(materialized='table') }}

WITH
    kw_list
    AS
    (
        SELECT keyword, category, sub_category
        FROM (VALUES
                -- failles / Vulnérabilités
                ('zero-day', 'failles', 'Vulnérabilités'),
                ('0-day', 'failles', 'Vulnérabilités'),
                ('cve', 'failles', 'Vulnérabilités'),
                ('rce', 'failles', 'Vulnérabilités'),
                ('remote code execution', 'failles', 'Vulnérabilités'),
                ('lpe', 'failles', 'Vulnérabilités'),
                ('privilege escalation', 'failles', 'Vulnérabilités'),
                -- failles / Techniques
                ('sql injection', 'failles', 'Techniques'),
                ('xss', 'failles', 'Techniques'),
                ('cross-site scripting', 'failles', 'Techniques'),
                ('buffer overflow', 'failles', 'Techniques'),
                ('man-in-the-middle', 'failles', 'Techniques'),
                ('mitm', 'failles', 'Techniques'),
                ('supply chain attack', 'failles', 'Techniques'),
                ('supply chain', 'failles', 'Techniques'),
                -- failles / Fuites
                ('data breach', 'failles', 'Fuites'),
                ('database dump', 'failles', 'Fuites'),
                ('leaked credentials', 'failles', 'Fuites'),
                ('exfiltration', 'failles', 'Fuites'),
                ('data leak', 'failles', 'Fuites'),
                ('exposed credentials', 'failles', 'Fuites'),
                -- infra / Cloud
                ('aws', 'infra', 'Cloud'),
                ('s3 bucket', 'infra', 'Cloud'),
                ('azure', 'infra', 'Cloud'),
                ('azure ad', 'infra', 'Cloud'),
                ('google cloud', 'infra', 'Cloud'),
                ('gcp', 'infra', 'Cloud'),
                ('kubernetes', 'infra', 'Cloud'),
                ('docker', 'infra', 'Cloud'),
                -- infra / Systèmes
                ('active directory', 'infra', 'Systèmes'),
                ('windows server', 'infra', 'Systèmes'),
                ('linux kernel', 'infra', 'Systèmes'),
                ('macos', 'infra', 'Systèmes'),
                ('tcc', 'infra', 'Systèmes'),
                -- infra / Réseaux
                ('vpn', 'infra', 'Réseaux'),
                ('firewall', 'infra', 'Réseaux'),
                ('sd-wan', 'infra', 'Réseaux'),
                ('dns tunneling', 'infra', 'Réseaux'),
                ('firewall bypass', 'infra', 'Réseaux'),
                ('vpn gateway', 'infra', 'Réseaux'),
                -- editeurs / Hardware
                ('cisco', 'editeurs', 'Hardware'),
                ('fortinet', 'editeurs', 'Hardware'),
                ('palo alto', 'editeurs', 'Hardware'),
                ('check point', 'editeurs', 'Hardware'),
                ('juniper', 'editeurs', 'Hardware'),
                ('ubiquiti', 'editeurs', 'Hardware'),
                ('f5', 'editeurs', 'Hardware'),
                -- editeurs / Software
                ('microsoft 365', 'editeurs', 'Software'),
                ('exchange', 'editeurs', 'Software'),
                ('vmware', 'editeurs', 'Software'),
                ('esxi', 'editeurs', 'Software'),
                ('citrix', 'editeurs', 'Software'),
                ('sap', 'editeurs', 'Software'),
                ('salesforce', 'editeurs', 'Software'),
                ('atlassian', 'editeurs', 'Software'),
                ('confluence', 'editeurs', 'Software'),
                ('jira', 'editeurs', 'Software'),
                -- menaces / Malware
                ('ransomware', 'menaces', 'Malware'),
                ('infostealer', 'menaces', 'Malware'),
                ('trojan', 'menaces', 'Malware'),
                ('rat', 'menaces', 'Malware'),
                ('botnet', 'menaces', 'Malware'),
                ('wiper', 'menaces', 'Malware'),
                ('malware', 'menaces', 'Malware'),
                -- menaces / Groupes APT
                ('apt28', 'menaces', 'Groupes APT'),
                ('lazarus', 'menaces', 'Groupes APT'),
                ('lockbit', 'menaces', 'Groupes APT'),
                ('revil', 'menaces', 'Groupes APT'),
                ('fancy bear', 'menaces', 'Groupes APT'),
                ('scattered spider', 'menaces', 'Groupes APT'),
                ('volt typhoon', 'menaces', 'Groupes APT'),
                -- menaces / Indicateurs
                ('ioc', 'menaces', 'Indicateurs'),
                ('indicator of compromise', 'menaces', 'Indicateurs'),
                ('ttp', 'menaces', 'Indicateurs'),
                ('threat intelligence', 'menaces', 'Indicateurs'),
                ('threat actor', 'menaces', 'Indicateurs')
    ) AS t(keyword, category, sub_category)
    ),

    articles_base
    AS
    (
        SELECT
            id,
            source,
            published_date,
            LOWER(COALESCE(title, '') || ' ' || COALESCE(description, '')) AS corpus
        FROM {{ ref
    ('stg_articles') }}
    WHERE published_date IS NOT NULL
),

matched AS
(
    SELECT
    k.keyword,
    k.category,
    k.sub_category,
    a.id,
    a.source,
    a.published_date,
    (
            LENGTH(a.corpus)
            - LENGTH(REPLACE(a.corpus, k.keyword, ''))
        ) / NULLIF(LENGTH(k.keyword), 0) AS occ_in_doc
FROM kw_list k
    JOIN articles_base a ON a.corpus LIKE '%' || k.keyword || '%'
)

SELECT
    k.keyword,
    k.category,
    k.sub_category,
    p.period_days,
    COALESCE(
        SUM(
            CASE
                WHEN m.published_date >= CURRENT_DATE - (p.period_days || ' days')::INTERVAL
                THEN m.occ_in_doc
                ELSE 0
            END
        )::INT,
        0
    )                       AS occurrences,
    COUNT(
        DISTINCT CASE
            WHEN m.published_date >= CURRENT_DATE - (p.period_days || ' days')::INTERVAL
            THEN m.id
        END
    )                       AS article_count,
    -- ↓ NOUVEAU : nombre de sources distinctes ayant couvert ce mot-clé
    COUNT(
        DISTINCT CASE
            WHEN m.published_date >= CURRENT_DATE - (p.period_days || ' days')::INTERVAL
            THEN m.source
        END
    )                       AS source_count
FROM kw_list k
CROSS JOIN (VALUES
        (3),
        (7),
        (15),
        (30)) AS p(period_days)
    LEFT JOIN matched m ON m.keyword = k.keyword
GROUP BY k.keyword, k.category, k.sub_category, p.period_days
ORDER BY p.period_days, occurrences DESC