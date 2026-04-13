# app.py -- StatCyberMatrix Dashboard -- Page d'accueil
# Metriques globales + tableau articles + navigation KPI 1-6 + Carte

import base64
import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Import des fonctions de données
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from db_connect import get_mart_k1, get_stg_articles, force_refresh
from utils_lang import t

st.set_page_config(page_title="StatCyberMatrix", layout="wide", initial_sidebar_state="expanded")

# Injection CSS pour la sidebar
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()


# ── CSS GLOBAL ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

.stApp {
    background: radial-gradient(ellipse at 20% 50%, rgba(14,40,80,0.9) 0%, #050a14 60%),
                radial-gradient(ellipse at 80% 20%, rgba(8,30,60,0.8) 0%, transparent 50%);
    background-color: #050a14 !important;
}
.stApp::before { display: none !important; }

[data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }

/* Styles Sidebar */
[data-testid="stSidebar"] {
    z-index: 2 !important;
    background: #050a14 !important;
    border-right: 1px solid rgba(30,111,255,0.15);
}

/* Styles Cartes KPI Navigation */
.kpi-btn-inner {
    background: rgba(13,18,32,0.85); border-radius: 12px;
    border-left: 5px solid var(--c); padding: 36px 28px;
    position: relative; overflow: hidden; cursor: pointer;
    transition: background 0.22s, transform 0.22s, box-shadow 0.22s;
    backdrop-filter: blur(8px); min-height: 220px;
}
.kpi-btn-inner:hover {
    background: rgba(17,24,39,0.95); transform: translateX(6px);
    box-shadow: 8px 0 40px rgba(0,0,0,0.55);
}
.kpi-bnum {
    position: absolute; top: -10px; right: 10px;
    font-size: 140px; font-weight: 800; color: var(--c);
    opacity: 0.05; line-height: 1; pointer-events: none;
}
.kpi-btitle { font-size: 22px; font-weight: 700; color: #cbd5e1; margin-bottom: 12px; text-align: center; }
.kpi-bdesc  { font-size: 14px; color: #7a8fa6; text-align: center; line-height: 1.5; }

/* Carte Menace (Large) */
.map-btn-inner {
    background: rgba(13,18,32,0.85); border-radius: 12px;
    border-left: 5px solid #6366f1; padding: 36px 28px;
    display: flex; align-items: center; gap: 28px;
    cursor: pointer; position: relative; overflow: hidden;
    backdrop-filter: blur(8px); transition: all 0.22s;
}
.map-btn-inner:hover { background: rgba(17,24,39,0.95); transform: translateX(6px); }
.map-btitle { font-size: 22px; font-weight: 700; color: #cbd5e1; }
.map-btag { font-size: 12px; color: #6366f1; border: 1px solid rgba(99,102,241,0.35); border-radius: 5px; padding: 4px 12px; margin-right: 8px;}
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : CODE RAIN ──────────────────────────────────────────────────
components.html("""
<script>
(function() {
    var p = window.parent.document, w = window.parent;
    function startCodeRain(){
        var old = p.getElementById('sentinel-rain-bg-home'); 
        if(old) old.parentNode.removeChild(old);
        var cv = p.createElement('canvas'); 
        cv.id = 'sentinel-rain-bg-home';
        cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.12;';
        p.body.appendChild(cv);
        var ctx = cv.getContext('2d');
        var W = cv.width = w.innerWidth, H = cv.height = w.innerHeight;
        var symbols = "01ABCDEF💀RATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
        var fontSize = 14, columns = W / fontSize, drops = [];
        for (var i = 0; i < columns; i++) { drops[i] = Math.random() * (H / fontSize); }
        function draw(){
            ctx.fillStyle = 'rgba(5, 10, 20, 0.1)'; ctx.fillRect(0, 0, W, H);
            ctx.fillStyle = '#3b82f6'; ctx.font = fontSize + 'px Roboto Mono';
            for (var i = 0; i < drops.length; i++) {
                var text = symbols[Math.floor(Math.random() * symbols.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                drops[i]++;
                if (drops[i] * fontSize > H && Math.random() > 0.975) { drops[i] = 0; }
            }
            requestAnimationFrame(draw);
        }
        draw();
    }
    setTimeout(startCodeRain, 100);
})();
</script>
""", height=0)

# ── DONNÉES & LOGO ──────────────────────────────────────────────────────────
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
    if st.button("Rafraîchir les données"):
        force_refresh()
        st.rerun()

# ── BANNER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:rgba(15,20,34,0.85);backdrop-filter:blur(8px);border:1px solid #1e2a42;border-radius:16px;padding:40px;text-align:center;margin-bottom:28px;">
    {"<img src='data:image/png;base64,"+LOGO_B64+"' style='max-width:700px;width:80%;'>" if LOGO_B64 else "<h1>StatCyberMatrix</h1>"}
    <div style="font-size:0.95rem;color:#64748b;margin-top:15px;">Veille automatique de l'actualité cyber</div>
</div>
""", unsafe_allow_html=True)

# ── MÉTRIQUES PRINCIPALES ─────────────────────────────────────────────────────
components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@700&family=Roboto+Mono:wght@700&display=swap');
body {{ background:transparent; font-family:'Roboto',sans-serif; margin:0; }}
.cards {{ display:grid; grid-template-columns:1fr 1fr; gap:15px; }}
.card {{ background:rgba(15,20,34,0.85); border:1px solid #1e2a42; border-radius:12px; padding:25px; text-align:center; color:#e2e8f0; }}
.value {{ font-size:3.5rem; font-weight:700; font-family:'Roboto Mono'; color:#3b82f6; }}
</style>
<div class="cards">
    <div class="card"><div>ARTICLES COLLECTÉS</div><div class="value">{total_articles}</div></div>
    <div class="card"><div>SOURCES ACTIVES</div><div class="value" style="color:#22c55e">{nb_sources}</div></div>
</div>
""", height=160)

# ── TABLEAU RÉCENT ────────────────────────────────────────────────────────────
if not df_articles.empty:
    st.dataframe(df_articles[["source", "title", "published_date"]].head(10), use_container_width=True, hide_index=True)

# ── SECTION KPI 1 À 6 ─────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
_KPIS = [
    ("kpi1", "#3b82f6", "01", "Articles collectés", "Volume par source et évolution temporelle", "pages/1_Articles_collectes.py"),
    ("kpi2", "#a855f7", "02", "Suivi mots-clés", "Fréquence des termes et sujets dominants", "pages/2_Suivi_des_mots-cles.py"),
    ("kpi3", "#ef4444", "03", "Analyse Menaces", "Répartition Ransomware, Phishing, APT...", "pages/3_Analyse_des_menaces.py"),
    ("kpi4", "#f59e0b", "04", "Tendances", "Évolution hebdomadaire des vecteurs", "pages/4_Analyse_des_tendances.py"),
    ("kpi5", "#22c55e", "05", "Alertes", "Nombre d'alertes critiques et volatilité", "pages/5_Analyse_des_alertes.py"),
    ("kpi6", "#14b8a6", "06", "CVEs", "Vulnérabilités officielles détaillées", "pages/6_CVEs.py"),
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
        if st.button(f"Voir l'analyse {num}", key=f"btn_{key}", use_container_width=True):
            st.switch_page(page)

# ── CARTE DES MENACES (KPI 07) ────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_map, _ = st.columns([2, 1])
with col_map:
    st.markdown("""
    <div class="map-btn-inner">
      <div style="font-size:40px;">🌍</div>
      <div style="flex:1">
        <div class="map-btitle">07. Carte mondiale des menaces</div>
        <div style="color:#7a8fa6; margin-bottom:10px;">Visualisation géographique des hotspots et origines des attaques.</div>
        <div><span class="map-btag">Temps réel</span><span class="map-btag">Géolocalisation</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Ouvrir la Carte Live", key="btn_map", use_container_width=True):
        st.switch_page("pages/7_Carte_Menaces.py")