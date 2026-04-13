# 2_kpi2_Mots_cles.py -- Version Corrigée (Focus Lisibilité & ECG Discret)

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

st.set_page_config(page_title="KPI 2 - Threat Intelligence", layout="wide")

# ── CSS GLOBAL (Harmonisation KPI 1) ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&family=Roboto+Mono:wght@400;700&display=swap');
.stApp { background-color: #050a14 !important; color: #94a3b8; }
.page-title { text-align:center; font-size:2.5rem; font-weight:700; color:#a855f7; margin-bottom:10px; }
.section-title { font-family:'Roboto Mono'; font-size:0.8rem; color:#a855f7; border-left:4px solid #a855f7; padding-left:15px; margin:30px 0 20px; text-transform:uppercase; letter-spacing:0.1em; }
/* Cartes de monitoring type SOC */
.metric-container { background: rgba(15,20,34,0.6); border: 1px solid rgba(168,85,247,0.2); border-radius: 8px; padding: 20px; text-align: center; backdrop-filter: blur(10px); }
.metric-label { font-size: 0.8rem; text-transform: uppercase; color: #94a3b8; margin-bottom: 5px; }
.metric-value { font-family: 'Roboto Mono'; font-size: 2.2rem; font-weight: 700; color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ── ANIMATION ECG DISCRÈTE (Identique KPI 1, Teinte Violette) ──────────────────
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

# ── CHARGEMENT DES DONNÉES ───────────────────────────────────────────────────
try:
    df_raw = get_mart_k2()
    # Calcul de la vélocité (comparaison 3j vs 15j)
    v3 = df_raw[df_raw['period_days'] == 3][['keyword', 'occurrences', 'source_count']].rename(columns={'occurrences':'occ_3j', 'source_count':'src_3j'})
    v15 = df_raw[df_raw['period_days'] == 15][['keyword', 'occurrences']].rename(columns={'occurrences':'occ_15j'})
    drift_df = pd.merge(v3, v15, on='keyword', how='left').fillna(0)
    drift_df['acceleration'] = (drift_df['occ_3j'] + 1) / ((drift_df['occ_15j'] / 5) + 1)
except Exception as e:
    st.error(f"Erreur de données : {e}"); st.stop()

# ── HEADER & COMPTEURS (SANS SUPERPOSITION) ──────────────────────────────────
st.markdown('<div class="page-title">Threat Keywords Intelligence</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""<div class="metric-container"><div class="metric-label">Mots-clés Actifs</div>
                <div class="metric-value">{len(drift_df)}</div></div>""", unsafe_allow_html=True)
with col2:
    top_k = drift_df.sort_values('occ_3j', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "N/A"
    st.markdown(f"""<div class="metric-container"><div class="metric-label">Top Volume (3j)</div>
                <div class="metric-value" style="font-size:1.5rem; color:#a855f7;">{top_k}</div></div>""", unsafe_allow_html=True)
with col3:
    fast_k = drift_df.sort_values('acceleration', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "N/A"
    st.markdown(f"""<div class="metric-container"><div class="metric-label">Top Vélocité</div>
                <div class="metric-value" style="font-size:1.5rem; color:#22c55e;">{fast_k}</div></div>""", unsafe_allow_html=True)
with col4:
    if st.button("⟳ Refresh Data", use_container_width=True):
        force_refresh()
        st.rerun()

# ── GRAPHIQUE 1 : DRIFT DES MENACES (NETTOYÉ) ────────────────────────────────
st.markdown('<div class="section-title">Analyse du Drift : Volume vs Accélération</div>', unsafe_allow_html=True)

fig_drift = px.scatter(
    drift_df,
    x="occ_3j", y="acceleration",
    size="src_3j", color="acceleration",
    text="keyword",
    color_continuous_scale="Purples",
    labels={"occ_3j": "Volume (3 jours)", "acceleration": "Indice d'accélération", "src_3j": "Sources"},
    height=600
)

fig_drift.add_hline(y=1.5, line_dash="dash", line_color="rgba(168,85,247,0.5)", annotation_text="Seuil d'émergence")
fig_drift.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='rgba(255,255,255,0.1)')))
fig_drift.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", 
    plot_bgcolor="rgba(15,20,34,0.4)",
    font=dict(family="Roboto Mono", color="#94a3b8"),
    margin=dict(t=20, b=20)
)
st.plotly_chart(fig_drift, use_container_width=True)

# ── GRAPHIQUE 2 : FIDÉLITÉ DU SIGNAL ──────────────────────────────────────────
st.markdown('<div class="section-title">Fiabilité du Signal (Nombre de Sources Uniques)</div>', unsafe_allow_html=True)

df_snr = drift_df.nlargest(15, 'occ_3j').sort_values('src_3j')
fig_snr = go.Figure(go.Bar(
    y=df_snr['keyword'], x=df_snr['src_3j'],
    orientation='h',
    marker=dict(color='#a855f7', line=dict(color='#f0abfc', width=1)),
    hovertemplate="<b>%{y}</b><br>Sources : %{x}<extra></extra>"
))

fig_snr.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,20,34,0.4)",
    height=450, font=dict(family="Roboto Mono", color="#94a3b8"),
    margin=dict(t=20, b=20, l=20, r=20)
)
st.plotly_chart(fig_snr, use_container_width=True)