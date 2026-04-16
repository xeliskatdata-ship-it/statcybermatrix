# acquisition.py -- Collecte reelle des articles cyber
# Sprint 6 : 7 API + 100 flux RSS = 107 sources
# Nouvelles API : Ransomware.live, ThreatFox, URLhaus, MalwareBazaar
# v9.2 : NVD avec filtre temporel + retry / RSS logging détaillé par flux
# Sortie : data/raw/articles_YYYY-MM-DD.csv

import logging
import os
import time
from datetime import datetime, timedelta, timezone

import feedparser
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# -- Config globale --
TIMEOUT    = 8
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS_CHROME = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    # Headers anti-Cloudflare -- imitent un vrai navigateur (v9.2)
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

# -- 70 flux RSS vérifiés 
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
    # Francophone (3)
    "Zataz":                  "https://www.zataz.com/feed/",
    "French Breaches":        "https://frenchbreaches.com/feed.xml",
    "IT-Connect":             "https://www.it-connect.fr/feed/",
    # Gouvernemental & CERTs (4)
    "ANSSI":                  "https://www.cert.ssi.gouv.fr/feed/",
    "CERT-EU":                "https://cert.europa.eu/publications/threat-intelligence-rss",
    "NCSC UK":                "https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml",
    "NCSC NZ":                "https://www.ncsc.govt.nz/rss/all/",
    # Vendors threat research (10)
    "Malwarebytes Labs":      "https://blog.malwarebytes.com/feed/",
    "We Live Security":       "https://www.welivesecurity.com/feed/",
    "Recorded Future Blog":   "https://www.recordedfuture.com/feed",
    "Cybereason":             "https://www.cybereason.com/blog/rss.xml",
    "Unit42 (Palo Alto)":     "https://unit42.paloaltonetworks.com/feed/",
    "Talos Intelligence":     "https://blog.talosintelligence.com/feeds/posts/default/",
    "Microsoft Security":     "https://www.microsoft.com/en-us/security/blog/feed/",
    "Elastic Security":       "https://www.elastic.co/security-labs/rss/feed.xml",
    "SentinelOne":            "https://www.sentinelone.com/blog/feed/",
    "Bitdefender Labs":       "https://www.bitdefender.com/en-us/blog/labs/feed",
    # DFIR & Blue Team (3)
    "The DFIR Report":        "https://thedfirreport.com/feed/",
    "Red Canary":             "https://redcanary.com/blog/feed/",
    "Huntress":               "https://www.huntress.com/blog/rss.xml",
    # Presse tech securite (2)
    "Wired Security":         "https://www.wired.com/feed/category/security/latest/rss",
    "TechCrunch Security":    "https://techcrunch.com/tag/cybersecurity/feed/",
    # OSINT & investigations (5)
    "OSINT Curious":          "https://www.osintcurio.us/feed/",
    "Bellingcat":             "https://www.bellingcat.com/feed/",
    "Intel471":               "https://www.intel471.com/blog/rss.xml",
    "Shodan Blog":            "https://blog.shodan.io/rss/",
    "NixIntel":               "https://nixintel.info/feed/",
    # Threat Intelligence (7)
    "SANS ISC":               "https://isc.sans.edu/rssfeed_full.xml",
    "Mandiant Blog":          "https://www.mandiant.com/resources/blog/rss.xml",
    "CrowdStrike Blog":       "https://www.crowdstrike.com/blog/feed/",
    "Securelist":             "https://securelist.com/feed/",
    "Proofpoint":             "https://www.proofpoint.com/us/rss.xml",
    "Citizen Lab":            "https://citizenlab.ca/feed/",
    "The Intercept":          "https://theintercept.com/feed/?rss",
    # Attribution / Ransomware (3)
    "Cyble Blog":             "https://cyble.com/feed/",
    "Flashpoint Blog":        "https://flashpoint.io/blog/feed/",
    "Security Affairs":       "https://securityaffairs.com/feed",
    # OCCRP investigations (1)
    "OCCRP":                  "https://www.occrp.org/en/feed/articles",
    # Vendors recherche complementaires (5)
    "Check Point Research":   "https://research.checkpoint.com/feed/",
    "Rapid7 Blog":            "https://blog.rapid7.com/rss/",
    "Tenable Blog":           "https://www.tenable.com/blog/feed",
    "Qualys Blog":            "https://blog.qualys.com/feed",
    "ZDI Advisories":         "https://www.zerodayinitiative.com/rss/published/",
    # CERTs internationaux (1)
    "JPCERT Japon":           "https://www.jpcert.or.jp/english/rss/jpcert-en.rdf",
    # Cloud / Big Tech (3)
    "AWS Security Blog":      "https://aws.amazon.com/blogs/security/feed/",
    "GitHub Security":        "https://github.blog/tag/security/feed/",
    "Cloudflare Blog":        "https://blog.cloudflare.com/rss",
    # Law enforcement (1)
    "Europol":                "https://www.europol.europa.eu/rss.xml",
    # Traffic analysis (1)
    "Malware Traffic Analysis": "https://www.malware-traffic-analysis.net/blog-entries.rss",
    # News supplémentaires (3)
    "Heimdal Blog":           "https://heimdalsecurity.com/blog/feed/",
    "Troy Hunt":              "https://troyhunt.com/rss/",
    "IntelligenceX Blog":     "https://blog.intelligencex.org/rss/latest-posts",
    # Supplémentaires (2)
    "UnderNews":              "https://www.undernews.fr/feed",
    "Google Security Blog":   "https://security.googleblog.com/feeds/posts/default",
    # Europe (7)
    "CERT.PL":                "https://cert.pl/en/rss.xml",
    "CERT.LV":                "https://cert.lv/en/feed/rss/all",
    "CERT.at":                "https://cert.at/cert-at.en.blog.rss_2.0.xml",
    "NCSC-FI":                "https://www.kyberturvallisuuskeskus.fi/feed/rss/en",
    "CCN-CERT":               "https://www.ccn-cert.cni.es/en/communication-events/articles-and-reports.rss",
    "Swiss GovCERT":          "https://www.newsd.admin.ch/newsd/feeds/rss?lang=en&org-nr=1101",
    "CERT-BE":                "https://ccb.belgium.be/news.xml",
    # Asie-Pacifique (3)
    "AusCERT":                "https://portal.auscert.org.au/rss/bulletins/",
    "HKCERT":                 "https://www.hkcert.org/getrss/security-bulletin",
    "JPCERT Blog":            "https://blogs.jpcert.or.jp/en/atom.xml",
    # Amérique du Nord (1)
    "Canadian Cyber Centre":  "https://cyber.gc.ca/webservice/en/rss/news",
}


