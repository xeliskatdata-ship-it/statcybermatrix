# acquisition.py -- Collecte reelle des articles cyber
# Sprint 5 : 3 API (NewsAPI, OTX, NVD) + 61 flux RSS = 64 sources
# Sortie : data/raw/articles_YYYY-MM-DD.csv

import logging
import os
from datetime import datetime

import feedparser
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# -- Config globale --
TIMEOUT    = 15
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS_CHROME = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# -- 61 flux RSS organises en 7 groupes --
RSS_FEEDS = {
    # Presse anglo generaliste (9)
    "The Hacker News":        "https://feeds.feedburner.com/TheHackersNews",
    "BleepingComputer":       "https://www.bleepingcomputer.com/feed/",
    "CISA Alerts":            "https://www.cisa.gov/news.xml",
    "Krebs on Security":      "https://krebsonsecurity.com/feed/",
    "Dark Reading":           "https://www.darkreading.com/rss.xml",
    "SecurityWeek":           "https://feeds.feedburner.com/Securityweek",
    "Cyber Scoop":            "https://cyberscoop.com/feed/",
    "Threatpost":             "https://threatpost.com/feed/",
    "Schneier on Security":   "https://www.schneier.com/feed/atom/",
    # Investigatif & experts (4)
    "The Record":             "https://therecord.media/feed",
    "Infosecurity Magazine":  "https://www.infosecurity-magazine.com/rss/news/",
    "Helpnet Security":       "https://www.helpnetsecurity.com/feed/",
    "Graham Cluley":          "https://grahamcluley.com/feed/",
    # Francophone (4)
    "Zataz":                  "https://www.zataz.com/feed/",
    "French Breaches":        "https://frenchbreaches.com/feed.xml",
    "LeMagIT Securite":       "https://www.lemagit.fr/rss/Securite/",
    "No.log":                 "https://nolog.cz/feed/",
    # Gouvernemental (4)
    "ANSSI":                  "https://www.cert.ssi.gouv.fr/feed/",
    "CERT-EU":                "https://cert.europa.eu/publications/threat-intelligence/rss.xml",
    "NCSC UK":                "https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml",
    "ENISA":                  "https://www.enisa.europa.eu/news/enisa-news/RSS",
    # Vendors threat research (14)
    "Malwarebytes Labs":      "https://blog.malwarebytes.com/feed/",
    "Naked Security":         "https://nakedsecurity.sophos.com/feed/",
    "We Live Security":       "https://www.welivesecurity.com/feed/",
    "Trend Micro":            "https://feeds.trendmicro.com/Anti-MalwareBlog",
    "Recorded Future Blog":   "https://www.recordedfuture.com/feed",
    "Cybereason":             "https://www.cybereason.com/blog/rss.xml",
    "Unit42 (Palo Alto)":     "https://unit42.paloaltonetworks.com/feed/",
    "Talos Intelligence":     "https://blog.talosintelligence.com/feeds/posts/default",
    "Microsoft Security":     "https://www.microsoft.com/en-us/security/blog/feed/",
    "IBM X-Force":            "https://securityintelligence.com/feed/",
    "Elastic Security":       "https://www.elastic.co/security-labs/rss/feed.xml",
    "Secureworks":            "https://www.secureworks.com/blog/rss",
    "SentinelOne":            "https://www.sentinelone.com/blog/feed/",
    "WithSecure Labs":        "https://labs.withsecure.com/feed",
    # DFIR & Blue Team (3)
    "The DFIR Report":        "https://thedfirreport.com/feed/",
    "Red Canary":             "https://redcanary.com/blog/feed/",
    "Huntress":               "https://www.huntress.com/blog/rss.xml",
    # Presse tech securite (2)
    "Wired Security":         "https://www.wired.com/feed/category/security/latest/rss",
    "Ars Technica Security":  "https://feeds.arstechnica.com/arstechnica/security",
    # OSINT & investigations (7)
    "OSINT Curious":          "https://osintcurio.us/feed/",
    "Bellingcat":             "https://www.bellingcat.com/feed/",
    "Intel471":               "https://intel471.com/blog/rss.xml",
    "Shodan Blog":            "https://blog.shodan.io/rss/",
    "Maltego Blog":           "https://www.maltego.com/blog/feed/",
    "NixIntel":               "https://nixintel.info/feed/",
    "Sector035":              "https://sector035.nl/feed",
    # Threat Intelligence (11+)
    "SANS ISC":               "https://isc.sans.edu/rssfeed_full.xml",
    "Mandiant Blog":          "https://www.mandiant.com/resources/blog/rss.xml",
    "CrowdStrike Blog":       "https://www.crowdstrike.com/blog/feed/",
    "Securelist":             "https://securelist.com/feed/",
    "Proofpoint":             "https://www.proofpoint.com/us/rss.xml",
    "CIRCL":                  "https://www.circl.lu/pub/tr/rss/",
    "Abuse.ch":               "https://abuse.ch/blog/feed/",
    "Citizen Lab":            "https://citizenlab.ca/feed/",
    "The Intercept":          "https://theintercept.com/feed/?rss",
    "OCCRP":                  "https://occrp.org/en/feed/articles",
    "GreyNoise Blog":         "https://www.greynoise.io/blog/feed",
    "Censys Blog":            "https://censys.com/blog/feed/",
    "VulnCheck":              "https://vulncheck.com/blog/rss.xml",
    "AttackerKB":             "https://attackerkb.com/blog/feed/",
}


def _row(source, title, description, url, published_at):
    """Format standard pour chaque article collecte."""
    return {
        "source":       source,
        "title":        title or "",
        "description":  (description or "")[:500],
        "url":          url or "",
        "published_at": published_at or "",
        "collected_at": datetime.now().isoformat(),
    }


