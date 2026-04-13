# StatCyberMatrix

**Veille automatique & analyse NLP des actualités cyber**

Dashboard de threat intelligence qui collecte, nettoie, classifie les articles cyber et géolocalise les menaces cyber en temps réel depuis 64 sources spécialisées.

> Projet solo · Wild Code School · Data Analytics 2026  

---

## Problématique

**Comment identifier rapidement les sujets émergents en cybersécurité et suivre leur évolution ?**

StatCyberMatrix automatise la veille structurée : collecte toutes les heures, classification en 13 catégories de menaces, géolocalisation du pays attaqué par NLP, et affichage sur un dashboard interactif.

---

## Stack technique

| Couche | Outils |
|--------|--------|
| Collecte | Python · Requests · feedparser · 3 APIs REST + 61 flux RSS |
| Nettoyage | Pandas · 942 mots-clés · 13 catégories |
| Base de données | PostgreSQL (Neon) · 3 couches (raw → stg → mart) |
| Transformation | SQL pur · vues chaînées (stg → 6 marts) |
| Orchestration | GitHub Actions · cron horaire |
| Dashboard | Streamlit Cloud · Plotly · Leaflet.js |
| NLP | spaCy (en_core_web_sm + fr_core_news_sm) |
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
load_to_db.py → Neon PostgreSQL raw_articles
                      │
                      ▼
              stg_articles (vue · classification regex)
                      │
                      ▼
                 mart_k1 ... mart_k6 (vues · agrégation)
                      │
                      ▼
              Streamlit Cloud Dashboard (8 pages)
```

**Orchestration GitHub Actions :**
```
acquisition.py → cleaning.py → load_to_db.py → refresh_marts.py
```

---

## Déploiement cloud

| Service | Plateforme | Rôle |
|---------|-----------|------|
| Base de données | Neon (eu-central-1) | PostgreSQL serverless |
| Dashboard | Streamlit Cloud | Frontend interactif |
| Pipeline | GitHub Actions | Collecte horaire automatisée |

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
| K2 | Top mots-clés fréquents | Lollipop chart horizontal + heatmap catégorie×période |
| K3 | Répartition par type de menace | Donut / Treemap |
| K4 | Évolution des mentions d'une menace | Courbe temporelle + filtre |
| K5 | Alertes critiques par semaine | Barres + seuil d'alerte |
| K6 | Top CVE les plus mentionnées | Tableau classé + histogramme |
| MAP | Carte mondiale des menaces | Leaflet.js + géolocalisation NLP |

---

## Classification des menaces

**13 catégories · 942 mots-clés** (cleaning.py) + **regex SQL** (stg_articles)

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
| cryptography | chiffrement, tls, post-quantum, aes |
| defense | siem, soc, edr, xdr, forensic |
| offensive | pentest, red team, bug bounty, ctf |
| compliance | nis2, dora, iso 27001, rgpd |
| identity | mfa, zero trust, sso, iam |
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

## Arborescence

```
statcybermatrix/
├── src/
│   ├── acquisition.py        # 3 APIs + 61 RSS = 64 sources
│   └── cleaning.py           # 13 catégories · 942 mots-clés
│
├── app/
│   ├── Accueil.py            # Dashboard accueil + navigation KPI
│   ├── db_connect.py         # Connexion PostgreSQL · cache TTL 120s
│   ├── sidebar_css.py        # CSS sidebar · badges KPI + compteurs live
│   ├── utils_lang.py         # i18n FR/EN · 95+ clés
│   ├── carte_menaces.html    # Leaflet.js · marqueurs scintillants
│   ├── static/
│   │   ├── logo_statcybermatrix.png
│   │   └── statcybermatrix_sidebar.png
│   └── pages/
│       ├── 1_Articles_collectes.py
│       ├── 2_Suivi_des_mots-cles.py
│       ├── 3_Analyse_des_menaces.py
│       ├── 4_Analyse_des_tendances.py
│       ├── 5_Analyse_des_alertes.py
│       ├── 6_CVEs.py
│       └── 7_Carte_Menaces.py
│
├── db/
│   └── load_to_db.py         # INSERT WHERE NOT EXISTS · dedup 3 couches
│
├── .github/
│   └── workflows/
│       └── pipeline.yml      # GitHub Actions · cron horaire
│
└── README.md
```

---

## Architecture SQL (Neon)

```
raw_articles (table)
  → stg_articles (vue · classification 13 catégories par regex)
    → mart_k1 ... mart_k6 (vues · agrégation auto-refresh)
```

**Principe DRY** : la classification est uniquement dans `stg_articles`. Les marts ne font que l'agrégation. Toutes les couches sont des vues — les données se rafraîchissent automatiquement à chaque nouvelle collecte.

---

## Limites connues

| Limite | Description |
|--------|------------|
| Attaquant vs victime | La géoloc peut confondre le pays attaquant et le pays attaqué. Le score faible alerte sur ces cas. |
| Une catégorie par article | Un article multi-menaces est forcé dans une seule catégorie (premier match) |
| Déduplication URL | Le pipeline rejette les articles dont l'URL existe déjà — les flux RSS renvoyant les mêmes URLs ne génèrent pas de doublons mais empêchent la mise à jour d'articles modifiés |

---

## Auteur

**Stéphanie Bérard alias Xelis** · Wild Code School · Promotion Data Analytics 2026

---

*Dernière mise à jour : 13 avril 2026*