# StatCyberMatrix

Veille automatique et analyse NLP des actualités cyber.

Dashboard qui collecte, nettoie et classifie les articles cyber, attribue les attaques à des états-nations et géolocalise les menaces sur un globe 3D interactif depuis 106 sources spécialisées avec un taux de santé de 100 %.

Projet solo réalisé dans le cadre de la formation Data Analytics 2026 à la Wild Code School.

---

## Problématique

Comment identifier rapidement les sujets émergents en cybersécurité et suivre leur évolution ?

StatCyberMatrix automatise la veille structurée : collecte toutes les heures, classification en 13 catégories de menaces, géolocalisation du pays attaqué par NLP, attribution de l'attaquant par détection d'environ 120 groupes APT et ransomware, et affichage sur un globe 3D avec des arcs animés reliant le pays attaquant au pays victime.

---

## Stack technique

| Couche | Outils |
|--------|--------|
| Collecte | Python, Requests, feedparser, 7 APIs REST + 99 flux RSS |
| Nettoyage | Pandas, 942 mots-clés, 13 catégories |
| Base de données | PostgreSQL sur Neon, 3 couches (raw, stg, mart) |
| Transformation | SQL pur, vues chaînées (stg vers 6 marts) |
| Orchestration | GitHub Actions, cron horaire |
| Dashboard | Streamlit Cloud, Plotly |
| Globe 3D | Three.js r128, TopoJSON, Canvas texture, WebGL |
| NLP | spaCy avec en_core_web_sm et fr_core_news_sm |
| Attribution | environ 120 groupes APT/ransomware, 11 regex EN+FR |
| Cartographie | world-atlas countries-110m, 177 pays |
| Traduction | FR/EN via deep-translator |
| Maintenance RSS | Script de diagnostic parallélisé (scripts/check_feeds.py) |

---

## Architecture

Le pipeline s'exécute toutes les heures via GitHub Actions et suit un enchaînement séquentiel :

```
acquisition.py (7 APIs + 99 RSS = 106 sources)
      |
      v
cleaning.py (942 keywords, 13 catégories)
      |
      v
load_to_db.py --> Neon PostgreSQL raw_articles
                      |
                      v
              stg_articles (vue, classification regex)
                      |
                      v
                 mart_k1 ... mart_k6 (vues, agrégation)
                      |
                      v
              Streamlit Cloud Dashboard (8 pages + globe 3D)
```

L'étape d'acquisition collecte simultanément les 7 APIs (NewsAPI, OTX, NVD, Ransomware.live, ThreatFox, URLhaus, MalwareBazaar) et les 99 flux RSS actifs. Le nettoyage classifie chaque article. Le chargement insère les données dans Neon avec déduplication. Enfin, les vues matérialisées sont recalculées.

---

## Déploiement cloud

| Service | Plateforme | Rôle |
|---------|-----------|------|
| Base de données | Neon (eu-central-1) | PostgreSQL serverless |
| Dashboard | Streamlit Cloud | Frontend interactif |
| Pipeline | GitHub Actions | Collecte horaire automatisée |
| Globe 3D | Three.js via CDN cdnjs | Rendu WebGL dans iframe Streamlit |
| Cartographie | jsdelivr CDN | TopoJSON countries-110m |

---

## Sources de données

Le projet agrège 106 sources réparties en 7 APIs REST et 99 flux RSS actifs, avec un taux de santé du pipeline RSS de 100 %.

### APIs REST

| API | Clé requise | Ce que ça collecte | Impact sur le globe |
|-----|-------------|-------------------|---------------------|
| NewsAPI | Oui | Articles presse cyber mondiale | Indirect |
| AlienVault OTX | Oui, gratuite | Pulses threat intelligence | Indirect |
| NVD / NIST | Optionnelle | Vulnérabilités CVE avec scores CVSS | Indirect |
| Ransomware.live | Non | Victimes revendiquées avec groupe, pays et date | Direct |
| ThreatFox | Auth-Key gratuite | IOCs avec familles malware | Direct |
| URLhaus | Auth-Key gratuite | URLs malveillantes avec tags | Enrichissement |
| MalwareBazaar | Auth-Key gratuite | Échantillons malware avec signature | Enrichissement |

Ransomware.live est la source la plus impactante pour le globe car elle fournit directement le triplet groupe attaquant / victime / pays, que le NLP peut exploiter sans ambiguïté.

### Flux RSS (99 sources actives, 100 % de santé)

