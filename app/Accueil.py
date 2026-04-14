# Accueil.py -- StatCyberMatrix Dashboard -- Home page

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
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

if "lang" not in st.session_state:
    st.session_state.lang = "en"

# ── DATA & LOGO ──────────────────────────────────────────────────────────────
df_k1 = get_mart_k1()
df_articles = get_stg_articles(limit=5000)
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
    lang_choice = st.selectbox("Language", options=["English", "Francais"],
                               index=0 if st.session_state.lang == "en" else 1, key="lang_select")
    st.session_state.lang = "en" if lang_choice == "English" else "fr"
    lang = st.session_state.lang
    if st.button(t("Refresh", lang)):
        force_refresh()
        st.rerun()

inject_sidebar_css(lang)

# ── KPI CARD CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
.kpi-card {
    background: rgba(10,22,40,0.7);
    border: 1px solid rgba(0,212,255,0.08);
    border-left: 3px solid var(--c);
    border-radius: 10px;
    padding: 36px 22px;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.2s;
    backdrop-filter: blur(8px);
    min-height: 160px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.kpi-card:hover {
    background: rgba(10,22,40,0.95);
    transform: translateX(4px);
    border-color: rgba(0,212,255,0.2);
}
.kpi-ghost {
    position: absolute;
    top: -12px;
    right: 8px;
    font-family: 'Syne', sans-serif;
    font-size: 120px;
    font-weight: 800;
    color: var(--c);
    opacity: 0.04;
    line-height: 1;
    pointer-events: none;
}
.kpi-label {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    text-align: center;
    line-height: 1.3;
}
</style>
""", unsafe_allow_html=True)

# ── BANNER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:rgba(10,22,40,0.7);backdrop-filter:blur(8px);border:1px solid rgba(0,212,255,0.1);border-radius:12px;padding:36px;text-align:center;margin-bottom:24px;">
    {"<img src='data:image/png;base64,"+LOGO_B64+"' style='max-width:700px;width:80%;'>" if LOGO_B64 else "<h1 style='font-family:Syne;color:#fff'>StatCyberMatrix</h1>"}
    <div style="font-family:JetBrains Mono;font-size:0.85rem;color:#7a9cc8;margin-top:12px;">{t("Cyber monitoring", lang)}</div>
</div>
""", unsafe_allow_html=True)

# ── MAIN METRICS (animated counters) ──────────────────────────────────────────
_lbl_art = "ARTICLES COLLECTED" if lang == "en" else "ARTICLES COLLECTES"
_lbl_src = "ACTIVE SOURCES" if lang == "en" else "SOURCES ACTIVES"

components.html(f"""
<style>
@font-face {{ font-family:'Syne'; src:url('https://fonts.gstatic.com/s/syne/v22/8vIS7w4qzmVxp2ztD.woff2') format('woff2'); font-weight:800; }}
@font-face {{ font-family:'JBM'; src:url('https://fonts.gstatic.com/s/jetbrainsmono/v18/tDbY2o-flEEny0FZhsfKu5WU4xD-.woff2') format('woff2'); font-weight:400; }}
body {{ background:transparent; margin:0; overflow:hidden; }}
.cards {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
.card {{ background:rgba(10,22,40,0.75); border:1px solid var(--bc); border-bottom:3px solid var(--ac); border-radius:12px; padding:24px; text-align:center; }}
.label {{ font-family:'JBM',monospace; font-size:10px; color:#7a9cc8; letter-spacing:2.5px; margin-bottom:8px; }}
.num {{ font-family:'Syne',sans-serif; font-size:52px; font-weight:800; color:var(--ac); line-height:1; }}
</style>
<div class="cards">
    <div class="card" style="--ac:#00d4ff;--bc:rgba(0,212,255,0.12)">
        <div class="label">{_lbl_art}</div>
        <div class="num" id="c1">0</div>
    </div>
    <div class="card" style="--ac:#a855f7;--bc:rgba(168,85,247,0.12)">
        <div class="label">{_lbl_src}</div>
        <div class="num" id="c2">0</div>
    </div>
</div>
<script>
function fmt(n){{ return n.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, '\\u00A0'); }}
function anim(id,target,ms){{
    var el=document.getElementById(id),t0=null;
    function step(ts){{ if(!t0)t0=ts; var p=Math.min((ts-t0)/ms,1),ease=1-Math.pow(1-p,3); el.textContent=fmt(Math.floor(ease*target)); if(p<1)requestAnimationFrame(step); }}
    requestAnimationFrame(step);
}}
anim('c1',{total_articles},2000);
anim('c2',{nb_sources},1200);
</script>
""", height=150)

# ── RECENT TABLE ──────────────────────────────────────────────────────────────
if not df_articles.empty:
    df_articles['published_date'] = pd.to_datetime(df_articles['published_date']).dt.strftime('%Y-%m-%d')
    st.dataframe(
        df_articles[["source", "title", "published_date"]],
        use_container_width=True, hide_index=True, height=500,
        column_config={"source": t("Sources", lang), "title": "Title",
                       "published_date": st.column_config.TextColumn("Date", width="small")}
    )

# ── KPI CARDS (titres uniquement, pas de description) ────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

_KPIS = [
    ("kpi1", "#00d4ff", "01", t("KPI 1 title", lang), "pages/1_Articles_collectes.py"),
    ("kpi2", "#a855f7", "02", t("KPI 2 title", lang), "pages/2_Suivi_des_mots-cles.py"),
    ("kpi3", "#ef4444", "03", t("KPI 3 title", lang), "pages/3_Analyse_des_menaces.py"),
    ("kpi4", "#f59e0b", "04", t("KPI 4 title", lang), "pages/4_Analyse_des_tendances.py"),
    ("kpi5", "#22c55e", "05", t("KPI 5 title", lang), "pages/5_Analyse_des_alertes.py"),
    ("kpi6", "#14b8a6", "06", t("KPI 6 title", lang), "pages/6_CVEs.py"),
    ("kpi7", "#a855f7", "07", t("Threat map", lang),  "pages/7_Carte_Menaces.py"),
]

# 3 colonnes x 3 lignes (7 cartes identiques)
rows = [_KPIS[0:3], _KPIS[3:6], _KPIS[6:7]]

for row_kpis in rows:
    cols = st.columns(3)
    for i, (key, color, num, title, page) in enumerate(row_kpis):
        with cols[i]:
            st.markdown(f"""
            <div class="kpi-card" style="--c:{color}">
                <div class="kpi-ghost">{num}</div>
                <div class="kpi-label">{title}</div>
            </div>
            """, unsafe_allow_html=True)
            btn_label = t("Open live map", lang) if key == "kpi7" else f"{t('See analysis', lang)} {num}"
            if st.button(btn_label, key=f"btn_{key}", use_container_width=True):
                st.switch_page(page)