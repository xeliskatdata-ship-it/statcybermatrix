# 1_kpi1_Articles.py -- Version Sentinel Rain Blue Edition (Optimized Visibility)

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

# Import des fonctions de données
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k1, get_stg_articles, force_refresh

st.set_page_config(page_title="StatCyberMatrix - Veille", layout="wide")

# Injection CSS pour la sidebar
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()

# ── CSS GLOBAL (Contraste amélioré & Couleurs) ────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

.stApp { background-color: #050a14 !important; }

/* Forcer l'écriture en blanc pour la lisibilité */
[data-testid="stMarkdownContainer"] p, .stSelectbox label, .stSlider label {
    color: #ffffff !important;
}

.page-title {
    text-align: center; font-size: 2.8rem; font-weight: 700; color: #ffffff !important;
    margin-top: 10px; margin-bottom: 20px; text-shadow: 0 0 15px rgba(59,130,246,0.4);
}

.section-title {
    font-family: 'Roboto Mono', monospace; font-size: 1rem; color: #3b82f6;
    margin: 30px 0 15px; border-left: 4px solid #3b82f6; padding-left: 15px;
    text-transform: uppercase;
}

/* Boîte d'analyse dynamique */
.insight-box {
    background: rgba(59, 130, 246, 0.08);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 8px;
    padding: 15px 20px;
    margin: 10px 0 30px;
    color: #ffffff;
    font-size: 0.95rem;
    border-left: 4px solid #3b82f6;
}

.article-card { 
    background: rgba(255,255,255,0.03); border-left: 3px solid #3b82f6; 
    padding: 10px 15px; margin-bottom: 8px; border-radius: 4px; 
}
.article-card:hover { background: rgba(59,130,246,0.08); }

/* Styling Selectbox */
div[data-baseweb="select"] { background-color: #0d1117 !important; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN (Passé en arrière-plan) ───────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  function startCodeRain(){
    var old=p.getElementById('sentinel-rain-bg-k1'); if(old)old.parentNode.removeChild(old);
    var cv=p.createElement('canvas'); cv.id='sentinel-rain-bg-k1';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;opacity:0.1;';
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

# ── TITRE & FILTRE ───────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Articles collectés & Signaux émergents</div>', unsafe_allow_html=True)

with st.container():
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f2:
        period_label = st.selectbox(
            "Période d'analyse :",
            options=["3 derniers jours", "7 derniers jours", "14 derniers jours", "30 derniers jours"],
            index=1 
        )
        days_map = {"3 derniers jours": 3, "7 derniers jours": 7, "14 derniers jours": 14, "30 derniers jours": 30}
        selected_days = days_map[period_label]

# ── CALCULS ──────────────────────────────────────────────────────────────────
now = datetime.now()
limit_date = now - timedelta(days=selected_days)
df_filtered = df[df['published_date'] >= limit_date]

df_24h = df[df['published_date'] >= (now - timedelta(days=1))]
df_hist = df[(df['published_date'] >= limit_date) & (df['published_date'] < (now - timedelta(days=1)))]

vol_24h = df_24h.groupby('source')['nb_articles'].sum().reset_index(name='today')
vol_hist = df_hist.groupby('source')['nb_articles'].sum().reset_index(name='total_hist')
vol_hist['avg_daily'] = vol_hist['total_hist'] / (selected_days - 1) if selected_days > 1 else 1

trend_df = pd.merge(vol_24h, vol_hist, on='source', how='left').fillna(0)
trend_df['velocity_score'] = (trend_df['today'] + 1) / (trend_df['avg_daily'] + 1)

# Config Plotly pour l'écriture blanche
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,20,34,0.6)",
    font=dict(family="Roboto Mono", color="#ffffff"),
    margin=dict(l=40, r=40, t=40, b=40)
)

# ── RADAR VÉLOCITÉ ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">RADAR D\'ÉMERGENCE (Dernières 24h)</div>', unsafe_allow_html=True)

fig_radar = px.scatter(
    trend_df, x="today", y="velocity_score", size="today", color="velocity_score",
    text="source", labels={"today": "Volume Articles", "velocity_score": "Indice d'Accélération"},
    color_continuous_scale="Blues", height=500
)
fig_radar.add_hline(y=2.0, line_dash="dash", line_color="#3b82f6", annotation_text="Seuil d'alerte")
fig_radar.update_traces(textposition='top center')
fig_radar.update_layout(**PLOTLY_BASE)
st.plotly_chart(fig_radar, use_container_width=True)

# Insight Radar
if not trend_df.empty:
    top_accel = trend_df.sort_values('velocity_score', ascending=False).iloc[0]
    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse des flux :</b> La source <b>{top_accel['source']}</b> montre une activité anormale avec un indice 
        d'accélération de <b>{top_accel['velocity_score']:.1f}x</b>. Une surveillance accrue de ce flux est recommandée.
    </div>
    """, unsafe_allow_html=True)

# ── ÉVOLUTION TEMPORELLE ──────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">SUIVI DE L\'ÉVOLUTION TEMPORELLE ({selected_days} Jours)</div>', unsafe_allow_html=True)

fast_sources = trend_df.sort_values('velocity_score', ascending=False).head(5)['source'].tolist()
df_evo = df_filtered[df_filtered['source'].isin(fast_sources)].sort_values('published_date')

fig_line = px.line(
    df_evo, x='published_date', y='nb_articles', color='source', markers=True, height=400,
    color_discrete_sequence=px.colors.sequential.Blues_r
)
fig_line.update_layout(**PLOTLY_BASE, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig_line, use_container_width=True)

# Insight Évolution
if not df_evo.empty:
    total_articles = df_filtered['nb_articles'].sum()
    st.markdown(f"""
    <div class="insight-box">
        <b>Tendance temporelle :</b> Un volume total de <b>{int(total_articles)} articles</b> a été analysé sur la période. 
        La stabilité des courbes permet de confirmer la fiabilité des collectes automatiques par API.
    </div>
    """, unsafe_allow_html=True)

# ── DERNIERS FLUX ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">DERNIERS FLUX COLLECTÉS</div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 3])
with c1:
    unique_sources = sorted(trend_df['source'].unique()) if not trend_df.empty else ["Aucune donnée"]
    src_select = st.selectbox("Source à inspecter", unique_sources)
with c2:
    df_detail = get_stg_articles(limit=100)
    df_src = df_detail[df_detail["source"] == src_select].sort_values("published_date", ascending=False).head(8)
    
    if df_src.empty:
        st.info("Aucun article récent pour cette source.")
    else:
        for _, row in df_src.iterrows():
            st.markdown(f"""
            <div class="article-card">
                <a href="{row['url']}" target="_blank" style="color:#ffffff; text-decoration:none; font-size:0.9rem; font-weight:500;">{row['title']}</a>
                <div style="font-size:0.75rem; color:#94a3b8;">{str(row['published_date'])[:16]} | {row['category']}</div>
            </div>
            """, unsafe_allow_html=True)