# 1_kpi1_Articles.py -- KPI 1 : Détection d'Émergence Cyber
# Design : Radar de Vélocité & Evolution épurée

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

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif;}
.stApp {
    background: radial-gradient(ellipse at 20% 50%, rgba(14,40,80,0.9) 0%, #050a14 60%);
    background-color: #050a14 !important;
}
.page-title{text-align:center;font-size:2.5rem;font-weight:700;color:#3b82f6;margin-top:10px;margin-bottom:30px;}
.alert-banner{background:rgba(239, 68, 68, 0.1);border:1px solid #ef4444;border-radius:8px;padding:15px;margin:20px 0;}
.section-title{font-family:'Roboto Mono',monospace;font-size:1rem;color:#3b82f6;margin:30px 0 15px;border-left:4px solid #3b82f6;padding-left:15px;}
</style>
""", unsafe_allow_html=True)

# ── Titre Principal (Nettoyé) ────────────────────────────────────────────────
st.markdown('<div class="page-title">Articles collectés & Signaux émergents</div>', unsafe_allow_html=True)

# ── Chargement des Données ──────────────────────────────────────────────────
try:
    df = get_mart_k1()
    df['published_date'] = pd.to_datetime(df['published_date'])
except Exception as e:
    st.error(f"Erreur Connexion : {e}"); st.stop()

# ── LOGIQUE DE VÉLOCITÉ (Calcul de l'émergence) ──────────────────────────────
now = datetime.now()
df_24h = df[df['published_date'] >= (now - timedelta(days=1))]
df_hist = df[(df['published_date'] >= (now - timedelta(days=7))) & (df['published_date'] < (now - timedelta(days=1)))]

vol_24h = df_24h.groupby('source')['nb_articles'].sum().reset_index(name='today')
vol_hist = df_hist.groupby('source')['nb_articles'].sum().reset_index(name='total_hist')
vol_hist['avg_daily'] = vol_hist['total_hist'] / 6

trend_df = pd.merge(vol_24h, vol_hist, on='source', how='left').fillna(0)
# Score de vélocité (ratio croissance)
trend_df['velocity_score'] = (trend_df['today'] + 1) / (trend_df['avg_daily'] + 1)

# ── Configuration Plotly Base ────────────────────────────────────────────────
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,20,34,0.5)",
    font=dict(family="Roboto Mono", color="#94a3b8"),
    margin=dict(l=40, r=40, t=40, b=40)
)

# ── Visual 1 : Radar de Vélocité (Radar d'alerte) ─────────────────────────────
st.markdown('<div class="section-title">RADAR D\'ÉMERGENCE (Dernières 24h)</div>', unsafe_allow_html=True)

fig_radar = px.scatter(
    trend_df,
    x="today",
    y="velocity_score",
    size="today",
    color="velocity_score",
    text="source",
    labels={"today": "Volume Articles", "velocity_score": "Indice d'Accélération"},
    color_continuous_scale="Reds",
    height=500
)
fig_radar.add_hline(y=2.0, line_dash="dash", line_color="#ef4444", annotation_text="Seuil d'alerte")
fig_radar.update_traces(textposition='top center')
fig_radar.update_layout(**PLOTLY_BASE)
st.plotly_chart(fig_radar, use_container_width=True)

# ── Alertes ──────────────────────────────────────────────────────────────────
top_threat = trend_df.sort_values('velocity_score', ascending=False).iloc[0]
if top_threat['velocity_score'] > 2.0:
    st.markdown(f"""
    <div class="alert-banner">
        <b style="color:#ef4444">⚠️ ALERTE VÉLOCITÉ :</b> La source <b>{top_threat['source']}</b> 
        publie {top_threat['velocity_score']:.1f}x plus que d'habitude. Sujet critique potentiel détecté.
    </div>
    """, unsafe_allow_html=True)

# ── Visual 2 : Suivi de l'évolution (Version simplifiée et lisible) ───────────
st.markdown('<div class="section-title">SUIVI DE L\'ÉVOLUTION TEMPORELLE (7 Jours)</div>', unsafe_allow_html=True)

# On filtre sur les sources les plus pertinentes pour éviter la surcharge visuelle
fast_sources = trend_df.sort_values('velocity_score', ascending=False).head(5)['source'].tolist()
df_evo = df[df['source'].isin(fast_sources) & (df['published_date'] >= (now - timedelta(days=7)))]
df_evo = df_evo.sort_values('published_date')

# Graphique de lignes simple (plus lisible que l'area chart pour suivre des courbes individuelles)
fig_line = px.line(
    df_evo,
    x='published_date',
    y='nb_articles',
    color='source',
    markers=True,
    height=400,
    labels={'nb_articles': 'Articles / jour', 'published_date': 'Date'},
    color_discrete_sequence=px.colors.qualitative.Pastel
)

fig_line.update_layout(
    **PLOTLY_BASE,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified"
)
fig_line.update_xaxes(showgrid=False)
fig_line.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig_line, use_container_width=True)

# ── Tableau de détail ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">DERNIERS FLUX COLLECTÉS</div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 3])
with c1:
    src_select = st.selectbox("Source à inspecter", sorted(trend_df['source'].unique()))
with c2:
    df_detail = get_stg_articles(limit=100)
    df_src = df_detail[df_detail["source"] == src_select].sort_values("published_date", ascending=False).head(8)
    
    for _, row in df_src.iterrows():
        st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03); border-left:3px solid #3b82f6; padding:10px 15px; margin-bottom:8px; border-radius:4px;">
                <a href="{row['url']}" target="_blank" style="color:#e2e8f0; text-decoration:none; font-size:0.9rem;">{row['title']}</a>
                <div style="font-size:0.75rem; color:#64748b;">{row['published_date']} | {row['category']}</div>
            </div>
        """, unsafe_allow_html=True)