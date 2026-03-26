"""
CyberPulse — load_to_db.py
Charge les CSV (raw + cleaned) dans PostgreSQL via SQLAlchemy.
Usage : python db/load_to_db.py
"""

import os
import glob
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from datetime import datetime

# ──────────────────────────────────────────────
# 1. Connexion a PostgreSQL
# ──────────────────────────────────────────────

load_dotenv()

DB_USER     = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME     = os.getenv("POSTGRES_DB")
DB_HOST     = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT     = os.getenv("POSTGRES_PORT", "5432")

_MISSING = [
    name for name, val in {
        "POSTGRES_USER":     DB_USER,
        "POSTGRES_PASSWORD": DB_PASSWORD,
        "POSTGRES_DB":       DB_NAME,
    }.items()
    if not val
]
if _MISSING:
    raise EnvironmentError(
        f"Variables d'environnement manquantes : {', '.join(_MISSING)}\n"
        "Ajoutez-les dans docker-compose.yml sous les services "
        "airflow-webserver et airflow-scheduler :\n"
        "  environment:\n"
        "    - POSTGRES_USER=...\n"
        "    - POSTGRES_PASSWORD=...\n"
        "    - POSTGRES_DB=...\n"
        "    - POSTGRES_HOST=postgres\n"
        "Puis relancez : docker compose down && docker compose up -d"
    )

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def get_engine():
    """Cree et retourne le moteur SQLAlchemy."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Connexion PostgreSQL OK")
        return engine
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        print("Verifiez que Docker tourne : docker compose up -d")
        raise


# ──────────────────────────────────────────────
# 2. Chargement raw_articles
# ──────────────────────────────────────────────

RAW_COLS = ["source", "title", "description", "url", "published_at", "collected_at"]

def load_raw(engine):
    """
    Charge tous les CSV de data/raw/ dans la table raw_articles.
    ON CONFLICT (url) DO NOTHING evite les doublons sur URL.
    """
    files = glob.glob("data/raw/articles_*.csv")

    if not files:
        print("Aucun fichier trouve dans data/raw/")
        return

    total_inserted = 0
    total_skipped  = 0

    for filepath in sorted(files):
        print(f"Fichier raw : {filepath}")

        df = pd.read_csv(filepath, usecols=lambda c: c in RAW_COLS)

        for col in RAW_COLS:
            if col not in df.columns:
                df[col] = None

        df = df[RAW_COLS]
        inserted = 0
        skipped  = 0

        with engine.begin() as conn:
            for _, row in df.iterrows():
                try:
                    conn.execute(
                        text("""
                            INSERT INTO raw_articles
                                (source, title, description, url, published_at, collected_at)
                            VALUES
                                (:source, :title, :description, :url, :published_at, :collected_at)
                            ON CONFLICT (url) DO NOTHING
                        """),
                        row.to_dict()
                    )
                    inserted += 1
                except Exception:
                    skipped += 1

        print(f"  Inserees : {inserted}  |  Ignorees : {skipped}")
        total_inserted += inserted
        total_skipped  += skipped

    print(f"raw_articles -- Total : {total_inserted} inserees, {total_skipped} ignorees")


# ──────────────────────────────────────────────
# 3. Chargement stg_articles
# ──────────────────────────────────────────────

STG_COLS = [
    "source", "title", "description", "url",
    "published_at", "collected_at",
    "published_date", "content_length", "category"
]

def load_stg(engine):
    """
    Charge tous les CSV de data/cleaned/ dans stg_articles.
    WHERE NOT EXISTS (title, source) evite les doublons.
    """
    files = glob.glob("data/cleaned/articles_cleaned_*.csv")

    if not files:
        print("Aucun fichier trouve dans data/cleaned/")
        return

    total_inserted = 0
    total_skipped  = 0

    for filepath in sorted(files):
        print(f"Fichier cleaned : {filepath}")

        df = pd.read_csv(filepath, usecols=lambda c: c in STG_COLS)

        for col in STG_COLS:
            if col not in df.columns:
                df[col] = None

        df = df[STG_COLS]

        df["content_length"] = pd.to_numeric(df["content_length"], errors="coerce")
        df["published_date"] = pd.to_datetime(
            df["published_date"], errors="coerce"
        ).dt.date

        df = df.where(pd.notnull(df), None)

        inserted = 0
        skipped  = 0

        with engine.begin() as conn:
            for _, row in df.iterrows():
                try:
                    conn.execute(
                        text("""
                            INSERT INTO stg_articles
                                (source, title, description, url,
                                 published_at, collected_at,
                                 published_date, content_length, category)
                            SELECT
                                :source, :title, :description, :url,
                                :published_at, :collected_at,
                                :published_date, :content_length, :category
                            WHERE NOT EXISTS (
                                SELECT 1 FROM stg_articles
                                WHERE title = :title AND source = :source
                            )
                        """),
                        row.to_dict()
                    )
                    inserted += 1
                except Exception as e:
                    print(f"  Erreur ligne : {e}")
                    skipped += 1

        print(f"  Inserees : {inserted}  |  Ignorees (doublons) : {skipped}")
        total_inserted += inserted
        total_skipped  += skipped

    print(f"stg_articles -- Total : {total_inserted} inserees, {total_skipped} ignorees")


# ──────────────────────────────────────────────
# 4. Verification finale
# ──────────────────────────────────────────────

def check_counts(engine):
    """Affiche le nombre de lignes dans chaque table."""
    print("\n" + "-" * 45)
    print("Etat de la base apres chargement :")
    print("-" * 45)

    with engine.connect() as conn:
        for table in ["raw_articles", "stg_articles", "mart_kpis"]:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table:<20} : {count} lignes")
            except Exception:
                print(f"  {table:<20} : table non trouvee")

    print("-" * 45)

def main():
    print("=" * 45)
    print("CyberPulse -- Chargement en base")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 45)

    engine = get_engine()
    load_raw(engine)
    load_stg(engine)
    check_counts(engine)

    print("\nChargement termine.")


# ──────────────────────────────────────────────
# 5. Main
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 45)
    print("CyberPulse -- Chargement en base")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 45)

    engine = get_engine()
    load_raw(engine)
    load_stg(engine)
    check_counts(engine)

    print("\nChargement termine.")