def _row(source, title, description, url, published_at):
    # Format standard pour chaque article collecté
    return {
        "source":       source,
        "title":        title or "",
        "description":  (description or "")[:500],
        "url":          str(url).strip() if url and str(url).lower() != "nan" else "",
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
            "https://otx.alienvault.com/api/v1/pulses/activity",
            headers={"X-OTX-API-KEY": key, **HEADERS_CHROME},
            params={"limit": 50, "page": 1},
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
# 3. NVD / NIST -- avec filtre temporel + retry x3 (v9.2)
# ---------------------------------------------------
def collect_nvd():
    headers = {**HEADERS_CHROME, "Accept": "application/json"}
    key = os.getenv("NVD_API_KEY")
    if key:
        headers["apiKey"] = key

    # Filtre temporel obligatoire -- NVD rejette les requêtes sans borne temporelle
    pub_end   = datetime.now(timezone.utc)
    pub_start = pub_end - timedelta(days=7)

    params = {
        "resultsPerPage": 20,
        # Format NVD : YYYY-MM-DDTHH:MM:SS.000
        "pubStartDate":   pub_start.strftime("%Y-%m-%dT%H:%M:%S.000"),
        "pubEndDate":     pub_end.strftime("%Y-%m-%dT%H:%M:%S.000"),
    }

    # Retry x3 avec backoff -- NVD a des 404/503/429 sporadiques documentés
    # Rate limit : 5 req/30s sans clé, 50 req/30s avec clé -> backoff 6s
    r = None
    for attempt in range(1, 4):
        try:
            r = requests.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0",
                headers=headers, params=params, timeout=30,
            )
            if r.status_code == 200:
                break
            if r.status_code in (403, 404, 429, 503):
                log.warning("NVD tentative %d/3 : HTTP %d -- backoff 6s", attempt, r.status_code)
                time.sleep(6)
                continue
            r.raise_for_status()
        except requests.exceptions.Timeout:
            log.warning("NVD tentative %d/3 : timeout", attempt)
            time.sleep(6)
        except Exception as e:
            log.warning("NVD tentative %d/3 : %s", attempt, e)
            time.sleep(6)
    else:
        log.error("NVD : 3 tentatives échouées, skip")
        return []

    if r is None or r.status_code != 200:
        log.error("NVD : réponse invalide après retry, skip")
        return []

    try:
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

        log.info("NVD : %d CVE (fenêtre 7j)", len(articles))
        return articles

    except Exception as e:
        log.error("NVD parsing : %s", e)
        return []


