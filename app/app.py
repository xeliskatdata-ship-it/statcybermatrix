"""
CyberPulse -- app.py
Dashboard Streamlit -- Page d'accueil
Charge les metriques directement depuis PostgreSQL via db_connect.
"""

import streamlit as st
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from db_connect import get_mart_k1, get_mart_k3, get_stg_articles, force_refresh
from utils_lang import t

# ---------------------------------------------------
# CONFIGURATION PAGE
# ---------------------------------------------------
st.set_page_config(
    page_title="CyberPulse",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# STYLE
# ---------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #0a0e1a; }
[data-testid="stSidebar"] {
    background: #0f1422 !important;
    border-right: 1px solid #1e2a42;
}
[data-testid="stSidebar"] * { color: #a8b8d0 !important; }
.metric-card {
    background: #0f1422;
    border: 1px solid #1e2a42;
    border-radius: 8px;
    padding: 18px 22px;
    position: relative;
    overflow: hidden;
}
.metric-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: #3b82f6;
}
.metric-card.green::after  { background: #22c55e; }
.metric-card.orange::after { background: #f59e0b; }
.metric-card.red::after    { background: #ef4444; }
.metric-card.teal::after   { background: #14b8a6; }
.metric-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem; font-weight: 700; color: #e2e8f0;
}
.metric-lbl { font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }
.metric-sub { font-size: 0.8rem; color: #22c55e; margin-top: 6px; }
.section-tag {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem; letter-spacing: 0.15em; text-transform: uppercase;
    color: #3b82f6; background: rgba(59,130,246,0.1);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 4px; padding: 3px 10px; margin-bottom: 14px;
}
.banner {
    background: linear-gradient(135deg, #0f1422 0%, #111827 60%, #0d1b2a 100%);
    border: 1px solid #1e2a42; border-radius: 12px;
    padding: 32px 36px; margin-bottom: 28px;
}
.banner-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.2rem; font-weight: 700; color: #e2e8f0;
}
.banner-sub { font-size: 0.95rem; color: #64748b; margin-top: 6px; }
.live-dot {
    display: inline-block; width: 7px; height: 7px;
    background: #22c55e; border-radius: 50%; margin-right: 7px;
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
with st.sidebar:
    st.markdown(
        "<div style='padding:12px 0 8px 0;text-align:center'>"
        "<img src='https://raw.githubusercontent.com/twitter/twemoji/master/assets/svg/1f6e1.svg' "
        "style='width:90%;max-width:200px;border-radius:10px;margin-bottom:6px'>"
        "<div style='font-size:0.68rem;color:#64748b;letter-spacing:.08em'>"
        "Veille cyber automatisee</div>"
        "</div>",
        unsafe_allow_html=True
    )
    st.divider()

    lang_choice = st.selectbox(
        t("Language", "en"),
        options=["English", "Francais"],
        index=0,
        key="lang_select"
    )
    lang = "fr" if lang_choice == "Francais" else "en"
    st.session_state['lang'] = lang

    st.divider()

    if st.button("Rafraichir les donnees", key="home_refresh"):
        force_refresh()
        st.rerun()

    st.divider()

    # --- Sources actives ---
    st.markdown(
        "<div style='font-size:0.72rem;color:#64748b;text-transform:uppercase;"
        "letter-spacing:.08em;margin-bottom:8px'>Sources actives</div>",
        unsafe_allow_html=True
    )
    _df_src = get_mart_k1()
    if not _df_src.empty:
        _sources = sorted(_df_src['source'].unique().tolist())
        for _s in _sources:
            _n = int(_df_src[_df_src['source'] == _s]['nb_articles'].sum())
            st.markdown(
                f"<div style='font-size:0.75rem;color:#94a3b8;padding:2px 0'>"
                f"<span style='color:#3b82f6'>&#9679;</span>&nbsp;{_s}"
                f"<span style='color:#475569;float:right'>{_n}</span></div>",
                unsafe_allow_html=True
            )

    st.divider()
    st.markdown(
        "<div style='font-size:0.72rem;color:#475569'>"
        "Sprint 2 · Mars 2026<br>PostgreSQL · dbt · Streamlit</div>",
        unsafe_allow_html=True
    )

# ---------------------------------------------------
# CHARGEMENT METRIQUES DEPUIS POSTGRESQL
# ---------------------------------------------------
df_k1 = get_mart_k1()
df_k3 = get_mart_k3()

total_articles = int(df_k1['nb_articles'].sum())                       if not df_k1.empty else 0
nb_sources     = df_k1['source'].nunique()                             if not df_k1.empty else 0
top_source     = df_k1.groupby('source')['nb_articles'].sum().idxmax() if not df_k1.empty else '—'
top_cat        = df_k3.groupby('category')['nb_articles'].sum().idxmax() if not df_k3.empty else '—'
date_max       = df_k1['published_date'].max().strftime('%d/%m/%Y')    if not df_k1.empty else '—'

# ---------------------------------------------------
# BANNER
# ---------------------------------------------------
st.markdown(f"""
<div class="banner" style="text-align:center;padding:40px 36px;">
    <div class="banner-title">CyberPulse</div>
    <div class="banner-sub" style="justify-content:center;font-size:1rem">
        <span class="live-dot"></span>
        {"Veille automatique des menaces cyber" if lang == "fr" else "Automated cyber threat monitoring"}
        &nbsp;·&nbsp; {nb_sources} {t('Sources active', lang)}
        &nbsp;·&nbsp; {total_articles} articles
    </div>
</div>
""", unsafe_allow_html=True)

# --- Metriques ---
st.markdown(f'<div class="section-tag">{t("Overview", lang)}</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

for col, val, lbl, sub, cls in [
    (c1, str(total_articles), t("Filtered articles", lang), f"{nb_sources} {t('Sources active', lang)}", ""),
    (c2, str(nb_sources),     t("Sources active", lang),    "NewsAPI + RSS",                              "green"),
    (c3, top_cat,             t("Top threat", lang),        "par volume" if lang == "fr" else "by volume","orange"),
    (c4, top_source,          t("Top source", lang),        "par nb" if lang == "fr" else "by count",     "teal"),
    (c5, date_max,            "Derniere mise a jour",       "date article recente",                       "red"),
]:
    col.markdown(f"""
    <div class="metric-card {cls}">
        <div class="metric-val">{val}</div>
        <div class="metric-lbl">{lbl}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Apercu articles recents ---
st.markdown(f'<div class="section-tag">{t("Data preview", lang)}</div>', unsafe_allow_html=True)

df_preview = get_stg_articles(limit=20)

if not df_preview.empty:
    cols_affichees = ['source', 'title', 'published_date', 'content_length']
    st.dataframe(
        df_preview[cols_affichees].sort_values('published_date', ascending=False),
        use_container_width=True,
        hide_index=True,
        height=380
    )
    st.markdown("<br>", unsafe_allow_html=True)
    csv = df_preview.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=t("Download CSV", lang),
        data=csv,
        file_name=f"cyberpulse_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )
else:
    st.warning(t("No data", lang))

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-tag">Navigation</div>', unsafe_allow_html=True)
st.markdown(
    f"<div style='color:#64748b;font-size:0.88rem'>{t('Navigation hint', lang)}</div>",
    unsafe_allow_html=True
)
