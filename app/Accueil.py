# app.py -- StatCyberMatrix Dashboard -- Page d'accueil
# Metriques globales + tableau articles + navigation KPI

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

# ── Sidebar CSS (module partagé) ─────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()

# ── CSS GLOBAL (ECG & GRILLES SUPPRIMÉS) ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

/* Fond dégradé pur sans image fixe ni grille */
.stApp {
    background: radial-gradient(ellipse at 20% 50%, rgba(14,40,80,0.9) 0%, #050a14 60%),
                radial-gradient(ellipse at 80% 20%, rgba(8,30,60,0.8) 0%, transparent 50%);
    background-color: #050a14 !important;
}

/* On s'assure qu'aucun pseudo-élément ne vient polluer le fond */
.stApp::before { display: none !important; content: none !important; }

[data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }

/* Styles Sidebar */
[data-testid="stSidebar"] {
    z-index: 2 !important;
    background: #050a14 !important;
    border-right: 1px solid rgba(30,111,255,0.15);
}

/* Styles Cartes KPI */
.kpi-btn-inner {
    background: rgba(13,18,32,0.85); border-radius: 12px;
    border-left: 5px solid var(--c); padding: 36px 28px;
    position: relative; overflow: hidden; cursor: pointer;
    transition: background 0.22s, transform 0.22s, box-shadow 0.22s;
    backdrop-filter: blur(8px);
}
.kpi-btn-inner:hover {
    background: rgba(17,24,39,0.95); transform: translateX(6px);
    box-shadow: 8px 0 40px rgba(0,0,0,0.55);
}
.kpi-btitle { font-size: 22px; font-weight: 700; color: #cbd5e1; margin-bottom: 12px; text-align: center; }
.kpi-bdesc  { font-size: 15px; color: #7a8fa6; line-height: 1.75; text-align: center; }

/* Tableaux Streamlit en transparence */
[data-testid="stDataFrame"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN (Structure KPI 3) ────────────────────────
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
        var W = cv.width = w.innerWidth;
        var H = cv.height = w.innerHeight;
        
        var symbols = "01ABCDEF💀RATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
        var fontSize = 14; 
        var columns = W / fontSize; 
        var drops = [];
        for (var i = 0; i < columns; i++) { drops[i] = Math.random() * (H / fontSize); }
        
        function draw(){
            if(!p.getElementById('sentinel-rain-bg-home')) return;
            ctx.fillStyle = 'rgba(5, 10, 20, 0.1)'; 
            ctx.fillRect(0, 0, W, H);
            ctx.fillStyle = '#3b82f6'; 
            ctx.font = fontSize + 'px Roboto Mono';
            
            for (var i = 0; i < drops.length; i++) {
                var text = symbols[Math.floor(Math.random() * symbols.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                drops[i]++;
                if (drops[i] * fontSize > H && Math.random() > 0.975) { drops[i] = 0; }
            }
            requestAnimationFrame(draw);
        }
        draw(); 
        w.addEventListener('resize', function(){
            W = cv.width = w.innerWidth;
            H = cv.height = w.innerHeight;
        });
    }
    setTimeout(startCodeRain, 100);
})();
</script>
""", height=0)

# ── DATA PROCESSING ──────────────────────────────────────────────────────────
df_k1 = get_mart_k1()
df_articles = get_stg_articles(limit=500)

total_articles = int(df_k1["nb_articles"].sum()) if not df_k1.empty else 0
nb_sources = df_k1["source"].nunique() if not df_k1.empty else 0
date_max = df_k1["published_date"].max().strftime("%d/%m/%Y") if not df_k1.empty else "--"
last_update = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")

# ── LOGO ──────────────────────────────────────────────────────────────────────
_logo_path = os.path.join(os.path.dirname(__file__), "static", "logo_statcybermatrix.png")
LOGO_B64 = ""
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    if LOGO_B64:
        st.markdown(f"<div style='text-align:center'><img src='data:image/png;base64,{LOGO_B64}' style='width:100%;max-width:300px;border-radius:10px;'></div>", unsafe_allow_html=True)
    st.divider()
    if st.button("Rafraîchir les données"):
        force_refresh()
        st.rerun()

# ── BANNER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:rgba(15,20,34,0.85);backdrop-filter:blur(8px);border:1px solid #1e2a42;border-radius:16px;padding:40px;text-align:center;margin-bottom:28px;">
    {f"<img src='data:image/png;base64,{LOGO_B64}' style='max-width:700px;width:80%;'>" if LOGO_B64 else "<h1>StatCyberMatrix</h1>"}
    <div style="font-size:0.95rem;color:#64748b;margin-top:15px;">
        <span class="live-dot" style="display:inline-block;width:8px;height:8px;background:#22c55e;border-radius:50%;margin-right:8px;"></span>
        Veille automatique de l'actualité cyber en temps réel
    </div>
</div>
""", unsafe_allow_html=True)

# ── MÉTRIQUES ANIMÉES ─────────────────────────────────────────────────────────
components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Roboto+Mono:wght@700&display=swap');
body {{ background:transparent; font-family:'Roboto',sans-serif; margin:0; }}
.cards {{ display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-bottom:15px; }}
.card {{
    background:rgba(15,20,34,0.85); border:1px solid #1e2a42; border-radius:12px;
    padding:25px; text-align:center; color:#e2e8f0; backdrop-filter:blur(8px);
}}
.label {{ font-size:12px; letter-spacing:0.1em; text-transform:uppercase; color:#3b82f6; margin-bottom:10px; }}
.value {{ font-size:3.5rem; font-weight:700; font-family:'Roboto Mono'; }}
</style>
<div class="cards">
    <div class="card"><div class="label">Articles collectés</div><div class="value" id="v1">0</div></div>
    <div class="card"><div class="label" style="color:#22c55e">Sources actives</div><div class="value" id="v2">0</div></div>
</div>
<script>
function anim(id, end) {{
    let obj = document.getElementById(id);
    let curr = 0;
    let step = end / 60;
    let t = setInterval(() => {{
        curr += step;
        if(curr >= end) {{ curr = end; clearInterval(t); }}
        obj.innerText = Math.floor(curr).toLocaleString('fr-FR');
    }}, 20);
}}
anim('v1', {total_articles});
anim('v2', {nb_sources});
</script>
""", height=180)

# ── TABLEAU ARTICLES ──────────────────────────────────────────────────────────
if not df_articles.empty:
    df_show = df_articles[["source", "title", "published_date", "url"]].copy()
    df_show = df_show.rename(columns={"source": "Source", "title": "Titre", "published_date": "Date"})
    st.dataframe(df_show, use_container_width=True, hide_index=True, height=400)

# ── NAVIGATION KPI ────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
cols = st.columns(3)
kpi_data = [
    ("#3b82f6", "01", "Articles collectés", "pages/1_Articles_collectes.py"),
    ("#a855f7", "02", "Mots-clés", "pages/2_Suivi_des_mots-cles.py"),
    ("#ef4444", "03", "Analyse Menaces", "pages/3_Analyse_des_menaces.py")
]

for i, (color, num, title, page) in enumerate(kpi_data):
    with cols[i]:
        st.markdown(f"""
        <div class="kpi-btn-inner" style="--c:{color}">
            <div style="font-size:12px; color:{color}; font-weight:bold;">KPI {num}</div>
            <div class="kpi-btitle">{title}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Explorer {num}", key=f"btn_{num}", use_container_width=True):
            st.switch_page(page)