# 4_kpi4_Analyse_Tendances.py -- Version Sentinel Rain Blue Edition

import sys, os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configuration chemins
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k4, force_refresh

st.set_page_config(page_title="StatCyberMatrix - KPI 4 Tendances", layout="wide")

# Injection CSS pour la sidebar
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()

# ── CSS GLOBAL (Uniformisé avec KPI 1) ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif;}

.stApp { background-color: #050a14 !important; }

/* Forcer l'écriture blanche partout */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3,
.stSelectbox label, .stCheckbox p {
    color: #ffffff !important;
}

.page-title {
    text-align: center; font-size: 2.8rem; font-weight: 700; color: #ffffff;
    margin-bottom: 20px; text-shadow: 0 0 15px rgba(59,130,246,0.5);
}

.section-title {
    text-align:center; font-family:'Roboto Mono',monospace; font-size:1.1rem;
    letter-spacing:.1em; text-transform:uppercase; color:#3b82f6;
    border-bottom:1px solid rgba(59,130,246,0.3); width:fit-content;
    margin:40px auto 20px; padding-bottom:8px;
}

.insight-box {
    background: rgba(59, 130, 246, 0.08);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-left: 4px solid #3b82f6;
    border-radius: 8px; padding: 15px 20px; margin: 15px auto 30px;
    color: #e2e8f0; font-size: 0.95rem; backdrop-filter: blur(10px);
    max-width: 90%;
}

.badge-live {
    display:inline-flex; align-items:center; gap:8px; font-family:'Roboto Mono';
    font-size:0.75rem; color:#22c55e; background:rgba(34,197,94,0.1);
    border:1px solid rgba(34,197,94,0.3); border-radius:20px; padding:5px 15px;
}
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN (Version Bleue) ──────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  function startCodeRain(){
    var old=p.getElementById('sentinel-rain-bg-k4'); if(old)old.parentNode.removeChild(old);
    var cv=p.createElement('canvas'); cv.id='sentinel-rain-bg-k4';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;opacity:0.12;';
    p.body.appendChild(cv);
    var ctx=cv.getContext('2d'), W=cv.width=w.innerWidth, H=cv.height=w.innerHeight;
    var codeSymbols = "01ABCDEF💀RATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
    var fontSize = 14; var columns = W / fontSize; var drops = [];
    for (var i = 0; i < columns; i++) { drops[i] = Math.random() * (H / fontSize); }
    function draw(){
      if(!p.getElementById('sentinel-rain-bg-k4'))return;
      ctx.fillStyle = 'rgba(5, 10, 20, 0.08)'; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#3b82f6'; ctx.font = fontSize + 'px Roboto Mono';
      for (var i = 0; i < drops.length; i++) {
        var text = codeSymbols[Math.floor(Math.random() * codeSymbols.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        drops[i]++;
        if (drops[i] * fontSize > H && Math.random() > 0.975) { drops[i] = 0; }
      }
      requestAnimationFrame(draw);
    }
    draw(); 
    w.addEventListener('resize', function(){W=cv.width=w.innerWidth; H=cv.height=w.innerHeight;});
  }
  startCodeRain();
})();
</script>
""", height=0)

# ── DATA PROCESSING ──────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k4()
    if not df_raw.empty:
        df_raw['published_date'] = pd.to_datetime(df_raw['published_date']).dt.normalize()
except Exception as e:
    st.error(f"Erreur de connexion : {e}"); st.stop()

# ── SIDEBAR FILTRES ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ Paramètres CTI")
    choix_temps = st.selectbox("Fenetre d'observation", ["7 derniers jours", "14 derniers jours", "30 derniers jours"], index=1)
    nb_jours = int(choix_temps.split()[0])
    cats_dispo = sorted(df_raw['category'].unique().tolist())
    target = st.selectbox("Vecteur cible", cats_dispo)
    show_global = st.checkbox("Comparer au volume total", value=True)

# Filtrage temporel
date_limite = df_raw['published_date'].max() - timedelta(days=nb_jours)
df = df_raw[df_raw['published_date'] >= date_limite].copy()

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Analyse des Tendances</div>', unsafe_allow_html=True)

# ── GRAPHIQUE 1 : EVOLUTION TEMPORELLE ───────────────────────────────────────
st.markdown(f'<div class="section-title">Évolution du vecteur {target}</div>', unsafe_allow_html=True)

data_target = df[df['category'] == target].groupby('published_date')['nb_mentions'].sum().reset_index()
data_global = df.groupby('published_date')['nb_mentions'].sum().reset_index()

fig = go.Figure()
if show_global and not data_global.empty:
    fig.add_trace(go.Scatter(x=data_global['published_date'], y=data_global['nb_mentions'], name="Volume Global", 
                             line=dict(color='rgba(148,163,184,0.2)', width=1), fill='tozeroy', fillcolor='rgba(148,163,184,0.05)'))

if not data_target.empty:
    fig.add_trace(go.Scatter(x=data_target['published_date'], y=data_target['nb_mentions'], name=target,
                             line=dict(color='#3b82f6', width=4), mode='lines+markers',
                             marker=dict(size=8, color='#3b82f6', line=dict(width=1, color='#050a14'))))

fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,34,0.6)',
                  font=dict(family="Roboto Mono", color='#ffffff'), hovermode='x unified', height=400)
st.plotly_chart(fig, use_container_width=True)

# Phrase d'analyse 1
if not data_target.empty:
    max_val = data_target['nb_mentions'].max()
    pic_date = data_target.loc[data_target['nb_mentions'].idxmax(), 'published_date'].strftime('%d/%m')
    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse de tendance :</b> Le vecteur <b>{target}</b> a atteint un pic d'activité le <b>{pic_date}</b> avec <b>{int(max_val)} mentions</b>. 
        L'écart par rapport au volume global permet d'identifier si cette menace est isolée ou liée à une campagne cyber massive.
    </div>
    """, unsafe_allow_html=True)

# ── GRAPHIQUE 2 : COMPARATIF DES MENACES ─────────────────────────────────────
st.markdown('<div class="section-title">Répartition Comparative des Menaces</div>', unsafe_allow_html=True)

df_comp = df.groupby('category')['nb_mentions'].sum().sort_values(ascending=True).reset_index()

fig_bar = px.bar(df_comp, x='nb_mentions', y='category', orientation='h',
                 color='nb_mentions', color_continuous_scale='Blues')
fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,34,0.6)', 
                      font=dict(family="Roboto Mono", color='#ffffff'), height=max(300, len(df_comp) * 35))
st.plotly_chart(fig_bar, use_container_width=True)

# Phrase d'analyse 2
if not df_comp.empty:
    top_cat = df_comp.iloc[-1]
    total_period = df_comp['nb_mentions'].sum()
    part = (top_cat['nb_mentions'] / total_period) * 100
    st.markdown(f"""
    <div class="insight-box">
        <b>Répartition des menaces :</b> La catégorie <b>{top_cat['category']}</b> domine actuellement le paysage avec 
        <b>{part:.1f}%</b> de la part de voix. Ce volume suggère une priorité de veille élevée pour ce vecteur spécifique.
    </div>
    """, unsafe_allow_html=True)