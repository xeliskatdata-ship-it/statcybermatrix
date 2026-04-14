# Accueil.py -- StatCyberMatrix Dashboard -- Home page
# Unified theme + English default + FR toggle

import base64
import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from db_connect import get_mart_k1, get_stg_articles, force_refresh
from utils_lang import t

st.set_page_config(page_title="StatCyberMatrix", layout="wide", initial_sidebar_state="expanded")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

# ── LANGUAGE STATE ───────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"
lang = st.session_state.lang

# ── DATA & LOGO ──────────────────────────────────────────────────────────────
df_k1 = get_mart_k1()
df_articles = get_stg_articles(limit=500)
total_articles = int(df_k1["nb_articles"].sum()) if not df_k1.empty else 0
nb_sources = df_k1["source"].nunique() if not df_k1.empty else 0

_logo_path = os.path.join(os.path.dirname(__file__), "static", "logo_statcybermatrix.png")
LOGO_B64 = ""
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    if LOGO_B64:
        st.markdown(f"<div style='text-align:center'><img src='data:image/png;base64,{LOGO_B64}' style='width:100%;'></div>", unsafe_allow_html=True)
    st.divider()

    # Language toggle
    lang_choice = st.selectbox(
        "Language",
        options=["English", "Francais"],
        index=0 if lang == "en" else 1,
        key="lang_select"
    )
    st.session_state.lang = "en" if lang_choice == "English" else "fr"
    lang = st.session_state.lang

    if st.button(t("Refresh", lang)):
        force_refresh()
        st.rerun()

# ── BANNER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:rgba(10,22,40,0.7);backdrop-filter:blur(8px);border:1px solid rgba(0,212,255,0.1);border-radius:12px;padding:36px;text-align:center;margin-bottom:24px;">
    {"<img src='data:image/png;base64,"+LOGO_B64+"' style='max-width:700px;width:80%;'>" if LOGO_B64 else "<h1 style='font-family:Syne;color:#fff'>StatCyberMatrix</h1>"}
    <div style="font-family:JetBrains Mono;font-size:0.85rem;color:#7a9cc8;margin-top:12px;">{t("Cyber monitoring", lang)}</div>
</div>
""", unsafe_allow_html=True)

# ── MAIN METRICS ──────────────────────────────────────────────────────────────
components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=JetBrains+Mono:wght@400;500&display=swap');
body {{ background:transparent; margin:0; }}
.cards {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; font-family:'JetBrains Mono',monospace; }}
.card {{
    background:rgba(10,22,40,0.7); border:1px solid rgba(0,212,255,0.1);
    border-radius:10px; padding:22px; text-align:center; color:#7a9cc8;
    font-size:0.65rem; text-transform:uppercase; letter-spacing:1.5px;
}}
.value {{ font-family:'Syne',sans-serif; font-size:3rem; font-weight:800; color:#00d4ff; margin-top:4px; }}
</style>
<div class="cards">
    <div class="card">{t("Articles collected", lang).upper()}<div class="value">{total_articles}</div></div>
    <div class="card">{t("Active sources", lang).upper()}<div class="value" style="color:#a855f7">{nb_sources}</div></div>
</div>
""", height=140)

# ── RECENT TABLE ──────────────────────────────────────────────────────────────
if not df_articles.empty:
    df_articles['published_date'] = pd.to_datetime(df_articles['published_date']).dt.strftime('%Y-%m-%d')
    st.dataframe(
        df_articles[["source", "title", "published_date"]].head(10),
        use_container_width=True,
        hide_index=True,
        column_config={
            "source": t("Sources", lang),
            "title": "Title",
            "published_date": st.column_config.TextColumn("Date", width="small")
        }
    )

# ── KPI CARDS ─────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

