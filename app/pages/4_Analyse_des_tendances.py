# 4_kpi4_Analyse_Tendances.py -- Version Sentinel Green / CTI Insights

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

# ── CSS GLOBAL (Style Vert Pomme) ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif; color: #ffffff !important;}
.stApp { background-color: #050a14 !important; }

/* Forcer l'écriture blanche pour la lisibilité sur fond sombre */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3,
.stSelectbox label, .stCheckbox p {
    color: #ffffff !important;
}

.page-title {
    text-align: center; font-size: 2.8rem; font-weight: 700; color: #ffffff;
    margin-bottom: 20px; text-shadow: 0 0 15px rgba(50,205,50,0.5);
}

.section-title {
    text-align:center; font-family:'Roboto Mono',monospace; font-size:1.1rem;
    letter-spacing:.1em; text-transform:uppercase; color:#32CD32;
    border-bottom:1px solid rgba(50,205,50,0.3); width:fit-content;
    margin:40px auto 20px; padding-bottom:8px;
}

.insight-box {
    background: rgba(50, 205, 50, 0.08);
    border: 1px solid rgba(50, 205, 50, 0.2);
    border-left: 4px solid #32CD32;
    border-radius: 8px; padding: 15px 20px; margin: 10px auto 30px;
    color: #e2e8f0; font-size: 0.95rem; backdrop-filter: blur(10px);
    max-width: 95%;
}
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN (Vert Pomme Arrière-plan) ────────────────
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
      ctx.fillStyle = '#32CD32'; ctx.font = fontSize + 'px Roboto Mono';
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

# ── LOGIQUE DONNÉES ──────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k4()
    df_raw['published_date'] = pd.to_datetime(df_raw['published_date']).dt.normalize()
except:
    st.error("Base de données injoignable"); st.stop()

# ── FILTRES ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Analyse de Menaces")
    choix_temps = st.selectbox("Fenetre temporelle", ["7 derniers jours", "14 derniers jours", "30 derniers jours"], index=1)
    nb_jours = int(choix_temps.split()[0])
    cats_dispo = sorted(df_raw['category'].unique().tolist())
    target = st.selectbox("Vecteur spécifique", cats_dispo)

date_limite = df_raw['published_date'].max() - timedelta(days=nb_jours)
df = df_raw[df_raw['published_date'] >= date_limite].copy()

st.markdown('<div class="page-title">Analyse CTI des Tendances</div>', unsafe_allow_html=True)

# ── GRAPHIQUE 1 : RADAR D'ÉMERGENCE (Z-SCORE) ────────────────────────────────
st.markdown(f'<div class="section-title">Indice d\'Accélération (Z-Score) - {target}</div>', unsafe_allow_html=True)

data_trend = df[df['category'] == target].groupby('published_date')['nb_mentions'].sum().reset_index()

if not data_trend.empty:
    mean_val = data_trend['nb_mentions'].mean()
    std_val = data_trend['nb_mentions'].std()
    data_trend['z_score'] = (data_trend['nb_mentions'] - mean_val) / std_val if std_val > 0 else 0

    fig_radar = px.scatter(data_trend, x='nb_mentions', y='z_score', size='nb_mentions', color='z_score',
                           text=data_trend['published_date'].dt.strftime('%d/%m'),
                           color_continuous_scale=['#1b4d1b', '#32CD32', '#7fff00'], height=450)
    fig_radar.add_hline(y=2.0, line_dash="dash", line_color="#ff0000")
    fig_radar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,34,0.6)', font=dict(color='#ffffff'))
    st.plotly_chart(fig_radar, use_container_width=True)

    # ANALYSE DYNAMIQUE 1
    max_z = data_trend['z_score'].max()
    status = "CRITIQUE" if max_z > 2 else "STABLE"
    color_status = "#ff4b4b" if max_z > 2 else "#32CD32"
    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse d'Émergence :</b> Le signal est actuellement <b><span style="color:{color_status}">{status}</span></b>. 
        Le pic d'accélération (Z-Score: {max_z:.2f}) indique {'une anomalie forte nécessitant une veille immédiate' if max_z > 2 else 'une activité conforme aux normales saisonnières'}.
    </div>
    """, unsafe_allow_html=True)

# ── GRAPHIQUE 2 : EVOLUTION LISSÉE ───────────────────────────────────────────
st.markdown(f'<div class="section-title">Suivi de la Persistance - {target}</div>', unsafe_allow_html=True)

data_target = df[df['category'] == target].groupby('published_date')['nb_mentions'].sum().reset_index()
if not data_target.empty:
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=data_target['published_date'], y=data_target['nb_mentions'], name="Brut", line=dict(color='#32CD32', width=3)))
    data_target['ma'] = data_target['nb_mentions'].rolling(window=3).mean()
    fig_line.add_trace(go.Scatter(x=data_target['published_date'], y=data_target['ma'], name="Tendance (3j)", line=dict(color='#7fff00', width=2, dash='dot')))
    fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,34,0.6)', font=dict(color='#ffffff'), height=400)
    st.plotly_chart(fig_line, use_container_width=True)

    # ANALYSE DYNAMIQUE 2
    recent_trend = "en augmentation" if data_target['nb_mentions'].iloc[-1] > data_target['ma'].iloc[-1] else "en résorption"
    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse de Persistance :</b> Sur les 3 derniers points, la menace est <b>{recent_trend}</b> par rapport à sa moyenne mobile. 
        Cela permet de distinguer un pic éphémère d'une campagne de fond qui s'installe dans la durée.
    </div>
    """, unsafe_allow_html=True)

# ── GRAPHIQUE 3 : RÉPARTITION GLOBALE ────────────────────────────────────────
st.markdown('<div class="section-title">Dominance Relative des Vecteurs</div>', unsafe_allow_html=True)

df_comp = df.groupby('category')['nb_mentions'].sum().sort_values(ascending=True).reset_index()
fig_bar = px.bar(df_comp, x='nb_mentions', y='category', orientation='h', color='nb_mentions', color_continuous_scale=['#1b4d1b', '#32CD32'])
fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,34,0.6)', font=dict(color='#ffffff'))
st.plotly_chart(fig_bar, use_container_width=True)

# ANALYSE DYNAMIQUE 3
top_cat = df_comp.iloc[-1]['category']
st.markdown(f"""
<div class="insight-box">
    <b>Analyse de Dominance :</b> Le vecteur <b>{top_cat}</b> concentre la majorité du bruit numérique actuel. 
    Pour un consultant, cela signifie que les outils de défense doivent être prioritairement durcis contre ce type d'attaque spécifique ce mois-ci.
</div>
""", unsafe_allow_html=True)