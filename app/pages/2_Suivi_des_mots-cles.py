# 2_kpi2_Mots_cles.py -- Version Treemap & Deep Dive Sources

import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k2, force_refresh

st.set_page_config(page_title="KPI 2 - Threat Keywords", layout="wide")

# ── CSS GLOBAL (Style StatCyberMatrix) ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&family=Roboto+Mono:wght@400;700&display=swap');
.stApp { background-color: #050a14 !important; color: #94a3b8; }
.page-title { text-align:center; font-size:2.5rem; font-weight:700; color:#a855f7; margin-bottom:10px; }
.section-title { font-family:'Roboto Mono'; font-size:0.8rem; color:#a855f7; border-left:4px solid #a855f7; padding-left:15px; margin:30px 0 20px; text-transform:uppercase; letter-spacing:0.1em; }
.metric-container { background: rgba(15,20,34,0.6); border: 1px solid rgba(168,85,247,0.2); border-radius: 8px; padding: 20px; text-align: center; backdrop-filter: blur(10px); }
.metric-label { font-size: 0.8rem; text-transform: uppercase; color: #94a3b8; margin-bottom: 5px; }
.metric-value { font-family: 'Roboto Mono'; font-size: 2.2rem; font-weight: 700; color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ── ANIMATION ECG DISCRÈTE (Identique KPI 1) ──────────────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  var PT_SIZE=20, TRAIL_PX=270, SPD=2.5;
  function ecgValue(x,H){var margin=PT_SIZE+10,maxAmp=H/2-margin,mod=x%220,raw;
    if(mod<70)raw=Math.sin(mod*0.05)*5;else if(mod<80)raw=(mod-70)*13;
    else if(mod<85)raw=130-(mod-80)*55;else if(mod<90)raw=-145+(mod-85)*32;
    else if(mod<100)raw=-25+(mod-90)*3;else if(mod<115)raw=Math.sin((mod-100)*0.4)*9;
    else raw=Math.sin(mod*0.04)*3;return(raw/130)*maxAmp;}
  function startECG(){
    var old=p.getElementById('ecg-bg-k2'); if(old)old.parentNode.removeChild(old);
    var cv=p.createElement('canvas'); cv.id='ecg-bg-k2';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';
    p.body.appendChild(cv); var ctx=cv.getContext('2d'),ecgX=0,history=[],alive=true;
    function resize(){cv.width=p.documentElement.clientWidth;cv.height=p.documentElement.clientHeight;}
    resize(); w.addEventListener('resize',resize);
    function draw(){if(!p.getElementById('ecg-bg-k2')||!alive)return;
      var W=cv.width,H=cv.height; ctx.clearRect(0,0,W,H);
      history.push({x:ecgX%W,y:H/2-ecgValue(ecgX,H)}); ecgX+=SPD;
      if(history.length>Math.round(TRAIL_PX/SPD))history.shift();
      if(history.length>1){for(var k=1;k<history.length;k++){
        var alpha=(k/history.length)*0.6, isSpike=Math.abs(history[k].y-H/2)>H*0.08;
        ctx.beginPath(); ctx.moveTo(history[k-1].x,history[k-1].y); ctx.lineTo(history[k].x,history[k].y);
        ctx.strokeStyle=isSpike?'rgba(168,85,247,'+alpha+')':'rgba(59,130,246,'+(alpha*0.3)+')';
        ctx.lineWidth=isSpike?2.5:1.2; ctx.stroke();}
        var head=history[history.length-1];
        ctx.beginPath(); ctx.arc(head.x,head.y,4,0,Math.PI*2); ctx.fillStyle='rgba(168,85,247,0.8)'; ctx.fill();
      }
      requestAnimationFrame(draw);} draw(); return function(){alive=false;};}
  var stop=startECG();
})();
</script>
""", height=0)

# ── CHARGEMENT ET CALCULS ────────────────────────────────────────────────────
try:
    df_raw = get_mart_k2()
    # On sépare 3j et 15j pour calculer l'accélération
    v3 = df_raw[df_raw['period_days'] == 3].copy()
    v15 = df_raw[df_raw['period_days'] == 15][['keyword', 'occurrences']].rename(columns={'occurrences':'occ_15j'})
    
    drift_df = pd.merge(v3, v15, on='keyword', how='left').fillna(0)
    # Formule d'accélération (Volume récent / Moyenne lissée ancienne)
    drift_df['acceleration'] = (drift_df['occurrences'] + 1) / ((drift_df['occ_15j'] / 5) + 1)
    # Simuler des catégories si elles n'existent pas dans ta base pour le Treemap
    if 'category' not in drift_df.columns:
        drift_df['category'] = 'Threats' 
except Exception as e:
    st.error(f"Erreur de données : {e}"); st.stop()

# ── HEADER & COMPTEURS ────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Threat Keywords Intelligence</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-container"><div class="metric-label">Mots-clés Actifs</div><div class="metric-value">{len(drift_df)}</div></div>', unsafe_allow_html=True)
with col2:
    top_k = drift_df.sort_values('occurrences', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"
    st.markdown(f'<div class="metric-container"><div class="metric-label">Top Volume</div><div class="metric-value" style="color:#a855f7">{top_k}</div></div>', unsafe_allow_html=True)
with col3:
    fast_k = drift_df.sort_values('acceleration', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"
    st.markdown(f'<div class="metric-container"><div class="metric-label">Top Vélocité</div><div class="metric-value" style="color:#22c55e">{fast_k}</div></div>', unsafe_allow_html=True)
with col4:
    if st.button("⟳ Refresh Data", use_container_width=True):
        force_refresh(); st.rerun()

# ── FILTRES ET TREEMAP ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Analyse Hiérarchique : Part de Voix & Accélération</div>', unsafe_allow_html=True)

f_col1, f_col2 = st.columns([1, 2])
with f_col1:
    min_accel = st.slider("Seuil d'accélération (Emergence)", 0.5, 3.0, 1.0, step=0.1)

df_filtered = drift_df[drift_df['acceleration'] >= min_accel]

fig_tree = px.treemap(
    df_filtered,
    path=[px.Constant("Toutes les menaces"), 'category', 'keyword'],
    values='occurrences',
    color='acceleration',
    color_continuous_scale='Purples',
    range_color=[0.5, 2.5],
    hover_data={'acceleration': ':.2f', 'occurrences': True, 'source_count': True}
)

fig_tree.update_layout(
    margin=dict(t=10, b=10, l=10, r=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Roboto Mono", color="#e2e8f0")
)
st.plotly_chart(fig_tree, use_container_width=True)

# ── GRAPHIQUE BARRES : FIABILITÉ DU SIGNAL ────────────────────────────────────
st.markdown('<div class="section-title">Fiabilité du Signal (Sources Uniques & Détails)</div>', unsafe_allow_html=True)

# On prépare une chaîne de texte pour le hover qui liste les sources (si ton DF les contient)
# Si ta colonne s'appelle 'sources_list', on l'utilise, sinon on affiche le compte.
df_snr = df_filtered.nlargest(15, 'occurrences').sort_values('source_count')

fig_snr = go.Figure(go.Bar(
    y=df_snr['keyword'], 
    x=df_snr['source_count'],
    orientation='h',
    marker=dict(
        color=df_snr['source_count'],
        colorscale='Purples',
        line=dict(color='rgba(168,85,247,0.6)', width=1)
    ),
    # C'est ici qu'on définit ce qui s'affiche au survol
    hovertemplate="<b>Keyword: %{y}</b><br>" +
                  "Nombre de sources: %{x}<br>" +
                  "<i>Survoler pour voir l'intensité du signal</i><extra></extra>"
))

fig_snr.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,20,34,0.4)",
    height=500,
    xaxis=dict(title="Nombre de sources distinctes", gridcolor="rgba(255,255,255,0.05)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    font=dict(family="Roboto Mono", color="#94a3b8")
)
st.plotly_chart(fig_snr, use_container_width=True)

# ── TABLEAU DE DÉTAILS POUR LES CONSULTANTS ───────────────────────────────────
st.markdown('<div class="section-title">🔍 Deep Dive : Explorer les articles</div>', unsafe_allow_html=True)

selected_kw = st.selectbox("Sélectionner un mot-clé pour voir les sources", ["-- Choisir un mot-clé --"] + list(df_snr['keyword']))

if selected_kw != "-- Choisir un mot-clé --":
    # Ici, tu peux appeler une fonction qui va chercher les articles réels pour ce mot-clé
    st.info(f"Affichage des derniers articles liés à : **{selected_kw}**")
    # Exemple de structure de lien pour les consultants :
    st.markdown(f"""
    - [Source 1] Article sur {selected_kw} - *12/04/2026*
    - [Source 2] Analyse technique de {selected_kw} - *13/04/2026*
    """)