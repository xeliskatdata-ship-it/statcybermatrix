# 4_kpi4_Analyse_Tendances.py -- Version CTI Expert Finale (Sentinel Green)

import sys, os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configuration chemins (à adapter selon ton arborescence)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k4

st.set_page_config(page_title="StatCyberMatrix - KPI 4 Tendances", layout="wide")

# ── CSS GLOBAL (Style Vert Pomme / Sentinel) ───────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif; color: #ffffff !important;}

.stApp { background-color: #050a14 !important; }

/* Forcer l'écriture blanche partout */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3,
.stSelectbox label, .stCheckbox p, .stTable td, .stTable th {
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

/* Boîte d'analyse style Sentinel Green */
.insight-box {
    background: rgba(50, 205, 50, 0.08);
    border: 1px solid rgba(50, 205, 50, 0.2);
    border-left: 4px solid #32CD32;
    border-radius: 8px; padding: 20px; margin: 15px auto 30px;
    color: #e2e8f0; font-size: 0.95rem; backdrop-filter: blur(10px);
    max-width: 95%; line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN (Vert Pomme en arrière-plan) ────────────
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

# ── DATA PROCESSING ──────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k4()
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

# Filtrage temporel
date_limite = df_raw['published_date'].max() - timedelta(days=nb_jours)
df = df_raw[df_raw['published_date'] >= date_limite].copy()

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Analyse des Tendances CTI</div>', unsafe_allow_html=True)

# ── GRAPHIQUE 1 : RADAR D'ÉMERGENCE (Z-SCORE) ────────────────────────────────
st.markdown(f'<div class="section-title">Indice d\'Accélération (Z-Score) - {target}</div>', unsafe_allow_html=True)

data_trend = df[df['category'] == target].groupby('published_date')['nb_mentions'].sum().reset_index()

if not data_trend.empty:
    # Calculs statistiques
    mean_val = data_trend['nb_mentions'].mean()
    std_val = data_trend['nb_mentions'].std()
    data_trend['z_score'] = (data_trend['nb_mentions'] - mean_val) / std_val if std_val > 0 else 0
    
    # Identification du pic d'anomalie
    top_emergence = data_trend.sort_values('z_score', ascending=False).iloc[0]
    date_pic = top_emergence['published_date'].strftime('%d/%m/%Y')
    vol_pic = int(top_emergence['nb_mentions'])
    bond_percent = ((vol_pic - mean_val) / mean_val * 100) if mean_val > 0 else 0

    # Plot Radar
    fig_radar = px.scatter(data_trend, x='nb_mentions', y='z_score', size='nb_mentions', color='z_score',
                           text=data_trend['published_date'].dt.strftime('%d/%m'),
                           labels={'nb_mentions': 'Volume de Mentions', 'z_score': 'Indice Z-Score'},
                           color_continuous_scale=['#1b4d1b', '#32CD32', '#7fff00'], height=450)
    
    fig_radar.add_hline(y=2.0, line_dash="dash", line_color="#ff4b4b", 
                        annotation_text="SEUIL D'ALERTE (ANOMALIE)", annotation_font_color="#ff4b4b")
    
    fig_radar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,34,0.6)',
                          font=dict(family="Roboto Mono", color='#ffffff'), hovermode='closest')
    st.plotly_chart(fig_radar, use_container_width=True)

    # Phrases d'Analyse Dynamiques
    status = "CRITIQUE" if top_emergence['z_score'] > 2 else "STABLE"
    color_status = "#ff4b4b" if top_emergence['z_score'] > 2 else "#32CD32"
    
    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse d'Émergence :</b> Le signal est actuellement <b><span style="color:{color_status}">{status}</span></b>. 
        Le pic d'accélération (Z-Score: {top_emergence['z_score']:.2f}) indique {'une anomalie forte nécessitant une veille immédiate' if top_emergence['z_score'] > 2 else 'une activité conforme aux normales saisonnières'}.<br>
        <b>Détail de l'alerte :</b> Le {date_pic}, il a été détecté un volume de <b>{vol_pic} mentions</b>, soit un bond de <b>{bond_percent:.1f}%</b> au-dessus de l'activité normale des {nb_jours} derniers jours.
    </div>
    """, unsafe_allow_html=True)

# ── GRAPHIQUE 2 : EVOLUTION LISSÉE ───────────────────────────────────────────
st.markdown(f'<div class="section-title">Suivi de la Persistance Temporelle</div>', unsafe_allow_html=True)

if not data_trend.empty:
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=data_trend['published_date'], y=data_trend['nb_mentions'], name="Flux Brut", 
                                 line=dict(color='#32CD32', width=3), mode='lines+markers'))
    
    # Moyenne mobile 3 jours
    data_trend['ma'] = data_trend['nb_mentions'].rolling(window=3).mean()
    fig_line.add_trace(go.Scatter(x=data_trend['published_date'], y=data_trend['ma'], name="Tendance Lisse", 
                                 line=dict(color='#7fff00', width=2, dash='dot')))

    fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,34,0.6)',
                          font=dict(family="Roboto Mono", color='#ffffff'), height=400)
    st.plotly_chart(fig_line, use_container_width=True)

    # Analyse
    recent_trend = "en augmentation" if data_trend['nb_mentions'].iloc[-1] > data_trend['ma'].iloc[-1] else "en résorption"
    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse de Persistance :</b> La menace est actuellement <b>{recent_trend}</b>. 
        L'écart entre la courbe brute et la tendance lisse permet de confirmer si le pic d'anomalie se stabilise ou s'il s'agissait d'un signal isolé.
    </div>
    """, unsafe_allow_html=True)

# ── TABLEAU RÉCAPITULATIF POUR LE RAPPORT ────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Guide d'interprétation du Signal (Z-Score)")
data_guide = {
    "Valeur Z-Score": ["0", "1 à 2", "> 2"],
    "Signification pour le Consultant": [
        "Activité parfaitement normale (calme plat).",
        "Vigilance : bruit de fond en légère augmentation.",
        "ANOMALIE : Signal fort d'une attaque ou d'une actualité cyber critique."
    ]
}
st.table(pd.DataFrame(data_guide))