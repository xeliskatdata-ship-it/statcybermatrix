# scripts/check_feeds.py
# Diagnostic rapide des 100 flux RSS : test en parallèle + rapport CSV
# Usage : python scripts/check_feeds.py

import sys
import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from acquisition import RSS_FEEDS, HEADERS_CHROME

OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "feeds_diagnostic.csv")
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)


def check_feed(name, url):
    # Test 1 requête, analyse du retour
    try:
        r = requests.get(url, headers=HEADERS_CHROME, timeout=10, allow_redirects=True)
        status   = r.status_code
        ctype    = r.headers.get("Content-Type", "").split(";")[0].strip()
        size     = len(r.content)
        final    = r.url if r.url != url else ""

        # Diagnostic
        if status == 404:
            verdict = "URL_MORTE"
        elif status in (403, 406):
            verdict = "ANTI_BOT"
        elif status >= 500:
            verdict = "SERVEUR_KO"
        elif "html" in ctype.lower() and "xml" not in ctype.lower():
            verdict = "HTML_AU_LIEU_XML"
        elif status == 200 and size < 200:
            verdict = "VIDE"
        elif status == 200 and ("xml" in ctype.lower() or b"<rss" in r.content[:500] or b"<feed" in r.content[:500]):
            verdict = "OK"
        elif final and final != url:
            verdict = "REDIRECTION"
        else:
            verdict = f"AUTRE_{ctype}"

        return (name, url, status, ctype, size, final, verdict)

    except requests.exceptions.Timeout:
        return (name, url, 0, "", 0, "", "TIMEOUT")
    except requests.exceptions.ConnectionError:
        return (name, url, 0, "", 0, "", "DNS_KO")
    except Exception as e:
        return (name, url, 0, "", 0, "", f"ERR_{type(e).__name__}")


def main():
    print(f"Test de {len(RSS_FEEDS)} flux RSS en parallèle...\n")

    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(check_feed, name, url): name for name, url in RSS_FEEDS.items()}
        for future in as_completed(futures):
            results.append(future.result())

    # Tri par verdict puis par nom
    results.sort(key=lambda x: (x[6], x[0]))

    # Écriture CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "url", "status", "content_type", "size", "final_url", "verdict"])
        writer.writerows(results)

    # Synthèse écran
    verdicts = {}
    for r in results:
        v = r[6]
        verdicts[v] = verdicts.get(v, 0) + 1

    print(f"{'Verdict':<20} {'Nombre':>6}")
    print("-" * 30)
    for v, n in sorted(verdicts.items(), key=lambda x: -x[1]):
        print(f"{v:<20} {n:>6}")

    print(f"\nDétail complet : {OUTPUT_CSV}")


if __name__ == "__main__":
    main()