| Type | Nombre | Exemples |
|------|--------|----------|
| Vendors threat research | 25 | Unit42, Microsoft Security, CrowdStrike, Mandiant, Securelist, Proofpoint, SentinelOne, Check Point Research, Malwarebytes Labs, Recorded Future, Cybereason, Elastic Security, Arctic Wolf Labs, Varonis |
| Gouvernemental et CERTs | 18 | ANSSI, CERT-FR Alertes, CERT-FR Avis, CERT-EU, CISA Alerts, CISA ICS Advisories, NCSC UK, CERT.PL, CERT.LV, CERT.at, NCSC-FI, CCN-CERT, Swiss GovCERT, CERT-BE, AusCERT, HKCERT, JPCERT Japon, Canadian Cyber Centre |
| Presse cyber anglophone | 15 | The Hacker News, BleepingComputer, Krebs on Security, Dark Reading, SecurityWeek, CyberScoop, Threatpost, Schneier on Security, The Record, The Register Security, CyberWire Daily |
| DFIR, Blue Team et recherche indépendante | 10 | The DFIR Report, Red Canary, Huntress, Didier Stevens, SANS ISC, Malware Traffic Analysis, PortSwigger Research |
| OSINT et investigations | 8 | Bellingcat, Citizen Lab, Shodan Blog, NixIntel, The Intercept |
| Francophone | 8 | Zataz, ANSSI, IT-Connect, UnderNews, French Breaches, CERT-FR Alertes, CERT-FR Avis, Global Security Mag |
| Attribution et ransomware spécialisés | 6 | Cyble, SOCRadar, Flashpoint, Security Affairs, Kaspersky Daily, Group-IB |
| Médias tech généralistes | 5 | Wired Security, TechCrunch Security, Troy Hunt, Security Boulevard, Infosecurity Magazine |
| Cloud et Big Tech | 4 | AWS Security Blog, GitHub Security, Cloudflare, Google Security Blog |

Les sources francophones sont automatiquement traitées par le modèle spaCy français pour une meilleure extraction des entités géographiques.

---

## Maintenance du pipeline RSS

Le pipeline collecte 99 sources RSS cybersécurité avec un taux de santé de 100 %.
Pour auditer la santé des flux à tout moment :

```bash
python scripts/check_feeds.py
```

Sortie : synthèse écran + CSV détaillé dans `data/feeds_diagnostic.csv`.
Durée : ~15-20 secondes pour 100 flux testés en parallèle (15 workers).

### Workflow lors d'un ajout de flux

1. Ajouter l'URL dans `RSS_FEEDS` (src/acquisition.py)
2. Ajouter les coordonnées dans `SOURCE_GEO` (app/pages/7_Carte_Menaces.py)
3. Lancer `python scripts/check_feeds.py`
4. Retirer les flux KO identifiés (verdicts : URL_MORTE, ANTI_BOT, HTML_AU_LIEU_XML)
5. Commit + push

### Verdicts de santé possibles

