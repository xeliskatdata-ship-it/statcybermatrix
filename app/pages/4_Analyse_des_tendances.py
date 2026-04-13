# 4_kpi4_Analyse_Tendances.py -- Version CTI Expert Sans Emoji - Fix KeyError

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
from db_connect import get_mart_k4

st.set_page_config(page_title="StatCyberMatrix - KPI 4 Tendances", layout="wide")

# ── CSS GLOBAL (Style Vert Pomme / Sentinel) ───────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif; color: #ffffff !important;}
.stApp { background-color: #050a14 !important; }

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

.insight-box {
    background: rgba(5, 10, 20, 0.7);
    border: 1px solid rgba(50, 205, 50, 0.3);
    border-radius: 8px; padding: 25px; margin: 15px auto;
    backdrop-filter: blur(10px); max-width: 95%;
}

.alert-highlight {
    background: rgba(255, 75, 75, 0.1);
    border: 2px solid #ff4b4b;
    border-radius: 5px; padding: 15px; margin-top: 15px;
    font-family: 'Roboto Mono', monospace;
}

.source-link {
    color: #32CD32 !important;
    text-decoration: underline; font-size: 0.9rem;
    display: block; margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN ──────────────────────────────────────────
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
    var codeSymbols = "01ABCDEFSRATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
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
    st.markdown("### Analyse de Menaces")
    choix_temps = st.selectbox("Fenetre d'observation", ["7 derniers jours", "14 derniers jours", "30 derniers jours"], index=1)
    nb_jours = int(choix_temps.split()[0])
    cats_dispo = sorted(df_raw['category'].unique().tolist())
    target = st.selectbox("Vecteur cible", cats_dispo)

date_limite = df_raw['published_date'].max() - timedelta(days=nb_jours)
df = df_raw[df_raw['published_date'] >= date_limite].copy()

st.markdown('<div class="page-title">Analyse des Tendances CTI</div>', unsafe_allow_html=True)

# ── GRAPHIQUE 1 : RADAR D'ÉMERGENCE (Z-SCORE) ────────────────────────────────
st.markdown(f'<div class="section-title">Indice d\'Accélération (Z-Score) - {target}</div>', unsafe_allow_html=True)

data_trend = df[df['category'] == target].groupby('published_date')['nb_mentions'].sum().reset_index()

if not data_trend.empty:
    mean_val = data_trend['nb_mentions'].mean()
    std_val = data_trend['nb_mentions'].std()
    data_trend['z_score'] = (data_trend['nb_mentions'] - mean_val) / std_val if std_val > 0 else 0
    
    top_emergence = data_trend.sort_values('z_score', ascending=False).iloc[0]
    raw_date_pic = top_emergence['published_date']
    date_pic_str = raw_date_pic.strftime('%d/%m/%Y')
    vol_pic = int(top_emergence['nb_mentions'])
    bond_percent = ((vol_pic - mean_val) / mean_val * 100) if mean_val > 0 else 0

    fig_radar = px.scatter(data_trend, x='nb_mentions', y='z_score', size='nb_mentions', color='z_score',
                           text=data_trend['published_date'].dt.strftime('%d/%m'),
                           color_continuous_scale=['#1b4d1b', '#32CD32', '#7fff00'], height=450)
    fig_radar.add_hline(y=2.0, line_dash="dash", line_color="#ff4b4b")
    fig_radar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,20,34,0.6)', font=dict(color='#ffffff'))
    st.plotly_chart(fig_radar, use_container_width=True)

    # ── ANALYSE ET ALERTE ────────────────────────────────────────────────────
    status = "CRITIQUE" if top_emergence['z_score'] > 2 else "STABLE"
    color_status = "#ff4b4b" if top_emergence['z_score'] > 2 else "#32CD32"
    
    st.markdown(f"""
    <div class="insight-box">
        <b>Etat du signal :</b> <span style="color:{color_status}; font-weight:bold;">{status}</span> (Score Z : {top_emergence['z_score']:.2f})
        <div class="alert-highlight">
            <b>DETAIL DE L'ALERTE :</b> Le <b>{date_pic_str}</b>, un volume de <b>{vol_pic} mentions</b> a ete identifie. 
            Cela représente un bond de <b>{bond_percent:.1f}%</b> par rapport a l'activite habituelle de la categorie <b>{target}</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SOURCES ET PREUVES (CORRECTION KEYERROR) ──────────────────────────────
    st.markdown(f"#### Identification des sources au {date_pic_str} ({target}) :")
    sources_pic = df_raw[(df_raw['published_date'] == raw_date_pic) & (df_raw['category'] == target)]
    
    if not sources_pic.empty:
        # Vérification dynamique du nom de la colonne de lien
        col_link = 'link' if 'link' in sources_pic.columns else 'url'
        
        for _, row in sources_pic.iterrows():
            href = row[col_link] if col_link in row else "#"
            st.markdown(f"""
                <a href="{href}" target="_blank" class="source-link">
                    - {row['title']} (Source : {row.get('source_name', 'Information libre')})
                </a>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucun detail de source disponible pour cette date precise.")

# ── TABLEAU RECAPITULATIF ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Guide d'interpretation du Z-Score")
st.table(pd.DataFrame({
    "Valeur Z-Score": ["0", "1 a 2", "> 2"],
    "Signification": ["Activite normale", "Vigilance (bruit en hausse)", "ANOMALIE (Signal d'attaque)"]
}))