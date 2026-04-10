# CyberPulse

**Veille automatique & analyse NLP des actualités cyber**

Dashboard de threat intelligence qui collecte, nettoie, classifie et géolocalise les menaces cyber en temps réel depuis 64 sources spécialisées.

> Projet solo · Wild Code School · Data Analytics 2026  
> Démo finale : 23 avril 2026

---

## Problématique

**Comment identifier rapidement les sujets émergents en cybersécurité et suivre leur évolution ?**

CyberPulse automatise la veille structurée : collecte toutes les heures, classification en 13 catégories de menaces, géolocalisation du pays attaqué par NLP, et affichage sur un dashboard interactif.

---

## Stack technique

| Couche | Outils |
|--------|--------|
| Collecte | Python · Requests · feedparser · 3 APIs REST + 61 flux RSS |
| Nettoyage | Pandas · 942 mots-clés · 13 catégories |
| Base de données | PostgreSQL 15 · 3 couches (raw → stg → mart) |
| Transformation | dbt (staging + 6 marts) |
| Orchestration | Apache Airflow 2.8 · DAG 4 tâches · cron horaire |
| Dashboard | Streamlit · Plotly · Leaflet.js |
| NLP | spaCy (en_core_web_sm + fr_core_news_sm) |
| Conteneurisation | Docker Compose (3 services) |
| i18n | FR/EN · deep-translator |

---

## Architecture

```
acquisition.py (3 APIs + 61 RSS)
      │
      ▼
cleaning.py (942 keywords → 13 catégories)
      │
      ▼
load_to_db.py → PostgreSQL raw_articles
                      │
                      ▼
              dbt run → stg_articles (classification regex)
                      │
                      ▼
                 mart_k1 ... mart_k6 (agrégation)
                      │
                      ▼
              Streamlit Dashboard (8 pages)
```

**Orchestration Airflow :**
```
t1_acquisition → t2_cleaning → t3_load_to_db → t4_dbt_run
```

---

## Sources de données (64)

| Type | Nombre | Exemples |
|------|--------|----------|
| API REST | 3 | NewsAPI, AlienVault OTX, NVD/NIST |
| Presse anglo généraliste | 9 | The Hacker News, BleepingComputer, Krebs on Security |
| Investigatif & experts | 4 | The Record, Infosecurity Magazine |
| Francophone | 4 | Zataz, ANSSI, French Breaches, LeMagIT |
| Gouvernemental | 4 | ANSSI, CERT-EU, NCSC UK, ENISA |
| Vendors threat research | 14 | Unit42, Talos, Microsoft Security, CrowdStrike |
| DFIR & Blue Team | 3 | The DFIR Report, Red Canary, Huntress |
| OSINT & investigations | 7 | Bellingcat, Intel471, Shodan Blog |
| Threat Intelligence | 11+ | SANS ISC, Securelist, Proofpoint, Citizen Lab |
| Presse tech sécurité | 2 | Wired Security, Ars Technica Security |

---

## KPIs & Dashboard

| # | Indicateur | Visualisation |
|---|-----------|---------------|
| K1 | Articles collectés par jour / source | Small multiples + heatmap |
| K2 | Top mots-clés fréquents | Bar chart + heatmap catégorie×période + scatter interactif |
| K3 | Répartition par type de menace | Donut / Treemap |
| K4 | Évolution des mentions d'une menace | Courbe temporelle + filtre |
| K5 | Alertes critiques par semaine | Barres + seuil d'alerte |
| K6 | Top CVE les plus mentionnées | Tableau classé + histogramme |
| K7 | Carte mondiale des menaces | Leaflet.js + géolocalisation NLP |

---

## Classification des menaces

**13 catégories · 942 mots-clés** (cleaning.py) + **regex SQL** (stg_articles.sql)

| Catégorie | Exemples de mots-clés |
|-----------|----------------------|
| ransomware | lockbit, blackcat, ryuk, conti, akira, double extortion |
| phishing | spear-phishing, bec, credential stuffing, quishing |
| vulnerability | cve, zero-day, rce, log4shell, privilege escalation |
| malware | trojan, cobalt strike, mimikatz, infostealer |
| apt | lazarus, volt typhoon, apt28, fancy bear |
| data_breach | data breach, leak, exfiltration, dark web |
| ddos | ddos, amplification, killnet, botnet attack |
| supply_chain | npm, pypi, solarwinds, dependency confusion |
| cryptography | — |
| defense | — |
| offensive | — |
| compliance | — |
| identity | — |
| general | filet de sécurité (17,9% des articles) |

