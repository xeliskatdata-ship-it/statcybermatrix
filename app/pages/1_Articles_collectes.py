# 1_kpi1_Articles.py -- KPI 1 : Articles collectés & Détection d'Émergence
# Design : Cyber-Velocity Radar, Pulse de Menaces, Fond Bokeh & ECG

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k1, get_stg_articles, force_refresh

st.set_page_config(page_title="KPI 1 - Cyber Velocity", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()

# ── CSS global (Optimisé pour Alertes) ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif;}
.stApp {
    background: radial-gradient(ellipse at 20% 50%, rgba(14,40,80,0.9) 0%, #050a14 60%),
                radial-gradient(ellipse at 80% 20%, rgba(8,30,60,0.8) 0%, transparent 50%);
    background-color: #050a14 !important;
}
.kpi-tag{display:inline-block;font-family:'Roboto Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#3b82f6;background:rgba(59,130,246,.1);
border:1px solid rgba(59,130,246,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}
.page-title{text-align:center;font-size:2.8rem;font-weight:700;color:#3b82f6;margin-bottom:20px;line-height:1.2;}
.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.insight-box{background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#93c5fd;font-size:0.88rem;backdrop-filter:blur(8px);}
.alert-banner{background:rgba(239, 68, 68, 0.12);border:1px solid #ef4444;border-radius:10px;padding:20px;margin:20px 0;}
</style>
""", unsafe_allow_html=True)

# ── Fond ECG (Composant HTML conservé) ────────────────────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  var PT_SIZE=24, TRAIL_PX=270, SPD=2;
  function ecgValue(x,H){var margin=PT_SIZE+10,maxAmp=H/2-margin,mod=x%220,raw;
    if(mod<70)raw=Math.sin(mod*0.05)*5;else if(mod<80)raw=(mod-70)*13;
    else if(mod<85)raw=130-(mod-80)*55;else if(mod<90)raw=-145+(mod-85)*32;
    else if(mod<100)raw=-25+(mod-90)*3;else if(mod<115)raw=Math.sin((mod-100)*0.4)*9;
    else raw=Math.sin(mod*0.04)*3;return(raw/130)*maxAmp;}
  function startECG(){var old=p.getElementById('ecg-bg');if(old)old.parentNode.removeChild(old);
    var cv=p.createElement('canvas');cv.id='ecg-bg';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';
    p.body.appendChild(cv);var ctx=cv.getContext('2d'),t=0,ecgX=0,history=[],alive=true;
    function resize(){cv.width=p.documentElement.clientWidth;cv.height=p.documentElement.clientHeight;}
    resize();w.addEventListener('resize',resize);
    function draw(){if(!p.getElementById('ecg-bg')||!alive)return;
      var W=cv.width,H=cv.height;ctx.clearRect(0,0,W,H);t+=0.016;
      history.push({x:ecgX%W,y:H/2-ecgValue(ecgX,H)});ecgX+=SPD;
      if(history.length>Math.round(TRAIL_PX/SPD))history.shift();
      if(history.length>1){for(var k=1;k<history.length;k++){
        var prog=k/history.length,alpha=prog*0.8,isSpike=Math.abs(history[k].y-H/2)>H*0.08;
        ctx.beginPath();ctx.moveTo(history[k-1].x,history[k-1].y);ctx.lineTo(history[k].x,history[k].y);
        ctx.strokeStyle=isSpike?'rgba(168,85,247,'+alpha+')':'rgba(59,130,246,'+(alpha*0.6)+')';
        ctx.lineWidth=isSpike?3:1.5;ctx.stroke();}}
      requestAnimationFrame(draw);}
    draw();return function(){alive=false;};}
  var stop=startECG();
})();
</script>
""", height=0)

# ── Configuration Visuelle ───────────────────────────────────────────────────
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,20,34,0.6)",
    font=dict(family="Roboto Mono", color="#94a3b8"),
    margin=dict(l=40, r=40, t=60, b=40)
)

def _section(title):
    st.markdown(f"<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:1.2rem;letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;border-bottom:1px solid rgba(59,130,246,0.3);padding-bottom:8px;width:fit-content;margin:40px auto 20px'>{title}</div>", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-tag">KPI 1 • Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">Radar d\'Émergence & Flux de Collecte</div>', unsafe_allow_html=True)

# ── Chargement des Données ──────────────────────────────────────────────────
try:
    df = get_mart_k1()
    df['published_date'] = pd.to_datetime(df['published_date'])
except Exception as e:
    st.error(f"Erreur Connexion : {e}"); st.stop()

# ── LOGIQUE DE VÉLOCITÉ (Cœur de la problématique) ──────────────────────────
now = datetime.now()
df_24h = df[df['published_date'] >= (now - timedelta(days=1))]
df_hist = df[(df['published_date'] >= (now - timedelta(days=7))) & (df['published_date'] < (now - timedelta(days=1)))]

# Agrégation pour calcul de tendance
vol_24h = df_24h.groupby('source')['nb_articles'].sum().reset_index(name='today')
vol_hist = df_hist.groupby('source')['nb_articles'].sum().reset_index(name='total_hist')
vol_hist['avg_daily'] = vol_hist['total_hist'] / 6

trend_df = pd.merge(vol_24h, vol_hist, on='source', how='left').fillna(0)
trend_df['velocity_score'] = (trend_df['today'] + 1) / (trend_df['avg_daily'] + 1)

# ── Alertes Dynamiques ────────────────────────────────────────────────────────
top_emergent = trend_df.sort_values('velocity_score', ascending=False).iloc[0]
if top_emergent['velocity_score'] > 2.0:
    st.markdown(f"""
    <div class="alert-banner">
        <h3 style="color:#ef4444;margin:0">🚨 SIGNAL ÉMERGENT DÉTECTÉ : {top_emergent['source']}</h3>
        <p style="color:#f87171;margin:10px 0 0 0">
            Cette source publie actuellement <b>{top_emergent['velocity_score']:.1f}x</b> plus d'articles que sa moyenne hebdomadaire. 
            <b>Action requise :</b> Vérifier les derniers titres pour identifier une menace Zero-Day ou une campagne massive.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Visual 1 : Radar de Vélocité ──────────────────────────────────────────────
_section("Identification des Sujets Émergents (24h)")

fig_radar = px.scatter(
    trend_df,
    x="today",
    y="velocity_score",
    size="today",
    color="velocity_score",
    text="source",
    labels={"today": "Volume d'articles", "velocity_score": "Indice de Vélocité (Pertinence)"},
    color_continuous_scale="Reds",
    height=550
)
fig_radar.add_hrect(y0=2.0, y1=trend_df['velocity_score'].max()+0.5, fillcolor="red", opacity=0.07, line_width=0, annotation_text="ZONE D'ALERTE")
fig_radar.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='white')))
fig_radar.update_layout(**PLOTLY_BASE)
st.plotly_chart(fig_radar, use_container_width=True)

# ── Visual 2 : Pulse 7 Jours (Évolution) ──────────────────────────────────────
_section("Suivi de l'évolution (Pulse des 7 derniers jours)")

# On suit les 6 sources les plus actives en vélocité
fast_sources = trend_df.nlargest(6, 'velocity_score')['source'].tolist()
df_pulse = df[df['source'].isin(fast_sources) & (df['published_date'] >= (now - timedelta(days=7)))]

fig_pulse = px.area(
    df_pulse.sort_values('published_date'), 
    x='published_date', 
    y='nb_articles', 
    color='source',
    line_group='source',
    height=400,
    color_discrete_sequence=px.colors.qualitative.Vivid
)
fig_pulse.update_layout(**PLOTLY_BASE)
st.plotly_chart(fig_pulse, use_container_width=True)

# ── Détail des Articles (Interaction) ─────────────────────────────────────────
st.markdown('<div class="section-title">Flux de détails par source</div>', unsafe_allow_html=True)
src_select = st.selectbox("Sélectionner une source pour audit", ["-- Sélectionner --"] + sorted(trend_df['source'].unique()))

if src_select != "-- Sélectionner --":
    df_detail = get_stg_articles(limit=100)
    df_src = df_detail[df_detail["source"] == src_select].sort_values("published_date", ascending=False)
    
    for _, row in df_src.head(10).iterrows():
        st.markdown(f"""
            <div style="background:rgba(15,20,34,0.7); border-left:4px solid #3b82f6; padding:15px; margin-bottom:10px; border-radius:0 8px 8px 0;">
                <div style="font-weight:bold; color:#e2e8f0;"><a href="{row['url']}" target="_blank" style="color:inherit; text-decoration:none;">{row['title']}</a></div>
                <div style="font-size:0.8rem; color:#64748b; margin-top:5px;">{row['published_date']} | {row['category']}</div>
            </div>
        """, unsafe_allow_html=True)

# ── Footer Export ─────────────────────────────────────────────────────────────
st.markdown("---")
if st.button("⬇ Exporter le rapport de vélocité (CSV)"):
    st.download_button("Confirmer le téléchargement", trend_df.to_csv(), "cyber_velocity.csv", "text/csv")