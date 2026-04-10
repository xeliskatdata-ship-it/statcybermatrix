# CyberPulse

Dashboard automatise de Threat Intelligence cyber. 
Collecte, classifie et visualise en temps reel les tendances issues de 64 sources (3 API + 61 flux RSS).
Projet de fin de formation Data Analyst — Wild Code School, promotion 2026.

---

## Architecture

```
Sources (64)          Pipeline ETL              PostgreSQL           Dashboard
+-----------+     +----------------+     +------------------+     +------------+
| NewsAPI   |     | acquisition.py |     | raw_articles     |     | Streamlit  |
| OTX       | --> | cleaning.py    | --> | stg_articles (v) | --> | 6 KPIs     |
| NVD       |     | load_to_db.py  |     | mart_k1..k6 (t)  |     | Carte      |
| 61 RSS    |     +----------------+     +------------------+     +------------+
              orchestre par Airflow        transforme par dbt
```

**3 couches de donnees :**

- **raw** — articles bruts inseres par `load_to_db.py`
- **stg** — vue dbt avec parsing de dates, classification par regex (13 categories, 942 keywords)
- **mart** — 6 tables dbt pre-agregees, lues directement par le dashboard

---

## Stack technique

| Composant | Technologie | Role |
|-----------|-------------|------|
| Collecte | Python, feedparser, requests | 3 API REST + 61 flux RSS |
| Nettoyage | Pandas, regex | Dedup, normalisation, classification |
| Base | PostgreSQL 15 | Stockage 3 couches (raw/stg/mart) |
| Transformation | dbt 1.9 | 7 modeles (1 view + 6 tables) |
| Orchestration | Airflow 2.8 | DAG horaire, 4 taches |
| Dashboard | Streamlit 1.53 | 6 KPIs + carte interactive |
| NLP | spaCy (en + fr) | Geolocalisation NER sur la carte |
| Cartographie | Leaflet.js | Carte temps reel avec scoring de confiance |
| Visualisation | Plotly | Graphiques interactifs |
| Infra | Docker Compose | 3 containers (postgres, streamlit, airflow) |

---

## KPIs

| Page | Titre | Contenu |
|------|-------|---------|
| KPI 1 | Volume de collecte | Articles par jour et par source |
| KPI 2 | Mots-cles cyber | Heatmap categorie x periode, scatter interactif |
| KPI 3 | Repartition des menaces | Radar/donut/bar par categorie, heatmap source x categorie |
| KPI 4 | Tendances temporelles | Evolution par vecteur avec moyenne mobile et z-score |
| KPI 5 | Threat Intelligence Matrix | Alertes hebdomadaires, treemap, volatilite |
| KPI 6 | CVEs les plus citees | Top CVEs, fiche detail NVD, echelle CVSS |
| Carte | Carte des menaces | Geolocalisation NER, 4 layers, scoring de confiance |

---

## Sources de donnees

**3 API REST :**
- NewsAPI (100 articles/requete)
- AlienVault OTX (50 pulses)
- NVD / NIST (50 CVEs recentes)

**61 flux RSS** repartis en 7 groupes :
presse generaliste (9), investigatif (4), francophone (4), gouvernemental (4), vendors threat research (14), DFIR & Blue Team (3), presse tech (2), OSINT (7), Threat Intelligence (14).

---

## Installation et lancement

### Pre-requis

- Docker Desktop
- Git Bash (Windows) ou terminal Unix
- Fichier `.env` a la racine du projet

### Lancement

```bash
# 1. Demarrer les containers
docker compose up -d --build

# 2. Attendre que PostgreSQL soit pret
docker compose logs -f postgres
# Attendre "database system is ready to accept connections", puis Ctrl+C

# 3. Lancer la collecte initiale
docker exec -it cyberpulse_streamlit bash -c "cd /app && python src/acquisition.py && python src/cleaning.py && python db/load_to_db.py"

# 4. Lancer dbt
docker exec -it cyberpulse_airflow bash -c "cd /opt/airflow/dbt && dbt run --profiles-dir ."

# 5. Ouvrir le dashboard
# http://

# 6. Ouvrir Airflow (admin / admin)
# http://
```

---

## Arborescence

```
cyberpulse/
  app/
    app.py                    # Page d'accueil Streamlit
    carte_menaces.html        # Template HTML Leaflet
    pages/
      1_kpi1_*.py
      2_kpi2_*.py
      3_kpi3_Menaces.py
      4_kpi4_Tendances.py
      5_kpi5_Alertes.py
      6_kpi6_CVE.py
      7_Carte_Menaces.py
  src/
    acquisition.py            # Collecte 64 sources
    cleaning.py               # Nettoyage 7 etapes, 942 keywords
    db_connect.py             # Connecteur PostgreSQL pour Streamlit
  db/
    schema.sql                # Init raw_articles
    load_to_db.py             # Chargement CSV -> PostgreSQL
  dbt/
    models/
      staging/
        stg_articles.sql      # Vue : parsing dates + classification
        sources.yml
      mart/
        mart_k1.sql           # Articles par jour x source
        mart_k2.sql           # Keywords x periode glissante
        mart_k3.sql           # Repartition categorie x source
        mart_k4.sql           # Mentions par jour x categorie
        mart_k5.sql           # Alertes par semaine x categorie
        mart_k6.sql           # Top 20 CVEs
    dbt_project.yml
    profiles.yml
  pipelines/
    dag_cyberpulse.py         # DAG Airflow (horaire)
  docker-compose.yml
  requirements.txt
  .env
```

---

## Pipeline Airflow

DAG `cyberpulse_daily_pipeline` — execution toutes les heures :

```
acquisition -> cleaning -> load_to_db -> dbt_run
```

- 2 retries par tache, delai de 5 minutes
- Tags : `cyberpulse`, `etl`

---

## Classification des menaces

13 categories detectees par regex (stg_articles) :

ransomware, phishing, vulnerability, malware, apt, ddos, data_breach, supply_chain, cryptography, defense, offensive, compliance, identity.

Fallback : `general` si aucun pattern ne matche.

---

## Geolocalisation (Carte des menaces)

4 niveaux d'enrichissement :

1. **Patterns de contexte** — regex bilingues (EN/FR) detectant le pays attaque
2. **Scan titre + description** — lookup dans un referentiel de 80+ pays
3. **spaCy NER** — modeles `en_core_web_sm` + `fr_core_news_sm` avec scoring de proximite mot-cle cyber / entite GPE
4. **Fallback source** — geolocalisation par origine de la source si aucun pays detecte

Score de confiance 0-100 sur 4 axes : localisation, victime, signal cyber, penalites.

---

## Auteur

**Xelis - Stéphanie Bérard** — Data Analyst, Wild Code School 2026

