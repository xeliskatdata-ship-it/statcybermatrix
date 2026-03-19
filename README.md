#CyberPulse — Veille automatique & analyse NLP des actualités cyber

Mon projet solo — Formation Data Analyst
L'objectif : automatiser la veille cyber et détecter les menaces émergentes via un dashboard Streamlit.

*Problématique : Comment automatiser la veille cyber et détecter les sujets émergents avant qu'ils deviennent des crises ?

#Utilisateurs cibles
Analyste SOC / RSSI · Consultant cyber · DSI / CTO · Étudiant / Chercheur · Citoyen passionné

#KPIs

| K1 | Articles collectés par jour / par source | Barres groupées + heatmap | 
| K2 | Top 10 mots-clés (7 jours glissants) | Histogramme horizontal | 
| K3 | Répartition par type de menace | Camembert / Treemap | 
| K4 | Évolution des mentions d'une menace | Courbe temporelle + filtre | 
| K5 | Alertes critiques par semaine | Barres + seuil d'alerte | |
| K6 | Top CVE les plus mentionnées | Tableau classé + histogramme + API NVD | 

#Sources de données

| NewsAPI | API REST | 
| The Hacker News | Flux RSS | 
| BleepingComputer | Flux RSS | 
| CISA Alerts | Flux RSS | 
| Krebs on Security | Flux RSS | 
| Dark Reading | Flux RSS | 
| SecurityWeek | Flux RSS |
| Cyber Scoop | Flux RSS | 
| Threatpost | Flux RSS | 
| Schneier on Security | Flux RSS | 
| The Record | Flux RSS | 
| Infosecurity Magazine | Flux RSS | 
| Helpnet Security | Flux RSS | 
| Graham Cluley | Flux RSS | 
| Zataz | Flux RSS | 
| ANSSI | Flux RSS | 
| CERT-EU | Flux RSS | 

#Priorités
*Socle obligatoire : ETL · PostgreSQL (raw → staging → mart) · Airflow · Streamlit · Docker
*Bonus après socle : TF-IDF · VADER · LDA · Déploiement Render

#Architecture