# ---------------------------------------------------
# 4. RANSOMWARE.LIVE
# ---------------------------------------------------
def collect_ransomware_live():
    try:
        r = requests.get(
            "https://api.ransomware.live/v2/recentvictims",
            headers=HEADERS_CHROME,
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()

        articles = []
        for v in data[:200]:
            group   = v.get("group_name", "unknown")
            victim  = v.get("victim", "")
            country = v.get("country", "")
            date    = v.get("discovered", "") or v.get("published", "")
            url     = v.get("post_url") or v.get("website", "") or ""

            title = f"{group} ransomware attack on {victim}"
            if country:
                title += f" ({country})"

            desc = f"Ransomware group {group} claimed attack on {victim}."
            if country:
                desc += f" Victim located in {country}."

            articles.append(_row("Ransomware.live", title, desc, url, date))

        log.info("Ransomware.live : %d victimes", len(articles))
        return articles

    except Exception as e:
        log.error("Ransomware.live : %s", e)
        return []


# ---------------------------------------------------
# 5. THREATFOX
# ---------------------------------------------------
def collect_threatfox():
    key = os.getenv("ABUSECH_AUTH_KEY")
    if not key:
        log.info("ABUSECH_AUTH_KEY absente -- skip ThreatFox")
        return []

    try:
        r = requests.post(
            "https://threatfox-api.abuse.ch/api/v1/",
            headers={"Auth-Key": key, **HEADERS_CHROME},
            json={"query": "get_iocs", "days": 1},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()

        if data.get("query_status") != "ok":
            log.warning("ThreatFox : status %s", data.get("query_status"))
            return []

        articles = []
        seen = set()
        for ioc in data.get("data", [])[:150]:
            family  = ioc.get("malware_printable", "")
            ioc_val = ioc.get("ioc", "")
            tags    = ", ".join(ioc.get("tags", []) or [])
            threat  = ioc.get("threat_type_desc", "")
            date    = ioc.get("first_seen_utc", "")

            dedup_key = f"{family}_{threat}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            title = f"{family} -- {threat}" if threat else family
            desc  = f"Malware family: {family}. IOC: {ioc_val}. Tags: {tags}"

            articles.append(_row(
                "ThreatFox", title, desc,
                f"https://threatfox.abuse.ch/ioc/{ioc.get('id', '')}",
                date,
            ))

        log.info("ThreatFox : %d familles", len(articles))
        return articles

    except Exception as e:
        log.error("ThreatFox : %s", e)
        return []


# ---------------------------------------------------
# 6. URLHAUS
# ---------------------------------------------------
def collect_urlhaus():
    key = os.getenv("ABUSECH_AUTH_KEY")
    if not key:
        log.info("ABUSECH_AUTH_KEY absente -- skip URLhaus")
        return []

    try:
        r = requests.get(
            "https://urlhaus-api.abuse.ch/v1/urls/recent/limit/100/",
            headers={"Auth-Key": key, **HEADERS_CHROME},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()

        articles = []
        seen = set()
        for u in data.get("urls", [])[:100]:
            threat = u.get("threat", "") or "malware"
            tags   = ", ".join(u.get("tags", []) or [])
            url_v  = u.get("url", "")
            date   = u.get("date_added", "")

            dedup_key = f"{threat}_{tags}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            title = f"Malicious URL distributing {threat}"
            if tags:
                title += f" ({tags})"
            desc = f"URLhaus: malicious URL distributing {threat}. Tags: {tags}. URL: {url_v[:100]}"

            articles.append(_row(
                "URLhaus", title, desc,
                f"https://urlhaus.abuse.ch/url/{u.get('id', '')}",
                date,
            ))

        log.info("URLhaus : %d URLs", len(articles))
        return articles

    except Exception as e:
        log.error("URLhaus : %s", e)
        return []


# ---------------------------------------------------
# 7. MALWAREBAZAAR
# ---------------------------------------------------
def collect_malwarebazaar():
    key = os.getenv("ABUSECH_AUTH_KEY")
    if not key:
        log.info("ABUSECH_AUTH_KEY absente -- skip MalwareBazaar")
        return []

    try:
        r = requests.post(
            "https://mb-api.abuse.ch/api/v1/",
            headers={"Auth-Key": key, **HEADERS_CHROME},
            data={"query": "get_recent", "selector": "time"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()

        if data.get("query_status") != "ok":
            log.warning("MalwareBazaar : status %s", data.get("query_status"))
            return []

        articles = []
        seen = set()
        for s in data.get("data", [])[:100]:
            family = s.get("signature", "") or "unknown"
            ftype  = s.get("file_type", "")
            tags   = ", ".join(s.get("tags", []) or [])
            date   = s.get("first_seen", "")
            sha    = s.get("sha256_hash", "")[:16]

            if family in seen:
                continue
            seen.add(family)

            title = f"{family} malware sample detected ({ftype})"
            desc  = f"MalwareBazaar: {family} ({ftype}). Tags: {tags}. SHA256: {sha}..."

            articles.append(_row(
                "MalwareBazaar", title, desc,
                f"https://bazaar.abuse.ch/sample/{s.get('sha256_hash', '')}",
                date,
            ))

        log.info("MalwareBazaar : %d familles", len(articles))
        return articles

    except Exception as e:
        log.error("MalwareBazaar : %s", e)
        return []


# ---------------------------------------------------
# 8. FLUX RSS -- logging détaillé par flux (v9.2)
# ---------------------------------------------------
def collect_rss():
    articles  = []
    ok_count  = 0
    ko_list   = []   # [(nom, motif)] -- pour récap à la fin

    for name, url in RSS_FEEDS.items():
        feed    = None
        err_msg = None

        # Etape 1 : requests + UA Chrome (evite les blocages anti-bot)
        try:
            r = requests.get(url, headers=HEADERS_CHROME, timeout=TIMEOUT)
            if r.status_code >= 400:
                err_msg = f"HTTP {r.status_code}"
            else:
                feed = feedparser.parse(r.content)
        except requests.exceptions.Timeout:
            err_msg = "timeout"
        except requests.exceptions.ConnectionError:
            err_msg = "connection_refused"
        except Exception as e:
            err_msg = type(e).__name__

        # Etape 2 : feedparser direct en fallback (si etape 1 KO ou 0 entrées)
        if not feed or len(feed.entries) == 0:
            try:
                feed = feedparser.parse(url)
            except Exception as e:
                motif = err_msg or type(e).__name__
                log.warning("RSS EXCEPTION : %-30s -> %s", name, motif)
                ko_list.append((name, motif))
                continue

        # Diagnostic final : 3 cas distincts pour logs actionnables
        # Cas 1 : XML malformé ET 0 entries -> flux cassé
        if feed.bozo and feed.bozo_exception and len(feed.entries) == 0:
            motif = type(feed.bozo_exception).__name__
            log.warning("RSS KO       : %-30s -> %s", name, motif)
            ko_list.append((name, motif))
            continue

        # Cas 2 : parsing OK mais 0 entries -> flux réellement vide
        if len(feed.entries) == 0:
            motif = err_msg or "0_entries"
            log.warning("RSS VIDE     : %-30s -> %s", name, motif)
            ko_list.append((name, motif))
            continue

        # Cas 3 : entries présentes -> on prend (même si bozo True avec warnings mineurs)
        entries = [
            _row(name, e.get("title"), e.get("summary"), e.get("link"), e.get("published"))
            for e in feed.entries
        ]
        articles.extend(entries)
        ok_count += 1

    log.info("RSS : %d sources OK / %d erreurs ou vides", ok_count, len(ko_list))

    # Récapitulatif des KO (utile pour décider quoi retirer / corriger)
    if ko_list:
        log.info("RSS KO détail (%d flux) :", len(ko_list))
        for name, motif in ko_list:
            log.info("  - %-30s : %s", name, motif)

    return articles


# ---------------------------------------------------
# 9. SAUVEGARDE CSV
# ---------------------------------------------------
def _save_to_csv(articles):
    if not articles:
        log.warning("Aucun article a sauvegarder")
        return None

    today    = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(OUTPUT_DIR, f"articles_{today}.csv")
    df       = pd.DataFrame(articles)

    if os.path.exists(filepath):
        df.to_csv(filepath, mode="a", header=False, index=False, encoding="utf-8")
    else:
        df.to_csv(filepath, index=False, encoding="utf-8")

    log.info("Sauvegarde : %d articles -> %s", len(df), filepath)
    return filepath


# ---------------------------------------------------
# 10. ORCHESTRATION
# ---------------------------------------------------
def main():
    log.info("=" * 50)
    log.info("StatCyberMatrix -- Collecte S6 -- %d sources", 7 + len(RSS_FEEDS))
    log.info("=" * 50)

    all_articles = (
        collect_newsapi()
        + collect_otx()
        + collect_nvd()
        + collect_ransomware_live()
        + collect_threatfox()
        + collect_urlhaus()
        + collect_malwarebazaar()
        + collect_rss()
    )

    n_sources = len({a["source"] for a in all_articles})
    log.info("Total : %d articles / %d sources actives", len(all_articles), n_sources)

    filepath = _save_to_csv(all_articles)
    return filepath


if __name__ == "__main__":
    main()