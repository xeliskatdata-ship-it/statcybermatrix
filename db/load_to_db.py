# load_to_db.py -- Charge les CSV raw dans PostgreSQL
# Usage : python db/load_to_db.py
# Seule raw_articles est alimentee ici — stg + mart sont geres par dbt

import glob
import logging
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# -- Connexion PostgreSQL --
DB_USER     = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME     = os.getenv("POSTGRES_DB")
DB_HOST     = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT     = os.getenv("POSTGRES_PORT", "5432")

_MISSING = [k for k, v in {
    "POSTGRES_USER": DB_USER, "POSTGRES_PASSWORD": DB_PASSWORD, "POSTGRES_DB": DB_NAME,
}.items() if not v]

if _MISSING:
    raise EnvironmentError(
        f"Variables manquantes : {', '.join(_MISSING)}\n"
        "Ajoutez-les dans docker-compose.yml (services airflow + streamlit)."
    )

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"


def _get_engine():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    log.info("Connexion PostgreSQL OK (%s:%s/%s)", DB_HOST, DB_PORT, DB_NAME)
    return engine


# ---------------------------------------------------
# 1. RAW ARTICLES
# ---------------------------------------------------
RAW_COLS = ["source", "title", "description", "url", "published_at", "collected_at"]


def _load_raw(engine):
    files = glob.glob("data/raw/articles_*.csv")
    if not files:
        log.warning("Aucun fichier dans data/raw/")
        return

    total_ins = total_skip = 0

    for fp in sorted(files):
        df = pd.read_csv(fp, usecols=lambda c: c in RAW_COLS)
        for col in RAW_COLS:
            if col not in df.columns:
                df[col] = None
        df = df[RAW_COLS]

        # Nettoyer les NaN AVANT tout INSERT (Ransomware.live envoie url=NaN) -> indispensable, cela m'a bloqué lors du chargement dans streamlit
        df = df.fillna('')

        # Dedup intra-fichier : sur (source, title) pour ne pas perdre les articles sans URL
        df = df.drop_duplicates(subset=["source", "title"], keep="first")

        ins = skip = 0
        with engine.begin() as conn:
            for _, row in df.iterrows():
                try:
                    # Dedup : url si present, sinon (source, title)
                    if row['url'] and row['url'].strip():
                        conn.execute(text("""
                            INSERT INTO raw_articles
                                (source, title, description, url, published_at, collected_at)
                            SELECT
                                :source, :title, :description, :url, :published_at, :collected_at
                            WHERE NOT EXISTS (
                                SELECT 1 FROM raw_articles
                                WHERE url = :url
                            )
                        """), row.to_dict())
                    else:
                        # Articles sans URL : dedup sur (source, title)
                        conn.execute(text("""
                            INSERT INTO raw_articles
                                (source, title, description, url, published_at, collected_at)
                            SELECT
                                :source, :title, :description, :url, :published_at, :collected_at
                            WHERE NOT EXISTS (
                                SELECT 1 FROM raw_articles
                                WHERE source = :source AND title = :title
                            )
                        """), row.to_dict())
                    ins += 1
                except Exception as e:
                    if skip == 0:
                        log.error("Premiere erreur INSERT : %s", e)
                    skip += 1

        log.info("raw  | %s : %d inserees / %d ignorees", os.path.basename(fp), ins, skip)
        total_ins  += ins
        total_skip += skip

    log.info("raw_articles total : %d inserees / %d ignorees", total_ins, total_skip)


# ---------------------------------------------------
# 2. VERIFICATION
# ---------------------------------------------------
def _check_counts(engine):
    log.info("-" * 40)
    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM raw_articles")).scalar()
        log.info("  %-20s : %d lignes", "raw_articles", n)

        for name in ("stg_articles", "mart_k1", "mart_k3", "mart_k6"):
            try:
                n = conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar()
                log.info("  %-20s : %d lignes", name, n)
            except Exception:
                log.info("  %-20s : pas encore cree (lance dbt run)", name)
    log.info("-" * 40)


# ---------------------------------------------------
# ORCHESTRATION
# ---------------------------------------------------
def main():
    log.info("=" * 40)
    log.info("CyberPulse -- Chargement en base (raw uniquement)")
    log.info("=" * 40)

    engine = _get_engine()
    _load_raw(engine)
    _check_counts(engine)

    log.info("Chargement termine.")


if __name__ == "__main__":
    main()
