# 1_Articles_collectes.py -- StatCyberMatrix theme unifie

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k1, get_stg_articles, force_refresh

st.set_page_config(page_title="StatCyberMatrix - Veille", layout="wide")

# Theme unifie : sidebar + page
from sidebar_css import inject_sidebar_css
inject_sidebar_css()
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

# ── DATA ─────────────────────────────────────────────────────────────────────
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

# ── RADAR VÉLOCITÉ ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Radar d\'émergence (dernières 24h)</div>', unsafe_allow_html=True)

fig_radar = px.scatter(
    trend_df, x="today", y="velocity_score", size="today", color="velocity_score",
    text="source", labels={"today": "Volume Articles", "velocity_score": "Indice d'Accélération"},
    color_continuous_scale=[[0, "#0d1117"], [0.3, "#3b82f6"], [0.6, "#a855f7"], [1, "#00d4ff"]],
    height=500
)
fig_radar.add_hline(y=2.0, line_dash="dash", line_color="#a855f7", annotation_text="Seuil d'alerte",
                    annotation=dict(font_color="#a855f7", font_size=11))
fig_radar.update_traces(textposition='top center', textfont=dict(size=10, color="#c8d6e5"))
fig_radar.update_layout(**PLOTLY_THEME)
st.plotly_chart(fig_radar, use_container_width=True)

# Insight
if not trend_df.empty:
    top_accel = trend_df.sort_values('velocity_score', ascending=False).iloc[0]
    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse des flux :</b> La source <b>{top_accel['source']}</b> montre une activité anormale avec un indice
        d'accélération de <b>{top_accel['velocity_score']:.1f}x</b>. Une surveillance accrue de ce flux est recommandée.
    </div>
    """, unsafe_allow_html=True)

# ── ÉVOLUTION TEMPORELLE ──────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">Suivi de l\'évolution temporelle ({selected_days} jours)</div>', unsafe_allow_html=True)

fast_sources = trend_df.sort_values('velocity_score', ascending=False).head(5)['source'].tolist()
df_evo = df_filtered[df_filtered['source'].isin(fast_sources)].sort_values('published_date')

fig_line = px.line(
    df_evo, x='published_date', y='nb_articles', color='source', markers=True, height=400,
    color_discrete_sequence=["#00d4ff", "#a855f7", "#3b82f6", "#22c55e", "#f59e0b"]
)
fig_line.update_layout(**PLOTLY_THEME, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)))
st.plotly_chart(fig_line, use_container_width=True)

# Insight
if not df_evo.empty:
    total_articles = df_filtered['nb_articles'].sum()
    st.markdown(f"""
    <div class="insight-box">
        <b>Tendance temporelle :</b> Un volume total de <b>{int(total_articles)} articles</b> a été analysé sur la période.
        La stabilité des courbes permet de confirmer la fiabilité des collectes automatiques par API.
    </div>
    """, unsafe_allow_html=True)

# ── DERNIERS FLUX ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Derniers flux collectés</div>', unsafe_allow_html=True)
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
                <a href="{row['url']}" target="_blank">{row['title']}</a>
                <div style="font-size:0.7rem; color:#7a9cc8; margin-top:3px">{str(row['published_date'])[:16]} · {row['category']}</div>
            </div>
            """, unsafe_allow_html=True)