# CSS for KPI cards
st.markdown("""
<style>
.kpi-btn-inner {
    background: rgba(10,22,40,0.7); border-radius: 10px;
    border-left: 3px solid var(--c); padding: 28px 22px;
    position: relative; overflow: hidden; cursor: pointer;
    transition: all 0.2s; backdrop-filter: blur(8px); min-height: 180px;
    border: 1px solid rgba(0,212,255,0.06);
}
.kpi-btn-inner:hover {
    background: rgba(10,22,40,0.9); transform: translateX(4px);
    border-color: rgba(0,212,255,0.15);
}
.kpi-bnum {
    position: absolute; top: -8px; right: 8px;
    font-family: 'Syne', sans-serif; font-size: 110px; font-weight: 800;
    color: var(--c); opacity: 0.04; line-height: 1; pointer-events: none;
}
.kpi-btitle {
    font-family: 'Syne', sans-serif; font-size: 17px; font-weight: 600;
    color: #fff; margin-bottom: 8px; text-align: center;
}
.kpi-bdesc {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: #7a9cc8; text-align: center; line-height: 1.5;
}
.map-btn-inner {
    background: rgba(10,22,40,0.7); border-radius: 10px;
    border-left: 3px solid #a855f7; padding: 28px 22px;
    display: flex; align-items: center; gap: 24px;
    cursor: pointer; position: relative; overflow: hidden;
    backdrop-filter: blur(8px); transition: all 0.2s;
    border: 1px solid rgba(0,212,255,0.06);
}
.map-btn-inner:hover { background: rgba(10,22,40,0.9); transform: translateX(4px); }
.map-btitle { font-family: 'Syne', sans-serif; font-size: 17px; font-weight: 600; color: #fff; }
.map-btag {
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    color: #a855f7; border: 1px solid rgba(168,85,247,0.3);
    border-radius: 4px; padding: 3px 10px; margin-right: 6px; letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)

_KPIS = [
    ("kpi1", "#00d4ff", "01", t("KPI 1 title", lang),  t("KPI 1 desc", lang),  "pages/1_Articles_collectes.py"),
    ("kpi2", "#a855f7", "02", t("KPI 2 title", lang),  t("KPI 2 desc", lang),  "pages/2_Suivi_des_mots-cles.py"),
    ("kpi3", "#ef4444", "03", t("KPI 3 title", lang),  t("KPI 3 desc", lang),  "pages/3_Analyse_des_menaces.py"),
    ("kpi4", "#f59e0b", "04", t("KPI 4 title", lang),  t("KPI 4 desc", lang),  "pages/4_Analyse_des_tendances.py"),
    ("kpi5", "#22c55e", "05", t("KPI 5 title", lang),  t("KPI 5 desc", lang),  "pages/5_Analyse_des_alertes.py"),
    ("kpi6", "#14b8a6", "06", t("KPI 6 title", lang),  t("KPI 6 desc", lang),  "pages/6_CVEs.py"),
]

col1, col2, col3 = st.columns(3)
for i, (key, color, num, title, desc, page) in enumerate(_KPIS):
    col = [col1, col2, col3][i % 3]
    with col:
        st.markdown(f"""
        <div class="kpi-btn-inner" style="--c:{color}">
            <div class="kpi-bnum">{num}</div>
            <div class="kpi-btitle">{title}</div>
            <div class="kpi-bdesc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"{t('See analysis', lang)} {num}", key=f"btn_{key}", use_container_width=True):
            st.switch_page(page)

# ── THREAT MAP CARD ───────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_map, _ = st.columns([2, 1])
with col_map:
    st.markdown(f"""
    <div class="map-btn-inner">
      <div style="font-size:32px;">&#127758;</div>
      <div style="flex:1">
        <div class="map-btitle">07. {t("Threat map", lang)}</div>
        <div style="font-family:JetBrains Mono;font-size:11px;color:#7a9cc8;margin:6px 0 10px;">{t("Threat map desc", lang)}</div>
        <div><span class="map-btag">{t("Real time", lang)}</span><span class="map-btag">{t("Geolocation", lang)}</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(t("Open live map", lang), key="btn_map", use_container_width=True):
        st.switch_page("pages/7_Carte_Menaces.py")