**Résultat :** catégorie "general" réduite de 54,8% à 17,9% grâce à un enrichissement en 2 passes.

---

## Géolocalisation intelligente (carte des menaces)

Le pipeline `extract_target()` identifie le **pays attaqué** (pas la source du média) en 5 étapes :

1. **Phrases explicites** — 10 regex EN+FR ("breach in France", "attaque contre l'Allemagne")
2. **Nom de pays dans le titre** — 65+ pays reconnus (TARGET_GEO)
3. **Nom de pays dans le corps** — description[:1000], filtre len ≥ 4
4. **spaCy NER bilingue** — modèles en/fr, scoring par proximité pays↔mot-clé cyber
5. **Fallback source** — coordonnées de la source RSS (dernier recours)

**Score de confiance** (`_compute_confidence`) : 0–100 sur 3 axes :
- Localisation (0–40 pts) : pays trouvé dans le texte vs fallback
- Victime (0–35 pts) : organisation identifiée par regex + spaCy ORG
- Signal cyber (0–15 pts) : mot-clé cyber en début d'article

Seuils : **forte** ≥ 70 | **moyenne** ≥ 45 | **faible** < 45

---

## Installation

### Prérequis

- Docker & Docker Compose
- Python 3.11+
- Clés API dans `.env` 

### Lancement

```bash
# Démarrer les 3 services (PostgreSQL + Airflow + Streamlit)
docker compose up -d

# Vérifier
docker ps

### Lancement manuel du pipeline

```bash
# Collecte
python src/acquisition.py

# Nettoyage
python src/cleaning.py

# Chargement en base
python db/load_to_db.py

# Transformation dbt
docker exec -it cyberpulse_airflow bash -c "cd /opt/airflow/dbt && dbt run"
```

---

## Arborescence

```
cyberpulse/
├── src/
│   ├── acquisition.py        # 3 APIs + 61 RSS = 64 sources
│   ├── cleaning.py           # 13 catégories · 942 mots-clés
│   ├── db_connect.py         # Connexion PostgreSQL · cache TTL 120s
│   └── utils_lang.py         # i18n FR/EN · 95+ clés
│
├── app/
│   ├── app.py                # Dashboard accueil + navigation KPI
│   ├── carte_menaces.html    # Leaflet.js · marqueurs scintillants
│   └── pages/
│       ├── 1_kpi1_Articles.py
│       ├── 2_kpi2_Mots_cles.py
│       ├── 3_KPI3_Menaces.py
│       ├── 4_KPI4_Tendances.py
│       ├── 5_KPI5_Alertes.py
│       ├── 6_KPI6_CVE.py
│       └── 7_Carte_Menaces.py
│
├── db/
│   ├── schema.sql            # Tables raw / stg / mart
│   └── load_to_db.py         # INSERT ON CONFLICT · WHERE NOT EXISTS
│
├── dbt/
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       │   └── stg_articles.sql   # Classification 13 catégories · CTE
│       └── mart/
│           ├── mart_k1.sql ... mart_k6.sql
│
├── pipelines/
│   └── dag_cyberpulse.py     # DAG Airflow · 4 tâches · cron horaire
│
├── docker-compose.yml        # PostgreSQL + Airflow + Streamlit
├── .env                      # Clés API + credentials PostgreSQL
└── README.md
```

---

## Architecture Docker

| Service | Image | Port | Rôle |
|---------|-------|------|------|
| postgres | postgres:15 | 5432 | Base de données |
| streamlit | python:3.11-slim | 8501 | Dashboard |
| airflow | apache/airflow:2.8.0 | 8080 | Orchestration pipeline |

---

## Architecture dbt

```
raw_articles (table PostgreSQL)
  → stg_articles (view · classification 13 catégories par regex)
    → mart_k1 ... mart_k6 (tables · agrégation uniquement)
```

**Principe DRY** : la classification est uniquement dans `stg_articles.sql`. Les marts ne font que l'agrégation.

---

## Limites connues

| Limite | Description |
|--------|------------|
| Attaquant vs victime | La géoloc peut confondre le pays attaquant et le pays attaqué (ex: "Russia's Forest Blizzard" → Russie détectée comme victime). Le score faible alerte sur ces cas. |
| Une catégorie par article | Un article multi-menaces est forcé dans une seule catégorie (premier match) |
| Deux systèmes de classification | cleaning.py (942 keywords) et stg_articles.sql (regex dbt) coexistent — le dashboard lit dbt |

---

## Auteur

**Stéphanie Bérard alias Xelis** · Wild Code School · Promotion Data Analytics 2026

---

*Dernière mise à jour : 10 avril 2026*