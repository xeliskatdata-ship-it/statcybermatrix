"""
CyberPulse -- db_connect.py
Connexion PostgreSQL partagee entre toutes les pages KPI.
"""

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER     = os.getenv("POSTGRES_USER",     "cyberpulse")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cyberpulse123")
DB_NAME     = os.getenv("POSTGRES_DB",       "cyberpulse_db")
DB_HOST     = os.getenv("POSTGRES_HOST",     "localhost")
DB_PORT     = os.getenv("POSTGRES_PORT",     "5432")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


@st.cache_resource
def get_engine():
    """Cree le moteur SQLAlchemy (singleton, partage entre reruns)."""
    return create_engine(DATABASE_URL, pool_pre_ping=True)


@st.cache_data(ttl=120)
def get_mart_k1() -> pd.DataFrame:
    engine = get_engine()
    query = text("""
        SELECT published_date, source, nb_articles
        FROM mart_k1
        WHERE published_date IS NOT NULL
        ORDER BY published_date DESC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    df["published_date"] = pd.to_datetime(df["published_date"])
    return df


@st.cache_data(ttl=120)
def get_mart_k2() -> pd.DataFrame:
    """
    Charge mart_k2 depuis PostgreSQL.
    Colonnes : keyword, category, sub_category,
               period_days, occurrences, article_count, source_count
    """
    engine = get_engine()
    query = text("""
        SELECT
            keyword, category, sub_category,
            period_days, occurrences, article_count, source_count
        FROM mart_k2
        ORDER BY period_days, occurrences DESC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


@st.cache_data(ttl=120)
def get_stg_articles(keyword: str = None, limit: int = 2000) -> pd.DataFrame:
    engine = get_engine()
    if keyword:
        query = text("""
            SELECT
                source, title, description, url,
                published_date, category, content_length
            FROM stg_articles
            WHERE published_date IS NOT NULL
              AND (
                LOWER(title)          LIKE :kw
                OR LOWER(description) LIKE :kw
              )
            ORDER BY published_date DESC
            LIMIT :limit
        """)
        params = {"kw": f"%{keyword.lower()}%", "limit": limit}
    else:
        query = text("""
            SELECT
                source, title, description, url,
                published_date, category, content_length
            FROM stg_articles
            WHERE published_date IS NOT NULL
            ORDER BY published_date DESC
            LIMIT :limit
        """)
        params = {"limit": limit}
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=params)
    df["published_date"] = pd.to_datetime(df["published_date"])
    return df


@st.cache_data(ttl=120)
def get_articles_by_keyword(keyword: str, period_days: int = 7) -> pd.DataFrame:
    """
    Retourne les articles de stg_articles mentionnant le mot-cle
    dans le titre ou la description, sur la periode demandee.
    Utilisee par KPI 2 au clic sur une bulle du scatter.
    """
    engine = get_engine()
    query = text("""
        SELECT title, source, url, published_date, category
        FROM stg_articles
        WHERE published_date >= NOW() - INTERVAL '1 day' * :days
          AND (
            LOWER(title)          LIKE :kw
            OR LOWER(description) LIKE :kw
          )
        ORDER BY published_date DESC
        LIMIT 50
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={
            "days": period_days,
            "kw":   f"%{keyword.lower()}%",
        })
    df["published_date"] = pd.to_datetime(df["published_date"])
    return df


@st.cache_data(ttl=120)
def get_mart_k3() -> pd.DataFrame:
    engine = get_engine()
    query = text("""
        SELECT category, source, nb_articles
        FROM mart_k3
        ORDER BY category, nb_articles DESC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


@st.cache_data(ttl=120)
def get_mart_k4() -> pd.DataFrame:
    engine = get_engine()
    query = text("""
        SELECT published_date, category, nb_mentions
        FROM mart_k4
        ORDER BY published_date DESC, nb_mentions DESC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    df["published_date"] = pd.to_datetime(df["published_date"])
    return df


@st.cache_data(ttl=120)
def get_mart_k5() -> pd.DataFrame:
    engine = get_engine()
    query = text("""
        SELECT semaine, category, nb_alertes
        FROM mart_k5
        ORDER BY semaine DESC, nb_alertes DESC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    df["semaine"] = pd.to_datetime(df["semaine"])
    return df


@st.cache_data(ttl=120)
def get_mart_k6() -> pd.DataFrame:
    engine = get_engine()
    query = text("""
        SELECT cve, nb_mentions
        FROM mart_k6
        ORDER BY nb_mentions DESC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


def force_refresh():
    """Vide le cache et force le rechargement depuis PostgreSQL."""
    get_mart_k1.clear()
    get_mart_k2.clear()
    get_mart_k3.clear()
    get_mart_k4.clear()
    get_mart_k5.clear()
    get_mart_k6.clear()
    get_stg_articles.clear()
    get_articles_by_keyword.clear()
    