| Verdict | Cause | Action |
|---------|-------|--------|
| OK | Flux RSS valide, XML parsable | Garder |
| URL_MORTE | HTTP 404, URL changée ou supprimée | Retirer |
| HTML_AU_LIEU_XML | Serveur retourne du HTML (page d'accueil) | Retirer |
| ANTI_BOT | HTTP 403/406 (Cloudflare strict) | Retirer |
| TIMEOUT | Serveur ne répond pas sous 10s | Retirer si récurrent |
| DNS_KO | Domaine disparu | Retirer |
| SERVEUR_KO | HTTP 5xx récurrent | Retirer si récurrent |
| REDIRECTION | URL finale différente | Mettre à jour |

### Commandes de filtrage utiles

```bash
# Lister tous les flux d'une catégorie
grep "URL_MORTE" data/feeds_diagnostic.csv

# Lister plusieurs catégories d'un coup
grep "URL_MORTE\|ANTI_BOT\|HTML_AU_LIEU_XML" data/feeds_diagnostic.csv

# Ouvrir le CSV dans VS Code
code data/feeds_diagnostic.csv
```

---

## KPIs et Dashboard

| KPI | Indicateur | Visualisation |
|-----|-----------|---------------|
| K1 | Articles collectés par jour et par source | Small multiples + heatmap |
| K2 | Top mots-clés fréquents | Lollipop chart horizontal + heatmap catégorie par période |
| K3 | Répartition par type de menace | Donut et Treemap |
| K4 | Évolution des mentions d'une menace | Courbe temporelle avec filtre |
| K5 | Alertes critiques par semaine | Barres avec seuil d'alerte |
| K6 | Top CVE les plus mentionnées | Tableau classé + histogramme |
| Globe | Globe de veille cyber | Three.js 3D avec arcs attaquant vers victime et TopoJSON |

---

## Classification des menaces

La classification repose sur 13 catégories et 942 mots-clés, appliquée en deux passes : d'abord dans cleaning.py lors du nettoyage, puis par regex SQL dans la vue stg_articles.

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
| general | articles non classifiés, 17,9% du total |

La catégorie general a été réduite de 54,8% à 17,9% grâce à l'enrichissement en deux passes.

---

## Géolocalisation intelligente

La fonction extract_target() identifie le pays attaqué, et non la source du média, en cinq étapes :

Première étape : recherche de phrases explicites via 10 regex bilingues, comme "breach in France" ou "attaque contre l'Allemagne".
Deuxième étape : scan du titre pour détecter un nom de pays parmi les 70 référencés dans le dictionnaire TARGET_GEO.
Troisième étape : scan du corps de l'article sur les 1000 premiers caractères avec un filtre de longueur minimale pour éviter les faux positifs.
Quatrième étape : analyse NER bilingue via spaCy (modèles anglais et français), avec un scoring par proximité entre l'entité géographique et les mots-clés cyber les plus proches dans le texte.
Cinquième étape : fallback sur les coordonnées de la source RSS si aucun pays n'a été identifié dans les étapes précédentes.

Chaque géolocalisation reçoit un score de confiance entre 0 et 100, calculé sur quatre axes :
   localisation (0 à 40 points selon la méthode de détection),
   victime identifiée (0 à 35 points si une organisation est confirmée par spaCy),
   signal cyber (0 à 15 points si un mot-clé fort apparaît en début d'article),
   et pénalités pour ambiguïtés (jusqu'à -28 points).
Les seuils sont : forte au-dessus de 70, moyenne entre 45 et 70, faible en dessous de 45.

---

## Attribution des attaquants

Le module d'attribution identifie le pays d'origine de l'attaque en deux passes.

La première passe scanne le titre et la description contre un dictionnaire d'environ 120 noms de groupes APT et ransomware, chacun mappé à son pays d'origine. La Russie concentre environ 55 groupes (Fancy Bear, Sandworm, LockBit, Cl0p, BlackCat, Qilin, Akira, RansomHub, Conti, REvil entre autres). La Chine en compte environ 25 (Volt Typhoon, Salt Typhoon, APT41, APT10, Hafnium, Mustang Panda). La Corée du Nord environ 12 (Lazarus, Kimsuky, APT38, BlueNoroff). L'Iran environ 15 (Charming Kitten, MuddyWater, OilRig, Peach Sandstorm). Quelques groupes occidentaux sont aussi référencés comme Scattered Spider (USA) ou Lapsus$ (UK).

La seconde passe utilise 11 regex pour détecter les formulations d'attribution en anglais et en français : "Russia-linked hackers", "China-backed threat actor", "attributed to North Korea", "hackers russes", "attribué à la Chine", et d'autres variantes.

Un arc n'apparaît sur le globe que si deux conditions sont simultanément réunies : le pays attaquant est identifié par un nom APT ou un pattern d'attribution, et le pays victime est identifié par le NLP avec certitude, c'est-à-dire sans recours au fallback sur la source. Chaque arc visible est donc vérifiable et défendable.

---

## Globe 3D

Le globe est rendu via Three.js r128 dans un iframe Streamlit. La terre est une sphère avec une texture canvas de 2048 par 1024 pixels sur laquelle les frontières de 177 pays sont dessinées dynamiquement via TopoJSON, à partir du dataset world-atlas countries-110m chargé depuis le CDN jsdelivr.

L'atmosphère est simulée par deux couches de shaders : un glow bleu externe côté arrière de la sphère, et un rim-light cyan interne côté face. Les marqueurs représentent les attaques attribuées, avec une taille proportionnelle à la sévérité et une couleur correspondant à la catégorie de menace (rouge pour les failles, bleu pour les infrastructures, ambre pour les éditeurs critiques, violet pour les groupes APT).

Les arcs animés relient le pays attaquant au pays victime via des courbes de Bézier quadratiques en 3D, avec un sprite lumineux qui voyage le long de l'arc pour simuler le flux d'attaque. L'altitude de chaque arc est proportionnelle à la distance géodésique entre les deux points.

L'utilisateur peut faire pivoter le globe par drag, zoomer par scroll, et survoler un marqueur pour afficher un tooltip détaillé avec la catégorie, le titre de l'article, le pays victime, la source, la date, l'organisation ciblée, le pays attaquant et le score de confiance.

---

## Arborescence

```
statcybermatrix/
|-- src/
|   |-- acquisition.py          # 7 APIs + 99 RSS = 106 sources
|   |-- cleaning.py             # 13 catégories, 942 mots-clés
|   |-- db_connect.py           # Connexion PostgreSQL, cache TTL 120s
|   +-- sidebar_css.py          # CSS sidebar, badges KPI + compteurs live
|
|-- app/
|   |-- Accueil.py              # Dashboard accueil + navigation KPI
|   |-- carte_menaces_globe.html # Three.js globe 3D, TopoJSON, arcs animés
|   |-- carte_menaces.html      # Version legacy Leaflet.js 2D
|   |-- static/
|   |   |-- logo_statcybermatrix.png
|   |   +-- statcybermatrix_sidebar.png
|   +-- pages/
|       |-- 1_Articles_collectes.py
|       |-- 2_Suivi_des_mots-cles.py
|       |-- 3_Analyse_des_menaces.py
|       |-- 4_Analyse_des_tendances.py
|       |-- 5_Analyse_des_alertes.py
|       |-- 6_CVEs.py
|       +-- 7_Carte_Menaces.py  # NLP + attribution APT + globe 3D
|
|-- db/
|   |-- load_to_db.py           
|   |-- neon_stg_marts.sql
|   |-- queries.sql
|   +-- schema.sql
|
|-- dbt/
|   |-- models/
|   |   |-- mart/               # mart_k1.sql ... mart_k6.sql
|   |   +-- staging/            # stg_articles.sql
|   +-- profiles.yml
|
|-- scripts/
|   +-- check_feeds.py          # Diagnostic parallélisé du pipeline RSS
|
|-- data/
|   |-- raw/                    # CSV articles par jour
|   +-- feeds_diagnostic.csv    # Sortie de check_feeds.py
|
|-- .github/
|   |-- scripts/
|   |   +-- refresh_marts.py    # Recalcul des vues sur Neon
|   +-- workflows/
|       +-- pipeline.yml        # GitHub Actions, cron horaire
|
+-- README.md
```

---

## Architecture SQL

La base suit une architecture en trois couches sur Neon PostgreSQL :

```
raw_articles (table)
  --> stg_articles (vue, classification 13 catégories par regex)
    --> mart_k1 ... mart_k6 (vues, agrégation auto-refresh)
```

La classification est définie uniquement dans stg_articles.
Les marts ne font que de l'agrégation.
Toutes les couches intermédiaires sont des vues, ce qui signifie que les données se rafraîchissent automatiquement à chaque nouvelle collecte sans intervention manuelle.

---

## Limites connues

Le NLP peut confondre le pays attaquant et le pays attaqué. Par exemple, un article titrant "Chinese hackers target US infrastructure" risque d'être géolocalisé en Chine au lieu des États-Unis.
Le filtre strict qui impose que l'attaquant soit différent de la cible atténue ce biais, mais ne l'élimine pas complètement.

Chaque article est classifié dans une seule catégorie.
Un article traitant simultanément de ransomware et de fuite de données sera attribué à la première catégorie détectée par les regex.

Le pipeline rejette les articles dont l'URL existe déjà en base.
Les flux RSS renvoyant les mêmes URLs ne génèrent pas de doublons, mais les articles modifiés après publication ne sont pas mis à jour.

Certaines APIs comme NVD ou OTX peuvent être temporairement indisponibles.
Le pipeline gère ces erreurs et continue la collecte avec les sources disponibles sans interrompre l'exécution.

Les flux RSS changent régulièrement (sites migrés, URLs retirées, protections anti-bot Cloudflare). Le script scripts/check_feeds.py permet de détecter et nettoyer ces flux en une commande.

---

## Évolutions prévues

Le pipeline horaire accumule l'historique en continu.
Plus le temps passe, plus le globe s'enrichit d'attaques attribuées, ce qui rend la visualisation de plus en plus pertinente.

Une correction du biais attaquant-cible est prévue pour que le système ignore la géolocalisation quand le pays attaquant est détecté comme pays cible, et cherche le vrai pays victime plus loin dans le texte.

L'intégration de sources structurées comme OpenCTI au format STIX/TAXII et les feeds publics MISP est envisagée pour augmenter le volume d'attributions vérifiées avec des données déjà normalisées.

Un filtre temporel (24h, 7 jours, 30 jours) sera réintroduit sur le globe une fois que les timestamps des articles seront correctement normalisés et que le volume de données récentes sera suffisant.

Une évolution de check_feeds.py avec désactivation des redirections automatiques est prévue pour éviter les faux positifs lorsqu'un serveur redirige une URL 404 vers une autre page 404.

---

## Auteur

Stéphanie Bérard -- Wild Code School -- Promotion Data Analytics 2026
Dernière mise à jour : 16 avril 2026
