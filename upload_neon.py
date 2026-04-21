# upload_neon.py -- Upload raw_articles.csv vers Neon via COPY
# Credentials lus depuis .env (jamais en dur dans le code)

import os
import logging

import psycopg2
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# -- Lecture credentials depuis .env (ou variables d'env GitHub Actions) --
NEON_HOST     = os.getenv("NEON_HOST")
NEON_DBNAME   = os.getenv("NEON_DBNAME")
NEON_USER     = os.getenv("NEON_USER")
NEON_PASSWORD = os.getenv("NEON_PASSWORD")

# Garde-fou : on refuse de tourner si une variable manque
_required = {"NEON_HOST": NEON_HOST, "NEON_DBNAME": NEON_DBNAME,
             "NEON_USER": NEON_USER, "NEON_PASSWORD": NEON_PASSWORD}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    raise EnvironmentError(
        f"Variables d'environnement manquantes : {', '.join(_missing)}\n"
        "Verifier le fichier .env (local) ou les secrets GitHub Actions (CI)."
    )

conn = psycopg2.connect(
    host=NEON_HOST,
    dbname=NEON_DBNAME,
    user=NEON_USER,
    password=NEON_PASSWORD,
    sslmode="require",
)
cur = conn.cursor()

with open("raw_articles.csv", "r", encoding="utf-8") as f:
    # COPY est le plus rapide (bulk load natif PostgreSQL)
    cur.copy_expert("COPY raw_articles FROM STDIN WITH CSV HEADER", f)

conn.commit()
cur.execute("SELECT COUNT(*) FROM raw_articles")
log.info("Lignes importees sur Neon : %d", cur.fetchone()[0])
cur.close()
conn.close()