# ---------------------------------------------------
# 1. NEWSAPI
# ---------------------------------------------------
def collect_newsapi():
    key = os.getenv("NEWSAPI_KEY")
    if not key:
        log.warning("NEWSAPI_KEY absente -- skip")
        return []

    params = {
        "q":        "cybersecurity OR ransomware OR phishing OR malware OR CVE OR vulnerability",
        "language": "en",
        "pageSize": 100,
        "sortBy":   "publishedAt",
        "apiKey":   key,
    }

    try:
        r    = requests.get("https://newsapi.org/v2/everything", params=params, timeout=TIMEOUT)
        data = r.json()
        if data.get("status") != "ok":
            log.error("NewsAPI : %s", data.get("message"))
            return []

        articles = [
            _row("NewsAPI", a.get("title"), a.get("description"), a.get("url"), a.get("publishedAt"))
            for a in data.get("articles", [])
        ]
        log.info("NewsAPI : %d articles", len(articles))
        return articles

    except Exception as e:
        log.error("NewsAPI : %s", e)
        return []


# ---------------------------------------------------
# 2. ALIENVAULT OTX
# ---------------------------------------------------
def collect_otx():
    key = os.getenv("OTX_API_KEY")
    if not key:
        log.info("OTX_API_KEY absente -- skip (optionnel)")
        return []

    try:
        r = requests.get(
            "https://otx.alienvault.com/api/v1/pulses/subscribed",
            headers={"X-OTX-API-KEY": key},
            params={"limit": 50, "sort": "-created"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()

        articles = [
            _row(
                "AlienVault OTX",
                p.get("name"),
                p.get("description") or ", ".join(p.get("tags", [])),
                f"https://otx.alienvault.com/pulse/{p.get('id', '')}",
                p.get("created"),
            )
            for p in r.json().get("results", [])
        ]
        log.info("OTX : %d pulses", len(articles))
        return articles

    except Exception as e:
        log.error("OTX : %s", e)
        return []


# ---------------------------------------------------
# 3. NVD / NIST
# ---------------------------------------------------
def collect_nvd():
    headers = {}
    key = os.getenv("NVD_API_KEY")
    if key:
        headers["apiKey"] = key

    try:
        r = requests.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0",
            headers=headers,
            params={"resultsPerPage": 50, "startIndex": 0},
            timeout=20,
        )
        r.raise_for_status()

        articles = []
        for item in r.json().get("vulnerabilities", []):
            cve   = item.get("cve", {})
            cid   = cve.get("id", "")
            descs = cve.get("descriptions", [])
            desc  = next((d["value"] for d in descs if d["lang"] == "en"), "")

            # Score CVSS v3.1 prioritaire, sinon v3.0
            metrics = cve.get("metrics", {})
            score   = ""
            for v in ("cvssMetricV31", "cvssMetricV30"):
                if metrics.get(v):
                    score = str(metrics[v][0]["cvssData"].get("baseScore", ""))
                    break

            title = f"{cid} -- CVSS {score}" if score else cid
            articles.append(_row(
                "NVD", title, desc,
                f"https://nvd.nist.gov/vuln/detail/{cid}",
                cve.get("published"),
            ))

        log.info("NVD : %d CVE", len(articles))
        return articles

    except Exception as e:
        log.error("NVD : %s", e)
        return []


# ---------------------------------------------------
# 4. FLUX RSS (61 sources, fallback 2 etapes)
# ---------------------------------------------------
def collect_rss():
    articles = []
    ok = err = 0

    for name, url in RSS_FEEDS.items():
        feed = None

        # Etape 1 : requests + User-Agent Chrome (evite les blocages)
        try:
            r    = requests.get(url, headers=HEADERS_CHROME, timeout=TIMEOUT)
            feed = feedparser.parse(r.content)
        except Exception:
            pass

        # Etape 2 : feedparser direct si etape 1 a echoue ou 0 entrees
        if not feed or len(feed.entries) == 0:
            try:
                feed = feedparser.parse(url)
            except Exception:
                log.warning("%-30s -- echec total", name)
                err += 1
                continue

        entries = [
            _row(name, e.get("title"), e.get("summary"), e.get("link"), e.get("published"))
            for e in feed.entries
        ]

        if entries:
            articles.extend(entries)
            ok += 1
        else:
            err += 1

    log.info("RSS : %d sources OK / %d erreurs ou vides", ok, err)
    return articles


# ---------------------------------------------------
# 5. SAUVEGARDE CSV
# ---------------------------------------------------
def _save_to_csv(articles):
    if not articles:
        log.warning("Aucun article a sauvegarder")
        return None

    today    = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(OUTPUT_DIR, f"articles_{today}.csv")
    df       = pd.DataFrame(articles)

    # Append si fichier du jour existe deja (relance intra-journee)
    if os.path.exists(filepath):
        df.to_csv(filepath, mode="a", header=False, index=False, encoding="utf-8")
    else:
        df.to_csv(filepath, index=False, encoding="utf-8")

    log.info("Sauvegarde : %d articles -> %s", len(df), filepath)
    return filepath


# ---------------------------------------------------
# 6. ORCHESTRATION
# ---------------------------------------------------
def main():
    log.info("=" * 50)
    log.info("CyberPulse -- Collecte S5 -- %d sources", 3 + len(RSS_FEEDS))
    log.info("=" * 50)

    all_articles = (
        collect_newsapi()
        + collect_otx()
        + collect_nvd()
        + collect_rss()
    )

    n_sources = len({a["source"] for a in all_articles})
    log.info("Total : %d articles / %d sources actives", len(all_articles), n_sources)

    filepath = _save_to_csv(all_articles)
    return filepath


if __name__ == "__main__":
    main()