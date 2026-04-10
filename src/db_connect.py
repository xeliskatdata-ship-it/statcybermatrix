# v2 sidebar counts
# db_connect.py -- Connexion PostgreSQL partagee entre toutes les pages KPI
# Cache TTL 120s via @st.cache_data -- force_refresh() vide tout
# Dual mode : st.secrets (Streamlit Cloud) ou .env (Docker local)

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# -- Connexion dual Cloud / Local
if "postgres" in st.secrets:
    s = st.secrets["postgres"]
    DATABASE_URL = (
        f"postgresql+psycopg2://{s['user']}:{s['password']}"
        f"@{s['host']}:{s.get('port', 5432)}/{s['dbname']}"
        f"?sslmode={s.get('sslmode', 'require')}"
    )
else:
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
    return create_engine(DATABASE_URL, pool_pre_ping=True)


# -- Helper pour eviter la repetition query → df → cast date --
def _query(sql, date_cols=None):
    with get_engine().connect() as conn:
        df = pd.read_sql(text(sql), conn)
    for col in (date_cols or []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


@st.cache_data(ttl=120)
def get_mart_k1():
    return _query("""
        SELECT published_date, source, nb_articles
        FROM mart_k1
        WHERE published_date IS NOT NULL
        ORDER BY published_date DESC
    """, date_cols=["published_date"])


@st.cache_data(ttl=120)
def get_mart_k2():
    return _query("""
        SELECT keyword, category, sub_category,
               period_days, occurrences, article_count, source_count
        FROM mart_k2
        ORDER BY period_days, occurrences DESC
    """)


@st.cache_data(ttl=120)
def get_stg_articles(keyword=None, limit=2000):
    base = """
        SELECT source, title, description, url,
               published_date, category, content_length
        FROM stg_articles
        WHERE published_date IS NOT NULL
    """
    if keyword:
        sql = base + """
              AND (LOWER(title) LIKE :kw OR LOWER(description) LIKE :kw)
            ORDER BY published_date DESC LIMIT :limit
        """
        params = {"kw": f"%{keyword.lower()}%", "limit": limit}
    else:
        sql = base + " ORDER BY published_date DESC LIMIT :limit"
        params = {"limit": limit}

    with get_engine().connect() as conn:
        df = pd.read_sql(text(sql), conn, params=params)
    df["published_date"] = pd.to_datetime(df["published_date"])
    return df


@st.cache_data(ttl=120)
def get_articles_by_keyword(keyword, period_days=7):
    # Utilisee par KPI2 au clic sur une bulle du scatter
    sql = """
        SELECT title, source, url, published_date, category
        FROM stg_articles
        WHERE published_date >= NOW() - INTERVAL '1 day' * :days
          AND (LOWER(title) LIKE :kw OR LOWER(description) LIKE :kw)
        ORDER BY published_date DESC
        LIMIT 50
    """
    with get_engine().connect() as conn:
        df = pd.read_sql(text(sql), conn, params={
            "days": period_days, "kw": f"%{keyword.lower()}%",
        })
    df["published_date"] = pd.to_datetime(df["published_date"])
    return df


@st.cache_data(ttl=120)
def get_mart_k3():
    return _query("""
        SELECT category, source, nb_articles
        FROM mart_k3
        ORDER BY category, nb_articles DESC
    """)


@st.cache_data(ttl=120)
def get_mart_k4():
    return _query("""
        SELECT published_date, category, nb_mentions
        FROM mart_k4
        ORDER BY published_date DESC, nb_mentions DESC
    """, date_cols=["published_date"])


@st.cache_data(ttl=120)
def get_mart_k5():
    return _query("""
        SELECT semaine, category, nb_alertes
        FROM mart_k5
        ORDER BY semaine DESC, nb_alertes DESC
    """, date_cols=["semaine"])


@st.cache_data(ttl=120)
def get_mart_k6():
    return _query("""
        SELECT cve, nb_mentions
        FROM mart_k6
        ORDER BY nb_mentions DESC
    """)

@st.cache_data(ttl=120)
def get_sidebar_counts():
    with get_engine().connect() as conn:
        counts = {}
        for key, sql in [
            ("k1", "SELECT COALESCE(SUM(nb_articles),0) FROM mart_k1"),
            ("k2", "SELECT COUNT(*) FROM mart_k2 WHERE period_days=7 AND occurrences>0"),
            ("k3", "SELECT COUNT(DISTINCT category) FROM mart_k3"),
            ("k5", "SELECT COALESCE(SUM(nb_alertes),0) FROM mart_k5"),
            ("k6", "SELECT COUNT(*) FROM mart_k6"),
        ]:
            try:
                counts[key] = conn.execute(text(sql)).scalar()
            except Exception:
                pass
    return counts

def force_refresh():
    # Vide le cache Streamlit -- force rechargement depuis PostgreSQL
    for fn in (get_mart_k1, get_mart_k2, get_mart_k3, get_mart_k4,
               get_mart_k5, get_mart_k6, get_stg_articles,
               get_articles_by_keyword, get_sidebar_counts):
        fn.clear()
