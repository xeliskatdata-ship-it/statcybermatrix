"""
Collecte reelle des articles cyber
Sources (17 au total) :
  API REST  : NewsAPI
  Flux RSS  : The Hacker News · BleepingComputer · Zataz · CISA Alerts
              Krebs on Security · Dark Reading · ANSSI · Schneier on Security
              SecurityWeek · Cyber Scoop · Threatpost
              The Record · Infosecurity Magazine · Helpnet Security
              Graham Cluley · CERT-EU

Sortie : data/raw/articles_YYYY-MM-DD.csv dont le dernier créé est articles_cleaned_2026-03-18.csv (recréé car ajout de nouvelles sources)
"""

import requests
import feedparser
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------

# Dossier de sortie pour les articles bruts
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Flux RSS : 16 sources publiques sans cle API
RSS_FEEDS = {
    # -- Sources anglophones generales --
    "The Hacker News"      : "https://feeds.feedburner.com/TheHackersNews",
    "BleepingComputer"     : "https://www.bleepingcomputer.com/feed/",
    "CISA Alerts"          : "https://www.cisa.gov/news.xml",
    "Krebs on Security"    : "https://krebsonsecurity.com/feed/",
    "Dark Reading"         : "https://www.darkreading.com/rss.xml",
    "SecurityWeek"         : "https://feeds.feedburner.com/Securityweek",
    "Cyber Scoop"          : "https://cyberscoop.com/feed/",
    "Threatpost"           : "https://threatpost.com/feed/",
    "Schneier on Security" : "https://www.schneier.com/feed/atom/",

    # -- Sources investigatives et experts --
    "The Record"           : "https://therecord.media/feed",
    "Infosecurity Magazine": "https://www.infosecurity-magazine.com/rss/news/",
    "Helpnet Security"     : "https://www.helpnetsecurity.com/feed/",
    "Graham Cluley"        : "https://grahamcluley.com/feed/",

    # -- Sources francophones --
    "Zataz"                : "https://www.zataz.com/feed/",

    # -- Sources gouvernementales officielles --
    "ANSSI"                : "https://www.cert.ssi.gouv.fr/feed/",
    "CERT-EU"              : "https://cert.europa.eu/publications/threat-intelligence/rss.xml",
}


# ---------------------------------------------------
# 1. COLLECTE NEWSAPI
# ---------------------------------------------------
def collect_newsapi():
    """
    Collecte les articles depuis NewsAPI (API REST).
    Necessite la cle NEWSAPI_KEY dans le fichier .env
    """
    print("\nCollecte NewsAPI...")
    key = os.getenv("NEWSAPI_KEY")
    if not key:
        print("  ERREUR : Cle NEWSAPI_KEY manquante dans .env")
        return []

    url    = "https://newsapi.org/v2/everything"
    params = {
        "q"       : "cybersecurity OR ransomware OR phishing OR malware OR CVE OR vulnerability",
        "language": "en",
        "pageSize": 100,
        "sortBy"  : "publishedAt",
        "apiKey"  : key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data     = response.json()

        if data.get("status") != "ok":
            print(f"  ERREUR NewsAPI : {data.get('message')}")
            return []

        articles = []
        for a in data.get("articles", []):
            articles.append({
                "source"      : "NewsAPI",
                "title"       : a.get("title", ""),
                "description" : a.get("description", ""),
                "url"         : a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
                "collected_at": datetime.now().isoformat(),
            })

        print(f"  OK -- {len(articles)} articles collectes")
        return articles

    except Exception as e:
        print(f"  ERREUR -- {e}")
        return []


# ---------------------------------------------------
# 2. COLLECTE RSS FEEDS
# ---------------------------------------------------
def collect_rss():
    """
    Collecte les articles depuis les 16 flux RSS.
    Aucune cle API requise.
    """
    print("\nCollecte flux RSS...")
    articles  = []
    ok_count  = 0
    err_count = 0

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed  = feedparser.parse(feed_url)
            count = 0

            for entry in feed.entries:
                articles.append({
                    "source"      : source_name,
                    "title"       : entry.get("title", ""),
                    "description" : entry.get("summary", ""),
                    "url"         : entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                    "collected_at": datetime.now().isoformat(),
                })
                count += 1

            print(f"  OK -- {source_name:<28} -- {count} articles")
            ok_count += 1

        except Exception as e:
            print(f"  ERREUR -- {source_name:<28} -- {e}")
            err_count += 1

    print(f"\n  Bilan RSS : {ok_count} sources OK / {err_count} erreurs")
    return articles


# ---------------------------------------------------
# 3. SAUVEGARDE CSV
# ---------------------------------------------------
def save_to_csv(articles):
    """
    Sauvegarde la liste d'articles dans data/raw/articles_YYYY-MM-DD.csv.
    Si un fichier existe deja pour la date du jour, les articles sont ajoutes
    a la suite sans dupliquer l'en-tete.
    """
    if not articles:
        print("\nATTENTION : Aucun article a sauvegarder.")
        return None

    today    = datetime.now().strftime("%Y-%m-%d")
    filename = f"articles_{today}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    df = pd.DataFrame(articles)

    if os.path.exists(filepath):
        df.to_csv(filepath, mode='a', header=False, index=False, encoding='utf-8')
        print(f"\nArticles ajoutes dans : {filepath}")
    else:
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"\nFichier cree : {filepath}")

    print(f"  > {len(df)} articles sauvegardes")
    print(f"  > Colonnes : {list(df.columns)}")

    # Distribution par source
    print("\n  Distribution par source :")
    for src, cnt in df['source'].value_counts().items():
        print(f"    {src:<28} : {cnt} articles")

    return filepath


# ---------------------------------------------------
# 4. FONCTION PRINCIPALE
# ---------------------------------------------------
def collect_all():
    """
    Orchestre la collecte complete depuis toutes les sources :
      NewsAPI --> RSS (16 sources) --> AlienVault OTX --> URLhaus --> CSV
    """
    print("=" * 60)
    print("CyberPulse -- Collecte reelle S2")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Sources : 1 API + {len(RSS_FEEDS)} flux RSS")
    print("=" * 60)

    all_articles = []

    # Collecte NewsAPI
    all_articles += collect_newsapi()

    # Collecte RSS (16 sources)
    all_articles += collect_rss()

    # Bilan
    print(f"\nTotal collecte : {len(all_articles)} articles")
    print(f"Sources actives : {len(set(a['source'] for a in all_articles))}")

    # Sauvegarde
    filepath = save_to_csv(all_articles)

    print("\nCollecte terminee !")
    return filepath


# ---------------------------------------------------
# LANCEMENT DIRECT
# ---------------------------------------------------
if __name__ == "__main__":
    collect_all()