Collecte    →    Nettoyage    →    ETL / PostgreSQL    →    Dashboard    
Python           Pandas            raw_articles              Streamlit        
NewsAPI                            stg_articles              Plotly           
17 RSS Feeds                       mart_kpis                 (EN MODE PROJET POUR L'INSTANT..)            
                                   Airflow · dbt
                                   Docker

#Structure du projet

cyberpulse/
└── cyberpulse/
    │
    ├── src/
    │   ├── acquisition.py        ← Collecte : NewsAPI + 16 flux RSS (17 sources)
    │   ├── cleaning.py           ← Nettoyage : 7 etapes pandas + 13 categories
    │   ├── etl.py                ← ETL : pipeline Extract-Transform-Load (S3)
    │   └── utils_lang.py         ← Interface : traduction FR/EN
    │
    ├── app/
    │   ├── app.py                ← Visualisation : dashboard accueil + filtres (EN MODE PROJET POUR L'INSTANT)
    │   └── pages/
    │       ├── 1_KPI1_Articles.py
    │       ├── 2_KPI2_Mots_cles.py
    │       ├── 3_KPI3_Menaces.py
    │       ├── 4_KPI4_Tendances.py
    │       ├── 5_KPI5_Alertes.py
    │       └── 6_KPI6_CVE.py
    │
    ├── db/
    │   ├── schema.sql            ← Automatisation : tables PostgreSQL (A FAIRE)
    │   ├── load_to_db.py         ← Automatisation : chargement SQLAlchemy (A FAIRE)
    │   └── queries.sql           ← Automatisation : requetes KPIs (A FAIRE)
    │
    ├── dbt/
    │   └── models/
    │       ├── staging/stg_articles.sql   ← dbt : nettoyage SQL (A FAIRE)
    │       └── mart/mart_kpis.sql         ← dbt : agregations KPI (A FAIRE)
    │
    ├── pipelines/
    │   └── dag_cyberpulse.py     ← Automatisation : A FAIRE
    │
    ├── data/
    │   ├── raw/
    │   │   └── articles_2026-03-18.csv        
    │   └── cleaned/
    │       └── articles_cleaned_2026-03-18.csv 
    │
    ├── docker-compose.yml        ← Automatisation : PostgreSQL + Airflow (A FAIRE) + Streamlit
    └── .env                      ← NEWSAPI_KEY 
├── requirements.txt
└── README.md

#Règles de nettoyage (S2)

Script : `src/cleaning.py`
Entrée : `data/raw/articles_YYYY-MM-DD.csv` — 325 articles · 6 colonnes
Sortie : `data/cleaned/articles_cleaned_YYYY-MM-DD.csv` — 323 articles · 9 colonnes

| 1 | Suppression doublons | Sur `url` puis sur `title` | 2 supprimés |
| 2 | Valeurs manquantes | `description` NaN → `''` · `title` NaN → `'Sans titre'` | 13 NaN → 0 |
| 3 | Normalisation dates | `2026-03-12T15:40:00Z` → `2026-03-12 15:40:00` | 323 OK |
| 4 | Nettoyage texte | Suppression HTML · entités · caractères de contrôle · troncature 500 chars | 323 traités |
| 5 | Colonne `published_date` | Date seule `YYYY-MM-DD` extraite de `published_at` | Créée |
| 6 | Colonne `content_length` | Longueur de la description en caractères | Créée |
| 7 | Colonne `category` | Type de menace détecté par mots-clés parmi 13 catégories | Créée |

#Catégories de menaces — 13 catégories (j'ai identifié les menaces qui étaient identifiées dans "général")

| `ransomware` | ransomware, lockbit, akira, blackcat, ryuk, conti |
| `phishing` | phishing, bec, credential, smishing, vishing, spoofing |
| `vulnerability` | vulnerability, cve, patch, exploit, zero-day, rce, sql injection |
| `malware` | malware, trojan, backdoor, botnet, emotet, cobalt strike, c2 |
| `apt` | apt, nation-state, lazarus, volt typhoon, espionage |
| `ddos` | ddos, denial of service, flood, killnet, syn flood |
| `data_breach` | data breach, leak, pii, gdpr, dark web, stolen data |
| `supply_chain` | supply chain, npm, pypi, xz utils, ci/cd |
| `cloud` | aws, azure, s3 bucket, kubernetes, iam, misconfigured |
| `iot` | iot, scada, ics, firmware, industrial control |
| `regulation` | nis2, dora, gdpr, iso 27001, nist, compliance |
| `incident` | siem, edr, forensics, ioc, threat hunting |
| `cryptojacking` | cryptomining, xmrig, monero, wallet drainer |
| `general` | Aucun mot-clé trouvé |

#Distribution observée (au 18/03/2026 -> 323 articles)

vulnerability  :  74 articles
malware        :  61 articles
phishing       :  31 articles
ransomware     :  21 articles
general        : 108 articles  <- en reduction (dictionnaire en cours d'enrichissement)
apt            :   7 articles
cloud          :   6 articles
data_breach    :   5 articles
iot            :   4 articles
regulation     :   3 articles
incident       :   2 articles
ddos           :   1 article

#Planning

Fait :
| S1 | 10 → 16 mars | Cadrage & Architecture 
| S2 | 17 → 23 mars | Collecte réelle & Nettoyage 

Reste à faire :
| S3 | 24 → 30 mars | Base de données & ETL (PostgreSQL + dbt + Docker) 
| S4 | 31 mars → 6 avril | ETL structuré & Dashboard final 
| S5 | 7 → 23 avril | Orchestration Airflow & NLP bonus 
| Démo | 23 avril | 
