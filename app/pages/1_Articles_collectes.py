# 1_kpi1_Articles.py -- Version Sentinel Rain Blue Edition

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k1, get_stg_articles, force_refresh

st.set_page_config(page_title="StatCyberMatrix - Veille", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()

# ── CSS GLOBAL (Maintien du Bleu originel) ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif;}
.stApp {
    background-color: #050a14 !important;
}
.page-title{text-align:center;font-size:2.8rem;font-weight:700;color:#3b82f6;margin-top:10px;margin-bottom:30px;text-shadow: 0 0 15px rgba(59,130,246,0.3);}
.alert-banner{background:rgba(59, 130, 246, 0.05);border:1px solid #3b82f6;border-radius:8px;padding:15px;margin:20px 0;}
.section-title{font-family:'Roboto Mono',monospace;font-size:1rem;color:#3b82f6;margin:30px 0 15px;border-left:4px solid #3b82f6;padding-left:15px;text-transform:uppercase;}
.article-card { background:rgba(255,255,255,0.03); border-left:3px solid #3b82f6; padding:10px 15px; margin-bottom:8px; border-radius:4px; transition: 0.3s;}
.article-card:hover { background:rgba(59,130,246,0.05); border-left-width: 6px; }
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN (VERSION BLEUE) ───────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  function startCodeRain(){
    var old=p.getElementById('sentinel-rain-bg-k1'); if(old)old.parentNode.removeChild(old);
    var cv=p.createElement('canvas'); cv.id='sentinel-rain-bg-k1';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.12;';
    p.body.appendChild(cv);
    var ctx=cv.getContext('2d'), W=cv.width=w.innerWidth, H=cv.height=w.innerHeight;
    var codeSymbols = "01ABCDEF💀RATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
    var fontSize = 14; var columns = W / fontSize; var drops = [];
    for (var i = 0; i < columns; i++) { drops[i] = Math.random() * (H / fontSize); }
    function draw(){
      if(!p.getElementById('sentinel-rain-bg-k1'))return;
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

# ── LOGIQUE DATA ─────────────────────────────────────────────────────────────
try:
    df = get_mart_k1()
    df['published_date'] = pd.to_datetime(df['published_date'])
except Exception as e:
    st.error(f"Erreur Connexion : {e}"); st.stop()

# ── TITRE ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Articles collectés & Signaux émergents</div>', unsafe_allow_html=True)

# ── CALCULS VÉLOCITÉ ─────────────────────────────────────────────────────────
now = datetime.now()
df_24h = df[df['published_date'] >= (now - timedelta(days=1))]
df_hist = df[(df['published_date'] >= (now - timedelta(days=7))) & (df['published_date'] < (now - timedelta(days=1)))]

vol_24h = df_24h.groupby('source')['nb_articles'].sum().reset_index(name='today')
vol_hist = df_hist.groupby('source')['nb_articles'].sum().reset_index(name='total_hist')
vol_hist['avg_daily'] = vol_hist['total_hist'] / 6

trend_df = pd.merge(vol_24h, vol_hist, on='source', how='left').fillna(0)
trend_df['velocity_score'] = (trend_df['today'] + 1) / (trend_df['avg_daily'] + 1)

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,20,34,0.5)",
    font=dict(family="Roboto Mono", color="#94a3b8"),
    margin=dict(l=40, r=40, t=40, b=40)
)

# ── RADAR VÉLOCITÉ ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">RADAR D\'ÉMERGENCE (Dernières 24h)</div>', unsafe_allow_html=True)

fig_radar = px.scatter(
    trend_df,
    x="today",
    y="velocity_score",
    size="today",
    color="velocity_score",
    text="source",
    labels={"today": "Volume Articles", "velocity_score": "Indice d'Accélération"},
    color_continuous_scale="Blues",
    height=500
)
fig_radar.add_hline(y=2.0, line_dash="dash", line_color="#3b82f6", annotation_text="Seuil d'alerte")
fig_radar.update_traces(textposition='top center')
fig_radar.update_layout(**PLOTLY_BASE)
st.plotly_chart(fig_radar, use_container_width=True)

# ── ALERTES ──────────────────────────────────────────────────────────────────
top_threat = trend_df.sort_values('velocity_score', ascending=False).iloc[0]
if top_threat['velocity_score'] > 2.0:
    st.markdown(f"""
    <div class="alert-banner">
        <b style="color:#3b82f6">ℹ️ ANALYSE DE FLUX :</b> La source <b>{top_threat['source']}</b> 
        présente une accélération notable ({top_threat['velocity_score']:.1f}x la normale).
    </div>
    """, unsafe_allow_html=True)

# ── ÉVOLUTION TEMPORELLE ──────────────────────────────────────────────────────
st.markdown('<div class="section-title">SUIVI DE L\'ÉVOLUTION TEMPORELLE (7 Jours)</div>', unsafe_allow_html=True)

fast_sources = trend_df.sort_values('velocity_score', ascending=False).head(5)['source'].tolist()
df_evo = df[df['source'].isin(fast_sources) & (df['published_date'] >= (now - timedelta(days=7)))]
df_evo = df_evo.sort_values('published_date')

fig_line = px.line(
    df_evo,
    x='published_date',
    y='nb_articles',
    color='source',
    markers=True,
    height=400,
    color_discrete_sequence=px.colors.sequential.Blues_r
)

fig_line.update_layout(
    **PLOTLY_BASE,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified"
)
st.plotly_chart(fig_line, use_container_width=True)

# ── DERNIERS FLUX ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">DERNIERS FLUX COLLECTÉS</div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 3])
with c1:
    src_select = st.selectbox("Source à inspecter", sorted(trend_df['source'].unique()))
with c2:
    df_detail = get_stg_articles(limit=100)
    df_src = df_detail[df_detail["source"] == src_select].sort_values("published_date", ascending=False).head(8)
    
    for _, row in df_src.iterrows():
        st.markdown(f"""
        <div class="article-card">
            <a href="{row['url']}" target="_blank" style="color:#e2e8f0; text-decoration:none; font-size:0.9rem;">{row['title']}</a>
            <div style="font-size:0.75rem; color:#64748b;">{str(row['published_date'])[:16]} | {row['category']}</div>
        </div>
        """, unsafe_allow_html=True)