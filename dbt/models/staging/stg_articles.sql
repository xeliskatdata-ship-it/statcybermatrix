-- CyberPulse -- modele staging
-- Source : raw_articles (chargee par load_to_db.py)
-- Gere deux formats de date :
--   ISO     : 2026-03-22T10:00:00Z  ou  2026-03-22 10:00:00
--   RFC2822 : Tue, 09 Dec 2025 10:00:00 +0000

{{ config(materialized='view') }}

-- Etape 1 : colonnes brutes + champ texte pour la classification
WITH base AS (
    SELECT
        id,
        source,
        title,
        description,
        url,
        published_at,
        collected_at,
        inserted_at,
        LOWER(title || ' ' || COALESCE(description, '')) AS text_search
    FROM {{ source('public', 'raw_articles') }}
    WHERE title IS NOT NULL
      AND title != ''
),

-- Etape 2 : parsing de la date une seule fois (DRY)
parsed AS (
    SELECT
        *,
        CASE
            WHEN published_at ~ '^\d{4}-\d{2}-\d{2}'
                THEN LEFT(published_at, 10)::date
            WHEN published_at ~ '\d{1,2} \w{3} \d{4}'
                THEN TO_DATE(
                    (regexp_match(published_at, '(\d{1,2} \w{3} \d{4})'))[1],
                    'DD Mon YYYY'
                )
            ELSE NULL
        END AS published_date,
        LENGTH(description) AS content_length
    FROM base
)

-- Etape 3 : classification + filtre dates futures
SELECT
    id,
    source,
    title,
    description,
    url,
    published_at,
    collected_at,
    inserted_at,
    published_date,
    content_length,

    -- Classification par vecteur de menace
    CASE
        -- Sources dont le contenu est connu par nature
        WHEN source = 'French Breaches'
            THEN 'data_breach'

        -- Ransomware
        WHEN text_search ~ 'ransomware|rançon|lockbit|blackcat|alphv|clop|akira|rhysida|medusa|black.?basta|royal.?ransom|hive.?ransom|double.?extortion|double.?extorsion|chiffrement.?fichier'
            THEN 'ransomware'

        -- Malware
        WHEN text_search ~ 'malware|maliciel|trojan|troyen|cheval.?de.?troie|botnet|spyware|rootkit|keylogger|infostealer|stealer|wiper|backdoor|porte.?dérobée|charge.?utile|payload|remote.?access.?trojan|rat\b|remote.?access|dissecting|crashfix'
            THEN 'malware'

        -- Phishing
        WHEN text_search ~ 'phishing|hameçonnage|smishing|vishing|spear.?phishing|ingénierie.?sociale|social.?engineering|credential.?harvesting|faux.?site|usurpation.?identité|business.?email.?compromise|bec|scam|arnaque'
            THEN 'phishing'

        -- Vulnerabilites
        WHEN text_search ~ 'vulnérabilité|vulnerability|cve-\d|zero.?day|0.?day|faille|exploit|rce|remote.?code.?execution|buffer.?overflow|privilege.?escalation|élévation.?de.?privilège|patch|correctif|mise.?à.?jour.?de.?sécurité|security.?update|security.?advisory|cyberattack|cyber.?attack|hacked|hijack'
            THEN 'vulnerability'

        -- Fuites de donnees
        WHEN text_search ~ 'data.?breach|fuite.?de.?données|leak|données.?personnelles|données.?exposées|exposed.?data|vol.?de.?données|data.?theft|rgpd|gdpr|cnil|information.?disclosure|credentials.?leaked|password.?leak|database.?exposed|account.?takeover|fraud'
            THEN 'data_breach'

        -- APT
        WHEN text_search ~ 'apt|advanced.?persistent|état.?nation|state.?sponsored|cyberespionnage|cyber.?espionage|lazarus|fancy.?bear|cozy.?bear|volt.?typhoon|salt.?typhoon|sandworm|turla|kimsuky|charming.?kitten|mustang.?panda|threat.?actor|nation.?state'
            THEN 'apt'

        -- DDoS
        WHEN text_search ~ 'ddos|déni.?de.?service|denial.?of.?service|distributed.?denial|attaque.?volumétrique|flooding'
            THEN 'ddos'

        -- Supply chain
        WHEN text_search ~ 'supply.?chain|chaîne.?d.?approvisionnement|logiciel.?compromis|dépendance.?malveillante|typosquatting|dependency.?confusion|third.?party.?risk|solarwinds|npm.?malicious|pypi.?malicious'
            THEN 'supply_chain'

        -- Cryptographie
        WHEN text_search ~ 'chiffrement|encryption|cryptograph|certificat|tls|ssl|clé.?publique|clé.?privée|aes|rsa|post.?quantum|sha-|md5'
            THEN 'cryptography'

        -- Defense et operations de securite
        WHEN text_search ~ 'pare.?feu|firewall|siem|soc|ids|ips|endpoint|edr|xdr|mdr|antivirus|détection|security.?operations|threat.?detection|incident.?response|réponse.?à.?incident|blue.?team|forensic|cybersecurity|cyber.?security|cybercrime|cyber.?crime|dark.?web|dark.?economy|cyber.?insurance|itdr|cmmc|security.?awareness|managed.?detection|intrusion\b|password.?manag'
            THEN 'defense'

        -- Securite offensive
        WHEN text_search ~ 'pentest|red.?team|bug.?bounty|test.?d.?intrusion|offensive.?security|ethical.?hacking|penetration.?test|ctf|capture.?the.?flag'
            THEN 'offensive'

        -- Conformite et reglementation
        WHEN text_search ~ 'compliance|conformité|réglementation|regulation|nis2|dora|iso.?27001|nist|anssi|certification|audit|gouvernance|governance|politique.?de.?sécurité|cyber.?résilience'
            THEN 'compliance'

        -- Identite et acces
        WHEN text_search ~ 'iam|identité|identity|authentification|authentication|mfa|2fa|oauth|saml|sso|single.?sign|active.?directory|ldap|zero.?trust|accès.?control|privileged.?access|pam'
            THEN 'identity'

        ELSE 'general'
    END AS category,

    -- Flag criticite
    CASE
        WHEN text_search ~ 'ransomware|zero.?day|apt|malware|vulnerability|data.?breach'
            THEN TRUE
        ELSE FALSE
    END AS is_critical

FROM parsed
-- Exclut les dates futures (erreurs de parsing ou flux RSS mal formes)
WHERE published_date IS NULL
   OR published_date <= CURRENT_DATE
   